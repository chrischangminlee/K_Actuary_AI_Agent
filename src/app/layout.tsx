import './globals.css';

export const metadata = {
  title: 'K-Actuary AI Agent',
  description: '한국 계리사를 위한 AI 챗봇 서비스',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
