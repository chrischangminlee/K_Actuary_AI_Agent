import { OpenAIConfig } from '@/types/chat';

// if (!process.env.OPENAI_API_KEY) {
//   throw new Error('OPENAI_API_KEY가 설정되지 않았습니다.');
// }

export const openAIConfig: OpenAIConfig = {
  apiKey: process.env.OPENAI_API_KEY || 'dummy_key',
  model: 'gpt-3.5-turbo',
  temperature: 0.7,
  max_tokens: 500,
}; 