document.addEventListener('DOMContentLoaded', function () {
    const messageContainer = document.getElementById('messageContainer');
    const messageForm = document.getElementById('messageForm');
    const recipientInput = document.querySelector('.message-select');
    const messageInput = document.querySelector('.message-input');
    const fileInput = document.getElementById('fileInput');
    const sendFileButton = document.getElementById('sendFileButton');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const faceLockedCheckbox = document.getElementById('faceLocked');
    const currentUserId = document.body.dataset.userId;
    
    // Global flag to prevent duplicate form submissions
    let messageSubmissionInProgress = false;

    let socket;

    try {
        socket = io({
            reconnection: true,
            reconnectionAttempts: Infinity,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            randomizationFactor: 0.5
        });

        // Socket event handlers
        socket.on('connect', function () {});

        socket.on('disconnect', function (reason) {
            if (reason === 'io server disconnect') {
                // Server initiated disconnect
            }
        });

        socket.on('connect_error', (error) => {
            // Handle connection error silently
        });

        socket.on('user_list', function (users) {
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
            }
        });

        // Message handlers
        socket.on('new_message', function (data) {
            const isCurrentUserSender = String(data.sender_id) === String(currentUserId);
            if (isCurrentUserSender || String(data.recipient_id) === String(currentUserId)) {
                // Check for face_locked messages
                if (data.is_face_locked && !isCurrentUserSender) {
                    // Only show locked for recipient
                    if (!data.id && !data.message_id) {
                        data.id = 'msg_' + Date.now();
                    }
                    addLockedItemToUI('message', data.sender_username, data);
                } else {
                    addMessageToUI(data.content, data.sender_username, isCurrentUserSender, data.is_face_locked);
                }
            }
        });

        // File handlers  
        socket.on('new_file', function (data) {
            const isCurrentUserSender = String(data.sender_id) === String(currentUserId);
            if (isCurrentUserSender || String(data.recipient_id) === String(currentUserId)) {
                // Check for face_locked files
                if (data.is_face_locked && !isCurrentUserSender) {
                    addLockedItemToUI('file', data.sender_username, data);
                } else {
                    addFileToUI(data.file_url, data.file_name, data.sender_username, isCurrentUserSender, data.is_face_locked);
                }
            }
        });

        // Status update handler
        socket.on('user_status_update', function (data) {
            const localCurrentUserId = document.body.dataset.userId;
            if (data.type === 'face_unlocked' || data.type === 'user_logged_out') {
                if (String(data.userId) !== String(localCurrentUserId) || data.type === 'user_logged_out') {
                    if (data.type === 'face_unlocked' && String(data.userId) === String(localCurrentUserId)) return;
                    addNotificationToUI(data.message);
                }
            }
        });

        // FIXED MESSAGE FORM HANDLER - Anti-duplication version
        if (messageForm) {
            messageForm.addEventListener('submit', handleMessageSubmit);
            
            // Also prevent Enter key from causing duplicates
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    handleMessageSubmit(e);
                }
            });
            
        } else {
            console.error("Message form not found.");
        }

        function handleMessageSubmit(e) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            if (messageSubmissionInProgress) {
                return false;
            }
            messageSubmissionInProgress = true;
            
            const content = messageInput.value.trim();
            const recipientId = recipientInput.value;
            const isFaceLocked = faceLockedCheckbox ? faceLockedCheckbox.checked : false;

            if (!recipientId) {
                showCustomAlert('Please select a recipient.');
                messageSubmissionInProgress = false;
                return false;
            }
            if (!content) {
                showCustomAlert('Please enter a message.');
                messageSubmissionInProgress = false;
                return false;
            }

            const submitButton = document.getElementById('sendButton');
            const buttonText = submitButton.querySelector('.button-text');
            if (submitButton) {
                submitButton.disabled = true;
                if (buttonText) buttonText.textContent = 'Sending...';
            }

            const csrfToken = getCSRFToken();
            if (!csrfToken) {
                showCustomAlert("Error: Missing security token. Please refresh.");
                resetSubmissionState();
                return false;
            }

            const formData = new FormData();
            formData.append('content', content);
            formData.append('recipient_id', recipientId);
            formData.append('face_locked', isFaceLocked);

            fetch('/send_message', {
                method: 'POST',
                headers: { 
                    'X-CSRFToken': csrfToken 
                },
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errData => {
                        throw new Error(errData.message || `Server error: ${response.status}`);
                    }).catch(() => { 
                        throw new Error(`Server error: ${response.status}`); 
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    messageInput.value = '';
                    if (data.message_data) {
                        const msgData = data.message_data;
                        addMessageToUI(
                            msgData.content, 
                            msgData.sender_username, 
                            true,
                            msgData.is_face_locked
                        );
                    }
                } else {
                    showCustomAlert('Failed to send message: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                showCustomAlert('Error sending message: ' + error.message);
            })
            .finally(() => {
                resetSubmissionState();
            });
            
            return false;
        }

        function resetSubmissionState() {
            messageSubmissionInProgress = false;
            const submitButton = document.getElementById('sendButton');
            const buttonText = submitButton ? submitButton.querySelector('.button-text') : null;
            if (submitButton) {
                submitButton.disabled = false;
                if (buttonText) buttonText.textContent = 'Send';
            }
        }

        if (fileInput && fileNameDisplay) {
            fileInput.addEventListener('change', () => {
                fileNameDisplay.textContent = fileInput.files.length > 0 ? fileInput.files[0].name : '';
            });
        }

        if (sendFileButton) {
            sendFileButton.addEventListener('click', function () {
                const file = fileInput.files[0];
                const recipientId = recipientInput.value;
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

                const csrfToken = getCSRFToken();
                if (!csrfToken) {
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
                    if (data.success && data.file_url && data.file_name) {
                        socket.emit('new_file', {
                            file_url: data.file_url,
                            file_name: data.file_name,
                            recipient_id: recipientId,
                            face_locked: isFaceLocked
                        });
                    } else {
                        showCustomAlert('Failed to process file: ' + (data.message || 'Unknown error'));
                    }
                })
                .catch(error => {
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
            if (isLockedForSender && !isCurrentUserSender) {
                const messageId = typeof content === 'object' && content.id ? content.id : 
                                 typeof content === 'object' && content._id ? content._id : 'msg_' + Date.now();
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
            if (isCurrentUserSender && isLockedForSender) {
                contentDiv.innerHTML = `<em>(Sent as Face Locked)</em><br>${content}`;
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

        // Function to display a locked item placeholder
        function addLockedItemToUI(itemType, senderUsername, itemData) {
            if (!messageContainer) return;
            
            // Create message container
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message received locked-item-placeholder'; 

            // Create user info
            const userDiv = document.createElement('div');
            userDiv.className = 'message-user';
            userDiv.textContent = senderUsername;

            // Create content container
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content locked-content';
            
            // Add lock icon
            const lockIcon = document.createElement('span');
            lockIcon.className = 'lock-icon';
            lockIcon.innerHTML = '&#x1F512;';

            // Add lock text
            const lockText = document.createElement('span');
            lockText.textContent = `This ${itemType} is Face Locked. `;
            
            // Create unlock button with proper styling
            const unlockButton = document.createElement('button');
            unlockButton.className = 'unlock-button';
            unlockButton.style.backgroundColor = '#007bff';
            unlockButton.style.color = 'white';
            unlockButton.style.border = 'none';
            unlockButton.style.borderRadius = '4px';
            unlockButton.style.padding = '8px 16px';
            unlockButton.style.margin = '5px 0';
            unlockButton.style.cursor = 'pointer';
            unlockButton.style.fontWeight = 'bold';
            unlockButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            unlockButton.style.position = 'relative';
            unlockButton.style.zIndex = '1000';
            unlockButton.textContent = 'Unlock';
            
            // Add click handler for unlock button
            unlockButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Get the item ID, with better logging for debugging
                let itemId = itemData.id || itemData.message_id || itemData.file_id || 
                            itemData._id || itemData.messageId || itemData.fileId || 'unknown';
                
                // Define success callback
                const handleVerificationSuccess = function(data) {
                    // On successful verification, update the UI with the unlocked content
                    if (itemType === 'message') {
                        messageDiv.innerHTML = '';
                        addMessageToUI(data.content, senderUsername, false, false);
                    } else if (itemType === 'file') {
                        messageDiv.innerHTML = '';
                        addFileToUI(data.fileUrl, data.fileName, senderUsername, false, false);
                    }
                    
                    // Show notification
                    showCustomAlert(`Face verification successful! ${itemType} unlocked.`);
                };
                
                // Use face modal handler from face_modal.js
                try {
                    showFaceVerificationModal(itemType, itemId, senderUsername, handleVerificationSuccess);
                } catch (err) {
                    console.error("[DEBUG] Error showing face verification modal:", err);
                    showCustomAlert("Error initializing face verification. Please try again.");
                }
            });

            // Assemble the message
            contentDiv.appendChild(lockIcon);
            contentDiv.appendChild(lockText);
            contentDiv.appendChild(unlockButton);

            messageDiv.appendChild(userDiv);
            messageDiv.appendChild(contentDiv);
            messageContainer.appendChild(messageDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }

        function addNotificationToUI(messageText) {
            if (!messageContainer) return;
            
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'message system-notification';
            const textElement = document.createElement('p');
            textElement.textContent = messageText;
            notificationDiv.appendChild(textElement);
            messageContainer.appendChild(notificationDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }

        function getCSRFToken() {
            const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
            if (csrfTokenMeta) {
                return csrfTokenMeta.getAttribute('content');
            }
            
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith('csrf_token=')) {
                    return cookie.substring('csrf_token='.length);
                }
            }
            
            return '';
        }

        function showCustomAlert(message) {
            alert(message);
        }

        (async () => {
            try {
                await faceapi.nets.tinyFaceDetector.loadFromUri('/static/face-api-models');
                await faceapi.nets.faceLandmark68Net.loadFromUri('/static/face-api-models');
            } catch (error) {
                // Face API models failed to load - handled silently
            }
        })();

    } catch (e) {
        if (messageContainer) {
            messageContainer.innerHTML = '<p style="text-align:center; color:red;">Chat service is currently unavailable. Please try refreshing the page later.</p>';
        }
    }
    
    console.log("[DEBUG] ✅ Chat.js loaded successfully - Single instance");
});