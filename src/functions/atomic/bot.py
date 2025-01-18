from io import BytesIO
from typing import List
from PIL import Image  # Убедитесь, что PIL установлен с помощью `pip install pillow`
import requests
import telebot
from telebot import types
from telebot.callback_data import CallbackData
from bot_func_abc import AtomicBotFunctionABC


class AtomicDuckBotFunction(AtomicBotFunctionABC):
    """Класс для реализации функционала команды /ducks."""

    commands: List[str] = ["ducks", "duck"]
    authors: List[str] = ["IHVH"]
    about: str = "Функция с утками!"
    description: str = (
        "Этот бот отправляет случайные изображения уток по команде /ducks. "
        "Укажите количество уток, которые вы хотите увидеть, и формат для сохранения!"
    )
    state: bool = True

    def __init__(self):
        """Инициализирует бота и фабрику клавиатуры для уток."""
        self.bot = None
        self.duck_keyboard_factory = None

    def set_handlers(self, app: telebot.TeleBot):
        """Устанавливает обработчики для команд и кнопок."""
        self.bot = app
        self.duck_keyboard_factory = CallbackData('t_key_button', prefix=self.commands[0])

        @app.message_handler(commands=self.commands)
        def ducks_message_handler(message: types.Message):
            """Обработчик команды /ducks."""
            msg = "Отправьте количество уток, которое вы хотите увидеть (например, 3):"
            force_reply = types.ForceReply(selective=False)
            app.send_message(chat_id=message.chat.id, text=msg, reply_markup=force_reply)
            app.register_next_step_handler(message, self.__process_count_step)

        @app.callback_query_handler(func=None, config=self.duck_keyboard_factory.filter())
        def duck_keyboard_callback(call: types.CallbackQuery):
            """Обработчик для кнопок."""
            callback_data: dict = self.duck_keyboard_factory.parse(callback_data=call.data)
            t_key_button = callback_data.get('t_key_button', '')

            if t_key_button == 'force_reply':
                force_reply = types.ForceReply(selective=False)
                text = "Отправьте количество уток, которое вы хотите увидеть (например, 3):"
                app.send_message(call.message.chat.id, text, reply_markup=force_reply)
                app.register_next_step_handler(call.message, self.__process_count_step)
            else:
                app.answer_callback_query(call.id, "Неверная кнопка")

    def __process_count_step(self, message: types.Message):
        """Обрабатывает количество уток, введённое пользователем."""
        try:
            chat_id = message.chat.id
            txt = message.text
            if txt.isdigit():
                count = int(txt)
                if count <= 0:
                    raise ValueError("Число должно быть положительным!")
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('PNG', 'JPEG')
                msg = "Выберите формат изображения для сохранения (PNG или JPEG):"
                self.bot.send_message(chat_id, msg, reply_markup=markup)
                self.bot.register_next_step_handler(message, self.__process_format_step, count)
            else:
                self.bot.send_message(chat_id, "Введите корректное число.")
        except ValueError as ex:
            self.bot.reply_to(message, f"Ошибка: {ex}")

    def __process_format_step(self, message: types.Message, count: int):
        """Обрабатывает выбор формата изображения для сохранения."""
        try:
            chat_id = message.chat.id
            file_format = message.text.lower()

            if file_format not in ['png', 'jpeg']:
                raise ValueError("Неверный формат! Выберите PNG или JPEG.")

            duck_images = self.get_duck_images(count, file_format)

            for i, img in enumerate(duck_images):
                self.bot.send_photo(chat_id, img, caption=f"Утка {i + 1}")

            self.bot.send_message(
                chat_id, 
                f"Вот {count} уток в формате {file_format.upper()}! 🦆"
            )
        except ValueError as ex:
            self.bot.reply_to(message, f"Ошибка: {ex}")

    def get_duck_images(self, count: int = 2, file_format: str = 'png') -> List[BytesIO]:
        """Получает случайные изображения уток в указанном формате."""
        images = []
        for _ in range(count):
            url = "https://random-d.uk/api/randomimg"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img_byte_arr = BytesIO()
                img.save(img_byte_arr, format=file_format.upper())
                img_byte_arr.seek(0)
                images.append(img_byte_arr)
        return images
