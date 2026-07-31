import os
import json
import time
import logging
import requests
import feedparser
from groq import Groq

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 1. Получаем ключи из окружения
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# СТИЛЬ С ХЕШТЕГАМИ И HTML-ФОРМАТИРОВАНИЕМ
SYSTEM_PROMPT = """Ти — досвідчений фінансовий аналітик та автор Telegram-каналу Market Voice. Твоя мета — перетворювати сирі новини на стислі, інсайдерські та живі пости для криптоінвесторів.
ПРАВИЛА ФОРМАТУВАННЯ ТА СТИЛЮ (СУВОРО):
Жодних шаблонів та ярликів ("Заголовок:", "Суть:", "Аналіз:", "Висновок:"). Пиши одразу фінальний текст посту.
Структура посту та правила форматування (використовуй ТІЛЬКИ HTML-теги):
Заголовок: Одне релевантне емодзі + звичайний текст (без тегів). Приклад: 📊 Крипторинок сьогодні: головні події
Основна частина (1-2 короткі абзаци).
Обов'язково виділяй <b>жирним</b> ключові цифри, відсотки, суми та найважливіші показники (наприклад: <b>майже подвоїлася</b>, <b>у 4-5 разів</b>).
Виділяй ключові терміни чи сутності <u>підкресленим</u> (за допомогою тегу <u>термін</u>), якщо хочеш привернути до них увагу.
📌 Market Voice: (Твій авторський інсайт одним рядком). Сам текст інсайту бери в <i>курсив</i> (тег <i>текст</i>).
Хештеги: В самому кінці тексту обов'язково додай 3-4 актуальні тематичні хештеги через пробіл (наприклад: #BTC #DeFi #макро).
Мова: виключно грамотна українська. Жодних русизмів.
Якщо вхідна новина не несе цінності (вода, чутки без фактів, реклама, немає конкретики) — у відповідь видай лише одне слово: SKIP.
Заборонено використовувати Markdown-розмітку (**, *, _). Тільки HTML: <b>, <i>, <u>."""

# Файл для хранения истории (защита от дублей и потери данных)
HISTORY_FILE = "history.json"
MAX_HISTORY = 20

# Список RSS-источников
RSS_URLS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptoslate.com/feed/"
]

def get_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_history(history):
    history = history[-MAX_HISTORY:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def main():
    logging.info("⏳ Бот запущен и проверяет новостные источники...")
    
    if not GROQ_API_KEY or not BOT_TOKEN:
        logging.error("❌ Ошибка: Ключи не найдены в настройках!")
        return

    all_entries = []
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                all_entries.extend(feed.entries)
        except Exception as e:
            logging.warning(f"⚠️ Не удалось прочитать ленту {url}: {e}")

    if not all_entries:
        logging.error("❌ Ошибка: Не удалось получить новости ни из одного источника.")
        return

    try:
        all_entries.sort(key=lambda x: x.get('published_parsed', (0,)), reverse=True)
    except Exception:
        pass

    history = get_history()
    new_entries = [e for e in all_entries if e.link not in history]

    if not new_entries:
        logging.info("⏭️ Новых новостей нет. Все актуально.")
        return

    logging.info(f"✅ Найдено новых новостей для обработки: {len(new_entries)}")
    
    client = Groq(api_key=GROQ_API_KEY)
    url_tg = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for news in new_entries:
        logging.info(f"⏳ Обрабатываем: {news.title}")
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
                logging.info("⏭️ ИИ решил пропустить эту новость.")
                history.append(news.link)
                continue
                
            full_post = f"{post_text}\n\nДжерело: {news.link}"
        except Exception as e:
            logging.error(f"❌ Ошибка ИИ для новости: {e}")
            continue

        payload = {"chat_id": CHANNEL_ID, "text": full_post, "parse_mode": "HTML"}
        try:
            res = requests.post(url_tg, json=payload, timeout=10)
            if res.status_code == 200:
                logging.info("🎉 Успех! Новость опубликована.")
                history.append(news.link)
            else:
                logging.error(f"❌ Ошибка Telegram: {res.text}")
        except Exception as e:
            logging.error(f"❌ Ошибка сети Telegram: {e}")

        time.sleep(3)

    save_history(history)

if __name__ == "__main__":
    main()
