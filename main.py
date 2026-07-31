import os
import logging
from pathlib import Path
import requests
from dotenv import load_dotenv

# Настройка профессионального логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из файла .env (если он есть локально)
load_dotenv()

# Конфигурация из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
STATE_FILE = Path("last_post.txt")

if not BOT_TOKEN or not CHANNEL_ID:
    logger.error("Критична помилка: Не задано BOT_TOKEN або CHANNEL_ID у змінних середовища!")
    exit(1)

def get_last_processed_id() -> str:
    """Читає ID останнього опрацьованого поста з файлу."""
    if STATE_FILE.exists():
        return STATE_FILE.read_text(encoding="utf-8").strip()
    return ""

def save_last_processed_id(post_id: str) -> None:
    """Зберігає ID останнього опрацьованого поста."""
    STATE_FILE.write_text(str(post_id), encoding="utf-8")

def send_telegram_message(text: str) -> bool:
    """Безпечне надсилання повідомлення в Telegram канал українською мовою."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Повідомлення успішно надіслано в канал.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка під час надсилання запиту в Telegram API: {e}")
        return False

def main():
    logger.info("Запуск Market Voice Bot...")
    
    last_id = get_last_processed_id()
    logger.info(f"Поточний стан (last_id): {last_id if last_id else 'Порожньо'}")
    
    # Назва каналу жирним шрифтом, слово Update повністю прибрано
    new_content_id = "sample_market_update_02"
    new_text = "📈 **Market Voice**\n\nСитуація на ринках стабільна. Дані оновлено в автоматичному режимі."

    if new_content_id != last_id:
        success = send_telegram_message(new_text)
        if success:
            save_last_processed_id(new_content_id)
    else:
        logger.info("Нових даних для публікації немає.")

if __name__ == "__main__":
    main()
