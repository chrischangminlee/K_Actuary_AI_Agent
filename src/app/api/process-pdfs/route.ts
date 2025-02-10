import { NextResponse } from 'next/server';
import { processPDFFiles } from '@/utils/pdf';

export const dynamic = 'force-dynamic';

export async function POST() {
  try {
    await processPDFFiles();
    return NextResponse.json({ message: 'PDF files processed successfully' });
  } catch (error) {
    console.error('Error processing PDF files:', error);
    return NextResponse.json(
      { error: 'PDF 파일 처리 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
} 