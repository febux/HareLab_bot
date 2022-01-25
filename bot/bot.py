import asyncio
import logging
import aioschedule  # библиотека для выставления заданий по расписанию

# подключаем библиотеку для работы с API телеграм бота
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardRemove

# подключение функций из сторонних файлов
from admin_panel import in_admin_panel, first_launch, admin_panel, admin_inline
from author_panel import author_inline, in_author_panel, author_panel
from defs import get_admin_list, get_moder_list, log, get_csv, get_state, set_state, get_author_list
from mod_panel import in_moder_panel, moder_panel, moder_inline
from extensions import Settings
from config import admin_id
import files

# set logging level
logging.basicConfig(filename=files.system_log, format='%(levelname)s:%(name)s:%(asctime)s:%(message)s',
                    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO)

# настройка и инициализация бота
settings = Settings()
bot = Bot(token=settings.token)
logging.info('Settings are accepted')
dp = Dispatcher(bot)


# обработчик команды start
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    if message.chat.type == 'private':
        if (message.chat.id == admin_id or
            message.chat.id in [message.chat.id for item in get_admin_list() if message.chat.id in item]) and \
                await first_launch(bot, message.chat.id) is False:
            await bot.send_message(message.chat.id, f"Привет, Админ {message.chat.username}!\n",
                                   reply_markup=ReplyKeyboardRemove())

            await bot.send_message(message.chat.id, "Я HareLab-бот!\n "
                                                    "При помощи меня можно создать пост для канала "
                                                    "HareCrypta - Лаборатория Идей!\n"
                                                    "По команде /help можно получить "
                                                    "дополнительную информацию")
            await admin_panel(bot, message)
            await log(f'Admin {message.chat.id} started bot')
        elif message.chat.id in [message.chat.id for item in get_moder_list() if message.chat.id in item]:
            await bot.send_message(message.chat.id, f"Привет, Модератор {message.chat.username}!")
            await bot.send_message(message.chat.id, "Я HareLab-бот!\n "
                                                    "При помощи меня можно создать пост для канала "
                                                    "HareCrypta - Лаборатория Идей!\n"
                                                    "По команде /help можно получить "
                                                    "дополнительную информацию")
            await moder_panel(bot, message)
            await log(f'Moder {message.chat.id} started bot')
        elif message.chat.id in [message.chat.id for item in get_author_list() if message.chat.id in item]:
            await bot.send_message(message.chat.id, f"Привет, Автор {message.chat.username}!")
            await bot.send_message(message.chat.id, "Я HareLab-бот!\n "
                                                    "При помощи меня можно создать пост для канала "
                                                    "HareCrypta - Лаборатория Идей!\n"
                                                    "По команде /help можно получить "
                                                    "дополнительную информацию")
            await author_panel(bot, message)
            await log(f'Author {message.chat.id} started bot')
    else:
        pass


# обработчик команды help
@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    if message.chat.type == 'private':
        await bot.send_message(message.chat.id, settings.help_text)
    else:
        pass


# обработчик входных данных из сообщений
# обработка команд для админ панели, для мод панели, для панели автора
@dp.message_handler(content_types=["text"])
async def text_handler(message: types.Message):
    if message.chat.type == 'private':
        if message.chat.id == admin_id or \
                message.chat.id in [message.chat.id for item in get_admin_list() if message.chat.id in item]:
            await in_admin_panel(bot, settings, message)
        elif message.chat.id in [message.chat.id for item in get_moder_list() if message.chat.id in item]:
            await in_moder_panel(bot, settings, message)
        elif message.chat.id in [message.chat.id for item in get_author_list() if message.chat.id in item]:
            await in_author_panel(bot, settings, message)
    else:
        pass


# обработчик фото и документов (используется при загрузке баннеров для постов)
@dp.message_handler(content_types=["document", "photo"])
async def document_handler(message: types.Message):
    if message.chat.type == 'private':
        if message.chat.id == admin_id or \
                message.chat.id in [message.chat.id for item in get_admin_list() if message.chat.id in item]:
            if get_state(message.chat.id) in [8, 21, 210]:
                await in_admin_panel(bot, settings, message)
        elif message.chat.id in [message.chat.id for item in get_moder_list() if message.chat.id in item]:
            if get_state(message.chat.id) in [8, 21, 210]:
                await in_moder_panel(bot, settings, message)
        elif message.chat.id in [message.chat.id for item in get_author_list() if message.chat.id in item]:
            if get_state(message.chat.id) in [8, 21, 210]:
                await in_author_panel(bot, settings, message)
    else:
        pass


# обработчик коллбэков от инлайн кнопок
@dp.callback_query_handler(lambda c: True)
async def callback(callback_query: types.CallbackQuery):
    if callback_query.message:
        if callback_query.message.chat.type == 'private':
            if callback_query.message.chat.id in [callback_query.message.chat.id
                                                  for item in get_admin_list()
                                                  if callback_query.message.chat.id in item]:
                await admin_inline(bot, callback_query, settings)
            elif callback_query.message.chat.id in [callback_query.message.chat.id
                                                    for item in get_moder_list()
                                                    if callback_query.message.chat.id in item]:
                await moder_inline(bot, callback_query, settings)
            elif callback_query.message.chat.id in [callback_query.message.chat.id
                                                    for item in get_author_list()
                                                    if callback_query.message.chat.id in item]:
                await author_inline(bot, callback_query, settings)

        await bot.answer_callback_query(callback_query.id)


# расписание задач
async def scheduler():
    aioschedule.every(60).minutes.do(get_csv, bot=bot, settings=settings)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


# функция при запуске бота
async def on_startup(_):
    asyncio.create_task(scheduler())

    await bot.send_message(admin_id, 'Вставьте ссылку с одноразовым ключом для доступа к csv файлу.'
                                     'Получите её у Combot по команде /onetime.')
    set_state(admin_id, 55)


# функция при отключении бота
async def on_shutdown(_):
    get_list = 0


# входная точка программы
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup, on_shutdown=on_shutdown)
