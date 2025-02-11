import streamlit as st
import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Pinecone 초기화
pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pinecone.Index('actuary-docs')

# 시스템 프롬프트 설정
SYSTEM_PROMPT = """당신은 한국의 계리사들을 돕는 AI 어시스턴트입니다.
전문성과 정확성을 바탕으로 다음 원칙을 따라 응답해주세요:

오직 제공된 문서 내용을 기반으로 답변하고, 문서에 없는 내용에 대해서는 답변하지 마세요.
답변 시 참고한 문서의 내용을 반드시 해당 파일명과 페이지를 인용하여 설명해주세요.

보험료 산출, 준비금 평가, 손해율 가정 등 계리적 가정과 모델과 같은 실무에 필요한 설명을 제공하세요.

1. 관련 법규와 규정을 고려하여 조언
   - 보험업법, 감독규정, IFRS17 등 관련 규정 참조
   - 법규 준수 사항 강조

2. 불확실한 내용에 대해서는 명확히 한계점 언급
   - 추가 검토나 전문가 확인이 필요한 사항 명시
   - 가정이나 제한사항 명확히 설명"""

def query_pinecone(query):
    """Pinecone에서 관련 문서 검색"""
    # 쿼리 임베딩 생성
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # Pinecone 검색
    results = index.query(
        vector=query_embedding,
        top_k=3,
        include_metadata=True
    )
    
    # 검색 결과 텍스트 조합
    contexts = []
    for match in results.matches:
        metadata = match.metadata
        contexts.append(
            f"[{metadata['source']} - {metadata['page']}페이지, {metadata['type']}]\n{metadata['text']}"
        )
    
    return "\n\n".join(contexts)

def get_ai_response(query, context):
    """OpenAI API를 사용하여 응답 생성"""
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"다음은 질문과 관련된 문서 내용입니다:\n\n{context}"},
            {"role": "user", "content": query}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content

def initialize_session_state():
    """세션 상태 초기화"""
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "안녕하세요, K-Actuary AI Agent입니다. 궁금하신 점이 있으시다면 말씀해주세요."}
        ]

def main():
    st.set_page_config(
        page_title="K-Actuary AI Agent",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("K-Actuary AI Agent")
    
    # 세션 상태 초기화
    initialize_session_state()
    
    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input():
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하고 있습니다..."):
                # 관련 문서 검색
                context = query_pinecone(prompt)
                
                # AI 응답 생성
                response = get_ai_response(prompt, context)
                
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 