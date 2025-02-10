import { Pinecone } from '@pinecone-database/pinecone';
import { Document } from '@langchain/core/documents';
import { OpenAIEmbeddings } from '@langchain/openai';
import { RecursiveCharacterTextSplitter } from 'langchain/text_splitter';
import { PDFLoader } from '@langchain/community/document_loaders/fs/pdf';
import fs from 'fs';
import path from 'path';

let pinecone: Pinecone | null = null;

export async function initPinecone() {
  if (!pinecone) {
    pinecone = new Pinecone({
      apiKey: process.env.PINECONE_API_KEY!,
    });
  }
  return pinecone;
}

export async function loadPDFContent(filePath: string) {
  const loader = new PDFLoader(filePath);
  const pages = await loader.load();
  return pages;
}

export async function processDocument(document: Document[]) {
  const textSplitter = new RecursiveCharacterTextSplitter({
    chunkSize: 1000,
    chunkOverlap: 200,
  });
  const chunks = await textSplitter.splitDocuments(document);
  return chunks;
}

export async function embedDocuments(chunks: Document[]) {
  const embeddings = new OpenAIEmbeddings({
    openAIApiKey: process.env.OPENAI_API_KEY,
  });
  const vectors = await Promise.all(
    chunks.map(async (chunk) => {
      const embedding = await embeddings.embedQuery(chunk.pageContent);
      return {
        id: `${chunk.metadata.source}-${chunk.metadata.page}-${Date.now()}`,
        values: embedding,
        metadata: {
          text: chunk.pageContent,
          source: chunk.metadata.source,
          page: chunk.metadata.page,
        },
      };
    })
  );
  return vectors;
}

export async function processPDFFiles() {
  const docsDir = path.join(process.cwd(), 'public', 'docs');
  
  try {
    const files = fs.readdirSync(docsDir).filter(file => file.toLowerCase().endsWith('.pdf'));
    
    const pineconeClient = await initPinecone();
    const index = pineconeClient.index('actuary-docs');

    for (const file of files) {
      const filePath = path.join(docsDir, file);
      console.log(`Processing ${file}...`);

      const pages = await loadPDFContent(filePath);
      
      const chunks = await processDocument(pages);
      
      const vectors = await embedDocuments(chunks);
      
      const batchSize = 100;
      for (let i = 0; i < vectors.length; i += batchSize) {
        const batch = vectors.slice(i, i + batchSize);
        await index.upsert(batch);
      }
      
      console.log(`Completed processing ${file}`);
    }
    
    console.log('All PDF files have been processed and uploaded to Pinecone');
    
  } catch (error) {
    console.error('Error processing PDF files:', error);
    throw error;
  }
}

export async function queryPinecone(query: string) {
  const embeddings = new OpenAIEmbeddings({
    openAIApiKey: process.env.OPENAI_API_KEY,
  });
  const queryEmbedding = await embeddings.embedQuery(query);
  
  const pineconeClient = await initPinecone();
  const index = pineconeClient.index('actuary-docs');
  const queryResponse = await index.query({
    vector: queryEmbedding,
    topK: 3,
    includeMetadata: true,
  });

  return queryResponse.matches?.map(match => match.metadata.text).join('\n\n');
} 