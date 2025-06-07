/**
 * This module provides API functions for communication with the Flask backend
 */

// Base URL for API requests
const BASE_API_URL = '';

// Function to get the CSRF token from meta tag
export const getCsrfToken = (): string => {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  return metaTag ? metaTag.getAttribute('content') || '' : '';
};

// API call to fetch all users
export const fetchUsers = async () => {
  try {
    const response = await fetch(`${BASE_API_URL}/api/users`);
    if (!response.ok) throw new Error('Failed to fetch users');
    return await response.json();
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
};

// API call to fetch messages for a specific user
export const fetchMessages = async (userId: string) => {
  try {
    const response = await fetch(`${BASE_API_URL}/api/messages/${userId}`);
    if (!response.ok) throw new Error('Failed to fetch messages');
    return await response.json();
  } catch (error) {
    console.error('Error fetching messages:', error);
    throw error;
  }
};

// API call to send a message
export const sendMessage = async (content: string, recipientId: string, isLocked: boolean) => {
  const csrfToken = getCsrfToken();
  
  try {
    const response = await fetch(`${BASE_API_URL}/api/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({
        content,
        recipient_id: recipientId,
        face_locked: isLocked,
      }),
    });
    
    if (!response.ok) throw new Error('Failed to send message');
    return await response.json();
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

// API call to upload a file
export const uploadFile = async (file: File, recipientId: string, isLocked: boolean) => {
  const csrfToken = getCsrfToken();
  const formData = new FormData();
  
  formData.append('file', file);
  formData.append('recipient_id', recipientId);
  formData.append('face_locked', isLocked.toString());
  
  try {
    const response = await fetch(`${BASE_API_URL}/upload_file`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
      },
      body: formData,
    });
    
    if (!response.ok) throw new Error('Failed to upload file');
    return await response.json();
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

// API call to update security level
export const updateSecurityLevel = async (level: string) => {
  const csrfToken = getCsrfToken();
  
  try {
    const response = await fetch(`${BASE_API_URL}/security/update_level`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ level }),
    });
    
    if (!response.ok) throw new Error('Failed to update security level');
    return await response.json();
  } catch (error) {
    console.error('Error updating security level:', error);
    throw error;
  }
};

// API call to get security tips based on risk level
export const getSecurityTips = async (level: string) => {
  try {
    const response = await fetch(`${BASE_API_URL}/security/get_tips?level=${level}`);
    if (!response.ok) throw new Error('Failed to fetch security tips');
    return await response.json();
  } catch (error) {
    console.error('Error fetching security tips:', error);
    throw error;
  }
};
