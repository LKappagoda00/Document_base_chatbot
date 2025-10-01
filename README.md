# SaaS LLM Application

A complete SaaS application for document-based question answering using RAG (Retrieval-Augmented Generation) architecture. Users can upload PDF documents and ask natural language questions to get AI-powered answers with source references.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │   Ollama LLM    │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│  (Port 11434)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Interface │    │   Vector DB     │    │   Remote LLM    │
│   • Upload PDFs │    │   (ChromaDB)    │    │   (Production)  │
│   • Ask Questions│    │   • Embeddings  │    │   • GPU Server  │
│   • View Results │    │   • Similarity  │    │   • API Gateway │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Key Features

### ✅ Implemented Features
- **User Authentication**: JWT-based login/register system
- **PDF Upload & Processing**: Extract text, chunk, and embed documents
- **RAG Question Answering**: Ask questions and get contextual answers
- **Multi-tenant Architecture**: User isolation for SaaS deployment
- **Switchable LLM Endpoints**: Easy switch between local Ollama and remote GPU servers
- **Vector Database Integration**: ChromaDB for similarity search
- **Clean React UI**: Modern interface with Tailwind CSS
- **Real-time Processing**: Async document processing and query handling

### 🔄 Ready for Production Extensions
- **Cloud Vector DB**: Easy migration to Pinecone/Weaviate
- **Remote LLM Integration**: Switch to hosted LLM APIs
- **Advanced Chunking**: Semantic chunking strategies
- **Multi-file Support**: Support for more document types
- **Chat History**: Conversation persistence
- **Admin Dashboard**: User management and analytics

## 📁 Project Structure

```
saas-llm/
├── backend/                    # FastAPI Backend
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py        # Environment configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py        # SQLite database models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication routes
│   │   ├── files.py          # File upload routes
│   │   └── query.py          # Question answering routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py           # JWT authentication service
│   │   ├── embeddings.py     # Text embedding service
│   │   ├── llm.py            # LLM integration service
│   │   └── vector_store.py   # ChromaDB vector operations
│   ├── .env                  # Environment variables
│   ├── .env.example         # Example environment config
│   ├── main.py              # FastAPI application entry
│   └── requirements.txt     # Python dependencies
├── frontend/                 # React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.js     # Main app layout
│   │   │   └── LoadingSpinner.js
│   │   ├── contexts/
│   │   │   └── AuthContext.js # Authentication context
│   │   ├── pages/
│   │   │   ├── LoginPage.js
│   │   │   ├── RegisterPage.js
│   │   │   ├── DashboardPage.js
│   │   │   ├── UploadPage.js
│   │   │   └── AskPage.js
│   │   ├── services/
│   │   │   └── api.js        # Backend API integration
│   │   └── App.js           # Main React component
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- Ollama (for local LLM)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env file with your settings

# Run the backend
python main.py
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### 3. Ollama Setup (Local LLM)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (e.g., Llama 2)
ollama pull llama2

# Start Ollama server (runs on localhost:11434)
ollama serve
```

## ⚙️ Configuration

### Environment Variables

**Backend (.env)**:
```env
# LLM Configuration
LLM_API_URL=http://localhost:11434  # Local Ollama
# LLM_API_URL=https://your-gpu-server.com  # Production
LLM_MODEL=llama2

# Authentication
JWT_SECRET_KEY=your-super-secret-key
JWT_EXPIRATION_HOURS=24

# File Upload
MAX_FILE_SIZE_MB=50
UPLOAD_DIR=./uploads

# Vector Database
CHROMA_DB_PATH=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2

# API Configuration
API_CORS_ORIGINS=["http://localhost:3000"]
```

**Frontend (.env)**:
```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

### Switching to Production LLM

To switch from local Ollama to a remote GPU server:

1. Update `LLM_API_URL` in backend `.env`
2. Modify `llm.py` service for your specific API format
3. Add authentication headers if required

Example for OpenAI-compatible API:
```python
# In services/llm.py
headers = {
    "Authorization": f"Bearer {os.getenv('LLM_API_KEY')}",
    "Content-Type": "application/json"
}
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info
- `POST /auth/verify-token` - Verify JWT token

### File Management Endpoints
- `POST /files/upload` - Upload PDF document
- `GET /files/documents` - Get user's documents
- `DELETE /files/documents/{id}` - Delete document
- `GET /files/stats` - Get upload statistics

### Query Endpoints
- `POST /query/ask` - Ask question (RAG)
- `POST /query/search` - Search documents
- `GET /query/health` - Service health check

### Example API Usage

**Upload a PDF:**
```bash
curl -X POST \
  http://localhost:8000/files/upload \
  -H "Authorization: Bearer <jwt_token>" \
  -F "file=@document.pdf"
```

**Ask a Question:**
```bash
curl -X POST \
  http://localhost:8000/query/ask \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key findings in the report?",
    "max_chunks": 5,
    "temperature": 0.7
  }'
```

## 🚀 Deployment Guide

### Development Deployment
1. Start Ollama: `ollama serve`
2. Start Backend: `python main.py`
3. Start Frontend: `npm start`

