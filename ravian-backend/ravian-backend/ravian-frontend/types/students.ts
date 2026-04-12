// Student Intelligence TypeScript Interface Definitions
// Defines all types and interfaces for student data, confusion analysis, and risk assessment

export interface Confusion {
  topic: string;
  module: string;
  confusion_count: number;
  last_occurred: string; // ISO date string
}

export interface RiskStudent {
  id: string;
  name: string;
  course: string;
  risk_score: number; // Risk score (0-100 scale)
  last_active: string; // ISO date string
  modules_behind: number;
  attendance_rate: number; // Attendance rate as percentage (0-100)
}

export interface ModuleConfusion {
  module_name: string;
  confusion_level: number; // Confusion level as percentage (0-100)
  student_count: number;
}

export interface StudentDataResponse {
  confusions: Confusion[];
  riskStudents: RiskStudent[];
  heatmap: ModuleConfusion[];
}

// Additional utility types for Student Intelligence
export type RiskLevel = 'High' | 'Medium' | 'Low';

export interface StudentFilter {
  course?: string;
  risk_level?: RiskLevel;
  modules_behind_threshold?: number;
}

export interface ConfusionStats {
  total_topics: number;
  most_confused_module: string;
  average_confusion_count: number;
}

export interface RiskStats {
  total_at_risk: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
}

export interface HeatmapStats {
  most_confused_module: string;
  least_confused_module: string;
  average_confusion_level: number;
}
