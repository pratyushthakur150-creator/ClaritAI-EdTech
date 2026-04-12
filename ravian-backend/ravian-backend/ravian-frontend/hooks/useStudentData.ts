import { useQuery } from '@tanstack/react-query';

// TypeScript interfaces
interface Confusion {
  id: string;
  topic: string;
  module: string;
  count: number;
  lastOccurred: string;
}

interface RiskStudent {
  id: string;
  name: string;
  course: string;
  riskLevel: 'High Risk' | 'Medium Risk' | 'Low Risk';
  modulesBehind: number;
  attendance: number;
  lastActive: string;
}

interface HeatmapData {
  moduleId: string;
  moduleName: string;
  confusionLevel: number;
  studentCount: number;
}

interface StudentDataResponse {
  confusions: Confusion[];
  riskStudents: RiskStudent[];
  heatmap: HeatmapData[];
}

const fetchStudentData = async (courseFilter?: string): Promise<StudentDataResponse> => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
  const params = new URLSearchParams();
  
  if (courseFilter && courseFilter !== 'all') {
    params.append('course', courseFilter);
  }

  const queryString = params.toString();
  const urlSuffix = queryString ? `?${queryString}` : '';
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const headers: HeadersInit = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  // Fetch data from all three endpoints in parallel (using full backend URL with /api/v1/ prefix)
  const [confusionsResponse, riskStudentsResponse, heatmapResponse] = await Promise.all([
    fetch(`${baseUrl}/api/v1/students/confusion${urlSuffix}`, { headers, credentials: 'include' }),
    fetch(`${baseUrl}/api/v1/students/risk${urlSuffix}`, { headers, credentials: 'include' }),
    fetch(`${baseUrl}/api/v1/students/heatmap${urlSuffix}`, { headers, credentials: 'include' }),
  ]);

  // Check if all responses are ok
  if (!confusionsResponse.ok) {
    throw new Error(`Failed to fetch confusion data: ${confusionsResponse.statusText}`);
  }
  if (!riskStudentsResponse.ok) {
    throw new Error(`Failed to fetch risk students data: ${riskStudentsResponse.statusText}`);
  }
  if (!heatmapResponse.ok) {
    throw new Error(`Failed to fetch heatmap data: ${heatmapResponse.statusText}`);
  }

  // Parse JSON responses
  const [confusions, riskStudents, heatmap] = await Promise.all([
    confusionsResponse.json(),
    riskStudentsResponse.json(),
    heatmapResponse.json()
  ]);

  return {
    confusions: confusions.data || [],
    riskStudents: riskStudents.data || [],
    heatmap: heatmap.data || []
  };
};

export const useStudentData = (courseFilter?: string) => {
  return useQuery({
    queryKey: ['studentData', courseFilter],
    queryFn: () => fetchStudentData(courseFilter),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
};

export type { Confusion, RiskStudent, HeatmapData, StudentDataResponse };