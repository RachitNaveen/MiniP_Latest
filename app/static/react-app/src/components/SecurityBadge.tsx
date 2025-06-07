import React from 'react';
import { useSecurity, RiskLevel } from '@/context/SecurityContext';
import { Button } from './ui/button';

interface SecurityBadgeProps {
  level?: RiskLevel;
}

export const SecurityBadge: React.FC<SecurityBadgeProps> = ({ level }) => {
  const { riskLevel: contextRiskLevel } = useSecurity();
  const riskLevel = level || contextRiskLevel;
  
  const getBadgeColor = () => {
    switch (riskLevel) {
      case 'low':
        return {
          bg: 'bg-green-100',
          text: 'text-green-800',
          border: 'border-green-200'
        };
      case 'medium':
        return {
          bg: 'bg-yellow-100',
          text: 'text-yellow-800',
          border: 'border-yellow-200'
        };
      case 'high':
        return {
          bg: 'bg-red-100',
          text: 'text-red-800',
          border: 'border-red-200'
        };
      default:
        return {
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200'
        };
    }
  };
  
  const { bg, text, border } = getBadgeColor();
  
  return (
    <div className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${bg} ${text} ${border} border`}>
      Security: {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}
    </div>
  );
};
