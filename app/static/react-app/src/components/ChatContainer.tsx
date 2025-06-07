import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { RiskIndicator } from './RiskIndicator';
import { SecurityLevelSelector } from './SecurityLevelSelector';
import { useSecurity } from '@/context/SecurityContext';
import { useAuth } from '@/context/AuthContext';
import * as api from '@/lib/api';
import { ChatHeader } from './ChatHeader';
import { ChatMessages } from './ChatMessages';
import { MessageForm } from './MessageForm';

// Message interface
interface Message {
  id: number;
  content: string;
  sender: string;
  recipient: string;
  timestamp: string;
  isLocked: boolean;
  filePath?: string;
}

// User interface
interface User {
  id: string;
  username: string;
  isOnline: boolean;
}

export const ChatContainer: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { securityFeatures } = useSecurity();
  const { logout } = useAuth();
  const currentUsername = 'You'; // This would normally come from auth context
  
  // Fetch users on component mount
  useEffect(() => {
    api.fetchUsers()
      .then(data => {
        setUsers(data.users || []);
      })
      .catch(err => console.error('Error fetching users:', err));
  }, []);
  
  // Fetch messages when a user is selected
  useEffect(() => {
    if (selectedUser) {
      api.fetchMessages(selectedUser.id)
        .then(data => {
          setMessages(data.messages || []);
          scrollToBottom();
        })
        .catch(err => console.error('Error fetching messages:', err));
    }
  }, [selectedUser]);
  
  // Scroll to bottom of message list when messages update
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  const handleUserSelect = (user: User) => {
    setSelectedUser(user);
  };
  
  // Refactor handleSendMessage to match the expected signature
  const handleSendMessage = (message: string, isLocked: boolean) => {
    if (!message.trim() || !selectedUser) return;

    api.sendMessage(message, selectedUser.id, isLocked)
      .then(data => {
        if (data.success) {
          setMessages(prev => [...prev, data.message]);
        }
      })
      .catch(err => console.error('Error sending message:', err));
  };
  
  // Update handleFileUpload to accept isLocked as a parameter
  const handleFileUpload = (file: File, isLocked: boolean) => {
    if (!selectedUser) return;

    api.uploadFile(file, selectedUser.id, isLocked)
      .then(data => {
        if (data.success && data.message) {
          setMessages(prev => [...prev, data.message]);
        }
      })
      .catch(err => console.error('Error uploading file:', err));
  };
  
  return (
    <div className="flex flex-col h-screen">
      <header className="bg-primary text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Secure Chat App</h1>
          <div className="flex items-center space-x-4">
            <SecurityLevelSelector />
            <Button variant="secondary">Logout</Button>
          </div>
        </div>
      </header>
      
      <main className="flex-1 container mx-auto p-4 flex">
        {/* User List */}
        <div className="w-1/4 bg-muted p-4 rounded-lg mr-4">
          <h2 className="font-bold mb-4">Users</h2>
          <ul>
            {users.map(user => (
              <li 
                key={user.id} 
                onClick={() => handleUserSelect(user)}
                className={`p-2 rounded cursor-pointer mb-2 ${
                  selectedUser?.id === user.id 
                    ? 'bg-primary text-white'
                    : 'hover:bg-background'
                }`}
              >
                <div className="flex items-center">
                  <div className="flex-1">{user.username}</div>
                  {user.isOnline && (
                    <div className="h-2 w-2 rounded-full bg-[var(--success-color)]"></div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
        
        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <ChatHeader username={currentUsername} onLogout={logout} />
          
          {/* Messages */}
          <div className="flex-1 bg-muted p-4 rounded-lg mb-4 overflow-y-auto">
            <ChatMessages messages={messages} currentUsername={currentUsername} />
            <div ref={messagesEndRef}></div>
          </div>
          
          {/* Message Input */}
          <MessageForm 
            onSendMessage={handleSendMessage} 
            onFileUpload={handleFileUpload} 
            securityFeatures={securityFeatures} 
            isRecipientSelected={!!selectedUser} 
          />
        </div>
      </main>
      
      <RiskIndicator />
    </div>
  );
};
