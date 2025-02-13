# 새로운 코드
import os
import pdfplumber
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib
import sys

# 즉시 출력을 위한 설정
sys.stdout.flush()

print("스크립트 시작...")
print("환경 변수 로드 중...")
load_dotenv()  # .env 파일 로드 (OPENAI_API_KEY, PINECONE_API_KEY 등)

print("API 키 확인 중...")
# Pinecone 및 OpenAI 설정
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")

if not PINECONE_API_KEY:
    print("오류: PINECONE_API_KEY가 설정되지 않았습니다.")
    sys.exit(1)

print("OpenAI 클라이언트 초기화 중...")
# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("Pinecone 초기화 중...")
# Pinecone 초기화
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("actuary-docs")  # 이미 생성된 인덱스 사용

def get_pdf_texts(pdf_file_path: str) -> list:
    """
    PDF를 페이지 단위로 읽어서 [(page_number, page_text), ...] 형태로 반환.
    """
    print(f"PDF 파일 읽기 시작: {pdf_file_path}")
    texts = []
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            print(f"총 {len(pdf.pages)}페이지 발견")
            for i, page in enumerate(pdf.pages):
                print(f"페이지 {i+1} 처리 중...")
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    texts.append((i+1, page_text))
                    print(f"페이지 {i+1} 텍스트 추출 완료 (길이: {len(page_text)})")
    except Exception as e:
        print(f"PDF 읽기 오류: {str(e)}")
        raise
    return texts

def chunk_texts(texts: list, chunk_size=500, chunk_overlap=50) -> list:
    """
    LangChain의 RecursiveCharacterTextSplitter를 이용해 chunk list 반환.
    texts = [(page_number, page_text), ...]
    반환 형식 예: [{"page": page_number, "text": chunk_text}, ... ]
    """
    print(f"텍스트 분할 시작 (총 {len(texts)}개 텍스트)")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    chunked = []
    for page_num, page_text in texts:
        print(f"페이지 {page_num} 텍스트 분할 중...")
        chunks = splitter.split_text(page_text)
        print(f"페이지 {page_num}: {len(chunks)}개의 청크 생성됨")
        for chunk in chunks:
            chunked.append({
                "page": page_num,
                "text": chunk
            })
    print(f"총 {len(chunked)}개의 청크 생성 완료")
    return chunked

def get_text_hash(text: str) -> str:
    """텍스트의 해시값 생성"""
    return hashlib.md5(text.encode()).hexdigest()

def embed_and_upsert(chunks: list, file_name: str):
    """
    chunked 텍스트를 OpenAI 임베딩으로 변환 → Pinecone에 upsert
    chunks: [{"page": ~, "text": ~ }, ... ]
    """
    print(f"임베딩 및 업서트 시작 (총 {len(chunks)}개 청크)")
    # 파일명에서 한글 제거하고 영문/숫자만 유지
    ascii_file_name = ''.join(c for c in file_name if ord(c) < 128)
    print(f"ASCII 파일명: {ascii_file_name}")
    
    # 이미 처리된 텍스트 해시 추적
    processed_hashes = set()
    vectors_to_upsert = []
    batch_size = 50  # 한 번에 처리할 벡터 수
    
    for i, ch in enumerate(chunks, 1):
        try:
            text = ch["text"]
            page_num = ch["page"]
            
            # 텍스트 해시 생성
            text_hash = get_text_hash(text)
            
            # 이미 처리된 텍스트는 건너뛰기
            if text_hash in processed_hashes:
                print(f"중복된 텍스트 발견 - 건너뛰기 (페이지 {page_num})")
                continue
            
            processed_hashes.add(text_hash)
            print(f"청크 {i}/{len(chunks)} 처리 중 (페이지 {page_num})")
            
            # OpenAI Embedding API 호출
            print(f"OpenAI API 호출 중... (청크 {i})")
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            print(f"임베딩 생성 완료 (청크 {i})")
            
            # 벡터 준비
            vector_id = f"{ascii_file_name}_p{page_num}_{text_hash[:16]}"
            vectors_to_upsert.append(
                (
                    vector_id,
                    embedding,
                    {"file_name": file_name, "page": page_num, "text": text}
                )
            )
            
            # 배치 크기에 도달하면 업서트 실행
            if len(vectors_to_upsert) >= batch_size:
                print(f"\n배치 업서트 실행 중... ({len(vectors_to_upsert)}개 벡터)")
                try:
                    index.upsert(vectors=vectors_to_upsert)
                    print("배치 업서트 완료")
                    vectors_to_upsert = []  # 벡터 리스트 초기화
                except Exception as e:
                    print(f"배치 업서트 중 오류 발생: {str(e)}")
                    # 실패한 경우 배치 크기를 줄여서 재시도
                    if len(vectors_to_upsert) > 10:
                        print("배치 크기를 줄여서 재시도합니다...")
                        for small_batch in [vectors_to_upsert[i:i+10] for i in range(0, len(vectors_to_upsert), 10)]:
                            try:
                                index.upsert(vectors=small_batch)
                                print(f"작은 배치 업서트 성공 ({len(small_batch)}개)")
                            except Exception as e2:
                                print(f"작은 배치 업서트 실패: {str(e2)}")
                    vectors_to_upsert = []
            
        except Exception as e:
            print(f"청크 {i} 처리 중 오류 발생: {str(e)}")
            continue
    
    # 남은 벡터들 처리
    if vectors_to_upsert:
        print(f"\n마지막 배치 업서트 실행 중... ({len(vectors_to_upsert)}개 벡터)")
        try:
            index.upsert(vectors=vectors_to_upsert)
            print("마지막 배치 업서트 완료")
        except Exception as e:
            print(f"마지막 배치 업서트 중 오류 발생: {str(e)}")
            # 실패한 경우 배치 크기를 줄여서 재시도
            print("배치 크기를 줄여서 재시도합니다...")
            for small_batch in [vectors_to_upsert[i:i+10] for i in range(0, len(vectors_to_upsert), 10)]:
                try:
                    index.upsert(vectors=small_batch)
                    print(f"작은 배치 업서트 성공 ({len(small_batch)}개)")
                except Exception as e2:
                    print(f"작은 배치 업서트 실패: {str(e2)}")
    
    print("모든 벡터 업서트 완료")

