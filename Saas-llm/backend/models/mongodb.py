"""
MongoDB models for the SaaS LLM application.
Using Motor (async MongoDB driver) for better performance with FastAPI.
"""

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import hashlib
from config.settings import settings


class MongoDB:
    """MongoDB database connection and management."""
    
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
        self.database: AsyncIOMotorDatabase = self.client[settings.mongodb_database]
        
    async def close(self):
        """Close database connection."""
        self.client.close()
    
    async def init_database(self):
        """Initialize database collections and indexes."""
        # Create indexes for better performance
        
        # Users collection indexes
        await self.database.users.create_index("email", unique=True)
        await self.database.users.create_index("created_at")
        
        # Documents collection indexes
        await self.database.documents.create_index("user_id")
        await self.database.documents.create_index("created_at")
        await self.database.documents.create_index([("user_id", 1), ("created_at", -1)])
        
        # Document chunks collection indexes
        await self.database.document_chunks.create_index("document_id")
        await self.database.document_chunks.create_index([("document_id", 1), ("chunk_index", 1)], unique=True)
        
        # Conversations collection indexes
        await self.database.conversations.create_index("user_id")
        await self.database.conversations.create_index("created_at")
        
        # Messages collection indexes
        await self.database.messages.create_index("conversation_id")
        await self.database.messages.create_index("created_at")


class MongoUser:
    """User model for MongoDB."""
    
    def __init__(self, db: MongoDB = None):
        self.db = db or MongoDB()
        self.collection: AsyncIOMotorCollection = self.db.database.users
    
    async def create_user(self, email: str, password_hash: str, full_name: str = None) -> str:
        """Create a new user."""
        user_doc = {
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(user_doc)
        return str(result.inserted_id)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        user = await self.collection.find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
            del user["_id"]
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            user = await self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["id"] = str(user["_id"])
                del user["_id"]
            return user
        except Exception:
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data."""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False


class MongoDocument:
    """Document model for MongoDB."""
    
    def __init__(self, db: MongoDB = None):
        self.db = db or MongoDB()
        self.collection: AsyncIOMotorCollection = self.db.database.documents
        self.chunks_collection: AsyncIOMotorCollection = self.db.database.document_chunks
    
    async def create_document(self, user_id: str, filename: str, file_path: str, 
                             file_size: int, content_preview: str = None) -> str:
        """Create a new document record."""
        doc = {
            "user_id": user_id,
            "filename": filename,
            "file_path": file_path,
            "file_size": file_size,
            "content_preview": content_preview,
            "status": "processing",
            "created_at": datetime.utcnow(),
            "processed_at": None
        }
        
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)
    
    async def update_document_status(self, doc_id: str, status: str):
        """Update document processing status."""
        try:
            await self.collection.update_one(
                {"_id": ObjectId(doc_id)},
                {
                    "$set": {
                        "status": status,
                        "processed_at": datetime.utcnow()
                    }
                }
            )
        except Exception:
            pass
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a user."""
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1)
        
        documents = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
            documents.append(doc)
        
        return documents
    
    async def add_document_chunk(self, doc_id: str, chunk_index: int, content: str) -> str:
        """Add a document chunk."""
        chunk_hash = hashlib.sha256(content.encode()).hexdigest()
        
        chunk_doc = {
            "document_id": doc_id,
            "chunk_index": chunk_index,
            "content": content,
            "chunk_hash": chunk_hash,
            "created_at": datetime.utcnow()
        }
        
        # Use upsert to handle duplicates
        result = await self.chunks_collection.replace_one(
            {"document_id": doc_id, "chunk_index": chunk_index},
            chunk_doc,
            upsert=True
        )
        
        return str(result.upserted_id) if result.upserted_id else doc_id
    
    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(doc_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
            return doc
        except Exception:
            return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its chunks."""
        try:
            # Delete document chunks first
            await self.chunks_collection.delete_many({"document_id": doc_id})
            
            # Delete the document
            result = await self.collection.delete_one({"_id": ObjectId(doc_id)})
            
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a document."""
        cursor = self.chunks_collection.find(
            {"document_id": doc_id}
        ).sort("chunk_index", 1)
        
        chunks = []
        async for chunk in cursor:
            chunk["id"] = str(chunk["_id"])
            del chunk["_id"]
            chunks.append(chunk)
        
        return chunks


class MongoConversation:
    """Conversation model for MongoDB."""
    
    def __init__(self, db: MongoDB = None):
        self.db = db or MongoDB()
        self.collection: AsyncIOMotorCollection = self.db.database.conversations
        self.messages_collection: AsyncIOMotorCollection = self.db.database.messages
    
    async def create_conversation(self, user_id: str, title: str = None) -> str:
        """Create a new conversation."""
        conversation_doc = {
            "user_id": user_id,
            "title": title,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.collection.insert_one(conversation_doc)
        return str(result.inserted_id)
    
    async def add_message(self, conversation_id: str, role: str, content: str, 
                         sources: List[str] = None) -> str:
        """Add a message to a conversation."""
        message_doc = {
            "conversation_id": conversation_id,
            "role": role,  # 'user' or 'assistant'
            "content": content,
            "sources": sources or [],
            "created_at": datetime.utcnow()
        }
        
        result = await self.messages_collection.insert_one(message_doc)
        
        # Update conversation timestamp
        await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"updated_at": datetime.utcnow()}}
        )
        
        return str(result.inserted_id)
    
    async def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user."""
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort("updated_at", -1)
        
        conversations = []
        async for conv in cursor:
            conv["id"] = str(conv["_id"])
            del conv["_id"]
            conversations.append(conv)
        
        return conversations
    
    async def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation."""
        cursor = self.messages_collection.find(
            {"conversation_id": conversation_id}
        ).sort("created_at", 1)
        
        messages = []
        async for msg in cursor:
            msg["id"] = str(msg["_id"])
            del msg["_id"]
            messages.append(msg)
        
        return messages


