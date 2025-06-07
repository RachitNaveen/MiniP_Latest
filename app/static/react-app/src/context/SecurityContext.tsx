import { createContext, useContext, useState, ReactNode, useEffect } from 'react';

// Security risk levels
export type RiskLevel = 'low' | 'medium' | 'high';

// Security features
export interface SecurityFeatures {
  requireCaptcha: boolean;
  requireFaceVerification: boolean;
}

// Security context shape
interface SecurityContextType {
  riskLevel: RiskLevel;
  setRiskLevel: (level: RiskLevel) => void;
  securityFeatures: SecurityFeatures;
  updateSecurityFeatures: (features: Partial<SecurityFeatures>) => void;
}

// Default security features based on risk level
const getDefaultSecurityFeatures = (riskLevel: RiskLevel): SecurityFeatures => {
  switch (riskLevel) {
    case 'low':
      return { requireCaptcha: false, requireFaceVerification: false };
    case 'medium':
      return { requireCaptcha: true, requireFaceVerification: false };
    case 'high':
      return { requireCaptcha: true, requireFaceVerification: true };
    default:
      return { requireCaptcha: false, requireFaceVerification: false };
  }
};

// Create the context with a default value
const SecurityContext = createContext<SecurityContextType>({
  riskLevel: 'low',
  setRiskLevel: () => {},
  securityFeatures: { requireCaptcha: false, requireFaceVerification: false },
  updateSecurityFeatures: () => {},
});

// Provider component
export const SecurityProvider = ({ children }: { children: ReactNode }) => {
  const [riskLevel, setRiskLevel] = useState<RiskLevel>('low');
  const [securityFeatures, setSecurityFeatures] = useState<SecurityFeatures>(
    getDefaultSecurityFeatures('low')
  );

  // Update the risk level and security features
  const handleSetRiskLevel = (level: RiskLevel) => {
    setRiskLevel(level);
    setSecurityFeatures(getDefaultSecurityFeatures(level));

    // Send to backend
    fetch('/security/update_level', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ level }),
    })
      .then(response => response.json())
      .then(data => {
        console.log('Security level updated:', data);
      })
      .catch(error => {
        console.error('Error updating security level:', error);
      });
  };

  // Update individual security features
  const updateSecurityFeatures = (features: Partial<SecurityFeatures>) => {
    setSecurityFeatures(prev => ({ ...prev, ...features }));
  };

  // Update the SecurityContext to dynamically toggle authentication methods
  useEffect(() => {
    // Update security features based on the selected risk level
    setSecurityFeatures(getDefaultSecurityFeatures(riskLevel));
  }, [riskLevel]);

  return (
    <SecurityContext.Provider
      value={{
        riskLevel,
        setRiskLevel: handleSetRiskLevel,
        securityFeatures,
        updateSecurityFeatures,
      }}
    >
      {children}
    </SecurityContext.Provider>
  );
};

// Custom hook to use the security context
export const useSecurity = () => useContext(SecurityContext);
