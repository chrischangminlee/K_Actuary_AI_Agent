import os
from pinecone import Pinecone
from dotenv import load_dotenv
from collections import defaultdict
import hashlib

# 환경 변수 로드
load_dotenv()

# Pinecone 초기화
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("actuary-docs")

def get_content_hash(text):
    """텍스트의 해시값 생성"""
    return hashlib.md5(text.encode()).hexdigest()

def find_duplicates():
    """중복된 벡터 찾기"""
    # 전체 벡터 가져오기
    results = index.query(
        vector=[0] * 1536,  # 더미 벡터
        top_k=10000,
        include_metadata=True
    )
    
    # 페이지별 텍스트 해시 저장
    content_hashes = defaultdict(list)
    for match in results.matches:
        metadata = match.metadata
        if metadata:
            text = metadata.get('text', '')
            file_name = metadata.get('file_name', '')
            page = metadata.get('page', '')
            content_hash = get_content_hash(text)
            content_hashes[f"{file_name}_{page}_{content_hash}"].append(match)
    
    # 중복 확인
    print("\n=== 중복 검사 결과 ===")
    total_duplicates = 0
    for key, matches in content_hashes.items():
        if len(matches) > 1:
            file_name = matches[0].metadata['file_name']
            page = matches[0].metadata['page']
            print(f"\n파일: {file_name}, 페이지: {page}")
            print(f"중복 수: {len(matches)}")
            total_duplicates += len(matches) - 1
    
    print(f"\n총 중복 벡터 수: {total_duplicates}")
    return content_hashes

def remove_duplicates(content_hashes):
    """중복된 벡터 제거"""
    print("\n=== 중복 벡터 제거 ===")
    total_removed = 0
    
    for matches in content_hashes.values():
        if len(matches) > 1:
            # 첫 번째를 제외한 나머지 삭제
            ids_to_delete = [match.id for match in matches[1:]]
            try:
                index.delete(ids=ids_to_delete)
                total_removed += len(ids_to_delete)
                print(f"{len(ids_to_delete)}개 벡터 삭제 완료")
            except Exception as e:
                print(f"삭제 중 오류 발생: {str(e)}")
    
    print(f"\n총 {total_removed}개의 중복 벡터가 제거되었습니다.")

if __name__ == "__main__":
    print("중복 벡터 검사 중...")
    content_hashes = find_duplicates()
    
    response = input("\n중복된 벡터를 제거하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        remove_duplicates(content_hashes)
    else:
        print("작업이 취소되었습니다.") 