import logging
import os
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# הגדרת לוגים
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# טוקן הבוט ומשתני סביבה
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# פונקציה למחיקת הודעות הצטרפות/עזיבה
async def delete_join_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and (update.message.new_chat_members or update.message.left_chat_member):
        try:
            await update.message.delete()
            logger.info(f"Deleted join/leave message in chat {update.message.chat_id}")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

# פונקציה לטיפול בפקודה /cleanup
async def cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat_id = update.message.chat_id
    bot = context.bot
    last_message_id = update.message.message_id

    # בדיקה אם למשתמש יש הרשאות אדמין
    admins = await bot.get_chat_administrators(chat_id)
    if update.effective_user.id not in [admin.user.id for admin in admins]:
        await update.message.reply_text("רק אדמינים יכולים להשתמש בפקודה זו!")
        return

    start_time = time.time()  # זמן התחלה
    deleted_count = 0  # מונה למספר ההודעות שנמחקו

    try:
        # מחיקת כל ההודעות עד להודעה הנוכחית
        for message_id in range(1, last_message_id):
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
                deleted_count += 1
                logger.info(f"Deleted message ID {message_id} in chat {chat_id}")
            except Exception as e:
                logger.warning(f"Could not delete message ID {message_id}: {e}")

        # חישוב משך הזמן
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        time_str = f"{minutes:02d}:{seconds:02d}"

        # שליחת הודעת אישור
        await update.message.reply_text(f"✅ הפעולה הושלמה\n{deleted_count} הודעות נמחקו ב-{time_str} דקות")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        await update.message.reply_text("שגיאה במחיקת ההודעות. ודא שלבוט יש הרשאות מתאימות.")

async def webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        if update.message.new_chat_members or update.message.left_chat_member:
            await delete_join_messages(update, context)
        elif update.message.text == "/cleanup":
            await cleanup(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER, delete_join_messages))
    app.add_handler(CommandHandler("cleanup", cleanup))
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == '__main__':
    main()