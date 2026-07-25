import os
import requests
import feedparser
from groq import Groq

# 1. Получаем ключи из окружения
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# ИСПРАВЛЕННЫЙ ПРОМПТ ПОД СТИЛЬ ВАРИАНТА 1
SYSTEM_PROMPT = """Ти — досвідчений фінансовий аналітик та автор Telegram-каналу Market Voice. Твоя мета — перетворювати сирі новини на стислі, інсайдерські та живі пости для криптоінвесторів.

ПРАВИЛА ФОРМАТУВАННЯ ТА СТИЛЮ (СУВОРО):
1. Жодних шаблонів та ярликів ("Заголовок:", "Суть:", "Аналіз:", "Висновок:"). Пиши одразу фінальний текст посту.
2. Структура посту (як у Варіанті 1):
   - Одне релевантне емодзі + Звичайний текст заголовка (БЕЗ жирного шрифту markdown). Приклад: 📊 Крипторинок сьогодні: головні події
   - Основна частина (1-2 короткі абзаци). Тільки цифри, причини, наслідки без води.
   - 📌 Market Voice: (Твій авторський інсайт одним рядком, без курсиву на назві мітки).
   - БЕЗ хештегів в кінці тексту.
3. Мова: виключно грамотна українська. Жодних русизмів.
4. Якщо вхідна новина не несе цінності (вода, чутки без фактів, реклама, немає конкретики) — у відповідь видай лише одне слово: SKIP.
5. Мінімум зайвої розмітки. Не використовуй HTML-теги."""

# Файл для хранения последней новости (чтобы не было спама дублями)
LAST_POST_FILE = "last_post.txt"

def get_last_posted_link():
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_posted_link(link):
    with open(LAST_POST_FILE, "w") as f:
        f.write(link)

def main():
    print("⏳ Бот запущен и проверяет новости...")
    
    if not GROQ_API_KEY or not BOT_TOKEN:
        print("❌ Ошибка: Ключи не найдены в настройках!")
        return

    RSS_URL = "https://cointelegraph.com/rss"
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ Ошибка: Не удалось получить новости из RSS.")
        return
    
    news = feed.entries[0]
    latest_link = news.link
    
    # === ПРОВЕРКА НА ДУБЛИКАТ ===
    if latest_link == get_last_posted_link():
        print("⏭️ Эта новость уже была опубликована. Ждем новую.")
        return
        
    print(f"✅ Найдена новая новость: {news.title}")
    
    client = Groq(api_key=GROQ_API_KEY)
    raw_text = f"Заголовок: {news.title}\nТекст: {getattr(news, 'summary', '')}"
    
    try:
        print("⏳ Отправляем новость на анализ в AI...")
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.4
        )
        
        post_text = completion.choices[0].message.content.strip()
        
        if post_text == "SKIP" or "SKIP" in post_text:
            print("⏭️ ИИ решил пропустить новость (недостаточно данных или вода).")
            save_last_posted_link(latest_link)
            return
            
        full_post = f"{post_text}\n\nДжерело: {news.link}"
        
    except Exception as e:
        print(f"❌ Ошибка ИИ: {e}")
        return

    print("⏳ Отправляем пост в Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": full_post}
    
    # Отправляем без принудительного parse_mode, чтобы текст шел чистым блоком
    res = requests.post(url, json=payload)
    
    if res.status_code == 200:
        print("🎉 Успех! Пост опубликован.")
        save_last_posted_link(latest_link)
    else:
        print(f"❌ Ошибка Telegram: {res.text}")

if __name__ == "__main__":
    main()
