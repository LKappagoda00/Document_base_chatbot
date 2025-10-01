/**
 * Enhanced Ask page - Chat-style interface for asking questions with RAG
 */

import React, { useState, useEffect, useRef } from 'react';
import { queryAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const AskPage = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [settings, setSettings] = useState({
    maxChunks: 5,
    temperature: 0.7,
  });
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Add welcome message
    setMessages([
      {
        type: 'system',
        content: 'Welcome! Ask me anything about your uploaded documents. I\'ll search through your knowledge base and provide answers with source references.',
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!currentQuestion.trim() || loading) return;

    const question = currentQuestion.trim();
    setCurrentQuestion('');
    setError('');

    // Add user message
    const userMessage = {
      type: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      setLoading(true);

      // Add thinking message
      const thinkingMessage = {
        type: 'assistant',
        content: '🤔 Searching through your documents...',
        timestamp: new Date().toISOString(),
        isThinking: true,
      };
      setMessages(prev => [...prev, thinkingMessage]);

      const response = await queryAPI.askQuestion(question, {
        maxChunks: settings.maxChunks,
        temperature: settings.temperature,
      });

      // Remove thinking message and add real response
      setMessages(prev => {
        const withoutThinking = prev.filter(msg => !msg.isThinking);
        const assistantMessage = {
          type: 'assistant',
          content: response.answer,
          sources: response.sources,
          modelInfo: response.model_info,
          processingTime: response.processing_time_ms,
          timestamp: new Date().toISOString(),
        };
        return [...withoutThinking, assistantMessage];
      });

    } catch (error) {
      console.error('Query error:', error);
      setError(error.response?.data?.detail || 'Failed to get answer');
      
      // Remove thinking message and add error message
      setMessages(prev => {
        const withoutThinking = prev.filter(msg => !msg.isThinking);
        const errorMessage = {
          type: 'error',
          content: error.response?.data?.detail || 'Sorry, I encountered an error while processing your question.',
          timestamp: new Date().toISOString(),
        };
        return [...withoutThinking, errorMessage];
      });
    } finally {
      setLoading(false);
    }
  };

  const clearConversation = () => {
    setMessages([
      {
        type: 'system',
        content: 'Conversation cleared. Ask me anything about your uploaded documents!',
        timestamp: new Date().toISOString(),
      },
    ]);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const renderMessage = (message, index) => {
    switch (message.type) {
      case 'system':
        return (
          <div key={index} className="flex justify-center mb-4">
            <div className="bg-blue-50 text-blue-800 px-4 py-2 rounded-lg text-sm max-w-md text-center">
              {message.content}
            </div>
          </div>
        );

      case 'user':
        return (
          <div key={index} className="flex justify-end mb-4">
            <div className="bg-blue-600 text-white px-4 py-2 rounded-lg max-w-md">
              <p>{message.content}</p>
              <p className="text-xs text-blue-100 mt-1">{formatTime(message.timestamp)}</p>
            </div>
          </div>
        );

      case 'assistant':
        return (
          <div key={index} className="flex justify-start mb-4">
            <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg max-w-2xl">
              <div className="flex items-start space-x-2">
                <span className="text-lg">🤖</span>
                <div className="flex-1">
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <h4 className="text-xs font-medium text-gray-600 mb-2">Sources:</h4>
                      <div className="space-y-2">
                        {message.sources.map((source, i) => (
                          <div key={i} className="bg-white p-2 rounded border text-xs">
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium">Document {source.document_id}</span>
                              <span className="text-gray-500">
                                {(source.similarity_score * 100).toFixed(1)}% match
                              </span>
                            </div>
                            <p className="text-gray-600 italic">"{source.snippet}"</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                    <span>{formatTime(message.timestamp)}</span>
                    {message.processingTime && (
                      <span>{message.processingTime}ms</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'error':
        return (
          <div key={index} className="flex justify-start mb-4">
            <div className="bg-red-50 text-red-800 px-4 py-2 rounded-lg max-w-md">
              <div className="flex items-start space-x-2">
                <span>❌</span>
                <div>
                  <p>{message.content}</p>
                  <p className="text-xs text-red-600 mt-1">{formatTime(message.timestamp)}</p>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-full flex flex-col">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Ask Questions</h1>
            <p className="text-sm text-gray-600">Get AI-powered answers from your documents</p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md"
            >
              ⚙️ Settings
            </button>
            <button
              onClick={clearConversation}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md"
            >
              🗑️ Clear
            </button>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Query Settings</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Max Chunks</label>
                <select
                  value={settings.maxChunks}
                  onChange={(e) => setSettings(prev => ({ ...prev, maxChunks: parseInt(e.target.value) }))}
                  className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={7}>7</option>
                  <option value={10}>10</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Temperature</label>
                <select
                  value={settings.temperature}
                  onChange={(e) => setSettings(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                  className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value={0.3}>0.3 (Focused)</option>
                  <option value={0.7}>0.7 (Balanced)</option>
                  <option value={1.0}>1.0 (Creative)</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Messages Container */}
      <div className="flex-1 bg-white shadow rounded-lg p-4 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-2" style={{ maxHeight: '60vh' }}>
          {messages.map((message, index) => renderMessage(message, index))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <div className="border-t pt-4 mt-4">
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <input
              type="text"
              value={currentQuestion}
              onChange={(e) => setCurrentQuestion(e.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={loading}
              className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
            />
            <button
              type="submit"
              disabled={loading || !currentQuestion.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md font-medium"
            >
              {loading ? '⏳' : '➤'}
            </button>
          </form>
          
          {error && (
            <div className="mt-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AskPage;