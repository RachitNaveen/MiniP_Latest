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
