# IDEA: сделать также изменение фразы для команды /start
import shelve
import sqlite3
import requests
import logging
from aiogram.utils.json import json

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
import validators

import files
from config import admin_id
from defs import get_admin_list, log, new_admin, get_state, del_id, get_moder_list, new_moder, \
    get_author_list, new_author, get_csv, delete_state, set_state, preview, edit_post, change_settings, \
    set_chat_value_message, delete_chat_value_message, get_chat_value_message

# set logging level
logging.basicConfig(filename=files.system_log, format='%(levelname)s:%(name)s:%(asctime)s:%(message)s',
                    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO)

main_menu = '🏠 Главное меню'


async def first_launch(bot, chat_id):
    try:
        with open(files.working_log, encoding='utf-8') as f:
            return False
    except:
        await admin_panel(bot, chat_id, first__launch=True)
        return True


async def admin_panel(bot, message, first__launch=False):
    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    user_markup.row('Посты')
    user_markup.row('Списки')
    user_markup.row('Настройки бота')
    if first__launch:
        await bot.send_message(message.chat.id, "Добро пожаловать в админ панель. Это первый запуск бота.",
                               reply_markup=user_markup)
        await log(f'First launch admin panel of bot by admin {message.chat.id}')
    else:
        await bot.send_message(message.chat.id, "Добро пожаловать в админ панель.", reply_markup=user_markup)

        await log(f'Launch admin panel of bot by admin {message.chat.id}')


