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
  // API 라우트를 정적으로 내보내지 않도록 설정
  experimental: {
    appDir: true,
  },
}

module.exports = nextConfig 