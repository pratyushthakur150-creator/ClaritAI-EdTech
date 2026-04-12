import React from 'react';

interface HeatmapData {
  moduleId: string;
  moduleName: string;
  confusionLevel: number;
  studentCount: number;
}

interface ConfusionHeatmapProps {
  heatmap: HeatmapData[];
  isLoading: boolean;
  error: string | null;
}

const ConfusionHeatmap: React.FC<ConfusionHeatmapProps> = ({ heatmap, isLoading, error }) => {
  const getColorByConfusion = (level: number) => {
    if (level <= 25) return 'bg-green-100 border-green-300';
    if (level <= 50) return 'bg-yellow-100 border-yellow-300';
    if (level <= 75) return 'bg-orange-100 border-orange-300';
    return 'bg-red-100 border-red-300';
  };

  const getProgressBarColor = (level: number) => {
    if (level <= 25) return 'bg-green-500';
    if (level <= 50) return 'bg-yellow-500';
    if (level <= 75) return 'bg-orange-500';
    return 'bg-red-500';
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Confusion Heatmap by Module</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-32 bg-gray-200 rounded-lg"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Confusion Heatmap by Module</h3>
        <div className="text-center py-8">
          <div className="text-red-500 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  if (!heatmap || heatmap.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Confusion Heatmap by Module</h3>
        <div className="text-center py-8">
          <div className="text-gray-500 text-sm">No module data available</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Confusion Heatmap by Module</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {heatmap.map((module) => (
          <div
            key={module.moduleId}
            className={`border-2 rounded-lg p-4 transition-transform duration-200 hover:scale-105 ${getColorByConfusion(module.confusionLevel)}`}
          >
            <div className="flex justify-between items-start mb-3">
              <h4 className="text-sm font-medium text-gray-900 truncate flex-1">
                {module.moduleName}
              </h4>
              <span className="text-lg font-bold text-gray-700 ml-2">
                {module.confusionLevel}%
              </span>
            </div>
            
            <div className="mb-3">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Confusion Level</span>
                <span>{module.studentCount} students</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(module.confusionLevel)}`}
                  style={{ width: `${module.confusionLevel}%` }}
                ></div>
              </div>
            </div>
            
            <div className="text-xs text-gray-600">
              {module.studentCount} student{module.studentCount !== 1 ? 's' : ''} showing confusion
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="border-t pt-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Legend</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
            <span>0-25% (Low)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-100 border border-yellow-300 rounded"></div>
            <span>25-50% (Medium)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-orange-100 border border-orange-300 rounded"></div>
            <span>50-75% (High)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-100 border border-red-300 rounded"></div>
            <span>75-100% (Critical)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfusionHeatmap;