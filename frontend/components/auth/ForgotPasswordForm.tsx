'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  EyeIcon, 
  EyeSlashIcon, 
  EnvelopeIcon, 
  LockClosedIcon, 
  ArrowLeftIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline'
import { useAuth } from './AuthProvider'

interface ForgotPasswordFormProps {
  onSuccess: () => void
  onBackToLogin: () => void
}

export default function ForgotPasswordForm({ onSuccess, onBackToLogin }: ForgotPasswordFormProps) {
  const [email, setEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [isSuccess, setIsSuccess] = useState(false)

  const { resetPassword } = useAuth()

  // Password validation
  const passwordRequirements = [
    { text: 'At least 8 characters', met: newPassword.length >= 8 },
    { text: 'Contains a number', met: /\d/.test(newPassword) },
    { text: 'Contains uppercase letter', met: /[A-Z]/.test(newPassword) },
    { text: 'Contains lowercase letter', met: /[a-z]/.test(newPassword) },
  ]

  const isPasswordValid = passwordRequirements.every(req => req.met)
  const passwordsMatch = newPassword === confirmPassword && confirmPassword.length > 0

  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email) {
      setError('Please enter your email address')
      return
    }

    if (!isPasswordValid) {
      setError('Please meet all password requirements')
      return
    }

    if (!passwordsMatch) {
      setError('Passwords do not match')
      return
    }

    setIsLoading(true)

    try {
      const result = await resetPassword(email, newPassword, confirmPassword)
      
      if (result.success) {
        // Show success message instead of redirecting to dashboard
        setIsSuccess(true)
      } else {
        setError(result.error || 'Password reset failed. Please try again.')
      }
    } catch (err) {
      setError('Network error. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const isPasswordFormValid = email.length > 0 && isPasswordValid && passwordsMatch

  // Success Step
  if (isSuccess) {
    return (
      <div className="space-y-6 text-center">
        {/* Success Icon */}
        <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
          <CheckCircleIcon className="h-8 w-8 text-green-600" />
        </div>

        {/* Success Message */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Password Reset Successful!
          </h3>
          <p className="text-sm text-gray-600">
            Your password has been successfully reset for <span className="font-medium">{email}</span>
          </p>
        </div>

        {/* Login Button */}
        <motion.button
          type="button"
          onClick={onBackToLogin}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-200"
        >
          Continue to Sign In
        </motion.button>
      </div>
    )
  }

  return (
    <form onSubmit={handlePasswordReset} className="space-y-6">
      {/* Back Button */}
      <button
        type="button"
        onClick={onBackToLogin}
        className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-800 transition-colors duration-200"
      >
        <ArrowLeftIcon className="h-4 w-4" />
        <span>Back</span>
      </button>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm"
        >
          {error}
        </motion.div>
      )}

      {/* Instructions */}
      <div className="text-center">
        <p className="text-sm text-gray-600 mb-4">
          Enter your email and set a new password
        </p>
      </div>

      {/* Email Field */}
      <div className="space-y-2">
        <label htmlFor="reset-email" className="block text-sm font-medium text-gray-700">
          Email Address
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <EnvelopeIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            id="reset-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white"
            placeholder="Enter your email"
            disabled={isLoading}
          />
        </div>
      </div>

      {/* New Password Field */}
      <div className="space-y-2">
        <label htmlFor="new-password" className="block text-sm font-medium text-gray-700">
          New Password
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <LockClosedIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            id="new-password"
            name="newPassword"
            type={showNewPassword ? 'text' : 'password'}
            autoComplete="new-password"
            required
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white"
            placeholder="Enter new password"
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={() => setShowNewPassword(!showNewPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            disabled={isLoading}
          >
            {showNewPassword ? (
              <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            ) : (
              <EyeIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            )}
          </button>
        </div>

        {/* Password Requirements */}
        {newPassword.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-3 space-y-2"
          >
            {passwordRequirements.map((req, index) => (
              <div key={index} className="flex items-center space-x-2 text-xs">
                <CheckCircleIcon
                  className={`h-4 w-4 ${req.met ? 'text-green-500' : 'text-gray-300'}`}
                />
                <span className={req.met ? 'text-green-600' : 'text-gray-500'}>
                  {req.text}
                </span>
              </div>
            ))}
          </motion.div>
        )}
      </div>

      {/* Confirm Password Field */}
      <div className="space-y-2">
        <label htmlFor="confirm-new-password" className="block text-sm font-medium text-gray-700">
          Confirm New Password
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <LockClosedIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            id="confirm-new-password"
            name="confirmPassword"
            type={showConfirmPassword ? 'text' : 'password'}
            autoComplete="new-password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className={`w-full pl-10 pr-12 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white ${
              confirmPassword.length > 0
                ? passwordsMatch
                  ? 'border-green-300'
                  : 'border-red-300'
                : 'border-gray-300'
            }`}
            placeholder="Confirm new password"
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
            disabled={isLoading}
          >
            {showConfirmPassword ? (
              <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            ) : (
              <EyeIcon className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            )}
          </button>
        </div>

        {/* Password Match Indicator */}
        {confirmPassword.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`text-xs flex items-center space-x-1 ${
              passwordsMatch ? 'text-green-600' : 'text-red-600'
            }`}
          >
            <CheckCircleIcon className="h-4 w-4" />
            <span>
              {passwordsMatch ? 'Passwords match' : 'Passwords do not match'}
            </span>
          </motion.div>
        )}
      </div>

      {/* Submit Button */}
      <motion.button
        type="submit"
        disabled={!isPasswordFormValid || isLoading}
        whileHover={{ scale: isPasswordFormValid && !isLoading ? 1.02 : 1 }}
        whileTap={{ scale: isPasswordFormValid && !isLoading ? 0.98 : 1 }}
        className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-all duration-200 ${
          isPasswordFormValid && !isLoading
            ? 'bg-blue-600 hover:bg-blue-700 shadow-lg hover:shadow-xl'
            : 'bg-gray-300 cursor-not-allowed'
        }`}
      >
        {isLoading ? (
          <div className="flex items-center justify-center">
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            Resetting Password...
          </div>
        ) : (
          'Reset Password'
        )}
      </motion.button>
    </form>
  )
}
