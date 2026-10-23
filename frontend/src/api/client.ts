import type { ApiErrorResponse } from '../types/auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Safely extract cookie value by name from document.cookie.
 * Used exclusively for non-HttpOnly cookies such as 'csrf_token'.
 */
export function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'));
  return match ? decodeURIComponent(match[3]) : null;
}

export class ApiError extends Error {
  status: number;
  data: ApiErrorResponse;

  constructor(status: number, data: ApiErrorResponse) {
    super(data.error || 'An unexpected API error occurred');
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Main HTTP client wrapper around native fetch:
 * - Always includes credentials for HttpOnly cookie authentication
 * - Automatically attaches X-CSRF-Token header to state-changing requests
 * - Parses structured JSON error payloads
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const method = (options.method || 'GET').toUpperCase();

  const headers = new Headers(options.headers || {});
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Attach Double-Submit CSRF token for state-changing requests
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrfToken = getCookie('csrf_token');
    if (csrfToken && !headers.has('X-CSRF-Token')) {
      headers.set('X-CSRF-Token', csrfToken);
    }
  }

  const response = await fetch(url, {
    ...options,
    method,
    headers,
    credentials: 'include', // Ensure cookies are sent and received
  });

  if (!response.ok) {
    let errorData: ApiErrorResponse;
    try {
      errorData = await response.json();
    } catch {
      errorData = {
        error: response.statusText || 'Request failed',
        code: `HTTP_${response.status}`,
      };
    }
    throw new ApiError(response.status, errorData);
  }

  // Handle empty responses (such as 204 No Content)
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}
