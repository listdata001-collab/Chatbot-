from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import _, get_locale
from werkzeug.security import generate_password_hash
from datetime import datetime, date
from sqlalchemy import func
import logging

from app import db
from models import User, Bot, Subscription, Conversation, Message, BotAnalytics, SubscriptionType, PlatformType, BotStatus
from services.ai_service import AIService
from services.telegram_service import TelegramService

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
bot_bp = Blueprint('bot', __name__)
admin_bp = Blueprint('admin', __name__)

@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.user_dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def user_dashboard():
    """User dashboard"""
    user_bots = Bot.query.filter_by(user_id=current_user.id).all()
    subscription_limits = current_user.get_subscription_limits()
    
    # Get recent analytics
    recent_analytics = []
    for bot in user_bots:
        analytics = BotAnalytics.query.filter_by(bot_id=bot.id).order_by(BotAnalytics.date.desc()).limit(7).all()
        recent_analytics.append({
            'bot': bot,
            'analytics': analytics
        })
    
    return render_template('dashboard.html', 
                         bots=user_bots, 
                         limits=subscription_limits,
                         analytics=recent_analytics)

@main_bp.route('/language/<language>')
def set_language(language):
    """Set user language"""
    session['language'] = language
    return redirect(request.referrer or url_for('main.index'))

# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            remember_me = bool(request.form.get('remember', False))
            login_user(user, remember=remember_me)
            next_page = request.args.get('next')
            flash(_('Login successful!'), 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.user_dashboard'))
        else:
            flash(_('Invalid username or password'), 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash(_('Username already exists'), 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash(_('Email already registered'), 'error')
            return render_template('register.html')
        
        # Create new user
        user = User()
        user.username = username
        user.email = email
        user.language = get_locale()
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Create free subscription
        subscription = Subscription()
        subscription.user_id = user.id
        subscription.subscription_type = SubscriptionType.FREE
        db.session.add(subscription)
        db.session.commit()
        
        flash(_('Registration successful! Please log in.'), 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash(_('You have been logged out'), 'info')
    return redirect(url_for('main.index'))

# Bot management routes
@bot_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new bot"""
    limits = current_user.get_subscription_limits()
    current_bot_count = Bot.query.filter_by(user_id=current_user.id).count()
    
    if limits['max_bots'] != -1 and current_bot_count >= limits['max_bots']:
        flash(_('You have reached your bot limit. Please upgrade your subscription.'), 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        platform = request.form['platform']
        ai_personality = request.form.get('ai_personality', 'You are a helpful assistant.')
        
        # Platform-specific configuration
        telegram_token = request.form.get('telegram_token', '')
        
        # Create bot
        bot = Bot()
        bot.user_id = current_user.id
        bot.name = name
        bot.description = description
        bot.platform = PlatformType(platform)
        bot.ai_personality = ai_personality
        if platform == 'telegram':
            bot.telegram_token = telegram_token
        
        db.session.add(bot)
        db.session.commit()
        
        # Start bot if it's Telegram
        if platform == 'telegram' and telegram_token:
            try:
                telegram_service = TelegramService()
                success = telegram_service.start_bot(bot.id, telegram_token, ai_personality)
                if success:
                    bot.status = BotStatus.ACTIVE
                    flash(_('Bot created and started successfully!'), 'success')
                else:
                    bot.status = BotStatus.INACTIVE
                    flash(_('Bot created but failed to start. Please check your token.'), 'warning')
                db.session.commit()
            except Exception as e:
                logging.error(f"Failed to start bot: {e}")
                flash(_('Bot created but failed to start. Please check your configuration.'), 'warning')
        else:
            flash(_('Bot created successfully!'), 'success')
        
        return redirect(url_for('main.dashboard'))
    
    return render_template('bot_create.html')

@bot_bp.route('/manage/<int:bot_id>')
@login_required
def manage(bot_id):
    """Manage specific bot"""
    bot = Bot.query.filter_by(id=bot_id, user_id=current_user.id).first_or_404()
    
    # Get bot statistics
    total_conversations = Conversation.query.filter_by(bot_id=bot_id).count()
    total_messages = db.session.query(func.sum(Conversation.message_count)).filter_by(bot_id=bot_id).scalar() or 0
    
    # Get recent conversations
    recent_conversations = Conversation.query.filter_by(bot_id=bot_id).order_by(Conversation.last_message_at.desc()).limit(10).all()
    
    # Get analytics for the last 7 days
    analytics = BotAnalytics.query.filter_by(bot_id=bot_id).order_by(BotAnalytics.date.desc()).limit(7).all()
    
    return render_template('bot_manage.html', 
                         bot=bot, 
                         total_conversations=total_conversations,
                         total_messages=total_messages,
                         recent_conversations=recent_conversations,
                         analytics=analytics)

@bot_bp.route('/toggle/<int:bot_id>')
@login_required
def toggle_status(bot_id):
    """Toggle bot active/inactive status"""
    bot = Bot.query.filter_by(id=bot_id, user_id=current_user.id).first_or_404()
    
    if bot.platform == PlatformType.TELEGRAM:
        telegram_service = TelegramService()
        if bot.status == BotStatus.ACTIVE:
            telegram_service.stop_bot(bot_id)
            bot.status = BotStatus.INACTIVE
            flash(_('Bot stopped successfully'), 'info')
        else:
            success = telegram_service.start_bot(bot_id, bot.telegram_token, bot.ai_personality)
            if success:
                bot.status = BotStatus.ACTIVE
                flash(_('Bot started successfully'), 'success')
            else:
                flash(_('Failed to start bot. Please check your configuration.'), 'error')
    
    db.session.commit()
    return redirect(url_for('bot.manage', bot_id=bot_id))

@bot_bp.route('/delete/<int:bot_id>')
@login_required
def delete(bot_id):
    """Delete bot"""
    bot = Bot.query.filter_by(id=bot_id, user_id=current_user.id).first_or_404()
    
    # Stop bot if running
    if bot.status == BotStatus.ACTIVE and bot.platform == PlatformType.TELEGRAM:
        telegram_service = TelegramService()
        telegram_service.stop_bot(bot_id)
    
    db.session.delete(bot)
    db.session.commit()
    
    flash(_('Bot deleted successfully'), 'success')
    return redirect(url_for('main.dashboard'))

# Admin routes
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash(_('Access denied'), 'error')
        return redirect(url_for('main.dashboard'))
    
    # System statistics
    total_users = User.query.count()
    total_bots = Bot.query.count()
    active_bots = Bot.query.filter_by(status=BotStatus.ACTIVE).count()
    total_conversations = Conversation.query.count()
    
    # Recent registrations
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Subscription distribution
    subscription_stats = db.session.query(
        Subscription.subscription_type,
        func.count(Subscription.id)
    ).group_by(Subscription.subscription_type).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_bots=total_bots,
                         active_bots=active_bots,
                         total_conversations=total_conversations,
                         recent_users=recent_users,
                         subscription_stats=subscription_stats)
