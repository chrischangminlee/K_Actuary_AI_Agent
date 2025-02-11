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