import os
from dotenv import load_dotenv
from groq import Groq

# Завантажуємо змінні з файлу .env
load_dotenv()

# Отримуємо ключ із захищеного файлу .env
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("API ключ не знайдено. Перевірте файл .env")

# Ініціалізація клієнта
client = Groq(api_key=api_key)

print("Бот успішно ініціалізований з ключем із файлу .env")
