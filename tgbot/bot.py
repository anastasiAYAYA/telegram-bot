import logging
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Update
from telegram.keyboard import ReplyKeyboardMarkup  # Правильный импорт
from django.contrib.auth.models import User
from sections.models import Section, Enrollment

logging.basicConfig(level=logging.INFO)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать! Используйте команды:\n"
                                    "/register - зарегистрироваться\n"
                                    "/sections - список секций\n"
                                    "/enroll - записаться на секцию")

# Команда /register
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if User.objects.filter(username=user.username).exists():
        await update.message.reply_text("Вы уже зарегистрированы.")
    else:
        User.objects.create_user(username=user.username, password="telegram")
        await update.message.reply_text("Вы успешно зарегистрированы!")

# Команда /sections
async def sections(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sections = Section.objects.all()
    if sections:
        response = "\n".join([f"{section.id}. {section.name}" for section in sections])
    else:
        response = "Секции пока не добавлены."
    await update.message.reply_text(response)

# Инициализация бота
if __name__ == "__main__":
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("sections", sections))
    app.run_polling()
