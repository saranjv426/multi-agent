'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface Stat {
  label: string
  value: string
  suffix?: string
  description: string
}

const stats: Stat[] = [
  {
    label: "Accuracy Rate",
    value: "99.2",
    suffix: "%",
    description: "Building code compliance detection accuracy"
  },
  {
    label: "Analysis Time", 
    value: "< 2",
    suffix: " min",
    description: "Average time from upload to report"
  },
  {
    label: "Code Sections",
    value: "500+",
    description: "Florida Building Code provisions covered"
  },
  {
    label: "Projects Validated",
    value: "1,200+", 
    description: "Successful roof design validations"
  }
]

function AnimatedCounter({ value, suffix = "" }: { value: string; suffix?: string }) {
  const [displayValue, setDisplayValue] = useState("0")
  
  useEffect(() => {
    // Extract number from value string
    const numericValue = parseFloat(value.replace(/[^\d.]/g, ''))
    
    if (isNaN(numericValue)) {
      setDisplayValue(value)
      return
    }
    
    const duration = 2000 // 2 seconds
    const steps = 60
    const increment = numericValue / steps
    let current = 0
    
    const timer = setInterval(() => {
      current += increment
      if (current >= numericValue) {
        setDisplayValue(value)
        clearInterval(timer)
      } else {
        setDisplayValue(Math.floor(current).toString())
      }
    }, duration / steps)
    
    return () => clearInterval(timer)
  }, [value])
  
  return (
    <span className="text-5xl lg:text-6xl font-bold text-gradient">
      {displayValue}{suffix}
    </span>
  )
}

export default function StatsSection() {
  return (
    <section className="py-16 section-padding bg-white/50 backdrop-blur-sm">
      <div className="container-width">
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
            Trusted by Professionals
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Our AI-powered validation system has processed thousands of roof designs, 
            helping architects and engineers ensure code compliance.
          </p>
        </motion.div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              className="text-center"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
            >
              <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow duration-300">
                <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                <h3 className="text-xl font-semibold text-gray-900 mt-4 mb-2">
                  {stat.label}
                </h3>
                <p className="text-gray-600 text-sm">
                  {stat.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}