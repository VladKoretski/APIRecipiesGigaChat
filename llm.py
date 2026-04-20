import os
import base64
import uuid
import requests
import urllib3
from dotenv import load_dotenv

# Отключаем предупреждения о сертификатах (для учебного проекта)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET")

AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Получение токена
def _get_access_token() -> str | None:
    """Получает access token. Возвращает токен или None."""
    if not CLIENT_ID or not CLIENT_SECRET:
        return None

    try:
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": f"Basic {encoded}",
            "RqUID": str(uuid.uuid4())
        }
        
        data = "scope=GIGACHAT_API_PERS"
        
        # verify=False для обхода проблем с сертификатами
        response = requests.post(
            AUTH_URL, 
            headers=headers, 
            data=data, 
            timeout=10, 
            verify=False
        )
        
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
        
    except Exception:
        return None


def get_shopping_list(dish: str, people: str, format_type: str) -> str:
    """Основной обработчик. Возвращает результат или понятное сообщение об ошибке."""
    
    token = _get_access_token()
    if not token:
        return "Не настроен доступ к сервису."

    # Формируем промпт
    if format_type == "Список + шаги":
        format_instr = (
            "Сначала выведи список продуктов (по одному на строку) и количество. "
            "Затем добавь 5-8 коротких шагов приготовления и рекомендации по подаче на стол."
        )
    else:
        format_instr = "Выведи ТОЛЬКО список продуктов, каждый с новой строки. Без шагов и комментариев."

    system_prompt = (
        f"Ты помощник шеф-повара. Составь ответ для блюда: {dish}. "
        f"Рассчитай порции на {people} человек. "
        f"Требование к формату: {format_instr}"
    )

    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Сгенерируй ответ."}
        ],
        "temperature": 0.3
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(
            CHAT_URL, 
            json=payload, 
            headers=headers, 
            timeout=20,
            verify=False
        )
        
        if 400 <= response.status_code < 500:
            return "Не настроен доступ к сервису."
        if response.status_code >= 500:
            return "Сервис временно недоступен. Попробуйте позже."
            
        response.raise_for_status()
        
        data = response.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        if not text:
            return "Пустой ответ модели. Попробуйте переформулировать вопрос."
            
        return text

# Отработка ошибок
    except requests.exceptions.Timeout:
        return "Не удалось получить ответ. Попробуйте ещё раз."
    except requests.exceptions.ConnectionError:
        return "Не удалось получить ответ. Попробуйте ещё раз."
    except Exception:
        return "Не удалось получить ответ. Попробуйте ещё раз."