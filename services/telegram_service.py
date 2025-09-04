import os
import logging
import threading
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from app import db
from models import Bot, Conversation, Message, BotAnalytics
from services.ai_service import AIService

class TelegramService:
    def __init__(self):
        self.running_bots = {}  # bot_id: application
        self.ai_service = AIService()
    
    def start_bot(self, bot_id, token, personality):
        """Start a Telegram bot"""
        try:
            # Stop existing bot if running
            if bot_id in self.running_bots:
                self.stop_bot(bot_id)
            
            # Create application
            application = Application.builder().token(token).build()
            
            # Add handlers
            application.add_handler(CommandHandler("start", lambda update, context: self._handle_start(update, context, bot_id)))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: self._handle_message(update, context, bot_id, personality)))
            
            # Start bot in separate thread
            def run_bot():
                try:
                    application.run_polling()
                except Exception as e:
                    logging.error(f"Bot {bot_id} polling error: {e}")
            
            bot_thread = threading.Thread(target=run_bot, daemon=True)
            bot_thread.start()
            
            self.running_bots[bot_id] = application
            logging.info(f"Bot {bot_id} started successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start bot {bot_id}: {e}")
            return False
    
    def stop_bot(self, bot_id):
        """Stop a Telegram bot"""
        if bot_id in self.running_bots:
            try:
                application = self.running_bots[bot_id]
                application.stop()
                del self.running_bots[bot_id]
                logging.info(f"Bot {bot_id} stopped successfully")
                return True
            except Exception as e:
                logging.error(f"Failed to stop bot {bot_id}: {e}")
                return False
        return True
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: int):
        """Handle /start command"""
        if not update.effective_user or not update.message:
            return
            
        user_id = str(update.effective_user.id)
        
        # Create or get conversation
        conversation = self._get_or_create_conversation(bot_id, user_id)
        
        # Send welcome message
        welcome_message = "Hello! I'm your AI assistant. How can I help you today?"
        await update.message.reply_text(welcome_message)
        
        # Save message to database
        self._save_message(conversation.id, welcome_message, False)
        
        # Update analytics
        self._update_analytics(bot_id)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: int, personality: str):
        """Handle user messages"""
        if not update.effective_user or not update.message:
            return
            
        user_id = str(update.effective_user.id)
        user_message = update.message.text
        
        # Get conversation
        conversation = self._get_or_create_conversation(bot_id, user_id)
        
        # Save user message
        self._save_message(conversation.id, user_message, True)
        
        # Get conversation history
        recent_messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp.desc()).limit(20).all()
        recent_messages.reverse()  # Chronological order
        
        # Generate AI response
        ai_response = self.ai_service.generate_response(user_message, personality, recent_messages)
        
        # Send response
        if update.message:
            await update.message.reply_text(ai_response['text'])
        
        # Save AI response
        message = self._save_message(conversation.id, ai_response['text'], False)
        message.ai_response_time = ai_response['response_time']
        message.tokens_used = ai_response['tokens_used']
        
        # Update conversation
        conversation.last_message_at = datetime.utcnow()
        conversation.message_count += 2  # User message + AI response
        
        # Commit changes
        db.session.commit()
        
        # Update analytics
        self._update_analytics(bot_id)
    
    def _get_or_create_conversation(self, bot_id, user_platform_id):
        """Get existing conversation or create new one"""
        conversation = Conversation.query.filter_by(
            bot_id=bot_id,
            user_platform_id=user_platform_id
        ).first()
        
        if not conversation:
            conversation = Conversation()
            conversation.bot_id = bot_id
            conversation.user_platform_id = user_platform_id
            db.session.add(conversation)
            db.session.commit()
        
        return conversation
    
    def _save_message(self, conversation_id, content, is_from_user):
        """Save message to database"""
        message = Message()
        message.conversation_id = conversation_id
        message.content = content
        message.is_from_user = is_from_user
        db.session.add(message)
        db.session.commit()
        return message
    
    def _update_analytics(self, bot_id):
        """Update daily analytics for bot"""
        today = datetime.utcnow().date()
        
        analytics = BotAnalytics.query.filter_by(bot_id=bot_id, date=today).first()
        
        if not analytics:
            analytics = BotAnalytics()
            analytics.bot_id = bot_id
            analytics.date = today
            db.session.add(analytics)
        
        # Update metrics
        analytics.total_messages = Message.query.join(Conversation).filter(
            Conversation.bot_id == bot_id,
            Message.timestamp >= today
        ).count()
        
        analytics.unique_users = db.session.query(Conversation.user_platform_id).filter(
            Conversation.bot_id == bot_id,
            Conversation.started_at >= today
        ).distinct().count()
        
        analytics.new_conversations = Conversation.query.filter(
            Conversation.bot_id == bot_id,
            Conversation.started_at >= today
        ).count()
        
        # Calculate average response time
        avg_response = db.session.query(db.func.avg(Message.ai_response_time)).join(Conversation).filter(
            Conversation.bot_id == bot_id,
            Message.timestamp >= today,
            Message.ai_response_time.isnot(None)
        ).scalar()
        
        analytics.avg_response_time = avg_response or 0.0
        
        db.session.commit()
