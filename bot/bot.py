import asyncio
import logging
import aioschedule  # библиотека для выставления заданий по расписанию

# подключаем библиотеку для работы с API телеграм бота
from aiogram import Bot, Dispatcher, executor
from aiogram.types import MessageEntity, Message, CallbackQuery

# подключение функций из сторонних файлов
from bot_panel import in_bot_panel, first_launch, panel, bot_inline
from models import User
from defs import get_csv, get_state, set_state, do_reserve_copy_db
from extensions import Settings
from config import admin_id
import files

# set logging level
logging.basicConfig(filename=files.system_log, format='%(levelname)s:%(name)s:%(asctime)s:%(message)s',
                    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO)

# настройка и инициализация бота
settings = Settings()
settings.get_local_settings()
settings.get_global_settings()
settings.get_phrases()

bot = Bot(token=settings.token)
logging.info('Settings are accepted')
dp = Dispatcher(bot)


# обработчик команды start
@dp.message_handler(commands=['start'])
async def process_start_command(message: Message):
    if message.chat.type == 'private':
        user = User.get_or_none(user_id=message.chat.id)

        if user is not None or message.chat.id == admin_id:
            if await first_launch() is False:
                await panel(bot, message)
            else:
                await panel(bot, message, first__launch=True)
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
    else:
        pass


# обработчик команды help
@dp.message_handler(commands=['help'])
async def process_help_command(message: Message):
    if message.chat.type == 'private':
        await bot.send_message(message.chat.id, settings.help_text)
    else:
        pass


# обработчик входных данных из сообщений
# обработка команд для панели бота
@dp.message_handler(content_types=["text"])
async def text_handler(message: Message):
    if message.chat.type == 'private':
        user = User.get_or_none(user_id=message.chat.id)

        if user is not None or message.chat.id == admin_id:
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
    else:
        pass


# обработчик фото и документов (используется при загрузке баннеров для постов)
@dp.message_handler(content_types=["document", "photo"])
async def document_handler(message: Message):
    if message.chat.type == 'private':
        user = User.get_or_none(user_id=message.chat.id)

        if user is not None or message.chat.id == admin_id:
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
    else:
        pass


# обработчик коллбэков от инлайн кнопок
@dp.callback_query_handler(lambda c: True)
async def callback(callback_query: CallbackQuery):
    if callback_query.message:
        if callback_query.message.chat.type == 'private':
            user = User.get_or_none(user_id=callback_query.message.chat.id)

            if user is not None or callback_query.message.chat.id == admin_id:
                await bot_inline(bot, callback_query, settings)

        await bot.answer_callback_query(callback_query.id)


# расписание задач
async def scheduler():
    aioschedule.every(5).minutes.do(get_csv, settings=settings)
    aioschedule.every(48).hours.do(do_reserve_copy_db)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


# функция при запуске бота
async def on_startup(_):
    asyncio.create_task(scheduler())

    await bot.send_message(admin_id, 'Вставьте ссылку с одноразовым ключом для доступа к csv файлу.'
                                     'Получите её у Combot по команде /onetime.')
    set_state(admin_id, 55)


# входная точка программы
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
