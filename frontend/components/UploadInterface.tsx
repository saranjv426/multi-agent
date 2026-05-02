'use client'

import { useState, useCallback, useEffect } from 'react'
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
import { api } from '../lib/api'

interface UploadInterfaceProps {
  onBack: () => void
}

interface ExtractionPageDiagnostics {
  page_number: number
  title_region_count: number
  refined_title_region_count: number
  image_region_count: number
  fused_region_count: number
  selected_region_count: number
  strategy: string
}

interface ExtractionDiagnostics {
  source_kind?: string
  render_dpi?: number | null
  total_drawings?: number
  raw_total_drawings?: number
  filtered_total_drawings?: number
  extraction_time?: number
  pages?: ExtractionPageDiagnostics[]
}

interface ValidationResult {
  filename?: string
  source_filename?: string
  source_file_index?: number
  source_document_key?: string
  selected_model?: string
  source_page?: number
  drawing_index?: number
  drawing_label?: string
  analysis?: string
  validation_report?: string
  compliance_report?: string
  parsed_report?: any
  report_image_data?: string
  estimated_cost?: number
  processing_time?: number
  extraction_diagnostics?: ExtractionDiagnostics
  extraction_page_diagnostics?: ExtractionPageDiagnostics
  total_drawings?: number
  raw_total_drawings?: number
  successful_drawings?: number
  failed_drawings?: number
  results?: ValidationResult[]
  success: boolean
  error?: string
}

interface BatchValidationResponse {
  success: boolean
  total_files: number
  successful_files: number
  failed_files: number
  total_drawings?: number
  successful_drawings?: number
  failed_drawings?: number
  results: ValidationResult[]
}

interface UploadedDesign {
  file: File
  preview: string | null
}

type ExtractionMode = 'wall-sections' | 'direct'

interface AnalysisStep {
  id: string
  title: string
  description: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  icon: React.ComponentType<any>
}

interface ModelOption {
  value: string
  label: string
}

interface SystemStatusResponse {
  available_models?: string[]
  default_model?: string | null
}

const MAX_FILES = 3
const MAX_FILE_SIZE = 10 * 1024 * 1024
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
const DEFAULT_MODEL_OPTIONS = [
  { value: 'mistral-small-3.1', label: 'Mistral Small 3.1' },
  { value: 'gpt-5.2', label: 'GPT-5.2' },
  { value: 'llama-3.1-nemotron-nano-8B-v1', label: 'Llama 3.1 Nemotron Nano 8B' },
  { value: 'gpt-4.1-nano', label: 'GPT-4.1 Nano' },
  { value: 'gpt-5.4', label: 'GPT-5.4' }
]
const EXTRACTION_MODE_OPTIONS: Array<{
  value: ExtractionMode
  label: string
  description: string
}> = [
  {
    value: 'wall-sections',
    label: 'Extract Wall Sections First',
    description: 'Split PDFs into wall-section crops before validation.'
  },
  {
    value: 'direct',
    label: 'Analyze Upload Directly',
    description: 'Send the full image or each PDF page to the model with no separate cropping.'
  }
]
const GENERATED_REPORT_PATTERN = /^roof-compliance-report-/i

const isPdfUpload = (file: File) =>
  file.type === 'application/pdf' || /\.pdf$/i.test(file.name)

const isGeneratedReportUpload = (file: File) =>
  isPdfUpload(file) && GENERATED_REPORT_PATTERN.test(file.name)

const normalizeSourceName = (value?: string) =>
  (value || '')
    .replace(/\s+-\s+Page\s+\d+\s+Drawing\s+\d+$/i, '')
    .replace(/\s+-\s+Drawing\s+\d+$/i, '')
    .trim()

const normalizeReportModelName = (value?: string) =>
  normalizeSourceName(value).replace(/[^a-zA-Z0-9-_]+/g, '_')

const getSourceDocumentKey = (result?: ValidationResult) => {
  if (!result) return ''
  if (result.source_document_key) return result.source_document_key
  if (typeof result.source_file_index === 'number' && result.source_filename) {
    return `${result.source_file_index}:${result.source_filename}`
  }
  if (typeof result.source_file_index === 'number') {
    return `file-index:${result.source_file_index}`
  }

  const normalizedName = normalizeSourceName(result.source_filename || result.filename)
  return normalizedName ? `filename:${normalizedName}` : ''
}

