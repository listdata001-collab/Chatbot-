import logging
from datetime import datetime
from models import Bot, Conversation, Message
from services.telegram_service import TelegramService
from services.instagram_service import InstagramService
from services.whatsapp_service import WhatsAppService

class BroadcastService:
    """
    Service for broadcasting messages to multiple users
    """
    
    def __init__(self):
        self.telegram_service = TelegramService()
        self.instagram_service = InstagramService()
        self.whatsapp_service = WhatsAppService()
    
    def broadcast_message(self, bot_id, message, target_users=None):
        """
        Broadcast message to all users or specific target users
        
        Args:
            bot_id (int): Bot ID
            message (str): Message to broadcast
            target_users (list): List of user platform IDs (optional)
        
        Returns:
            dict: Broadcast results
        """
        try:
            bot = Bot.query.get(bot_id)
            if not bot:
                return {"success": False, "error": "Bot not found"}
            
            # Get target conversations
            query = Conversation.query.filter_by(bot_id=bot_id)
            if target_users:
                query = query.filter(Conversation.user_platform_id.in_(target_users))
            
            conversations = query.all()
            
            results = {
                "total_targets": len(conversations),
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            # Send messages based on platform
            for conversation in conversations:
                try:
                    success = False
                    
                    if bot.platform.value == "telegram":
                        success = self._send_telegram_broadcast(bot, conversation.user_platform_id, message)
                    elif bot.platform.value == "instagram":
                        success = self._send_instagram_broadcast(bot, conversation.user_platform_id, message)
                    elif bot.platform.value == "whatsapp":
                        success = self._send_whatsapp_broadcast(bot, conversation.user_platform_id, message)
                    
                    if success:
                        results["successful"] += 1
                        # Save broadcast message to database
                        self._save_broadcast_message(conversation.id, message)
                    else:
                        results["failed"] += 1
                        
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"User {conversation.user_platform_id}: {str(e)}")
                    logging.error(f"Broadcast error for user {conversation.user_platform_id}: {e}")
            
            return {"success": True, "results": results}
            
        except Exception as e:
            logging.error(f"Broadcast service error: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_telegram_broadcast(self, bot, user_id, message):
        """Send broadcast via Telegram"""
        # This would require access to the running bot application
        # For now, returning False as placeholder
        logging.info(f"Telegram broadcast to {user_id}: {message}")
        return False
    
    def _send_instagram_broadcast(self, bot, user_id, message):
        """Send broadcast via Instagram"""
        return self.instagram_service.send_message(user_id, message)
    
    def _send_whatsapp_broadcast(self, bot, user_id, message):
        """Send broadcast via WhatsApp"""
        return self.whatsapp_service.send_message(user_id, message)
    
    def _save_broadcast_message(self, conversation_id, message):
        """Save broadcast message to database"""
        try:
            broadcast_message = Message()
            broadcast_message.conversation_id = conversation_id
            broadcast_message.content = message
            broadcast_message.is_from_user = False
            broadcast_message.timestamp = datetime.utcnow()
            
            from app import db
            db.session.add(broadcast_message)
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Failed to save broadcast message: {e}")
    
    def get_broadcast_history(self, bot_id, limit=50):
        """Get broadcast message history"""
        try:
            # This is a simplified implementation
            # In a real system, you'd want a separate broadcasts table
            recent_messages = Message.query.join(Conversation).filter(
                Conversation.bot_id == bot_id,
                Message.is_from_user == False
            ).order_by(Message.timestamp.desc()).limit(limit).all()
            
            return {"success": True, "messages": recent_messages}
            
        except Exception as e:
            logging.error(f"Failed to get broadcast history: {e}")
            return {"success": False, "error": str(e)}
