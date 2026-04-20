import streamlit as st
from llm import get_shopping_list

st.set_page_config(page_title="Список покупок по блюду", page_icon="🛒")
st.title("🛒 Список покупок по блюду")

# 1. Поля ввода
dish = st.text_area("Что приготовить?", placeholder="Например: Борщ украинский")
people = st.selectbox("На сколько человек?", ["1", "2", "4", "6"])
format_type = st.selectbox("Формат ответа", ["Список продуктов", "Список + шаги"])

# 2. Валидация ввода ДО вызова API
input_error = None
if not dish.strip():
    input_error = "Напишите, что хотите приготовить."
elif len(dish.strip()) > 200:
    input_error = "Слишком длинный текст — сократите или разбейте на части."

# 3. Кнопка и вывод
if st.button("Сгенерировать список покупок", use_container_width=True):
    if input_error:
        st.warning(input_error)
    else:
        with st.spinner("Генерируем список..."):
            result = get_shopping_list(dish, people, format_type)
            
        # Проверяем, является ли результат ошибкой (по ключевым словам)
        error_keywords = ["не настроен", "временно недоступен", "не удалось", "пустой ответ"]
        is_error = any(keyword in result.lower() for keyword in error_keywords)
        
        if is_error:
            st.error(result)
        else:
            st.success("✅ Готово!")
            st.markdown(result.replace("\n", "  \n")) # Сохраняем переносы строк