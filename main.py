import os
import requests
import feedparser
from groq import Groq

# 1. Получаем ключи из окружения
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

SYSTEM_PROMPT = """Ти — досвідчений фінансовий аналітик та автор Telegram-каналу Market Voice. Твоя мета — перетворювати сирі новини на стислі, інсайдерські та живі пости для криптоінвесторів.

ПРАВИЛА ФОРМАТУВАННЯ ТА СТИЛЮ (СУВОРО):
1. Жодних шаблонів та ярликів ("Заголовок:", "Суть:", "Аналіз:", "Висновок:"). Пиши одразу фінальний текст посту.
2. Структура посту:
   - Одне релевантне емодзі + **Яскравий заголовок, що передає головний інфопривід**.
   - Основна частина (1-2 короткі абзаци). Тільки "м'ясо": цифри, причини, наслідки. Пиши динамічно, без води.
   - *📌 Market Voice:* (Одне речення курсивом. Твій авторський інсайт: як ця подія вплине на ринок, ліквідність чи тренди).
   - 3-4 тематичні хештеги в кінці (наприклад, #BTC #DeFi #макро).
3. Мова: виключно грамотна українська. Жодних русизмів.
4. Якщо вхідна новина не несе цінності (вода, чутки без фактів, реклама, немає конкретики) — у відповідь видай лише одне слово: SKIP.
5. Розмітка: використовуй лише базовий Telegram Markdown (**текст** для жирного, *текст* для курсиву). КАТЕГОРИЧНО заборонено використовувати HTML-теги."""

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
            # Сохраняем ссылку, чтобы в следующий раз бот не пытался переписать этот же мусор
            save_last_posted_link(latest_link)
            return
            
        full_post = f"{post_text}\n\nДжерело: {news.link}"
        
    except Exception as e:
        print(f"❌ Ошибка ИИ: {e}")
        return

    print("⏳ Отправляем пост в Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": full_post, "parse_mode": "Markdown"}
    
    # Используем json=payload вместо data=payload
    res = requests.post(url, json=payload)
    
    if res.status_code == 200:
        print("🎉 Успех! Пост опубликован.")
        save_last_posted_link(latest_link) # Обновляем память бота только после успешной отправки
    else:
        print(f"⚠️ Ошибка Markdown: {res.text}. Пробуем отправить без разметки...")
        # Запасной план: отправка без Markdown, если ИИ ошибся в спецсимволах
        del payload["parse_mode"]
        fallback_res = requests.post(url, json=payload)
        
        if fallback_res.status_code == 200:
            print("🎉 Пост опубликован (без разметки).")
            save_last_posted_link(latest_link)
        else:
            print(f"❌ Критическая ошибка Telegram: {fallback_res.text}")

if __name__ == "__main__":
    main()
