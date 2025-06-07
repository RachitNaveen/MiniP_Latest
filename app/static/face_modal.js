/**
 * Face Verification Modal Handler for SecureChat
 * This file contains functions to create and manage the face verification modal
 * for unlocking face-locked messages and files.
 */
//face_modal.js
// Keep track of global resources that need cleaning up
let currentFaceModal = null;
let currentDetectionInterval = null;
let currentVideoStream = null;
let modelsLoaded = false;

// Ensure face-api models are loaded
document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('[FACE-MODAL] Loading face detection models on page load...');
        if (!faceapi.nets.tinyFaceDetector.params) {
            await faceapi.nets.tinyFaceDetector.loadFromUri('/static/face-api-models');
            await faceapi.nets.faceLandmark68Net.loadFromUri('/static/face-api-models');
            modelsLoaded = true;
            console.log('[FACE-MODAL] Face detection models pre-loaded successfully');
        }
    } catch (err) {
        console.error('[FACE-MODAL] Error pre-loading face detection models:', err);
    }
});

/**
 * Create and show a face verification modal
 * @param {string} itemType - Type of item being unlocked (message, file)
 * @param {string} itemId - ID of the item to unlock
 * @param {string} senderUsername - Username of the sender
 * @param {Function} onSuccess - Callback function to execute when verification is successful
 * @returns {HTMLElement} The modal DOM element
 */
