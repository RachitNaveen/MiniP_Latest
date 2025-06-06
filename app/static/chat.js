document.addEventListener('DOMContentLoaded', function () {
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
            lockIcon.innerHTML = '&#x1F512; '; // Lock emoji 🔒

            // Add lock text
            const lockText = document.createElement('span');
            lockText.textContent = `This ${itemType} is Face Locked. `;
            
            // Create unlock button with proper styling
            const unlockButton = document.createElement('button');
            unlockButton.className = 'unlock-button';
            unlockButton.style.backgroundColor = '#007bff';  // Use blue color
            unlockButton.style.color = 'white';
            unlockButton.style.border = 'none';
            unlockButton.style.borderRadius = '4px';
            unlockButton.style.padding = '8px 16px';
            unlockButton.style.margin = '5px 0';
            unlockButton.style.cursor = 'pointer';
            unlockButton.style.fontWeight = 'bold';
            unlockButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            unlockButton.style.position = 'relative';
            unlockButton.style.zIndex = '1000'; // Ensure it's above other elements
            unlockButton.textContent = 'Unlock';
            
            // Add a direct onclick handler as a backup method
            unlockButton.onclick = function(e) {
                console.log("[DEBUG] Unlock button clicked via onclick property");
                
                // Try directly showing the face modal to test if the issue is with the button or with the modal
                try {
                    // This direct call bypasses event listeners and other potential issues
                    showFaceVerificationModal(itemType, 'test_direct_call', senderUsername, (data) => {
                        console.log("[DEBUG] Direct modal call succeeded");
                        alert("Face verification modal called directly");
                    });
                } catch (err) {
                    console.error("[DEBUG] Error in direct modal call:", err);
                    alert("Error showing face verification modal: " + err.message);
                }
            };
            
            // Log the itemData for debugging
            console.log("[DEBUG] Item data for unlock:", itemData);
            
            // Add click handler for unlock button
            console.log("[DEBUG] Setting up unlock button click handler");
            unlockButton.addEventListener('click', function(e) {
                // Prevent default to ensure the event is captured
                e.preventDefault();
                e.stopPropagation();
                console.log("[DEBUG] Unlock button clicked via addEventListener");
                
                // Get the item ID, with better logging for debugging
                let itemId;
                if (itemData.id) {
                    itemId = itemData.id;
                    console.log("[DEBUG] Using itemData.id:", itemId);
                } else if (itemData.message_id) {
                    itemId = itemData.message_id;
                    console.log("[DEBUG] Using itemData.message_id:", itemId);
                } else if (itemData.file_id) {
                    itemId = itemData.file_id;
                    console.log("[DEBUG] Using itemData.file_id:", itemId);
                } else {
                    // Fallbacks for different structures
                    itemId = itemData._id || itemData.messageId || itemData.fileId || 'unknown';
                    console.log("[DEBUG] Using fallback itemId:", itemId);
                }
                
                console.log(`[DEBUG] Unlocking ${itemType} with ID: ${itemId}`);
                
                // Define success callback ahead of time
                const handleVerificationSuccess = function(data) {
                    console.log(`[DEBUG] Face verification successful callback executed: ${itemType} unlocked`, data);
                    
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
                
                // Use our dedicated face modal handler from face_modal.js
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
});