### Production Deployment

**Backend (Docker):**
```dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend (Build):**
```bash
npm run build
# Deploy build/ folder to CDN/hosting service
```

**Environment Setup:**
- Update `LLM_API_URL` to remote GPU server
- Use production database (PostgreSQL recommended)
- Configure cloud vector database (Pinecone, Weaviate)
- Set up proper secrets management
- Enable HTTPS and security headers

### Cloud Migration Checklist

**Vector Database:**
- [ ] Replace ChromaDB with Pinecone/Weaviate
- [ ] Update vector_store.py service
- [ ] Migrate existing embeddings

**LLM Service:**
- [ ] Configure remote LLM endpoint
- [ ] Add API authentication
- [ ] Update rate limiting

**Database:**
- [ ] Migrate from SQLite to PostgreSQL
- [ ] Set up database migrations
- [ ] Configure connection pooling

**Authentication:**
- [ ] Use secure JWT secrets
- [ ] Implement refresh tokens
- [ ] Add OAuth providers (optional)

**Infrastructure:**
- [ ] Set up load balancing
- [ ] Configure auto-scaling
- [ ] Add monitoring and logging
- [ ] Set up backup strategies

## 🔧 Development Notes

### Adding New Features

**New Document Type Support:**
1. Update `allowed_file_types` in settings
2. Add processing logic in `files.py`
3. Create appropriate text extraction method

**Advanced Chunking:**
1. Modify `embeddings.py` chunk_text method
2. Implement semantic chunking strategies
3. Add chunk overlap optimization

**Chat History:**
1. Add conversation models to database
2. Create chat persistence endpoints
3. Update frontend for conversation UI

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Performance Optimization

**Embedding Generation:**
- Use batch processing for multiple documents
- Implement caching for frequently accessed embeddings
- Consider using smaller, faster embedding models

**Vector Search:**
- Optimize ChromaDB collection configuration
- Implement search result caching
- Use approximate search for large datasets

**LLM Queries:**
- Implement request batching
- Add response caching
- Use streaming for long responses

## 🔐 Security Considerations

- JWT tokens with secure secrets
- File type validation and size limits
- User input sanitization
- Rate limiting on API endpoints
- CORS configuration for production
- Secure file storage and access
- Database query parameterization

## 📊 Monitoring and Analytics

**Metrics to Track:**
- Document upload success/failure rates
- Query response times
- User engagement metrics
- LLM API usage and costs
- Vector database performance
- Authentication events

**Recommended Tools:**
- Backend: Prometheus + Grafana
- Frontend: Google Analytics / Mixpanel
- Logs: ELK Stack / CloudWatch
- Errors: Sentry / Rollbar

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Troubleshooting

**Common Issues:**

1. **Ollama Connection Failed**
   - Ensure Ollama is running: `ollama serve`
   - Check port 11434 is accessible
   - Verify model is pulled: `ollama list`

2. **CORS Issues**
   - Update `API_CORS_ORIGINS` in backend `.env`
   - Restart backend after changes

3. **File Upload Fails**
   - Check file size limits
   - Verify upload directory permissions
   - Ensure PDF is not corrupted

4. **Authentication Errors**
   - Verify JWT secret is set
   - Check token expiration
   - Clear browser storage and re-login

5. **Vector Search Issues**
   - Verify ChromaDB directory exists
   - Check embedding model is loaded
   - Ensure documents are properly processed

For more help, check the logs or create an issue in the repository. PDF Q&A Platform

## Overview
A SaaS-ready web application for Q&A over uploaded PDF files using RAG architecture, local Ollama, and ChromaDB. Easily switch to remote LLM and Pinecone for production.

## Tech Stack
- Frontend: React + Tailwind
- Backend: FastAPI (Python)
- Vector DB: ChromaDB (local, swappable)
- LLM: Ollama (local dev, remote prod)
- File Processing: PyMuPDF
- Auth: JWT (multi-tenant ready)

## Features
- Upload PDFs, extract text, chunk, embed, store in vector DB
- Ask questions, retrieve relevant chunks, send to LLM, get answers with references
- Clean UI: upload page, chat page
- Configurable LLM endpoint via `.env`

## Example API Calls
### Upload PDF
```bash
curl -X POST "http://localhost:8000/files/upload" -F "file=@yourfile.pdf" -H "Authorization: Bearer <JWT>"
```
### Ask Question
```bash
curl -X POST "http://localhost:8000/query/ask" -H "Content-Type: application/json" -H "Authorization: Bearer <JWT>" -d '{"question": "What are the sprint goals?"}'
```

## Environment Variables
- Backend: `.env` (LLM_API_URL, VECTOR_DB, JWT_SECRET)
- Frontend: `.env.example` (REACT_APP_API_URL)

## Extending for Production
- Swap ChromaDB for Pinecone in `services/vector_store.py`
- Change `LLM_API_URL` in `.env` for remote LLM
- Extend JWT auth for multi-tenancy
- Add scaling/cloud deployment as needed
