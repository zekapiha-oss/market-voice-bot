import os
import time
import requests
import feedparser
from groq import Groq

# 1. Получаем ключи из окружения
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# СТИЛЬ ВАРИАНТА 1
SYSTEM_PROMPT = """Ти — досвідчений фінансовий аналітик та автор Telegram-каналу Market Voice. Твоя мета — перетворювати сирі новини на стислі, інсайдерські та живі пости для криптоінвесторів.

ПРАВИЛА ФОРМАТУВАННЯ ТА СТИЛЮ (СУВОРО):
1. Жодних шаблонів та ярликів ("Заголовок:", "Суть:", "Аналіз:", "Висновок:"). Пиши одразу фінальний текст посту.
2. Структура посту:
   - Одне релевантне емодзі + Звичайний текст заголовка (БЕЗ жирного шрифту markdown). Приклад: 📊 Крипторинок сьогодні: головні події
   - Основна частина (1-2 короткі абзаци). Тільки цифри, причини, наслідки без води.
   - 📌 Market Voice: (Твій авторський інсайт одним рядком, без курсиву на назві мітки).
   - БЕЗ хештегів в кінці тексту.
3. Мова: виключно грамотна українська. Жодних русизмів.
4. Якщо вхідна новина не несе цінності (вода, чутки без фактів, реклама, немає конкретики) — у відповідь видай лише одно слово: SKIP.
5. Мінімум зайвої розмітки. Не використовуй HTML-теги."""

LAST_POST_FILE = "last_post.txt"

RSS_URLS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptoslate.com/feed/"
]

def get_last_posted_link():
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_posted_link(link):
    with open(LAST_POST_FILE, "w") as f:
        f.write(link)

def main():
    print("⏳ Бот запущен и проверяет новостные источники...")
    
    if not GROQ_API_KEY or not BOT_TOKEN:
        print("❌ Ошибка: Ключи не найдены в настройках!")
        return

    all_entries = []
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                all_entries.extend(feed.entries)
        except Exception as e:
            print(f"⚠️ Не удалось прочитать ленту {url}: {e}")

    if not all_entries:
        print("❌ Ошибка: Не удалось получить новости ни из одного источника.")
        return
    
    # Сортируем от самых новых к самым старым (как обычно отдают RSS)
    try:
        all_entries.sort(key=lambda x: x.get('published_parsed', (0,)), reverse=True)
    except Exception:
        pass

    last_link = get_last_posted_link()
    new_entries = []

    if last_link is None:
        # Если запуск первый, берем только самую свежую новость, чтобы не спамить архивом
        new_entries = [all_entries[0]]
    else:
        # Ищем, где в текущем списке находится последняя опубликованная ссылка
        indices = [i for i, entry in enumerate(all_entries) if entry.link == last_link]
        if indices:
            idx = indices[0]
            # Все элементы выше этого индекса — более новые. 
            # Берем их и переворачиваем, чтобы публиковать в хронологическом порядке (от старых к новым)
            new_entries = all_entries[0:idx][::-1]
        else:
            # Если ссылок накопилось слишком много и последняя ушла из RSS-ленты, берем самую свежую
            new_entries = [all_entries[0]]

    if not new_entries:
        print("⏭️ Новых новостей нет. Все актуально.")
        return

    print(f"✅ Найдено новых новостей для обработки: {len(new_entries)}")
    client = Groq(api_key=GROQ_API_KEY)
    url_tg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    # Обрабатываем каждую новую новость по очереди
    for news in new_entries:
        print(f"⏳ Обрабатываем: {news.title}")
        raw_text = f"Заголовок: {news.title}\nТекст: {getattr(news, 'summary', '')}"
        
        try:
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
                print("⏭️ ИИ решил пропустить эту новость (вода/нет конкретики).")
                save_last_posted_link(news.link)
                continue
                
            full_post = f"{post_text}\n\nДжерело: {news.link}"
            
        except Exception as e:
            print(f"❌ Ошибка ИИ для новости: {e}")
            continue

        # Отправка в Telegram
        payload = {"chat_id": CHANNEL_ID, "text": full_post}
        res = requests.post(url_tg, json=payload)
        
        if res.status_code == 200:
            print("🎉 Успех! Новость опубликована.")
            save_last_posted_link(news.link)
        else:
            print(f"❌ Ошибка Telegram: {res.text}")
        
        # Пауза в 3 секунды между постами, чтобы Telegram не заблокировал за флуд
        time.sleep(3)

if __name__ == "__main__":
    main()
