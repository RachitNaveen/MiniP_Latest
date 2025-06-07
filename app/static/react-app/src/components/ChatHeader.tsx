import React from 'react';
import { Button } from './ui/button';
import { useSecurity } from '@/context/SecurityContext';

interface ChatHeaderProps {
  username: string;
  onLogout: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ username, onLogout }) => {
  const { riskLevel } = useSecurity();

  return (
    <header className="bg-primary text-white p-4 flex justify-between items-center">
      <h2 className="text-2xl font-bold">SecureChat</h2>
      <div className="flex items-center space-x-4">
        <span>Welcome, {username}</span>
        <span className="security-badge">Risk: {riskLevel}</span>
        <Button variant="secondary" onClick={onLogout}>Logout</Button>
      </div>
    </header>
  );
};
