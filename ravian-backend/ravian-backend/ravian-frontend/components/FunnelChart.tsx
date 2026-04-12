import React from 'react';
import type { FunnelStage, FunnelChartProps } from '@/types/funnel';

export default function FunnelChart({ stages }: FunnelChartProps) {
  const maxCount = stages.length > 0 ? stages[0].count : 1;

  if (!stages.length) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Conversion Funnel</h2>
        <div className="text-center text-gray-500 py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-lg font-medium">No funnel data available</p>
          <p className="text-sm mt-1">Data will appear here once available for the selected period.</p>
        </div>
      </div>
    );
  }

  const getStageColor = (index: number) => {
    const colors = [
      'bg-blue-500',
      'bg-indigo-500', 
      'bg-purple-500',
      'bg-pink-500',
      'bg-red-500',
      'bg-orange-500'
    ];
    return colors[index % colors.length];
  };

  const getDropoffRate = (currentIndex: number): number => {
    if (currentIndex === 0) return 0;
    const previousStage = stages[currentIndex - 1];
    const currentStage = stages[currentIndex];
    if (previousStage.count === 0) return 0;
    return Math.round(((previousStage.count - currentStage.count) / previousStage.count) * 100);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
      <h2 className="text-xl font-semibold text-gray-900 mb-8">Conversion Funnel</h2>
      
      <div className="space-y-6">
        {stages.map((stage, index) => (
          <div key={stage.label} className="relative">
            {/* Stage Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${getStageColor(index)}`}></div>
                <span className="text-sm font-medium text-gray-900">{stage.label}</span>
              </div>
              <div className="text-right">
                <span className="text-lg font-semibold text-gray-900">
                  {stage.count.toLocaleString()}
                </span>
                {index > 0 && (
                  <div className="flex items-center space-x-2 mt-1">
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                      {stage.percentage}% converted
                    </span>
                    <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
                      {getDropoffRate(index)}% dropped
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="relative h-10 bg-gray-100 rounded-lg overflow-hidden">
              <div
                className={`absolute h-full ${getStageColor(index)} transition-all duration-700 ease-in-out rounded-lg`}
                style={{ width: `${(stage.count / maxCount) * 100}%` }}
              />
              <div className="absolute inset-0 flex items-center px-4">
                <span className="text-sm font-medium text-white drop-shadow-sm">
                  {Math.round((stage.count / maxCount) * 100)}% of total traffic
                </span>
              </div>
            </div>

            {/* Conversion Arrow */}
            {index < stages.length - 1 && (
              <div className="flex justify-center my-4">
                <div className="flex flex-col items-center">
                  <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                    </svg>
                  </div>
                  <span className="text-xs text-gray-500 mt-1">
                    {((stages[index + 1].count / stage.count) * 100).toFixed(1)}% continue
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Summary Statistics */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Funnel Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
            <div className="text-2xl font-bold text-indigo-900">
              {stages.length > 0 ? stages[0].count.toLocaleString() : '0'}
            </div>
            <div className="text-sm text-indigo-700">Top of Funnel</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
            <div className="text-2xl font-bold text-emerald-900">
              {stages.length > 0 ? stages[stages.length - 1].count.toLocaleString() : '0'}
            </div>
            <div className="text-sm text-emerald-700">Bottom of Funnel</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
            <div className="text-2xl font-bold text-pink-900">
              {stages.length > 1 ? 
                ((stages[stages.length - 1].count / stages[0].count) * 100).toFixed(1) : '0'}%
            </div>
            <div className="text-sm text-pink-700">Overall Conversion</div>
          </div>
          <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-900">
              {stages.reduce((total, stage) => total + stage.count, 0).toLocaleString()}
            </div>
            <div className="text-sm text-red-700">Total Volume</div>
          </div>
        </div>
      </div>

      {/* Best Performing Stage */}
      {stages.length > 1 && (
        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h4 className="text-sm font-semibold text-yellow-800 mb-2">💡 Optimization Insight</h4>
          <p className="text-sm text-yellow-700">
            {(() => {
              const conversions = stages.slice(1).map((stage, idx) => ({
                stage: stage.label,
                rate: stage.percentage
              }));
              const bestStage = conversions.reduce((best, current) => 
                current.rate > best.rate ? current : best
              );
              const worstStage = conversions.reduce((worst, current) => 
                current.rate < worst.rate ? current : worst
              );
              return `Best conversion: ${bestStage.stage} (${bestStage.rate}%). Focus on improving ${worstStage.stage} (${worstStage.rate}%) for maximum impact.`;
            })()}
          </p>
        </div>
      )}
    </div>
  );
}