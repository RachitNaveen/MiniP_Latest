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

Expected Result: Password, CAPTCHA, and Face Verification are required, security level is HIGH.

## Testing Risk Scenarios

You can use the included demo script to simulate different risk scenarios:

```
python demo_security_ai.py testuser
```

This will show risk assessments for three scenarios (Low, Medium, High) for the test user.

## Running Unit Tests

To run unit tests for the security level transitions:

```
python test_security_levels.py
```

## Risk Factor Details

The system evaluates the following risk factors:

1. **Failed Login Attempts**: Recent failed login or face verification attempts
2. **Unusual Location/IP**: Changes in IP address during session or new locations
3. **Time Risk**: Time of day when login attempts occur
4. **Previous Breaches**: Based on account activity patterns and time since last login
5. **Device Risk**: Based on device fingerprinting and browser identification

## Viewing Risk Details

The system displays risk assessment information to users in two places:
1. On the login page after initial authentication
2. On the face verification page if high-security authentication is required

The risk details include:
- Overall risk score
- Security level (Low, Medium, High)
- Breakdown of individual risk factors
- Required authentication factors