function showFaceVerificationModal(itemType, itemId, senderUsername, onSuccess) {
    console.log(`[FACE-MODAL] Opening modal to unlock ${itemType} from ${senderUsername}`, 
                {itemType, itemId, senderUsername, hasCallback: typeof onSuccess === 'function'});
    
    // Clean up any existing modals first
    cleanupFaceVerificationResources();
    
    // Create modal container
    const modal = document.createElement('div');
    modal.className = 'face-unlock-modal';
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'face-unlock-modal-content';
    
    // Create modal header
    const heading = document.createElement('h3');
    heading.textContent = 'Face Verification Required';
    
    // Create instruction paragraph
    const instruction = document.createElement('p');
    instruction.textContent = `Please verify your face to unlock this ${itemType}`;
    
    // Create status div
    const statusDiv = document.createElement('div');
    statusDiv.id = 'face-unlock-status';
    statusDiv.className = 'message';
    statusDiv.textContent = 'Initializing camera...';
    
    // Create video container
    const videoContainer = document.createElement('div');
    videoContainer.className = 'video-container';
    
    // Create video element
    const video = document.createElement('video');
    video.id = 'face-unlock-video';
    video.autoplay = true;
    video.playsInline = true; // Important for iOS
    video.style.width = '100%';
    video.style.borderRadius = '8px';
    
    videoContainer.appendChild(video);
    
    // Create buttons container
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'buttons-container';
    
    // Create verify button
    const verifyBtn = document.createElement('button');
    verifyBtn.textContent = 'Verify Face';
    verifyBtn.className = 'btn verify-btn';
    verifyBtn.style.zIndex = '1000';
    verifyBtn.disabled = true; // Start disabled until face is detected
    
    // Create cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.className = 'btn cancel-btn';
    cancelBtn.style.zIndex = '1000';
    
    // Add buttons to container
    buttonsContainer.appendChild(verifyBtn);
    buttonsContainer.appendChild(cancelBtn);
    
    // Assemble the modal
    modalContent.appendChild(heading);
    modalContent.appendChild(instruction);
    modalContent.appendChild(statusDiv);
    modalContent.appendChild(videoContainer);
    modalContent.appendChild(buttonsContainer);
    modal.appendChild(modalContent);
    
    // Add modal to document
    document.body.appendChild(modal);
    
    // Save reference to current modal
    currentFaceModal = modal;
    
    // Start camera
    navigator.mediaDevices.getUserMedia({
        video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: "user"
        }
    })
    .then(stream => {
        // Save reference to current stream
        currentVideoStream = stream;
        
        // Set video source
        video.srcObject = stream;
        
        // Handle video metadata loaded
        video.onloadedmetadata = () => {
            video.play();
            
            // Add a delay to ensure camera is fully initialized
            setTimeout(async () => {
                try {
                    statusDiv.textContent = 'Loading face detection...';
                    
                    // Load face-api.js models if needed
                    if (!modelsLoaded || !faceapi.nets.tinyFaceDetector.params) {
                        console.log('[FACE-MODAL] Loading face detection models on demand...');
                        await faceapi.nets.tinyFaceDetector.loadFromUri('/static/face-api-models');
                        await faceapi.nets.faceLandmark68Net.loadFromUri('/static/face-api-models');
                        modelsLoaded = true;
                        console.log('[FACE-MODAL] Face detection models loaded successfully');
                    }
                    
                    // Create overlay canvas for face landmarks
                    const overlayCanvas = document.createElement('canvas');
                    overlayCanvas.className = 'face-overlay-canvas';
                    overlayCanvas.width = video.videoWidth;
                    overlayCanvas.height = video.videoHeight;
                    videoContainer.appendChild(overlayCanvas);
                    
                    // Define face detection function
                    const detectFaces = async () => {
                        if (!video || video.paused || video.ended) return;

                        try {
                            const detections = await faceapi.detectSingleFace(
                                video, 
                                new faceapi.TinyFaceDetectorOptions()
                            ).withFaceLandmarks();

                            // Log detected landmarks for debugging
                            if (detections && detections.landmarks) {
                                console.log('[FACE-MODAL] Detected landmarks:', detections.landmarks.positions);
                            } else {
                                console.warn('[FACE-MODAL] No landmarks detected.');
                            }

                            // Get canvas context and clear it
                            const ctx = overlayCanvas.getContext('2d');
                            ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

                            if (detections) {
                                // Draw face landmarks
                                faceapi.draw.drawFaceLandmarks(ctx, detections.landmarks);

                                // Draw face positioning guide
                                const displaySize = { width: video.videoWidth, height: video.videoHeight };
                                const center = { x: displaySize.width / 2, y: displaySize.height / 2 };

                                ctx.strokeStyle = "#00ff00";
                                ctx.lineWidth = 2;
                                ctx.beginPath();
                                ctx.arc(center.x, center.y, 100, 0, 2 * Math.PI);
                                ctx.stroke();

                                // Update status
                                statusDiv.textContent = 'Align your face within the frame and hold still.';
                                statusDiv.style.color = '#007bff'; // Blue text for instructions
                                statusDiv.style.fontWeight = 'bold';
                                statusDiv.style.marginBottom = '10px';

                                // Enable verify button
                                verifyBtn.disabled = false;
                            } else {
                                // Update status
                                statusDiv.textContent = 'No face detected. Please position your face in the camera.';
                                statusDiv.className = 'message warning';

                                // Disable verify button
                                verifyBtn.disabled = true;
                            }
                        } catch (error) {
                            console.error('[FACE-MODAL] Face detection error:', error);
                        }
                    };
                    window.detectFaces = detectFaces;
                    // Start face detection interval
                    if (currentDetectionInterval) {
                        clearInterval(currentDetectionInterval);
                    }
                    currentDetectionInterval = setInterval(detectFaces, 200);
                    
                } catch (error) {
                    console.error('[FACE-MODAL] Error initializing face detection:', error);
                    statusDiv.textContent = 'Error initializing face detection. Please try again.';
                    statusDiv.className = 'message error';
                }
            }, 500);
        };
        
        // Handle verify button click
        verifyBtn.addEventListener('click', async () => {
            try {
                verifyBtn.disabled = true;
                if (currentDetectionInterval) {
                    clearInterval(currentDetectionInterval);
                    currentDetectionInterval = null;
                }

                statusDiv.textContent = 'Verifying...';
                statusDiv.className = 'message info';
                const spinner = document.createElement('div');
                spinner.className = 'spinner';
                statusDiv.appendChild(spinner);

                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                const faceImage = canvas.toDataURL('image/jpeg', 0.95);

                const response = await fetch('/unlock_item', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        itemType: itemType,
                        itemId: itemId,
                        faceImage: faceImage
                    })
                });

                const data = await response.json();
                console.log('[FACE-MODAL] Verification response:', data);

                if (spinner.parentElement) {
                    spinner.parentElement.removeChild(spinner);
                }

                if (data.success) {
                    statusDiv.textContent = 'Face verification successful!';
                    statusDiv.className = 'message success';
                    setTimeout(() => {
                        cleanupFaceVerificationResources();
                        if (typeof onSuccess === 'function') {
                            onSuccess(data); // This triggers the UI update in chat.js
                        }
                    }, 1000);
                } else {
                    // --- FAILURE HANDLING ---
                    statusDiv.textContent = data.message || 'Verification failed.';
                    statusDiv.className = 'message error';

                    if (data.deleted) {
                        // If the backend confirms deletion, disable the button permanently and show the message.
                        verifyBtn.style.display = 'none'; // Hide verify button
                        cancelBtn.textContent = 'Close'; // Change cancel to close
                        
                        // We need to inform chat.js to update the original message element
                        if (typeof onSuccess === 'function') {
                            // We can re-use the onSuccess callback to pass the deletion status
                            onSuccess({ deleted: true, message: data.message });
                        }

                    } else {
                        // Not deleted yet, so re-enable the button for another try.
                        setTimeout(() => {
                            verifyBtn.disabled = false;
                            if (!currentDetectionInterval) {
                                currentDetectionInterval = setInterval(window.detectFaces, 200);
                            }
                        }, 2000);
                    }
                }
            } catch (error) {
                console.error('[FACE-MODAL] Network or other error during verification:', error);
                statusDiv.textContent = 'Network error. Please check your connection and try again.';
                statusDiv.className = 'message error';
                verifyBtn.disabled = false;
            }
        });
        
        // Handle cancel button click
        cancelBtn.addEventListener('click', async () => {
            // Send cancellation to backend
            try {
                const response = await fetch('/unlock_item', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        itemType: itemType,
                        itemId: itemId,
                        cancelled: true
                    })
                });

                const data = await response.json();
                console.log('[FACE-MODAL] Cancellation response:', data);

                if (data.is_replaced) {
                    statusDiv.textContent = "MESSAGE DELETED...";
                    statusDiv.className = 'message error';
                    cleanupFaceVerificationResources();
                }
            } catch (error) {
                console.error('[FACE-MODAL] Error sending cancellation:', error);
            }

            // Close modal
            cleanupFaceVerificationResources();
        });
        
    })
    .catch(error => {
        console.error('[FACE-MODAL] Camera access error:', error);
        statusDiv.textContent = 'Camera access denied. Please allow camera access and try again.';
        statusDiv.className = 'message error';
        
        // Enable close button even if camera fails
        cancelBtn.addEventListener('click', () => {
            cleanupFaceVerificationResources();
        });
    });
    
    return modal;
}

/**
 * Clean up resources used by the face verification modal
 */
function cleanupFaceVerificationResources() {
    console.log('[FACE-MODAL] Cleaning up resources');
    
    // Clear detection interval
    if (currentDetectionInterval) {
        clearInterval(currentDetectionInterval);
        currentDetectionInterval = null;
    }
    
    // Stop video stream
    if (currentVideoStream) {
        currentVideoStream.getTracks().forEach(track => track.stop());
        currentVideoStream = null;
    }
    
    // Remove modal
    if (currentFaceModal && currentFaceModal.parentElement) {
        currentFaceModal.parentElement.removeChild(currentFaceModal);
        currentFaceModal = null;
    }
}

/**
 * Get CSRF token from meta tag or cookie
 */
function getCSRFToken() {
    // Try getting from meta tag
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    
    // Try getting from cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith('csrf_token=')) {
            return cookie.substring('csrf_token='.length);
        }
    }
    
    console.warn('[FACE-MODAL] CSRF token not found');
    return '';
}