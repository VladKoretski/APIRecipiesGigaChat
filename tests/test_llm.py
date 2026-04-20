import pytest
from unittest.mock import patch, Mock
import sys
import os

# Добавляем корень проекта в путь, чтобы импортировать llm
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm import get_shopping_list

class TestInputValidation:
    """Тесты валидации ввода (проверяются в streamlit_app.py)"""
    
    def test_empty_dish_message(self):
        """Пустое название блюда должно возвращать понятное сообщение"""
        # Эту валидацию делаем в UI, но проверяем, что функция не падает
        result = get_shopping_list("", "2", "Список продуктов")
        # Функция попытается вызвать API, но без ключей вернёт ошибку доступа
        assert isinstance(result, str)
        assert len(result) > 0


class TestAPIErrorHandling:
    """Тесты обработки ошибок API через моки"""
    
    @patch('llm._get_access_token')
    def test_no_token_returns_config_error(self, mock_token):
        """Если токен не получен — возвращаем 'Не настроен доступ'"""
        mock_token.return_value = None
        
        result = get_shopping_list("Борщ", "2", "Список продуктов")
        
        assert result == "Не настроен доступ к сервису."
    
    @patch('llm._get_access_token')
    @patch('llm.requests.post')
    def test_4xx_error_returns_config_message(self, mock_post, mock_token):
        """4xx ошибки → 'Не настроен доступ'"""
        mock_token.return_value = "fake_token"
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        result = get_shopping_list("Борщ", "2", "Список продуктов")
        
        assert result == "Не настроен доступ к сервису."
    
    @patch('llm._get_access_token')
    @patch('llm.requests.post')
    def test_5xx_error_returns_retry_message(self, mock_post, mock_token):
        """5xx ошибки → 'Сервис временно недоступен'"""
        mock_token.return_value = "fake_token"
        
        mock_response = Mock()
        mock_response.status_code = 503
        mock_post.return_value = mock_response
        
        result = get_shopping_list("Борщ", "2", "Список продуктов")
        
        assert result == "Сервис временно недоступен. Попробуйте позже."
    
    @patch('llm._get_access_token')
    @patch('llm.requests.post')
    def test_timeout_returns_retry_message(self, mock_post, mock_token):
        """Таймаут → 'Не удалось получить ответ'"""
        mock_token.return_value = "fake_token"
        mock_post.side_effect = TimeoutError()
        
        result = get_shopping_list("Борщ", "2", "Список продуктов")
        
        assert "Не удалось получить ответ" in result
    
    @patch('llm._get_access_token')
    @patch('llm.requests.post')
    def test_empty_response_returns_rephrase_message(self, mock_post, mock_token):
        """Пустой ответ модели → 'Попробуйте переформулировать'"""
        mock_token.return_value = "fake_token"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}
        mock_post.return_value = mock_response
        
        result = get_shopping_list("Борщ", "2", "Список продуктов")
        
        assert "переформулировать" in result


class TestSuccessfulResponse:
    """Тесты успешного ответа"""
    
    @patch('llm._get_access_token')
    @patch('llm.requests.post')
    def test_returns_shopping_list(self, mock_post, mock_token):
        """Успешный ответ возвращается как есть"""
        mock_token.return_value = "fake_token"
        
        expected = "🥕 Морковь, 2 шт.\n🧅 Лук, 1 шт."
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": expected}}]
        }
        mock_post.return_value = mock_response
        
        result = get_shopping_list("Борщ", "2", "Список продуктов")
        
        assert result == expected
