# Face Verification in SecureChat

This document provides information about the face verification feature in SecureChat.

## Overview

Face verification adds an additional layer of security to SecureChat by:

1. Requiring biometric authentication during login (for high security sessions)
2. Enabling face-locked messages and files that can only be accessed via face verification
3. Protecting sensitive information from unauthorized access

## Features

### Face Registration

- Users can register their face during account creation
- Face data is securely stored and encrypted
- Face registration is recommended but optional

### Face-Based Authentication

- Dynamic security levels determine when face verification is required
- AI-based risk assessment can trigger face verification for suspicious login attempts
- Security level can be manually set to require face verification for all logins

### Face-Locked Messages & Files

- Users can send messages and files that require face verification to access
- Face-locked content is protected even if the user's password is compromised
- Recipients need to verify their identity with their face to view sensitive content

## Usage

### Registering Your Face

1. During account creation, click "Start Camera" in the face registration section
2. Position your face in the camera frame
3. Click "Capture Face" when the system detects your face
4. Complete registration normally

### Accessing Face-Locked Content

1. When you receive a face-locked message or file, click the "Unlock" button
2. Verify your face using the camera
3. Upon successful verification, the content will be displayed

## Technical Implementation

- Face detection and recognition using face-api.js (browser) and face_recognition (server)
- Face encodings stored securely in the database
- Multiple security checks to prevent spoofing attempts

### Test User

For testing purposes, use:
- Username: testface
- Password: Face123!

This user has face verification enabled and can send/receive face-locked messages.
