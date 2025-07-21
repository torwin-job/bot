import os
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes, CallbackQueryHandler
from services.service_logic import format_description, get_all_services, get_service_by_id
from applications.service_logic import create_application
import logging

load_dotenv()

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

AWAIT_START, CHOOSING_SERVICE, ENTER_NAME, ENTER_PHONE = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Вызвана команда /start")
    logger.debug(f"Update: {update}")
    keyboard = [["Услуги"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Это твой личный ассистент.\n"
        "Я помогу тебе выбрать услугу и передам заявку\n"
        "нашей команде.\n"
        "Нажми «Услуги», чтобы посмотреть, что мы предлагаем или выбери действие из меню ниже.",
        reply_markup=reply_markup
    )
    return AWAIT_START

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Пользователь запросил список услуг")
    services = await get_all_services()
    for service in services:
        desc = format_description(service.description)
        text = f"💼 <b>{service.name}</b>\n{desc}"
        await update.message.reply_text(text, parse_mode="HTML")
    keyboard = [
        [InlineKeyboardButton(service.name, callback_data=f"service_{service.id}")]
        for service in services
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите услугу из списка ниже:",
        reply_markup=reply_markup
    )
    return CHOOSING_SERVICE

async def service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service_id = int(query.data.replace("service_", ""))
    service = await get_service_by_id(service_id)
    desc = format_description(service.description)
    logger.info(f"Пользователь выбрал услугу: {service.name}")
    await query.edit_message_text(
        f"💼 <b>{service.name}</b>\n{desc}\n\n<b>Пожалуйста, введите ваше имя:</b>",
        parse_mode="HTML"
    )
    context.user_data['service'] = service.name
    context.user_data['service_obj'] = service
    return ENTER_NAME

async def already_applied(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data and context.user_data.get('application_created'):
        await update.message.reply_text("Вы не можете создать больше одной заявки")
        return ConversationHandler.END
    return

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    logger.info(f"Пользователь ввёл имя: {context.user_data['name']}")
    await update.message.reply_text("Введите ваш телефон:")
    return ENTER_PHONE

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    if not phone.isdigit() or len(phone) < 5:
        await update.message.reply_text("Пожалуйста, введите номер телефона, используя только цифры (минимум 5).")
        return ENTER_PHONE
    context.user_data['phone'] = phone
    logger.info(f"Пользователь ввёл телефон: {context.user_data['phone']}")
    try:
        service = context.user_data['service_obj']
        await create_application(
            name=context.user_data['name'],
            phone=context.user_data['phone'],
            service=service
        )
        logger.info(f"Заявка создана: имя={context.user_data['name']}, телефон={context.user_data['phone']}, услуга={service.name}")
        context.user_data['application_created'] = True
        await update.message.reply_text("Спасибо! Ваша заявка принята.")
    except Exception as e:
        logger.error(f"Ошибка при создании заявки: {e}")
        await update.message.reply_text("Ошибка: выбранная услуга не найдена.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Пользователь отменил заявку")
    await update.message.reply_text("Заявка отменена.")
    return ConversationHandler.END

class Command(BaseCommand):
    help = 'Запуск Telegram-бота'

    def handle(self, *args, **options):
        TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
        logger.info(f"Используемый токен: {TOKEN}")
        if not TOKEN:
            logger.error('TELEGRAM_BOT_TOKEN не найден в переменных окружения!')
            raise RuntimeError('TELEGRAM_BOT_TOKEN не найден в переменных окружения!')
        application = ApplicationBuilder().token(TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                AWAIT_START: [
                    MessageHandler(filters.Regex(r'(?i)^\s*услуги\s*$'), show_services),
                    MessageHandler(filters.ALL, already_applied)
                ],
                CHOOSING_SERVICE: [CallbackQueryHandler(service_callback)],
                ENTER_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)
                ],
                ENTER_PHONE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)
                ],
            },
            fallbacks=[CommandHandler('start', start), CommandHandler('cancel', cancel)],
            # per_message=True,  # Удалено для корректной работы
        )

        application.add_handler(conv_handler)
        application.add_handler(MessageHandler(filters.ALL, already_applied))
        logger.info("Бот запущен и ожидает команды.")
        application.run_polling()
