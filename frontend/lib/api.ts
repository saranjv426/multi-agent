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
  options: RequestInit & { responseType?: 'json' | 'text' | 'blob' } = {}
): Promise<ApiResponse<T>> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

  const bodyIsFormData = typeof FormData !== 'undefined' && options.body instanceof FormData

  const defaultHeaders: HeadersInit = {}
  // Only set JSON Content-Type if we're not sending FormData and caller didn't set it
  if (!bodyIsFormData) {
    (defaultHeaders as any)['Content-Type'] = (options.headers as any)?.['Content-Type'] ?? 'application/json'
  }

  if (token) {
    (defaultHeaders as any)['Authorization'] = `Bearer ${token}`
  }

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {}),
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
    const { responseType } = options as any
    const contentType = response.headers.get('content-type') || ''

    if (responseType === 'blob') {
      data = (await response.blob()) as unknown as T
    } else if (responseType === 'text') {
      data = (await response.text()) as unknown as T
    } else if (contentType.includes('application/json')) {
      data = await response.json()
    } else {
      // Default to text when content type is unknown
      data = (await response.text()) as unknown as T
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
  get: <T = any>(endpoint: string, options?: RequestInit & { responseType?: 'json' | 'text' | 'blob' }) =>
    apiRequest<T>(endpoint, { ...(options || {}), method: 'GET' }),
    
  post: <T = any>(endpoint: string, body?: any, options?: RequestInit & { responseType?: 'json' | 'text' | 'blob' }) =>
    apiRequest<T>(endpoint, {
      ...(options || {}),
      method: 'POST',
      // If body is FormData, pass as-is; otherwise JSON.stringify
      body: body instanceof FormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
    }),
    
  put: <T = any>(endpoint: string, body?: any, options?: RequestInit & { responseType?: 'json' | 'text' | 'blob' }) =>
    apiRequest<T>(endpoint, {
      ...(options || {}),
      method: 'PUT',
      body: body instanceof FormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
    }),
    
  delete: <T = any>(endpoint: string, options?: RequestInit & { responseType?: 'json' | 'text' | 'blob' }) =>
    apiRequest<T>(endpoint, { ...(options || {}), method: 'DELETE' }),
}
