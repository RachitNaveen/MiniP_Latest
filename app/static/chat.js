document.addEventListener('DOMContentLoaded', function () {
    const messageContainer = document.getElementById('messageContainer');
    const messageForm = document.getElementById('messageForm');
    const recipientInput = document.querySelector('.message-select');
    const messageInput = document.querySelector('.message-input');
    const fileInput = document.getElementById('fileInput');
    const sendFileButton = document.getElementById('sendFileButton');
    const currentUserId = document.body.dataset.userId;

    let socket;

    try {
        socket = io();

        // Handle connection
        socket.on('connect', function () {
            console.log('Connected to server');
        });

        // Handle disconnection
        socket.on('disconnect', function () {
            console.log('Disconnected from server. Attempting to reconnect...');
            setTimeout(() => {
                socket.connect();
            }, 1000);
        });

        // Update online users dropdown
        socket.on('user_list', function (users) {
            console.log('Received user_list:', users);
            recipientInput.innerHTML = '<option value="" disabled selected>Select recipient</option>';
            users.forEach(user => {
                if (String(user.id) !== String(currentUserId)) {
                    const option = document.createElement('option');
                    option.value = user.id;
                    option.textContent = user.username;
                    recipientInput.appendChild(option);
                }
            });
            console.log('Recipient dropdown updated');
        });

        // Handle incoming messages
        socket.on('new_message', function (data) {
            console.log("[DEBUG] Received new_message event with data:", data);

            const isCurrentUser = String(data.sender_id) === String(currentUserId);
            addMessageToUI(data.content, isCurrentUser);
        });

        // Handle incoming files
        socket.on('new_file', function (data) {
            console.log("[DEBUG] Received new_file event with data:", data);

            // Determine if the current user is the sender or recipient
            const isCurrentUser = String(data.sender_id) === String(currentUserId);

            // Add the file to the UI only if:
            // - The current user is the sender (to show the file they sent).
            // - OR the current user is the recipient (to show the file they received).
            if (isCurrentUser) {
                console.log("[DEBUG] Sender is adding the file to their UI.");
                addFileToUI(data.file_url, data.file_name, true);
            } else if (String(data.recipient_id) === String(currentUserId)) {
                console.log("[DEBUG] Recipient is adding the file to their UI.");
                addFileToUI(data.file_url, data.file_name, false);
            }
        });

        // Handle message form submission
        if (messageForm) {
            messageForm.addEventListener('submit', function (e) {
                e.preventDefault();

                const content = messageInput.value.trim();
                const recipientId = recipientInput.value;

                if (!recipientId || !content) {
                    alert('Please select a recipient and enter a message.');
                    return;
                }

                console.log("[DEBUG] Emitting send_message event with:", { content, recipient_id: recipientId });

                // Emit message
                socket.emit('send_message', {
                    content: content,
                    recipient_id: recipientId
                });

                messageInput.value = '';
            });
        }

        // Handle file upload
        sendFileButton.addEventListener('click', function () {
            const file = fileInput.files[0];
            const recipientId = recipientInput.value;

            if (!recipientId || !file) {
                alert('Please select a recipient and a file to send.');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('recipient_id', recipientId);

            // Get the CSRF token from the meta tag
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            console.log("[DEBUG] Sending file upload request with:", {
                file: file.name,
                recipient_id: recipientId,
                csrf_token: csrfToken
            });

            fetch('/upload_file', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken // Include the CSRF token in the headers
                },
                body: formData
            })
            .then(response => {
                console.log("[DEBUG] Response status:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("[DEBUG] File upload response:", data);
                if (!data.success) {
                    alert('Failed to send file: ' + data.message);
                }
            })
            .catch(error => {
                console.error("[ERROR] Error uploading file:", error);
            })
            .finally(() => {
                sendFileButton.disabled = false;
                fileInput.value = '';
            });

            sendFileButton.disabled = true;
        });

        // Add message to the UI
        function addMessageToUI(content, isCurrentUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isCurrentUser ? 'sent' : 'received'}`;
            messageDiv.innerHTML = `
                <div class="message-user">${isCurrentUser ? 'You' : 'Other'}</div>
                <div class="message-content">${content}</div>
            `;
            console.log("[DEBUG] Adding message to UI:", { content, isCurrentUser });
            messageContainer.appendChild(messageDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }

        // Add file to the UI
        function addFileToUI(fileUrl, fileName, isCurrentUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isCurrentUser ? 'sent' : 'received'}`;
            messageDiv.innerHTML = `
                <div class="message-user">${isCurrentUser ? 'You' : 'Other'}</div>
                <div class="message-content">
                    <a href="${fileUrl}" target="_blank" download>${fileName}</a>
                </div>
            `;
            console.log("[DEBUG] Adding file to UI:", { fileUrl, fileName, isCurrentUser });
            messageContainer.appendChild(messageDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }

    } catch (e) {
        console.error('Socket.IO not available:', e);
    }
});