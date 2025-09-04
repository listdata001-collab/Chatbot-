from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import enum

class SubscriptionType(enum.Enum):
    FREE = "free"
    STARTER = "starter"
    BASIC = "basic"
    PREMIUM = "premium"

class BotStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class PlatformType(enum.Enum):
    TELEGRAM = "telegram"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    language = db.Column(db.String(5), default='en', nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bots = db.relationship('Bot', backref='owner', lazy=True, cascade='all, delete-orphan')
    subscription = db.relationship('Subscription', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_subscription_limits(self):
        if not self.subscription:
            return {'max_bots': 1, 'max_messages_per_month': 100}
        
        limits = {
            SubscriptionType.FREE: {'max_bots': 1, 'max_messages_per_month': 100},
            SubscriptionType.STARTER: {'max_bots': 3, 'max_messages_per_month': 1000},
            SubscriptionType.BASIC: {'max_bots': 10, 'max_messages_per_month': 5000},
            SubscriptionType.PREMIUM: {'max_bots': -1, 'max_messages_per_month': -1}  # Unlimited
        }
        return limits.get(self.subscription.subscription_type, limits[SubscriptionType.FREE])

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_type = db.Column(db.Enum(SubscriptionType), default=SubscriptionType.FREE)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class Bot(db.Model):
    __tablename__ = 'bots'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    platform = db.Column(db.Enum(PlatformType), nullable=False)
    status = db.Column(db.Enum(BotStatus), default=BotStatus.PENDING)
    
    # Platform-specific configurations
    telegram_token = db.Column(db.String(200))
    instagram_access_token = db.Column(db.String(500))
    whatsapp_phone_number_id = db.Column(db.String(100))
    
    # AI Configuration
    ai_personality = db.Column(db.Text, default="You are a helpful assistant.")
    ai_instructions = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='bot', lazy=True, cascade='all, delete-orphan')
    analytics = db.relationship('BotAnalytics', backref='bot', lazy=True, cascade='all, delete-orphan')

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bots.id'), nullable=False)
    user_platform_id = db.Column(db.String(100), nullable=False)  # Platform-specific user ID
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    message_count = db.Column(db.Integer, default=0)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_from_user = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # AI processing info
    ai_response_time = db.Column(db.Float)  # Response time in seconds
    tokens_used = db.Column(db.Integer)

class BotAnalytics(db.Model):
    __tablename__ = 'bot_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bots.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    # Metrics
    total_messages = db.Column(db.Integer, default=0)
    unique_users = db.Column(db.Integer, default=0)
    new_conversations = db.Column(db.Integer, default=0)
    avg_response_time = db.Column(db.Float, default=0.0)
    
    # Constraints
    __table_args__ = (db.UniqueConstraint('bot_id', 'date', name='unique_bot_date'),)
