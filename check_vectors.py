import os
from pinecone import Pinecone
from dotenv import load_dotenv
from collections import defaultdict

# 환경 변수 로드
load_dotenv()

# Pinecone 초기화
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("actuary-docs")

def check_index_stats():
    """인덱스 통계 확인"""
    # 인덱스 상태 확인
    stats = index.describe_index_stats()
    print("\n=== 인덱스 통계 ===")
    print(f"총 벡터 수: {stats.total_vector_count}")
    print(f"차원 수: {stats.dimension}")
    
    # 네임스페이스별 벡터 수
    if stats.namespaces:
        print("\n네임스페이스별 벡터 수:")
        for ns, count in stats.namespaces.items():
            print(f"- {ns}: {count}")

def analyze_vectors():
    """벡터 분석"""
    # 전체 벡터 가져오기 (fetch는 한 번에 최대 10000개까지 가능)
    # 먼저 모든 벡터의 ID 목록을 가져옴
    results = index.query(
        vector=[0] * 1536,  # 더미 벡터
        top_k=10000,
        include_metadata=True
    )
    
    print("\n=== 벡터 분석 ===")
    
    # 파일별 벡터 수 계산
    file_counts = defaultdict(int)
    page_counts = defaultdict(int)
    
    for match in results.matches:
        metadata = match.metadata
        if metadata:
            file_name = metadata.get('file_name', 'unknown')
            page = metadata.get('page', 'unknown')
            file_counts[file_name] += 1
            page_counts[f"{file_name} - page {page}"] += 1
    
    print("\n파일별 벡터 수:")
    for file_name, count in file_counts.items():
        print(f"- {file_name}: {count}개")
    
    print("\n페이지별 벡터 수 (상위 10개):")
    sorted_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for page, count in sorted_pages:
        print(f"- {page}: {count}개")

if __name__ == "__main__":
    check_index_stats()
    analyze_vectors() 