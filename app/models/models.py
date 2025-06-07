from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Store hashed passwords
    face_data = db.Column(db.Text, nullable=True)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    face_verification_enabled = db.Column(db.Boolean, default=False)
    face_verification_failed_attempts = db.Column(db.Integer, default=0)
    face_verification_locked_until = db.Column(db.DateTime, nullable=True)

    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')

    face_logs = db.relationship('FaceVerificationLog', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_face_locked = db.Column(db.Boolean, default=False)
    file_path = db.Column(db.String(256), nullable=True)

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to {self.recipient_id}>'

class FaceVerificationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    success = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    details = db.Column(db.Text, nullable=True)  # JSON string for storing verification details

    def __repr__(self):
        return f'<FaceVerificationLog {self.id} User:{self.user_id} Success:{self.success}>'

    def get_details(self):
        """Get verification details as a dictionary"""
        if self.details:
            try:
                return json.loads(self.details)
            except:
                return {}
        return {}