async def in_admin_panel(bot, settings, message):
    """
    Функция состоит из двух частей: в первой части обработка текстовых команд,
    во второй - обработка состояний переписки.
    Вначале работы бота требуется вставить одноразовый ключ от Combot.
    Состояние 55 отвечает за обработку этого ключа.

    При добавлении поста учитываются состояния 1, 2, 3, 4, 5, 6, 7, 8, 9, 10:
    1 - ввод темы поста,
    2 - ввод описания,
    3 - ввод даты или дедлайна,
    4 - ввод требований для участия,
    5 - ввод сайта проекта,
    6 - ввод твиттера проекта,
    7 - ввод дискорда проекта,
    8 - вставка баннера,
    9 - ввод хэштегов,
    10 - подтверждение создания поста

    При размещение постов учитываются состояния 90:
    90 - вывод неразмещённых постов

    При удалении поста - состояние 11:
    11 - выбор поста для удаления

    При редактировании поста - состояния 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22
    (120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220 состояния
    соответственно для редактирования поста перед размещением):
    12 - выбор поста для редактирования из существующих,
    13 - состояние изменения поста,
    14 - изменение темы поста,
    15 - изменение описания поста,
    16 - изменение даты поста,
    17 - изменение требований к участию,
    18 - изменение сайта проекта,
    19 - изменение твиттера проекта,
    20 - изменение дискорда проекта,
    21 - изменение баннера,
    22 - изменение хэштегов

    При работе со списком авторов - состояния 31, 32:
    31 - добавление нового автора,
        где нужно вставить пересланное от пользователя сообщение (может сделать только один из админов )
    32 - удаление автора из списка (может сделать только один из админов)

    При работе со списком админов - состояния 41, 42:
    41 - добавление нового админа,
        где нужно вставить пересланное от пользователя сообщение (может сделать только один из админов)
    42 - удаление админа из списка (может сделать только один из админов)

    При работе со списком модераторов - состояния 51, 52:
    51 - добавление нового модератора,
        где нужно вставить пересланное от пользователя сообщение (может сделать только один из админов)
    52 - удаление модератора из списка (может сделать только один из админов)

    При настройке бота - состояние 61, 62:
    61 - изменений выводной фразы по команде /help
    62 - изменение нижней подписи к постам
    63 - изменение порога опыта для авторов


    :param bot: Bot from aiogram
    :param settings: object class: Settings from hare_bot.py
    :param message: types.Message from aiogram
    :return: None
    """

    if message.chat.id in [message.chat.id for item in get_admin_list() if message.chat.id in item] or \
            message.chat.id == admin_id:
        if get_state(message.chat.id) == 55:
            if 'https://combot.org/api/one_time_auth?hash=' in message.text and message.chat.id == admin_id:
                settings.url_one_time_link = message.text
                settings.session = requests.Session()
                settings.session.get(settings.url_one_time_link)
                logging.info('Session was opened')

                delete_state(message.chat.id)

                if await get_csv(bot, settings):
                    await bot.send_message(admin_id, 'Спасибо, данные были обновлены.')
            else:
                await bot.send_message(admin_id, 'Сначала введите ссылку для получения доступа к csv файлу.')

        elif message.text == main_menu:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id):
                delete_state(message.chat.id)
            if get_chat_value_message(message):
                delete_chat_value_message(message)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row('Посты')
            user_markup.row('Списки')
            user_markup.row('Настройки бота')

            await bot.send_message(message.chat.id, 'Вы в главном меню бота.',
                                   reply_markup=user_markup)

        elif message.text == 'Посты':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row('Добавить новый пост', 'Удалить пост')
            user_markup.row('Редактирование постов', 'Размещение постов')
            user_markup.row(main_menu)

            entity_list = []
            count_string_track = len('Созданные посты:\n\n')
            posts = 'Созданные посты:\n\n'
            a = 0
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()

            try:
                cursor.execute("SELECT author_name, post_name, "
                               "name_entities, status FROM posts;")
            except Exception as e:
                logging.critical(e)
            else:
                for author_name, post_name, name_entities, status in cursor.fetchall():
                    a += 1
                    count_string_track += len(str(a)) + 2
                    name_entities = json.loads(str(name_entities))

                    if "entities" in name_entities:

                        for entity in name_entities["entities"]:
                            entity_values_list = list(entity.values())

                            if entity["type"] == "text_link":
                                entity = MessageEntity(type=entity_values_list[0],
                                                       offset=count_string_track + entity_values_list[1],
                                                       length=entity_values_list[2], url=entity_values_list[3])
                                entity_list.append(entity)
                            elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                                    "email", "phone_number", "bold", "italic", "underline",
                                                    "strikethrough", "code"]:
                                entity = MessageEntity(type=entity_values_list[0],
                                                       offset=count_string_track + entity_values_list[1],
                                                       length=entity_values_list[2])
                                entity_list.append(entity)

                    count_string_track += len(post_name) + 3

                    count_string_track += len(author_name) + 3 + len('Posted' if status else 'Not posted') + 1

                    posts += str(a) + '. ' + str(post_name) + ' - ' + str(author_name) + \
                             ' - ' + str('Posted' if status else 'Not posted') + '\n'

                    if a % 10 == 0:
                        await bot.send_message(message.chat.id, posts, reply_markup=user_markup, entities=entity_list)
                        entity_list = []
                        count_string_track = len('Созданные посты:\n\n')
                        posts = 'Созданные посты:\n\n'

                con.close()

            if a == 0:
                posts = "Посты не созданы!"
            else:
                pass

            await bot.send_message(message.chat.id, posts, reply_markup=user_markup, entities=entity_list)

        elif message.text == 'Добавить новый пост':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(main_menu)

            with open(files.example_text, encoding='utf-8') as example_text:
                example_text = example_text.read()

            example_entities = []
            raw_entities = [{"type": "bold", "offset": 0, "length": 46},
                            {"type": "underline", "offset": 0, "length": 46},
                            {"type": "code", "offset": 46, "length": 27},
                            {"type": "bold", "offset": 73, "length": 23},
                            {"type": "pre", "offset": 96, "length": 31},
                            {"type": "text_link", "offset": 127, "length": 10,
                             "url": "https://t.me/harecrypta"},
                            {"type": "text_link", "offset": 236, "length": 3,
                             "url": "https://t.me/harecrypta_chat"},
                            {"type": "pre", "offset": 492, "length": 36},
                            {"type": "italic", "offset": 528, "length": 1},
                            {"type": "text_link", "offset": 598, "length": 5,
                             "url": "https://t.me/harecrypta"},
                            {"type": "text_link", "offset": 635, "length": 4,
                             "url": "https://t.me/harecrypta_chat"},
                            {"type": "text_link", "offset": 669, "length": 16,
                             "url": "https://t.me/HareCrypta_lab_ann"},
                            {"type": "text_link", "offset": 719, "length": 9,
                             "url": "https://www.youtube.com/c/Harecrypta"},
                            {"type": "pre", "offset": 728, "length": 35},
                            {"type": "italic", "offset": 763, "length": 2},
                            {"type": "pre", "offset": 783, "length": 25},
                            {"type": "text_link", "offset": 808, "length": 15,
                             "url": "http://www.google.com/"},
                            {"type": "text_link", "offset": 826, "length": 7,
                             "url": "http://twitter.com/"},
                            {"type": "text_link", "offset": 836, "length": 7,
                             "url": "http://discord.com/"},
                            {"type": "pre", "offset": 845, "length": 24},
                            {"type": "hashtag", "offset": 869, "length": 11},
                            {"type": "hashtag", "offset": 881, "length": 10},
                            {"type": "hashtag", "offset": 892, "length": 7},
                            {"type": "italic", "offset": 901, "length": 22},
                            {"type": "code", "offset": 924, "length": 13},
                            {"type": "bold", "offset": 937, "length": 10},
                            {"type": "text_link", "offset": 950, "length": 5,
                             "url": "https://t.me/harecrypta"},
                            {"type": "text_link", "offset": 958, "length": 3,
                             "url": "https://t.me/harecrypta_chat"},
                            {"type": "text_link", "offset": 964, "length": 7,
                             "url": "https://www.youtube.com/c/Harecrypta"},
                            {"type": "text_link", "offset": 974, "length": 9,
                             "url": "https://instagram.com/harecrypta"}]

            for entity in raw_entities:
                if entity["type"] == "text_link":
                    entity = MessageEntity(type=entity["type"],
                                           offset=entity["offset"],
                                           length=entity["length"], url=entity["url"])
                    example_entities.append(entity)
                elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                        "email", "phone_number", "bold", "italic", "underline",
                                        "strikethrough", "code"]:
                    entity = MessageEntity(type=entity["type"],
                                           offset=entity["offset"],
                                           length=entity["length"])
                    example_entities.append(entity)

            photo = open(files.photo_example, 'rb')
            await bot.send_photo(message.chat.id, photo, caption=example_text, caption_entities=example_entities)

            await bot.send_message(message.chat.id, 'Введите тему поста', reply_markup=user_markup)
            set_state(message.chat.id, 1)

        elif message.text == 'Размещение постов':
            await bot.delete_message(message.chat.id, message.message_id)
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT post_name, status FROM posts;")
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            a = 0
            for post_name, status in cursor.fetchall():
                if status:
                    pass
                else:
                    a += 1
                    user_markup.row(str(post_name))
            if a == 0:
                await bot.send_message(message.chat.id, 'Не размещенных постов нет!', reply_markup=user_markup)
            else:
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Какой пост хотите разместить?',
                                       parse_mode='Markdown', reply_markup=user_markup)
                set_state(message.chat.id, 90)
            con.close()

        elif message.text == 'Редактирование постов':
            await bot.delete_message(message.chat.id, message.message_id)
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT author_name, post_name, post_date FROM posts;")
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            a = 0
            for author_name, post_name, post_date in cursor.fetchall():
                a += 1
                user_markup.row(str(post_name))
            if a == 0:
                await bot.send_message(message.chat.id, 'Никаких постов ещё не создано!', reply_markup=user_markup)
            else:
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Какой пост хотите редактировать?',
                                       parse_mode='Markdown', reply_markup=user_markup)
                set_state(message.chat.id, 12)
            con.close()

        elif message.text == 'Назад':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [14, 15, 16, 17, 18, 19, 20, 21, 22]:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Изменить тему', 'Изменить описание')
                user_markup.row('Изменить дату', 'Изменить требования')
                user_markup.row('Изменить сайт проекта')
                user_markup.row('Изменить твиттер', 'Изменить дискорд')
                user_markup.row('Изменить баннер', 'Изменить хэштеги')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                       reply_markup=user_markup)
                set_state(message.chat.id, 13)
            elif get_state(message.chat.id) in [140, 150, 160, 170, 180, 190, 200, 210, 220]:
                edition_post = get_chat_value_message(message)

                if await preview(bot, message, edition_post, settings):
                    key = InlineKeyboardMarkup()
                    key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)

        elif message.text == 'Изменить тему':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute(f"SELECT post_name FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    await bot.send_message(message.chat.id, 'Поста с такой темой нет!\nВыберите заново!')
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Назад')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Введите новую тему поста',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 14)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 140)
                con.close()

        elif message.text == 'Изменить описание':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute(f"SELECT post_desc FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    await bot.send_message(message.chat.id, 'Поста с таким описанием нет!\nВыберите заново!')
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Назад')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Введите новое описание поста',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 15)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 150)
                con.close()

        elif message.text == 'Изменить дату':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute(f"SELECT post_date FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    await bot.send_message(message.chat.id, 'Поста с такой датой нет!\nВыберите заново!')
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Назад')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Введите новую дату поста',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 16)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 160)
                con.close()

        elif message.text == 'Изменить требования':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute(f"SELECT what_needs FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    await bot.send_message(message.chat.id, 'Поста с такими требованиями нет!\nВыберите заново!')
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Назад')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Введите что нужно сделать для участия',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 17)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 170)
                con.close()

        elif message.text == 'Изменить сайт проекта':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute(f"SELECT site FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    await bot.send_message(message.chat.id, 'Поста с такими сайтом нет!\nВыберите заново!')
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Назад')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Введите новый сайт проекта',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 18)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 180)
                con.close()

        elif message.text == 'Изменить твиттер':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute(f"SELECT twitter FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    await bot.send_message(message.chat.id, 'Поста с такими твиттером нет!\nВыберите заново!')
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Назад')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Введите новый твиттер проекта',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 19)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 190)
                con.close()

        elif message.text == 'Изменить дискорд':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute(f"SELECT discord FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    await bot.send_message(message.chat.id, 'Поста с такими дискордом нет!\nВыберите заново!')
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Назад')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Введите новый дискорд проекта',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 20)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 200)
                con.close()

        elif message.text == 'Изменить баннер':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute(f"SELECT pic_post FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    await bot.send_message(message.chat.id, 'Поста с таким баннером нет!\nВыберите заново!')
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Назад')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Вставьте баннер (изображение) поста.'
                                                            'Или если нет баннера, то пропишите /empty',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 21)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 210)
                con.close()

        elif message.text == 'Изменить хэштеги':
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                a = 0
                cursor.execute(f"SELECT hashtags FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")
                for i in cursor.fetchall(): a += 1
                if a == 0:
                    await bot.send_message(message.chat.id, 'Поста с такими хэштегами нет!\nВыберите заново!')
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Назад')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Введите новые хэштеги',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 22)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 220)
                con.close()

        elif message.text == 'Удалить пост':
            await bot.delete_message(message.chat.id, message.message_id)
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute("SELECT author_name, post_name, post_date FROM posts;")
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            a = 0
            for author_username, post_name, post_date in cursor.fetchall():
                a += 1
                user_markup.row(str(post_name))
            if a == 0:
                await bot.send_message(message.chat.id, 'Никаких постов ещё не создано!', reply_markup=user_markup)
            else:
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Какой пост нужно удалить?',
                                       parse_mode='Markdown', reply_markup=user_markup)
                set_state(message.chat.id, 11)
            con.close()

        elif message.text == 'Списки':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row('Список авторов')
            user_markup.row('Список модераторов', 'Список админов')
            user_markup.row(main_menu)

            await bot.send_message(message.chat.id, "Выберите список для отображения", reply_markup=user_markup)

        elif message.text == 'Список авторов':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row('Добавить нового автора', 'Удалить автора')
            user_markup.row(main_menu)

            authors = "Список авторов:\n\n"
            if len(get_admin_list()) != 0:
                for author in get_author_list():
                    authors += f"{author[0]} - @{author[1]} - {author[2]} XP\n"

                await bot.send_message(message.chat.id, authors, reply_markup=user_markup, parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id, "Авторов еще нет", reply_markup=user_markup)

        elif message.text == 'Добавить нового автора':
            await bot.delete_message(message.chat.id, message.message_id)
            key = InlineKeyboardMarkup()
            key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                         callback_data='Вернуться в главное меню'))
            await bot.send_message(message.chat.id, 'Перешлите любое сообщение от пользователя,'
                                                    'которого хотите сделать автором', reply_markup=key)
            set_state(message.chat.id, 31)

        elif message.text == 'Удалить автора':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            a = 0
            for author in get_author_list():
                a += 1
                user_markup.row(f"{author[0]} - @{author[1]} - {author[2]} XP\n")
            if a == 1:
                await bot.send_message(message.chat.id, 'Вы ещё не добавляли авторов!')
            else:
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Выбери автора, которого нужно удалить',
                                       reply_markup=user_markup)
                set_state(message.chat.id, 32)

        elif message.text == 'Список админов':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row('Добавить нового админа', 'Удалить админа')
            user_markup.row(main_menu)

            admins = "Список админов:\n\n"
            if len(get_admin_list()) != 0:
                for admin in get_admin_list():
                    admins += f"{admin[0]} - @{admin[1]}\n"

                await bot.send_message(message.chat.id, admins, reply_markup=user_markup, parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id, "Админов еще нет", reply_markup=user_markup)

        elif message.text == 'Добавить нового админа':
            await bot.delete_message(message.chat.id, message.message_id)
            key = InlineKeyboardMarkup()
            key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                         callback_data='Вернуться в главное меню'))
            await bot.send_message(message.chat.id, 'Перешлите любое сообщение от пользователя,'
                                                    'которого хотите сделать админом', reply_markup=key)
            set_state(message.chat.id, 41)

        elif message.text == 'Удалить админа':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            a = 0
            for admin in get_admin_list():
                a += 1
                if int(admin[0]) != admin_id: user_markup.row(f"{str(admin[0])} - {admin[1]}")
            if a == 1:
                await bot.send_message(message.chat.id, 'Вы ещё не добавляли админов!')
            else:
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Выбери админа, которого нужно удалить',
                                       reply_markup=user_markup)
                set_state(message.chat.id, 42)

        elif message.text == 'Список модераторов':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row('Добавить нового модератора', 'Удалить модератора')
            user_markup.row(main_menu)

            moders = "Список модераторов:\n\n"
            if len(get_moder_list()) != 0:
                for moder in get_moder_list():
                    moders += f"{moder[0]} - @{moder[1]}\n"
                await bot.send_message(message.chat.id, moders, reply_markup=user_markup, parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id, "Модераторов еще нет", reply_markup=user_markup)

        elif message.text == 'Добавить нового модератора':
            await bot.delete_message(message.chat.id, message.message_id)
            key = InlineKeyboardMarkup()
            key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                         callback_data='Вернуться в главное меню'))
            await bot.send_message(message.chat.id, 'Перешлите сообщение пользователя в бота, '
                                                    'чтобы сделать его модератором.', reply_markup=key)
            set_state(message.chat.id, 51)

        elif message.text == 'Удалить модератора':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            a = 0
            for moder in get_moder_list():
                a += 1
                user_markup.row(f'{str(moder[0])} - {moder[1]}')
            if a == 0:
                await bot.send_message(message.chat.id, 'Вы ещё не добавляли модераторов!')
            else:
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Выбери id модератора, которого нужно удалить',
                                       reply_markup=user_markup)
                set_state(message.chat.id, 52)

        elif message.text == 'Скачать лог файл':
            await bot.delete_message(message.chat.id, message.message_id)
            working_log = open(files.working_log, 'rb')
            await bot.send_document(message.chat.id, working_log)
            working_log.close()
            system_log = open(files.system_log, 'rb')
            await bot.send_document(message.chat.id, system_log)
            system_log.close()

        elif message.text == 'Настройки бота':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)

            user_markup.row(f'Часовой пояс: {settings.time_zone}')
            user_markup.row(f'Название канала: {settings.channel_name}')
            user_markup.row(f'Порог опыта авторам: {settings.threshold_xp}')
            user_markup.row('Изменить выводное сообщение команды /help')
            user_markup.row('Изменить нижнюю подпись для постов')
            user_markup.row('Скачать лог файл')
            user_markup.row(main_menu)

            await bot.send_message(message.chat.id, "Вы вошли в настройки бота", reply_markup=user_markup,
                                   parse_mode="HTML")

        elif message.text == 'Изменить выводное сообщение команды /help':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(main_menu)
            help_entities = []

            help_text = settings.help_text
            raw_entities = json.loads(str(settings.help_text_entities))

            if "entities" in raw_entities:

                for entity in raw_entities["entities"]:
                    entity_values_list = list(entity.values())

                    if entity["type"] == "text_link":
                        entity = MessageEntity(type=entity_values_list[0],
                                               offset=entity_values_list[1],
                                               length=entity_values_list[2], url=entity_values_list[3])
                        help_entities.append(entity)
                    elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                            "email", "phone_number", "bold", "italic", "underline",
                                            "strikethrough", "code"]:
                        entity = MessageEntity(type=entity_values_list[0],
                                               offset=entity_values_list[1],
                                               length=entity_values_list[2])
                        help_entities.append(entity)

            await bot.send_message(message.chat.id, "На данный момент сообщение help такое:")
            await bot.send_message(message.chat.id, help_text, entities=help_entities, reply_markup=user_markup)
            await bot.send_message(message.chat.id, "Введите новое сообщение для команды help:")

            set_state(message.chat.id, 61)

        elif message.text == 'Изменить нижнюю подпись для постов':
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(main_menu)
            footer_entities = []

            footer_text = settings.footer_text
            raw_entities = json.loads(str(settings.footer_text_entities))

            if "entities" in raw_entities:

                for entity in raw_entities["entities"]:
                    entity_values_list = list(entity.values())

                    if entity["type"] == "text_link":
                        entity = MessageEntity(type=entity_values_list[0],
                                               offset=entity_values_list[1],
                                               length=entity_values_list[2], url=entity_values_list[3])
                        footer_entities.append(entity)
                    elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                            "email", "phone_number", "bold", "italic", "underline",
                                            "strikethrough", "code"]:
                        entity = MessageEntity(type=entity_values_list[0],
                                               offset=entity_values_list[1],
                                               length=entity_values_list[2])
                        footer_entities.append(entity)

            await bot.send_message(message.chat.id, "На данный момент footer такой:")
            await bot.send_message(message.chat.id, footer_text, entities=footer_entities, reply_markup=user_markup)
            await bot.send_message(message.chat.id, "Введите новый footer:")

            set_state(message.chat.id, 62)

        elif isinstance(message.text, str) and 'Порог опыта авторам:' in message.text:
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)

            user_markup.row(main_menu)

            await bot.send_message(message.chat.id, "Введите новый порог для авторов"
                                                    " (только число)", reply_markup=user_markup)
            set_state(message.chat.id, 63)

        elif get_state(message.chat.id) == 1:
            set_chat_value_message(message, 1)

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            a = 0

            try:
                cursor.execute("SELECT author_name, post_name, status FROM posts "
                               f"WHERE post_name = '{message.text}';")
            except Exception as e:
                print(e)
            else:
                for author_name, post_name, status in cursor.fetchall():
                    temp_status = status
                    a += 1

                if a == 0:
                    creation_post = get_chat_value_message(message)

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, f"Тема поста: {str(creation_post['post_name'])}",
                                           reply_markup=user_markup)

                    key = InlineKeyboardMarkup()
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, f"Введите описание для {creation_post['post_name']}",
                                           reply_markup=key)
                    set_state(message.chat.id, 2)
                else:
                    await bot.send_message(message.chat.id, 'Пост с похожей темой существует. '
                                                            'Введите другую тему поста')

            con.close()

        elif get_state(message.chat.id) == 2:
            set_chat_value_message(message, 2)

            key = InlineKeyboardMarkup()
            key.row(InlineKeyboardButton(text='ДА', callback_data='Есть дата проведения'),
                    InlineKeyboardButton(text='НЕТ', callback_data='Нет даты проведения'))
            key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                         callback_data='Вернуться в главное меню'))
            await bot.send_message(message.chat.id, 'Есть ли дата проведения события или дедлайн?',
                                   reply_markup=key)
            delete_state(message.chat.id)

        elif get_state(message.chat.id) == 3:
            set_chat_value_message(message, 3)

            key = InlineKeyboardMarkup()
            key.row(InlineKeyboardButton(text='ДА', callback_data='Есть требования'),
                    InlineKeyboardButton(text='НЕТ', callback_data='Нет требований'))
            key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                         callback_data='Вернуться в главное меню'))
            await bot.send_message(message.chat.id, 'Нужно ли что-то сделать для участия?', reply_markup=key)
            delete_state(message.chat.id)

        elif get_state(message.chat.id) in [4, 5, 6]:
            key = InlineKeyboardMarkup()
            if get_state(message.chat.id) == 4:
                set_chat_value_message(message, 4)

                key.row(InlineKeyboardButton(text='ДА', callback_data='Есть сайт'),
                        InlineKeyboardButton(text='НЕТ', callback_data='Нет сайта'))
                key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                             callback_data='Вернуться в главное меню'))
                await bot.send_message(message.chat.id, 'Есть ли сайт у проекта?', reply_markup=key)

                delete_state(message.chat.id)
            elif get_state(message.chat.id) == 5:
                if validators.url(message.text):
                    set_chat_value_message(message, 5)

                    key.row(InlineKeyboardButton(text='ДА', callback_data='Есть твиттер'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Нет твиттера'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Есть ли твиттер у проекта?', reply_markup=key)
                    delete_state(message.chat.id)
                else:
                    await bot.send_message(message.chat.id, 'Введите ссылку формата http://example.com')
            elif get_state(message.chat.id) == 6:
                if validators.url(message.text):
                    set_chat_value_message(message, 6)

                    key.row(InlineKeyboardButton(text='ДА', callback_data='Есть дискорд'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Нет дискорда'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Есть ли дискорд у проекта?', reply_markup=key)
                    delete_state(message.chat.id)
                else:
                    await bot.send_message(message.chat.id, 'Введите ссылку формата http://example.com')

        elif get_state(message.chat.id) == 7:
            if validators.url(message.text):
                set_chat_value_message(message, 7)

                key = InlineKeyboardMarkup()
                key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                             callback_data='Вернуться в главное меню'))
                await bot.send_message(message.chat.id, 'Важное напоминание!!! '
                                                        'Определитесь, будет ли в нём картинка.'
                                                        'Если вы не добавите картинку сразу, '
                                                        'то потом вы её не сможете уже добавить, и если картинка уже была,'
                                                        'то вы не сможете её убрать!')
                await bot.send_message(message.chat.id, 'Вставьте баннер (изображение) поста. '
                                                        'Или если нет баннера, то пропишите /empty', reply_markup=key)

                set_state(message.chat.id, 8)
            else:
                await bot.send_message(message.chat.id, 'Введите ссылку формата http://example.com')

        elif get_state(message.chat.id) == 8:
            if message.text == '/empty':
                set_chat_value_message(message, 8)
            elif message.document:
                file_info = await bot.get_file(message.document.file_id)
                downloaded_file = await bot.download_file(file_info.file_path)

                creation_post = get_chat_value_message(message)

                src = f"data/media/posts_media/pic for post - {creation_post['post_name']}.jpeg"
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file.getvalue())
                set_chat_value_message(message, 8, pic_src=src)

                await bot.send_message(message.chat.id, 'Изображение загружено.')
            elif message.photo:
                file_info = await bot.get_file(message.photo[-1].file_id)
                downloaded_file = await bot.download_file(file_info.file_path)

                creation_post = get_chat_value_message(message)

                src = f"data/media/posts_media/pic for post - {creation_post['post_name']}.jpeg"
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file.getvalue())
                set_chat_value_message(message, 8, pic_src=src)

                await bot.send_message(message.chat.id, 'Изображение загружено.')

            key = InlineKeyboardMarkup()
            key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                         callback_data='Вернуться в главное меню'))
            await bot.send_message(message.chat.id, 'Введите хэштеги поста', reply_markup=key)

            set_state(message.chat.id, 9)

        elif get_state(message.chat.id) == 9:
            if '#' in message.text:
                set_chat_value_message(message, 9)

                creation_post = get_chat_value_message(message)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute("INSERT INTO posts (author_name, author_id, post_name, post_desc, post_date, "
                               "what_needs, site, twitter, discord, hashtags, pic_post, name_entities, "
                               "desc_entities, date_entities, what_needs_entities) "
                               f"VALUES ('{str(creation_post['author_name'])}', "
                               f"{str(creation_post['author_id'])}, '{str(creation_post['post_name'])}', "
                               f"'{str(creation_post['post_desc'])}', '{str(creation_post['post_date'])}', "
                               f"'{str(creation_post['what_needs'])}', '{str(creation_post['site'])}', "
                               f"'{str(creation_post['twitter'])}', '{str(creation_post['discord'])}', "
                               f"'{str(creation_post['hashtags'])}', "
                               f"'{str(creation_post['pic_post'])}', "
                               f"'{str(creation_post['name_entities'])}', "
                               f"'{str(creation_post['desc_entities'])}', "
                               f"'{str(creation_post['date_entities'])}', "
                               f"'{str(creation_post['what_needs_entities'])}');")
                con.commit()
                con.close()

                await log(f"Post {str(creation_post['post_name'])} is created by {message.chat.id}")

                await bot.send_message(message.chat.id, 'Пост был сохранён в базу данных.')

                if await preview(bot, message, creation_post, settings):
                    key = InlineKeyboardMarkup()
                    key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)

            else:
                await bot.send_message(message.chat.id, 'Вы не ввели ни одного хэштега!'
                                                        'Введите хэштеги поста.')

        elif get_state(message.chat.id) == 10:
            if message.text.lower() == 'да':
                creation_post = get_chat_value_message(message)
                entity_list = []
                text = f"{creation_post['post_name']}\n\n" \
                       f"{creation_post['post_desc']}\n\n"

                if creation_post['what_needs'] != '':
                    text += f"✅ {creation_post['what_needs']}\n\n"

                if creation_post['post_date'] != '':
                    text += f"📆 {creation_post['post_date']}\n\n"

                if creation_post['site'] != '' or creation_post['twitter'] != '' or creation_post['discord'] != '':
                    text += "🔗 "
                    if creation_post['site'] != '':
                        text += "Сайт проекта "
                    if creation_post['twitter'] != '':
                        if creation_post['site'] == '':
                            text += "Twitter "
                        else:
                            text += "| Twitter "
                    if creation_post['discord'] != '':
                        if creation_post['site'] == '' and creation_post['twitter'] == '':
                            text += "Discord"
                        else:
                            text += "| Discord"
                    text += "\n\n"

                text += f"{creation_post['hashtags']}\n\n" \
                        f"Автор: @{creation_post['author_name']}\n" \
                        f"{settings.footer_text}"

                name_entities = json.loads(str(creation_post['name_entities']))
                description_entities = json.loads(str(creation_post['desc_entities']))
                date_entities = json.loads(str(creation_post['date_entities']))
                what_needs_entities = json.loads(str(creation_post['what_needs_entities']))
                footer_text_entities = json.loads(settings.footer_text_entities)

                count_string_track = 0

                entity = MessageEntity(type="bold",
                                       offset=count_string_track,
                                       length=len(creation_post['post_name']))
                entity_list.append(entity)

                if "entities" in name_entities:

                    for entity in name_entities["entities"]:
                        entity_values_list = list(entity.values())

                        if entity["type"] == "text_link":
                            entity = MessageEntity(type=entity_values_list[0],
                                                   offset=count_string_track + entity_values_list[1],
                                                   length=entity_values_list[2], url=entity_values_list[3])
                            entity_list.append(entity)
                        elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                                "email", "phone_number", "bold", "italic", "underline",
                                                "strikethrough", "code"]:
                            entity = MessageEntity(type=entity_values_list[0],
                                                   offset=count_string_track + entity_values_list[1],
                                                   length=entity_values_list[2])
                            entity_list.append(entity)

                count_string_track += len(str(creation_post['post_name'])) + len("\n\n")

                if "entities" in description_entities:

                    for entity in description_entities["entities"]:
                        entity_values_list = list(entity.values())

                        if entity["type"] == "text_link":
                            entity = MessageEntity(type=entity_values_list[0],
                                                   offset=count_string_track + entity_values_list[1],
                                                   length=entity_values_list[2], url=entity_values_list[3])
                            entity_list.append(entity)
                        elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                                "email", "phone_number", "bold", "italic", "underline",
                                                "strikethrough", "code"]:
                            entity = MessageEntity(type=entity_values_list[0],
                                                   offset=count_string_track + entity_values_list[1],
                                                   length=entity_values_list[2])
                            entity_list.append(entity)

                count_string_track += len(str(creation_post['post_desc'])) + len("\n\n")

                if creation_post['what_needs'] != '':
                    count_string_track += len(str('✅ '))

                    if "entities" in what_needs_entities:

                        for entity in what_needs_entities["entities"]:
                            entity_values_list = list(entity.values())

                            if entity["type"] == "text_link":
                                entity = MessageEntity(type=entity_values_list[0],
                                                       offset=count_string_track + entity_values_list[1],
                                                       length=entity_values_list[2], url=entity_values_list[3])
                                entity_list.append(entity)
                            elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                                    "email", "phone_number", "bold", "italic", "underline",
                                                    "strikethrough", "code"]:
                                entity = MessageEntity(type=entity_values_list[0],
                                                       offset=count_string_track + entity_values_list[1],
                                                       length=entity_values_list[2])
                                entity_list.append(entity)

                    count_string_track += len(str(creation_post['what_needs'])) + len("\n\n")

                if creation_post['post_date'] != '':
                    count_string_track += len(str('📆 ')) + 1

                    if "entities" in date_entities:

                        for entity in date_entities["entities"]:
                            entity_values_list = list(entity.values())

                            if entity["type"] == "text_link":
                                entity = MessageEntity(type=entity_values_list[0],
                                                       offset=count_string_track + entity_values_list[1],
                                                       length=entity_values_list[2], url=entity_values_list[3])
                                entity_list.append(entity)
                            elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                                    "email", "phone_number", "bold", "italic", "underline",
                                                    "strikethrough", "code"]:
                                entity = MessageEntity(type=entity_values_list[0],
                                                       offset=count_string_track + entity_values_list[1],
                                                       length=entity_values_list[2])
                                entity_list.append(entity)

                    count_string_track += len(str(creation_post['post_date'])) + len("\n\n")

                if creation_post['site'] != '' or creation_post['twitter'] != '' or creation_post['discord'] != '':
                    count_string_track += len("🔗 ") + 1
                    if creation_post['site'] != '':
                        entity = MessageEntity(type="text_link",
                                               offset=count_string_track,
                                               length=len("Сайт проекта"),
                                               url=f"{creation_post['site']}")
                        entity_list.append(entity)
                        count_string_track += len("Сайт проекта ")
                    if creation_post['twitter'] != '':
                        if creation_post['site'] == '':
                            entity = MessageEntity(type="text_link",
                                                   offset=count_string_track,
                                                   length=len("Twitter"),
                                                   url=f"{creation_post['twitter']}")
                            entity_list.append(entity)
                            count_string_track += len("Twitter ")
                        else:
                            entity = MessageEntity(type="text_link",
                                                   offset=count_string_track + len("| "),
                                                   length=len("Twitter"),
                                                   url=f"{creation_post['twitter']}")
                            entity_list.append(entity)
                            count_string_track += len("| Twitter ")
                    if creation_post['discord'] != '':
                        if creation_post['site'] == '' and creation_post['twitter'] == '':
                            entity = MessageEntity(type="text_link",
                                                   offset=count_string_track,
                                                   length=len("Discord"),
                                                   url=f"{creation_post['discord']}")
                            entity_list.append(entity)
                            count_string_track += len("Discord")
                        else:
                            entity = MessageEntity(type="text_link",
                                                   offset=count_string_track + len("| "),
                                                   length=len("Discord"),
                                                   url=f"{creation_post['discord']}")
                            entity_list.append(entity)
                            count_string_track += len("| Discord")
                    count_string_track += len("\n\n")

                count_string_track += len(str(creation_post['hashtags'])) + len("\n\n")

                entity = MessageEntity(type="italic",
                                       offset=count_string_track,
                                       length=len('Автор'))
                entity_list.append(entity)

                count_string_track += len(f"Автор: @{creation_post['author_name']}\n")

                if "entities" in footer_text_entities:

                    for entity in footer_text_entities["entities"]:
                        entity_values_list = list(entity.values())

                        if entity["type"] == "text_link":
                            entity = MessageEntity(type=entity_values_list[0],
                                                   offset=count_string_track + entity_values_list[1],
                                                   length=entity_values_list[2], url=entity_values_list[3])
                            entity_list.append(entity)
                        elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                                "email", "phone_number", "bold", "italic", "underline",
                                                "strikethrough", "code"]:
                            entity = MessageEntity(type=entity_values_list[0],
                                                   offset=count_string_track + entity_values_list[1],
                                                   length=entity_values_list[2])
                            entity_list.append(entity)

                if type(creation_post['pic_post']) is tuple:
                    if creation_post['pic_post'][0] == '':
                        message_result = await bot.send_message(settings.channel_name, text, entities=entity_list)
                    else:
                        photo = open(creation_post['pic_post'][0], 'rb')
                        message_result = await bot.send_photo(settings.channel_name,
                                                              photo, caption=text, caption_entities=entity_list)
                else:
                    if creation_post['pic_post'] == '':
                        message_result = await bot.send_message(settings.channel_name, text, entities=entity_list)
                    else:
                        photo = open(creation_post['pic_post'], 'rb')
                        message_result = await bot.send_photo(settings.channel_name,
                                                              photo, caption=text, caption_entities=entity_list)

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Посты')
                user_markup.row('Списки')
                user_markup.row('Настройки бота')

                await bot.send_message(message.chat.id, 'Пост был создан и размещен на канале.',
                                       reply_markup=user_markup)

                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute(f"UPDATE posts SET status = 1, message_id = {message_result.message_id} "
                               f"WHERE post_name = '{str(creation_post['post_name'])}';")
                con.commit()
                con.close()

                await log(f"Post {str(creation_post['post_name'])} is posted by {message.chat.id}")

                delete_chat_value_message(message)
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Посты')
                user_markup.row('Списки')
                user_markup.row('Настройки бота')

                await bot.send_message(message.chat.id, "Вы не написали 'Да', поэтому Пост не был размещён.",
                                       reply_markup=user_markup)

                delete_chat_value_message(message)
                delete_state(message.chat.id)

        elif get_state(message.chat.id) == 90:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            a = 0
            cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                           "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                           f"what_needs_entities, status FROM posts WHERE post_name = '{message.text}';")
            for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                pic_post, name_entities, desc_entities, date_entities, \
                what_needs_entities, status in cursor.fetchall():
                a += 1

                with shelve.open(files.bot_message_bd) as bd:
                    bd[str(message.chat.id)] = {
                        'author_name': str(author_name),
                        'post_name': str(post_name),
                        'post_desc': str(post_desc),
                        'post_date': str(post_date),
                        'what_needs': str(what_needs),
                        'site': str(site),
                        'twitter': str(twitter),
                        'discord': str(discord),
                        'hashtags': str(hashtags),
                        'pic_post': str(pic_post),
                        'name_entities': str(name_entities),
                        'desc_entities': str(desc_entities),
                        'date_entities': str(date_entities),
                        'what_needs_entities': str(what_needs_entities),
                        'status': status
                    }

            if a == 0:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')
            else:
                unposted_post = get_chat_value_message(message)

                if not await preview(bot, message, unposted_post, settings):
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)
                else:
                    post_key = InlineKeyboardMarkup()
                    post_key.add(InlineKeyboardButton(text="ДА", callback_data='Разместить пост'),
                                 InlineKeyboardButton(text="НЕТ", callback_data='Вернуться в меню размещения'))

                    await bot.send_message(message.chat.id, 'Разместить данный пост?',
                                           reply_markup=post_key)
            con.close()

        elif get_state(message.chat.id) == 11:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            a = 0
            cursor.execute(f"SELECT post_name, message_id FROM posts WHERE post_name = '{message.text}'")
            for post_name, message_id in cursor.fetchall():
                a += 1
                try:
                    await bot.delete_message(settings.channel_name, message_id)
                except:
                    await bot.send_message(message.chat.id, 'Пост не может быть удалён из канала: '
                                                            'он не был там размещён!')
            if a == 0:
                await bot.send_message(message.chat.id,
                                       'Выбранного поста не обнаружено! '
                                       'Выберите его, нажав на соответствующую кнопку')
            else:
                cursor.execute(f"DELETE FROM posts WHERE post_name = '{message.text}';")
                con.commit()

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Добавить новый пост', 'Удалить пост')
                user_markup.row('Редактирование постов', 'Размещение постов')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Пост успешно удален!', reply_markup=user_markup)
                await log(f'Post {message.text} is deleted by {message.chat.id}')
                delete_state(message.chat.id)
            con.close()

        elif get_state(message.chat.id) == 12:
            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            a = 0
            cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                           "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                           f"what_needs_entities, status FROM posts WHERE post_name = '{message.text}';")
            for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                pic_post, name_entities, desc_entities, date_entities, \
                what_needs_entities, status in cursor.fetchall():
                a += 1

                with shelve.open(files.bot_message_bd) as bd:
                    bd[str(message.chat.id)] = {
                        'author_name': str(author_name),
                        'post_name': str(post_name),
                        'post_desc': str(post_desc),
                        'post_date': str(post_date),
                        'what_needs': str(what_needs),
                        'site': str(site),
                        'twitter': str(twitter),
                        'discord': str(discord),
                        'hashtags': str(hashtags),
                        'pic_post': str(pic_post),
                        'name_entities': str(name_entities),
                        'desc_entities': str(desc_entities),
                        'date_entities': str(date_entities),
                        'what_needs_entities': str(what_needs_entities),
                        'status': status
                    }

            edition_post = get_chat_value_message(message)

            if a == 0:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')
            else:
                await preview(bot, message, edition_post, settings)

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Изменить тему', 'Изменить описание')
                user_markup.row('Изменить дату', 'Изменить требования')
                user_markup.row('Изменить сайт проекта')
                user_markup.row('Изменить твиттер', 'Изменить дискорд')
                user_markup.row('Изменить баннер', 'Изменить хэштеги')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                       reply_markup=user_markup)
                set_state(message.chat.id, 13)
            con.close()

        elif get_state(message.chat.id) in [14, 140]:
            edition_post = get_chat_value_message(message)

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute(f"UPDATE posts SET post_name = '{message.text}', name_entities = '{str(message)}' "
                           f"WHERE post_name = '{str(edition_post['post_name'])}';")
            con.commit()

            if get_state(message.chat.id) == 14:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{message.text}';")
                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if edition_post['status']:
                    await edit_post(bot, message, edition_post, settings, 0)
                else:
                    pass

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Изменить тему', 'Изменить описание')
                user_markup.row('Изменить дату', 'Изменить требования')
                user_markup.row('Изменить сайт проекта')
                user_markup.row('Изменить твиттер', 'Изменить дискорд')
                user_markup.row('Изменить баннер', 'Изменить хэштеги')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Тема поста успешно изменена!', reply_markup=user_markup)
                await log(f"Name post {edition_post['post_name']} is changed by {message.chat.id}")
                set_state(message.chat.id, 13)

            elif get_state(message.chat.id) == 140:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{message.text}';")
                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if await preview(bot, message, edition_post, settings):
                    key = InlineKeyboardMarkup()
                    key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)

            con.close()

        elif get_state(message.chat.id) in [15, 150]:
            edition_post = get_chat_value_message(message)

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute(f"UPDATE posts SET post_desc = '{message.text}', desc_entities = '{str(message)}' "
                           f"WHERE post_name = '{str(edition_post['post_name'])}';")
            con.commit()

            if get_state(message.chat.id) == 15:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if edition_post['status']:
                    await edit_post(bot, message, edition_post, settings, 0)
                else:
                    pass

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Изменить тему', 'Изменить описание')
                user_markup.row('Изменить дату', 'Изменить требования')
                user_markup.row('Изменить сайт проекта')
                user_markup.row('Изменить твиттер', 'Изменить дискорд')
                user_markup.row('Изменить баннер', 'Изменить хэштеги')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Описание поста успешно изменено!', reply_markup=user_markup)
                await log(f"Description post {edition_post['post_name']} is changed by {message.chat.id}")
                set_state(message.chat.id, 13)
            elif get_state(message.chat.id) == 150:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if await preview(bot, message, edition_post, settings):
                    key = InlineKeyboardMarkup()
                    key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)
            con.close()

        elif get_state(message.chat.id) in [16, 160]:
            edition_post = get_chat_value_message(message)

            if message.text == '/empty':
                post_date = ''
                date_entities = ''
            else:
                post_date = message.text
                date_entities = message

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute(f"UPDATE posts SET post_date = '{post_date}', date_entities = '{date_entities}' "
                           f"WHERE post_name = '{str(edition_post['post_name'])}';")
            con.commit()

            if get_state(message.chat.id) == 16:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if edition_post['status']:
                    await edit_post(bot, message, edition_post, settings, 0)
                else:
                    pass

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Изменить тему', 'Изменить описание')
                user_markup.row('Изменить дату', 'Изменить требования')
                user_markup.row('Изменить сайт проекта')
                user_markup.row('Изменить твиттер', 'Изменить дискорд')
                user_markup.row('Изменить баннер', 'Изменить хэштеги')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Дата события успешно изменена!',
                                       reply_markup=user_markup)
                await log(f"Date post {edition_post['post_name']} is changed by {message.chat.id}")
                set_state(message.chat.id, 13)
            elif get_state(message.chat.id) == 160:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if await preview(bot, message, edition_post, settings):
                    key = InlineKeyboardMarkup()
                    key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)
            con.close()

        elif get_state(message.chat.id) in [17, 170]:
            edition_post = get_chat_value_message(message)

            if message.text == '/empty':
                what_needs = ''
                what_needs_entities = ''
            else:
                what_needs = message.text
                what_needs_entities = message

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute(f"UPDATE posts SET what_needs = '{what_needs}', "
                           f"what_needs_entities = '{what_needs_entities}' "
                           f"WHERE post_name = '{str(edition_post['post_name'])}';")
            con.commit()

            if get_state(message.chat.id) == 17:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if edition_post['status']:
                    await edit_post(bot, message, edition_post, settings, 0)
                else:
                    pass

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Изменить тему', 'Изменить описание')
                user_markup.row('Изменить дату', 'Изменить требования')
                user_markup.row('Изменить сайт проекта')
                user_markup.row('Изменить твиттер', 'Изменить дискорд')
                user_markup.row('Изменить баннер', 'Изменить хэштеги')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Условия участия успешно изменены!', reply_markup=user_markup)
                await log(f"Requirements {edition_post['post_name']} is changed by {message.chat.id}")
                set_state(message.chat.id, 13)
            elif get_state(message.chat.id) == 170:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if await preview(bot, message, edition_post, settings):
                    key = InlineKeyboardMarkup()
                    key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)
            con.close()

        elif get_state(message.chat.id) in [18, 180]:
            edition_post = get_chat_value_message(message)

            site = ''

            if message.text == '/empty':
                flag_site = 1
            else:
                if validators.url(message.text):
                    site = message.text
                    flag_site = 1
                else:
                    await bot.send_message(message.chat.id, 'Введите ссылку формата http://example.com')
                    flag_site = 0

            if flag_site:
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute(f"UPDATE posts SET site = '{site}' "
                               f"WHERE post_name = '{str(edition_post['post_name'])}';")
                con.commit()

                if get_state(message.chat.id) == 18:
                    cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                                   "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                                   "what_needs_entities, status, message_id "
                                   f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                    for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                        pic_post, name_entities, desc_entities, date_entities, \
                        what_needs_entities, status, message_id in cursor.fetchall():
                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(author_name),
                                'post_name': str(post_name),
                                'post_desc': str(post_desc),
                                'post_date': str(post_date),
                                'what_needs': str(what_needs),
                                'site': str(site),
                                'twitter': str(twitter),
                                'discord': str(discord),
                                'hashtags': str(hashtags),
                                'pic_post': str(pic_post),
                                'name_entities': str(name_entities),
                                'desc_entities': str(desc_entities),
                                'date_entities': str(date_entities),
                                'what_needs_entities': str(what_needs_entities),
                                'status': status,
                                'message_id': message_id
                            }

                    edition_post = get_chat_value_message(message)

                    if edition_post['status']:
                        await edit_post(bot, message, edition_post, settings, 0)
                    else:
                        pass

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Сайт проекта успешно изменен!', reply_markup=user_markup)
                    await log(f"Requirements {edition_post['post_name']} is changed by {message.chat.id}")
                    set_state(message.chat.id, 13)
                elif get_state(message.chat.id) == 180:
                    cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                                   "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                                   "what_needs_entities, status, message_id "
                                   f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                    for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                        pic_post, name_entities, desc_entities, date_entities, \
                        what_needs_entities, status, message_id in cursor.fetchall():
                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(author_name),
                                'post_name': str(post_name),
                                'post_desc': str(post_desc),
                                'post_date': str(post_date),
                                'what_needs': str(what_needs),
                                'site': str(site),
                                'twitter': str(twitter),
                                'discord': str(discord),
                                'hashtags': str(hashtags),
                                'pic_post': str(pic_post),
                                'name_entities': str(name_entities),
                                'desc_entities': str(desc_entities),
                                'date_entities': str(date_entities),
                                'what_needs_entities': str(what_needs_entities),
                                'status': status,
                                'message_id': message_id
                            }

                    edition_post = get_chat_value_message(message)

                    if await preview(bot, message, edition_post, settings):
                        key = InlineKeyboardMarkup()
                        key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                     callback_data='Вернуться в главное меню'))
                        await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                    else:
                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row('Изменить тему', 'Изменить описание')
                        user_markup.row('Изменить дату', 'Изменить требования')
                        user_markup.row('Изменить сайт проекта')
                        user_markup.row('Изменить твиттер', 'Изменить дискорд')
                        user_markup.row('Изменить баннер', 'Изменить хэштеги')
                        user_markup.row(main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)
                con.close()

        elif get_state(message.chat.id) in [19, 190]:
            edition_post = get_chat_value_message(message)

            twitter = ''

            if message.text == '/empty':
                flag_site = 1
            else:
                if validators.url(message.text):
                    twitter = message.text
                    flag_site = 1
                else:
                    await bot.send_message(message.chat.id, 'Введите ссылку формата http://example.com')
                    flag_site = 0

            if flag_site:
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute(f"UPDATE posts SET twitter = '{twitter}' "
                               f"WHERE post_name = '{str(edition_post['post_name'])}';")
                con.commit()

                if get_state(message.chat.id) == 19:
                    cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                                   "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                                   "what_needs_entities, status, message_id "
                                   f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                    for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                        pic_post, name_entities, desc_entities, date_entities, \
                        what_needs_entities, status, message_id in cursor.fetchall():
                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(author_name),
                                'post_name': str(post_name),
                                'post_desc': str(post_desc),
                                'post_date': str(post_date),
                                'what_needs': str(what_needs),
                                'site': str(site),
                                'twitter': str(twitter),
                                'discord': str(discord),
                                'hashtags': str(hashtags),
                                'pic_post': str(pic_post),
                                'name_entities': str(name_entities),
                                'desc_entities': str(desc_entities),
                                'date_entities': str(date_entities),
                                'what_needs_entities': str(what_needs_entities),
                                'status': status,
                                'message_id': message_id
                            }

                    edition_post = get_chat_value_message(message)

                    if edition_post['status']:
                        await edit_post(bot, message, edition_post, settings, 0)
                    else:
                        pass

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Твиттер проекта успешно изменен!', reply_markup=user_markup)
                    await log(f"Requirements {edition_post['post_name']} is changed by {message.chat.id}")
                    set_state(message.chat.id, 13)
                elif get_state(message.chat.id) == 190:
                    cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                                   "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                                   "what_needs_entities, status, message_id "
                                   f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                    for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                        pic_post, name_entities, desc_entities, date_entities, \
                        what_needs_entities, status, message_id in cursor.fetchall():
                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(author_name),
                                'post_name': str(post_name),
                                'post_desc': str(post_desc),
                                'post_date': str(post_date),
                                'what_needs': str(what_needs),
                                'site': str(site),
                                'twitter': str(twitter),
                                'discord': str(discord),
                                'hashtags': str(hashtags),
                                'pic_post': str(pic_post),
                                'name_entities': str(name_entities),
                                'desc_entities': str(desc_entities),
                                'date_entities': str(date_entities),
                                'what_needs_entities': str(what_needs_entities),
                                'status': status,
                                'message_id': message_id
                            }

                    edition_post = get_chat_value_message(message)

                    if await preview(bot, message, edition_post, settings):
                        key = InlineKeyboardMarkup()
                        key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                     callback_data='Вернуться в главное меню'))
                        await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                    else:
                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row('Изменить тему', 'Изменить описание')
                        user_markup.row('Изменить дату', 'Изменить требования')
                        user_markup.row('Изменить сайт проекта')
                        user_markup.row('Изменить твиттер', 'Изменить дискорд')
                        user_markup.row('Изменить баннер', 'Изменить хэштеги')
                        user_markup.row(main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)
                con.close()

        elif get_state(message.chat.id) in [20, 200]:
            edition_post = get_chat_value_message(message)

            discord = ''

            if message.text == '/empty':
                flag_site = 1
            else:
                if validators.url(message.text):
                    discord = message.text
                    flag_site = 1
                else:
                    await bot.send_message(message.chat.id, 'Введите ссылку формата http://example.com')
                    flag_site = 0

            if flag_site:
                con = sqlite3.connect(files.main_db)
                cursor = con.cursor()
                cursor.execute(f"UPDATE posts SET discord = '{discord}' "
                               f"WHERE post_name = '{str(edition_post['post_name'])}';")
                con.commit()

                if get_state(message.chat.id) == 20:
                    cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                                   "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                                   "what_needs_entities, status, message_id "
                                   f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                    for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                        pic_post, name_entities, desc_entities, date_entities, \
                        what_needs_entities, status, message_id in cursor.fetchall():
                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(author_name),
                                'post_name': str(post_name),
                                'post_desc': str(post_desc),
                                'post_date': str(post_date),
                                'what_needs': str(what_needs),
                                'site': str(site),
                                'twitter': str(twitter),
                                'discord': str(discord),
                                'hashtags': str(hashtags),
                                'pic_post': str(pic_post),
                                'name_entities': str(name_entities),
                                'desc_entities': str(desc_entities),
                                'date_entities': str(date_entities),
                                'what_needs_entities': str(what_needs_entities),
                                'status': status,
                                'message_id': message_id
                            }

                    edition_post = get_chat_value_message(message)

                    if edition_post['status']:
                        await edit_post(bot, message, edition_post, settings, 0)
                    else:
                        pass

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Дискорд проекта успешно изменен!', reply_markup=user_markup)
                    await log(f"Requirements {edition_post['post_name']} is changed by {message.chat.id}")
                    set_state(message.chat.id, 13)
                elif get_state(message.chat.id) == 200:
                    cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                                   "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                                   "what_needs_entities, status, message_id "
                                   f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                    for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                        pic_post, name_entities, desc_entities, date_entities, \
                        what_needs_entities, status, message_id in cursor.fetchall():
                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(author_name),
                                'post_name': str(post_name),
                                'post_desc': str(post_desc),
                                'post_date': str(post_date),
                                'what_needs': str(what_needs),
                                'site': str(site),
                                'twitter': str(twitter),
                                'discord': str(discord),
                                'hashtags': str(hashtags),
                                'pic_post': str(pic_post),
                                'name_entities': str(name_entities),
                                'desc_entities': str(desc_entities),
                                'date_entities': str(date_entities),
                                'what_needs_entities': str(what_needs_entities),
                                'status': status,
                                'message_id': message_id
                            }

                    edition_post = get_chat_value_message(message)

                    if await preview(bot, message, edition_post, settings):
                        key = InlineKeyboardMarkup()
                        key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                     callback_data='Вернуться в главное меню'))
                        await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                    else:
                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row('Изменить тему', 'Изменить описание')
                        user_markup.row('Изменить дату', 'Изменить требования')
                        user_markup.row('Изменить сайт проекта')
                        user_markup.row('Изменить твиттер', 'Изменить дискорд')
                        user_markup.row('Изменить баннер', 'Изменить хэштеги')
                        user_markup.row(main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)
                con.close()

        elif get_state(message.chat.id) in [21, 210]:
            '''download photo'''
            edition_post = get_chat_value_message(message)

            src = ''
            if message.text == '/empty':
                edition_post['pic_post'] = ''
            elif message.document:
                file_info = await bot.get_file(message.document.file_id)
                downloaded_file = await bot.download_file(file_info.file_path)

                src = f"data/media/posts_media/pic for post - {edition_post['post_name']}.jpeg"
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file.getvalue())

                edition_post['pic_post'] = src
                await bot.send_message(message.chat.id, 'Изображение загружено.')
            elif message.photo:
                file_info = await bot.get_file(message.photo[-1].file_id)
                downloaded_file = await bot.download_file(file_info.file_path)

                src = f"data/media/posts_media/pic for post - {edition_post['post_name']}.jpeg"
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file.getvalue())

                edition_post['pic_post'] = src
                await bot.send_message(message.chat.id, 'Изображение загружено.')

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute(f"UPDATE posts SET pic_post = '{src}' "
                           f"WHERE post_name = '{str(edition_post['post_name'])}';")
            con.commit()

            if get_state(message.chat.id) == 21:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if edition_post['status']:
                    await edit_post(bot, message, edition_post, settings, 1)
                else:
                    pass

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Изменить тему', 'Изменить описание')
                user_markup.row('Изменить дату', 'Изменить требования')
                user_markup.row('Изменить сайт проекта')
                user_markup.row('Изменить твиттер', 'Изменить дискорд')
                user_markup.row('Изменить баннер', 'Изменить хэштеги')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Баннер поста успешно изменен!', reply_markup=user_markup)
                await log(f"Picture {edition_post['post_name']} is changed by {message.chat.id}")
                set_state(message.chat.id, 13)
            elif get_state(message.chat.id) == 210:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if await preview(bot, message, edition_post, settings):
                    key = InlineKeyboardMarkup()
                    key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)
            con.close()

        elif get_state(message.chat.id) in [22, 220]:
            edition_post = get_chat_value_message(message)

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute(f"UPDATE posts SET hashtags = '{message.text}' "
                           f"WHERE post_name = '{str(edition_post['post_name'])}';")
            con.commit()

            if get_state(message.chat.id) == 22:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if edition_post['status']:
                    await edit_post(bot, message, edition_post, settings, 0)
                else:
                    pass

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Изменить тему', 'Изменить описание')
                user_markup.row('Изменить дату', 'Изменить требования')
                user_markup.row('Изменить сайт проекта')
                user_markup.row('Изменить твиттер', 'Изменить дискорд')
                user_markup.row('Изменить баннер', 'Изменить хэштеги')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Хэштеги успешно изменены!', reply_markup=user_markup)
                await log(f"Hashtags {edition_post['post_name']} is changed by {message.chat.id}")
                set_state(message.chat.id, 13)
            elif get_state(message.chat.id) == 220:
                cursor.execute("SELECT author_name, post_name, post_date, post_desc, what_needs, site, twitter, "
                               "discord, hashtags, pic_post, name_entities, desc_entities, date_entities, "
                               "what_needs_entities, status, message_id "
                               f"FROM posts WHERE post_name = '{str(edition_post['post_name'])}';")

                for author_name, post_name, post_date, post_desc, what_needs, site, twitter, discord, hashtags, \
                    pic_post, name_entities, desc_entities, date_entities, \
                    what_needs_entities, status, message_id in cursor.fetchall():
                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(author_name),
                            'post_name': str(post_name),
                            'post_desc': str(post_desc),
                            'post_date': str(post_date),
                            'what_needs': str(what_needs),
                            'site': str(site),
                            'twitter': str(twitter),
                            'discord': str(discord),
                            'hashtags': str(hashtags),
                            'pic_post': str(pic_post),
                            'name_entities': str(name_entities),
                            'desc_entities': str(desc_entities),
                            'date_entities': str(date_entities),
                            'what_needs_entities': str(what_needs_entities),
                            'status': status,
                            'message_id': message_id
                        }

                edition_post = get_chat_value_message(message)

                if await preview(bot, message, edition_post, settings):
                    key = InlineKeyboardMarkup()
                    key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row('Изменить тему', 'Изменить описание')
                    user_markup.row('Изменить дату', 'Изменить требования')
                    user_markup.row('Изменить сайт проекта')
                    user_markup.row('Изменить твиттер', 'Изменить дискорд')
                    user_markup.row('Изменить баннер', 'Изменить хэштеги')
                    user_markup.row(main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)
            con.close()

        elif get_state(message.chat.id) == 31:
            if message.forward_from:
                new_author(settings, message.forward_from.id, message.forward_from.username)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Добавить нового автора', 'Удалить автора')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Новый автор успешно добавлен', reply_markup=user_markup)
                await log(f'New author {message.forward_from.username} is added by {message.chat.id}')
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Добавить нового автора', 'Удалить автора')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Новый автор не был добавлен\n'
                                                        'Перешлите сообщение пользователя в бота, '
                                                        'чтобы сделать его автором.',
                                       reply_markup=user_markup)

        elif get_state(message.chat.id) == 32:
            author = str(message.text)
            author = author.split(' - ')
            if int(author[0]) in [int(author[0]) for item in get_author_list() if int(author[0]) in item]:
                try:
                    del_id('authors', int(author[0]))
                except:
                    await log('Author was not deleted')
                else:
                    await bot.send_message(message.chat.id, 'Автор успешно удалён из списка')
                    await log(f'The author {message.text} is removed by {message.chat.id}')
                    delete_state(message.chat.id)
            else:
                await bot.send_message(message.chat.id, 'Такого id в списках авторов не обнаружено! '
                                                        'Выберите правильный id!')
                set_state(message.chat.id, 32)

        elif get_state(message.chat.id) == 41:
            if message.forward_from:
                new_admin(message.forward_from.id, message.forward_from.username)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Добавить нового админа', 'Удалить админа')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Новый админ успешно добавлен', reply_markup=user_markup)
                await log(f'New admin {message.forward_from.username} is added by {message.chat.id}')
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Добавить нового админа', 'Удалить админа')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Новый админ не был добавлен\n'
                                                        'Перешлите сообщение пользователя в бота, '
                                                        'чтобы сделать его админом.',
                                       reply_markup=user_markup)

        elif get_state(message.chat.id) == 42:
            admin = str(message.text)
            admin = admin.split(' - ')
            if int(admin[0]) in [int(admin[0]) for item in get_admin_list() if int(admin[0]) in item]:
                try:
                    del_id('admins', int(admin[0]))
                except:
                    await log('Admin was not deleted')
                else:
                    await bot.send_message(message.chat.id, 'Админ успешно удалён из списка')
                    await log(f'The admin {message.text} is removed by {message.chat.id}')
                    delete_state(message.chat.id)
            else:
                await bot.send_message(message.chat.id, 'Такого id в списках админов не обнаружено! '
                                                        'Выберите правильный id!')
                set_state(message.chat.id, 42)

        elif get_state(message.chat.id) == 51:
            if message.forward_from:
                new_moder(message.forward_from.id, message.forward_from.username)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Добавить нового модератора', 'Удалить модератора')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Новый модератор успешно добавлен',
                                       reply_markup=user_markup)
                await log(f'New moder {message.text} is added by {message.chat.id}')
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row('Добавить нового модератора', 'Удалить модератора')
                user_markup.row(main_menu)
                await bot.send_message(message.chat.id, 'Новый модератор не был добавлен\n'
                                                        'Перешлите сообщение пользователя в бота, '
                                                        'чтобы сделать его модератором.',
                                       reply_markup=user_markup)

        elif get_state(message.chat.id) == 52:
            moder = str(message.text)
            moder = moder.split(' - ')
            if int(moder[0]) in [int(moder[0]) for item in get_moder_list() if int(moder[0]) in item]:
                try:
                    del_id('moders', int(moder[0]))
                except:
                    await log('Moder was not deleted')
                else:
                    await bot.send_message(message.chat.id, 'Модератор успешно удалён из списка')
                    await log(f'The moder {message.text} is removed by {message.chat.id}')
                    delete_state(message.chat.id)
            else:
                await bot.send_message(message.chat.id, 'Такого id в списках модеров не обнаружено! '
                                                        'Выберите правильный id!')
                set_state(message.chat.id, 52)

        elif get_state(message.chat.id) == 61:
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(f'Часовой пояс: {settings.time_zone}')
            user_markup.row(f'Название канала: {settings.channel_name}')
            user_markup.row(f'Порог опыта авторам: {settings.threshold_xp}')
            user_markup.row('Изменить выводное сообщение команды /help')
            user_markup.row('Изменить нижнюю подпись для постов')
            user_markup.row('Скачать лог файл')
            user_markup.row(main_menu)

            settings.help_text = message.text
            settings.help_text_entities = message

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute(f"UPDATE phrases SET phrase_text = '{str(message.text)}', "
                           f"phrase_text_entities = '{str(message)}' "
                           f"WHERE phrase = 'help_text';")
            con.commit()
            con.close()

            await bot.send_message(message.chat.id, 'Добавлено новое сообщение помощи', reply_markup=user_markup)
            delete_state(message.chat.id)

        elif get_state(message.chat.id) == 62:
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(f'Часовой пояс: {settings.time_zone}')
            user_markup.row(f'Название канала: {settings.channel_name}')
            user_markup.row(f'Порог опыта авторам: {settings.threshold_xp}')
            user_markup.row('Изменить выводное сообщение команды /help')
            user_markup.row('Изменить нижнюю подпись для постов')
            user_markup.row('Скачать лог файл')
            user_markup.row(main_menu)

            settings.footer_text = message.text
            settings.footer_text_entities = message

            con = sqlite3.connect(files.main_db)
            cursor = con.cursor()
            cursor.execute(f"UPDATE phrases SET phrase_text = '{str(message.text)}', "
                           f"phrase_text_entities = '{str(message)}' "
                           f"WHERE phrase = 'footer_text';")
            con.commit()
            con.close()

            await bot.send_message(message.chat.id, 'Добавлен новый footer', reply_markup=user_markup)
            delete_state(message.chat.id)

        elif get_state(message.chat.id) == 63:
            if message.text.isdigit():
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(f'Часовой пояс: {settings.time_zone}')
                user_markup.row(f'Название канала: {settings.channel_name}')
                user_markup.row(f'Порог опыта авторам: {settings.threshold_xp}')
                user_markup.row('Изменить выводное сообщение команды /help')
                user_markup.row('Изменить нижнюю подпись для постов')
                user_markup.row('Скачать лог файл')
                user_markup.row(main_menu)

                settings.threshold_xp = int(message.text)

                change_settings(settings)

                await bot.send_message(message.chat.id, 'Добавлен новый порог', reply_markup=user_markup)
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(main_menu)

                await bot.send_message(message.chat.id, 'Введите ЧИСЛО', reply_markup=user_markup)


