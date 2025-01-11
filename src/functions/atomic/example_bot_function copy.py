import random
import logging
from typing import List
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import ReplyKeyboardMarkup
from io import BytesIO
from PIL import Image
from bot_func_abc import AtomicBotFunctionABC


class AtomicDuckBotFunction(AtomicBotFunctionABC):
    """Функция Telegram-бота для работы с утками"""
    
    commands: List[str] = ["ducks", "save"]
    authors: List[str] = ["User"]
    about: str = "Получение и сохранение случайных изображений уток."
    description: str = """Функция предоставляет возможность получить случайные изображения уток 
                          и сохранить их в выбранном формате (jpeg, png, gif и др.)."""

    bot: ApplicationBuilder
    duck_keyboard_factory: CallbackData

    def set_handlers(self, app: ApplicationBuilder):
        self.bot = app
        self.duck_keyboard_factory = CallbackData('action', prefix=self.commands[0])

        app.add_handler(CommandHandler("start", self.start_handler))
        app.add_handler(CommandHandler("ducks", self.ducks_handler))
        app.add_handler(CommandHandler("save", self.save_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Ducks")
        await update.message.reply_text(
            "Привет! Я бот с утками 🦆. Нажми 'Ducks', чтобы получить картинки уток!",
            reply_markup=keyboard
        )

    async def ducks_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /ducks"""
        await update.message.reply_text("Сколько уток вы хотите увидеть? Введите число (например, 3):")
        context.user_data['awaiting_duck_count'] = True

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений для получения уток"""
        if context.user_data.get('awaiting_duck_count', False):
            try:
                count = int(update.message.text)
                if count <= 0:
                    raise ValueError("Число должно быть положительным.")

                duck_images = self.get_duck_images(count)
                context.user_data['duck_images'] = duck_images

                await update.message.reply_text(f"Вот {count} уток! 🦆")
                for i, img in enumerate(duck_images):
                    await update.message.reply_photo(photo=img, caption=f"Утка {i + 1}")

                context.user_data['awaiting_duck_count'] = False
            except ValueError:
                await update.message.reply_text("Пожалуйста, введите корректное число.")
        elif update.message.text.lower() == "ducks":
            await self.ducks_handler(update, context)

    async def save_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /save"""
        if 'duck_images' in context.user_data and context.user_data['duck_images']:
            # Выбираем первое изображение из списка
            duck_image = context.user_data['duck_images'][0]
            await update.message.reply_text("Введите формат для сохранения изображения (например, jpeg, png, gif):")
            context.user_data['awaiting_format'] = duck_image
        else:
            await update.message.reply_text("Сначала получите утку командой 'Ducks'.")

    async def handle_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка формата и отправка файла на скачивание"""
        duck_image = context.user_data.get('awaiting_format')
        if duck_image:
            format = update.message.text.strip().lower()
            try:
                # Сохраняем изображение в выбранном формате
                output = self.save_image(duck_image, format)
                filename = f"duck.{format}"

                # Отправляем файл пользователю
                await update.message.reply_document(document=output, filename=filename)

                # Убираем ожидание формата после отправки
                context.user_data['awaiting_format'] = None
            except Exception as e:
                await update.message.reply_text(
                    f"Ошибка: невозможно сохранить в формате '{format}'. Попробуйте другой формат (jpeg, png, gif).")
        else:
            await update.message.reply_text("Нет изображения для сохранения. Сначала получите утку командой 'Ducks'.")

    def get_duck_images(self, count=2):
        """Функция для получения случайных изображений уток"""
        images = []
        for _ in range(count):
            url = f"https://random-d.uk/api/randomimg?t={random.randint(1, 10000)}"
            response = requests.get(url)
            if response.status_code == 200:
                images.append(response.content)
        return images

    def save_image(self, image_bytes, format):
        """Сохранение изображения в заданном формате"""
        img = Image.open(BytesIO(image_bytes))
        output = BytesIO()
        img.save(output, format=format.upper())
        output.seek(0)
        return output


# Основная функция для запуска бота
def main():
    TOKEN = "YOUR_BOT_TOKEN"  # Замените на токен вашего бота
    app = ApplicationBuilder().token(TOKEN).build()

    bot_function = AtomicDuckBotFunction()
    bot_function.set_handlers(app)

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()