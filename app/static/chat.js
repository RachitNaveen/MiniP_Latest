document.addEventListener('DOMContentLoaded', function () {
    const messageContainer = document.getElementById('messageContainer');
    const messageForm = document.getElementById('messageForm');
    const recipientInput = document.querySelector('.message-select');
    const messageInput = document.querySelector('.message-input');
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
        }, 1000); // Retry connection after 1 second
    });

    // Update online users dropdown
    socket.on('user_list', function (users) {
    console.log('Received user_list:', users); // Debug log
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
            addMessageToUI(data);
        });

        // Handle form submission
        if (messageForm) {
            messageForm.addEventListener('submit', function (e) {
                e.preventDefault();

                const content = messageInput.value.trim();
                const recipientId = recipientInput.value;

                if (!recipientId || !content) {
                    alert('Please select a recipient and enter a message.');
                    return;
                }

                // Emit the message to the server
                socket.emit('send_message', {
                    content: content,
                    recipient_id: recipientId
                });

                // Clear the input field
                messageInput.value = '';
            });
        }

        // Add message to the UI
        function addMessageToUI(message) {
            const isCurrentUser = String(message.sender_id) === String(currentUserId);
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isCurrentUser ? 'sent' : 'received'}`;
            messageDiv.innerHTML = `
                <div class="message-user">${isCurrentUser ? 'You' : message.sender_username}</div>
                <div class="message-content">${message.content}</div>
            `;
            messageContainer.appendChild(messageDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;
        }
    } catch (e) {
        console.error('Socket.IO not available:', e);
    }
});