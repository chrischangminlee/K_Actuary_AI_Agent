import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
from pinecone import Pinecone

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"],
    timeout=60.0  # 타임아웃 설정 추가
)

# Pinecone 초기화
pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
index = pc.Index("actuary-docs")

# 시스템 프롬프트 설정
SYSTEM_PROMPT = """당신은 한국의 계리사들을 돕는 AI 어시스턴트입니다.
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

아래는 사용자의 질문과 관련된 문서 내용입니다:
{context}

위 문서 내용을 바탕으로 답변해주세요."""

def get_relevant_context(query, top_k=5):
    """사용자 질문과 관련된 문서 검색"""
    # 임베딩 생성
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # KIC-S 관련 키워드 확인
    kics_keywords = ["KIC-S", "K-ICS", "KICS", "지급여력"]
    is_kics_related = any(keyword.lower() in query.lower() for keyword in kics_keywords)
    
    # Pinecone 검색 - 더 많은 결과를 가져옴
    results = index.query(
        vector=query_embedding,
        top_k=top_k * 4,  # 더 많은 결과를 가져와서 필터링
        include_metadata=True
    )
    
    # 디버깅을 위해 검색 결과 출력
    print("\n=== 검색 결과 ===")
    print(f"총 {len(results.matches)}개 결과 발견")
    print(f"KIC-S 관련 쿼리: {is_kics_related}")
    
    # 검색 결과를 문서별로 그룹화
    doc_groups = {
        "IFRS17보험회계해설서_2022.pdf": [],
        "KICS 해설서.pdf": []
    }
    
    for match in results.matches:
        metadata = match.metadata
        doc_key = metadata['file_name']
        if doc_key in doc_groups:
            doc_groups[doc_key].append((match.score, metadata))
    
    # 각 문서에서 가장 관련성 높은 결과 선택
    contexts = []
    
    # KIC-S 관련 쿼리인 경우 KIC-S 문서에서 더 많은 결과를 가져옴
    if is_kics_related:
        kics_count = 3
        ifrs_count = 2
    else:
        kics_count = 2
        ifrs_count = 3
    
    # KIC-S 해설서에서 결과 선택
    kics_matches = sorted(doc_groups["KICS 해설서.pdf"], key=lambda x: x[0], reverse=True)[:kics_count]
    for score, metadata in kics_matches:
        if score > 0.5:  # 유사도가 일정 수준 이상인 경우만 포함
            print(f"\n[결과] 파일: {metadata['file_name']}, 페이지: {metadata['page']}, 유사도: {score}")
            contexts.append(
                f"[{metadata['file_name']} - {metadata['page']}페이지]\n{metadata['text']}\n"
            )
    
    # IFRS17 해설서에서 결과 선택
    ifrs_matches = sorted(doc_groups["IFRS17보험회계해설서_2022.pdf"], key=lambda x: x[0], reverse=True)[:ifrs_count]
    for score, metadata in ifrs_matches:
        if score > 0.5:  # 유사도가 일정 수준 이상인 경우만 포함
            print(f"\n[결과] 파일: {metadata['file_name']}, 페이지: {metadata['page']}, 유사도: {score}")
            contexts.append(
                f"[{metadata['file_name']} - {metadata['page']}페이지]\n{metadata['text']}\n"
            )
    
    if not contexts:  # 유사도가 너무 낮아 결과가 없는 경우
        # 유사도 기준을 낮춰서 다시 시도
        for matches in [kics_matches, ifrs_matches]:
            for score, metadata in matches:
                print(f"\n[결과] 파일: {metadata['file_name']}, 페이지: {metadata['page']}, 유사도: {score}")
                contexts.append(
                    f"[{metadata['file_name']} - {metadata['page']}페이지]\n{metadata['text']}\n"
                )
                if len(contexts) >= 3:
                    break
    
    return "\n\n".join(contexts[:5])

def get_ai_response(query, temperature=0.7):
    """OpenAI API를 사용하여 응답 생성"""
    # 관련 문서 검색
    context = get_relevant_context(query)
    
    # 시스템 메시지를 첫 번째로 추가
    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]
    
    # 최근 10개의 대화 기록을 추가
    recent_messages = st.session_state.messages[-10:] if len(st.session_state.messages) > 10 else st.session_state.messages
    messages.extend(recent_messages)
    
    # 현재 질문 추가
    messages.append({"role": "user", "content": query})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=temperature,
        max_tokens=2000
    )
    
    return response.choices[0].message.content

def initialize_session_state():
    """세션 상태 초기화"""
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "안녕하세요, K-Actuary AI Assistant입니다. 보험계리 관련 질문이 있으시다면 말씀해주세요."}
        ]
    if 'temperature' not in st.session_state:
        st.session_state.temperature = 0.7

def set_custom_theme():
    """커스텀 테마 설정"""
    st.markdown("""
        <style>
        .stApp {
            background-color: #f5f5f5;
        }
        .css-1d391kg {
            padding: 1rem 1rem;
        }
        .stChatMessage {
            background-color: white;
            border-radius: 15px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="K Actuary AI Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 커스텀 테마 적용
    set_custom_theme()
    
    # 세션 상태 초기화
    initialize_session_state()
    
    # 사이드바
    with st.sidebar:
        st.markdown("### 소개")
        st.markdown("""
        - 본 AI 챗 서비스는 한국 계리업무를 수행하는 계리사를 위해 개발된 개인 프로젝트 기반 AI Chat / Agent입니다.
        - 현재 다양한 유용한 기능들이 지속적으로 개발 중이며, 보다 향상된 서비스를 제공하기 위해 개선을 이어가고 있습니다.
        """)
        st.markdown('<p style="color: red; font-size: 12px;">- (주의) 본 AI가 제공하는 답변은 참고용이며, 정확성을 보장할 수 없습니다. 보안을 위해 회사 기밀, 개인정보등은 제공하지 않기를 권장드리며, 반드시 실제 업무에 적용하기 전에 검토하시길 바랍니다.</p>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### 참고된 pdf")
        st.markdown("""
        - IFRS17보험회계해설서_2022.pdf
        - KIC-S 해설서.pdf
        """)
        st.markdown("---")
        st.markdown('[개발자 Linkedin](https://www.linkedin.com/in/chrislee9407/)')
        st.markdown('[K-계리 AI 플랫폼](https://chrischangminlee.github.io/K_Actuary_AI_Agent_Platform/)')
    
    # 메인 영역
    st.title("K Actuary AI Agent")
    st.markdown("---")
    
    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("질문을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하고 있습니다..."):
                response = get_ai_response(prompt, st.session_state.temperature)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 