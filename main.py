import os
import logging
from pathlib import Path
import requests
from dotenv import load-dotenv # type: ignore

# Загрузка переменных окружения из файла .env (если он есть локально)
load_dotenv()

# Настройка профессионального логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
STATE_FILE = Path("last_post.txt")

if not BOT_TOKEN or not CHANNEL_ID:
    logger.error("Критическая ошибка: Не заданы BOT_TOKEN или CHANNEL_ID в переменных окружения!")
    exit(1)

def get_last_processed_id() -> str:
    """Читает ID последнего обработанного поста из файла."""
    if STATE_FILE.exists():
        return STATE_FILE.read_text(encoding="utf-8").strip()
    return ""

def save_last_processed_id(post_id: str) -> None:
    """Сохраняет ID последнего обработанного поста."""
    STATE_FILE.write_text(str(post_id), encoding="utf-8")

def send_telegram_message(text: string) -> bool: # type: ignore
    """Безопасная отправка сообщения в Telegram канал."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Сообщение успешно отправлено в канал.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке запроса в Telegram API: {e}")
        return False

def main():
    logger.info("Запуск Market Voice Bot...")
    
    last_id = get_last_processed_id()
    logger.info(f"Текущее состояние (last_id): {last_id if last_id else 'Пусто'}")
    
    # Пример логики проверки данных и публикации
    # (Здесь интегрируется ваш парсер рынка / генератор контента)
    new_content_id = "sample_market_update_01"
    new_text = "📈 **Market Voice Update**\n\nСитуация на рынках стабильна. Данные обновлены в автоматическом режиме."

    if new_content_id != last_id:
        success = send_telegram_message(new_text)
        if success:
            save_last_processed_id(new_content_id)
    else:
        logger.info("Новых данных для публикации нет.")

if __name__ == "__main__":
    main()
