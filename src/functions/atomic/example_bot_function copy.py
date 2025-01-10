from abc import ABC, abstractmethod
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import requests
import random

class AtomicBotFunctionABC(ABC):
    """
    Абстрактный класс для реализации функций бота. Каждая функция будет представлять собой
    конкретную задачу, которую можно переопределить в разных ботовых приложениях.
    """

    @abstractmethod
    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

    @abstractmethod
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass


class DuckBotFunction(AtomicBotFunctionABC):
    """
    Реализация функции выбора утки для бота.
    """

    def get_duck_images(self, count=2):
        """
        Получает случайные изображения уток через API.
        """
        images = []
        for _ in range(count):
            url = f"https://random-d.uk/api/randomimg?t={random.randint(1, 10000)}"
            response = requests.get(url)
            if response.status_code == 200:
                images.append(response.content)  # Сохраняем изображение
        return images

    async def execute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Выполняет отправку изображений уток и предлагает пользователю выбрать одну.
        """
        duck_images = self.get_duck_images(2)
        context.user_data["duck_images"] = duck_images

        # Создаём inline-кнопки для выбора утки
        keyboard = [
            [InlineKeyboardButton("Утка 1", callback_data="0")],
            [InlineKeyboardButton("Утка 2", callback_data="1")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем изображения и текстовое сообщение
        for i, img in enumerate(duck_images):
            await update.message.reply_photo(photo=img, caption=f"Утка {i + 1}")

        await update.message.reply_text("Выберите утку 🦆:", reply_markup=reply_markup)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обрабатывает выбор утки пользователем.
        """
        query = update.callback_query
        await query.answer()

        choice = int(query.data)
        chosen_duck = context.user_data["duck_images"][choice]

        # Отправляем выбранную утку
        await query.message.reply_photo(photo=chosen_duck, caption="Вы выбрали эту утку 🦆!")