async def admin_inline(bot, callback_query, settings):
    if callback_query.data == 'Вернуться в главное меню':
        if get_state(callback_query.message.chat.id):
            delete_state(callback_query.message.chat.id)
        if get_chat_value_message(callback_query.message):
            delete_chat_value_message(callback_query.message)

        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        user_markup.row('Посты')
        user_markup.row('Списки')
        user_markup.row('Настройки бота')

        # удаляется старое сообщение
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await bot.send_message(callback_query.message.chat.id, 'Вы в главном меню бота.',
                               reply_markup=user_markup)

    elif callback_query.data == 'Есть дата проведения':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        key = InlineKeyboardMarkup()
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Введите дату проведения события или дедлайн',
                               reply_markup=key)

        set_state(callback_query.message.chat.id, 3)

    elif callback_query.data == 'Нет даты проведения':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        set_chat_value_message(callback_query.message, 3)

        key = InlineKeyboardMarkup()
        key.row(InlineKeyboardButton(text='ДА', callback_data='Есть требования'),
                InlineKeyboardButton(text='НЕТ', callback_data='Нет требований'))
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Нужно ли что-то сделать для участия?', reply_markup=key)

    elif callback_query.data == 'Есть требования':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        key = InlineKeyboardMarkup()
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Введите что нужно сделать для участия',
                               reply_markup=key)

        set_state(callback_query.message.chat.id, 4)

    elif callback_query.data == 'Нет требований':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        set_chat_value_message(callback_query.message, 4)

        key = InlineKeyboardMarkup()
        key.row(InlineKeyboardButton(text='ДА', callback_data='Есть сайт'),
                InlineKeyboardButton(text='НЕТ', callback_data='Нет сайта'))
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Есть ли сайт у проекта?', reply_markup=key)

    elif callback_query.data == 'Есть сайт':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        key = InlineKeyboardMarkup()
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Введите ссылку на сайт проекта 🌐\n'
                                                               '(в формате http://example.com)',
                               reply_markup=key)

        set_state(callback_query.message.chat.id, 5)

    elif callback_query.data == 'Нет сайта':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        set_chat_value_message(callback_query.message, 5)

        key = InlineKeyboardMarkup()
        key.row(InlineKeyboardButton(text='ДА', callback_data='Есть твиттер'),
                InlineKeyboardButton(text='НЕТ', callback_data='Нет твиттера'))
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Есть ли твиттер у проекта?', reply_markup=key)

    elif callback_query.data == 'Есть твиттер':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        key = InlineKeyboardMarkup()
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Введите ссылку на твиттер проекта 🐦\n'
                                                               '(в формате http://example.com)',
                               reply_markup=key)

        set_state(callback_query.message.chat.id, 6)

    elif callback_query.data == 'Нет твиттера':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        set_chat_value_message(callback_query.message, 6)

        key = InlineKeyboardMarkup()
        key.row(InlineKeyboardButton(text='ДА', callback_data='Есть дискорд'),
                InlineKeyboardButton(text='НЕТ', callback_data='Нет дискорда'))
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Есть ли дискорд у проекта?', reply_markup=key)

    elif callback_query.data == 'Есть дискорд':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        key = InlineKeyboardMarkup()
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Введите ссылку на дискорд проекта 👾\n'
                                                               '(в формате http://example.com)',
                               reply_markup=key)

        set_state(callback_query.message.chat.id, 7)

    elif callback_query.data == 'Нет дискорда':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        set_chat_value_message(callback_query.message, 7)

        key = InlineKeyboardMarkup()
        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                     callback_data='Вернуться в главное меню'))
        await bot.send_message(callback_query.message.chat.id, 'Важное напоминание!!! '
                                                               'Определитесь, будет ли в нём картинка.'
                                                               'Если вы не добавите картинку сразу, '
                                                               'то потом вы её не сможете уже добавить, '
                                                               'и если картинка уже была,'
                                                               'то вы не сможете её убрать!')
        await bot.send_message(callback_query.message.chat.id, 'Вставьте баннер (изображение) поста.'
                                                               'Или если нет баннера, то пропишите /empty.',
                               reply_markup=key)

        set_state(callback_query.message.chat.id, 8)

    elif callback_query.data == 'Редактировать пост':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        user_markup.row('Изменить тему', 'Изменить описание')
        user_markup.row('Изменить дату', 'Изменить требования')
        user_markup.row('Изменить сайт проекта')
        user_markup.row('Изменить твиттер', 'Изменить дискорд')
        user_markup.row('Изменить баннер', 'Изменить хэштеги')
        user_markup.row(main_menu)
        await bot.send_message(callback_query.message.chat.id, 'Теперь выберите, что хотите изменить',
                               reply_markup=user_markup)
        set_state(callback_query.message.chat.id, 130)

    elif callback_query.data == 'Подтвердить пост':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

        await bot.send_message(callback_query.message.chat.id,
                               "В качестве подтверждения размещения поста сейчас напишите 'Да'. "
                               "Если не хотите размещать пост сейчас - напишите что-нибудь другое")
        set_state(callback_query.message.chat.id, 10)

    elif callback_query.data == 'Разместить пост':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        entity_list = []
        unposted_post = get_chat_value_message(callback_query.message)
        text = f"{unposted_post['post_name']}\n\n" \
               f"{unposted_post['post_desc']}\n\n"

        if unposted_post['what_needs'] != '':
            text += f"✅ {unposted_post['what_needs']}\n\n"

        if unposted_post['post_date'] != '':
            text += f"📆 {unposted_post['post_date']}\n\n"

        if unposted_post['site'] != '' or unposted_post['twitter'] != '' or unposted_post['discord'] != '':
            text += "🔗 "
            if unposted_post['site'] != '':
                text += "Сайт проекта "
            if unposted_post['twitter'] != '':
                if unposted_post['site'] == '':
                    text += "Twitter "
                else:
                    text += "| Twitter "
            if unposted_post['discord'] != '':
                if unposted_post['site'] == '' and unposted_post['twitter'] == '':
                    text += "Discord"
                else:
                    text += "| Discord"
            text += "\n\n"

        text += f"{unposted_post['hashtags']}\n\n" \
                f"Автор: @{unposted_post['author_name']}\n" \
                f"{settings.footer_text}"

        name_entities = json.loads(str(unposted_post['name_entities']))
        description_entities = json.loads(str(unposted_post['desc_entities']))
        date_entities = json.loads(str(unposted_post['date_entities']))
        what_needs_entities = json.loads(str(unposted_post['what_needs_entities']))
        footer_text_entities = json.loads(settings.footer_text_entities)

        if type(unposted_post['pic_post']) is tuple:
            if unposted_post['pic_post'][0] == '':
                text_format_char = 4096
            else:
                text_format_char = 1024
        else:
            if unposted_post['pic_post'] == '':
                text_format_char = 4096
            else:
                text_format_char = 1024

        count_string_track = 0

        entity = MessageEntity(type="bold",
                               offset=count_string_track,
                               length=len(unposted_post['post_name']))
        entity_list.append(entity)

        if "entities" in name_entities:

            for entity in name_entities["entities"]:
                entity_values_list = list(entity.values())

                if entity["type"] == "text_link":
                    entity = MessageEntity(type=entity_values_list[0],
                                           offset=count_string_track + entity_values_list[1],
                                           length=entity_values_list[2], url=entity_values_list[3])
                    entity_list.append(entity)
                elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                        "email", "phone_number", "bold", "italic", "underline",
                                        "strikethrough", "code"]:
                    entity = MessageEntity(type=entity_values_list[0],
                                           offset=count_string_track + entity_values_list[1],
                                           length=entity_values_list[2])
                    entity_list.append(entity)

        count_string_track += len(str(unposted_post['post_name'])) + 2

        if "entities" in description_entities:

            for entity in description_entities["entities"]:
                entity_values_list = list(entity.values())

                if entity["type"] == "text_link":
                    entity = MessageEntity(type=entity_values_list[0],
                                           offset=count_string_track + entity_values_list[1],
                                           length=entity_values_list[2], url=entity_values_list[3])
                    entity_list.append(entity)
                elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                        "email", "phone_number", "bold", "italic", "underline",
                                        "strikethrough", "code"]:
                    entity = MessageEntity(type=entity_values_list[0],
                                           offset=count_string_track + entity_values_list[1],
                                           length=entity_values_list[2])
                    entity_list.append(entity)

        count_string_track += len(str(unposted_post['post_desc']))

        if unposted_post['what_needs'] != '':
            count_string_track += len(str('\n\n✅ '))

            if "entities" in what_needs_entities:

                for entity in what_needs_entities["entities"]:
                    entity_values_list = list(entity.values())

                    if entity["type"] == "text_link":
                        entity = MessageEntity(type=entity_values_list[0],
                                               offset=count_string_track + entity_values_list[1],
                                               length=entity_values_list[2], url=entity_values_list[3])
                        entity_list.append(entity)
                    elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                            "email", "phone_number", "bold", "italic", "underline",
                                            "strikethrough", "code"]:
                        entity = MessageEntity(type=entity_values_list[0],
                                               offset=count_string_track + entity_values_list[1],
                                               length=entity_values_list[2])
                        entity_list.append(entity)

            count_string_track += len(str(unposted_post['what_needs']))

        if unposted_post['post_date'] != '':
            count_string_track += len(str('\n\n📆 '))

            if "entities" in date_entities:

                for entity in date_entities["entities"]:
                    entity_values_list = list(entity.values())

                    if entity["type"] == "text_link":
                        entity = MessageEntity(type=entity_values_list[0],
                                               offset=count_string_track + entity_values_list[1],
                                               length=entity_values_list[2], url=entity_values_list[3])
                        entity_list.append(entity)
                    elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                            "email", "phone_number", "bold", "italic", "underline",
                                            "strikethrough", "code"]:
                        entity = MessageEntity(type=entity_values_list[0],
                                               offset=count_string_track + entity_values_list[1],
                                               length=entity_values_list[2])
                        entity_list.append(entity)

            count_string_track += len(str(unposted_post['post_date'])) + 1

        if unposted_post['site'] != '' or unposted_post['twitter'] != '' or unposted_post['discord'] != '':
            count_string_track += len("\n\n🔗 ") + 1
            if unposted_post['site'] != '':
                entity = MessageEntity(type="text_link",
                                       offset=count_string_track,
                                       length=len("Сайт проекта"),
                                       url=f"{unposted_post['site']}")
                entity_list.append(entity)
                count_string_track += len("Сайт проекта ")
            if unposted_post['twitter'] != '':
                if unposted_post['site'] == '':
                    entity = MessageEntity(type="text_link",
                                           offset=count_string_track,
                                           length=len("Twitter"),
                                           url=f"{unposted_post['twitter']}")
                    entity_list.append(entity)
                    count_string_track += len("Twitter ")
                else:
                    entity = MessageEntity(type="text_link",
                                           offset=count_string_track + 2,
                                           length=len("Twitter"),
                                           url=f"{unposted_post['twitter']}")
                    entity_list.append(entity)
                    count_string_track += len("| Twitter ")
            if unposted_post['discord'] != '':
                if unposted_post['site'] == '' and unposted_post['twitter'] == '':
                    entity = MessageEntity(type="text_link",
                                           offset=count_string_track,
                                           length=len("Discord"),
                                           url=f"{unposted_post['discord']}")
                    entity_list.append(entity)
                    count_string_track += len("Discord")
                else:
                    entity = MessageEntity(type="text_link",
                                           offset=count_string_track + 2,
                                           length=len("Discord"),
                                           url=f"{unposted_post['discord']}")
                    entity_list.append(entity)
                    count_string_track += len("| Discord")
            count_string_track += len("\n\n")

        count_string_track += len(str(unposted_post['hashtags'])) + 2

        entity = MessageEntity(type="italic",
                               offset=count_string_track,
                               length=len('Автор'))
        entity_list.append(entity)

        count_string_track += len(f"Автор: @{unposted_post['author_name']}\n")

        if "entities" in footer_text_entities:

            for entity in footer_text_entities["entities"]:
                entity_values_list = list(entity.values())

                if entity["type"] == "text_link":
                    entity = MessageEntity(type=entity_values_list[0],
                                           offset=count_string_track + entity_values_list[1],
                                           length=entity_values_list[2], url=entity_values_list[3])
                    entity_list.append(entity)
                elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                        "email", "phone_number", "bold", "italic", "underline",
                                        "strikethrough", "code"]:
                    entity = MessageEntity(type=entity_values_list[0],
                                           offset=count_string_track + entity_values_list[1],
                                           length=entity_values_list[2])
                    entity_list.append(entity)

        if type(unposted_post['pic_post']) is tuple:
            if unposted_post['pic_post'][0] == '':
                message_result = await bot.send_message(settings.channel_name, text, entities=entity_list)
            else:
                photo = open(unposted_post['pic_post'][0], 'rb')
                message_result = await bot.send_photo(settings.channel_name,
                                                      photo, caption=text, caption_entities=entity_list)
        else:
            if unposted_post['pic_post'] == '':
                message_result = await bot.send_message(settings.channel_name, text, entities=entity_list)
            else:
                photo = open(unposted_post['pic_post'], 'rb')
                message_result = await bot.send_photo(settings.channel_name,
                                                      photo, caption=text, caption_entities=entity_list)

        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        user_markup.row('Посты')
        user_markup.row('Списки')
        user_markup.row('Настройки бота')
        await bot.send_message(callback_query.message.chat.id, 'Пост был размещен на канале.', reply_markup=user_markup)

        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute(f"UPDATE posts SET status = 1, message_id = {str(message_result.message_id)} "
                       f"WHERE post_name = '{str(unposted_post['post_name'])}';")
        con.commit()
        con.close()

        delete_chat_value_message(callback_query.message)

        delete_state(callback_query.message.chat.id)

    elif callback_query.data == 'Вернуться в меню размещения':
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT post_name, status FROM posts;")
        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        a = 0
        for post_name, status in cursor.fetchall():
            if status:
                pass
            else:
                a += 1
                user_markup.row(str(post_name))
        if a == 0:
            await bot.send_message(callback_query.message.chat.id, 'Не размещенных постов нет!',
                                   reply_markup=user_markup)
        else:
            user_markup.row(main_menu)
            await bot.send_message(callback_query.message.chat.id, 'Какой пост хотите разместить?',
                                   parse_mode='Markdown', reply_markup=user_markup)
            set_state(callback_query.message.chat.id, 90)

        delete_chat_value_message(callback_query.message)
        con.close()
