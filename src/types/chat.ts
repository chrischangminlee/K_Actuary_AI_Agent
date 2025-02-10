export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
}

export interface ChatHistory {
  messages: Message[];
}

export interface OpenAIConfig {
  apiKey: string;
  model: string;
  temperature: number;
  max_tokens: number;
}

export interface ChatCompletionResponse {
  role: 'assistant';
  content: string;
} 