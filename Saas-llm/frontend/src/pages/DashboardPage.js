/**
 * Dashboard page - overview of user's documents and recent activity
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { filesAPI, queryAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const DashboardPage = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentDocuments, setRecentDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load stats and recent documents in parallel
      const [statsResponse, documentsResponse, healthResponse] = await Promise.allSettled([
        filesAPI.getUploadStats(),
        filesAPI.getDocuments(),
        queryAPI.getHealthCheck().catch(() => null) // Don't fail if health check fails
      ]);

      if (statsResponse.status === 'fulfilled') {
        setStats(statsResponse.value);
      }

      if (documentsResponse.status === 'fulfilled') {
        setRecentDocuments(documentsResponse.value.documents.slice(0, 5)); // Show last 5
      }

      if (healthResponse.status === 'fulfilled' && healthResponse.value) {
        setHealthStatus(healthResponse.value);
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, {user?.full_name || user?.email}!
            </h1>
            <p className="text-gray-600 mt-1">
              Here's an overview of your document library and AI assistant activity.
            </p>
          </div>
          <div className="flex space-x-3">
            <Link
              to="/upload"
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Upload Document
            </Link>
            <Link
              to="/ask"
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Ask Question
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <span className="text-2xl">📄</span>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Documents
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.total_documents}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <span className="text-2xl">💾</span>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Storage Used
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.total_file_size_mb} MB
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <span className="text-2xl">🧩</span>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Text Chunks
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.total_chunks}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <span className="text-2xl">✅</span>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Processed
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {stats.documents_by_status?.completed || 0}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* System Health Status */}
      {healthStatus && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${healthStatus.embedding_service?.working ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="text-sm">Embedding Service</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${healthStatus.llm_service?.available ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="text-sm">LLM Service</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${healthStatus.vector_store?.total_chunks >= 0 ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="text-sm">Vector Database</span>
            </div>
          </div>
        </div>
      )}

      {/* Recent Documents */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">Recent Documents</h2>
            <Link
              to="/upload"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              View all
            </Link>
          </div>
        </div>
        <div className="divide-y divide-gray-200">
          {recentDocuments.length > 0 ? (
            recentDocuments.map((doc, index) => (
              <div key={index} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {doc.filename}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {(doc.file_size / 1024 / 1024).toFixed(2)} MB • 
                      Uploaded {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex-shrink-0">
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      doc.status === 'completed' 
                        ? 'bg-green-100 text-green-800'
                        : doc.status === 'processing'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {doc.status}
                    </span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="px-6 py-8 text-center">
              <span className="text-4xl mb-4 block">📄</span>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No documents yet</h3>
              <p className="text-gray-500 mb-4">
                Upload your first PDF document to get started with AI-powered question answering.
              </p>
              <Link
                to="/upload"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Upload Document
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link
            to="/upload"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            <span className="text-2xl mr-4">⬆️</span>
            <div>
              <h3 className="font-medium text-gray-900">Upload Documents</h3>
              <p className="text-sm text-gray-500">Add new PDF files to your knowledge base</p>
            </div>
          </Link>
          <Link
            to="/ask"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            <span className="text-2xl mr-4">💬</span>
            <div>
              <h3 className="font-medium text-gray-900">Ask Questions</h3>
              <p className="text-sm text-gray-500">Get AI-powered answers from your documents</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;