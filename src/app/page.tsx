import ChatInterface from '@/components/ChatInterface';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-4 sm:p-8">
      <div className="w-full max-w-4xl">
        {/* 상단 버튼 영역 */}
        <div className="w-full flex justify-end mb-6">
          <a
            href="https://chrischangminlee.github.io/K_Actuary_AI_Agent_Platform/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium shadow-md"
          >
            K-계리 AI Platform
          </a>
        </div>

        {/* 타이틀과 설명 영역 */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4 text-center">K-Actuary AI Agent</h1>
          <div className="text-sm text-gray-600 space-y-1 text-center">
            <p>본 AI 챗 서비스는 한국 계리업무를 수행하는 계리사를 위해 개발된 개인 프로젝트 기반 AI Chat / Agent입니다.</p>
            <p>현재 다양한 유용한 기능들이 지속적으로 개발 중이며, 보다 향상된 서비스를 제공하기 위해 개선을 이어가고 있습니다.</p>
            <p className="text-red-500">※ 현재 GitHub Pages에서는 API 기능을 사용할 수 없습니다. 로컬 환경에서 실행해주세요.</p>
          </div>
        </div>

        {/* 안내 메시지 */}
        <div className="bg-gray-50 rounded-lg shadow-lg p-8 text-center">
          <h2 className="text-xl font-semibold mb-4">🚧 API 기능 사용 불가 안내</h2>
          <p className="text-gray-600 mb-4">
            GitHub Pages는 정적 웹 호스팅 서비스이기 때문에 API 기능을 사용할 수 없습니다.
          </p>
          <p className="text-gray-600">
            전체 기능을 사용하시려면 로컬 환경에서 실행해주세요.
          </p>
        </div>
      </div>
    </main>
  );
} 