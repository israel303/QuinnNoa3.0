# השתמש בדימוי בסיס של Python
FROM python:3.11-slim

# הגדרת תיקיית עבודה
WORKDIR /app

# העתקת קובץ הדרישות
COPY requirements.txt .

# התקנת הדרישות
RUN pip install --no-cache-dir -r requirements.txt

# התקנת tornado עבור webhooks
RUN pip install tornado~=6.4

# העתקת קוד הבוט
COPY bot.py .

# פקודה להרצת הבוט
CMD ["python", "bot.py"]