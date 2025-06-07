import React from 'react';
import { ChatContainer } from './components/ChatContainer';
import { ChatProvider } from './context/ChatContext';
import { AuthProvider } from './context/AuthContext';

const App: React.FC = () => {
  return (
    <AuthProvider>
      <ChatProvider>
        <ChatContainer />
      </ChatProvider>
    </AuthProvider>
  );
};

export default App;