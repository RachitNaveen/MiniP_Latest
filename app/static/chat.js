//chat.js 
// Declare variables only once at the top of the script
let securityRisk, faceAccuracy, securityDetailsBtn, securityDetailsModal, closeSecurityDetails;

document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM fully loaded - initializing chat.js");
    
    // Initialize variables
    securityRisk = document.getElementById('securityRisk');
    faceAccuracy = document.getElementById('faceAccuracy');
    securityDetailsBtn = document.getElementById('securityDetailsBtn');
    securityDetailsModal = document.getElementById('securityDetailsModal');
    closeSecurityDetails = document.getElementById('closeSecurityDetails');

    // Log the presence of security elements
    console.log("Security elements found:", {
        securityRisk: !!securityRisk,
        faceAccuracy: !!faceAccuracy,
        securityDetailsBtn: !!securityDetailsBtn, 
        securityDetailsModal: !!securityDetailsModal
    });

    // Chat elements
    const messageContainer = document.getElementById('messageContainer');
    const messageForm = document.getElementById('messageForm');
    const recipientInput = document.querySelector('.message-select');
    const messageInput = document.querySelector('.message-input');
    const fileInput = document.getElementById('fileInput');
    const sendFileButton = document.getElementById('sendFileButton');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const faceLockedCheckbox = document.getElementById('faceLocked'); // Get the checkbox
    const currentUserId = document.body.dataset.userId;
    
    let socket;

    try {
        socket = io({
            reconnection: true,
            reconnectionAttempts: Infinity,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            randomizationFactor: 0.5
        });

        socket.on('connect', function () {
            console.log('Connected to server with SID:', socket.id);
        });

        socket.on('disconnect', function (reason) {
            console.log('Disconnected from server. Reason:', reason);
            if (reason === 'io server disconnect') {
                console.log('Server disconnected the socket. Won\'t automatically reconnect.');
            }
        });

        socket.on('connect_error', (error) => {
            console.error('Connection Error:', error);
        });

        socket.on('user_list', function (users) {
            console.log('Received user_list:', users);
            if (recipientInput) {
                const currentRecipient = recipientInput.value;
                recipientInput.innerHTML = '<option value="" disabled selected>Select recipient</option>';
                users.forEach(user => {
                    if (String(user.id) !== String(currentUserId)) {
                        const option = document.createElement('option');
                        option.value = user.id;
                        option.textContent = user.username;
                        if (String(user.id) === currentRecipient) {
                            option.selected = true;
                        }
                        recipientInput.appendChild(option);
                    }
                });
                console.log('Recipient dropdown updated');
            } else {
                console.error("Recipient select element not found.");
            }
        });

        socket.on('new_message', function (data) {
            console.log("[DEBUG] Received new_message event with data:", data);
            const isCurrentUserSender = String(data.sender_id) === String(currentUserId);
            if (isCurrentUserSender || String(data.recipient_id) === String(currentUserId)) {
                console.log("[DEBUG] Processing new_message event:", data);
                // --- MODIFICATION: Check for is_face_locked ---
                if (data.is_face_locked && !isCurrentUserSender) { // Only show locked for recipient
                    // Ensure we have an ID for the message
                    if (!data.id && !data.message_id) {
                        data.id = 'msg_' + Date.now();
                    }
                    console.log("[DEBUG] Adding locked message from socket event:", data);
                    addLockedItemToUI('message', data.sender_username, data); // Pass full data for potential future use
                } else {
                    addMessageToUI(data.content, data.sender_username, isCurrentUserSender, data.is_face_locked);
                }
            }
        });

        socket.on('new_file', function (data) {
            console.log("[DEBUG] Received new_file event with data:", data);
            const isCurrentUserSender = String(data.sender_id) === String(currentUserId);
            if (isCurrentUserSender || String(data.recipient_id) === String(currentUserId)) {
                // --- MODIFICATION: Check for is_face_locked ---
                if (data.is_face_locked && !isCurrentUserSender) { // Only show locked for recipient
                    addLockedItemToUI('file', data.sender_username, data);
                } else {
                    addFileToUI(data.file_url, data.file_name, data.sender_username, isCurrentUserSender, data.is_face_locked);
                }
            }
        });

        socket.on('user_status_update', function (data) {
            console.log("[DEBUG] Received user_status_update:", data);
            const localCurrentUserId = document.body.dataset.userId;
            if (data.type === 'face_unlocked' || data.type === 'user_logged_out') {
                if (String(data.userId) !== String(localCurrentUserId) || data.type === 'user_logged_out') {
                    if (data.type === 'face_unlocked' && String(data.userId) === String(localCurrentUserId)) return;
                    addNotificationToUI(data.message);
                }
            }
        });

        socket.on('unlock_attempt_update', function (data) {
            console.log("[DEBUG] Received unlock_attempt_update event with data:", data);
            const messageElement = document.querySelector(`[data-message-id='${data.message_id}']`);
            if (messageElement) {
                if (data.is_replaced) {
                    messageElement.textContent = "MESSAGE DELETED...";
                } else {
                    messageElement.textContent = `Unlock attempts: ${data.attempts}`;
                }
            }
        });

        // --- NEW: Add this listener for intruder alerts ---
        socket.on('intruder_alert', function (data) {
            console.log("[INTRUDER-ALERT] Received intruder alert:", data);
            addIntruderAlertToUI(data);
        });

        if (messageForm) {
            messageForm.addEventListener('submit', function (e) {
                e.preventDefault();
                const content = messageInput.value.trim();
                const recipientId = recipientInput.value;
                // --- MODIFICATION: Get face_locked status ---
                const isFaceLocked = faceLockedCheckbox ? faceLockedCheckbox.checked : false;

                if (!recipientId) {
                    showCustomAlert('Please select a recipient.');
                    return;
                }
                if (!content) {
                    showCustomAlert('Please enter a message.');
                    return;
                }
                console.log("[DEBUG] Emitting send_message event with:", { content, recipient_id: recipientId, face_locked: isFaceLocked });
                socket.emit('send_message', {
                    content: content,
                    recipient_id: recipientId,
                    face_locked: isFaceLocked // --- MODIFICATION: Send status ---
                });
                messageInput.value = '';
            });
        } else {
            console.error("Message form not found.");
        }

        if (fileInput && fileNameDisplay) {
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) {
                    fileNameDisplay.textContent = fileInput.files[0].name;
                } else {
                    fileNameDisplay.textContent = '';
                }
            });
        }

        if (sendFileButton) {
            sendFileButton.addEventListener('click', function () {
                const file = fileInput.files[0];
                const recipientId = recipientInput.value;
                // --- MODIFICATION: Get face_locked status ---
                const isFaceLocked = faceLockedCheckbox ? faceLockedCheckbox.checked : false;

                if (!recipientId) {
                    showCustomAlert('Please select a recipient for the file.');
                    return;
                }
                if (!file) {
                    showCustomAlert('Please select a file to send.');
                    return;
                }
                sendFileButton.disabled = true;
                const formData = new FormData();
                formData.append('file', file);
                formData.append('recipient_id', recipientId);
                // --- MODIFICATION: Send face_locked status with FormData for the HTTP request if needed by /upload_file ---
                // Note: For SocketIO, we'll pass it after successful upload.
                // If /upload_file endpoint itself needs to know, you'd add it here:
                // formData.append('face_locked', isFaceLocked);


                const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
                const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : null;
                if (!csrfToken) {
                    console.error("CSRF token not found.");
                    showCustomAlert("Error: Missing security token. Please refresh.");
                    sendFileButton.disabled = false;
                    return;
                }

                fetch('/upload_file', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errData => {
                            throw new Error(errData.message || `Server error: ${response.status}`);
                        }).catch(() => { throw new Error(`Server error: ${response.status}`); });
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("[DEBUG] File upload response:", data);
                    if (data.success && data.file_url && data.file_name) {
                        // --- MODIFICATION: Emit new_file with face_locked status ---
                        // The server's /upload_file should return file_url and file_name
                        // Then the client emits this info via SocketIO
                        socket.emit('new_file', {
                            file_url: data.file_url,
                            file_name: data.file_name,
                            recipient_id: recipientId,
                            face_locked: isFaceLocked // Send status here
                        });
                        console.log("File uploaded, server will emit event via SocketIO.");
                    } else {
                        showCustomAlert('Failed to process file: ' + (data.message || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error("[ERROR] Error uploading file:", error);
                    showCustomAlert('Error uploading file: ' + error.message);
                })
                .finally(() => {
                    sendFileButton.disabled = false;
                    fileInput.value = '';
                    if (fileNameDisplay) fileNameDisplay.textContent = '';
                });
            });
        } else {
            console.error("Send file button not found.");
        }

        function addMessageToUI(content, senderUsername, isCurrentUserSender, isLockedForSender = false) {
            // For face-locked messages that need to be unlocked
            if (isLockedForSender && !isCurrentUserSender) {
                // Ensure we have a proper ID structure, content could be string or object
                const messageId = typeof content === 'object' && content.id ? content.id : 
                                 typeof content === 'object' && content._id ? content._id : 'msg_' + Date.now();
                
                console.log("[DEBUG] Adding locked message UI with ID:", messageId);
                addLockedItemToUI('message', senderUsername, { id: messageId, type: 'message' });
                return;
            }
            if (!messageContainer) return;
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isCurrentUserSender ? 'sent' : 'received'}`;
            
            const userDiv = document.createElement('div');
            userDiv.className = 'message-user';
            userDiv.textContent = isCurrentUserSender ? 'You' : senderUsername;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            // --- MODIFICATION: If sender sent a locked message, show them a visual cue ---
            if (isCurrentUserSender && isLockedForSender) {
                contentDiv.innerHTML = `<em>(Sent as Face Locked)</em><br>${content}`; // Or just content with a lock icon
            } else {
                contentDiv.textContent = content;
            }

            messageDiv.appendChild(userDiv);
            messageDiv.appendChild(contentDiv);
            messageContainer.appendChild(messageDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }

        function addFileToUI(fileUrl, fileName, senderUsername, isCurrentUserSender, isLockedForSender = false) {
            if (!messageContainer) return;
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isCurrentUserSender ? 'sent' : 'received'}`;

            const userDiv = document.createElement('div');
            userDiv.className = 'message-user';
            userDiv.textContent = isCurrentUserSender ? 'You' : senderUsername;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            const link = document.createElement('a');
            link.href = fileUrl;
            link.textContent = fileName;
            link.target = '_blank';
            link.download = fileName;

            // --- MODIFICATION: If sender sent a locked file, show them a visual cue ---
            if (isCurrentUserSender && isLockedForSender) {
                const lockIndicator = document.createElement('em');
                lockIndicator.textContent = '(Sent as Face Locked) ';
                contentDiv.appendChild(lockIndicator);
            }
            contentDiv.appendChild(link);

            messageDiv.appendChild(userDiv);
            messageDiv.appendChild(contentDiv);
            messageContainer.appendChild(messageDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }

        // --- Function to display a locked item placeholder ---
        function addLockedItemToUI(itemType, senderUsername, itemData) {
            if (!messageContainer) return;

            // --- Create the main parent elements ---
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message received locked-item-placeholder';

            const userDiv = document.createElement('div');
            userDiv.className = 'message-user';
            userDiv.textContent = senderUsername;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content locked-content';
            
            // --- Create the content of the locked message ---
            const lockIcon = document.createElement('span');
            lockIcon.className = 'lock-icon';
            lockIcon.innerHTML = '&#x1F512; '; // Lock emoji 🔒

            const lockText = document.createElement('span');
            lockText.textContent = `This ${itemType} is Face Locked. `;

            const unlockButton = document.createElement('button');
            unlockButton.className = 'unlock-button';
            unlockButton.textContent = 'Unlock';

            // Assemble the content div
            contentDiv.appendChild(lockIcon);
            contentDiv.appendChild(lockText);
            contentDiv.appendChild(unlockButton);

            // Assemble the final message div
            messageDiv.appendChild(userDiv);
            messageDiv.appendChild(contentDiv);

            // Add to the chat container
            messageContainer.appendChild(messageDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;

            // --- Event Listener ---
            unlockButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const itemId = itemData.id || itemData.message_id || 'unknown';
                console.log(`[DEBUG] Unlocking ${itemType} with ID: ${itemId}`);
                
                // --- THIS IS THE CALLBACK FUNCTION WE ARE FIXING ---
                const handleVerificationResult = function(data) {
                    console.log(`[DEBUG] Face verification callback executed:`, data);

                    if (data.deleted) {
                        // If deleted, create a new "deleted" content element
                        const deletedNotice = document.createElement('div');
                        deletedNotice.className = 'message-content';
                        deletedNotice.textContent = data.message || "This message has been deleted.";
                        
                        // Replace the entire content div (the one with the button) with the new notice
                        contentDiv.replaceWith(deletedNotice);
                        messageDiv.classList.remove('locked-item-placeholder');

                    } else if (data.success) {
                        // If successful, create a new "unlocked" content element
                        const unlockedContent = document.createElement('div');
                        unlockedContent.className = 'message-content';

                        if (itemType === 'message') {
                            unlockedContent.textContent = data.content;
                        } else if (itemType === 'file') {
                            const link = document.createElement('a');
                            link.href = data.fileUrl;
                            link.textContent = data.fileName;
                            link.target = '_blank';
                            link.download = data.fileName;
                            unlockedContent.appendChild(link);
                        }
                        
                        // Replace the content div with the new unlocked content
                        contentDiv.replaceWith(unlockedContent);
                        messageDiv.classList.remove('locked-item-placeholder');
                    }
                };

                // Call the modal and pass our new, more reliable callback
                try {
                    showFaceVerificationModal(itemType, itemId, senderUsername, handleVerificationResult);
                } catch (err) {
                    console.error("[DEBUG] Error showing face verification modal:", err);
                    showCustomAlert("Error initializing face verification. Please try again.");
                }
            });
        }

        function addNotificationToUI(messageText) {
            if (!messageContainer) {
                console.error("messageContainer element not found for notification!");
                return;
            }
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'message system-notification';
            const textElement = document.createElement('p');
            textElement.textContent = messageText;
            notificationDiv.appendChild(textElement);
            messageContainer.appendChild(notificationDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }

        // Helper to get CSRF token from meta tag
        function getCSRFToken() {
            // Try getting the token from meta tag
            const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
            if (csrfTokenMeta) {
                return csrfTokenMeta.getAttribute('content');
            }
            
            // Try getting from cookie as fallback
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith('csrf_token=')) {
                    return cookie.substring('csrf_token='.length);
                }
            }
            
            console.warn("CSRF token not found in meta tags or cookies");
            return '';
        }

        // Simple custom alert (replace with a proper modal in a real app)
        function showCustomAlert(message) {
            console.warn("ALERT (replace with modal):", message);
            // For now, using browser alert. In a real app, use a styled modal.
            alert(message);
        }

        // Load face-api.js models
        (async () => {
            try {
                await faceapi.nets.tinyFaceDetector.loadFromUri('/static/face-api-models');
                await faceapi.nets.faceLandmark68Net.loadFromUri('/static/face-api-models');
                console.log("Face-api models loaded.");
            } catch (error) {
                console.error("Error loading face-api models:", error);
            }
        })();

    } catch (e) {
        console.error('Socket.IO initialization or connection failed:', e);
        if (messageContainer) {
            messageContainer.innerHTML = '<p style="text-align:center; color:red;">Chat service is currently unavailable. Please try refreshing the page later.</p>';
        }
    }

    // Security metrics functionality
    const overallRiskLevel = document.getElementById('overallRiskLevel');
    const riskScore = document.getElementById('riskScore');
    const riskFactors = document.getElementById('riskFactors');
    const faceAccuracyValue = document.getElementById('faceAccuracyValue');
    const totalFaceAttempts = document.getElementById('totalFaceAttempts');
    const faceSuccessRate = document.getElementById('faceSuccessRate');
    const faceConfidence = document.getElementById('faceConfidence');
    
    // Open security details modal
    if (securityDetailsBtn) {
        securityDetailsBtn.addEventListener('click', function() {
            if (securityDetailsModal) {
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
            console.log("Security metrics data received:", JSON.stringify(data, null, 2));
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
    
    // Initial fetch
    if (securityRisk || faceAccuracy) {
        fetchSecurityMetrics();
        
        // Refresh metrics every 60 seconds
        setInterval(fetchSecurityMetrics, 60000);
    }
    
    // Risk level indicator update
    function updateRiskLevelIndicator(riskData) {
        const riskIndicatorDot = document.getElementById('riskIndicatorDot');
        const riskIndicatorText = document.getElementById('riskIndicatorText');
        
        if (!riskIndicatorDot || !riskIndicatorText) return;
        
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

    // --- NEW: Add this new function at the end of the file, near your other UI functions ---
// --- It will create the UI for the alert ---

/**
 * Adds a special intruder alert notification to the chat UI.
 * @param {object} data - The alert data from the server.
 * { message: string, image_url: string, timestamp: string }
 */
function addIntruderAlertToUI(data) {
    if (!messageContainer) {
        console.error("messageContainer element not found for intruder alert!");
        return;
    }

    const alertDiv = document.createElement('div');
    alertDiv.className = 'message system-notification intruder-alert'; // Special class for styling

    // Create the main alert message
    const textElement = document.createElement('p');
    textElement.innerHTML = `&#x26A0;&#xFE0F; <strong>Security Alert</strong><br>${data.message}`; // Warning emoji ⚠️

    // Create a container for the snapshot
    const snapshotContainer = document.createElement('div');
    snapshotContainer.className = 'intruder-snapshot-container';

    const snapshotHeader = document.createElement('p');
    snapshotHeader.textContent = "Captured image of the person who attempted access:";
    snapshotContainer.appendChild(snapshotHeader);

    // Create the image element for the snapshot
    const snapshotImage = document.createElement('img');
    snapshotImage.src = data.image_url;
    snapshotImage.className = 'intruder-snapshot-image';
    snapshotImage.alt = 'Intruder Snapshot';
    snapshotContainer.appendChild(snapshotImage);
    
    // Create a timestamp
    const timeElement = document.createElement('p');
    timeElement.className = 'intruder-alert-time';
    timeElement.textContent = `Time of attempt: ${new Date(data.timestamp).toLocaleString()}`;

    // Assemble the alert
    alertDiv.appendChild(textElement);
    alertDiv.appendChild(snapshotContainer);
    alertDiv.appendChild(timeElement);

    // Add to the message container and scroll
    messageContainer.appendChild(alertDiv);
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

// Micro-Interactions & Animations
function animateElement(element, animation) {
    element.style.animation = animation;
    element.addEventListener('animationend', () => {
        element.style.animation = '';
    });
}

// Real-Time Visual Feedback
let typingTimeout;
function showTypingIndicator(username) {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.textContent = `${username} is typing...`;
    document.getElementById('messageContainer').appendChild(indicator);
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        indicator.remove();
    }, 3000);
}

// Live Status Badges
function updateUserStatus(userId, status) {
    const userElement = document.querySelector(`[data-user-id="${userId}"]`);
    if (userElement) {
        const badge = userElement.querySelector('.status-badge');
        if (badge) {
            badge.className = `status-badge ${status}`;
        }
    }
}

// Risk Level Animation
function animateRiskLevel(riskLevel) {
    const dot = document.getElementById('riskIndicatorDot');
    const text = document.getElementById('riskIndicatorText');
    dot.className = `risk-indicator-dot risk-${riskLevel}`;
    text.textContent = `Risk Level by AI: ${riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}`;
    animateElement(dot, 'fadeIn 0.3s ease-in-out');
}

// Immersive UI Enhancements
// Dark Mode Toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Customizable Chat Backgrounds
function setChatBackground(imageUrl) {
    document.querySelector('.chat-messages').style.setProperty('--chat-bg-image', `url(${imageUrl})`);
}

// Sound Effects
let soundEnabled = false;
function toggleSound() {
    soundEnabled = !soundEnabled;
    document.body.classList.toggle('sound-enabled');
    localStorage.setItem('soundEnabled', soundEnabled);
}

function playSound(sound) {
    if (soundEnabled) {
        const audio = new Audio(sound);
        audio.play();
    }
}

// Enhanced Usability
// Drag & Drop File Upload
function setupDragAndDrop() {
    const dropZone = document.querySelector('.drag-drop-zone');
    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) {
                document.getElementById('fileInput').files = e.dataTransfer.files;
                document.getElementById('fileNameDisplay').textContent = file.name;
            }
        });
    }
}

