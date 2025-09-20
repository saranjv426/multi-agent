'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { XMarkIcon } from '@heroicons/react/24/outline'
import LoginForm from './LoginForm'
import SignupForm from './SignupForm'
import ForgotPasswordForm from './ForgotPasswordForm'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
  defaultTab?: 'login' | 'signup'
  onSuccess?: () => void
}

type AuthTab = 'login' | 'signup' | 'forgot-password'

export default function AuthModal({ isOpen, onClose, defaultTab = 'login', onSuccess }: AuthModalProps) {
  const [activeTab, setActiveTab] = useState<AuthTab>(defaultTab)

  // Reset to default tab when modal opens
  useEffect(() => {
    if (isOpen) {
      setActiveTab(defaultTab)
    }
  }, [isOpen, defaultTab])

  // Close modal on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  const handleSuccess = () => {
    onClose()
    onSuccess?.()
  }

  const handleSwitchToLogin = () => setActiveTab('login')
  const handleSwitchToSignup = () => setActiveTab('signup')
  const handleSwitchToForgot = () => setActiveTab('forgot-password')

  const modalVariants = {
    hidden: { 
      opacity: 0,
      scale: 0.95,
      y: 20
    },
    visible: { 
      opacity: 1,
      scale: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 30
      }
    },
    exit: { 
      opacity: 0,
      scale: 0.95,
      y: 20,
      transition: {
        duration: 0.2
      }
    }
  }

  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { duration: 0.3 }
    },
    exit: { 
      opacity: 0,
      transition: { duration: 0.3 }
    }
  }

  const getTitle = () => {
    switch (activeTab) {
      case 'login':
        return 'Welcome Back'
      case 'signup':
        return 'Create Account'
      case 'forgot-password':
        return 'Reset Password'
      default:
        return 'Authentication'
    }
  }

  const getSubtitle = () => {
    switch (activeTab) {
      case 'login':
        return 'Sign in to access roof validation tools'
      case 'signup':
        return 'Join thousands of architects and engineers'
      case 'forgot-password':
        return 'Enter your details to reset your password'
      default:
        return ''
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop Overlay */}
          <motion.div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={onClose}
          />

          {/* Modal Container */}
          <motion.div
            className="relative w-full max-w-md mx-4"
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {/* Modal Card */}
            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="relative bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-8 text-white">
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 p-2 rounded-full hover:bg-white/20 transition-colors duration-200"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
                
                <div className="text-center">
                  <motion.h2 
                    className="text-2xl font-bold mb-2"
                    key={activeTab}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    {getTitle()}
                  </motion.h2>
                  <motion.p 
                    className="text-blue-100 text-sm"
                    key={`${activeTab}-subtitle`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.1 }}
                  >
                    {getSubtitle()}
                  </motion.p>
                </div>
              </div>

              {/* Tab Navigation */}
              {activeTab !== 'forgot-password' && (
                <div className="flex border-b border-gray-200">
                  <button
                    onClick={() => setActiveTab('login')}
                    className={`flex-1 px-4 py-3 text-sm font-medium transition-colors duration-200 ${
                      activeTab === 'login'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => setActiveTab('signup')}
                    className={`flex-1 px-4 py-3 text-sm font-medium transition-colors duration-200 ${
                      activeTab === 'signup'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    Sign Up
                  </button>
                </div>
              )}

              {/* Form Content */}
              <div className="p-6">
                <AnimatePresence mode="wait">
                  {activeTab === 'login' && (
                    <motion.div
                      key="login"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.3 }}
                    >
                      <LoginForm 
                        onSuccess={handleSuccess}
                        onSwitchToSignup={handleSwitchToSignup}
                        onSwitchToForgot={handleSwitchToForgot}
                      />
                    </motion.div>
                  )}

                  {activeTab === 'signup' && (
                    <motion.div
                      key="signup"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.3 }}
                    >
                      <SignupForm 
                        onSuccess={handleSuccess}
                        onSwitchToLogin={handleSwitchToLogin}
                      />
                    </motion.div>
                  )}

                  {activeTab === 'forgot-password' && (
                    <motion.div
                      key="forgot-password"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.3 }}
                    >
                      <ForgotPasswordForm 
                        onSuccess={handleSuccess}
                        onBackToLogin={handleSwitchToLogin}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}