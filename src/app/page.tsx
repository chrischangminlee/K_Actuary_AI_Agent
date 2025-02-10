import ChatInterface from '@/components/ChatInterface';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="w-full max-w-4xl">
        <h1 className="text-4xl font-bold mb-4 text-center">K-Actuary AI Agent</h1>
        <div className="text-sm text-gray-600 mb-8 space-y-4 text-center">
          <p>본 AI 챗 서비스는 한국 계리업무를 수행하는 계리사를 위해 개발된 개인 프로젝트 기반 AI Chat / Agent입니다.</p>
          <p>현재 다양한 유용한 기능들이 지속적으로 개발 중이며, 보다 향상된 서비스를 제공하기 위해 개선을 이어가고 있습니다.</p>
          <p className="text-red-500">※ 본 AI가 제공하는 답변은 참고용이며, 정확성을 보장할 수 없습니다. 반드시 실제 업무에 적용하기 전에 검토하시길 바랍니다.</p>
        </div>
        <ChatInterface />
      </div>
    </main>
  );
} 