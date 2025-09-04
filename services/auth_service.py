import logging
from werkzeug.security import check_password_hash
from models import User, Subscription, SubscriptionType

class AuthService:
    """
    Authentication and authorization service
    """
    
    @staticmethod
    def authenticate_user(username, password):
        """Authenticate user with username/password"""
        try:
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                return user
            return None
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return None
    
    @staticmethod
    def create_user(username, email, password, language='en'):
        """Create new user with free subscription"""
        try:
            # Check if user exists
            if User.query.filter_by(username=username).first():
                return None, "Username already exists"
            
            if User.query.filter_by(email=email).first():
                return None, "Email already registered"
            
            # Create user
            user = User()
            user.username = username
            user.email = email
            user.language = language
            user.set_password(password)
            
            from app import db
            db.session.add(user)
            db.session.commit()
            
            # Create free subscription
            subscription = Subscription()
            subscription.user_id = user.id
            subscription.subscription_type = SubscriptionType.FREE
            db.session.add(subscription)
            db.session.commit()
            
            return user, "User created successfully"
            
        except Exception as e:
            logging.error(f"User creation error: {e}")
            return None, "Failed to create user"
    
    @staticmethod
    def check_permission(user, action, resource=None):
        """Check if user has permission for action"""
        if not user:
            return False
        
        # Admin has all permissions
        if user.is_admin:
            return True
        
        # Define permission rules here
        permissions = {
            'create_bot': lambda u: len(u.bots) < u.get_subscription_limits()['max_bots'] or u.get_subscription_limits()['max_bots'] == -1,
            'access_admin': lambda u: u.is_admin,
            'manage_bot': lambda u, bot: bot.user_id == u.id,
        }
        
        if action in permissions:
            if resource:
                return permissions[action](user, resource)
            else:
                return permissions[action](user)
        
        return False
