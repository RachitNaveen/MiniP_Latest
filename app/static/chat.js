document.addEventListener('DOMContentLoaded', function () {
    const messageContainer = document.getElementById('messageContainer');
    const messageForm = document.querySelector('.message-form');
    const messageInput = document.querySelector('.message-input');
    const recipientInput = document.querySelector('.message-select');
    const faceLockedCheckbox = document.querySelector('#faceLockedCheckbox');
    const fileInput = document.querySelector('.message-file');
    const currentUserId = document.body.dataset.userId;

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                      document.querySelector('input[name="csrf_token"]')?.value;

    if (messageContainer) {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    let socket;
    try {
        socket = io();
        
        // Join room when connected
        socket.on('connect', function() {
            console.log('Connected to server');
            socket.emit('join', { user_id: currentUserId });
        });

        // Handle new messages
        socket.on('new_message', function (data) {
            console.log('Received new message:', data);
            // Create a message object in the format expected by addMessageToUI
            const message = {
                id: data.message_id,
                content: data.message,
                timestamp: data.timestamp,
                is_face_locked: data.is_face_locked,
                user_id: data.sender_id,
                author: {
                    username: data.sender.username
                }
            };
            addMessageToUI(message);
        });

        // Handle status updates
        socket.on('status', function (status) {
            console.log('Status:', status);
        });

        // Handle connection errors
        socket.on('connect_error', function (error) {
            console.error('Socket connection error:', error);
            console.log('Falling back to HTTP polling');
        });

        // Handle disconnection
        socket.on('disconnect', function () {
            console.log('Disconnected from server');
        });
    } catch (e) {
        console.error('Socket.IO not available:', e);
    }

    // Message display function
    function addMessageToUI(message) {
        const existing = document.querySelector(`[data-message-id="${message.id}"]`);
        if (existing) return;

        const timestamp = new Date(message.timestamp);
        const time = timestamp.toTimeString().slice(0, 5);
        const isLocked = message.is_face_locked;
        const isCurrentUser = message.user_id == currentUserId;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isCurrentUser ? 'sent' : 'received'}`;
        messageDiv.dataset.messageId = message.id;

        const contentHtml = isLocked
            ? `<span class="locked-message">🔒 Face-locked message</span>`
            : message.content;

        messageDiv.innerHTML = `
            <div class="message-user">
                ${isCurrentUser ? 'You' : message.author.username}
            </div>
            ${contentHtml}
            ${message.file_path ? `<div>📎 <a href="/uploads/${message.file_path.split('/').pop()}" target="_blank">${message.file_path.split('/').pop()}</a></div>` : ''}
            <div class="message-time">${time}</div>
        `;

        if (isLocked) {
            const verifyBtn = document.createElement('button');
            verifyBtn.className = 'verify-btn';
            verifyBtn.innerHTML = 'Verify Face';
            verifyBtn.onclick = async function() {
                try {
                    // Create modal
                    const modal = document.createElement('div');
                    modal.className = 'face-verification-modal';
                    modal.innerHTML = `
                        <div class="modal-content">
                            <h3>Face Verification Required</h3>
                            <video id="verification-video" autoplay></video>
                            <div style="margin: 20px 0;">
                                <button id="verify-face-btn" class="verify-btn">Verify Face</button>
                                <button id="cancel-verification" class="cancel-btn">Cancel</button>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(modal);

                    // Get video element
                    const video = document.getElementById('verification-video');
                    const verifyBtn = document.getElementById('verify-face-btn');
                    const cancelBtn = document.getElementById('cancel-verification');

                    // Request camera access
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    video.srcObject = stream;

                    // Handle verification
                    verifyBtn.onclick = async function() {
                        try {
                            // Capture image
                            const canvas = document.createElement('canvas');
                            canvas.width = video.videoWidth;
                            canvas.height = video.videoHeight;
                            canvas.getContext('2d').drawImage(video, 0, 0);
                            
                            // Convert to base64
                            const faceImage = canvas.toDataURL('image/jpeg');
                            
                            // Send verification request with CSRF token
                            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                                              document.querySelector('input[name="csrf_token"]')?.value;

                            const response = await fetch('/verify_face', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': csrfToken
                                },
                                body: JSON.stringify({
                                    faceImage: faceImage,
                                    username: message.author.username
                                })
                            });
                            
                            const data = await response.json();
                            
                            if (data.success) {
                                // Unlock message
                                messageDiv.innerHTML = `
                                    <div class="message-user">
                                        ${isCurrentUser ? 'You' : message.author.username}
                                    </div>
                                    ${message.content}
                                    <div class="message-time">${time}</div>
                                `;
                                
                                // Remove verification button
                                messageDiv.querySelector('.verify-btn').remove();
                                
                                // Clean up
                                modal.remove();
                                stream.getTracks().forEach(track => track.stop());
                            } else {
                                alert(`Face verification failed: ${data.message}`);
                            }
                        } catch (error) {
                            console.error('Error during verification:', error);
                            alert('Error during face verification. Please try again.');
                        }
                    };

                    // Handle cancel
                    cancelBtn.onclick = function() {
                        modal.remove();
                        stream.getTracks().forEach(track => track.stop());
                    };

                    // Handle escape key
                    document.addEventListener('keydown', function(e) {
                        if (e.key === 'Escape') {
                            modal.remove();
                            stream.getTracks().forEach(track => track.stop());
                        }
                    });

                } catch (error) {
                    console.error('Error setting up verification:', error);
                    alert('Error setting up face verification. Please try again.');
                }
            };
            messageDiv.appendChild(verifyBtn);
        }

        messageContainer.appendChild(messageDiv);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    // Form submission handling
    if (messageForm) {
        messageForm.addEventListener('submit', function (e) {
            e.preventDefault();
            e.stopPropagation();

            const formData = new FormData(messageForm);
            const content = formData.get('content');
            const recipientId = formData.get('recipient_id');
            const isFaceLocked = formData.get('face_locked') === 'true';
            const file = formData.get('file');

            if (!recipientId) return;

            // Create temporary message
            const now = new Date();
            const time = now.toTimeString().slice(0, 5);
            const tempId = 'temp-' + Date.now();

            const messageDiv = document.createElement('div');
            messageDiv.className = 'message sent';
            messageDiv.dataset.messageId = tempId;

            const contentHtml = isFaceLocked
                ? `<span class="locked-message">🔒 Face-locked message</span>`
                : content;

            messageDiv.innerHTML = `
                <div class="message-user">
                    You → ${recipientInput.options[recipientInput.selectedIndex].text}
                </div>
                ${contentHtml}
                ${file ? `<div>📎 ${file.name}</div>` : ''}
                <div class="message-time">${time}</div>
            `;

            messageContainer.appendChild(messageDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;

            // Send message via Socket.IO if connected
            if (socket && socket.connected && !file) {
                socket.emit('send_message', {
                    content,
                    recipient_id: recipientId,
                    is_face_locked: isFaceLocked
                });
            } else {
                // Fallback to HTTP if Socket.IO not available or if sending a file
                fetch('/send_message', {
                    method: 'POST',
                    body: formData,
                    credentials: 'same-origin'
                })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            // Update temporary message ID with actual message ID
                            const tempMessage = messageContainer.querySelector(`[data-message-id="${tempId}"]`);
                            if (tempMessage) {
                                tempMessage.dataset.messageId = data.message_id;
                            }
                            fetchMessages(recipientId);
                        } else {
                            console.error('Failed to send message:', data.message);
                            const tempMessage = messageContainer.querySelector(`[data-message-id="${tempId}"]`);
                            if (tempMessage) tempMessage.remove();
                        }
                    })
                    .catch(error => {
                        console.error('Error sending message:', error);
                        const tempMessage = messageContainer.querySelector(`[data-message-id="${tempId}"]`);
                        if (tempMessage) tempMessage.remove();
                    });
            }

            messageInput.value = '';
            if (faceLockedCheckbox) faceLockedCheckbox.checked = false;
            if (fileInput) fileInput.value = '';
        });
    }

    // Fetch initial messages when chat loads
    if (recipientInput && recipientInput.value) {
        fetchMessages(recipientInput.value);
    }

    function fetchMessages(recipientId) {
        if (!recipientId) return;
            
        fetch(`/get_messages?recipient_id=${recipientId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(messages => {
                if (Array.isArray(messages)) {
                    updateMessages(messages);
                } else {
                    console.error('Invalid response format:', messages);
                    alert('Failed to fetch messages. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error fetching messages:', error);
                alert('Failed to fetch messages. Please try again.');
            });
    }
            
    function updateMessages(messages) {
        messageContainer.innerHTML = '';
        messages.forEach(message => addMessageToUI(message));
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    // Inactivity lock
    let inactivityTimer;
    const INACTIVITY_TIMEOUT = 300000; // 5 minutes

    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(() => {
            console.log('Inactivity detected - locking chat');
            // Implement inactivity lock logic here
        }, INACTIVITY_TIMEOUT);
    }

    document.addEventListener('mousemove', resetInactivityTimer);
    document.addEventListener('keypress', resetInactivityTimer);
    document.addEventListener('click', resetInactivityTimer);
    resetInactivityTimer();
});
