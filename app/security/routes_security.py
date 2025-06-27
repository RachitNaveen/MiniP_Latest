from flask import Blueprint, jsonify, request, session
from app.security.security_ai import SECURITY_LEVEL_LOW, SECURITY_LEVEL_MEDIUM, SECURITY_LEVEL_HIGH

security_blueprint = Blueprint('security', __name__)

@security_blueprint.route('/set_security_level_login', methods=['POST'])
def set_security_level_login():
    """
    Set the security level manually from the login screen
    """
    try:
        data = request.get_json()
        print(f"[DEBUG] Received data: {data}")
        
        if not data:
            print("[DEBUG] No JSON data received")
            return jsonify({'success': False, 'message': 'No JSON data received'}), 400
            
        # Support both 'level' and 'security_level' keys for backwards compatibility
        level_key = 'level' if 'level' in data else 'security_level'
        
        if level_key not in data:
            print(f"[DEBUG] Neither 'level' nor 'security_level' in data: {list(data.keys())}")
            return jsonify({'success': False, 'message': 'Invalid request data: missing security level parameter'}), 400
            
        level = data.get(level_key)
        print(f"[DEBUG] Selected level: {level}")
        
        # Map the level string to a security level number and name
        if level == 'low':
            level_num = SECURITY_LEVEL_LOW
            level_name = 'Low'
            required_factors = ['Password']
        elif level == 'medium':
            level_num = SECURITY_LEVEL_MEDIUM
            level_name = 'Medium'
            required_factors = ['Password', 'CAPTCHA']
        elif level == 'high':
            level_num = SECURITY_LEVEL_HIGH
            level_name = 'High'
            required_factors = ['Password', 'CAPTCHA', 'Face Verification']
        elif level == 'ai':
            level_num = -1  # Special value for AI-based
            level_name = 'AI-Based'
            required_factors = ['Determined by risk assessment']
        else:
            return jsonify({
                'success': False, 
                'message': 'Invalid security level'
            }), 400
        
        # Store the manual override in the session
        if level != 'ai':
            session['manual_security_level'] = level_num
            print(f"[SECURITY] Set manual security level to {level_name} ({level_num})")
        else:
            # Remove manual override
            if 'manual_security_level' in session:
                session.pop('manual_security_level', None)
                print("[SECURITY] Removed manual security level, using AI-based assessment")
            else:
                print("[SECURITY] Using AI-based security assessment")
                
        # Debugging logs
        print(f"[DEBUG] Received security level: {level}")
        print(f"[DEBUG] CAPTCHA enabled: {level in ['medium', 'high']}")
        print(f"[DEBUG] Face verification enabled: {level == 'high'}")

        # Update session with required factors for medium and high levels
        session['captcha_enabled'] = level in ['medium', 'high']
        session['face_verification_enabled'] = level == 'high'

        # Debugging logs for session
        print(f"[DEBUG] Session captcha_enabled: {session.get('captcha_enabled')}")
        print(f"[DEBUG] Session face_verification_enabled: {session.get('face_verification_enabled')}")
        
        # Force the session to update
        session.modified = True
        
        return jsonify({
            'success': True,
            'level': level,
            'levelNum': level_num,
            'levelName': level_name,
            'requiredFactors': ', '.join(required_factors)
        })
    except Exception as e:
        print(f"Error setting security level: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_blueprint.route('/get_security_metrics', methods=['GET'])
def get_security_metrics():
    """
    Get security metrics for the current user including:
    - Risk assessment
    - Face verification accuracy
    """
    from flask_login import current_user
    from app.security.security_ai import get_risk_details, get_face_verification_accuracy
    
    print(f"[DEBUG] get_security_metrics called, authenticated: {current_user.is_authenticated}")
    
    if not current_user.is_authenticated:
        print("[DEBUG] User not authenticated, returning 401")
        return jsonify({'success': False, 'message': 'Authentication required'}), 401
    
    try:
        print(f"[DEBUG] Getting risk details for user: {current_user.username}")
        # Get risk details
        risk_details = get_risk_details(current_user.username)
        
        print(f"[DEBUG] Getting face verification accuracy for user ID: {current_user.id}")
        # Get face verification accuracy
        accuracy_metrics = get_face_verification_accuracy(current_user.id)
        
        print(f"[DEBUG] Risk details: {risk_details}, Face metrics: {accuracy_metrics}")
        
        # Combine and return metrics
        metrics = {
            'success': True,
            'risk': {
                'score': round(risk_details['risk_score'] * 100, 2),  # Convert to percentage
                'level': risk_details['security_level'],
                'factors': risk_details['risk_factors']
            },
            'face_verification': accuracy_metrics
        }
        
        return jsonify(metrics)
    except Exception as e:
        print(f"Error retrieving security metrics: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'Error retrieving security metrics'
        }), 500

@security_blueprint.route('/api/security_assessment', methods=['GET'])
def security_assessment():
    """
    Perform AI-based security assessment and return the security level.
    """
    try:
        from app.security.security_ai import get_risk_details
        username = session.get('username')
        if not username:
            return jsonify({'success': False, 'message': 'No user logged in'}), 400

        risk_details = get_risk_details(username)

        # Update session security level based on AI risk assessment
        session['security_level'] = risk_details['security_level_num']
        print(f"[SECURITY] Updated session security level to {session['security_level']}")
        
        return jsonify({'success': True, 'details': risk_details}), 200
    except Exception as e:
        print(f"Error during security assessment: {str(e)}")
        return jsonify({'success': False, 'message': 'Error during security assessment'}), 500
