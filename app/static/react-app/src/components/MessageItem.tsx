import React, { useState } from 'react';
import { Button } from './ui/button';
import { UnlockCamera } from './UnlockCamera';
import { useSecurity } from '@/context/SecurityContext';

interface Message {
  id: number;
  content: string;
  sender: string;
  recipient: string;
  timestamp: string;
  isLocked: boolean;
  filePath?: string;
}

interface MessageItemProps {
  message: Message;
  isCurrentUser: boolean;
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

export const MessageItem: React.FC<MessageItemProps> = ({ message, isCurrentUser }) => {
  const [isUnlocked, setIsUnlocked] = useState(!message.isLocked);
  const [showCamera, setShowCamera] = useState(false);
  const { securityFeatures } = useSecurity();

  const handleUnlockClick = () => {
    if (securityFeatures.requireFaceVerification) {
      setShowCamera(true);
    } else {
      // If face verification is not required based on security level
      setIsUnlocked(true);
    }
  };

  const handleVerificationSuccess = () => {
    setShowCamera(false);
    setIsUnlocked(true);
  };

  const renderFileAttachment = (filePath?: string) => {
    if (!filePath) return null;

    const fileName = filePath.split('/').pop() || 'attachment';
    const fileExtension = fileName.split('.').pop()?.toLowerCase() || '';
    
    // Check if it's an image
    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExtension);
    
    return (
      <div className="mt-2 p-2 bg-background rounded border border-border">
        {isImage && isUnlocked ? (
          <img 
            src={filePath} 
            alt={fileName} 
            className="max-h-40 rounded"
            onClick={() => window.open(filePath, '_blank')}
          />
        ) : (
          <div className="flex items-center">
            <span className="mr-2">📎</span>
            <a 
              href={isUnlocked ? filePath : '#'} 
              className={`text-primary hover:underline ${!isUnlocked && 'pointer-events-none text-gray-400'}`}
              target="_blank"
              rel="noreferrer"
            >
              {fileName}
            </a>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <div 
        className={`mb-4 p-3 rounded-lg max-w-[75%] ${
          isCurrentUser 
            ? 'bg-primary text-white ml-auto' 
            : 'bg-muted text-foreground'
        }`}
      >
        <div className="flex justify-between items-center mb-1">
          <span className="font-bold">{message.sender}</span>
          <span className="text-xs opacity-70">{formatTime(message.timestamp)}</span>
        </div>
        
        {isUnlocked ? (
          <>
            <div className="mt-1">{message.content}</div>
            {renderFileAttachment(message.filePath)}
          </>
        ) : (
          <div className="flex flex-col">
            <div className="flex items-center">
              <span className="mr-2">🔒 This message is locked</span>
              <Button size="sm" variant="secondary" onClick={handleUnlockClick}>
                Unlock
              </Button>
            </div>
          </div>
        )}
      </div>

      {showCamera && (
        <UnlockCamera 
          onVerify={handleVerificationSuccess} 
          onClose={() => setShowCamera(false)} 
        />
      )}
    </>
  );
};
