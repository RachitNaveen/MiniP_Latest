import React, { useRef, useEffect } from 'react';
import { MessageItem } from './MessageItem';

interface Message {
  id: number;
  content: string;
  sender: string;
  recipient: string;
  timestamp: string;
  isLocked: boolean;
  filePath?: string;
}

interface ChatMessagesProps {
  messages: Message[];
  currentUsername: string;
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, currentUsername }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 bg-muted p-4 rounded-lg mb-4 overflow-y-auto">
      {messages.length > 0 ? (
        <>
          {messages.map(message => (
            <MessageItem 
              key={message.id} 
              message={message} 
              isCurrentUser={message.sender === currentUsername}
            />
          ))}
          <div ref={messagesEndRef}></div>
        </>
      ) : (
        <div className="flex items-center justify-center h-full">
          <p className="text-medium-text">No messages yet. Start a conversation!</p>
        </div>
      )}
    </div>
  );
};
