import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useSecurity } from '@/context/SecurityContext';

export const RiskIndicator: React.FC = () => {
  const { riskLevel } = useSecurity();
  const [showDetails, setShowDetails] = useState(false);

  // Get the color for the risk level indicator
  const getRiskColor = () => {
    switch (riskLevel) {
      case 'low':
        return 'bg-[var(--success-color)]';
      case 'medium':
        return 'bg-[var(--warning-color)]';
      case 'high':
        return 'bg-[var(--danger-color)]';
      default:
        return 'bg-[var(--info-color)]';
    }
  };

  // Get details for each risk level
  const getRiskDetails = () => {
    switch (riskLevel) {
      case 'low':
        return [
          'Basic security measures',
          'Standard authentication',
          'No additional verification steps'
        ];
      case 'medium':
        return [
          'Enhanced security',
          'CAPTCHA verification',
          'Rate limiting on login attempts',
          'IP monitoring'
        ];
      case 'high':
        return [
          'Maximum security',
          'CAPTCHA verification',
          'Face verification required',
          'Message encryption',
          'Strict session management',
          'Comprehensive activity monitoring'
        ];
      default:
        return ['Security details unavailable'];
    }
  };

  return (
    <>
      <div 
        onClick={() => setShowDetails(true)}
        className="fixed bottom-4 right-4 bg-background p-2 rounded-lg border border-border flex items-center shadow-md cursor-pointer hover:bg-muted"
      >
        <span className={`h-3 w-3 rounded-full mr-2 ${getRiskColor()}`}></span>
        <span className="text-sm">Risk Level: {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}</span>
      </div>
      
      {showDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-background p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-lg font-bold mb-4">Security Details</h3>
            <div className="flex items-center mb-4">
              <span className={`h-4 w-4 rounded-full mr-2 ${getRiskColor()}`}></span>
              <span className="font-medium">Risk Level: {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}</span>
            </div>
            
            <div className="mb-4">
              <h4 className="font-medium mb-2">Security Measures:</h4>
              <ul className="list-disc pl-5 space-y-1">
                {getRiskDetails().map((detail, idx) => (
                  <li key={idx}>{detail}</li>
                ))}
              </ul>
            </div>
            
            <div className="flex justify-end">
              <Button onClick={() => setShowDetails(false)}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
