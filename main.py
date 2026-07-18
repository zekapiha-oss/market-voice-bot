import os
import requests
import feedparser
from groq import Groq

# 1. Получаем ключи из GitHub Secrets
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

def main():
    print("⏳ Бот запущен и проверяет новости...")
    
    # 2. Проверка ключей
    if not GROQ_API_KEY or not BOT_TOKEN:
        print("❌ Ошибка: Ключи не найдены в настройках!")
        return

    # 3. Чтение RSS
    RSS_URL = "https://cointelegraph.com/rss"
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ Ошибка: Не удалось получить новости из RSS.")
        return
    
    # Берем первую свежую новость
    news = feed.entries[0]
    print(f"✅ Найдена новость: {news.title}")
    
    # 4. Анализ ИИ
    client = Groq(api_key=GROQ_API_KEY)
    raw_text = f"Заголовок: {news.title}\nТекст: {getattr(news, 'summary', '')}"
    
    try:
        print("⏳ Отправляем новость на анализ в AI...")
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Ты — аналитик. Перепиши новость для Telegram на украинском языке, формат: Заголовок, Суть, Анализ, Вывод."},
                {"role": "user", "content": raw_text}
            ]
        )
        post_text = completion.choices[0].message.content
        full_post = f"{post_text}\n\nИсточник: {news.link}"
    except Exception as e:
        print(f"❌ Ошибка ИИ: {e}")
        return

    # 5. Отправка в Telegram
    print("⏳ Отправляем пост в Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": full_post, "parse_mode": "Markdown"}
    
    res = requests.post(url, data=payload)
    
    if res.status_code == 200:
        print("🎉 Успех! Пост опубликован.")
    else:
        print(f"❌ Ошибка Telegram: {res.text}")

if __name__ == "__main__":
    main()
