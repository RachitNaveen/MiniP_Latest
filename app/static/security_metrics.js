// Security metrics functionality for SecureChat
document.addEventListener('DOMContentLoaded', function() {
    console.log("Loading security metrics functionality");
    
    // Security metrics elements
    const securityRisk = document.getElementById('securityRisk');
    const faceAccuracy = document.getElementById('faceAccuracy');
    const securityDetailsBtn = document.getElementById('securityDetailsBtn');
    const securityDetailsModal = document.getElementById('securityDetailsModal');
    const closeSecurityDetails = document.getElementById('closeSecurityDetails');
    const riskLevelIndicator = document.getElementById('riskLevelIndicator');
    const riskIndicatorDot = document.getElementById('riskIndicatorDot');
    const riskIndicatorText = document.getElementById('riskIndicatorText');
    
    // Security details elements
    const overallRiskLevel = document.getElementById('overallRiskLevel');
    const riskScore = document.getElementById('riskScore');
    const riskFactors = document.getElementById('riskFactors');
    const faceAccuracyValue = document.getElementById('faceAccuracyValue');
    const totalFaceAttempts = document.getElementById('totalFaceAttempts');
    const faceSuccessRate = document.getElementById('faceSuccessRate');
    const faceConfidence = document.getElementById('faceConfidence');
    
    // Log the presence of security elements
    console.log("Security elements found:", {
        securityRisk: !!securityRisk,
        faceAccuracy: !!faceAccuracy,
        securityDetailsBtn: !!securityDetailsBtn, 
        securityDetailsModal: !!securityDetailsModal,
        riskLevelIndicator: !!riskLevelIndicator,
        riskIndicatorDot: !!riskIndicatorDot,
        riskIndicatorText: !!riskIndicatorText
    });
    
    // Open security details modal
    if (securityDetailsBtn) {
        securityDetailsBtn.addEventListener('click', function() {
            if (securityDetailsModal) {
                console.log("Opening security details modal");
                securityDetailsModal.style.display = 'flex';
            }
        });
    }
    
    // Close security details modal
    if (closeSecurityDetails) {
        closeSecurityDetails.addEventListener('click', function() {
            if (securityDetailsModal) {
                securityDetailsModal.style.display = 'none';
            }
        });
    }
    
    // Close modal when clicking outside
    if (securityDetailsModal) {
        securityDetailsModal.addEventListener('click', function(e) {
            if (e.target === securityDetailsModal) {
                securityDetailsModal.style.display = 'none';
            }
        });
    }
    
    // Fetch security metrics
    function fetchSecurityMetrics() {
        // Get CSRF token
        const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : null;
        
        if (!csrfToken) {
            console.error("CSRF token not found.");
            return;
        }
        
        console.log("Fetching security metrics from: /security/get_security_metrics");
        fetch('/security/get_security_metrics', {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin' // Add credentials to ensure cookies are sent
        })
        .then(response => {
            console.log("Security metrics response status:", response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Security metrics data received:", data);
            if (data.success) {
                updateSecurityDisplay(data);
            } else {
                console.error("Failed to get security metrics:", data.message);
            }
        })
        .catch(error => {
            console.error("Error fetching security metrics:", error);
        });
    }
    
    // Update security display
    function updateSecurityDisplay(data) {
        const risk = data.risk;
        const faceVerification = data.face_verification;
        
        // Update risk badge
        if (securityRisk) {
            let riskLevel = '';
            let riskClass = '';
            
            if (risk.score < 30) {
                riskLevel = 'Low';
                riskClass = 'risk-low';
            } else if (risk.score < 70) {
                riskLevel = 'Medium';
                riskClass = 'risk-medium';
            } else {
                riskLevel = 'High';
                riskClass = 'risk-high';
            }
            
            securityRisk.textContent = `Risk: ${riskLevel} (${risk.score}%)`;
            securityRisk.className = 'security-badge ' + riskClass;
        }
        
        // Update face accuracy badge
        if (faceAccuracy) {
            let accuracyClass = '';
            
            if (faceVerification.accuracy >= 90) {
                accuracyClass = 'accuracy-high';
            } else if (faceVerification.accuracy >= 70) {
                accuracyClass = 'accuracy-medium';
            } else {
                accuracyClass = 'accuracy-low';
            }
            
            if (faceVerification.total_attempts > 0) {
                faceAccuracy.textContent = `Face AI: ${faceVerification.accuracy}% accurate`;
            } else {
                faceAccuracy.textContent = 'Face AI: No data';
            }
            
            faceAccuracy.className = 'security-badge ' + accuracyClass;
        }
        
        // Update risk level indicator at bottom right
        updateRiskLevelIndicator(risk);
        
        // Update detailed information
        if (overallRiskLevel) overallRiskLevel.textContent = risk.level;
        if (riskScore) riskScore.textContent = `${risk.score}%`;
        
        // Update risk factors
        if (riskFactors) {
            riskFactors.innerHTML = '';
            
            for (const [key, factor] of Object.entries(risk.factors)) {
                if (key === 'error') continue;
                
                const factorElement = document.createElement('div');
                factorElement.className = 'security-factor';
                
                let scoreClass = '';
                if (factor.score < 0.3) {
                    scoreClass = 'score-low';
                } else if (factor.score < 0.7) {
                    scoreClass = 'score-medium';
                } else {
                    scoreClass = 'score-high';
                }
                
                factorElement.innerHTML = `
                    <div class="security-factor-header">
                        <strong>${formatFactorName(key)}</strong>
                        <span class="security-factor-score ${scoreClass}">
                            ${Math.round(factor.score * 100)}%
                        </span>
                    </div>
                    <div class="security-factor-description">
                        ${factor.description}
                    </div>
                `;
                
                riskFactors.appendChild(factorElement);
            }
        }
        
        // Update face verification details
        if (faceAccuracyValue) faceAccuracyValue.textContent = `${faceVerification.accuracy}%`;
        if (totalFaceAttempts) totalFaceAttempts.textContent = faceVerification.total_attempts;
        if (faceSuccessRate) {
            faceSuccessRate.textContent = `${faceVerification.successful_attempts} / ${faceVerification.total_attempts}`;
        }
        if (faceConfidence) faceConfidence.textContent = faceVerification.confidence;
    }
    
    // Format factor name for display
    function formatFactorName(key) {
        return key
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    // Risk level indicator update
    function updateRiskLevelIndicator(riskData) {
        const riskIndicatorDot = document.getElementById('riskIndicatorDot');
        const riskIndicatorText = document.getElementById('riskIndicatorText');
        
        if (!riskIndicatorDot || !riskIndicatorText) return;
        
        console.log("Updating risk level indicator with data:", riskData);
        
        // Determine risk level
        let riskLevel = '';
        let riskClass = '';
        
        if (riskData.score < 30) {
            riskLevel = 'Low';
            riskClass = 'low';
        } else if (riskData.score < 70) {
            riskLevel = 'Medium';
            riskClass = 'medium';
        } else {
            riskLevel = 'High';
            riskClass = 'high';
        }
        
        // Update text and color
        riskIndicatorText.textContent = `Risk Level by AI: ${riskLevel}`;
        riskIndicatorDot.className = 'risk-indicator-dot ' + riskClass;
    }
    
    // Initial fetch
    if (securityRisk || faceAccuracy || riskLevelIndicator) {
        console.log("Initializing security metrics fetch");
        fetchSecurityMetrics();
        
        // Refresh metrics every 60 seconds
        setInterval(fetchSecurityMetrics, 60000);
    } else {
        console.warn("No security UI elements found - skipping security metrics fetching");
    }
});
