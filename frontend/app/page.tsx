'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  ShieldCheckIcon, 
  DocumentCheckIcon, 
  BuildingOfficeIcon,
  ArrowRightIcon,
  SparklesIcon,
  CloudArrowUpIcon,
  ChartBarIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

import HeroSection from '@/components/HeroSection'
import FeatureCard from '@/components/FeatureCard'
import UploadInterface from '@/components/UploadInterface'
import StatsSection from '@/components/StatsSection'

type FeatureColor = 'blue' | 'green' | 'purple' | 'orange'

interface Feature {
  icon: React.ComponentType<any>
  title: string
  description: string
  color: FeatureColor
}

export default function HomePage() {
  const [isUploadMode, setIsUploadMode] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null // Prevent hydration mismatch
  }

  const features: Feature[] = [
    {
      icon: CloudArrowUpIcon,
      title: "Smart Image Analysis",
      description: "Upload any roof design image, CAD file, or technical drawing. Our LLM's extracts every structural detail with precision.",
      color: "blue"
    },
    {
      icon: ShieldCheckIcon,
      title: "Code Compliance Validation",
      description: "Instantly validate against Florida Residential Building Code 2023. Get specific section citations and compliance status.",
      color: "green"
    },
    {
      icon: DocumentCheckIcon,
      title: "Professional Reports",
      description: "Generate permit-ready compliance reports with detailed analysis, code citations, and pass/fail determinations.",
      color: "purple"
    },
    {
      icon: ChartBarIcon,
      title: "Real-time Insights",
      description: "Track validation progress, view detailed analytics, and get instant feedback on design modifications.",
      color: "orange"
    }
  ]

  const processSteps = [
    {
      step: "01",
      title: "Upload Design",
      description: "Drop your roof design image, CAD file, or technical drawing"
    },
    {
      step: "02", 
      title: "AI Analysis",
      description: "we extract structural specifications and dimensions using LLM's"
    },
    {
      step: "03",
      title: "Code Validation", 
      description: "we validate the extracted data against Florida Building Code requirements"
    },
    {
      step: "04",
      title: "Compliance Report",
      description: "Download professional PDF report for permit submission"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Navigation */}
      <nav className="relative z-50 bg-white/80 backdrop-blur-lg border-b border-gray-200/50">
        <div className="container-width section-padding py-4">
          <div className="flex items-center justify-between">
            <motion.div 
              className="flex items-center space-x-3"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="p-2 bg-gradient-to-br from-primary-500 to-accent-500 rounded-lg">
                <BuildingOfficeIcon className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Roof Design validator</h1>
                <p className="text-sm text-gray-500">AI-Powered Code Compliance</p>
              </div>
            </motion.div>
            
            {/* <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="flex items-center space-x-4"
            >
              <span className="text-sm text-gray-600">Powered by</span>
              <div className="flex items-center space-x-2 px-3 py-1 bg-gray-100 rounded-full">
                <SparklesIcon className="h-4 w-4 text-yellow-500" />
                <span className="text-sm font-semibold text-gray-700">GPT-4o</span>
              </div>
            </motion.div> */}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      {!isUploadMode ? (
        <>
          {/* Hero Section */}
          <HeroSection onStartValidation={() => setIsUploadMode(true)} />

          {/* Stats Section */}
          <StatsSection />

          {/* Features Section */}
          <section className="py-20 section-padding">
            <div className="container-width">
              <motion.div
                className="text-center mb-16"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                <h2 className="text-4xl font-bold text-gray-900 mb-4">
                  Why Choose <span className="text-gradient">Roof Design validator</span>?
                </h2>
                <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                  Leverage cutting-edge AI technology to streamline your building code compliance process.
                  Save time, reduce errors, and ensure regulatory approval.
                </p>
              </motion.div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                {features.map((feature, index) => (
                  <FeatureCard 
                    key={index} 
                    feature={feature} 
                    index={index} 
                  />
                ))}
              </div>
            </div>
          </section>

          {/* Process Section */}
          <section className="py-20 bg-white section-padding">
            <div className="container-width">
              <motion.div
                className="text-center mb-16"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                <h2 className="text-4xl font-bold text-gray-900 mb-4">
                  Simple 4-Step Process
                </h2>
                <p className="text-xl text-gray-600">
                  From upload to compliance report in minutes, not hours
                </p>
              </motion.div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                {processSteps.map((step, index) => (
                  <motion.div
                    key={index}
                    className="relative"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                    viewport={{ once: true }}
                  >
                    <div className="text-center">
                      <div className="relative mb-6">
                        <div className="w-16 h-16 bg-gradient-to-br from-primary-500 to-accent-500 rounded-full flex items-center justify-center mx-auto">
                          <span className="text-white font-bold text-lg">{step.step}</span>
                        </div>
                        {index < processSteps.length - 1 && (
                          <div className="hidden lg:block absolute top-8 left-full w-full h-0.5 bg-gradient-to-r from-primary-200 to-transparent"></div>
                        )}
                      </div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-3">{step.title}</h3>
                      <p className="text-gray-600">{step.description}</p>
                    </div>
                  </motion.div>
                ))}
              </div>

              <motion.div
                className="text-center mt-12"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                viewport={{ once: true }}
              >
                <button
                  onClick={() => setIsUploadMode(true)}
                  className="btn-primary inline-flex items-center space-x-2 text-lg px-8 py-4"
                >
                  <span>Get Started Now</span>
                  <ArrowRightIcon className="h-5 w-5" />
                </button>
              </motion.div>
            </div>
          </section>
        </>
      ) : (
        <UploadInterface onBack={() => setIsUploadMode(false)} />
      )}

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12 section-padding">
        <div className="container-width">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-primary-500 to-accent-500 rounded-lg">
                  <BuildingOfficeIcon className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-xl font-bold">Roof Design validator</h3>
              </div>
              <p className="text-gray-400">
                AI-powered building code compliance validation for roof designs.
                Streamline your permit approval process with cutting-edge technology.
              </p>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold mb-4">Features</h4>
              <ul className="space-y-2 text-gray-400">
                <li className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-400" />
                  <span>Vision Analysis</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-400" />
                  <span>Florida Building Code Validation</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-400" />
                  <span>Professional PDF Reports</span>
                </li>
                <li className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-4 w-4 text-green-400" />
                  <span>Real-time Compliance Checking</span>
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold mb-4">Support</h4>
              <p className="text-gray-400 mb-4">
                Get help with your roof design validation process.
              </p>
              <div className="space-y-2 text-gray-400">
                <p>Email: durgamaheshboppani@gmail.com</p>
                <p>Documentation available</p>
              </div>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Roof Design validator. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}