# Global MongoDB instance
mongodb = MongoDB()

# Backward compatibility - keeping the same interface as before
class Database:
    """Compatibility wrapper for MongoDB."""
    
    def __init__(self, db_path: str = None):
        self.mongodb = MongoDB()
    
    async def get_connection(self):
        """Get database connection."""
        return self.mongodb.database
    
    async def init_database(self):
        """Initialize database."""
        await self.mongodb.init_database()


class User:
    """Compatibility wrapper for MongoUser."""
    
    def __init__(self, db: Database = None):
        self.mongo_user = MongoUser()
    
    async def create_user(self, email: str, password_hash: str, full_name: str = None) -> str:
        return await self.mongo_user.create_user(email, password_hash, full_name)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.mongo_user.get_user_by_email(email)
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.mongo_user.get_user_by_id(user_id)


class Document:
    """Compatibility wrapper for MongoDocument."""
    
    def __init__(self, db: Database = None):
        self.mongo_document = MongoDocument()
    
    async def create_document(self, user_id: str, filename: str, file_path: str, 
                             file_size: int, content_preview: str = None) -> str:
        return await self.mongo_document.create_document(user_id, filename, file_path, file_size, content_preview)
    
    async def update_document_status(self, doc_id: str, status: str):
        await self.mongo_document.update_document_status(doc_id, status)
    
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.mongo_document.get_user_documents(user_id)
    
    async def add_document_chunk(self, doc_id: str, chunk_index: int, content: str) -> str:
        return await self.mongo_document.add_document_chunk(doc_id, chunk_index, content)
    
    async def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return await self.mongo_document.get_document_by_id(doc_id)
    
    async def delete_document(self, doc_id: str) -> bool:
        return await self.mongo_document.delete_document(doc_id)


# Initialize database on import
db = Database()