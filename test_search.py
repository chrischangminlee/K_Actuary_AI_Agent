import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Pinecone 초기화
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("actuary-docs")

def test_search(query: str, top_k: int = 5):
    """검색 테스트"""
    print(f"\n검색어: {query}")
    
    # 임베딩 생성
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    query_embedding = response.data[0].embedding
    
    # Pinecone 검색
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    print(f"\n=== 검색 결과 (상위 {top_k}개) ===")
    print(f"총 {len(results.matches)}개 결과 발견")
    
    for i, match in enumerate(results.matches):
        metadata = match.metadata
        print(f"\n[결과 {i+1}]")
        print(f"파일: {metadata['file_name']}")
        print(f"페이지: {metadata['page']}")
        print(f"유사도 점수: {match.score}")
        print(f"텍스트 일부: {metadata['text'][:200]}...")

if __name__ == "__main__":
    # IFRS17 관련 검색
    test_search("IFRS17이란 무엇인가요?")
    
    # KIC-S 관련 검색
    test_search("KIC-S란 무엇인가요?") 