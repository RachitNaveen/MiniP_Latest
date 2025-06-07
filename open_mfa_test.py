#!/usr/bin/env python3
"""
MFA Test Instructions Opener

This script opens the SecureChatApp in the browser and provides testing instructions.
"""

import webbrowser

# Open the login page
URL = "http://127.0.0.1:5001/login"
webbrowser.open(URL)

print("""
==============================================================================
   Multi-Factor Authentication Test Instructions
==============================================================================

1. Test Password at Low Security Level:
   a. Set security level to "Low"
   b. Click "Apply Level" (page will reload)
   c. Try to submit the form without a password
   d. Verify that you receive an error message

2. Test CAPTCHA at Medium Security Level:
   a. Set security level to "Medium"
   b. Click "Apply Level" (page will reload)
   c. Verify that the CAPTCHA field appears
   d. Try to submit with username and password but without completing CAPTCHA
   e. Verify that you receive a CAPTCHA validation error

3. Test Face Verification at High Security Level:
   a. Set security level to "High"
   b. Click "Apply Level" (page will reload)
   c. Verify that the CAPTCHA field appears
   d. Fill in username, password, and complete CAPTCHA
   e. Submit the form
   f. Verify that you're redirected to face verification page

4. Test Security Level Dropdown Updates:
   a. Change security level using the dropdown
   b. Click "Apply Level" 
   c. Verify that the page reloads with updated form fields
   d. Try all security levels (Low, Medium, High)
   e. Verify appropriate fields appear for each level

==============================================================================
""")
