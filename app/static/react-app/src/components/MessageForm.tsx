import React, { useState } from 'react';
import { Button } from './ui/button';
import { FileUpload } from './FileUpload';

interface MessageFormProps {
  onSendMessage: (message: string, isLocked: boolean) => void;
  onFileUpload: (file: File, isLocked: boolean) => void;
  securityFeatures: { requireFaceVerification: boolean, requireCaptcha: boolean };
  isRecipientSelected: boolean;
}

export const MessageForm: React.FC<MessageFormProps> = ({
  onSendMessage,
  onFileUpload,
  securityFeatures,
  isRecipientSelected
}) => {
  const [messageText, setMessageText] = useState('');
  const [isLocked, setIsLocked] = useState(false);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (messageText.trim()) {
      onSendMessage(messageText, isLocked);
      setMessageText('');
    }
  };

  const handleFileUpload = (file: File) => {
    onFileUpload(file, isLocked);
  };

  // Dynamically include CAPTCHA and other elements based on securityFeatures
  return (
    <form onSubmit={handleSendMessage} className="flex flex-col space-y-4">
      <div className="flex space-x-2">
        <input
          type="text"
          value={messageText}
          onChange={e => setMessageText(e.target.value)}
          className="flex-1 p-2 border border-border rounded-md"
          placeholder={isRecipientSelected ? "Type a message..." : "Select a recipient..."}
          disabled={!isRecipientSelected}
        />
        <Button type="submit" disabled={!isRecipientSelected || !messageText.trim()}>
          Send
        </Button>
      </div>

      {securityFeatures.requireCaptcha && (
        <div className="captcha-container">
          <p className="text-sm text-light-text">Please complete the CAPTCHA to proceed.</p>
          {/* Placeholder for CAPTCHA implementation */}
          <div className="captcha-box border border-border rounded-md p-2">CAPTCHA</div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="lockMessage"
            checked={isLocked}
            onChange={() => setIsLocked(!isLocked)}
            className="mr-2"
            disabled={!securityFeatures.requireFaceVerification}
          />
          <label 
            htmlFor="lockMessage"
            className={!securityFeatures.requireFaceVerification ? "text-light-text" : ""}
          >
            Lock with Face Verification
            {!securityFeatures.requireFaceVerification && (
              <span className="ml-2 text-xs text-light-text">
                (Requires High security level)
              </span>
            )}
          </label>
        </div>

        <FileUpload 
          onUpload={handleFileUpload}
          disabled={!isRecipientSelected}
        />
      </div>
    </form>
  );
};
