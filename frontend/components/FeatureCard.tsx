'use client'

import { motion } from 'framer-motion'

interface Feature {
  icon: React.ComponentType<any>
  title: string
  description: string
  color: 'blue' | 'green' | 'purple' | 'orange'
}

interface FeatureCardProps {
  feature: Feature
  index: number
}

const colorClasses = {
  blue: {
    bg: 'bg-blue-100',
    icon: 'text-blue-600',
    border: 'border-blue-200',
    gradient: 'from-blue-500 to-blue-600'
  },
  green: {
    bg: 'bg-green-100',
    icon: 'text-green-600', 
    border: 'border-green-200',
    gradient: 'from-green-500 to-green-600'
  },
  purple: {
    bg: 'bg-purple-100',
    icon: 'text-purple-600',
    border: 'border-purple-200', 
    gradient: 'from-purple-500 to-purple-600'
  },
  orange: {
    bg: 'bg-orange-100',
    icon: 'text-orange-600',
    border: 'border-orange-200',
    gradient: 'from-orange-500 to-orange-600'
  }
}

export default function FeatureCard({ feature, index }: FeatureCardProps) {
  const colors = colorClasses[feature.color]
  const Icon = feature.icon

  return (
    <motion.div
      className="group relative"
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: index * 0.1 }}
      viewport={{ once: true }}
      whileHover={{ y: -5 }}
    >
      <div className={`card border-2 ${colors.border} group-hover:border-opacity-60 relative overflow-hidden`}>
        {/* Background gradient on hover */}
        <div className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>
        
        {/* Icon */}
        <div className="relative">
          <div className={`w-16 h-16 ${colors.bg} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
            <Icon className={`h-8 w-8 ${colors.icon}`} />
          </div>
          
          {/* Decorative element */}
          <div className={`absolute -top-2 -right-2 w-4 h-4 bg-gradient-to-br ${colors.gradient} rounded-full opacity-60 group-hover:scale-125 transition-transform duration-300`}></div>
        </div>
        
        {/* Content */}
        <div className="relative">
          <h3 className="text-xl font-bold text-gray-900 mb-4 group-hover:text-gray-800 transition-colors">
            {feature.title}
          </h3>
          <p className="text-gray-600 group-hover:text-gray-700 transition-colors leading-relaxed">
            {feature.description}
          </p>
        </div>
        
        {/* Hover indicator */}
        <div className={`absolute bottom-0 left-0 h-1 bg-gradient-to-r ${colors.gradient} w-0 group-hover:w-full transition-all duration-300`}></div>
      </div>
    </motion.div>
  )
}