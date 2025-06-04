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
                // --- MODIFICATION: Check for is_face_locked ---
                if (data.is_face_locked && !isCurrentUserSender) { // Only show locked for recipient
                    addLockedItemToUI('message', data.sender_username, data); // Pass full data for potential future use (e.g. messageId)
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
                addLockedItemToUI('message', senderUsername, { id: content.id, type: 'message' });
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

        // --- NEW FUNCTION: To display a locked item placeholder ---
        function addLockedItemToUI(itemType, senderUsername, itemData) {
            if (!messageContainer) return;
            const messageDiv = document.createElement('div');
            // Note: For recipients, locked items are always 'received'
            messageDiv.className = 'message received locked-item-placeholder'; 

            const userDiv = document.createElement('div');
            userDiv.className = 'message-user';
            userDiv.textContent = senderUsername;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content locked-content';
            
            const lockIcon = document.createElement('span');
            lockIcon.className = 'lock-icon'; // Style this with a lock icon (e.g., emoji or SVG)
            lockIcon.innerHTML = '&#x1F512; '; // Lock emoji 🔒

            const lockText = document.createElement('span');
            lockText.textContent = `This ${itemType} is Face Locked. `;
            
            const unlockButton = document.createElement('button');
            unlockButton.className = 'unlock-button secondary-action outline'; // Use your button styles
            unlockButton.textContent = 'Unlock';
            // TODO: Add event listener to unlockButton to trigger face verification for this item
            // This will be a more complex step, for now it's just a button.
            unlockButton.onclick = () => {
                // Store item data for later use
                // Get the ID from the appropriate property depending on the data structure
                const itemId = itemData.id || itemData.message_id || itemData.file_id;
                
                // Create a modal for face verification
                const modal = document.createElement('div');
                modal.className = 'face-unlock-modal';
                modal.innerHTML = `
                    <div class="face-unlock-modal-content">
                        <h3>Face Verification Required</h3>
                        <p>Please verify your face to unlock this ${itemType}</p>
                        <div id="face-unlock-status" class="message"></div>
                        <video id="face-unlock-video" autoplay style="width: 100%; border: 1px solid #ccc;"></video>
                        <div>
                            <button id="verify-unlock-btn" class="btn">Verify Face</button>
                            <button id="cancel-unlock-btn" class="btn">Cancel</button>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
                
                // Get video element and buttons
                const video = document.getElementById('face-unlock-video');
                const verifyBtn = document.getElementById('verify-unlock-btn');
                const cancelBtn = document.getElementById('cancel-unlock-btn');
                const statusDiv = document.getElementById('face-unlock-status');
                
                // Start camera with high quality settings
                navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        width: { ideal: 640 },    // Use smaller resolution for better performance
                        height: { ideal: 480 },
                        facingMode: "user"       // Use front camera
                    } 
                })
                    .then((stream) => {
                        video.srcObject = stream;
                        
                        // Wait for video to be initialized
                        video.onloadedmetadata = () => {
                            video.play();

                            // Add a delay to ensure camera is fully initialized
                            setTimeout(async () => {
                                statusDiv.textContent = 'Camera ready. Center your face and click "Verify Face"';
                                statusDiv.className = 'message success';

                                // Load face-api.js models if not already loaded
                                if (!faceapi.nets.tinyFaceDetector.params) {
                                    await faceapi.nets.tinyFaceDetector.loadFromUri('/static/face-api-models');
                                    await faceapi.nets.faceLandmark68Net.loadFromUri('/static/face-api-models');
                                    console.log("Face-api models loaded for modal.");
                                }

                                // --- Moved Face detection and landmark drawing here ---
                                const detectFaceFeatures = async () => {
                                    if (!video || video.paused || video.ended) return; // Ensure video is active
                                    const detections = await faceapi.detectSingleFace(video, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks();
                                    let overlayCanvas = video.parentElement.querySelector('.face-overlay-canvas');
                                    if (!overlayCanvas) {
                                        overlayCanvas = document.createElement('canvas');
                                        overlayCanvas.className = 'face-overlay-canvas'; // Add a class for potential styling/selection
                                        overlayCanvas.style.position = 'absolute';
                                        overlayCanvas.style.top = video.offsetTop + 'px';
                                        overlayCanvas.style.left = video.offsetLeft + 'px';
                                        overlayCanvas.width = video.clientWidth;
                                        overlayCanvas.height = video.clientHeight;
                                        video.parentElement.appendChild(overlayCanvas);
                                    }
                                    const ctx = overlayCanvas.getContext('2d');
                                    ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height); // Clear previous drawings

                                    if (detections) {
                                        faceapi.draw.drawFaceLandmarks(ctx, detections.landmarks);
                                        if (statusDiv.textContent.startsWith('No face detected') || statusDiv.textContent.startsWith('Camera ready')){
                                            statusDiv.textContent = 'Face detected! Position your face properly.';
                                            statusDiv.className = 'message success';
                                        }
                                    } else {
                                        if (!statusDiv.textContent.startsWith('Verifying')){
                                            statusDiv.textContent = 'No face detected. Please position your face in the camera.';
                                            statusDiv.className = 'message error';
                                        }
                                    }
                                };
                                // Continuously detect facial features
                                const detectionInterval = setInterval(detectFaceFeatures, 500);

                                // Clear interval when modal is closed or verification happens
                                const originalCancelClick = cancelBtn.onclick;
                                cancelBtn.onclick = () => {
                                    clearInterval(detectionInterval);
                                    if(originalCancelClick) originalCancelClick();
                                };

                                const originalVerifyClick = verifyBtn.onclick;
                                verifyBtn.onclick = async (event) => {
                                    clearInterval(detectionInterval);
                                    if(originalVerifyClick) await originalVerifyClick(event);
                                };

                            }, 1000);
                        };
                        
                        // Handle verify button click
                        verifyBtn.addEventListener('click', async () => {                                try {
                                    statusDiv.textContent = 'Verifying...';
                                    statusDiv.className = 'message info';
                                    
                                    // Wait for video to be ready
                                    if (!video.videoWidth) {
                                        statusDiv.textContent = 'Please wait for camera to initialize...';
                                        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
                                        if (!video.videoWidth) {
                                            statusDiv.textContent = 'Camera not initialized. Please try again.';
                                            statusDiv.className = 'message error';
                                            return;
                                        }
                                    }
                                         // Capture frame
                                const canvas = document.createElement('canvas');
                                canvas.width = video.videoWidth;
                                canvas.height = video.videoHeight;
                                canvas.getContext('2d').drawImage(video, 0, 0);
                                
                                // Use higher quality image format (quality 0.95)
                                const faceImage = canvas.toDataURL('image/jpeg', 0.95);
                                
                                // Add loading spinner
                                const spinner = document.createElement('div');
                                spinner.className = 'spinner';
                                statusDiv.appendChild(spinner);

                                // Send to server
                                console.log(`[DEBUG] Sending face verification request to unlock ${itemType} with ID ${itemId}`);
                                statusDiv.textContent = 'Sending face data to server...';

                                const csrfToken = getCSRFToken();
                                console.log('[DEBUG] CSRF Token available:', !!csrfToken);
                                console.log(`[DEBUG] Image data size: ${Math.round(faceImage.length / 1024)}KB`);

                                const response = await fetch('/unlock_item', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'X-CSRFToken': csrfToken
                                    },
                                    body: JSON.stringify({
                                        itemType: itemType,
                                        itemId: itemId,
                                        faceImage: faceImage
                                    })
                                });

                                const data = await response.json();
                                console.log(`[DEBUG] Face verification response:`, data);

                                // Remove spinner
                                spinner.remove();

                                if (data.success) {
                                    console.log(`[DEBUG] Successfully unlocked ${itemType}:`, data);
                                    statusDiv.textContent = 'Face verification successful!';
                                    statusDiv.className = 'message success';

                                    // Add short delay before stopping video and removing modal
                                    setTimeout(() => {
                                        // Stop video
                                        stream.getTracks().forEach(track => track.stop());

                                        // Remove modal
                                        document.body.removeChild(modal);

                                        // Replace locked content with unlocked content
                                        if (itemType === 'message') {
                                            messageDiv.innerHTML = '';
                                            addMessageToUI(data.content, senderUsername, false, false);
                                        } else if (itemType === 'file') {
                                            messageDiv.innerHTML = '';
                                            addFileToUI(data.fileUrl, data.fileName, senderUsername, false, false);
                                        }

                                        // Show notification
                                        showCustomAlert(`Face verification successful! ${itemType} unlocked.`);
                                    }, 1000);
                                } else {
                                    console.error(`[DEBUG] Failed to unlock ${itemType}:`, data.message);
                                    statusDiv.textContent = data.message || 'Face verification failed. Please try again.';
                                    statusDiv.className = 'message error';
                                    
                                    // Enable retry after a short delay
                                    setTimeout(() => {
                                        verifyBtn.disabled = false;
                                        statusDiv.textContent += ' (You may try again)';
                                    }, 2000);
                                }
                            } catch (error) {
                                console.error('Error verifying face:', error);
                                statusDiv.textContent = 'Error verifying face';
                                statusDiv.className = 'message error';
                            }
                        });
                        
                        // Handle cancel button click
                        cancelBtn.addEventListener('click', () => {
                            // Stop video
                            stream.getTracks().forEach(track => track.stop());
                            
                            // Remove modal
                            document.body.removeChild(modal);
                        });
                    })
                    .catch((error) => {
                        console.error('Error accessing camera:', error);
                        statusDiv.textContent = 'Camera access denied';
                        statusDiv.className = 'message error';
                    });
            };

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