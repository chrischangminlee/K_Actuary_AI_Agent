import os
from pinecone import Pinecone
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Pinecone 초기화
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("actuary-docs")

def delete_all_vectors():
    """인덱스의 모든 벡터 삭제"""
    print("모든 벡터 삭제 중...")
    
    # 인덱스 통계 확인
    stats = index.describe_index_stats()
    total_vectors = stats.total_vector_count
    print(f"현재 총 벡터 수: {total_vectors}")
    
    # 모든 벡터 삭제
    try:
        index.delete(delete_all=True)
        print("모든 벡터가 성공적으로 삭제되었습니다.")
    except Exception as e:
        print(f"삭제 중 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    response = input("정말로 모든 벡터를 삭제하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        delete_all_vectors()
    else:
        print("작업이 취소되었습니다.") 