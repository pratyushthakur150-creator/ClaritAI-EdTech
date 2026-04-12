import { formatTime } from '@/lib/utils';
import type { Insight } from '@/hooks/useInsights';
import { useState } from 'react';

interface InsightCardProps {
  insight: Insight;
}

const typeConfig = {
  opportunity: {
    icon: '🚀',
    color: 'border-l-emerald-500 bg-gradient-to-r from-emerald-50 to-green-50',
    badgeColor: 'bg-emerald-100 text-emerald-800',
    iconBg: 'bg-emerald-500'
  },
  warning: {
    icon: '⚠️',
    color: 'border-l-red-500 bg-gradient-to-r from-red-50 to-pink-50',
    badgeColor: 'bg-red-100 text-red-800',
    iconBg: 'bg-red-500'
  },
  recommendation: {
    icon: '💡',
    color: 'border-l-blue-500 bg-gradient-to-r from-blue-50 to-indigo-50',
    badgeColor: 'bg-blue-100 text-blue-800',
    iconBg: 'bg-blue-500'
  },
  trend: {
    icon: '📈',
    color: 'border-l-purple-500 bg-gradient-to-r from-purple-50 to-indigo-50',
    badgeColor: 'bg-purple-100 text-purple-800',
    iconBg: 'bg-purple-500'
  }
};

const priorityConfig = {
  high: {
    color: 'bg-red-100 text-red-800 border border-red-200',
    icon: '🔥',
    pulse: 'animate-pulse'
  },
  medium: {
    color: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
    icon: '⚡',
    pulse: ''
  },
  low: {
    color: 'bg-green-100 text-green-800 border border-green-200',
    icon: '✅',
    pulse: ''
  }
};

export default function InsightCard({ insight }: InsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const typeStyle = typeConfig[insight.type];
  const priorityStyle = priorityConfig[insight.priority];

  const formatRelativeTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return `${Math.floor(diffInHours / 24)}d ago`;
    }
  };

  const getImpactColor = (score: number) => {
    if (score >= 8) return 'text-red-600 bg-red-50';
    if (score >= 6) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 border-l-4 ${typeStyle.color} hover:shadow-md transition-all duration-200 overflow-hidden`}>
      {/* Header */}
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-4 flex-1">
            <div className={`p-3 rounded-full ${typeStyle.iconBg} text-white text-xl flex-shrink-0`}>
              {typeStyle.icon}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-900 leading-tight">
                  {insight.title}
                </h3>
              </div>

              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${priorityStyle.color} ${priorityStyle.pulse}`}>
                  <span>{priorityStyle.icon}</span>
                  {insight.priority.toUpperCase()} PRIORITY
                </span>

                <span className={`px-2 py-1 text-xs font-medium rounded-full ${typeStyle.badgeColor}`}>
                  {insight.type.charAt(0).toUpperCase() + insight.type.slice(1)}
                </span>

                <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full">
                  {insight.category}
                </span>

                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {formatRelativeTime(insight.timestamp)}
                </span>
              </div>

              <p className="text-gray-700 leading-relaxed mb-4">
                {insight.description}
              </p>

              {/* Metrics */}
              {insight.metrics && (
                <div className="flex items-center gap-4 mb-4">
                  <div className={`px-3 py-1 rounded-lg text-sm font-medium ${getImpactColor(insight.metrics.impact_score)}`}>
                    <span className="text-xs text-gray-600">Impact: </span>
                    <span className="font-bold">{insight.metrics.impact_score}/10</span>
                  </div>
                  <div className={`px-3 py-1 rounded-lg text-sm font-medium ${getConfidenceColor(insight.metrics.confidence)}`}>
                    <span className="text-xs text-gray-600">Confidence: </span>
                    <span className="font-bold">{Math.round(insight.metrics.confidence * 100)}%</span>
                  </div>
                </div>
              )}

              {/* Action Items */}
              {insight.action_items && insight.action_items.length > 0 && (
                <div className="border-t border-gray-100 pt-4">
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center gap-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 mb-3"
                  >
                    <span>Recommended Actions ({insight.action_items.length})</span>
                    <svg
                      className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {isExpanded && (
                    <div className="space-y-2 animate-fade-in">
                      {insight.action_items.map((action, index) => (
                        <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                          <div className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-xs font-medium">
                            {index + 1}
                          </div>
                          <span className="text-sm text-gray-700 leading-relaxed">{action}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 ml-4">
            <button
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Mark as read"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
            <button
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Dismiss"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Add fade-in animation to Tailwind config if not present
if (typeof window !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fade-in {
      from { opacity: 0; transform: translateY(-10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .animate-fade-in {
      animation: fade-in 0.2s ease-out;
    }
  `;
  document.head.appendChild(style);
}
