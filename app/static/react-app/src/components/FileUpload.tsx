import React, { useState } from 'react';
import { Button } from './ui/button';

interface FileUploadProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUpload, disabled = false }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile);
      setSelectedFile(null);
      // Reset input
      const fileInput = document.getElementById('fileInput') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <input
        type="file"
        id="fileInput"
        onChange={handleFileChange}
        className="hidden"
      />
      <Button
        variant="outline"
        onClick={() => document.getElementById('fileInput')?.click()}
        disabled={disabled}
      >
        Attach File
      </Button>
      {selectedFile && (
        <>
          <span className="text-sm truncate max-w-[120px]">{selectedFile.name}</span>
          <Button onClick={handleUpload} disabled={disabled}>
            Send File
          </Button>
        </>
      )}
    </div>
  );
};
