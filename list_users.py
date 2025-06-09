#!/usr/bin/env python3
"""
Script to list all users in the database
"""
from app import create_app
from app.models.models import User

app = create_app()

with app.app_context():
    users = User.query.all()
    print('Users in database:')
    for user in users:
        print(f'- {user.username} (ID: {user.id})')
