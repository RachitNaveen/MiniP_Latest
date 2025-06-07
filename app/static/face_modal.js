/**
 * Face Verification Modal Handler for SecureChat
 * This file contains functions to create and manage the face verification modal
 * for unlocking face-locked messages and files.
 */

// Keep track of global resources that need cleaning up
let currentFaceModal = null;
let currentDetectionInterval = null;
let currentVideoStream = null;
let modelsLoaded = false;

// Ensure face-api models are loaded
document.addEventListener('DOMContentLoaded', async () => {
    try {
        if (!faceapi.nets.tinyFaceDetector.params) {
            await faceapi.nets.tinyFaceDetector.loadFromUri('/static/face-api-models');
            await faceapi.nets.faceLandmark68Net.loadFromUri('/static/face-api-models');
            modelsLoaded = true;
        }
    } catch (err) {
        console.error('Error loading face detection models:', err);
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
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.className = 'face-unlock-modal-content';
    modalContent.style.cssText = `
        background: white;
        padding: 20px;
        border-radius: 10px;
        max-width: 500px;
        width: 90%;
        text-align: center;
    `;
    
    // Create modal header
    const heading = document.createElement('h3');
    heading.textContent = 'Face Verification Required';
    heading.style.marginBottom = '10px';
    
    // Create instruction paragraph
    const instruction = document.createElement('p');
    instruction.textContent = `Please verify your face to unlock this ${itemType}`;
    instruction.style.marginBottom = '15px';
    
    // Create status div
    const statusDiv = document.createElement('div');
    statusDiv.id = 'face-unlock-status';
    statusDiv.className = 'message';
    statusDiv.textContent = 'Initializing camera...';
    statusDiv.style.cssText = `
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
        background-color: #e3f2fd;
    `;
    
    // Create video container
    const videoContainer = document.createElement('div');
    videoContainer.className = 'video-container';
    videoContainer.style.cssText = `
        position: relative;
        margin: 15px 0;
    `;
    
    // Create video element
    const video = document.createElement('video');
    video.id = 'face-unlock-video';
    video.autoplay = true;
    video.playsInline = true; // Important for iOS
    video.style.cssText = `
        width: 100%;
        max-width: 400px;
        border-radius: 8px;
        border: 2px solid #ddd;
    `;
    
    videoContainer.appendChild(video);
    
    // Create buttons container
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'buttons-container';
    buttonsContainer.style.cssText = `
        display: flex;
        gap: 10px;
        justify-content: center;
        margin-top: 15px;
    `;
    
    // Create verify button
    const verifyBtn = document.createElement('button');
    verifyBtn.textContent = 'Verify Face';
    verifyBtn.className = 'btn verify-btn';
    verifyBtn.style.cssText = `
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
        z-index: 1000;
    `;
    verifyBtn.disabled = true; // Start disabled until face is detected
    
    // Create cancel button
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.className = 'btn cancel-btn';
    cancelBtn.style.cssText = `
        background-color: #f44336;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
        z-index: 1000;
    `;
    
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
                    overlayCanvas.style.cssText = `
                        position: absolute;
                        top: 0;
                        left: 0;
                        pointer-events: none;
                    `;
                    videoContainer.appendChild(overlayCanvas);
                    
                    // Define face detection function
                    const detectFaces = async () => {
                        if (!video || video.paused || video.ended) return;

                        try {
                            const detections = await faceapi.detectSingleFace(
                                video, 
                                new faceapi.TinyFaceDetectorOptions()
                            ).withFaceLandmarks();

                            // Get canvas context and clear it
                            const ctx = overlayCanvas.getContext('2d');
                            ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

                            if (detections) {
                                // Draw face landmarks
                                faceapi.draw.drawFaceLandmarks(overlayCanvas, detections.landmarks);

                                // Update status
                                statusDiv.textContent = 'Face detected! Click "Verify Face" to continue.';
                                statusDiv.style.backgroundColor = '#e8f5e8';

                                // Enable verify button
                                verifyBtn.disabled = false;
                                verifyBtn.style.opacity = '1';
                            } else {
                                // Update status
                                statusDiv.textContent = 'No face detected. Please position your face in the camera.';
                                statusDiv.style.backgroundColor = '#fff3cd';

                                // Disable verify button
                                verifyBtn.disabled = true;
                                verifyBtn.style.opacity = '0.5';
                            }
                        } catch (error) {
                            console.error('[FACE-MODAL] Face detection error:', error);
                        }
                    };
                    
                    // Start face detection interval
                    if (currentDetectionInterval) {
                        clearInterval(currentDetectionInterval);
                    }
                    currentDetectionInterval = setInterval(detectFaces, 200);
                    
                } catch (error) {
                    console.error('[FACE-MODAL] Error initializing face detection:', error);
                    statusDiv.textContent = 'Error initializing face detection. Please try again.';
                    statusDiv.style.backgroundColor = '#f8d7da';
                }
            }, 500);
        };
        
        // Handle verify button click
        verifyBtn.addEventListener('click', async () => {
            try {
                console.log('[FACE-MODAL] Verify button clicked');
                
                // Disable the button
                verifyBtn.disabled = true;
                verifyBtn.style.opacity = '0.5';
                
                // Stop detection
                if (currentDetectionInterval) {
                    clearInterval(currentDetectionInterval);
                    currentDetectionInterval = null;
                }
                
                // Update status
                statusDiv.textContent = 'Verifying...';
                statusDiv.style.backgroundColor = '#e3f2fd';
                
                // Get CSRF token
                const csrfToken = getCSRFToken();
                
                // FIXED: Use correct parameter names that match the backend
                const requestData = {
                    item_type: itemType,  // FIXED: Changed from itemType to item_type
                    item_id: parseInt(itemId)  // FIXED: Changed from itemId to item_id and ensure it's a number
                };
                
                console.log('[FACE-MODAL] Sending unlock request with data:', requestData);
                
                try {
                    // Send request to server
                    const response = await fetch('/unlock_item', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify(requestData)
                    });
                
                    // Parse response
                    const data = await response.json();
                    console.log('[FACE-MODAL] Unlock response:', data);
                    
                    if (data.success) {
                        // Update status
                        statusDiv.textContent = 'Face verification successful!';
                        statusDiv.style.backgroundColor = '#e8f5e8';
                        
                        // Add delay before cleanup
                        setTimeout(() => {
                            // Cleanup resources
                            cleanupFaceVerificationResources();
                            
                            // Call success callback
                            if (typeof onSuccess === 'function') {
                                console.log('[FACE-MODAL] Calling success callback with data:', data);
                                onSuccess(data);
                            }
                        }, 1000);
                    } else {
                        // Update status
                        statusDiv.textContent = data.message || 'Face verification failed. Please try again.';
                        statusDiv.style.backgroundColor = '#f8d7da';
                        
                        // Re-enable button after delay
                        setTimeout(() => {
                            verifyBtn.disabled = false;
                            verifyBtn.style.opacity = '1';
                            
                            // Restart detection
                            if (!currentDetectionInterval) {
                                currentDetectionInterval = setInterval(detectFaces, 200);
                            }
                        }, 2000);
                    }
                } catch (error) {
                    console.error('[FACE-MODAL] Network error during verification:', error);
                    statusDiv.textContent = 'Network error during verification. Please try again.';
                    statusDiv.style.backgroundColor = '#f8d7da';
                    
                    // Re-enable button
                    verifyBtn.disabled = false;
                    verifyBtn.style.opacity = '1';
                }
            } catch (error) {
                console.error('[FACE-MODAL] Error during verification:', error);
                statusDiv.textContent = 'Error during verification. Please try again.';
                statusDiv.style.backgroundColor = '#f8d7da';
                
                // Re-enable button
                verifyBtn.disabled = false;
                verifyBtn.style.opacity = '1';
            }
        });
        
        // Handle cancel button click
        cancelBtn.addEventListener('click', () => {
            console.log('[FACE-MODAL] Cancel button clicked');
            cleanupFaceVerificationResources();
        });
        
    })
    .catch(error => {
        console.error('[FACE-MODAL] Camera access error:', error);
        statusDiv.textContent = 'Camera access denied. Please allow camera access and try again.';
        statusDiv.style.backgroundColor = '#f8d7da';
        
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