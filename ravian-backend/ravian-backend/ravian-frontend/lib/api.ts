import axios, { AxiosError, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

// Create axios instance with default config
// Set NEXT_PUBLIC_API_URL in .env.local (e.g. http://127.0.0.1:8001) if your backend runs on a different port
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001',
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Flag to avoid multiple parallel refresh calls
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

const normalizeStoredToken = (value: string | null): string | null => {
  if (!value) return null;
  const trimmed = value.trim();
  // Sometimes tokens get stored with quotes accidentally.
  const unquoted = trimmed.startsWith('"') && trimmed.endsWith('"')
    ? trimmed.slice(1, -1)
    : trimmed;
  return unquoted.trim() || null;
};

const isLikelyJwt = (token: string): boolean => {
  // Basic JWT shape check: 3 base64url-ish segments separated by dots.
  return /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(token);
};

const performTokenRefresh = async (): Promise<string | null> => {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      if (typeof window === 'undefined') return null;
      const refreshToken = normalizeStoredToken(localStorage.getItem('refresh_token'));
      if (!refreshToken) return null;
      if (!isLikelyJwt(refreshToken)) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return null;
      }

      const { data } = await axios.post(
        `${apiClient.defaults.baseURL || ''}/api/v1/auth/refresh`,
        null,
        {
          params: { refresh_token: refreshToken },
        },
      );

      const newAccessToken = data.access_token as string | undefined;
      const newRefreshToken = data.refresh_token as string | undefined;

      if (newAccessToken) {
        localStorage.setItem('access_token', newAccessToken);
      }
      if (newRefreshToken) {
        localStorage.setItem('refresh_token', newRefreshToken);
      }

      return newAccessToken ?? null;
    } catch (err) {
      console.error('❌ Token refresh failed:', err);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
      return null;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Don't add Authorization to OPTIONS requests (CORS preflight - browser sends these)
    if (config.method?.toUpperCase() === 'OPTIONS') {
      return config;
    }
    // Always sanitize Authorization header (some components set it manually)
    if (config.headers && (config.headers as any).Authorization) {
      delete (config.headers as any).Authorization;
    }

    // Add auth token from localStorage
    if (typeof window !== 'undefined') {
      const token = normalizeStoredToken(localStorage.getItem('access_token'));
      if (token && !isLikelyJwt(token)) {
        // Corrupted/invalid token stored; clear and proceed unauthenticated.
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return config;
      }
      if (token && config.headers) {
        (config.headers as any).Authorization = `Bearer ${token}`;
      }
    }

    // Log request in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }

    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful response in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error: AxiosError) => {
    // Handle different types of errors
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = error.response.data || 'An error occurred';
      const originalRequest = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;

      switch (status) {
        case 401: {
          // Attempt refresh once before forcing logout
          if (originalRequest && !originalRequest._retry) {
            originalRequest._retry = true;
            return performTokenRefresh().then((newToken) => {
              if (newToken && originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return apiClient(originalRequest);
              }

              if (typeof window !== 'undefined') {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
              }
              return Promise.reject(error);
            });
          }

          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
          break;
        }

        case 403:
          // Forbidden - user doesn't have permission
          console.error('❌ Access denied:', message);
          break;

        case 404:
          // Not found
          console.error('❌ Resource not found:', error.config?.url);
          break;

        case 422:
          // Validation error
          console.error('❌ Validation error:', message);
          break;

        case 429:
          // Rate limiting
          console.error('❌ Too many requests. Please try again later.');
          break;

        case 500:
        case 502:
        case 503:
        case 504:
          // Server errors
          console.error('❌ Server error:', status, message);
          break;

        default:
          console.error(`❌ HTTP ${status}:`, message);
      }
    } else if (error.request) {
      // Network error - no response received
      console.error('❌ Network error:', error.message);

      // Check if it's a timeout
      if (error.code === 'ECONNABORTED') {
        console.error('❌ Request timeout. Please check your connection.');
      }
    } else {
      // Something else happened
      console.error('❌ Request setup error:', error.message);
    }

    return Promise.reject(error);
  }
);

// Helper function to handle file uploads
export const uploadFile = async (
  url: string,
  file: File,
  onProgress?: (progress: number) => void
): Promise<AxiosResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  return apiClient.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
};

// Helper function for retrying failed requests
export const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
      }
    }
  }

  throw lastError;
};

export default apiClient;
