/**
 * API service for communicating with the SaaS LLM backend
 * Handles authentication, file uploads, and queries
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('userData');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (email, password, fullName) => {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  verifyToken: async () => {
    const response = await api.post('/auth/verify-token');
    return response.data;
  },
};

// Files API
export const filesAPI = {
  uploadPDF: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });
    return response.data;
  },

  getDocuments: async () => {
    const response = await api.get('/files/documents');
    return response.data;
  },

  deleteDocument: async (documentId) => {
    const response = await api.delete(`/files/documents/${documentId}`);
    return response.data;
  },

  getUploadStats: async () => {
    const response = await api.get('/files/stats');
    return response.data;
  },
};

// Query API
export const queryAPI = {
  askQuestion: async (question, options = {}) => {
    const payload = {
      question,
      document_ids: options.documentIds,
      max_chunks: options.maxChunks || 5,
      temperature: options.temperature || 0.7,
    };

    const response = await api.post('/query/ask', payload);
    return response.data;
  },

  searchDocuments: async (query, options = {}) => {
    const payload = {
      question: query,
      document_ids: options.documentIds,
      max_chunks: options.maxChunks || 10,
    };

    const response = await api.post('/query/search', payload);
    return response.data;
  },

  getHealthCheck: async () => {
    const response = await api.get('/query/health');
    return response.data;
  },
};

// General API
export const generalAPI = {
  getHealthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;