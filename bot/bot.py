import asyncio
import logging
from logging.handlers import RotatingFileHandler
import aioschedule  # библиотека для выставления заданий по расписанию

# подключаем библиотеку для работы с API телеграм бота
from aiogram import Bot, Dispatcher, executor
from aiogram.types import MessageEntity, Message, CallbackQuery

# подключение функций из сторонних файлов
import files
from bot_panel import in_bot_panel, panel, bot_inline
from models import User, Admin, Author, BlockedUser
from defs import get_csv, get_state, set_state, do_reserve_copy_db, delete_state, get_chat_value_message, \
    delete_chat_value_message
from extensions import Settings, SUPER_ADMIN_ID, TOKEN, CHAT_MODE_PRIVATE, TOTAL_RETRIES, \
    CONNECT_RETRY, TIME_BETWEEN_ATTEMPTS, TIME_FOR_CONNECT, TIME_DATA_REC


# Create handlers
console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(files.system_log, mode='a',
                                   maxBytes=2048000, backupCount=2,
                                   encoding='utf-8', delay=True)


logging.basicConfig(
    format="%(asctime)s::[%(levelname)s]::%(name)s::(%(filename)s).%(funcName)s(%(lineno)d)::%(message)s",
    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO, handlers=(file_handler, console_handler)
)


# настройка и инициализация бота
settings = Settings()
settings.get_local_settings()
settings.get_global_settings()
settings.get_phrases()
logging.info('Settings are accepted')

bot = Bot(token=TOKEN)
logging.info('Token was set')
dp = Dispatcher(bot)


# обработчик команды start
@dp.message_handler(commands=['start'])
async def process_start_command(message: Message):
    if message.chat.type == CHAT_MODE_PRIVATE:
        user = User.get_or_none(user_id=message.chat.id)

        if user is not None or message.chat.id == SUPER_ADMIN_ID:
            await panel(settings, bot, message)
        else:
            entity_list = []
            entity = MessageEntity(type="text_link",
                                   offset=len("У вас недостаточно опыта для доступа к боту, пожалуйста, "
                                              "проявите больше активностей в сообществе "),
                                   length=len('HareCrypta'),
                                   url='https://t.me/harecrypta_chat')
            entity_list.append(entity)
            await bot.send_message(message.chat.id, "У вас недостаточно опыта для доступа к боту, пожалуйста, "
                                                    "проявите больше активностей в сообществе HareCrypta.",
                                   entities=entity_list, disable_web_page_preview=True)


# обработчик команды help
@dp.message_handler(commands=['help'])
async def process_help_command(message: Message):
    if message.chat.type == CHAT_MODE_PRIVATE:
        await bot.send_message(message.chat.id, settings.help_text)


# обработчик входных данных из сообщений
# обработка команд для панели бота
@dp.message_handler(content_types=["text"])
async def text_handler(message: Message):
    if message.chat.type == CHAT_MODE_PRIVATE:
        user = User.get_or_none(user_id=message.chat.id)

        if user is not None or message.chat.id == SUPER_ADMIN_ID:
            await in_bot_panel(bot, settings, message)
        else:
            entity_list = []
            entity = MessageEntity(type="text_link",
                                   offset=len("У вас недостаточно опыта для доступа к боту, пожалуйста, "
                                              "проявите больше активностей в сообществе "),
                                   length=len('HareCrypta'),
                                   url='https://t.me/harecrypta_chat')
            entity_list.append(entity)
            await bot.send_message(message.chat.id, "У вас недостаточно опыта для доступа к боту, пожалуйста, "
                                                    "проявите больше активностей в сообществе HareCrypta.",
                                   entities=entity_list, disable_web_page_preview=True)


# обработчик фото и документов (используется при загрузке баннеров для постов)
@dp.message_handler(content_types=["document", "photo"])
async def document_handler(message: Message):
    if message.chat.type == CHAT_MODE_PRIVATE:
        user = User.get_or_none(user_id=message.chat.id)

        if user is not None or message.chat.id == SUPER_ADMIN_ID:
            if get_state(message.chat.id) in [8, 21, 210]:
                await in_bot_panel(bot, settings, message)
        else:
            entity_list = []
            entity = MessageEntity(type="text_link",
                                   offset=len("У вас недостаточно опыта для доступа к боту, пожалуйста, "
                                              "проявите больше активностей в сообществе "),
                                   length=len('HareCrypta'),
                                   url='https://t.me/harecrypta_chat')
            entity_list.append(entity)
            await bot.send_message(message.chat.id, "У вас недостаточно опыта для доступа к боту, пожалуйста, "
                                                    "проявите больше активностей в сообществе HareCrypta.",
                                   entities=entity_list, disable_web_page_preview=True)


# обработчик коллбэков от инлайн кнопок
@dp.callback_query_handler(lambda c: True)
async def callback(callback_query: CallbackQuery):
    if callback_query.message:
        if callback_query.message.chat.type == 'private':
            user = User.get_or_none(user_id=callback_query.message.chat.id)

            if user is not None or callback_query.message.chat.id == SUPER_ADMIN_ID:
                await bot_inline(bot, callback_query, settings)

        await bot.answer_callback_query(callback_query.id)


# расписание задач
async def scheduler():
    aioschedule.every(10).minutes.do(get_csv, bot=bot, settings=settings)
    aioschedule.every(48).hours.do(do_reserve_copy_db, settings=settings)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


# функция при запуске бота
async def on_startup(_):
    asyncio.create_task(scheduler())

    await bot.send_message(SUPER_ADMIN_ID, 'Вставьте ссылку с одноразовым ключом для доступа к csv файлу.'
                                           'Получите её у Combot по команде /onetime.')
    set_state(SUPER_ADMIN_ID, 55)


# функция при выключении бота
async def on_shutdown(_):
    logging.info('Cleaning states...')
    for table in [Admin, Author, BlockedUser]:
        for obj in table.select():
            if get_state(obj.profile.user_id):
                delete_state(obj.profile.user_id)
            if get_chat_value_message(obj.profile.user_id):
                delete_chat_value_message(obj.profile.user_id)
        logging.info(f'{table.__name__} states were cleaned')

    logging.info('Bot was stopped')


# входная точка программы
if __name__ == '__main__':
    logging.info("Bot was started")
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup, on_shutdown=on_shutdown)
