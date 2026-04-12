import React from 'react';

interface Confusion {
  id: string;
  topic: string;
  module: string;
  count: number;
  lastOccurred: string;
}

interface TopConfusionsProps {
  confusions: Confusion[];
  isLoading: boolean;
  error: string | null;
}

const TopConfusions: React.FC<TopConfusionsProps> = ({ confusions, isLoading, error }) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Top Student Confusions</h3>
        <div className="animate-pulse space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Top Student Confusions</h3>
        <div className="text-center py-8">
          <div className="text-red-500 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  if (!confusions || confusions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Top Student Confusions</h3>
        <div className="text-center py-8">
          <div className="text-green-600 text-sm font-medium">
            🎉 Great news! No major confusion topics detected.
          </div>
          <div className="text-gray-500 text-xs mt-1">
            Students are doing well with the current material.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Top Student Confusions</h3>
      <div className="space-y-3">
        {confusions.map((confusion, index) => (
          <div
            key={confusion.id}
            className="border rounded-lg p-4 hover:shadow-md transition-shadow duration-200 hover:bg-gray-50"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-3 flex-1">
                <div className="flex-shrink-0 w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-xs font-bold">
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {confusion.topic}
                  </h4>
                  <p className="text-xs text-gray-500 mt-1">
                    Module: {confusion.module}
                  </p>
                </div>
              </div>
              <div className="flex-shrink-0 text-right">
                <div className="text-sm font-medium text-red-600">
                  {confusion.count} students
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Last: {new Date(confusion.lastOccurred).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopConfusions;