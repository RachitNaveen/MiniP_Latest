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

## 🚀 Features

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

## 🧠 How It Works

The AI-based Multi-Factor Authentication system works as follows:

1. **Risk Assessment**: When a user attempts to log in, the system evaluates various risk factors:
   - Recent failed login attempts
   - Login location/IP address analysis
   - Time-of-day risk evaluation
   - Account activity patterns
   - Device fingerprinting

2. **Security Level Determination**: Based on the calculated risk score, the system assigns one of three security levels:
   - **Low Risk (Level 1)**: Only password required
   - **Medium Risk (Level 2)**: Password + CAPTCHA required
   - **High Risk (Level 3)**: Password + CAPTCHA + Face Verification required

3. **Transparent Security**: The system shows users why certain security measures are being required by displaying:
   - Overall risk score
   - Security level explanation
   - Breakdown of individual risk factors
   - Descriptive explanations of detected risks

## 📦 Requirements

**For Local Development:**
- Python 3.9+ (recommended)
- pip (Python package manager)
- Virtual environment tool (recommended)
- CMake (for dlib/face_recognition installation)
- Face-API.js models

**For Docker Deployment:**
- Docker Desktop installed and running

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker (optional, for containerized deployment)

### Backend Setup
1. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   flask db upgrade
   python init_db.py
   ```

4. Run the Flask app:
   ```bash
   flask run
   ```

### Frontend Setup
1. Navigate to the React app directory:
   ```bash
   cd app/static/react-app
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### Running with Docker
1. Build the Docker image:
   ```bash
   docker build -t securechat .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 -p 5173:5173 securechat
   ```

## 🚀 Running the Application

1. Start the Flask backend:
   ```bash
   flask run
   ```

2. Start the React frontend:
   ```bash
   cd app/static/react-app
   npm run dev
   ```

3. Access the application:
   - Flask API: `http://127.0.0.1:5000`
   - React Frontend: `http://127.0.0.1:5173`

## 🧪 Testing the AI-MFA System

Run the test suite to verify the functionality:
```bash
pytest
```

The project includes several tools for testing the AI-based MFA system:

1. **Demo Script:**
   Run this to visualize different risk scenarios for a user:
   ```bash
   python demo_security_ai.py testuser
   ```

2. **Comprehensive Test:**
   Run this to test all security level transitions:
   ```bash
   python test_mfa.py all
   ```

3. **Test Runner with Instructions:**
   This creates a test user and provides interactive testing instructions:
   ```bash
   python test_run.py
   ```

4. **Unit Tests:**
   Run specific tests for the security level determination:
   ```bash
   python test_security_levels.py
   ```

For detailed testing instructions, refer to the `TESTING_MFA.md` file.

## 🔒 Security Level Examples

### Low Risk Login
- User has logged in recently (within last 24 hours)
- Login from a known device/location
- Login during business hours
- No failed login attempts

### Medium Risk Login
- User has not logged in for several days
- Some recent failed login attempts
- Login from a new device or slightly unusual time
- Some account inactivity

### High Risk Login
- Multiple failed login attempts
- Login from an unusual location
- Login at unusual hours (late night/early morning)
- Long period of account inactivity (30+ days)
- Login from an uncommon browser or device

## 👤 Face Verification Features

SecureChat includes comprehensive face verification features:

- **Face Registration During Signup**
  - Users can register their face during account creation
  - Face data is securely stored using face_recognition library

- **Face-Based Authentication**
  - Face verification required for high-security sessions
  - Seamless verification process with real-time feedback
  - Protection against unauthorized access

- **Face-Locked Messages**
  - Users can send face-locked messages for sensitive information
  - Recipients must verify their face to view face-locked content
  - Visual indicators for face-locked messages

For more details on the face verification system, see [FACE_VERIFICATION_GUIDE.md](FACE_VERIFICATION_GUIDE.md) and [FACE_VERIFICATION_IMPLEMENTATION.md](FACE_VERIFICATION_IMPLEMENTATION.md).
- Login at unusual hours (late night/early morning)
- Long period of account inactivity (30+ days)
- Login from an uncommon browser or device

## 🔧 Troubleshooting

### Database Migration Issues
If you encounter database schema errors:
```bash
flask db upgrade
```

### Face Recognition Problems
- Ensure good lighting for face verification
- Position your face clearly in the camera view
- Check that Face-API.js models are properly installed

### Docker Networking Issues
If the Docker container is running but you can't access the app:
```bash
docker logs securechat-container
```

## 📁 Project Structure

- **app/** - Main application directory
  - **auth.py** - Authentication routes and logic
  - **security_ai.py** - AI-based security assessment system
  - **models.py** - Database models
  - **templates/** - HTML templates
  - **static/** - JS, CSS, and face-api models
  
- **migrations/** - Database migrations
- **instance/** - SQLite database
- **test_*.py** - Various test scripts

## 📚 Additional Documentation

- **TESTING_MFA.md** - Detailed guide for testing the MFA system
- **IMPLEMENTATION_SUMMARY.md** - Summary of the AI MFA implementation

## 🔐 Security Notes

- Risk factors are weighted to prioritize certain security concerns
- Security level thresholds can be adjusted in security_ai.py
- By default, successful logins update the user's last_login timestamp, reducing future risk scores
- Failed face verification attempts increase a user's risk score for future login attempts
