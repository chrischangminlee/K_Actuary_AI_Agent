# 기존 코드 주석 처리
'''
import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
import fitz  # PyMuPDF

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Pinecone 초기화
pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pinecone.Index('actuary-docs')

def process_pdf(pdf_path):
    """PDF 파일에서 텍스트만 추출"""
    doc = fitz.open(pdf_path)
    content = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 텍스트 추출
        text = page.get_text()
        if text.strip():  # 빈 텍스트가 아닌 경우에만 추가
            content.append({
                "type": "text",
                "content": text,
                "page": page_num + 1
            })
    
    return content

def create_embeddings(content, pdf_path):
    """컨텐츠를 임베딩하여 Pinecone에 저장"""
    for item in content:
        text = item["content"]
        page = item["page"]
        
        # 텍스트가 너무 긴 경우 분할
        max_length = 8000  # OpenAI API 제한
        text_chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        for chunk_idx, chunk in enumerate(text_chunks):
            try:
                # OpenAI API로 임베딩 생성
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=chunk
                )
                embedding = response.data[0].embedding
                
                # Pinecone에 저장
                index.upsert(
                    vectors=[{
                        "id": f"{os.path.basename(pdf_path)}-{page}-{chunk_idx}",
                        "values": embedding,
                        "metadata": {
                            "text": chunk,
                            "page": page,
                            "source": os.path.basename(pdf_path)
                        }
                    }]
                )
                print(f"Successfully processed chunk {chunk_idx} from page {page}")
            except Exception as e:
                print(f"Warning: Failed to process chunk {chunk_idx} from page {page}: {e}")

if __name__ == "__main__":
    pdf_dir = "data/pdfs"
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, pdf_file)
            print(f"Processing {pdf_file}...")
            
            try:
                # PDF 처리
                content = process_pdf(pdf_path)
                
                # 임베딩 생성 및 저장
                create_embeddings(content, pdf_path)
                
                print(f"Completed processing {pdf_file}")
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")
'''

# 새로운 코드
import os
import pdfplumber
from pinecone import Pinecone
from openai import OpenAI
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
import hashlib

load_dotenv()  # .env 파일 로드 (OPENAI_API_KEY, PINECONE_API_KEY 등)

# Pinecone 및 OpenAI 설정
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")  # 예: "us-west1-gcp"

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    
    for i, ch in enumerate(chunks):
        text = ch["text"]
        page_num = ch["page"]
        
        # 텍스트 해시 생성
        text_hash = get_text_hash(text)
        
        # 이미 처리된 텍스트는 건너뛰기
        if text_hash in processed_hashes:
            print(f"중복된 텍스트 발견 - 건너뛰기 (페이지 {page_num})")
            continue
        
        processed_hashes.add(text_hash)
        print(f"청크 {i+1}/{len(chunks)} 처리 중 (페이지 {page_num})")
        
        try:
            # OpenAI Embedding API 호출
            print("OpenAI API 호출 중...")
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            print("임베딩 생성 완료")
            
            # Pinecone에 upsert - 텍스트 해시를 ID에 포함
            vector_id = f"{ascii_file_name}_p{page_num}_{text_hash[:16]}"
            print("Pinecone에 업서트 중...")
            index.upsert([
                (
                    vector_id,
                    embedding,
                    {"file_name": file_name, "page": page_num, "text": text}
                )
            ])
            print("업서트 완료")
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            raise

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
    # 필요에 따라 여러 pdf ingest
    pdf_dir = "data/pdfs"
    ingest_pdf(os.path.join(pdf_dir, "IFRS17보험회계해설서_2022.pdf"))
    ingest_pdf(os.path.join(pdf_dir, "KICS 해설서.pdf"))
    print("모든 PDF Ingest 완료!") 