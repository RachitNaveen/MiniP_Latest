# SecureChat: AI-Based Multi-Factor Authentication System

A secure real-time chat application featuring an advanced AI-based Multi-Factor Authentication (MFA) system that dynamically adjusts security requirements based on risk assessment.

## Table of Contents
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Requirements](#-requirements)
- [Installation & Setup](#%EF%B8%8F-installation--setup)
- [Running the Application](#-running-the-application)
- [Testing the AI-MFA System](#-testing-the-ai-mfa-system)
- [Security Level Examples](#-security-level-examples)
- [Troubleshooting](#-troubleshooting)

## 

- **AI-Based Multi-Factor Authentication**
  - Dynamic security levels based on risk assessment
  - Real-time risk factor evaluation
  - Transparent security decisions with risk visualization
  - Face registration during signup
  
- **Multiple Authentication Factors**
  - Password authentication
  - CAPTCHA verification
  - Face verification with face-api.js and face_recognition
  - Face-locked messages and files
  
- **Advanced Security Features**
  - Password hashing using PBKDF2-SHA256
  - Session management
  - Secure credential handling
  
- **Real-Time Communication**
  - Public and private messaging
  - Online user status updates
  - Real-time notifications

- **User-Friendly Interface**
  - Clean, responsive design
  - Risk visualization panels
  - Clear security level indicators

## 

The AI-based Multi-Factor Authentication system works as follows:

1. **Risk Assessment**: When a user attempts to log in, the system evaluates various risk factors:
   - Recent failed login attempts
   - Login location/IP address analysis
