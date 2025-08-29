'use client'

import { motion } from 'framer-motion'
import { 
  ArrowRightIcon, 
  SparklesIcon,
  ShieldCheckIcon,
  DocumentCheckIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

interface HeroSectionProps {
  onStartValidation: () => void
}

export default function HeroSection({ onStartValidation }: HeroSectionProps) {
  const fadeInUp = {
    initial: { opacity: 0, y: 60 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.6 }
    }
  }

  const stagger = {
    animate: {
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  return (
    <section className="relative py-20 lg:py-32 section-padding overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 left-0 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl animate-pulse-slow"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }}></div>
      </div>
      
      <div className="container-width">
        <motion.div 
          className="text-center"
          variants={stagger}
          initial="initial"
          animate="animate"
        >
          {/* Badge */}
          {/* <motion.div 
            className="inline-flex items-center space-x-2 bg-white/80 backdrop-blur-sm border border-primary-200 rounded-full px-4 py-2 mb-8"
            variants={fadeInUp}
          > */}
            {/* <SparklesIcon className="h-4 w-4 text-primary-600" />
            <span className="text-sm font-medium text-primary-700"> */}
            {/* </span> */}
          {/* </motion.div> */}

          {/* Main Heading */}
          <motion.h1 
            className="text-5xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight"
            variants={fadeInUp}
          >
            <span className="block">Validate Your</span>
            <span className="text-gradient block">Roof Designs</span>
            <span className="block">Instantly</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p 
            className="text-xl lg:text-2xl text-gray-600 mb-12 max-w-4xl mx-auto leading-relaxed"
            variants={fadeInUp}
          >
            Upload any roof design image and get instant building code compliance validation.
            Our AI analyzes your designs against Florida Building Code requirements 
            and generates professional reports in minutes.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div 
            className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-6 mb-16"
            variants={fadeInUp}
          >
            <button
              onClick={onStartValidation}
              className="btn-primary inline-flex items-center space-x-3 text-lg px-8 py-4 w-full sm:w-auto justify-center group"
            >
              <span>Start Validation</span>
              <ArrowRightIcon className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </button>
            
            <button 
              onClick={onStartValidation}
              className="btn-secondary inline-flex items-center space-x-2 text-lg px-8 py-4 w-full sm:w-auto justify-center"
            >
              <span>View Demo</span>
            </button>
          </motion.div>

          {/* Feature Pills */}
          <motion.div 
            className="flex flex-wrap items-center justify-center gap-4 mb-16"
            variants={fadeInUp}
          >
            {[
              { icon: ShieldCheckIcon, text: "99% Accurate", color: "bg-green-100 text-green-700" },
              { icon: ClockIcon, text: "< 2 Min Analysis", color: "bg-blue-100 text-blue-700" },
              { icon: DocumentCheckIcon, text: "Permit Ready", color: "bg-purple-100 text-purple-700" }
            ].map((pill, index) => (
              <div 
                key={index}
                className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full ${pill.color} backdrop-blur-sm`}
              >
                <pill.icon className="h-4 w-4" />
                <span className="text-sm font-medium">{pill.text}</span>
              </div>
            ))}
          </motion.div>

          {/* Visual Preview */}
          <motion.div 
            className="relative max-w-4xl mx-auto"
            variants={fadeInUp}
          >
            <div className="relative bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
              {/* Mock Browser Header */}
              <div className="bg-gray-100 px-4 py-3 border-b border-gray-200">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                  <div className="ml-4 bg-white rounded px-3 py-1 text-xs text-gray-600">
                    roofvalidator.com/upload
                  </div>
                </div>
              </div>
              
              {/* Mock Content */}
              <div className="p-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
                  {/* Upload Area */}
                  <div className="border-2 border-dashed border-primary-300 rounded-lg p-8 text-center bg-primary-50">
                    <div className="animate-float">
                      <svg className="w-16 h-16 text-primary-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <p className="text-primary-700 font-medium">Drop your roof design here</p>
                    <p className="text-sm text-primary-600 mt-1">PNG, JPG, PDF, CAD files</p>
                  </div>
                  
                  {/* Results Preview */}
                  <div className="space-y-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <ShieldCheckIcon className="h-5 w-5 text-green-600" />
                        <span className="font-medium text-green-800">COMPLIANT</span>
                      </div>
                      <p className="text-sm text-green-700">Sheathing thickness meets requirements</p>
                    </div>
                    
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <ClockIcon className="h-5 w-5 text-yellow-600" />
                        <span className="font-medium text-yellow-800">REVIEW REQUIRED</span>
                      </div>
                      <p className="text-sm text-yellow-700">Rafter spacing needs verification</p>
                    </div>
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <DocumentCheckIcon className="h-5 w-5 text-blue-600" />
                        <span className="font-medium text-blue-800">CITATION</span>
                      </div>
                      <p className="text-sm text-blue-700">Florida Building Code 2023</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Floating Elements */}
            <div className="absolute -top-4 -left-4 w-8 h-8 bg-primary-500 rounded-lg rotate-12 animate-float"></div>
            <div className="absolute -bottom-4 -right-4 w-6 h-6 bg-accent-500 rounded-full animate-float" style={{ animationDelay: '1s' }}></div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}