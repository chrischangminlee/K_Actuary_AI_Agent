'use client';

import { useState, useEffect } from 'react';
import { Message } from '@/types/chat';

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // 초기 메시지 설정
    setMessages([{
      role: 'assistant',
      content: '안녕하세요, K-Actuary AI Agent입니다. 궁금하신게 있으신가요?',
      timestamp: new Date(),
      status: 'sent'
    }]);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
      status: 'sending',
    };

    setMessages((prev) => [...prev, newMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, newMessage],
        }),
      });

      if (!response.ok) {
        throw new Error('API 응답 오류');
      }

      const data = await response.json();
      
      if (data.error) {
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { ...prev[prev.length - 1], status: 'error' },
          {
            role: 'assistant',
            content: `오류: ${data.error}`,
            timestamp: new Date(),
            status: 'error',
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { ...prev[prev.length - 1], status: 'sent' },
          {
            ...data,
            timestamp: new Date(),
            status: 'sent',
          },
        ]);
      }
    } catch (error) {
      console.error('채팅 요청 오류:', error);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { ...prev[prev.length - 1], status: 'error' },
        {
          role: 'assistant',
          content: '죄송합니다. 요청 처리 중 오류가 발생했습니다.',
          timestamp: new Date(),
          status: 'error',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  return (
    <div className="flex flex-col h-[600px] bg-gray-50 rounded-lg shadow-lg">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            } mb-4`}
          >
            {message.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white mr-2 font-medium">
                AI
              </div>
            )}
            <div className="flex flex-col max-w-[70%]">
              <div
                className={`p-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-green-600 text-white rounded-tr-none'
                    : 'bg-white text-black shadow-md rounded-tl-none'
                }`}
              >
                <p className="whitespace-pre-wrap text-[15px] leading-relaxed">{message.content}</p>
              </div>
              <div 
                className={`text-xs text-gray-500 mt-1 ${
                  message.role === 'user' ? 'text-right' : 'text-left'
                }`}
              >
                {formatTime(message.timestamp)}
                {message.status === 'sending' && ' • 전송중...'}
                {message.status === 'error' && ' • 오류'}
              </div>
            </div>
            {message.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 ml-2 font-medium">
                나
              </div>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="p-4 border-t bg-white rounded-b-lg">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 p-3 border rounded-full focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-[15px]"
            placeholder="메시지를 입력하세요..."
            disabled={isLoading}
          />
          <button
            type="submit"
            className="px-6 py-2 bg-green-600 text-white rounded-full hover:bg-green-700 disabled:bg-green-300 transition-colors font-medium"
            disabled={isLoading}
          >
            전송
          </button>
        </div>
      </form>
    </div>
  );
} 