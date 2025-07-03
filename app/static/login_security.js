/**
 * Login Security Management
 * Handles login form behavior based on security levels
 */

document.addEventListener('DOMContentLoaded', function() {
  console.log('[LOGIN-SECURITY] Script loaded');
  
  // Reference to form elements
  const usernameField = document.getElementById('username');
  const passwordField = document.getElementById('password');
  const captchaSection = document.getElementById('captchaSection');
  const loginForm = document.getElementById('loginForm');
  
  // Get current security level preference
  const securityLevelSelect = document.getElementById('security-level');
  const currentSecurityLevel = localStorage.getItem('selectedSecurityLevel') || 'ai';
  
  /**
   * Update the form UI based on the security level
   */
  function updateLoginFormForSecurityLevel(level) {
    console.log(`[LOGIN-SECURITY] Updating form for security level: ${level}`);
    
    // CRITICAL: Always ensure username and password fields are enabled and visible for ALL security levels
    if (usernameField) {
      console.log('[LOGIN-SECURITY] Username field found, ensuring it is visible');
      usernameField.disabled = false;
      usernameField.required = true;
      usernameField.style.display = 'block';
      usernameField.style.opacity = '1';
      usernameField.style.visibility = 'visible';
      
      if (usernameField.parentElement) {
        usernameField.parentElement.style.display = 'block';
        usernameField.parentElement.style.opacity = '1';
        usernameField.parentElement.style.visibility = 'visible';
      }
    } else {
      console.error('[LOGIN-SECURITY] Username field not found in DOM!');
    }
    
    // CRITICAL: Password field must always be visible, especially for LOW security
    if (passwordField) {
      console.log('[LOGIN-SECURITY] Password field found, ensuring it is visible');
      passwordField.disabled = false;
      passwordField.required = true;
      passwordField.readOnly = false;
      passwordField.style.display = 'block';
      passwordField.style.visibility = 'visible';
      passwordField.style.opacity = '1';
      passwordField.setAttribute('style', 'display: block !important; opacity: 1 !important; visibility: visible !important;');
      passwordField.tabIndex = 0;
      
      // Force parent element visibility too
      if (passwordField.parentElement) {
        passwordField.parentElement.style.display = 'block';
        passwordField.parentElement.style.visibility = 'visible';
        passwordField.parentElement.setAttribute('style', 'display: block !important; opacity: 1 !important; visibility: visible !important;');
      }
      
      // Add debugging output for password field
      console.log(`[LOGIN-SECURITY] Password field was made visible: display=${passwordField.style.display}, visible=${passwordField.style.visibility}`);
      console.log('[LOGIN-SECURITY] Password field style attribute: ' + passwordField.getAttribute('style'));
      
      // Ensure it's not hidden by class
      passwordField.className = passwordField.className.replace(/hidden|hide|invisible/g, '');
      if (passwordField.parentElement) {
        passwordField.parentElement.className = passwordField.parentElement.className.replace(/hidden|hide|invisible/g, '');
      }
    } else {
      console.error('[LOGIN-SECURITY] Password field not found in DOM!');
    }
    
    // Show/hide CAPTCHA based on security level
    if (captchaSection) {
      if (level === 'medium' || level === 'high') {
        captchaSection.style.display = 'block';
        console.log('[LOGIN-SECURITY] CAPTCHA section shown');
      } else {
        captchaSection.style.display = 'none';
        console.log('[LOGIN-SECURITY] CAPTCHA section hidden');
      }
    }
  }
  
  // Set the security level in the selector if available
  if (securityLevelSelect && currentSecurityLevel) {
    securityLevelSelect.value = currentSecurityLevel;
  }
  
  // Initialize form for the current security level
  updateLoginFormForSecurityLevel(currentSecurityLevel);
  
  // Listen for security level changes
  if (securityLevelSelect) {
    securityLevelSelect.addEventListener('change', function() {
      updateLoginFormForSecurityLevel(this.value);
    });
  }
  
  // Ensure password field is visible after a short delay to override any other scripts
  setTimeout(function() {
    if (passwordField) {
      console.log('[LOGIN-SECURITY] Forcing password field visibility after timeout');
      passwordField.style.display = 'block';
      passwordField.style.visibility = 'visible';
      passwordField.style.opacity = '1';
      passwordField.setAttribute('style', 'display: block !important; visibility: visible !important; opacity: 1 !important;');
      
      // Make sure the password field is required
      passwordField.required = true;
      passwordField.setAttribute('required', 'required');
      
      if (passwordField.parentElement) {
        passwordField.parentElement.style.display = 'block';
        passwordField.parentElement.style.visibility = 'visible';
        passwordField.parentElement.setAttribute('style', 'display: block !important; visibility: visible !important; opacity: 1 !important;');
      }
      
      // Focus the username field to indicate the form is ready
      if (usernameField) {
        usernameField.focus();
      }
      
      // Log the state of the password field for debugging
      console.log('[LOGIN-SECURITY] Password field final state:', {
        display: passwordField.style.display,
        visibility: passwordField.style.visibility,
        opacity: passwordField.style.opacity,
        required: passwordField.required,
        disabled: passwordField.disabled,
        styleAttribute: passwordField.getAttribute('style')
      });
    }
  }, 1000);
  
  // When applying a security level, ensure we update the form
  const setLevelBtn = document.getElementById('set-level-btn');
  if (setLevelBtn) {
    setLevelBtn.addEventListener('click', function() {
      const selectedLevel = securityLevelSelect.value;
      updateLoginFormForSecurityLevel(selectedLevel);
    });
  }
  
  // Form submission validation
  if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
      // Get the current security level
      const currentLevel = securityLevelSelect.value;
      console.log(`[LOGIN-SECURITY] Form submitted for security level: ${currentLevel}`);
      
      // For all security levels, validate username and password
      if (!usernameField.value.trim()) {
        event.preventDefault();
        alert('Please enter a username');
        usernameField.focus();
        return;
      }
      
      if (!passwordField.value.trim()) {
        event.preventDefault();
        alert('Please enter a password');
        passwordField.focus();
        return;
      }
      
      // For medium and high security, validate CAPTCHA is completed
      // Note: Server-side validation will still occur, this is just for UX
      if ((currentLevel === 'medium' || currentLevel === 'high') && captchaSection) {
        if (captchaSection.style.display !== 'none') {
          // CAPTCHA validation happens server-side via form.validate_on_submit()
          console.log('[LOGIN-SECURITY] Medium/High security form submitted, CAPTCHA required');
        }
      }
    });
  }
});
