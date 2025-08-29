/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost'],
    unoptimized: true, // Better for static deployment
  },
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  },
  // Optimized for cloud deployment
  output: 'standalone',
  experimental: {
    outputFileTracingRoot: undefined,
  },
  // Handle trailing slashes
  trailingSlash: false,
  // Optimize for Vercel deployment
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
}

module.exports = nextConfig