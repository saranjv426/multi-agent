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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Check if user is already logged in on app start
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      // Verify token with backend
      fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(res => res.json())
      .then(data => {
        if (data.user) {
          setUser(data.user)
        } else {
          localStorage.removeItem('access_token')
        }
      })
      .catch(() => {
        localStorage.removeItem('access_token')
      })
      .finally(() => {
        setIsLoading(false)
      })
    } else {
      setIsLoading(false)
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
      return { success: false, error: 'Network error. Please try again.' }
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
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    setUser(null)
  }

  const resetPassword = async (email: string, newPassword: string, confirmPassword: string): Promise<{ success: boolean; error?: string }> => {
    // For now, this is a simplified reset without email verification
    // In a real app, this would involve email verification
    
    if (newPassword !== confirmPassword) {
      return { success: false, error: 'Passwords do not match' }
    }

    if (newPassword.length < 8) {
      return { success: false, error: 'Password must be at least 8 characters long' }
    }

    try {
      // For now, we'll simulate a password reset
      // In real implementation, this would use the actual backend endpoint
      return { success: true }
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