const getDocumentDiagnostics = (results: ValidationResult[], selected?: ValidationResult) => {
  const sourceDocumentKey = getSourceDocumentKey(selected)
  if (sourceDocumentKey) {
    const grouped = results.find((result) => getSourceDocumentKey(result) === sourceDocumentKey)
    if (grouped?.extraction_diagnostics) return grouped.extraction_diagnostics
  }
  return selected?.extraction_diagnostics
}

const getNestedResults = (result?: ValidationResult) =>
  Array.isArray(result?.results) ? result.results : []

const getDisplayedDrawingCount = (result?: ValidationResult) =>
  result?.total_drawings ?? getNestedResults(result).length

const getComplianceStatusFromText = (report: string): string => {
  if (!report) return 'Unknown'

  const statusPatterns = [
    /OVERALL STATUS:\s*(COMPLIANT|NON-COMPLIANT|REQUIRES FURTHER REVIEW|MISSING)/i,
    /STATUS:\s*(COMPLIANT|NON-COMPLIANT|REQUIRES FURTHER REVIEW|MISSING)/i,
    /OVERALL:\s*(COMPLIANT|NON-COMPLIANT|REQUIRES FURTHER REVIEW|MISSING)/i,
    /COMPLIANCE:\s*(COMPLIANT|NON-COMPLIANT|REQUIRES FURTHER REVIEW|MISSING)/i,
    /RESULT:\s*(COMPLIANT|NON-COMPLIANT|REQUIRES FURTHER REVIEW|MISSING)/i
  ]

  for (const pattern of statusPatterns) {
    const match = report.match(pattern)
    if (match) {
      return match[1].toUpperCase()
    }
  }

  if (report.includes('NON-COMPLIANT')) return 'NON-COMPLIANT'
  if (report.includes('REQUIRES FURTHER REVIEW')) return 'REQUIRES FURTHER REVIEW'
  if (report.includes('MISSING')) return 'MISSING'
  if (report.includes('COMPLIANT')) return 'COMPLIANT'
  return 'ANALYSIS COMPLETE'
}

const getResultPreviewText = (result?: ValidationResult) => {
  if (!result) return ''
  if (result.validation_report) return result.validation_report

  const nestedResults = getNestedResults(result)
  if (!nestedResults.length) return ''

  const successful = nestedResults.filter(item => item.success).length
  const lines = [
    `DOCUMENT REPORT: ${result.source_filename || result.filename || 'Uploaded document'}`,
    `Successful drawings: ${successful}/${nestedResults.length}`,
    ''
  ]

  nestedResults.forEach((item, index) => {
    const status = item.success ? getComplianceStatusFromText(item.validation_report || '') : 'FAILED'
    const label = item.drawing_label || item.filename || `Drawing ${index + 1}`
    lines.push(`${label}: ${status}`)
  })

  return lines.join('\n')
}

const formatModelLabel = (modelName: string) =>
  modelName
    .split('-')
    .map((segment) => {
      if (!segment) return segment
      if (segment.toLowerCase() === 'gpt') return 'GPT'
      return segment.charAt(0).toUpperCase() + segment.slice(1)
    })
    .join(' ')

