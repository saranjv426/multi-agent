/**
 * API utility functions with automatic authentication handling
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

interface ApiResponse<T = any> {
  data?: T
  error?: string
  status: number
}

/**
 * Enhanced fetch function that handles authentication errors automatically
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = localStorage.getItem('access_token')
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`
  }
  
  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config)
    
    // Handle 401 errors globally
    if (response.status === 401) {
      console.log('🔄 401 error detected, dispatching auth error event')
      window.dispatchEvent(new CustomEvent('api-error', {
        detail: { status: 401, endpoint }
      }))
      
      return {
        error: 'Authentication expired. Please log in again.',
        status: 401
      }
    }
    
    let data: T | undefined
    const contentType = response.headers.get('content-type')
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json()
    } else {
      data = await response.text() as unknown as T
    }
    
    if (!response.ok) {
      return {
        error: (data as any)?.error || (data as any)?.detail || `HTTP ${response.status}`,
        status: response.status
      }
    }
    
    return {
      data,
      status: response.status
    }
    
  } catch (error) {
    console.error('API request failed:', error)
    return {
      error: 'Network error. Please check your connection.',
      status: 0
    }
  }
}

/**
 * Convenience methods for common HTTP methods
 */
export const api = {
  get: <T = any>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),
    
  post: <T = any>(endpoint: string, body?: any, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
    
  put: <T = any>(endpoint: string, body?: any, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),
    
  delete: <T = any>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
}
