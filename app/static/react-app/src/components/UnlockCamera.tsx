import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { useSecurity } from '@/context/SecurityContext';

interface UnlockCameraProps {
  onVerify: () => void;
  onClose: () => void;
}

export const UnlockCamera: React.FC<UnlockCameraProps> = ({ onVerify, onClose }) => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Start the camera when the component mounts
  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(mediaStream => {
        setStream(mediaStream);
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      })
      .catch(error => {
        console.error('Error accessing camera:', error);
      });

    // Clean up by stopping all tracks when the component unmounts
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Simulate face verification process
  const handleVerify = () => {
    setTimeout(() => {
      // Stop the camera stream after verification
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      onVerify();
    }, 2000);
  };

  const handleClose = () => {
    // Stop the camera stream
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    onClose();
  };

  // Adjust the styling of the UnlockCamera component
  return (
    <div className="unlock-camera-container flex flex-col items-center p-4 bg-white shadow-md rounded-lg max-w-md mx-auto">
      <video 
        ref={videoRef}
        autoPlay 
        muted
        className="w-[300px] h-[200px] rounded-md border border-border object-cover"
      />
      <div className="flex justify-between mt-4 w-full">
        <Button onClick={handleVerify} variant="default">Verify Face</Button>
        <Button onClick={handleClose} variant="secondary">Close</Button>
      </div>
    </div>
  );
};