def ingest_pdf(pdf_file_path: str):
    """
    PDF 하나를 파이프라인에 태워서 pinecone에 저장
    """
    print(f"\n=== PDF 처리 시작: {pdf_file_path} ===")
    file_name = os.path.basename(pdf_file_path)
    try:
        # 1) PDF -> 텍스트 추출
        print("1. PDF 텍스트 추출 단계")
        texts = get_pdf_texts(pdf_file_path)
        
        # 2) 텍스트 분할
        print("\n2. 텍스트 분할 단계")
        chunks = chunk_texts(texts, chunk_size=500, chunk_overlap=50)
        
        # 3) 임베딩 후 Pinecone 저장
        print("\n3. 임베딩 및 저장 단계")
        embed_and_upsert(chunks, file_name)
        
        print(f"\n=== {pdf_file_path} 처리 완료 ===")
    except Exception as e:
        print(f"\n!!! {pdf_file_path} 처리 중 오류 발생: {str(e)} !!!")
        raise

if __name__ == "__main__":
    print("\n=== PDF 처리 시작 ===")
    # 필요에 따라 여러 pdf ingest
    pdf_dir = "data/pdfs"
    
    # 모든 PDF 파일 처리
    pdf_files = [
        "IFRS17보험회계해설서_2022.pdf",
        "KICS 해설서.pdf",
        "보험개발원_20200220_일반손보 위험조정 적용기법 고도화.pdf",
        "보험개발원_202203_IFRS17 경제적 가정 실무적용방안.pdf",
        "금감원_230302공동재보험 및 재보험 데이터 제공 관련 업무처리 가이드라인.pdf",
        "금융위_241106_IFRS17 주요 계리가정 가이드라인.pdf"
    ]
    
    print(f"\n처리할 PDF 파일 목록:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"{i}. {pdf_file}")
    
    for pdf_file in pdf_files:
        try:
            print(f"\n=== {pdf_file} 처리 시작 ===")
            pdf_path = os.path.join(pdf_dir, pdf_file)
            
            # 파일 존재 여부 확인
            if not os.path.exists(pdf_path):
                print(f"오류: {pdf_file} 파일을 찾을 수 없습니다!")
                continue
                
            print(f"파일 크기: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB")
            ingest_pdf(os.path.join(pdf_dir, pdf_file))
            print(f"=== {pdf_file} 처리 완료 ===")
        except Exception as e:
            print(f"!!! {pdf_file} 처리 중 오류 발생: {str(e)} !!!")
            print("스택 트레이스:")
            import traceback
            print(traceback.format_exc())
    
    print("\n모든 PDF 처리가 완료되었습니다!") 