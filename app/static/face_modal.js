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
                            
                            // Get canvas context and clear it
                            const ctx = overlayCanvas.getContext('2d');
                            ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                            
                            if (detections) {
                                // Draw face landmarks
                                faceapi.draw.drawFaceLandmarks(ctx, detections.landmarks);
                                
                                // Draw face positioning guide
                                const displaySize = { width: video.videoWidth, height: video.videoHeight };
                                const center = { x: displaySize.width/2, y: displaySize.height/2 };
                                
                                ctx.strokeStyle = "#00ff00";
                                ctx.lineWidth = 2;
                                ctx.beginPath();
                                ctx.arc(center.x, center.y, 100, 0, 2 * Math.PI);
                                ctx.stroke();
                                
                                // Update status
                                statusDiv.textContent = 'Face detected! Click "Verify Face" to continue.';
                                statusDiv.className = 'message success';
                                
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
                // Disable the button
                verifyBtn.disabled = true;
                
                // Stop detection
                if (currentDetectionInterval) {
                    clearInterval(currentDetectionInterval);
                    currentDetectionInterval = null;
                }
                
                // Update status
                statusDiv.textContent = 'Verifying...';
                statusDiv.className = 'message info';
                
                // Add spinner
                const spinner = document.createElement('div');
                spinner.className = 'spinner';
                statusDiv.appendChild(spinner);
                
                // Capture frame
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                
                // Convert to image data
                const faceImage = canvas.toDataURL('image/jpeg', 0.95);
                
                // Get CSRF token
                const csrfToken = getCSRFToken();
                
                // Log request details for debugging
                console.log('[FACE-MODAL] Sending verification request for:', { 
                    itemType, 
                    itemId,
                    imageSize: faceImage ? faceImage.length : 'none',
                    paramName: 'face_image' // Log the parameter name we're using
                });
                
                try {
                    // Send request to server
                    const response = await fetch('/unlock_item', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify({
                            itemType: itemType,
                            itemId: itemId,
                            faceImage: faceImage // Updated field name to match backend expectation
                        })
                    });
                
                    // Parse response
                    const data = await response.json();
                    console.log('[FACE-MODAL] Verification response:', data);
                    
                    // Log more detailed info for debugging
                    if (!data.success) {
                        console.warn('[FACE-MODAL] Verification failed. Response:', data);
                        console.warn('[FACE-MODAL] Request parameters used: itemType=' + itemType + ', itemId=' + itemId + ', with face_image (param name)');
                    }
                    
                    // Remove spinner
                    if (spinner.parentElement) {
                        spinner.parentElement.removeChild(spinner);
                    }
                    
                    if (data.success) {
                        // Update status
                        statusDiv.textContent = 'Face verification successful!';
                        statusDiv.className = 'message success';
                        
                        // Add delay before cleanup
                        setTimeout(() => {
                            // Cleanup resources
                            cleanupFaceVerificationResources();
                            
                            // Call success callback
                            if (typeof onSuccess === 'function') {
                                onSuccess(data);
                            }
                        }, 1000);
                    } else {
                        // Update status
                        statusDiv.textContent = data.message || 'Face verification failed. Please try again.';
                        statusDiv.className = 'message error';
                        
                        // Re-enable button after delay
                        setTimeout(() => {
                            verifyBtn.disabled = false;
                            
                            // Restart detection
                            if (!currentDetectionInterval) {
                                currentDetectionInterval = setInterval(detectFaces, 200);
                            }
                        }, 2000);
                    }
                } catch (error) {
                    console.error('[FACE-MODAL] Network error during verification:', error);
                    statusDiv.textContent = 'Network error during verification. Please try again.';
                    statusDiv.className = 'message error';
                    
                    // Remove spinner if it exists
                    if (spinner && spinner.parentElement) {
                        spinner.parentElement.removeChild(spinner);
                    }
                    
                    // Re-enable button
                    verifyBtn.disabled = false;
                }
            } catch (error) {
                console.error('[FACE-MODAL] Error during verification:', error);
                statusDiv.textContent = 'Error during verification. Please try again.';
                statusDiv.className = 'message error';
                
                // Re-enable button
                verifyBtn.disabled = false;
            }
        });
        
        // Handle cancel button click
        cancelBtn.addEventListener('click', () => {
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