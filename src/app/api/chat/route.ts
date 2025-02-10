import { OpenAI } from 'openai';
import { NextResponse } from 'next/server';
import { queryPinecone, initPinecone } from '@/utils/pdf';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Pinecone 초기화
initPinecone();

const systemPrompt = `당신은 한국의 계리사들을 돕는 AI 어시스턴트입니다.
전문성과 정확성을 바탕으로 다음 원칙을 따라 응답해주세요:

오직 제공된 문서 내용을 기반으로 답변하고, 문서에 없는 내용에 대해서는 답변하지마세요.
답변 시 참고한 문서의 내용을 반드시 해당 파일명과 페이지를 인용하여 설명해주세요. 

보험료 산출, 준비금 평가, 손해율 가정 등 계리적 가정과 모델와 같은 실무에 필요한 설명 제공

1. 관련 법규와 규정을 고려하여 조언
   - 보험업법, 감독규정, IFRS17 등 관련 규정 참조
   - 법규 준수 사항 강조

2. 불확실한 내용에 대해서는 명확히 한계점 언급
   - 추가 검토나 전문가 확인이 필요한 사항 명시
   - 가정이나 제한사항 명확히 설명

`;

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();
    const userMessage = messages[messages.length - 1].content;

    // 관련 문서 검색
    const relevantDocs = await queryPinecone(userMessage);
    
    const response = await openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        { role: "system", content: systemPrompt },
        // 문서 컨텍스트 추가
        { 
          role: "system", 
          content: `다음은 질문과 관련된 문서 내용입니다:\n\n${relevantDocs || '관련 문서가 없습니다.'}`
        },
        ...messages.map((msg: any) => ({
          role: msg.role,
          content: msg.content
        }))
      ],
      temperature: 0.7,
      max_tokens: 2000,
      presence_penalty: 0.1,
      frequency_penalty: 0.1,
    });

    return NextResponse.json({
      role: "assistant",
      content: response.choices[0].message.content
    });

  } catch (error) {
    console.error('OpenAI API 오류:', error);
    return NextResponse.json(
      { error: '죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
} 