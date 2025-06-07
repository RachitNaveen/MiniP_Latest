import * as React from "react";
import { useEffect, useState } from "react";

interface RiskInformationProps {
  riskLevel: string;
}

// Component to display risk-related information based on AI analysis
export const RiskInformation: React.FC<RiskInformationProps> = ({ riskLevel }) => {
  const [securityTips, setSecurityTips] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch security tips from API based on risk level
    setIsLoading(true);
    fetch(`/security/get_tips?level=${riskLevel}`)
      .then(response => response.json())
      .then(data => {
        setSecurityTips(data.tips || []);
        setIsLoading(false);
      })
      .catch(error => {
        console.error("Error fetching security tips:", error);
        setSecurityTips([
          "Use strong passwords with a mix of letters, numbers, and symbols",
          "Enable two-factor authentication where available",
          "Be cautious of suspicious links and attachments",
        ]);
        setIsLoading(false);
      });
  }, [riskLevel]);

  return (
    <div className="bg-muted p-4 rounded-lg">
      <h3 className="font-bold mb-2">Security Intelligence</h3>
      {isLoading ? (
        <p className="text-sm">Loading security recommendations...</p>
      ) : (
        <>
          <p className="text-sm mb-2">
            Based on AI analysis, your current risk level is{" "}
            <span className={`font-bold ${
              riskLevel === 'low' ? 'text-[var(--success-color)]' : 
              riskLevel === 'medium' ? 'text-[var(--warning-color)]' : 
              'text-[var(--danger-color)]'
            }`}>
              {riskLevel.toUpperCase()}
            </span>
          </p>
          
          <div className="mt-3">
            <h4 className="text-sm font-semibold">Recommended security actions:</h4>
            <ul className="text-sm list-disc list-inside space-y-1 mt-1">
              {securityTips.map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
};
