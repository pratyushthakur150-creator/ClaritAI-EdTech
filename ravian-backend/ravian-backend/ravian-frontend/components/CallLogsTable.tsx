import React, { useState } from 'react';
import { OutcomeBadge } from './OutcomeBadge';
import { SentimentEmoji } from './SentimentEmoji';
import { TranscriptModal } from './TranscriptModal';
import { useCallLogs } from '@/hooks/useCallLogs';

interface CallLog {
  id: string;
  leadName: string;
  course: string;
  timestamp: string;
  duration: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  outcome: 'demo_booked' | 'callback' | 'not_interested' | 'voicemail' | 'no_answer' | 'information_provided';
}

interface CallLogsTableProps {
  sentimentFilter?: 'positive' | 'neutral' | 'negative';
}

export const CallLogsTable: React.FC<CallLogsTableProps> = ({ sentimentFilter }) => {
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
  const { data: callLogs, isLoading, error } = useCallLogs(sentimentFilter);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        Error loading call logs: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }

  if (!callLogs || callLogs.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 text-lg mb-2">📞</div>
        <div className="text-gray-600 font-medium">No calls found</div>
        <div className="text-gray-400 text-sm">Call logs will appear here once available</div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Lead Name</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Course</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Time</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Duration</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Sentiment</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {callLogs.map((call) => (
                <tr
                  key={call.id}
                  onClick={() => setSelectedCallId(call.id)}
                  className="hover:bg-gray-50 cursor-pointer transition-colors duration-150"
                >
                  <td className="py-3 px-4 text-gray-900 font-medium">{call.leadName}</td>
                  <td className="py-3 px-4 text-gray-600">{call.course}</td>
                  <td className="py-3 px-4 text-gray-600">{formatTime(call.timestamp)}</td>
                  <td className="py-3 px-4 text-gray-600">{formatDuration(call.duration)}</td>
                  <td className="py-3 px-4">
                    <SentimentEmoji sentiment={call.sentiment} />
                  </td>
                  <td className="py-3 px-4">
                    <OutcomeBadge outcome={call.outcome} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedCallId && (
        <TranscriptModal
          callId={selectedCallId}
          onClose={() => setSelectedCallId(null)}
        />
      )}
    </>
  );
};