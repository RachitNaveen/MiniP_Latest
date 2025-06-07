"""
Security AI Module for SecureChat
This module provides AI-based security level determination for multi-factor authentication.
"""
import time
from datetime import datetime, timedelta
import ipaddress
from flask import request, session
from app.models.models import FaceVerificationLog, User

# Security levels
SECURITY_LEVEL_LOW = 0      # Password only
SECURITY_LEVEL_MEDIUM = 1   # Password + CAPTCHA
SECURITY_LEVEL_HIGH = 2     # Password + CAPTCHA + Face Verification

# Risk factors weights
WEIGHTS = {
    'failed_attempts': 0.3,
    'unusual_location': 0.2,
    'time_risk': 0.15,
    'previous_breaches': 0.2,
    'device_risk': 0.15
}

def calculate_security_level(username):
    """
    Calculate the security level required for a user based on various risk factors.
    
    Args:
        username (str): The username attempting to log in
        
    Returns:
        int: The security level required (1=Low, 2=Medium, 3=High)
    """
    user = User.query.filter_by(username=username).first()
    
    # If user doesn't exist, require medium security by default
    if not user:
        return SECURITY_LEVEL_MEDIUM
    
    # Calculate risk score (0.0 to 1.0)
    risk_score = calculate_risk_score(user)
    
    # Determine security level based on risk score
    if risk_score < 0.3:
        return SECURITY_LEVEL_LOW
    elif risk_score < 0.7:
        return SECURITY_LEVEL_MEDIUM
    else:
        return SECURITY_LEVEL_HIGH
    
def calculate_risk_score(user):
    """
    Calculate a risk score based on multiple factors.
    
    Args:
        user (User): User object
        
    Returns:
        float: Risk score between 0.0 and 1.0
    """
    risk_factors = {}
    
    try:
        # 1. Failed login attempts
        risk_factors['failed_attempts'] = get_failed_attempts_risk(user)
        
        # 2. Unusual location/IP
        risk_factors['unusual_location'] = get_location_risk()
        
        # 3. Time of day risk
        risk_factors['time_risk'] = get_time_risk()
        
        # 4. Previous security breaches
        risk_factors['previous_breaches'] = get_previous_breaches_risk(user)
        
        # 5. Device risk
        risk_factors['device_risk'] = get_device_risk()
        
        # Calculate weighted average
        weighted_score = sum(risk_factors[factor] * WEIGHTS[factor] for factor in risk_factors)
        
        return weighted_score
    except Exception as e:
        print(f"Error calculating risk score: {str(e)}")
        # Return a moderate risk score as fallback
        return 0.5

def get_failed_attempts_risk(user):
    """Calculate risk based on recent failed login attempts"""
    # Get failed face verification attempts in the last 24 hours
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    failed_verifications = FaceVerificationLog.query.filter_by(
        user_id=user.id, 
        success=False
    ).filter(FaceVerificationLog.timestamp >= one_day_ago).count()
    
    # Simple scaling: 0 failures = 0.0, 5+ failures = 1.0
    return min(failed_verifications / 5.0, 1.0)

def get_location_risk():
    """Calculate risk based on IP address/location"""
    # Store a session fingerprint of IP
    ip = request.remote_addr
    
    # Check if this is a new IP for this user session
    if 'known_ip' not in session:
        session['known_ip'] = ip
        # New IP is moderate risk
        return 0.5
    
    # If IP changed during session, high risk
    if session['known_ip'] != ip:
        return 0.9
    
    # Known IP from session, lower risk
    return 0.1

def get_time_risk():
    """Calculate risk based on time of day"""
    current_hour = datetime.now().hour
    
    # Business hours (9 AM to 6 PM) considered lower risk
    if 9 <= current_hour <= 18:
        return 0.2
    # Early morning (5 AM to 9 AM) or evening (6 PM to 11 PM) is medium risk
    elif 5 <= current_hour < 9 or 18 < current_hour <= 23:
        return 0.5
    # Late night/early morning (11 PM to 5 AM) is higher risk
    else:
        return 0.8

def get_previous_breaches_risk(user):
    """Calculate risk based on previous account security incidents"""
    # For demo, we'll use last_login as a simple proxy
    # If user has never logged in before, moderate risk
    if not user.last_login:
        return 0.5
    
    # If user hasn't logged in for 30+ days, higher risk
    days_since_login = (datetime.utcnow() - user.last_login).days if user.last_login else 0
    if days_since_login > 30:
        return 0.8
    elif days_since_login > 7:
        return 0.5
    else:
        return 0.2

def get_device_risk():
    """Calculate risk based on device fingerprint"""
    # Simple user agent based analysis
    user_agent = request.user_agent.string.lower()
    
    # Check for mobile devices (generally higher risk than desktops)
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return 0.6
    
    # Check for uncommon browsers (might be bots or unusual clients)
    common_browsers = ['chrome', 'firefox', 'safari', 'edge']
    if not any(browser in user_agent for browser in common_browsers):
        return 0.7
        
    # Default for common desktop browsers
    return 0.3

