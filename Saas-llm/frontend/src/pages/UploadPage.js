/**
 * Enhanced Upload page for PDF documents with drag-and-drop and progress tracking
 */

import React, { useState, useEffect, useCallback } from 'react';
import { filesAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const UploadPage = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await filesAPI.getDocuments();
      setDocuments(response.documents);
    } catch (error) {
      console.error('Error loading documents:', error);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;

    // Validate file type
    if (file.type !== 'application/pdf') {
      setError('Please select a PDF file');
      return;
    }

    // Validate file size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB');
      return;
    }

    try {
      setUploading(true);
      setError('');
      setSuccess('');
      setUploadProgress(0);

      const response = await filesAPI.uploadPDF(file, (progress) => {
        setUploadProgress(progress);
      });

      setSuccess(`File "${response.filename}" uploaded successfully! Generated ${response.chunks_created} text chunks.`);
      setUploadProgress(100);
      
      // Reload documents list
      setTimeout(() => {
        loadDocuments();
        setUploadProgress(0);
      }, 1000);

    } catch (error) {
      console.error('Upload error:', error);
      setError(error.response?.data?.detail || 'Upload failed');
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleDrop = useCallback((event) => {
    event.preventDefault();
    setDragOver(false);
    
    const files = Array.from(event.dataTransfer.files);
    const pdfFile = files.find(file => file.type === 'application/pdf');
    
    if (pdfFile) {
      handleFileUpload(pdfFile);
    } else {
      setError('Please drop a PDF file');
    }
  }, []);

  const handleDragOver = useCallback((event) => {
    event.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((event) => {
    event.preventDefault();
    setDragOver(false);
  }, []);

  const handleDeleteDocument = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await filesAPI.deleteDocument(documentId);
      setSuccess('Document deleted successfully');
      loadDocuments();
    } catch (error) {
      console.error('Delete error:', error);
      setError(error.response?.data?.detail || 'Failed to delete document');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Upload Documents</h1>
        <p className="text-gray-600">
          Upload PDF documents to build your knowledge base. Our AI will extract text, 
          create embeddings, and make your documents searchable.
        </p>
      </div>

      {/* Upload Area */}
      <div className="bg-white shadow rounded-lg p-6">
        <div
          className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
            dragOver
              ? 'border-blue-400 bg-blue-50'
              : uploading
              ? 'border-yellow-400 bg-yellow-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <div className="text-center">
            {uploading ? (
              <div className="space-y-4">
                <div className="text-4xl">⏳</div>
                <div>
                  <p className="text-lg font-medium text-gray-900">Uploading and processing...</p>
                  <div className="mt-2 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{uploadProgress}% complete</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-4xl">📄</div>
                <div>
                  <p className="text-lg font-medium text-gray-900">
                    Drop your PDF here, or click to select
                  </p>
                  <p className="text-gray-500">Maximum file size: 50MB</p>
                </div>
                <label className="cursor-pointer">
                  <span className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                    Choose File
                  </span>
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    disabled={uploading}
                  />
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {success && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-md p-4">
            <p className="text-sm text-green-600">{success}</p>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Your Documents</h2>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : documents.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {documents.map((doc) => (
              <div key={doc.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">📄</span>
                      <div>
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {doc.filename}
                        </h3>
                        <div className="flex items-center space-x-2 text-sm text-gray-500">
                          <span>{formatFileSize(doc.file_size)}</span>
                          <span>•</span>
                          <span>Uploaded {formatDate(doc.created_at)}</span>
                          {doc.processed_at && (
                            <>
                              <span>•</span>
                              <span>Processed {formatDate(doc.processed_at)}</span>
                            </>
                          )}
                        </div>
                        {doc.content_preview && (
                          <p className="text-xs text-gray-400 mt-1 truncate max-w-md">
                            {doc.content_preview}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span
                      className={`inline-flex px-2 py-1 text-xs rounded-full ${
                        doc.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : doc.status === 'processing'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {doc.status}
                    </span>
                    <button
                      onClick={() => handleDeleteDocument(doc.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                      title="Delete document"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-6 py-8 text-center">
            <span className="text-4xl mb-4 block">📚</span>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No documents uploaded yet</h3>
            <p className="text-gray-500 mb-4">
              Upload your first PDF document to start building your AI-powered knowledge base.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;