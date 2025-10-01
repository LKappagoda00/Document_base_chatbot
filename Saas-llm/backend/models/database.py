"""
Database models for the SaaS LLM application.
Using SQLite with simple table structures for development.
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from config.settings import settings


class Database:
    """Simple database interface using SQLite."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_url.replace("sqlite:///", "")
        self.init_database()
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table for authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Documents table for uploaded PDFs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                content_preview TEXT,
                status TEXT DEFAULT 'processing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Document chunks table for vector storage metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                chunk_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id),
                UNIQUE(document_id, chunk_index)
            )
        """)
        
        # Conversations table for chat history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Messages table for chat messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,  -- 'user' or 'assistant'
                content TEXT NOT NULL,
                sources TEXT,  -- JSON array of source document references
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        """)
        
        conn.commit()
        conn.close()


class User:
    """User model for authentication."""
    
    def __init__(self, db: Database = None):
        self.db = db or Database()
    
    def create_user(self, email: str, password_hash: str, full_name: str = None) -> int:
        """Create a new user."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name)
            VALUES (?, ?, ?)
        """, (email, password_hash, full_name))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, password_hash, full_name, is_active, created_at
            FROM users WHERE email = ?
        """, (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "email": row[1],
                "password_hash": row[2],
                "full_name": row[3],
                "is_active": bool(row[4]),
                "created_at": row[5]
            }
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, password_hash, full_name, is_active, created_at
            FROM users WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "email": row[1],
                "password_hash": row[2],
                "full_name": row[3],
                "is_active": bool(row[4]),
                "created_at": row[5]
            }
        return None


class Document:
    """Document model for uploaded files."""
    
    def __init__(self, db: Database = None):
        self.db = db or Database()
    
    def create_document(self, user_id: int, filename: str, file_path: str, 
                       file_size: int, content_preview: str = None) -> int:
        """Create a new document record."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO documents (user_id, filename, file_path, file_size, content_preview)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, filename, file_path, file_size, content_preview))
        
        doc_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return doc_id
    
    def update_document_status(self, doc_id: int, status: str):
        """Update document processing status."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE documents 
            SET status = ?, processed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, doc_id))
        
        conn.commit()
        conn.close()
    
    def get_user_documents(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all documents for a user."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, filename, file_size, content_preview, status, created_at, processed_at
            FROM documents WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "filename": row[1],
                "file_size": row[2],
                "content_preview": row[3],
                "status": row[4],
                "created_at": row[5],
                "processed_at": row[6]
            }
            for row in rows
        ]
    
    def add_document_chunk(self, doc_id: int, chunk_index: int, content: str) -> int:
        """Add a document chunk."""
        chunk_hash = hashlib.sha256(content.encode()).hexdigest()
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO document_chunks 
            (document_id, chunk_index, content, chunk_hash)
            VALUES (?, ?, ?, ?)
        """, (doc_id, chunk_index, content, chunk_hash))
        
        chunk_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return chunk_id
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, user_id, filename, file_path, file_size, content_preview, 
                   status, created_at, processed_at
            FROM documents WHERE id = ?
        """, (doc_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "filename": row[2],
                "file_path": row[3],
                "file_size": row[4],
                "content_preview": row[5],
                "status": row[6],
                "created_at": row[7],
                "processed_at": row[8]
            }
        return None
    
    def delete_document(self, doc_id: int) -> bool:
        """Delete a document and its chunks."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete document chunks first
            cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc_id,))
            
            # Delete the document
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


# Initialize database on import
db = Database()