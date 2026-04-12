import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { API_BASE_URL, API_ENDPOINTS } from '@/lib/apiService';
import { SentimentEmoji } from './SentimentEmoji';

interface TranscriptMessage {
  id: string;
  speaker: 'agent' | 'user';
  message: string;
  timestamp: string;
  sentiment: 'positive' | 'neutral' | 'negative';
}

interface TranscriptData {
  id: string;
  messages: TranscriptMessage[];
  actionTaken?: string;
  leadName: string;
  course: string;
  timestamp: string;
}

interface TranscriptModalProps {
  callId: string;
  onClose: () => void;
}

const fetchTranscript = async (callId: string): Promise<TranscriptData> => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.callTranscript(callId)}`, {
    headers: {
      Authorization: token ? `Bearer ${token}` : '',
    },
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error('Failed to fetch transcript');
  }
  return response.json();
};

export const TranscriptModal: React.FC<TranscriptModalProps> = ({ callId, onClose }) => {
  const { data: transcript, isLoading, error } = useQuery<TranscriptData>({
    queryKey: ['transcript', callId],
    queryFn: () => fetchTranscript(callId),
    enabled: !!callId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Call Transcript</h2>
            {transcript && (
              <p className="text-sm text-gray-600 mt-1">
                {transcript.leadName} • {transcript.course} • {formatTime(transcript.timestamp)}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading && (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-gray-600">Loading transcript...</span>
            </div>
          )}

          {error && (
            <div className="text-center py-12">
              <div className="text-red-600 font-medium">Failed to load transcript</div>
              <div className="text-gray-500 text-sm mt-1">
                {error instanceof Error ? error.message : 'Unknown error occurred'}
              </div>
            </div>
          )}

          {transcript && (
            <div className="space-y-4">
              {transcript.messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.speaker === 'agent' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[70%] rounded-lg p-3 ${message.speaker === 'agent'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-900'
                      }`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span className={`text-xs font-medium ${message.speaker === 'agent' ? 'text-blue-100' : 'text-gray-500'
                        }`}>
                        {message.speaker === 'agent' ? 'Agent' : 'Lead'}
                      </span>
                      <div className="flex items-center space-x-1 ml-2">
                        <SentimentEmoji sentiment={message.sentiment} />
                        <span className={`text-xs ${message.speaker === 'agent' ? 'text-blue-100' : 'text-gray-400'
                          }`}>
                          {formatTime(message.timestamp)}
                        </span>
                      </div>
                    </div>
                    <div className="text-sm leading-relaxed">{message.message}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Action Taken Section */}
        {transcript?.actionTaken && (
          <div className="border-t border-gray-200 p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Action Taken</h3>
            <div className="bg-green-50 border border-green-200 rounded-md p-3">
              <p className="text-sm text-green-800">{transcript.actionTaken}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};