import logging
import os
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# טוקן הבוט ומשתני סביבה
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8443))

# הודעה סטטית לצ'אט פרטי
PRIVATE_CHAT_MESSAGE = "הבוט הזה חסר ערך בשבילך ככל הנראה, אבל אם אתה כבר כאן למה שלא תצטרף לקבוצה שלנו? https://t.me/OldTownBackup"

# פונקציה למחיקת הודעות הצטרפות/עזיבה (רק בקבוצות)
async def delete_join_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מחיקת הודעות הצטרפות ועזיבה מהקבוצה"""
    logger.info(f"Received join/leave message update in chat {update.effective_chat.id}")
    
    if update.message and (update.message.new_chat_members or update.message.left_chat_member):
        try:
            await update.message.delete()
            logger.info(f"Successfully deleted join/leave message in chat {update.message.chat_id}")
        except Exception as e:
            logger.error(f"Error deleting join/leave message: {e}")

# פונקציה לטיפול בפקודה /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """טיפול בפקודת /start"""
    if not update.message:
        return

    logger.info(f"Start command received in chat {update.effective_chat.id} (type: {update.message.chat.type})")
    
    # בדיקה אם זה צ'אט פרטי
    if update.message.chat.type == "private":
        await update.message.reply_text(PRIVATE_CHAT_MESSAGE)
    else:
        await update.message.reply_text("הבוט פעיל! שלח /cleanup לניקוי הודעות (רק אדמינים).")

# פונקציה לטיפול בפקודה /cleanup
async def cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ניקוי כל ההודעות בקבוצה"""
    if not update.message:
        return

    logger.info(f"Cleanup command received in chat {update.effective_chat.id} (type: {update.message.chat.type})")
    
    # בדיקה אם זה צ'אט פרטי
    if update.message.chat.type == "private":
        await update.message.reply_text(PRIVATE_CHAT_MESSAGE)
        return

    chat_id = update.message.chat_id
    bot = context.bot
    last_message_id = update.message.message_id

    try:
        # בדיקה אם למשתמש יש הרשאות אדמין
        admins = await bot.get_chat_administrators(chat_id)
        user_is_admin = any(admin.user.id == update.effective_user.id for admin in admins)
        
        if not user_is_admin:
            await update.message.reply_text("רק אדמינים יכולים להשתמש בפקודה זו!")
            return

        start_time = time.time()
        deleted_count = 0

        # שליחת הודעת התחלה
        status_msg = await update.message.reply_text("🔄 מתחיל מחיקת הודעות...")

        # מחיקת כל ההודעות עד להודעה הנוכחית
        for message_id in range(1, last_message_id):
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
                deleted_count += 1
                
                # עדכון סטטוס כל 100 הודעות
                if deleted_count % 100 == 0:
                    try:
                        await status_msg.edit_text(f"🔄 נמחקו {deleted_count} הודעות...")
                    except:
                        pass
                        
            except Exception as e:
                logger.debug(f"Could not delete message ID {message_id}: {e}")

        # חישוב משך הזמן
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        time_str = f"{minutes:02d}:{seconds:02d}"

        # שליחת הודעת אישור
        final_message = f"✅ הפעולה הושלמה\n{deleted_count} הודעות נמחקו ב-{time_str} דקות"
        
        try:
            await status_msg.edit_text(final_message)
        except:
            await update.message.reply_text(final_message)
            
        logger.info(f"Cleanup completed in chat {chat_id}: {deleted_count} messages deleted in {time_str}")
        
    except Exception as e:
        logger.error(f"Error during cleanup in chat {chat_id}: {e}")
        await update.message.reply_text("שגיאה במחיקת ההודעות. ודא שלבוט יש הרשאות מתאימות.")

# פונקציה לטיפול בשגיאות
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """לוג של שגיאות"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """הפונקציה הראשית"""
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable not set!")
        return

    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL environment variable not set!")
        return

    logger.info("Starting bot...")
    
    # יצירת האפליקציה
    app = Application.builder().token(TOKEN).build()
    
    # הוספת handlers
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER,
        delete_join_messages
    ))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cleanup", cleanup))
    app.add_error_handler(error_handler)
    
    logger.info(f"Starting webhook on port {PORT}")
    logger.info(f"Webhook URL: {WEBHOOK_URL}")
    
    # הרצת הבוט עם webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

if __name__ == '__main__':
    main()