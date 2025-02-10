/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: '/K_Actuary_AI_Agent',
  images: {
    unoptimized: true,
  },
  env: {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  },
}

module.exports = nextConfig 