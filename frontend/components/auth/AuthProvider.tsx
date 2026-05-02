'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface User {
  id: string
  email: string
  created_at: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  signup: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  logout: () => void
  resetPassword: (email: string, newPassword: string, confirmPassword: string) => Promise<{ success: boolean; error?: string }>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

const getFriendlyNetworkError = (error: unknown) => {
  if (error instanceof Error && error.name === 'TypeError') {
    return `Cannot reach the backend at ${API_BASE_URL}. Make sure the API server is running.`
  }
  return 'Network error. Please try again.'
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Helper function to handle token validation
  const validateToken = async (token: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.status === 401) {
        // Token is invalid or expired
        return false
      }
      
      if (!response.ok) {
        return false
      }
      
      const data = await response.json()
      if (data.user) {
        setUser(data.user)
        return true
      }
      
      return false
    } catch (error) {
      console.error('Token validation failed:', error)
      return false
    }
  }

  // Helper function to clear auth state
  const clearAuthState = () => {
    localStorage.removeItem('access_token')
    setUser(null)
  }

  // Check if user is already logged in on app start
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      validateToken(token).then(isValid => {
        if (!isValid) {
          clearAuthState()
        }
        setIsLoading(false)
      })
    } else {
      setIsLoading(false)
    }
  }, [])

  // Add global error handler for 401 responses
  useEffect(() => {
    const handleApiError = (event: Event) => {
      const customEvent = event as CustomEvent
      if (customEvent.detail?.status === 401) {
        console.log('🔄 401 error detected, logging out user')
        clearAuthState()
        // Optionally show a toast notification
        if (typeof window !== 'undefined' && window.dispatchEvent) {
          window.dispatchEvent(new CustomEvent('auth-expired'))
        }
      }
    }

    // Listen for API errors
    window.addEventListener('api-error', handleApiError)
    
    return () => {
      window.removeEventListener('api-error', handleApiError)
    }
  }, [])

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (data.success && data.access_token) {
        localStorage.setItem('access_token', data.access_token)
        setUser(data.user)
        return { success: true }
      } else {
        return { success: false, error: data.error || data.detail || 'Login failed' }
      }
    } catch (error) {
      return { success: false, error: getFriendlyNetworkError(error) }
    }
  }

  const signup = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (data.success && data.access_token) {
        localStorage.setItem('access_token', data.access_token)
        setUser(data.user)
        return { success: true }
      } else {
        return { success: false, error: data.error || data.detail || 'Signup failed' }
      }
    } catch (error) {
      return { success: false, error: getFriendlyNetworkError(error) }
    }
  }

  const logout = () => {
    clearAuthState()
  }

  const resetPassword = async (email: string, newPassword: string, confirmPassword: string): Promise<{ success: boolean; error?: string }> => {
    if (newPassword !== confirmPassword) {
      return { success: false, error: 'Passwords do not match' }
    }

    if (newPassword.length < 8) {
      return { success: false, error: 'Password must be at least 8 characters long' }
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          new_password: newPassword,
        }),
      })

      const data = await response.json()

      if (response.ok && data.success) {
        return { success: true }
      }

      return { success: false, error: data.error || data.detail || 'Password reset failed' }
    } catch (error) {
      return { success: false, error: 'Password reset failed. Please try again.' }
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    signup,
    logout,
    resetPassword,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
