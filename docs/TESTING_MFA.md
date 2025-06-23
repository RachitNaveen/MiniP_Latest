# AI-Based Multi-Factor Authentication Testing Guide

This guide outlines how to test the AI-based Multi-Factor Authentication (MFA) feature in the SecureChat application. The system dynamically applies different authentication requirements based on evaluated risk factors.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Initialize the database:
   ```
   python init_db.py
   ```

3. Run the test setup script:
   ```
   python test_run.py
   ```

## Test Scenarios

### Scenario 1: Low Risk Login
A login with minimal risk factors will only require password authentication.

1. Ensure the user has logged in recently (within the last day)
2. Use a known IP address/device
3. No recent failed login attempts
4. Login during normal hours

Expected Result: Only password is required, security level is LOW.

### Scenario 2: Medium Risk Login
A login with moderate risk factors will require password + CAPTCHA.

1. User has not logged in for several days
2. Some recent failed login attempts (but not many)
3. Login during non-standard hours
4. Using a different but not highly unusual device

Expected Result: Password and CAPTCHA are required, security level is MEDIUM.

### Scenario 3: High Risk Login
A login with significant risk factors will require password + CAPTCHA + Face Verification.

1. Multiple recent failed login attempts
2. User has not logged in for a long time (e.g., 30+ days)
3. Using an unusual device or IP address
4. Login during unusual hours (e.g., middle of the night)
