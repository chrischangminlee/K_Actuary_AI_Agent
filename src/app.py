import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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
   - 가정이나 제한사항 명확히 설명"""

def get_ai_response(query, temperature=0.7):
    """OpenAI API를 사용하여 응답 생성"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
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
        st.markdown('<p style="color: red;">- (주의) 본 AI가 제공하는 답변은 참고용이며, 정확성을 보장할 수 없습니다. 반드시 실제 업무에 적용하기 전에 검토하시길 바랍니다.</p>', unsafe_allow_html=True)
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