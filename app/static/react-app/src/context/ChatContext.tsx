import React, { createContext, useContext, useState, useEffect } from 'react';

// Define the types for your messages
export interface Message {
  id: number;
  content: string;
  sender: string;
  recipient: string;
  timestamp: string;
  isLocked: boolean;
  filePath?: string;
}

// Define the types for chat users
export interface User {
  id: string;
  username: string;
  isOnline: boolean;
}

// Define the chat context type
interface ChatContextType {
  messages: Message[];
  users: User[];
  selectedUser: User | null;
  fetchMessages: (userId: string) => void;
  sendMessage: (content: string, recipientId: string, isLocked: boolean) => void;
  sendFile: (file: File, recipientId: string, isLocked: boolean) => Promise<void>;
  selectUser: (user: User) => void;
}

// Create the context with default values
const ChatContext = createContext<ChatContextType>({
  messages: [],
  users: [],
  selectedUser: null,
  fetchMessages: () => {},
  sendMessage: () => {},
  sendFile: async () => {},
  selectUser: () => {},
});

// Provider component
export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Fetch users on component mount
  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(data => {
        setUsers(data.users || []);
      })
      .catch(err => console.error('Error fetching users:', err));
  }, []);

  // Fetch messages for a selected user
  const fetchMessages = (userId: string) => {
    fetch(`/api/messages/${userId}`)
      .then(res => res.json())
      .then(data => {
        setMessages(data.messages || []);
      })
      .catch(err => console.error('Error fetching messages:', err));
  };

  // Send a message
  const sendMessage = (content: string, recipientId: string, isLocked: boolean) => {
    fetch('/api/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content,
        recipient_id: recipientId,
        face_locked: isLocked,
      }),
    })
      .then(res => res.json())
      .then(data => {
        // Add the new message to the list
        if (data.success) {
          setMessages(prev => [...prev, data.message]);
        }
      })
      .catch(err => console.error('Error sending message:', err));
  };

  // Send a file
  const sendFile = async (file: File, recipientId: string, isLocked: boolean) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('recipient_id', recipientId);
    formData.append('face_locked', isLocked.toString());

    try {
      const response = await fetch('/upload_file', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Add the file message to the chat
        if (data.message) {
          setMessages(prev => [...prev, data.message]);
        }
        return data;
      } else {
        throw new Error(data.message || 'Failed to upload file');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  };

  // Select a user to chat with
  const selectUser = (user: User) => {
    setSelectedUser(user);
    fetchMessages(user.id);
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        users,
        selectedUser,
        fetchMessages,
        sendMessage,
        sendFile,
        selectUser,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

// Custom hook to use the chat context
export const useChat = () => useContext(ChatContext);
