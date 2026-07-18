import os
import requests
import feedparser
from groq import Groq

# Получаем ключи напрямую из системного окружения (GitHub Secrets)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# Проверка, что ключи вообще нашлись
if not GROQ_API_KEY or not BOT_TOKEN:
    print("❌ Ошибка: Ключи не найдены в переменных окружения!")
    exit(1)

client = Groq(api_key=GROQ_API_KEY)

def main():
    print("⏳ Бот запущен и проверяет новости...")
    # ... здесь твой код с RSS и логикой ...
    # (Оставь остальную часть своего кода здесь, просто убедись, 
    # что нет строк с load_dotenv)

if __name__ == "__main__":
    main()
