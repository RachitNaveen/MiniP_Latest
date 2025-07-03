# SecureChat - Multi-Factor Authentication System

## Overview

SecureChat is a secure messaging application that implements multiple levels of authentication based on risk assessment. The system uses AI-based risk analysis to determine the appropriate security level for each login attempt.

## Security Levels

The application implements three security levels:

1. **Low Security**
   - Requires: Username and Password
   - Use case: Low-risk scenarios

2. **Medium Security**
   - Requires: Username, Password, and CAPTCHA
   - Use case: Medium-risk scenarios or when suspicious activity is detected

3. **High Security**
   - Requires: Username, Password, CAPTCHA, and Face Verification
   - Use case: High-risk scenarios, sensitive operations, or when multiple risk factors are detected

## Running with Docker (Recommended)

The easiest way to run SecureChat is using Docker, which ensures all dependencies are properly installed and configured. This is especially important for the face recognition features.

### Prerequisites

- Docker installed on your system
- Git to clone the repository

### Quick Start

1. Clone the repository and enter the directory:
   ```
   git clone <repository-url>
   cd MiniP_Latest
   ```

2. Run the application using the provided Docker script:
   ```
   ./docker-run.sh
   ```
   
   This script will:
   - Create necessary directories (instance and logs)
   - Build the Docker image with all dependencies
   - Start the container with proper volume mapping

3. Access the application at:
   ```
   http://localhost:5000
   ```

### Using Docker Compose (Alternative)

For a more managed deployment approach, you can use Docker Compose:

1. Run the application using Docker Compose:
   ```
   docker-compose up
   ```

2. To run in detached mode (background):
   ```
   docker-compose up -d
   ```

3. To stop the application:
   ```
   docker-compose down
   ```

### Manual Docker Setup

If you prefer to run Docker commands manually:

1. Build the Docker image:
   ```
   docker build -t securechat .
   ```

2. Run the Docker container:
   ```
   docker run -p 5000:5000 \
     -v $(pwd)/instance:/app/instance \
     -v $(pwd)/logs:/app/logs \
     securechat
   ```

### Data Persistence

The application maintains persistent data in two directories:

- `instance/`: Contains the SQLite database files
- `logs/`: Contains application log files

Both directories are mounted as Docker volumes to ensure data persists between container restarts.

## Testing the Security Levels

### Option 1: Using the Test Script

Run the test script to create test users and start the application:

```bash
python test_login_security.py
```

This will:
1. Create test users for each security level
2. Start the Flask application
3. Provide credentials for testing

### Option 2: Manual Testing

1. Start the Flask application:
   ```bash
   flask run
   ```

2. Navigate to the login page: `http://localhost:5000/auth/login`

3. Use the Security Level Selector at the bottom of the page to choose a security level:
   - "AI-Based" - Will dynamically determine the security level
   - "Low" - Will only require username and password
   - "Medium" - Will require username, password, and CAPTCHA
   - "High" - Will require username, password, CAPTCHA, and face verification

4. Test credentials:
   - For Low: Username: `testlow`, Password: `lowpass123`
   - For Medium: Username: `testmedium`, Password: `mediumpass123`
   - For High: Username: `testhigh`, Password: `highpass123`

## Running Tests

To run the automated tests for security levels:

```bash
python -m unittest tests/test_login_security.py
```

## Implementation Details

- The security level is determined either manually or by AI-based risk assessment
- Form validation adapts dynamically based on the security level
- JavaScript handles UI updates to show/hide required authentication factors
