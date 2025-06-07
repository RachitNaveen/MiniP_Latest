import React, { ReactNode } from 'react';

interface ChatLayoutProps {
  children: ReactNode;
}

export const ChatLayout: React.FC<ChatLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#e9ecef]">
      {children}
    </div>
  );
};
