'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import toast from 'react-hot-toast'
import {
  CloudArrowUpIcon,
  DocumentIcon,
  XMarkIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowLeftIcon,
  DocumentArrowDownIcon,
  EyeIcon,
  ClockIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'
import axios from 'axios'

interface UploadInterfaceProps {
  onBack: () => void
}

interface ValidationResult {
  analysis: string
  validation_report: string
  compliance_report?: string
  parsed_report: any
  estimated_cost: number
  processing_time: number
  success: boolean
  error?: string
}

interface AnalysisStep {
  id: string
  title: string
  description: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  icon: React.ComponentType<any>
}

export default function UploadInterface({ onBack }: UploadInterfaceProps) {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [showResults, setShowResults] = useState(false)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  // Always use optimized mode - removed toggle for simplicity

  const analysisSteps: AnalysisStep[] = [
    {
      id: 'upload',
      title: 'Image Processing',
      description: 'Preparing your design file for analysis',
      status: 'pending',
      icon: CloudArrowUpIcon
    },
    {
      id: 'analysis',
      title: 'AI Design Analysis',
      description: 'Extracting structural specifications',
      status: 'pending', 
      icon: EyeIcon
    },
    {
      id: 'validation',
      title: 'Code Validation',
      description: 'Checking compliance against Florida Building Code',
      status: 'pending',
      icon: ShieldCheckIcon
    },
    {
      id: 'report',
      title: 'Report Generation',
      description: 'Creating your compliance report',
      status: 'pending',
      icon: DocumentIcon
    }
  ]

  const [steps, setSteps] = useState(analysisSteps)

  const updateStepStatus = (stepIndex: number, status: AnalysisStep['status']) => {
    setSteps(prev => prev.map((step, index) => 
      index === stepIndex ? { ...step, status } : step
    ))
  }

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
      if (!allowedTypes.includes(file.type)) {
        toast.error('Please upload an image (PNG, JPG, GIF) or PDF file')
        return
      }
      
      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File size must be less than 10MB')
        return
      }
      
      // Create image preview for display
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (e) => {
          setImagePreview(e.target?.result as string)
        }
        reader.readAsDataURL(file)
      } else {
        setImagePreview(null) // PDF files won't show preview
      }
      
      setUploadedFile(file)
      setShowResults(false)
      setValidationResult(null)
      setSteps(analysisSteps) // Reset steps
      toast.success('File uploaded successfully!')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
      'application/pdf': ['.pdf']
    },
    multiple: false
  })

  const handleValidation = async () => {
    if (!uploadedFile) {
      toast.error('Please upload a file first')
      return
    }

    setIsProcessing(true)
    setCurrentStep(0)
    
    try {
      // Step 1: Upload Processing
      updateStepStatus(0, 'processing')
      await new Promise(resolve => setTimeout(resolve, 1000))
      updateStepStatus(0, 'completed')
      setCurrentStep(1)

      // Step 2: AI Analysis
      updateStepStatus(1, 'processing')
      const formData = new FormData()
      formData.append('file', uploadedFile)
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/validation/validate-optimized`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 60000, // 60 second timeout
        }
      )
      
      updateStepStatus(1, 'completed')
      setCurrentStep(2)
      
      // Step 3: Validation
      updateStepStatus(2, 'processing')
      await new Promise(resolve => setTimeout(resolve, 1500))
      updateStepStatus(2, 'completed')
      setCurrentStep(3)
      
      // Step 4: Report Generation
      updateStepStatus(3, 'processing')
      await new Promise(resolve => setTimeout(resolve, 1000))
      updateStepStatus(3, 'completed')
      
      setValidationResult(response.data)
      setShowResults(true)
      toast.success('Validation completed successfully!')
      
    } catch (error: any) {
      console.error('Validation error:', error)
      updateStepStatus(currentStep, 'error')
      
      const errorMessage = error.response?.data?.detail || 
                          error.message || 
                          'An error occurred during validation'
      toast.error(errorMessage)
    } finally {
      setIsProcessing(false)
    }
  }

  const removeFile = () => {
    setUploadedFile(null)
    setValidationResult(null)
    setShowResults(false)
    setImagePreview(null)
    setSteps(analysisSteps)
  }

  // Extract overall compliance status from validation report
  const getComplianceStatus = (report: string): string => {
    if (!report) return 'Unknown'
    
    // Look for overall status patterns
    const statusPatterns = [
      /STATUS:\s*(COMPLIANT|NON-COMPLIANT|REVIEW|PENDING)/i,
      /OVERALL:\s*(COMPLIANT|NON-COMPLIANT|REVIEW|PENDING)/i,
      /COMPLIANCE:\s*(COMPLIANT|NON-COMPLIANT|REVIEW|PENDING)/i,
      /RESULT:\s*(COMPLIANT|NON-COMPLIANT|REVIEW|PENDING)/i
    ]
    
    for (const pattern of statusPatterns) {
      const match = report.match(pattern)
      if (match) {
        return match[1].toUpperCase()
      }
    }
    
    // Fallback: check if report contains compliance indicators
    if (report.includes('COMPLIANT') && !report.includes('NON-COMPLIANT')) {
      return 'COMPLIANT'
    } else if (report.includes('NON-COMPLIANT')) {
      return 'NON-COMPLIANT'
    } else if (report.includes('REVIEW')) {
      return 'REVIEW REQUIRED'
    }
    
    return 'ANALYSIS COMPLETE'
  }

  const downloadReport = () => {
    if (validationResult) {
      // Get the validation report content
      const reportContent = validationResult.validation_report || 
                           validationResult.compliance_report || 
                           JSON.stringify(validationResult, null, 2)
      
      // Create and download report
      const blob = new Blob([reportContent], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `roof-validation-report-${Date.now()}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('Report downloaded!')
    }
  }

  return (
    <div className="min-h-screen py-4">
      <div className="container mx-auto px-4 max-w-[1770px]">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={onBack}
            className="inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeftIcon className="h-5 w-5" />
            <span>Back to Home</span>
          </button>
          
          <h1 className="text-2xl font-bold text-gray-900">Roof Design Validation</h1>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 min-h-[calc(100vh-200px)]">
          {/* Upload Section */}
          <div className="space-y-4 h-full">
            <motion.div
              className="card"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Design File</h2>
              
              {!uploadedFile ? (
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all duration-200 ${
                    isDragActive 
                      ? 'border-primary-500 bg-primary-50' 
                      : 'border-gray-300 bg-gray-50 hover:border-primary-400 hover:bg-primary-25'
                  }`}
                >
                  <input {...getInputProps()} />
                  <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  
                  {isDragActive ? (
                    <p className="text-primary-600 font-medium">Drop your file here...</p>
                  ) : (
                    <>
                      <p className="text-gray-600 font-medium mb-2">
                        Drag & drop your roof design file here
                      </p>
                      <p className="text-sm text-gray-500 mb-4">
                        Or click to select a file
                      </p>
                      <div className="inline-flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                        Choose File
                      </div>
                    </>
                  )}
                  
                  <div className="mt-4 text-xs text-gray-500">
                    Supports: PNG, JPG, GIF, PDF (Max 10MB)
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {/* File Info */}
                  <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <DocumentIcon className="h-8 w-8 text-primary-600" />
                        <div>
                          <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                          <p className="text-sm text-gray-500">
                            {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={removeFile}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                      >
                        <XMarkIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Image Preview */}
                  {imagePreview && (
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <h4 className="font-medium text-gray-900 mb-3">Design Preview</h4>
                      <div className="relative">
                        <img 
                          src={imagePreview} 
                          alt="Uploaded design"
                          className="w-full h-80 object-contain rounded-lg border border-gray-200"
                        />
                        <div className="absolute top-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
                          Preview
                        </div>
                      </div>
                      <p className="text-xs text-gray-500 mt-2 text-center">
                        You can manually verify the design details before validation
                      </p>
                    </div>
                  )}
                </div>
              )}
              
              {uploadedFile && !isProcessing && (
                <button
                  onClick={handleValidation}
                  className="btn-primary w-full mt-4"
                >
                  Start Validation
                </button>
              )}
            </motion.div>

            {/* Progress Section */}
            <AnimatePresence>
              {(isProcessing || validationResult) && (
                <motion.div
                  className="card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.5 }}
                >
                  <h3 className="text-lg font-semibold text-gray-900 mb-6">Analysis Progress</h3>
                  
                  <div className="space-y-4">
                    {steps.map((step, index) => {
                      const Icon = step.icon
                      return (
                        <div key={step.id} className="flex items-center space-x-4">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                            step.status === 'completed' ? 'bg-green-100 text-green-600' :
                            step.status === 'processing' ? 'bg-primary-100 text-primary-600 animate-pulse' :
                            step.status === 'error' ? 'bg-red-100 text-red-600' :
                            'bg-gray-100 text-gray-400'
                          }`}>
                            {step.status === 'completed' ? (
                              <CheckCircleIcon className="h-5 w-5" />
                            ) : step.status === 'error' ? (
                              <ExclamationTriangleIcon className="h-5 w-5" />
                            ) : (
                              <Icon className="h-5 w-5" />
                            )}
                          </div>
                          
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{step.title}</p>
                            <p className="text-sm text-gray-500">{step.description}</p>
                          </div>
                          
                          {step.status === 'processing' && (
                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary-600 border-t-transparent"></div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Results Section */}
          <div className="space-y-4 h-full">
            <AnimatePresence>
              {showResults && validationResult && (
                <motion.div
                  className="card"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-gray-900">Validation Results</h3>
                    <button
                      onClick={downloadReport}
                      className="inline-flex items-center space-x-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                      <DocumentArrowDownIcon className="h-4 w-4" />
                      <span>Download Report</span>
                    </button>
                  </div>
                  
                  {/* Quick Stats */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="flex items-center space-x-2">
                        <ClockIcon className="h-4 w-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-800">Processing Time</span>
                      </div>
                      <p className="text-lg font-bold text-blue-900 mt-1">
                        {validationResult.processing_time?.toFixed(1)}s
                      </p>
                    </div>
                    
                    {(() => {
                      const status = getComplianceStatus(validationResult.validation_report || '')
                      const isCompliant = status.includes('COMPLIANT') && !status.includes('NON-COMPLIANT')
                      const isNonCompliant = status.includes('NON-COMPLIANT')
                      const isReview = status.includes('REVIEW')
                      
                      const bgColor = isCompliant ? 'bg-green-50 border-green-200' : 
                                    isNonCompliant ? 'bg-red-50 border-red-200' : 
                                    isReview ? 'bg-yellow-50 border-yellow-200' : 
                                    'bg-blue-50 border-blue-200'
                      
                      const textColor = isCompliant ? 'text-green-600' : 
                                      isNonCompliant ? 'text-red-600' : 
                                      isReview ? 'text-yellow-600' : 
                                      'text-blue-600'
                      
                      const statusColor = isCompliant ? 'text-green-900' : 
                                        isNonCompliant ? 'text-red-900' : 
                                        isReview ? 'text-yellow-900' : 
                                        'text-blue-900'
                      
                      const Icon = isCompliant ? CheckCircleIcon : 
                                  isNonCompliant ? XCircleIcon : 
                                  isReview ? ExclamationTriangleIcon : 
                                  CheckCircleIcon
                      
                      return (
                        <div className={`${bgColor} border rounded-lg p-3`}>
                          <div className="flex items-center space-x-2">
                            <Icon className={`h-4 w-4 ${textColor}`} />
                            <span className={`text-sm font-medium ${textColor.replace('600', '800')}`}>Design Status</span>
                          </div>
                          <p className={`text-lg font-bold ${statusColor} mt-1`}>
                            {status}
                          </p>
                        </div>
                      )
                    })()}
                  </div>
                  
                  {/* Validation Report Preview */}
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-[500px] overflow-y-auto w-full min-h-[450px]">
                    <h4 className="font-medium text-gray-900 mb-3">Compliance Report Preview</h4>
                    <div className="text-sm text-gray-700 whitespace-pre-wrap prose prose-sm max-w-none">
                      {validationResult.validation_report?.split('\n').map((line, index) => {
                        // Remove all asterisks and HTML tags
                        const cleanLine = line.replace(/\*\*/g, '').replace(/<[^>]*>/g, '')
                        
                        // Style main section headings (TECHNICAL SPECIFICATIONS, COMPLIANCE ASSESSMENT, etc.)
                        if (/^(###\s*)?(TECHNICAL SPECIFICATIONS|COMPLIANCE ASSESSMENT|CRITICAL FINDINGS|SUMMARY|OVERALL STATUS)/.test(cleanLine)) {
                          const displayText = cleanLine.replace(/^###\s*/, '')
                          return (
                            <div key={index} className="font-bold text-lg text-blue-600 mt-6 mb-3 border-b border-blue-200 pb-1">
                              {displayText}
                            </div>
                          )
                        }
                        
                        // Style subsection headings (Dimensions:, Materials:, etc.)
                        if (/^(Dimensions|Materials|Structural Elements|Roof Slope|Component Inventory|All Visible Text and Specifications|Major Issues|Required Corrections|Professional Recommendations|Overall Assessment|Key Concerns|Next Steps):$/.test(cleanLine)) {
                          return (
                            <div key={index} className="font-bold text-gray-800 mt-4 mb-2">
                              {cleanLine}
                            </div>
                          )
                        }
                        
                        // Style compliance items (any component followed by COMPLIANT/REVIEW/NON-COMPLIANT)
                        if (/^[A-Za-z\s&]+:\s*(COMPLIANT|REVIEW|NON-COMPLIANT)/.test(cleanLine)) {
                          return (
                            <div key={index} className="font-medium text-gray-700 mt-2 mb-1">
                              {cleanLine}
                            </div>
                          )
                        }
                        
                        // Regular content
                        return <div key={index} className="text-gray-600 leading-relaxed">{cleanLine}</div>
                      })}
                      {validationResult.validation_report?.length > 1000 && (
                        <div className="text-gray-500 text-xs mt-2">... (truncated for preview)</div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            
            {/* Placeholder when no results */}
            {!showResults && !isProcessing && (
              <motion.div
                className="card text-center py-12"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <ShieldCheckIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-600 mb-2">
                  Upload a file to start validation
                </h3>
                <p className="text-gray-500">
                  Your compliance report will appear here once analysis is complete
                </p>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}