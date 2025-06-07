import React from 'react';
import { Button } from './ui/button';
import { useSecurity, RiskLevel } from '@/context/SecurityContext';

interface SecurityLevelSelectorProps {
  onChange?: (level: RiskLevel) => void;
}

export const SecurityLevelSelector: React.FC<SecurityLevelSelectorProps> = ({ onChange }) => {
  const { riskLevel, setRiskLevel } = useSecurity();

  const handleClick = (newLevel: RiskLevel) => {
    setRiskLevel(newLevel);
    if (onChange) onChange(newLevel);
  };

  return (
    <div className="flex flex-col">
      <span className="text-sm font-medium mb-1 text-white">Security Level</span>
      <div className="flex space-x-2">
        <Button
          onClick={() => handleClick('low')}
          variant={riskLevel === 'low' ? 'default' : 'outline'}
          className={`${riskLevel === 'low' ? 'bg-[var(--success-color)]' : 'bg-white text-[var(--dark-text)]'}`}
          size="sm"
        >
          Low
        </Button>
        <Button
          onClick={() => handleClick('medium')}
          variant={riskLevel === 'medium' ? 'default' : 'outline'}
          className={`${riskLevel === 'medium' ? 'bg-[var(--warning-color)]' : 'bg-white text-[var(--dark-text)]'}`}
          size="sm"
        >
          Medium
        </Button>
        <Button
          onClick={() => handleClick('high')}
          variant={riskLevel === 'high' ? 'default' : 'outline'}
          className={`${riskLevel === 'high' ? 'bg-[var(--danger-color)]' : 'bg-white text-[var(--dark-text)]'}`}
          size="sm"
        >
          High
        </Button>
      </div>
    </div>
)};