def get_risk_details(username):
    """
    Get detailed risk assessment information for a user
    
    Args:
        username (str): The username to assess
        
    Returns:
        dict: Dictionary containing risk assessment details
    """
    try:
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Ensure all values are JSON-serializable
            return {
                'security_level': 'Medium',
                'security_level_num': SECURITY_LEVEL_MEDIUM,
                'risk_score': 0.5,
                'risk_factors': {
                    'failed_attempts': {'score': 0.0, 'description': 'Unknown user'},
                    'unusual_location': {'score': 0.5, 'description': 'New login location'},
                    'time_risk': {'score': float(get_time_risk()), 'description': 'Time of login risk'},
                    'previous_breaches': {'score': 0.5, 'description': 'Unknown user history'},
                    'device_risk': {'score': float(get_device_risk()), 'description': 'Device type risk'}
                },
                'required_factors': ['Password', 'CAPTCHA']
            }

        # Calculate risk factors and scores - ensure all are JSON serializable (float values)
        risk_factors = {
            'failed_attempts': {'score': float(get_failed_attempts_risk(user)), 'description': 'Failed login attempts'},
            'unusual_location': {'score': float(get_location_risk()), 'description': 'Unusual login location'},
            'time_risk': {'score': float(get_time_risk()), 'description': 'Time of login risk'},
            'previous_breaches': {'score': float(get_previous_breaches_risk(user)), 'description': 'Account security history'},
            'device_risk': {'score': float(get_device_risk()), 'description': 'Device type risk'}
        }

        # Calculate overall risk score
        risk_score = float(sum(risk_factors[factor]['score'] * WEIGHTS[factor] for factor in risk_factors))

        # Check if there's a manual security level override in the session
        manual_security_level = request.environ.get('HTTP_X_MANUAL_SECURITY_LEVEL')
        
        # Determine security level
        if manual_security_level:
            try:
                security_level_num = int(manual_security_level)
                if security_level_num == SECURITY_LEVEL_LOW:
                    security_level = 'Low'
                    required_factors = ['Password']
                elif security_level_num == SECURITY_LEVEL_MEDIUM:
                    security_level = 'Medium'
                    required_factors = ['Password', 'CAPTCHA']
                elif security_level_num == SECURITY_LEVEL_HIGH:
                    security_level = 'High'
                    required_factors = ['Password', 'CAPTCHA', 'Face Verification']
                else:
                    # Default to AI-based if invalid
                    security_level_num = None
            except (ValueError, TypeError):
                security_level_num = None
        
        # If no manual override, use AI-based assessment
        if not manual_security_level:
            if risk_score < 0.3:
                security_level = 'Low'
                security_level_num = SECURITY_LEVEL_LOW
                required_factors = ['Password']
            elif risk_score < 0.7:
                security_level = 'Medium'
                security_level_num = SECURITY_LEVEL_MEDIUM
                required_factors = ['Password', 'CAPTCHA']
            else:
                security_level = 'High'
                security_level_num = SECURITY_LEVEL_HIGH
                required_factors = ['Password', 'CAPTCHA', 'Face Verification']

        return {
            'security_level': security_level,
            'security_level_num': security_level_num,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'required_factors': required_factors
        }

    except Exception as e:
        print(f"Error in get_risk_details: {str(e)}")
        # Return a default medium security level
        return {
            'security_level': 'Medium',
            'security_level_num': SECURITY_LEVEL_MEDIUM,
            'risk_score': 0.5,
            'risk_factors': {
                'error': {'score': 0.5, 'description': 'Error assessing risk factors'}
            },
            'required_factors': ['Password', 'CAPTCHA']
        }

def get_failed_attempts_description(score):
    """Get human-readable description of failed attempts risk"""
    if score == 0:
        return "No recent failed login attempts"
    elif score < 0.6:
        return "Few recent failed login attempts"
    else:
        return "Multiple failed login attempts detected"

def get_location_description(score):
    """Get human-readable description of location risk"""
    if score <= 0.1:
        return "Login from familiar location"
    elif score < 0.7:
        return "Login from new location"
    else:
        return "Login location changed during session"

def get_time_risk_description():
    """Get human-readable description of time risk"""
    current_hour = datetime.now().hour
    
    if 9 <= current_hour <= 18:
        return "Login during normal business hours"
    elif 5 <= current_hour < 9 or 18 < current_hour <= 23:
        return "Login during non-standard hours"
    else:
        return "Login during unusual hours (late night/early morning)"

def get_breach_description(user):
    """Get human-readable description of breach risk"""
    if not user.last_login:
        return "First time login"
    
    days_since_login = (datetime.utcnow() - user.last_login).days
    
    if days_since_login > 30:
        return f"First login in over 30 days ({days_since_login} days)"
    elif days_since_login > 7:
        return f"First login in over a week ({days_since_login} days)"
    else:
        return f"Recent login activity ({days_since_login} days ago)"

def get_device_description():
    """Get human-readable description of device risk"""
    user_agent = request.user_agent.string.lower()
    
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return "Login from mobile device"
    
    common_browsers = ['chrome', 'firefox', 'safari', 'edge']
    if not any(browser in user_agent for browser in common_browsers):
        return "Login from uncommon browser"
        
    return "Login from desktop with common browser"