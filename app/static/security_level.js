/**
 * Security Level Management
 * 
 * Handles the risk level selection UI and logging
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configuration for security levels
    const securityLevels = {
        'low': {
            title: 'LOW Security Level',
            description: 'Basic security with minimal verification steps.',
            factors: 'Password only',
            color: '#E8F5E9',
            borderColor: '#4CAF50'
        },
        'medium': {
            title: 'MEDIUM Security Level',
            description: 'Standard security with additional verification.',
            factors: 'Password + CAPTCHA',
            color: '#FFF8E1',
            borderColor: '#FFC107'
        },
        'high': {
            title: 'HIGH Security Level',
            description: 'Maximum security with multiple verification steps.',
            factors: 'Password + CAPTCHA + Face Verification',
            color: '#FFEBEE',
            borderColor: '#F44336'
        },
        'ai': {
            title: 'AI-Based Risk Assessment',
            description: 'Dynamic security level based on AI risk analysis.',
            factors: 'Determined by risk assessment',
            color: '#E8EAF6',
            borderColor: '#3F51B5'
        }
    };
    
    /**
     * Display security assessment details in the risk panel
     */
    window.displaySecurityAssessment = function(riskDetails) {
        // If no risk details provided, exit the function
        if (!riskDetails) {
            console.log("No risk details provided to displaySecurityAssessment");
            return;
        }
        
        console.log("Displaying security assessment with details:", riskDetails);
        
        try {
            // Show the risk panel
            const riskPanel = document.getElementById('risk-panel');
            if (!riskPanel) {
                console.log("Risk panel element not found");
                return;
            }
            riskPanel.style.display = 'block';
            
            // Display risk score and level
            const riskScore = document.getElementById('risk-score');
            if (riskScore && typeof riskDetails.risk_score === 'number') {
                const scoreValue = riskDetails.risk_score.toFixed(2);
                const levelName = riskDetails.security_level || 'Medium';
                riskScore.innerHTML = `Risk Score: <strong>${scoreValue}</strong> <span class="risk-level ${levelName.toLowerCase()}">${levelName} Security</span>`;
            } else {
                console.log("Risk score element not found or risk_score not a number:", 
                            riskScore, typeof riskDetails.risk_score);
            }
            
            // Display risk factors
            const riskFactors = document.getElementById('risk-factors');
            if (riskFactors && riskDetails.risk_factors) {
                riskFactors.innerHTML = '<h4>Risk Factor Details:</h4>';
                
                for (const [factorName, factorData] of Object.entries(riskDetails.risk_factors)) {
                    if (!factorData) continue;
                    
                    const displayName = factorName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    const factorElement = document.createElement('div');
                    factorElement.className = 'risk-factor';
                    
                    const score = typeof factorData.score === 'number' ? factorData.score.toFixed(2) : 'N/A';
                    const description = factorData.description || 'No description available';
                    
                    factorElement.innerHTML = `
                        <span class="risk-factor-name">${displayName}:</span> 
                        <span class="risk-factor-value">${score}</span>
                        <div>${description}</div>
                    `;
                    riskFactors.appendChild(factorElement);
                }
            } else {
                console.log("Risk factors element not found or risk_factors missing:", 
                            riskFactors, riskDetails.risk_factors);
            }
            
            // Display required factors
            const requiredFactors = document.getElementById('required-factors');
            if (requiredFactors && Array.isArray(riskDetails.required_factors)) {
                requiredFactors.innerHTML = '<strong>Required Authentication Factors:</strong><br>';
                
                for (const factor of riskDetails.required_factors) {
                    const factorSpan = document.createElement('span');
                    factorSpan.className = 'required-factor';
                    factorSpan.textContent = factor;
                    requiredFactors.appendChild(factorSpan);
                }
            } else {
                console.log("Required factors element not found or required_factors not an array:", 
                            requiredFactors, riskDetails.required_factors);
            }
            console.log('[SECURITY] Displayed security assessment details');
        } catch (error) {
            console.error('Error displaying security assessment:', error);
        }
    };
    
    // Get DOM elements for login page selector
    const securityLevelSelect = document.getElementById('security-level');
    const setLevelBtn = document.getElementById('set-level-btn');
    const securityInfo = document.getElementById('security-info');
    
    // Handle the login page security level selector
    if (securityLevelSelect && setLevelBtn) {
        console.log('[SECURITY] Login page security level selector found');
        
        // Set up event listener for the Apply Level button
        setLevelBtn.addEventListener('click', function() {
            const selectedLevel = securityLevelSelect.value;
            console.log(`[SECURITY] Setting security level to: ${selectedLevel.toUpperCase()}`);
            
            // Send the security level to the server
            fetch('/set_security_level_login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({
                    level: selectedLevel
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`[SECURITY] Security level set to ${data.levelName} successfully`);
                    console.log(`[SECURITY] Response data:`, data);
                    
                    // Update the security info panel
                    if (securityInfo) {
                        // Create HTML for the security info
                        let infoHTML = `
                            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                                <span style="font-weight: bold; margin-right: 8px;">Current Mode:</span>
                                <strong>${data.levelName}</strong>
                        `;
                        
                        // Add AI indicator if in AI mode
                        if (selectedLevel === 'ai') {
                            infoHTML += `
                                <span class="ai-indicator" style="display: inline-block; margin-left: 10px; font-size: 0.8em; padding: 2px 8px; background-color: #3F51B5; color: white; border-radius: 10px; animation: pulse 2s infinite;">AI ACTIVE</span>
                            `;
                        }
                        
                        infoHTML += `
                            </div>
                            <p style="margin: 5px 0 0 0;">Required factors: <strong>${data.requiredFactors}</strong></p>
                        `;
                        
                        securityInfo.innerHTML = infoHTML;
                    }
                    
                    // If there are risk details in the response, display them
                    if (data.riskDetails) {
                        console.log('[SECURITY] Risk details received:', data.riskDetails);
                        displaySecurityAssessment(data.riskDetails);
                    }
                } else {
                    console.error('[SECURITY] Error setting security level:', data.message);
                }
            })
            .catch(error => {
                console.error('Error setting security level:', error);
            });
        });
    } else {
        console.log('[SECURITY] Login page security level selector not found');
    }
    
    // When the DOM loads, check for risk details in the data attribute and display them
    try {
        // Get the risk data element
        const riskDataElement = document.getElementById('risk-data');
        if (!riskDataElement) {
            console.log('[SECURITY] Risk data element not found');
            return;
        }
        
        // Check if risk details exist
        const hasRiskDetails = riskDataElement.getAttribute('data-has-risk-details') === 'true';
        
        if (hasRiskDetails) {
            console.log('[SECURITY] Risk details found in data attribute');
            
            // Parse the risk details from the data attribute
            const riskDetailsJson = riskDataElement.getAttribute('data-risk-details');
            console.log('[SECURITY] Raw risk details JSON:', riskDetailsJson);
            
            if (riskDetailsJson) {
                try {
                    const riskDetails = JSON.parse(riskDetailsJson);
                    console.log('[SECURITY] Parsed risk details:', riskDetails);
                    displaySecurityAssessment(riskDetails);
                } catch (error) {
                    console.error('[SECURITY] Error parsing risk details JSON:', error);
                }
            }
        } else {
            console.log('[SECURITY] No risk details found in data attribute');
        }
    } catch (error) {
        console.error('[SECURITY] Error handling risk details:', error);
    }
});