// Auto-Scroll
function scrollToBottom() {
    const messageContainer = document.getElementById('messageContainer');
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

// Message Reactions
function addReaction(messageId, reaction) {
    const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageElement) {
        const reactionsContainer = messageElement.querySelector('.message-reactions') || document.createElement('div');
        reactionsContainer.className = 'message-reactions';
        const reactionButton = document.createElement('button');
        reactionButton.className = 'reaction-button';
        reactionButton.textContent = reaction;
        reactionsContainer.appendChild(reactionButton);
        messageElement.appendChild(reactionsContainer);
    }
}

// Initialize new features
document.addEventListener('DOMContentLoaded', function () {
    // Dark Mode Toggle
    const darkModeToggle = document.createElement('button');
    darkModeToggle.className = 'dark-mode-toggle';
    darkModeToggle.textContent = 'Toggle Dark Mode';
    darkModeToggle.addEventListener('click', toggleDarkMode);
    document.querySelector('.chat-header').appendChild(darkModeToggle);

    // Sound Toggle
    const soundToggle = document.createElement('button');
    soundToggle.className = 'sound-toggle';
    soundToggle.textContent = 'Toggle Sound';
    soundToggle.addEventListener('click', toggleSound);
    document.querySelector('.chat-header').appendChild(soundToggle);

    // Setup Drag & Drop
    setupDragAndDrop();

    // Auto-Scroll
    const messageContainer = document.getElementById('messageContainer');
    messageContainer.classList.add('auto-scroll');

    // Load saved preferences
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
    if (localStorage.getItem('soundEnabled') === 'true') {
        document.body.classList.add('sound-enabled');
        soundEnabled = true;
    }
});
});