import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

# 환경 변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Pinecone 초기화
pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pinecone.Index('actuary-docs')

def extract_text_from_image(image):
    """이미지에서 텍스트 추출"""
    return pytesseract.image_to_string(image, lang='kor+eng')

def process_table(image):
    """표 이미지 처리 및 텍스트 추출"""
    # 여기에 표 처리 로직 추가
    # 예: tabula-py 또는 camelot-py 사용
    return extract_text_from_image(image)

def process_graph(image):
    """그래프 이미지 처리 및 설명 생성"""
    # 이미지를 base64로 인코딩
    img_bytes = image.tobytes()
    
    # OpenAI Vision API를 사용하여 그래프 설명 생성
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이 그래프를 자세히 설명해주세요. 데이터의 추세, 주요 포인트, 의미 등을 포함해주세요."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_bytes}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    return response.choices[0].message.content

def process_pdf(pdf_path):
    """PDF 파일 처리"""
    doc = fitz.open(pdf_path)
    content = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 텍스트 추출
        text = page.get_text()
        content.append({"type": "text", "content": text, "page": page_num + 1})
        
        # 이미지 추출
        images = page.get_images(full=True)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # PIL 이미지로 변환
            image = Image.frombytes("RGB", [base_image["width"], base_image["height"]], image_bytes)
            
            # 이미지 분석 (표, 그래프, 일반 이미지 구분)
            # 여기에 이미지 분류 로직 추가
            image_type = "graph"  # 예시로 모든 이미지를 그래프로 처리
            
            if image_type == "table":
                extracted_text = process_table(image)
                content.append({
                    "type": "table",
                    "content": extracted_text,
                    "page": page_num + 1
                })
            elif image_type == "graph":
                description = process_graph(image)
                content.append({
                    "type": "graph",
                    "content": description,
                    "page": page_num + 1
                })
            else:
                extracted_text = extract_text_from_image(image)
                content.append({
                    "type": "image",
                    "content": extracted_text,
                    "page": page_num + 1
                })
    
    return content

def create_embeddings(content):
    """컨텐츠를 임베딩하여 Pinecone에 저장"""
    for item in content:
        text = item["content"]
        page = item["page"]
        content_type = item["type"]
        
        # OpenAI API로 임베딩 생성
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        
        # Pinecone에 저장
        index.upsert(
            vectors=[{
                "id": f"{os.path.basename(pdf_path)}-{page}-{content_type}",
                "values": embedding,
                "metadata": {
                    "text": text,
                    "page": page,
                    "type": content_type,
                    "source": os.path.basename(pdf_path)
                }
            }]
        )

if __name__ == "__main__":
    pdf_dir = "../data/pdfs"
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, pdf_file)
            print(f"Processing {pdf_file}...")
            
            # PDF 처리
            content = process_pdf(pdf_path)
            
            # 임베딩 생성 및 저장
            create_embeddings(content)
            
            print(f"Completed processing {pdf_file}") 