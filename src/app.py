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
SYSTEM_PROMPT = """당신은 한국의 계리사들을 지원하는 AI 어시스턴트입니다.  
아래 규칙을 반드시 준수해주세요:

1. **출처 표기 필수:**  
   - 답변의 첫 부분에 반드시 "파일명 - 페이지" 형식으로 출처를 기재할 것.
2. **문서 기반 응답:**  
   - 제공된 문서({context})에 포함된 내용만을 활용하여 답변할 것.
   - 문서에 없는 내용은 추가하지 않을 것.
3. **실무 관련 설명:**  
   - 보험료 산출, 준비금 평가, 손해율 가정 등 계리 실무 관련 내용 포함.
4. **법규 및 규정 준수:**  
   - 보험업법, 감독규정, IFRS17 등 관련 규정을 참고하고, 법규 준수 사항 강조.
5. **불확실한 사항 명시:**  
   - 불확실하거나 추가 검토가 필요한 경우, 한계점 및 주의사항을 명확히 언급.

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
    
    # 검색 결과를 문서별로 그룹화
    doc_groups = {
        "IFRS17보험회계해설서_2022.pdf": [],
        "KICS 해설서.pdf": [],
        "보험개발원_20200220_일반손보 위험조정 적용기법 고도화.pdf": [],
        "보험개발원_202203_IFRS17 경제적 가정 실무적용방안.pdf": [],
        "금감원_230302공동재보험 및 재보험 데이터 제공 관련 업무처리 가이드라인.pdf": [],
        "금융위_241106_IFRS17 주요 계리가정 가이드라인.pdf": []
    }
    
    # KIC-S 관련 키워드 확인
    kics_keywords = ["KIC-S", "K-ICS", "KICS", "지급여력"]
    ifrs_keywords = ["IFRS", "IFRS17", "경제적 가정", "계리가정"]
    reinsurance_keywords = ["재보험", "공동재보험"]
    risk_adjustment_keywords = ["위험조정", "리스크마진"]
    
    # 키워드 매칭을 통한 문서 우선순위 결정
    is_kics_related = any(keyword.lower() in query.lower() for keyword in kics_keywords)
    is_ifrs_related = any(keyword.lower() in query.lower() for keyword in ifrs_keywords)
    is_reinsurance_related = any(keyword.lower() in query.lower() for keyword in reinsurance_keywords)
    is_risk_adjustment_related = any(keyword.lower() in query.lower() for keyword in risk_adjustment_keywords)
    
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
    
    for match in results.matches:
        metadata = match.metadata
        doc_key = metadata['file_name']
        if doc_key in doc_groups:
            doc_groups[doc_key].append((match.score, metadata))
    
    # 각 문서에서 가장 관련성 높은 결과 선택
    contexts = []
    target_counts = {
        "KICS 해설서.pdf": 3 if is_kics_related else 1,
        "IFRS17보험회계해설서_2022.pdf": 3 if is_ifrs_related else 1,
        "보험개발원_20200220_일반손보 위험조정 적용기법 고도화.pdf": 3 if is_risk_adjustment_related else 1,
        "보험개발원_202203_IFRS17 경제적 가정 실무적용방안.pdf": 3 if is_ifrs_related else 1,
        "금감원_230302공동재보험 및 재보험 데이터 제공 관련 업무처리 가이드라인.pdf": 3 if is_reinsurance_related else 1,
        "금융위_241106_IFRS17 주요 계리가정 가이드라인.pdf": 3 if is_ifrs_related else 1
    }
    
    # 각 문서에서 결과 선택
    for doc_name, count in target_counts.items():
        matches = sorted(doc_groups[doc_name], key=lambda x: x[0], reverse=True)[:count]
        for score, metadata in matches:
            if score > 0.5:  # 유사도가 일정 수준 이상인 경우만 포함
                print(f"\n[결과] 파일: {metadata['file_name']}, 페이지: {metadata['page']}, 유사도: {score}")
                contexts.append(
                    f"[{metadata['file_name']} - {metadata['page']}페이지]\n{metadata['text']}\n"
                )
    
    if not contexts:  # 유사도가 너무 낮아 결과가 없는 경우
        # 유사도 기준을 낮춰서 다시 시도
        for doc_name, matches in doc_groups.items():
            sorted_matches = sorted(matches, key=lambda x: x[0], reverse=True)[:1]
            for score, metadata in sorted_matches:
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
            {"role": "assistant", "content": "안녕하세요, K-Actuary AI Assistant입니다. 보험계리 관련 질문이 있으시다면 말씀해주세요. 좌측 참고된 pdf의 문서를 참고하여 답변을 드립니다."}
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
        - 본 AI 챗 서비스는 한국 계리업무를 수행하는 계리사를 위해 개발된 개인 프로젝트로 만들어진 AI Chatbot / Agent입니다.
        - RAG(검색증강생성)에 더불어 현재 다양한 유용한 기능들이 지속적으로 개발 중이며, 보다 향상된 서비스를 제공하기 위해 개선을 이어가고 있습니다.
        """)
        st.markdown('<p style="color: black; font-size: 12px;">- 현재 API 비용이 가장 저렴한 LLM인 gpt3.5-turbo를 사용하고 있어 기대보다 성능이 떨어질 수 있습니다.</p>', unsafe_allow_html=True)
        st.markdown('<p style="color: red; font-size: 12px;">* (주의) 본 AI가 제공하는 답변은 참고용이며, 정확성을 보장할 수 없습니다. 보안을 위해 회사 기밀, 개인정보등은 제공하지 않기를 권장드리며, 반드시 실제 업무에 적용하기 전에 검토하시길 바랍니다.</p>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown('[개발자 Linkedin](https://www.linkedin.com/in/chrislee9407/)')
        st.markdown('[K-계리 AI 플랫폼](https://chrischangminlee.github.io/K_Actuary_AI_Agent_Platform/)')
        
        # 이미지 표시
        try:
            st.markdown("### 챗봇 개발 구조도")
            st.image("KActuaryAgentStructure_021425.png", use_column_width=True, caption="우측 확대 버튼 클릭하여 크게 보기")
        except Exception as e:
            st.warning("구조도 이미지를 불러올 수 없습니다.")
        
        st.markdown("---")
        st.markdown("### 참고된 pdf")
        st.markdown("""
        - IFRS17보험회계해설서_2022.pdf
        - KICS 해설서.pdf
        - 보험개발원_20200220_일반손보 위험조정 적용기법 고도화.pdf
        - 보험개발원_202203_IFRS17 경제적 가정 실무적용방안.pdf
        - 금감원_230302공동재보험 및 재보험 데이터 제공 관련 업무처리 가이드라인.pdf
        - 금융위_241106_IFRS17 주요 계리가정 가이드라인.pdf
        """)
        
    
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