export default function UploadInterface({ onBack }: UploadInterfaceProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedDesign[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([])
  const [showResults, setShowResults] = useState(false)
  const [selectedResultIndex, setSelectedResultIndex] = useState(0)
  const [selectedModel, setSelectedModel] = useState<string>('mistral-small-3.1')
  const [modelOptions, setModelOptions] = useState<ModelOption[]>(DEFAULT_MODEL_OPTIONS)
  const [extractionMode, setExtractionMode] = useState<ExtractionMode>('wall-sections')

  const analysisSteps: AnalysisStep[] = [
    {
      id: 'upload',
      title: 'Image Processing',
      description: 'Preparing your uploaded design files for analysis',
      status: 'pending',
      icon: CloudArrowUpIcon
    },
    {
      id: 'analysis',
      title: 'AI Design Analysis',
      description: 'Extracting structural specifications from each design',
      status: 'pending',
      icon: EyeIcon
    },
    {
      id: 'validation',
      title: 'Code Validation',
      description: 'Checking each design against Florida Building Code',
      status: 'pending',
      icon: ShieldCheckIcon
    },
    {
      id: 'report',
      title: 'Report Generation',
      description: 'Preparing individual compliance reports',
      status: 'pending',
      icon: DocumentIcon
    }
  ]

  const [steps, setSteps] = useState(analysisSteps)

  useEffect(() => {
    let isMounted = true

    const loadAvailableModels = async () => {
      const response = await api.get<SystemStatusResponse>('/api/system/status')
      const availableModels = response.data?.available_models || []

      if (!isMounted || !availableModels.length) {
        return
      }

      const nextOptions = availableModels.map((modelName) => ({
        value: modelName,
        label: formatModelLabel(modelName)
      }))

      setModelOptions(nextOptions)
      setSelectedModel((currentModel) => {
        if (availableModels.includes(currentModel)) return currentModel
        return response.data?.default_model || availableModels[0]
      })
    }

    loadAvailableModels()

    return () => {
      isMounted = false
    }
  }, [])

  const updateStepStatus = (stepIndex: number, status: AnalysisStep['status']) => {
    setSteps(prev => prev.map((step, index) =>
      index === stepIndex ? { ...step, status } : step
    ))
  }

  const fileToPreview = (file: File): Promise<string | null> =>
    new Promise((resolve, reject) => {
      if (!file.type.startsWith('image/')) {
        resolve(null)
        return
      }

      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsDataURL(file)
    })

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!acceptedFiles.length) {
      return
    }

    const availableSlots = MAX_FILES - uploadedFiles.length
    if (availableSlots <= 0) {
      toast.error(`You can upload up to ${MAX_FILES} files only`)
      return
    }

    const incoming = acceptedFiles.slice(0, availableSlots)
    const validIncoming: File[] = []

    incoming.forEach((file) => {
      if (!ALLOWED_TYPES.includes(file.type)) {
        toast.error(`"${file.name}" is not supported. Use PNG, JPG, JPEG, GIF, or PDF.`)
        return
      }

      if (file.size > MAX_FILE_SIZE) {
        toast.error(`"${file.name}" exceeds the 10MB limit`)
        return
      }

      if (isGeneratedReportUpload(file)) {
        toast.error(`"${file.name}" is a generated compliance report, not a source drawing PDF`)
        return
      }

      validIncoming.push(file)
    })

    if (!validIncoming.length) {
      return
    }

    const uploads: UploadedDesign[] = []
    for (const file of validIncoming) {
      const preview = await fileToPreview(file)
      uploads.push({ file, preview })
    }

    setUploadedFiles(prev => [...prev, ...uploads])
    setShowResults(false)
    setValidationResults([])
    setSelectedResultIndex(0)
    setSteps(analysisSteps)
    toast.success(`${uploads.length} file(s) added`)

    if (acceptedFiles.length > availableSlots) {
      toast(`Only first ${availableSlots} file(s) were added`)
    }
  }, [uploadedFiles.length])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
      'application/pdf': ['.pdf']
    },
    multiple: true,
    maxFiles: MAX_FILES
  })

  const handleValidation = async () => {
    if (!uploadedFiles.length) {
      toast.error('Please upload at least one file')
      return
    }

    setIsProcessing(true)
    setCurrentStep(0)

    try {
      updateStepStatus(0, 'processing')
      await new Promise(resolve => setTimeout(resolve, 600))
      updateStepStatus(0, 'completed')
      setCurrentStep(1)

      updateStepStatus(1, 'processing')
      const formData = new FormData()
      uploadedFiles.forEach(({ file }) => formData.append('files', file))
      formData.append('selected_model', selectedModel)
      formData.append('extraction_mode', extractionMode)

      const response = await api.post<BatchValidationResponse>(
        '/api/validation/validate-optimized-batch',
        formData,
        { timeoutMs: 600000 }
      )

      if (response.error) {
        if (response.status === 401) {
          toast.error('Your session has expired. Please log in again.')
          return
        }
        throw new Error(response.error)
      }

      if (!response.data?.results?.length) {
        throw new Error('No validation data returned from server')
      }

      updateStepStatus(1, 'completed')
      setCurrentStep(2)

      updateStepStatus(2, 'processing')
      await new Promise(resolve => setTimeout(resolve, 900))
      updateStepStatus(2, 'completed')
      setCurrentStep(3)

      updateStepStatus(3, 'processing')
      await new Promise(resolve => setTimeout(resolve, 500))
      updateStepStatus(3, 'completed')

      setValidationResults(response.data.results)
      setSelectedResultIndex(0)
      setShowResults(true)

      const totalReports = response.data.total_files ?? response.data.results.length
      const successfulReports = response.data.successful_files ?? response.data.results.filter(result => result.success).length
      if (successfulReports === totalReports) {
        toast.success(`Validation completed for all ${totalReports} report(s)!`)
      } else {
        toast(`Validation completed: ${successfulReports}/${totalReports} report(s) successful`)
      }
    } catch (error: any) {
      console.error('Validation error:', error)
      updateStepStatus(currentStep, 'error')
      toast.error(error.message || 'An error occurred during validation')
    } finally {
      setIsProcessing(false)
    }
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
    setValidationResults([])
    setShowResults(false)
    setSelectedResultIndex(0)
    setSteps(analysisSteps)
  }

  const clearAllFiles = () => {
    setUploadedFiles([])
    setValidationResults([])
    setShowResults(false)
    setSelectedResultIndex(0)
    setSteps(analysisSteps)
  }

  const getComplianceStatus = (report: string): string => {
    return getComplianceStatusFromText(report)
  }

  const downloadReport = async (index: number) => {
    const result = validationResults[index]
    const sourceFile = typeof result?.source_file_index === 'number'
      ? uploadedFiles[result.source_file_index]?.file
      : undefined

    if (!result || !result.success) {
      toast.error('Report is not available for this drawing')
      return
    }

    try {
      const nestedResults = getNestedResults(result)
      const shouldDownloadGroupedReport = nestedResults.length > 0
      const reportModelName = result.selected_model || selectedModel || 'model'
      const reportName = normalizeSourceName(result.source_filename || result.filename) || result.drawing_label || 'drawing'
      const loadingToast = toast.loading(`Generating PDF for ${reportModelName}...`)

      let imageBase64 = result.report_image_data
      if (!imageBase64 && sourceFile) {
        imageBase64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader()
          reader.onload = () => resolve(reader.result as string)
          reader.onerror = reject
          reader.readAsDataURL(sourceFile)
        })
      }

      const payload = shouldDownloadGroupedReport
        ? {
            validation_data: result,
            image_filename: reportName,
            selected_model: reportModelName
          }
        : {
            validation_data: result,
            image_data: imageBase64,
            image_filename: reportName,
            selected_model: reportModelName
          }

      const response = await api.post('/generate-pdf-report', payload, { responseType: 'blob', timeoutMs: 120000 } as any)

      if (response.error) {
        if (response.status === 401) {
          toast.dismiss(loadingToast)
          toast.error('Your session has expired. Please log in again.')
          return
        }
        toast.dismiss(loadingToast)
        throw new Error(response.error)
      }

      if (!response.data) {
        toast.dismiss(loadingToast)
        throw new Error('No PDF data received from server')
      }

      const blob = response.data as Blob
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const safeModelName = normalizeReportModelName(reportModelName) || 'model'
      a.download = `${safeModelName}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.dismiss(loadingToast)
      toast.success(`Report downloaded for ${reportModelName}`)
    } catch (error) {
      console.error('Error downloading PDF report:', error)
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      toast.error(`Failed to generate PDF report: ${errorMessage}`)

      const reportContent = result.validation_report ||
                           result.analysis ||
                           result.compliance_report ||
                           JSON.stringify(result, null, 2)
      const blob = new Blob([reportContent], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `roof-validation-report-${Date.now()}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast('Downloaded text report as fallback')
    }
  }

  const selectedResult = validationResults[selectedResultIndex]
  const selectedDocumentDiagnostics = getDocumentDiagnostics(validationResults, selectedResult)
  const selectedPageDiagnostics = selectedResult?.extraction_page_diagnostics

  return (
    <div className="min-h-screen py-4">
      <div className="container mx-auto px-4 max-w-[1770px]">
        <div className="flex items-center mb-8">
          <button
            onClick={onBack}
            className="inline-flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeftIcon className="h-5 w-5" />
            <span>Back to Home</span>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 min-h-[calc(100vh-200px)]">
          <div className="space-y-4 h-full">
            <motion.div
              className="card"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Design Files</h2>
              <p className="text-sm text-gray-500 mb-4">Upload up to {MAX_FILES} files and validate them in one run.</p>

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
                  <p className="text-primary-600 font-medium">Drop files here...</p>
                ) : (
                  <>
                    <p className="text-gray-600 font-medium mb-2">Drag and drop roof design files</p>
                    <p className="text-sm text-gray-500 mb-4">Or click to select up to {MAX_FILES} files</p>
                    <div className="inline-flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                      Choose Files
                    </div>
                  </>
                )}
                <div className="mt-4 text-xs text-gray-500">
                  Supports: PNG, JPG, JPEG, GIF, PDF. Max Size: 10MB each
                </div>
              </div>

              {!!uploadedFiles.length && (
                <div className="mt-4 space-y-3">
                  <div className="grid grid-cols-1 gap-3">
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <label htmlFor="model-select" className="block text-sm font-medium text-gray-700 mb-2">
                        Validation Model
                      </label>
                      <select
                        id="model-select"
                        value={selectedModel}
                        onChange={(event) => setSelectedModel(event.target.value)}
                        disabled={isProcessing}
                        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200 disabled:bg-gray-100 disabled:text-gray-500"
                      >
                        {modelOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <label htmlFor="extraction-mode-select" className="block text-sm font-medium text-gray-700 mb-2">
                        Drawing Handling
                      </label>
                      <select
                        id="extraction-mode-select"
                        value={extractionMode}
                        onChange={(event) => setExtractionMode(event.target.value as ExtractionMode)}
                        disabled={isProcessing}
                        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200 disabled:bg-gray-100 disabled:text-gray-500"
                      >
                        {EXTRACTION_MODE_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <p className="mt-2 text-xs text-gray-500">
                        {EXTRACTION_MODE_OPTIONS.find((option) => option.value === extractionMode)?.description}
                      </p>
                    </div>
                  </div>

                  {uploadedFiles.map((upload, index) => (
                    <div key={`${upload.file.name}-${upload.file.lastModified}-${index}`} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <DocumentIcon className="h-7 w-7 text-primary-600" />
                          <div>
                            <p className="font-medium text-gray-900">{upload.file.name}</p>
                            <p className="text-sm text-gray-500">{(upload.file.size / (1024 * 1024)).toFixed(2)} MB</p>
                          </div>
                        </div>
                        <button
                          onClick={() => removeFile(index)}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <XMarkIcon className="h-5 w-5" />
                        </button>
                      </div>
                      {upload.preview && (
                        <img
                          src={upload.preview}
                          alt={`Preview ${upload.file.name}`}
                          className="w-full h-40 object-contain rounded-lg border border-gray-200 bg-white mt-3"
                        />
                      )}
                    </div>
                  ))}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {!isProcessing && (
                      <button onClick={handleValidation} className="btn-primary w-full">
                        Start Validation
                      </button>
                    )}
                    {!isProcessing && (
                      <button
                        onClick={clearAllFiles}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                      >
                        Clear All
                      </button>
                    )}
                  </div>
                </div>
              )}
            </motion.div>

            <AnimatePresence>
              {(isProcessing || validationResults.length > 0) && (
                <motion.div
                  className="card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.5 }}
                >
                  <h3 className="text-lg font-semibold text-gray-900 mb-6">Analysis Progress</h3>
                  <div className="space-y-4">
                    {steps.map(step => {
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

          <div className="space-y-4 h-full">
            <AnimatePresence>
              {showResults && validationResults.length > 0 && (
                <motion.div
                  className="card"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  <h3 className="text-lg font-semibold text-gray-900 mb-6">Validation Results</h3>

                  <div className="space-y-3 mb-6">
                    {validationResults.map((result, index) => {
                      const reportText = getResultPreviewText(result)
                      const status = result.success ? getComplianceStatus(reportText) : 'FAILED'
                      const isCompliant = status.includes('COMPLIANT') && !status.includes('NON-COMPLIANT')
                      const isNonCompliant = status.includes('NON-COMPLIANT')
                      const isReview = status.includes('REVIEW')
                      const isFailed = status === 'FAILED'
                      const fileName = result.filename || result.drawing_label || result.source_filename || `Drawing ${index + 1}`
                      const drawingCount = getDisplayedDrawingCount(result)

                      return (
                        <div
                          key={`${fileName}-${index}`}
                          className={`border rounded-lg p-3 ${selectedResultIndex === index ? 'border-primary-500 bg-primary-50' : 'border-gray-200 bg-white'}`}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                            <div>
                              <p className="font-medium text-gray-900">{fileName}</p>
                              <div className="text-sm text-gray-600 flex items-center gap-2">
                                <ClockIcon className="h-4 w-4" />
                                <span>{result.processing_time?.toFixed(1) ?? '0.0'}s</span>
                                {drawingCount > 0 && <span>• {drawingCount} drawing{drawingCount === 1 ? '' : 's'}</span>}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                isFailed ? 'bg-red-100 text-red-700' :
                                isCompliant ? 'bg-green-100 text-green-700' :
                                isNonCompliant ? 'bg-red-100 text-red-700' :
                                isReview ? 'bg-yellow-100 text-yellow-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {status}
                              </span>
                              <button
                                onClick={() => setSelectedResultIndex(index)}
                                className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100"
                              >
                                View
                              </button>
                              <button
                                onClick={() => downloadReport(index)}
                                disabled={!result.success}
                                className="inline-flex items-center space-x-1 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-300 text-white px-3 py-1 rounded-md transition-colors text-sm"
                              >
                                <DocumentArrowDownIcon className="h-4 w-4" />
                                <span>Download</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {selectedResult && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-[500px] overflow-y-auto w-full min-h-[350px]">
                      <h4 className="font-medium text-gray-900 mb-3">
                        Compliance Report Preview - {selectedResult.filename || selectedResult.drawing_label || selectedResult.source_filename || 'Selected Drawing'}
                      </h4>
                      {(selectedDocumentDiagnostics || selectedPageDiagnostics) && (
                        <div className="mb-4 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
                          <div className="font-semibold mb-2">Extraction Diagnostics</div>
                          {selectedDocumentDiagnostics && (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
                              <div>Source: {selectedDocumentDiagnostics.source_kind || 'unknown'}</div>
                              <div>Wall Sections Analyzed: {selectedDocumentDiagnostics.filtered_total_drawings ?? getDisplayedDrawingCount(selectedResult) ?? 'unknown'}</div>
                              <div>Panels Detected Before Filtering: {selectedDocumentDiagnostics.raw_total_drawings ?? selectedDocumentDiagnostics.total_drawings ?? 'unknown'}</div>
                              <div>Render DPI: {selectedDocumentDiagnostics.render_dpi ?? 'n/a'}</div>
                              <div>Extraction Time: {selectedDocumentDiagnostics.extraction_time?.toFixed(2) ?? 'n/a'}s</div>
                            </div>
                          )}
                          {selectedPageDiagnostics && (
                            <div className="space-y-1 border-t border-blue-200 pt-2">
                              <div>Page {selectedPageDiagnostics.page_number} Strategy: {selectedPageDiagnostics.strategy}</div>
                              <div>
                                Titles: {selectedPageDiagnostics.title_region_count} {'->'} Refined: {selectedPageDiagnostics.refined_title_region_count}
                              </div>
                              <div>
                                Image Regions: {selectedPageDiagnostics.image_region_count} | Fused Regions: {selectedPageDiagnostics.fused_region_count} | Selected: {selectedPageDiagnostics.selected_region_count}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                      {!selectedResult.success ? (
                        <p className="text-sm text-red-700">
                          Validation failed: {selectedResult.error || 'Unknown error'}
                        </p>
                      ) : (
                        <div className="text-sm text-gray-700 whitespace-pre-wrap prose prose-sm max-w-none">
                          {getResultPreviewText(selectedResult).split('\n').map((line, idx) => {
                            if (/^###\s*(.+)$/.test(line)) {
                              const displayText = line.replace(/^###\s*/, '')
                              return (
                                <div key={idx} className="font-bold text-lg text-blue-600 mt-6 mb-3 border-b border-blue-200 pb-1">
                                  {displayText}
                                </div>
                              )
                            }

                            if (/^\*\*(VALIDATION CHECKLIST|SUMMARY):\*\*\s*$/.test(line)) {
                              const displayText = line.replace(/^\*\*(.+):\*\*\s*$/, '$1:')
                              return (
                                <div key={idx} className="font-bold text-lg text-blue-600 mt-6 mb-3 border-b border-blue-200 pb-1">
                                  {displayText}
                                </div>
                              )
                            }

                            if (/^\*\*([^*]+):\*\*\s*$/.test(line)) {
                              const displayText = line.replace(/^\*\*(.+):\*\*\s*$/, '$1:')
                              return (
                                <div key={idx} className="font-bold text-gray-800 mt-4 mb-2">
                                  {displayText}
                                </div>
                              )
                            }

                            const cleanLine = line.replace(/\*\*/g, '').replace(/<[^>]*>/g, '')
                            if (/^(TECHNICAL SPECIFICATIONS|COMPLIANCE ASSESSMENT|CRITICAL FINDINGS|SUMMARY|OVERALL STATUS)/.test(cleanLine)) {
                              return (
                                <div key={idx} className="font-bold text-lg text-blue-600 mt-6 mb-3 border-b border-blue-200 pb-1">
                                  {cleanLine}
                                </div>
                              )
                            }

                            if (/^(DIMENSIONS FOUND|MATERIALS IDENTIFIED|SLOPE\/PITCH DETAILS|STRUCTURAL ELEMENTS|ALL VISIBLE TEXT|CRITICAL FINDINGS|REQUIRED CORRECTIONS|Major Issues|Required Corrections|Professional Recommendations|Overall Assessment|Key Concerns|Next Steps):$/.test(cleanLine)) {
                              return (
                                <div key={idx} className="font-bold text-gray-800 mt-4 mb-2">
                                  {cleanLine}
                                </div>
                              )
                            }

                            if (/^(Sheathing|Rafter Spacing\/Spans|Fastening\/Connections|Underlayment|Insulation|Wind Resistance):\s*(COMPLIANT|NON-COMPLIANT|REQUIRES FURTHER REVIEW|MISSING)/.test(cleanLine)) {
                              const status = cleanLine.match(/:\s*(COMPLIANT|NON-COMPLIANT|REQUIRES FURTHER REVIEW|MISSING)/)?.[1]
                              let bgColor = 'bg-gray-50'
                              let borderColor = 'border-gray-200'
                              let textColor = 'text-gray-700'

                              if (status === 'COMPLIANT') {
                                bgColor = 'bg-green-50'
                                borderColor = 'border-green-300'
                                textColor = 'text-green-800'
                              } else if (status === 'NON-COMPLIANT') {
                                bgColor = 'bg-red-50'
                                borderColor = 'border-red-300'
                                textColor = 'text-red-800'
                              } else if (status === 'REQUIRES FURTHER REVIEW') {
                                bgColor = 'bg-yellow-50'
                                borderColor = 'border-yellow-300'
                                textColor = 'text-yellow-800'
                              } else if (status === 'MISSING') {
                                bgColor = 'bg-orange-50'
                                borderColor = 'border-orange-300'
                                textColor = 'text-orange-800'
                              }

                              return (
                                <div key={idx} className={`font-medium ${textColor} mt-3 mb-2 pl-3 pr-3 py-2 rounded-lg ${bgColor} border-l-4 ${borderColor}`}>
                                  {cleanLine}
                                </div>
                              )
                            }

                            if (/^[A-Za-z\s&]+:\s*(COMPLIANT|REVIEW|NON-COMPLIANT)/.test(cleanLine)) {
                              return (
                                <div key={idx} className="font-medium text-gray-700 mt-2 mb-1">
                                  {cleanLine}
                                </div>
                              )
                            }

                            return <div key={idx} className="text-gray-600 leading-relaxed">{cleanLine}</div>
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {!showResults && !isProcessing && (
              <motion.div
                className="card text-center py-12"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <ShieldCheckIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-600 mb-2">Upload up to 3 files to start validation</h3>
                <p className="text-gray-500">Each uploaded file will produce one analysis result and one downloadable report.</p>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
