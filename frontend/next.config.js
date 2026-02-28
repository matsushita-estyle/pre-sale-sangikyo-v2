/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // Static export for Azure Static Web Apps
  images: {
    unoptimized: true,  // Required for static export
  },
  // API calls to backend
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig
