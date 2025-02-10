import { NextResponse } from 'next/server';
import { Message } from '@/types/chat';

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();
    
    // API 키가 없을 때의 테스트용 응답
    const testResponse = {
      role: 'assistant' as const,
      content: `테스트 응답입니다. 귀하의 메시지: "${messages[messages.length - 1].content}"
      \n현재 OpenAI API가 연결되지 않은 테스트 모드입니다.`,
      timestamp: new Date(),
      status: 'sent' as const,
    };

    // 의도적으로 응답 시간 지연 추가 (실제 API 호출처럼 보이게)
    await new Promise(resolve => setTimeout(resolve, 1000));

    return NextResponse.json(testResponse);
  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json(
      {
        error: '챗봇 응답 중 오류가 발생했습니다.',
      },
      { status: 500 }
    );
  }
} 