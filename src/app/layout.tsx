import './globals.css';

export const metadata = {
  title: 'K-Actuary AI Agent',
  description: '한국 계리사를 위한 AI 챗봇 서비스',
  icons: {
    icon: [
      {
        url: '/K_Actuary_AI_Agent/favicon.svg',
        type: 'image/svg+xml',
      },
    ],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <head>
        <link 
          rel="icon" 
          href="/K_Actuary_AI_Agent/favicon.svg" 
          type="image/svg+xml"
        />
      </head>
      <body>{children}</body>
    </html>
  )
}
