"""Module for working with a duck bot."""

from io import BytesIO
from typing import List
from PIL import Image  # Ensure PIL is installed with `pip install pillow`
import requests
import telebot
from telebot import types
from telebot.callback_data import CallbackData
from bot_func_abc import AtomicBotFunctionABC


class AtomicDuckBotFunction(AtomicBotFunctionABC):
    """Class for implementing the /ducks command functionality."""

    commands: List[str] = ["ducks", "duck"]
    authors: List[str] = ["IHVH"]
    about: str = "Duck function!"
    description: str = (
        "This bot sends random duck images upon the /ducks command. "
        "Specify the number of ducks you want to see and the format for saving!"
    )
    state: bool = True

    def __init__(self):
        """Initializes the bot and the duck keyboard factory."""
        self.bot = None
        self.duck_keyboard_factory = None

    def set_handlers(self, app: telebot.TeleBot):
        """Sets up handlers for commands and buttons."""
        self.bot = app
        self.duck_keyboard_factory = CallbackData('t_key_button', prefix=self.commands[0])

        @app.message_handler(commands=self.commands)
        def ducks_message_handler(message: types.Message):
            """Handler for the /ducks command."""
            msg = "Send the number of ducks you want to see (e.g., 3):"
            force_reply = types.ForceReply(selective=False)
            app.send_message(chat_id=message.chat.id, text=msg, reply_markup=force_reply)
            app.register_next_step_handler(message, self.__process_count_step)

        @app.callback_query_handler(func=None, config=self.duck_keyboard_factory.filter())
        def duck_keyboard_callback(call: types.CallbackQuery):
            """Handler for buttons."""
            callback_data: dict = self.duck_keyboard_factory.parse(callback_data=call.data)
            t_key_button = callback_data.get('t_key_button', '')

            if t_key_button == 'force_reply':
                force_reply = types.ForceReply(selective=False)
                text = "Send the number of ducks you want to see (e.g., 3):"
                app.send_message(call.message.chat.id, text, reply_markup=force_reply)
                app.register_next_step_handler(call.message, self.__process_count_step)
            else:
                app.answer_callback_query(call.id, "Invalid button")

    def __process_count_step(self, message: types.Message):
        """Processes the number of ducks entered by the user."""
        try:
            chat_id = message.chat.id
            txt = message.text
            if txt.isdigit():
                count = int(txt)
                if count <= 0:
                    raise ValueError("The number must be positive!")
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                markup.add('PNG', 'JPEG')
                msg = "Select the image format for saving (PNG or JPEG):"
                self.bot.send_message(chat_id, msg, reply_markup=markup)
                self.bot.register_next_step_handler(message, self.__process_format_step, count)
            else:
                self.bot.send_message(chat_id, "Enter a valid number.")
        except ValueError as ex:
            self.bot.reply_to(message, f"Error: {ex}")

    def __process_format_step(self, message: types.Message, count: int):
        """Processes the format selection for the images."""
        try:
            chat_id = message.chat.id
            file_format = message.text.lower()

            if file_format not in ['png', 'jpeg']:
                raise ValueError("Invalid format! Choose PNG or JPEG.")

            duck_images = self.get_duck_images(count, file_format)

            for i, img in enumerate(duck_images):
                self.bot.send_photo(chat_id, img, caption=f"Duck {i + 1}")

            self.bot.send_message(chat_id, f"Here are {count} ducks in {file_format.upper()} format! 🦆")
        except ValueError as ex:
            self.bot.reply_to(message, f"Error: {ex}")

    def get_duck_images(self, count: int = 2, file_format: str = 'png') -> List[BytesIO]:
        """Fetches random duck images in the specified format."""
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
