# IDEA: сделать также изменение фразы для команды /start
import logging
from logging.handlers import RotatingFileHandler
import shelve
import os

from aiogram import Bot
from aiogram.utils.json import json

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, \
    InlineKeyboardButton, MessageEntity, Message, CallbackQuery, ReplyKeyboardRemove
import validators

import files
from extensions import Settings, SUPER_ADMIN_ID, TOTAL_RETRIES, \
    CONNECT_RETRY, TIME_BETWEEN_ATTEMPTS, TIME_FOR_CONNECT, TIME_DATA_REC, Menu
from models import Author, Admin, Post, BlockedUser, Phrase, User
from defs import get_admin_list, log, new_admin, get_state, del_id, get_moder_list, new_moder, \
    get_author_list, new_author, get_csv, delete_state, set_state, preview, edit_post, change_settings, \
    set_chat_value_message, delete_chat_value_message, get_chat_value_message, \
    get_blocked_user_list, new_blocked_user, \
    emoji_count, entity_read, find_emoji, add_emoji_as_pattern


# Create handlers
console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(files.system_log, mode='a',
                                   maxBytes=2048000, backupCount=2,
                                   encoding='utf-8', delay=True)


logging.basicConfig(
    format="%(asctime)s::[%(levelname)s]::%(name)s::(%(filename)s).%(funcName)s(%(lineno)d)::%(message)s",
    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO, handlers=(file_handler, console_handler)
)


async def panel(settings: Settings, bot: Bot, message: Message) -> None:
    current_user = object

    for table in [Admin, Author, BlockedUser]:
        for obj in table.select():
            if obj.profile.user_id == message.chat.id:
                current_user = obj
                break

    if isinstance(current_user, BlockedUser):
        await bot.send_message(message.chat.id, "Вы были заблокированы администратором бота!")
        delete_state(message.chat.id)
    elif isinstance(current_user, (Admin, Author)) or message.chat.id == SUPER_ADMIN_ID:
        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        user_markup.row(Menu.posts)
        user_markup.row(Menu.lists)

        if current_user.permissions == 'admin_permissions' or message.chat.id == SUPER_ADMIN_ID:
            user_markup.row(Menu.settings)

            await bot.send_message(message.chat.id, f"Привет, Админ {message.chat.username}!\n",
                                   reply_markup=ReplyKeyboardRemove())
            await bot.send_message(message.chat.id, "Я HareGems-бот!\n"
                                                    "При помощи меня можно создать пост для канала "
                                                    "HareCrypta - Лаборатория Идей!\n"
                                                    "По команде /help можно получить "
                                                    "дополнительную информацию")
            await log(settings, f'Admin {message.chat.id} started bot')
        elif current_user.permissions == 'moder_permissions':
            await bot.send_message(message.chat.id, f"Привет, Модератор {message.chat.username}!")
            await bot.send_message(message.chat.id, "Я HareGems-бот!\n"
                                                    "При помощи меня можно создать пост для канала "
                                                    "HareCrypta - Лаборатория Идей!\n"
                                                    "По команде /help можно получить "
                                                    "дополнительную информацию")
            await log(settings, f'Moder {message.chat.id} started bot')
        elif current_user.permissions == 'author_permissions':
            await bot.send_message(message.chat.id, f"Привет, Автор {message.chat.username}!")
            await bot.send_message(message.chat.id, "Я HareGems-бот!\n"
                                                    "При помощи меня можно создать пост для канала "
                                                    "HareCrypta - Лаборатория Идей!\n"
                                                    "По команде /help можно получить "
                                                    "дополнительную информацию")
            await log(settings, f'Author {message.chat.id} started bot')

        await bot.send_message(message.chat.id, "Добро пожаловать в панель управления.", reply_markup=user_markup)

        await log(settings, f'Launch bot panel by user {message.chat.id}')
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


async def in_bot_panel(bot: Bot, settings: Settings, message: Message) -> None:
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

    При размещении постов учитываются состояния 90:
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

    При настройке бота - состояние 61, 62, 63, 65:
    61 - изменений выводной фразы по команде /help
    62 - изменение нижней подписи к постам
    63 - изменение порога опыта для авторов
    65 - восстановление бд из резервной копии


    :param bot: Bot from aiogram
    :param settings: object class: Settings from extensions.py
    :param message: types.Message from aiogram
    :return: None
    """

    if get_state(message.chat.id) == 55 and message.chat.id == SUPER_ADMIN_ID:
        if 'https://combot.org/api/one_time_auth?hash=' in message.text:
            settings.url_one_time_link = message.text
            settings.set_session_settings(
                total_retries=TOTAL_RETRIES,
                connect_retry=CONNECT_RETRY,
                time_between_attempts=TIME_BETWEEN_ATTEMPTS,
                time_for_connect=TIME_FOR_CONNECT,
                time_for_data_rec=TIME_DATA_REC,
            )

            try:
                settings.session.get(
                    settings.url_one_time_link,
                    timeout=(settings.time_for_connect, settings.time_for_data_rec)
                )
            except Exception as e:
                logging.error(e)
            else:
                if await get_csv(bot, settings):
                    logging.info('Session was opened')
                    delete_state(SUPER_ADMIN_ID)

                    await bot.send_message(SUPER_ADMIN_ID, 'Спасибо, данные были обновлены.')
        else:
            await bot.send_message(SUPER_ADMIN_ID, 'Сначала введите ссылку для получения доступа к csv файлу.')
            return

    current_user = object

    for table in [Admin, Author, BlockedUser]:
        for obj in table.select():
            if obj.profile.user_id == message.chat.id:
                current_user = obj
                break

    if isinstance(current_user, BlockedUser):
        await bot.send_message(message.chat.id, "Вы были заблокированы администратором бота!")
        delete_state(message.chat.id)
    elif isinstance(current_user, (Admin, Author)) or message.chat.id == SUPER_ADMIN_ID:
        if message.text == Menu.main_menu:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id):
                delete_state(message.chat.id)
            if get_chat_value_message(message.chat.id):
                delete_chat_value_message(message.chat.id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.posts)
            user_markup.row(Menu.lists)
            if current_user.permissions == 'admin_permissions':
                user_markup.row(Menu.settings)

            await bot.send_message(message.chat.id, 'Вы в главном меню бота.',
                                   reply_markup=user_markup)

        elif message.text == Menu.posts:
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.MenuPosts.add_new_post, Menu.MenuPosts.delete_post)
            user_markup.row(Menu.MenuPosts.edit_post, Menu.MenuPosts.posting)
            user_markup.row(Menu.main_menu)

            entity_list = []
            count_string_track = len('Созданные посты:\n\n')
            result_text = 'Созданные посты:\n\n'
            a = 0

            try:
                if isinstance(current_user, Author):
                    posts = Post.select().where(Post.author == current_user.profile)
                else:
                    posts = Post.select()
            except Exception as e:
                logging.exception(e)
            else:
                for post in posts:
                    a += 1
                    count_string_track += len(str(a)) + 2
                    name_entities = json.loads(str(post.name_entities))

                    if "entities" in name_entities:
                        entity_list = entity_read(name_entities, entity_list, count_string_track)

                    count_string_track += len(post.post_name) + 3 + emoji_count(str(post.post_name))

                    count_string_track += len(post.author.username) + 3 + \
                                          len('Posted' if post.status else 'Not posted') + 1

                    result_text += str(a) + '. ' + str(post.post_name) + ' - ' + \
                                   str(post.author.username) + \
                                   ' - ' + str('Posted' if post.status else 'Not posted') + '\n'

                    if a % 20 == 0:
                        await bot.send_message(
                            message.chat.id,
                            result_text,
                            reply_markup=user_markup,
                            entities=entity_list)
                        entity_list = []
                        count_string_track = len('Созданные посты:\n\n')
                        result_text = 'Созданные посты:\n\n'

            if a == 0:
                result_text = "Посты не созданы!"
            else:
                pass

            await bot.send_message(message.chat.id, result_text, reply_markup=user_markup, entities=entity_list)

        elif message.text == Menu.MenuPosts.add_new_post:
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.main_menu)

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
                                        "strikethrough", "code", "pre"]:
                    entity = MessageEntity(type=entity["type"],
                                           offset=entity["offset"],
                                           length=entity["length"])
                    example_entities.append(entity)

            photo = open(files.photo_example, 'rb')
            await bot.send_photo(message.chat.id, photo, caption=example_text, caption_entities=example_entities)

            await bot.send_message(message.chat.id,
                                   'Порядок заполнения данных поста: \n'
                                   '- ввод темы поста (обязательно)\n'
                                   '- ввод описания поста (обязательно)\n'
                                   '- *ввод даты проведения или дедлайна (необязательно)\n'
                                   '- *ввод требований к участию (необязательно)\n'
                                   '- **ввод сайта, **ввод твиттера, **ввод дискорда\n'
                                   '- выбор баннера поста '
                                   '((прикрепляете как документ или как картинку (сжатие изображения), '
                                   'если баннера нет, то ввести команду /empty))\n'
                                   '- ввод хэштегов (обязательно)\n\n'
                                   '* - обязательно сделать выбор (нажать инлайн кнопку "Да" или "Нет")\n'
                                   '** - кроме обязательного выбора нужно также '
                                   'учитывать формат вводимых данных (если это сайт, то http://example.com)'
                                   )

            await bot.send_message(message.chat.id, 'Введите тему поста', reply_markup=user_markup)
            set_state(message.chat.id, 1)

        elif message.text == Menu.MenuPosts.posting:
            await bot.delete_message(message.chat.id, message.message_id)

            try:
                if isinstance(current_user, Author):
                    posts = Post.select().where(Post.author == current_user.profile)
                else:
                    posts = Post.select()
            except Exception as e:
                logging.warning(e)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                a = 0
                for post in posts:
                    if not post.status:
                        a += 1
                        user_markup.row(str(post.post_name))

                if a == 0:
                    await bot.send_message(message.chat.id, 'Не размещенных постов нет!', reply_markup=user_markup)
                else:
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Какой пост хотите разместить?',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    set_state(message.chat.id, 90)

        elif message.text == Menu.MenuPosts.edit_post:
            await bot.delete_message(message.chat.id, message.message_id)

            try:
                if isinstance(current_user, Author):
                    posts = Post.select().where(Post.author == current_user.profile)
                else:
                    posts = Post.select()
            except Exception as e:
                logging.warning(e)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                a = 0
                for post in posts:
                    a += 1
                    user_markup.row(str(post.post_name))
                if a == 0:
                    await bot.send_message(message.chat.id, 'Никаких постов ещё не создано!', reply_markup=user_markup)
                else:
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Какой пост хотите редактировать?',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    set_state(message.chat.id, 12)

        elif message.text == Menu.back:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [14, 15, 16, 17, 18, 19, 20, 21, 22]:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                user_markup.row(Menu.main_menu)
                await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                       reply_markup=user_markup)
                set_state(message.chat.id, 13)
            elif get_state(message.chat.id) in [140, 150, 160, 170, 180, 190, 200, 210, 220]:
                edition_post = get_chat_value_message(message.chat.id)

                if await preview(bot, message, edition_post, settings):
                    key = InlineKeyboardMarkup()
                    key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                            InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                    key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                 callback_data='Вернуться в главное меню'))
                    await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                else:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)

        elif message.text == Menu.MenuPosts.EditMenu.edit_name:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message.chat.id)
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.back)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Введите новую тему поста',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 14)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 140)
                else:
                    await bot.send_message(message.chat.id, 'Поста с такой темой нет!\nВыберите заново!')

        elif message.text == Menu.MenuPosts.EditMenu.edit_desc:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message.chat.id)
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.back)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Введите новое описание поста',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 15)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 150)
                else:
                    await bot.send_message(message.chat.id, 'Поста с таким описанием нет!\nВыберите заново!')

        elif message.text == Menu.MenuPosts.EditMenu.edit_date:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message.chat.id)
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.back)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Введите новую дату поста '
                                                            'или введите /empty, чтобы удалить содержимое',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 16)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 160)
                else:
                    await bot.send_message(message.chat.id, 'Поста с такой датой нет!\nВыберите заново!')

        elif message.text == Menu.MenuPosts.EditMenu.edit_needs:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message.chat.id)
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.back)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Введите что нужно сделать для участия '
                                                            'или введите /empty, чтобы удалить содержимое',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 17)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 170)
                else:
                    await bot.send_message(message.chat.id, 'Поста с такими требованиями нет!\nВыберите заново!')

        elif message.text == Menu.MenuPosts.EditMenu.edit_site:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message.chat.id)
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.back)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Введите новый сайт проекта '
                                                            'или введите /empty, чтобы удалить содержимое',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 18)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 180)
                else:
                    await bot.send_message(message.chat.id, 'Поста с такими сайтом нет!\nВыберите заново!')

        elif message.text == Menu.MenuPosts.EditMenu.edit_twitter:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message.chat.id)
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.back)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Введите новый твиттер проекта '
                                                            'или введите /empty, чтобы удалить содержимое',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 19)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 190)
                else:
                    await bot.send_message(message.chat.id, 'Поста с такими твиттером нет!\nВыберите заново!')

        elif message.text == Menu.MenuPosts.EditMenu.edit_discord:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message.chat.id)
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.back)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Введите новый дискорд проекта '
                                                            'или введите /empty, чтобы удалить содержимое',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 20)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 200)
                else:
                    await bot.send_message(message.chat.id, 'Поста с такими дискордом нет!\nВыберите заново!')

        elif message.text == Menu.MenuPosts.EditMenu.edit_banner:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message.chat.id)
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.back)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Вставьте баннер (изображение) поста.'
                                                            'Или если нет баннера, то пропишите /empty',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 21)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 210)
                else:
                    await bot.send_message(message.chat.id, 'Поста с таким баннером нет!\nВыберите заново!')

        elif message.text == Menu.MenuPosts.EditMenu.edit_hashtags:
            await bot.delete_message(message.chat.id, message.message_id)
            if get_state(message.chat.id) in [13, 130]:
                edition_post = get_chat_value_message(message.chat.id)
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.back)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Введите новые хэштеги',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    if get_state(message.chat.id) == 13:
                        set_state(message.chat.id, 22)
                    elif get_state(message.chat.id) == 130:
                        set_state(message.chat.id, 220)
                else:
                    await bot.send_message(message.chat.id, 'Поста с такими хэштегами нет!\nВыберите заново!')

        elif message.text == Menu.MenuPosts.delete_post:
            await bot.delete_message(message.chat.id, message.message_id)

            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            a = 0
            try:
                if isinstance(current_user, Author):
                    posts = Post.select().where(Post.author == current_user.profile)
                else:
                    posts = Post.select()
            except Exception as e:
                logging.warning(e)
            else:
                for post in posts:
                    a += 1
                    user_markup.row(str(post.post_name))
                if a == 0:
                    await bot.send_message(message.chat.id, 'Никаких постов ещё не создано!', reply_markup=user_markup)
                else:
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Какой пост нужно удалить?',
                                           parse_mode='Markdown', reply_markup=user_markup)
                    set_state(message.chat.id, 11)

        elif message.text == Menu.lists:
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.ListsMenu.authors_list, Menu.ListsMenu.blocked_authors_lists)
            user_markup.row(Menu.ListsMenu.moders_lists, Menu.ListsMenu.admins_lists)
            user_markup.row(Menu.main_menu)

            await bot.send_message(message.chat.id, "Выберите список для отображения", reply_markup=user_markup)

        elif message.text == Menu.ListsMenu.authors_list:
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            if isinstance(current_user, Admin):
                user_markup.row(Menu.ListsMenu.AuthorMenu.add_new, Menu.ListsMenu.AuthorMenu.delete)
            user_markup.row(Menu.main_menu)
            a = 0

            authors = "Список авторов:\n\n"
            if len(get_author_list()) != 0:
                for author in get_author_list():
                    a += 1
                    authors += f"{a}. {author[0]} - @{author[1]} - {author[2]} XP\n"

                    if a % 50 == 0:
                        await bot.send_message(message.chat.id, authors, reply_markup=user_markup, parse_mode="HTML")
                        authors = ''

                await bot.send_message(message.chat.id, authors, reply_markup=user_markup, parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id, "Авторов еще нет", reply_markup=user_markup)

        elif message.text == Menu.ListsMenu.AuthorMenu.add_new:
            if isinstance(current_user, Admin):
                await bot.delete_message(message.chat.id, message.message_id)
                key = InlineKeyboardMarkup()
                key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                             callback_data='Вернуться в главное меню'))
                await bot.send_message(message.chat.id, 'Перешлите любое сообщение от пользователя,'
                                                        'которого хотите сделать автором', reply_markup=key)
                set_state(message.chat.id, 31)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.ListsMenu.AuthorMenu.delete:
            if isinstance(current_user, Admin):
                await bot.delete_message(message.chat.id, message.message_id)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                a = 0
                for author in get_author_list():
                    a += 1
                    user_markup.row(f"{author[0]} - @{author[1]} - {author[2]} XP\n")
                if a == 0:
                    await bot.send_message(message.chat.id, 'Вы ещё не добавляли авторов!')
                else:
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Выбери автора, которого нужно удалить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 32)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.ListsMenu.blocked_authors_lists:
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.main_menu)
            a = 0

            authors = "Удалённые авторы:\n\n"
            if len(get_blocked_user_list()) != 0:
                for author in get_blocked_user_list():
                    a += 1
                    authors += f"{a}. {author[0]} - {author[1]} - @{author[2]}\n"

                    if a % 50 == 0:
                        await bot.send_message(message.chat.id, authors, reply_markup=user_markup, parse_mode="HTML")
                        authors = ''

                await bot.send_message(message.chat.id, authors, reply_markup=user_markup, parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id, "Удалённых авторов еще нет", reply_markup=user_markup)

        elif message.text == Menu.ListsMenu.admins_lists:
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            if isinstance(current_user, Admin):
                user_markup.row(Menu.ListsMenu.AdminMenu.add_new, Menu.ListsMenu.AdminMenu.delete)
            user_markup.row(Menu.main_menu)
            a = 0

            admins = "Список админов:\n\n"
            if len(get_admin_list()) != 0:
                for admin in get_admin_list():
                    a += 1
                    admins += f"{a}. {admin[0]} - @{admin[1]}\n"

                    if a % 50 == 0:
                        await bot.send_message(message.chat.id, admins, reply_markup=user_markup, parse_mode="HTML")
                        admins = ''

                await bot.send_message(message.chat.id, admins, reply_markup=user_markup, parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id, "Админов еще нет", reply_markup=user_markup)

        elif message.text == Menu.ListsMenu.AdminMenu.add_new:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)
                key = InlineKeyboardMarkup()
                key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                             callback_data='Вернуться в главное меню'))
                await bot.send_message(message.chat.id, 'Перешлите любое сообщение от пользователя,'
                                                        'которого хотите сделать админом', reply_markup=key)
                set_state(message.chat.id, 41)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.ListsMenu.AdminMenu.delete:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                a = 0
                for admin in get_admin_list():
                    a += 1
                    if int(admin[0]) != SUPER_ADMIN_ID: user_markup.row(f"{str(admin[0])} - {admin[1]}")
                if a == 0:
                    await bot.send_message(message.chat.id, 'Вы ещё не добавляли админов!')
                else:
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Выбери админа, которого нужно удалить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 42)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.ListsMenu.moders_lists:
            await bot.delete_message(message.chat.id, message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            if isinstance(current_user, Admin):
                user_markup.row(Menu.ListsMenu.ModerMenu.add_new, Menu.ListsMenu.ModerMenu.delete)
            user_markup.row(Menu.main_menu)
            a = 0

            moders = "Список модераторов:\n\n"
            if len(get_moder_list()) != 0:
                for moder in get_moder_list():
                    a += 1
                    moders += f"{a}. {moder[0]} - @{moder[1]}\n"

                    if a % 50 == 0:
                        await bot.send_message(message.chat.id, moders, reply_markup=user_markup, parse_mode="HTML")
                        moders = ''

                await bot.send_message(message.chat.id, moders, reply_markup=user_markup, parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id, "Модераторов еще нет", reply_markup=user_markup)

        elif message.text == Menu.ListsMenu.ModerMenu.add_new:
            if isinstance(current_user, Admin):
                await bot.delete_message(message.chat.id, message.message_id)
                key = InlineKeyboardMarkup()
                key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                             callback_data='Вернуться в главное меню'))
                await bot.send_message(message.chat.id, 'Перешлите сообщение пользователя в бота, '
                                                        'чтобы сделать его модератором.', reply_markup=key)
                set_state(message.chat.id, 51)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.ListsMenu.ModerMenu.delete:
            if isinstance(current_user, Admin):
                await bot.delete_message(message.chat.id, message.message_id)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                a = 0
                for moder in get_moder_list():
                    a += 1
                    user_markup.row(f'{str(moder[0])} - {moder[1]}')
                if a == 0:
                    await bot.send_message(message.chat.id, 'Вы ещё не добавляли модераторов!')
                else:
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Выбери id модератора, которого нужно удалить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 52)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.settings:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)

                user_markup.row(Menu.Settings.time_zone_text + str(settings.time_zone))
                user_markup.row(Menu.Settings.channel_name_text + str(settings.channel_name))
                user_markup.row(Menu.Settings.threshold_xp_text + str(settings.threshold_xp))
                user_markup.row(Menu.Settings.help_edit_text)
                user_markup.row(Menu.Settings.footer_edit_text)
                user_markup.row(Menu.Settings.log_files_download_text)
                user_markup.row(Menu.Settings.copy_db_download_text)
                user_markup.row(Menu.Settings.create_copy_db_text)
                user_markup.row(Menu.Settings.restore_db_text)
                user_markup.row(Menu.Settings.check_emoji_text)
                user_markup.row(Menu.Settings.bad_emoji_text)
                user_markup.row(Menu.main_menu)

                await bot.send_message(message.chat.id, "Вы вошли в настройки бота", reply_markup=user_markup,
                                       parse_mode="HTML")
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.Settings.help_edit_text:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.main_menu)
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
                        elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                                "email", "phone_number", "bold", "italic", "underline",
                                                "strikethrough", "code", "pre"]:
                            entity = MessageEntity(type=entity_values_list[0],
                                                   offset=entity_values_list[1],
                                                   length=entity_values_list[2])
                        help_entities.append(entity)

                await bot.send_message(message.chat.id, "На данный момент сообщение help такое:")
                await bot.send_message(message.chat.id, help_text, entities=help_entities, reply_markup=user_markup)
                await bot.send_message(message.chat.id, "Введите новое сообщение для команды help:")

                set_state(message.chat.id, 61)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.Settings.footer_edit_text:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.main_menu)
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
                        elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                                "email", "phone_number", "bold", "italic", "underline",
                                                "strikethrough", "code", "pre"]:
                            entity = MessageEntity(type=entity_values_list[0],
                                                   offset=entity_values_list[1],
                                                   length=entity_values_list[2])
                        footer_entities.append(entity)

                await bot.send_message(message.chat.id, "На данный момент footer такой:")
                await bot.send_message(message.chat.id, footer_text, entities=footer_entities, reply_markup=user_markup)
                await bot.send_message(message.chat.id, "Введите новый footer:")

                set_state(message.chat.id, 62)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif isinstance(message.text, str) and Menu.Settings.threshold_xp_text in message.text:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)

                user_markup.row(Menu.main_menu)

                await bot.send_message(message.chat.id, "Введите новый порог для авторов"
                                                        " (только число)", reply_markup=user_markup)
                set_state(message.chat.id, 63)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.Settings.log_files_download_text:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)
                with open(files.working_log, 'rb') as working_log:
                    await bot.send_document(message.chat.id, working_log)
                with open(files.system_log, 'rb') as system_log:
                    await bot.send_document(message.chat.id, system_log)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.Settings.copy_db_download_text:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)
                try:
                    with open(files.reserve_db, 'rb') as database:
                        await bot.send_document(message.chat.id, database)
                except Exception as e:
                    logging.warning(e)
                    await bot.send_message(message.chat.id, 'Сначала создайте резервную копию БД')
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.Settings.create_copy_db_text:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)
                try:
                    with open(files.main_db, 'rb') as db:
                        db_bytes = db.read()
                        with open(files.reserve_db, 'wb') as rdb:
                            rdb.write(db_bytes)
                except Exception as e:
                    logging.error(e)
                    await bot.send_message(message.chat.id, "Ошибка при создании резервной копии")
                else:
                    await bot.send_message(message.chat.id, "Резервная копия создана")
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")
        elif message.text == Menu.Settings.restore_db_text:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)

                dir_name = os.path.join(os.path.dirname(__file__), 'data\\db\\reserve')
                db_reserve_list = os.listdir(dir_name)
                for copy in db_reserve_list:
                    user_markup.row(copy)
                user_markup.row(Menu.main_menu)

                await bot.send_message(message.chat.id,
                                       "Выберите копию для восстановления", reply_markup=user_markup)
                set_state(message.chat.id, 65)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.Settings.bad_emoji_text:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.main_menu)

                await bot.send_message(message.chat.id, "Вставьте эмоджи, "
                                                        "который смещает форматирование текста",
                                       reply_markup=user_markup)
                set_state(message.chat.id, 71)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif message.text == Menu.Settings.check_emoji_text:
            if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                await bot.delete_message(message.chat.id, message.message_id)

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.main_menu)

                await bot.send_message(message.chat.id, "Вставьте эмоджи, "
                                                        "который хотите проверить",
                                       reply_markup=user_markup)
                set_state(message.chat.id, 70)
            else:
                await bot.send_message(message.chat.id,
                                       "У вас нет прав на выполнение данного действия")

        elif get_state(message.chat.id) == 1:
            set_chat_value_message(message, 1)

            instance = Post.get_or_none(Post.post_name == message.text)
            if instance is None:
                creation_post = get_chat_value_message(message.chat.id)

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.main_menu)
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
                                                        'то потом вы её не сможете уже добавить, '
                                                        'и если картинка уже была,'
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

                creation_post = get_chat_value_message(message.chat.id)

                src = f"data/media/posts_media/pic for post - {creation_post['post_name']}.jpeg"
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file.getvalue())
                set_chat_value_message(message, 8, pic_src=src)

                await bot.send_message(message.chat.id, 'Изображение загружено.')
            elif message.photo:
                file_info = await bot.get_file(message.photo[-1].file_id)
                downloaded_file = await bot.download_file(file_info.file_path)

                creation_post = get_chat_value_message(message.chat.id)

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

                creation_post = get_chat_value_message(message.chat.id)

                author = User.get_or_none(user_id=creation_post['author_id'])

                try:
                    new_post = Post(
                        author=author,
                        post_name=str(creation_post['post_name']),
                        post_date=str(creation_post['post_date']),
                        post_desc=str(creation_post['post_desc']),
                        what_needs=str(creation_post['what_needs']),
                        site=str(creation_post['site']),
                        twitter=str(creation_post['twitter']),
                        discord=str(creation_post['discord']),
                        hashtags=str(creation_post['hashtags']),
                        pic_post=str(creation_post['pic_post']),
                        name_entities=str(creation_post['name_entities']),
                        desc_entities=str(creation_post['desc_entities']),
                        date_entities=str(creation_post['date_entities']),
                        what_needs_entities=str(creation_post['what_needs_entities']),
                    )
                    new_post.save()
                except Exception as e:
                    logging.warning(e)
                else:
                    await log(settings, f"Post {str(creation_post['post_name'])} is created by {message.chat.id}")

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
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)

            else:
                await bot.send_message(message.chat.id, 'Вы не ввели ни одного хэштега!'
                                                        'Введите хэштеги поста.')

        elif get_state(message.chat.id) == 10:
            if message.text.lower() == 'да':
                creation_post = get_chat_value_message(message.chat.id)
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
                footer_text_entities = json.loads(str(settings.footer_text_entities))

                count_string_track = 0

                entity = MessageEntity(type="bold",
                                       offset=count_string_track,
                                       length=len(str(creation_post['post_name'])) +
                                              emoji_count(str(creation_post['post_name'])))
                entity_list.append(entity)

                if "entities" in name_entities:
                    entity_list = entity_read(name_entities, entity_list, count_string_track)

                count_string_track += len(str(creation_post['post_name'])) + len("\n\n") + \
                                      emoji_count(str(creation_post['post_name']))

                if "entities" in description_entities:
                    entity_list = entity_read(description_entities, entity_list, count_string_track)

                count_string_track += len(str(creation_post['post_desc'])) + len("\n\n") + \
                                      emoji_count(str(creation_post['post_desc']))

                if creation_post['what_needs'] != '':
                    count_string_track += len(str('✅ '))

                    if "entities" in what_needs_entities:
                        entity_list = entity_read(what_needs_entities, entity_list, count_string_track)

                    count_string_track += len(str(creation_post['what_needs'])) + len("\n\n") + \
                                          emoji_count(str(creation_post['what_needs']))

                if creation_post['post_date'] != '':
                    count_string_track += len(str('📆 ')) + 1

                    if "entities" in date_entities:
                        entity_list = entity_read(date_entities, entity_list, count_string_track)

                    count_string_track += len(str(creation_post['post_date'])) + len("\n\n") + \
                                          emoji_count(str(creation_post['post_date']))

                if creation_post['site'] != '' or creation_post['twitter'] != '' or creation_post['discord'] != '':
                    count_string_track += len(str("🔗 ")) + 1
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
                    entity_list = entity_read(footer_text_entities, entity_list, count_string_track)

                count_string_track += len(f"{settings.footer_text}")

                if type(creation_post['pic_post']) is tuple:
                    if creation_post['pic_post'][0] == '':
                        try:
                            message_result = await bot.send_message(settings.channel_name, text, entities=entity_list)
                        except Exception as e:
                            logging.warning(e)
                        else:
                            await log(settings, f"Post {str(creation_post['post_name'])} is posted by {message.chat.id}")

                            post = Post.get(Post.post_name == str(creation_post['post_name']))
                            post.message_id = message_result.message_id
                            post.status = 1
                            post.save()

                            try:
                                await bot.forward_message(chat_id=settings.group_forward_id,
                                                          from_chat_id=settings.channel_name,
                                                          message_id=message_result.message_id)
                            except Exception as e:
                                logging.warning(e)
                    else:
                        photo = open(creation_post['pic_post'][0], 'rb')
                        try:
                            message_result = await bot.send_photo(settings.channel_name,
                                                                  photo, caption=text, caption_entities=entity_list)
                        except Exception as e:
                            logging.warning(e)
                        else:
                            await log(settings, f"Post {str(creation_post['post_name'])} is posted by {message.chat.id}")

                            post = Post.get(Post.post_name == str(creation_post['post_name']))
                            post.message_id = message_result.message_id
                            post.status = 1
                            post.save()

                            try:
                                await bot.forward_message(chat_id=settings.group_forward_id,
                                                          from_chat_id=settings.channel_name,
                                                          message_id=message_result.message_id)
                            except Exception as e:
                                logging.warning(e)
                else:
                    if creation_post['pic_post'] == '':
                        try:
                            message_result = await bot.send_message(settings.channel_name, text, entities=entity_list)
                        except Exception as e:
                            logging.warning(e)
                        else:
                            await log(settings, f"Post {str(creation_post['post_name'])} is posted by {message.chat.id}")

                            post = Post.get(Post.post_name == str(creation_post['post_name']))
                            post.message_id = message_result.message_id
                            post.status = 1
                            post.save()

                            try:
                                await bot.forward_message(chat_id=settings.group_forward_id,
                                                          from_chat_id=settings.channel_name,
                                                          message_id=message_result.message_id)
                            except Exception as e:
                                logging.warning(e)
                    else:
                        photo = open(creation_post['pic_post'], 'rb')
                        try:
                            message_result = await bot.send_photo(settings.channel_name,
                                                                  photo, caption=text, caption_entities=entity_list)
                        except Exception as e:
                            logging.warning(e)
                        else:
                            await log(settings, f"Post {str(creation_post['post_name'])} is posted by {message.chat.id}")

                            post = Post.get(Post.post_name == str(creation_post['post_name']))
                            post.message_id = message_result.message_id
                            post.status = 1
                            post.save()

                            try:
                                await bot.forward_message(chat_id=settings.group_forward_id,
                                                          from_chat_id=settings.channel_name,
                                                          message_id=message_result.message_id)
                            except Exception as e:
                                logging.warning(e)

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.posts)
                user_markup.row(Menu.lists)
                if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                    user_markup.row(Menu.settings)

                await bot.send_message(message.chat.id, 'Пост был создан и размещен на канале.',
                                       reply_markup=user_markup)

                delete_chat_value_message(message.chat.id)
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.posts)
                user_markup.row(Menu.lists)
                if isinstance(current_user, Admin) and current_user.permissions == 'admin_permissions':
                    user_markup.row(Menu.settings)

                await bot.send_message(message.chat.id, "Вы не написали 'Да', поэтому Пост не был размещён.",
                                       reply_markup=user_markup)

                delete_chat_value_message(message.chat.id)
                delete_state(message.chat.id)

        elif get_state(message.chat.id) == 90:
            post_for_pos = Post.get_or_none(Post.post_name == message.text)

            if post_for_pos is None:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')
            else:
                with shelve.open(files.bot_message_bd) as bd:
                    bd[str(message.chat.id)] = {
                        'author_name': str(post_for_pos.author.username),
                        'post_name': str(post_for_pos.post_name),
                        'post_desc': str(post_for_pos.post_desc),
                        'post_date': str(post_for_pos.post_date),
                        'what_needs': str(post_for_pos.what_needs),
                        'site': str(post_for_pos.site),
                        'twitter': str(post_for_pos.twitter),
                        'discord': str(post_for_pos.discord),
                        'hashtags': str(post_for_pos.hashtags),
                        'pic_post': str(post_for_pos.pic_post),
                        'name_entities': str(post_for_pos.name_entities),
                        'desc_entities': str(post_for_pos.desc_entities),
                        'date_entities': str(post_for_pos.date_entities),
                        'what_needs_entities': str(post_for_pos.what_needs_entities),
                        'status': post_for_pos.status
                    }

                unposted_post = get_chat_value_message(message.chat.id)

                if not await preview(bot, message, unposted_post, settings):
                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Не удаётся отобразить предпросмотр. '
                                                            'Выберите, что хотите изменить',
                                           reply_markup=user_markup)
                    set_state(message.chat.id, 130)
                else:
                    post_key = InlineKeyboardMarkup()
                    post_key.add(InlineKeyboardButton(text="ДА", callback_data='Разместить пост'),
                                 InlineKeyboardButton(text="НЕТ", callback_data='Вернуться в меню размещения'))

                    await bot.send_message(message.chat.id, 'Разместить данный пост?',
                                           reply_markup=post_key)

        elif get_state(message.chat.id) == 11:
            post_for_del = Post.get_or_none(Post.post_name == message.text)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.MenuPosts.add_new_post, Menu.MenuPosts.delete_post)
            user_markup.row(Menu.MenuPosts.edit_post, Menu.MenuPosts.posting)
            user_markup.row(Menu.main_menu)

            if post_for_del is not None:
                try:
                    await bot.delete_message(settings.channel_name, post_for_del.message_id)
                except:
                    await bot.send_message(message.chat.id, 'Пост не может быть удалён из канала: '
                                                            'он не был там размещён!')
                else:
                    await bot.send_message(message.chat.id, 'Пост успешно удален из канала!', reply_markup=user_markup)
                finally:
                    await bot.send_message(message.chat.id, 'Пост успешно удален!', reply_markup=user_markup)
                    await log(settings, f'Post {message.text} is deleted by {message.chat.id}')
                    post_for_del.delete_instance()
                    delete_state(message.chat.id)
            else:
                await bot.send_message(message.chat.id,
                                       'Выбранного поста не обнаружено! '
                                       'Выберите его, нажав на соответствующую кнопку')

        elif get_state(message.chat.id) == 12:
            post_for_edit = Post.get_or_none(post_name=message.text)
            if post_for_edit is not None:
                with shelve.open(files.bot_message_bd) as bd:
                    bd[str(message.chat.id)] = {
                        'author_name': str(post_for_edit.author.username),
                        'post_name': str(post_for_edit.post_name),
                        'post_desc': str(post_for_edit.post_desc),
                        'post_date': str(post_for_edit.post_date),
                        'what_needs': str(post_for_edit.what_needs),
                        'site': str(post_for_edit.site),
                        'twitter': str(post_for_edit.twitter),
                        'discord': str(post_for_edit.discord),
                        'hashtags': str(post_for_edit.hashtags),
                        'pic_post': str(post_for_edit.pic_post),
                        'name_entities': str(post_for_edit.name_entities),
                        'desc_entities': str(post_for_edit.desc_entities),
                        'date_entities': str(post_for_edit.date_entities),
                        'what_needs_entities': str(post_for_edit.what_needs_entities),
                        'status': post_for_edit.status
                    }

                edition_post = get_chat_value_message(message.chat.id)
                await preview(bot, message, edition_post, settings)

                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                user_markup.row(Menu.main_menu)
                await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                       reply_markup=user_markup)
                set_state(message.chat.id, 13)
            else:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) in [14, 140]:
            edition_post = get_chat_value_message(message.chat.id)

            post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))
            if post_for_edit is not None:
                post_for_edit.post_name = message.text
                post_for_edit.name_entities = str(message)
                post_for_edit.save()

                if get_state(message.chat.id) == 14:
                    edited_post = Post.get_or_none(post_name=message.text)

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if edition_post['status']:
                        await edit_post(bot, message, edition_post, settings, False)

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Тема поста успешно изменена!', reply_markup=user_markup)
                    await log(settings, f"Name post {edition_post['post_name']} is changed by {message.chat.id}")
                    set_state(message.chat.id, 13)

                elif get_state(message.chat.id) == 140:
                    edited_post = Post.get_or_none(post_name=message.text)

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if await preview(bot, message, edition_post, settings):
                        key = InlineKeyboardMarkup()
                        key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                     callback_data='Вернуться в главное меню'))
                        await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                    else:
                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)
            else:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) in [15, 150]:
            edition_post = get_chat_value_message(message.chat.id)

            post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))
            if post_for_edit is not None:
                post_for_edit.post_desc = message.text
                post_for_edit.desc_entities = str(message)
                post_for_edit.save()

                if get_state(message.chat.id) == 15:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if edition_post['status']:
                        await edit_post(bot, message, edition_post, settings, False)

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Описание поста успешно изменено!',
                                           reply_markup=user_markup)
                    await log(settings, f"Description post {edition_post['post_name']} is changed by {message.chat.id}")
                    set_state(message.chat.id, 13)
                elif get_state(message.chat.id) == 150:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if await preview(bot, message, edition_post, settings):
                        key = InlineKeyboardMarkup()
                        key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                     callback_data='Вернуться в главное меню'))
                        await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                    else:
                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)

            else:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) in [16, 160]:
            edition_post = get_chat_value_message(message.chat.id)

            if message.text == '/empty':
                post_date = ''
                date_entities = {}
            else:
                post_date = message.text
                date_entities = message

            post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))
            if post_for_edit is not None:
                post_for_edit.post_date = post_date
                post_for_edit.date_entities = date_entities
                post_for_edit.save()

                if get_state(message.chat.id) == 16:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if edition_post['status']:
                        await edit_post(bot, message, edition_post, settings, False)

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Дата события успешно изменена!',
                                           reply_markup=user_markup)
                    await log(settings, f"Date post {edition_post['post_name']} is changed by {message.chat.id}")
                    set_state(message.chat.id, 13)
                elif get_state(message.chat.id) == 160:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if await preview(bot, message, edition_post, settings):
                        key = InlineKeyboardMarkup()
                        key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                     callback_data='Вернуться в главное меню'))
                        await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                    else:
                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)
            else:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) in [17, 170]:
            edition_post = get_chat_value_message(message.chat.id)

            if message.text == '/empty':
                what_needs = ''
                what_needs_entities = {}
            else:
                what_needs = message.text
                what_needs_entities = message

            post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))
            if post_for_edit is not None:
                post_for_edit.what_needs = what_needs
                post_for_edit.what_needs_entities = what_needs_entities
                post_for_edit.save()

                if get_state(message.chat.id) == 17:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if edition_post['status']:
                        await edit_post(bot, message, edition_post, settings, False)

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Условия участия успешно изменены!',
                                           reply_markup=user_markup)
                    await log(settings, f"Requirements {edition_post['post_name']} is changed by {message.chat.id}")
                    set_state(message.chat.id, 13)
                elif get_state(message.chat.id) == 170:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if await preview(bot, message, edition_post, settings):
                        key = InlineKeyboardMarkup()
                        key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                     callback_data='Вернуться в главное меню'))
                        await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                    else:
                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)
            else:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) in [18, 180]:
            edition_post = get_chat_value_message(message.chat.id)

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
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    post_for_edit.site = site
                    post_for_edit.save()

                    if get_state(message.chat.id) == 18:
                        edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(edited_post.author.username),
                                'post_name': str(edited_post.post_name),
                                'post_desc': str(edited_post.post_desc),
                                'post_date': str(edited_post.post_date),
                                'what_needs': str(edited_post.what_needs),
                                'site': str(edited_post.site),
                                'twitter': str(edited_post.twitter),
                                'discord': str(edited_post.discord),
                                'hashtags': str(edited_post.hashtags),
                                'pic_post': str(edited_post.pic_post),
                                'name_entities': str(edited_post.name_entities),
                                'desc_entities': str(edited_post.desc_entities),
                                'date_entities': str(edited_post.date_entities),
                                'what_needs_entities': str(edited_post.what_needs_entities),
                                'status': edited_post.status,
                                'message_id': edited_post.message_id
                            }

                        edition_post = get_chat_value_message(message.chat.id)

                        if edition_post['status']:
                            await edit_post(bot, message, edition_post, settings, False)

                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Сайт проекта успешно изменен!',
                                               reply_markup=user_markup)
                        await log(settings, f"Requirements {edition_post['post_name']} is changed by {message.chat.id}")
                        set_state(message.chat.id, 13)
                    elif get_state(message.chat.id) == 180:
                        edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(edited_post.author.username),
                                'post_name': str(edited_post.post_name),
                                'post_desc': str(edited_post.post_desc),
                                'post_date': str(edited_post.post_date),
                                'what_needs': str(edited_post.what_needs),
                                'site': str(edited_post.site),
                                'twitter': str(edited_post.twitter),
                                'discord': str(edited_post.discord),
                                'hashtags': str(edited_post.hashtags),
                                'pic_post': str(edited_post.pic_post),
                                'name_entities': str(edited_post.name_entities),
                                'desc_entities': str(edited_post.desc_entities),
                                'date_entities': str(edited_post.date_entities),
                                'what_needs_entities': str(edited_post.what_needs_entities),
                                'status': edited_post.status,
                                'message_id': edited_post.message_id
                            }

                        edition_post = get_chat_value_message(message.chat.id)

                        if await preview(bot, message, edition_post, settings):
                            key = InlineKeyboardMarkup()
                            key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                    InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                            key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                         callback_data='Вернуться в главное меню'))
                            await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                        else:
                            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                            user_markup.row(Menu.main_menu)
                            await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                                   reply_markup=user_markup)
                            set_state(message.chat.id, 130)
                else:
                    await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) in [19, 190]:
            edition_post = get_chat_value_message(message.chat.id)

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
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    post_for_edit.twitter = twitter
                    post_for_edit.save()

                    if get_state(message.chat.id) == 19:
                        edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(edited_post.author.username),
                                'post_name': str(edited_post.post_name),
                                'post_desc': str(edited_post.post_desc),
                                'post_date': str(edited_post.post_date),
                                'what_needs': str(edited_post.what_needs),
                                'site': str(edited_post.site),
                                'twitter': str(edited_post.twitter),
                                'discord': str(edited_post.discord),
                                'hashtags': str(edited_post.hashtags),
                                'pic_post': str(edited_post.pic_post),
                                'name_entities': str(edited_post.name_entities),
                                'desc_entities': str(edited_post.desc_entities),
                                'date_entities': str(edited_post.date_entities),
                                'what_needs_entities': str(edited_post.what_needs_entities),
                                'status': edited_post.status,
                                'message_id': edited_post.message_id
                            }

                        edition_post = get_chat_value_message(message.chat.id)

                        if edition_post['status']:
                            await edit_post(bot, message, edition_post, settings, False)

                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Твиттер проекта успешно изменен!',
                                               reply_markup=user_markup)
                        await log(settings, f"Requirements {edition_post['post_name']} is changed by {message.chat.id}")
                        set_state(message.chat.id, 13)
                    elif get_state(message.chat.id) == 190:
                        edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(edited_post.author.username),
                                'post_name': str(edited_post.post_name),
                                'post_desc': str(edited_post.post_desc),
                                'post_date': str(edited_post.post_date),
                                'what_needs': str(edited_post.what_needs),
                                'site': str(edited_post.site),
                                'twitter': str(edited_post.twitter),
                                'discord': str(edited_post.discord),
                                'hashtags': str(edited_post.hashtags),
                                'pic_post': str(edited_post.pic_post),
                                'name_entities': str(edited_post.name_entities),
                                'desc_entities': str(edited_post.desc_entities),
                                'date_entities': str(edited_post.date_entities),
                                'what_needs_entities': str(edited_post.what_needs_entities),
                                'status': edited_post.status,
                                'message_id': edited_post.message_id
                            }

                        edition_post = get_chat_value_message(message.chat.id)

                        if await preview(bot, message, edition_post, settings):
                            key = InlineKeyboardMarkup()
                            key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                    InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                            key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                         callback_data='Вернуться в главное меню'))
                            await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                        else:
                            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                            user_markup.row(Menu.main_menu)
                            await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                                   reply_markup=user_markup)
                            set_state(message.chat.id, 130)
                else:
                    await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) in [20, 200]:
            edition_post = get_chat_value_message(message.chat.id)

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
                post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

                if post_for_edit is not None:
                    post_for_edit.discord = discord
                    post_for_edit.save()

                    if get_state(message.chat.id) == 20:
                        edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(edited_post.author.username),
                                'post_name': str(edited_post.post_name),
                                'post_desc': str(edited_post.post_desc),
                                'post_date': str(edited_post.post_date),
                                'what_needs': str(edited_post.what_needs),
                                'site': str(edited_post.site),
                                'twitter': str(edited_post.twitter),
                                'discord': str(edited_post.discord),
                                'hashtags': str(edited_post.hashtags),
                                'pic_post': str(edited_post.pic_post),
                                'name_entities': str(edited_post.name_entities),
                                'desc_entities': str(edited_post.desc_entities),
                                'date_entities': str(edited_post.date_entities),
                                'what_needs_entities': str(edited_post.what_needs_entities),
                                'status': edited_post.status,
                                'message_id': edited_post.message_id
                            }

                        edition_post = get_chat_value_message(message.chat.id)

                        if edition_post['status']:
                            await edit_post(bot, message, edition_post, settings, False)

                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Дискорд проекта успешно изменен!',
                                               reply_markup=user_markup)
                        await log(settings, f"Requirements {edition_post['post_name']} is changed by {message.chat.id}")
                        set_state(message.chat.id, 13)
                    elif get_state(message.chat.id) == 200:
                        edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                        with shelve.open(files.bot_message_bd) as bd:
                            bd[str(message.chat.id)] = {
                                'author_name': str(edited_post.author.username),
                                'post_name': str(edited_post.post_name),
                                'post_desc': str(edited_post.post_desc),
                                'post_date': str(edited_post.post_date),
                                'what_needs': str(edited_post.what_needs),
                                'site': str(edited_post.site),
                                'twitter': str(edited_post.twitter),
                                'discord': str(edited_post.discord),
                                'hashtags': str(edited_post.hashtags),
                                'pic_post': str(edited_post.pic_post),
                                'name_entities': str(edited_post.name_entities),
                                'desc_entities': str(edited_post.desc_entities),
                                'date_entities': str(edited_post.date_entities),
                                'what_needs_entities': str(edited_post.what_needs_entities),
                                'status': edited_post.status,
                                'message_id': edited_post.message_id
                            }

                        edition_post = get_chat_value_message(message.chat.id)

                        if await preview(bot, message, edition_post, settings):
                            key = InlineKeyboardMarkup()
                            key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                    InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                            key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                         callback_data='Вернуться в главное меню'))
                            await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                        else:
                            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                            user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                            user_markup.row(Menu.main_menu)
                            await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                                   reply_markup=user_markup)
                            set_state(message.chat.id, 130)
                else:
                    await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) in [21, 210]:
            '''download photo'''
            edition_post = get_chat_value_message(message.chat.id)

            src = ''
            if message.text == '/empty':
                edition_post['pic_post'] = src
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

            post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

            if post_for_edit is not None:
                post_for_edit.pic_post = src
                post_for_edit.save()

                if get_state(message.chat.id) == 21:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if edition_post['status']:
                        await edit_post(bot, message, edition_post, settings, True)

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Баннер поста успешно изменен!', reply_markup=user_markup)
                    await log(settings, f"Picture {edition_post['post_name']} is changed by {message.chat.id}")
                    set_state(message.chat.id, 13)
                elif get_state(message.chat.id) == 210:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if await preview(bot, message, edition_post, settings):
                        key = InlineKeyboardMarkup()
                        key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                     callback_data='Вернуться в главное меню'))
                        await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                    else:
                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)
            else:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) in [22, 220]:
            edition_post = get_chat_value_message(message.chat.id)

            post_for_edit = Post.get_or_none(post_name=str(edition_post['post_name']))

            if post_for_edit is not None:
                post_for_edit.hashtags = message.text
                post_for_edit.save()

                if get_state(message.chat.id) == 22:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if edition_post['status']:
                        await edit_post(bot, message, edition_post, settings, False)

                    user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                    user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                    user_markup.row(Menu.main_menu)
                    await bot.send_message(message.chat.id, 'Хэштеги успешно изменены!', reply_markup=user_markup)
                    await log(settings, f"Hashtags {edition_post['post_name']} is changed by {message.chat.id}")
                    set_state(message.chat.id, 13)
                elif get_state(message.chat.id) == 220:
                    edited_post = Post.get_or_none(post_name=str(edition_post['post_name']))

                    with shelve.open(files.bot_message_bd) as bd:
                        bd[str(message.chat.id)] = {
                            'author_name': str(edited_post.author.username),
                            'post_name': str(edited_post.post_name),
                            'post_desc': str(edited_post.post_desc),
                            'post_date': str(edited_post.post_date),
                            'what_needs': str(edited_post.what_needs),
                            'site': str(edited_post.site),
                            'twitter': str(edited_post.twitter),
                            'discord': str(edited_post.discord),
                            'hashtags': str(edited_post.hashtags),
                            'pic_post': str(edited_post.pic_post),
                            'name_entities': str(edited_post.name_entities),
                            'desc_entities': str(edited_post.desc_entities),
                            'date_entities': str(edited_post.date_entities),
                            'what_needs_entities': str(edited_post.what_needs_entities),
                            'status': edited_post.status,
                            'message_id': edited_post.message_id
                        }

                    edition_post = get_chat_value_message(message.chat.id)

                    if await preview(bot, message, edition_post, settings):
                        key = InlineKeyboardMarkup()
                        key.row(InlineKeyboardButton(text='ДА', callback_data='Редактировать пост'),
                                InlineKeyboardButton(text='НЕТ', callback_data='Подтвердить пост'))
                        key.add(InlineKeyboardButton(text='Отменить и вернуться в главное меню',
                                                     callback_data='Вернуться в главное меню'))
                        await bot.send_message(message.chat.id, 'Хотите ли редактировать пост?', reply_markup=key)
                    else:
                        user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
                        user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
                        user_markup.row(Menu.main_menu)
                        await bot.send_message(message.chat.id, 'Теперь выберите, что хотите изменить',
                                               reply_markup=user_markup)
                        set_state(message.chat.id, 130)
            else:
                await bot.send_message(message.chat.id, 'Поста с таким названием нет!\nВыберите заново!')

        elif get_state(message.chat.id) == 31:
            if message.forward_from:
                result_text = new_author(settings, message.forward_from.id, message.forward_from.username)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.ListsMenu.AuthorMenu.add_new, Menu.ListsMenu.AuthorMenu.delete)
                user_markup.row(Menu.main_menu)
                await bot.send_message(message.chat.id, result_text, reply_markup=user_markup)
                await log(settings, f'New author {message.forward_from.username} is added by {message.chat.id}')
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.ListsMenu.AuthorMenu.add_new, Menu.ListsMenu.AuthorMenu.delete)
                user_markup.row(Menu.main_menu)
                await bot.send_message(message.chat.id, 'Новый автор не был добавлен\n'
                                                        'Перешлите сообщение пользователя в бота, '
                                                        'чтобы сделать его автором.',
                                       reply_markup=user_markup)

        elif get_state(message.chat.id) == 32:
            author = str(message.text)
            author = author.split(' - ')
            if int(author[0]) in [int(author[0]) for item in get_author_list() if int(author[0]) in item]:
                try:
                    del_id(Author, int(author[0]))
                except Exception as e:
                    logging.warning(e)
                    await log(settings, 'Author was not deleted')
                else:
                    new_blocked_user(
                        his_id=int(author[0]),
                        his_username=author[1][1:],
                        who_blocked_username=message.chat.username
                    )
                    await bot.send_message(message.chat.id, 'Автор успешно удалён из списка')
                    await log(settings, f'The author {message.text} is removed by {message.chat.id}')
                    delete_state(message.chat.id)
            else:
                await bot.send_message(message.chat.id, 'Такого id в списках авторов не обнаружено! '
                                                        'Выберите правильный id!')
                set_state(message.chat.id, 32)

        elif get_state(message.chat.id) == 41:
            if message.forward_from:
                result_text = new_admin(message.forward_from.id, message.forward_from.username)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.ListsMenu.AdminMenu.add_new, Menu.ListsMenu.AdminMenu.delete)
                user_markup.row(Menu.main_menu)
                await bot.send_message(message.chat.id, result_text, reply_markup=user_markup)
                await log(settings, f'New admin {message.forward_from.username} is added by {message.chat.id}')
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.ListsMenu.AdminMenu.add_new, Menu.ListsMenu.AdminMenu.delete)
                user_markup.row(Menu.main_menu)
                await bot.send_message(message.chat.id, 'Новый админ не был добавлен\n'
                                                        'Перешлите сообщение пользователя в бота, '
                                                        'чтобы сделать его админом.',
                                       reply_markup=user_markup)

        elif get_state(message.chat.id) == 42:
            admin = str(message.text)
            admin = admin.split(' - ')
            if int(admin[0]) in [int(admin[0]) for item in get_admin_list() if int(admin[0]) in item]:
                try:
                    del_id(Admin, int(admin[0]))
                except Exception as e:
                    logging.warning(e)
                    await log(settings, 'Admin was not deleted')
                else:
                    await bot.send_message(message.chat.id, 'Админ успешно удалён из списка')
                    await log(settings, f'The admin {message.text} is removed by {message.chat.id}')
                    delete_state(message.chat.id)
            else:
                await bot.send_message(message.chat.id, 'Такого id в списках админов не обнаружено! '
                                                        'Выберите правильный id!')
                set_state(message.chat.id, 42)

        elif get_state(message.chat.id) == 51:
            if message.forward_from:
                result_text = new_moder(message.forward_from.id, message.forward_from.username)
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.ListsMenu.ModerMenu.add_new, Menu.ListsMenu.ModerMenu.delete)
                user_markup.row(Menu.main_menu)
                await bot.send_message(message.chat.id, result_text, reply_markup=user_markup)
                await log(settings, f'New moder {message.text} is added by {message.chat.id}')
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.ListsMenu.ModerMenu.add_new, Menu.ListsMenu.ModerMenu.delete)
                user_markup.row(Menu.main_menu)
                await bot.send_message(message.chat.id, 'Новый модератор не был добавлен\n'
                                                        'Перешлите сообщение пользователя в бота, '
                                                        'чтобы сделать его модератором.',
                                       reply_markup=user_markup)

        elif get_state(message.chat.id) == 52:
            moder = str(message.text)
            moder = moder.split(' - ')
            if int(moder[0]) in [int(moder[0]) for item in get_moder_list() if int(moder[0]) in item]:
                try:
                    del_id(Admin, int(moder[0]))
                except Exception as e:
                    logging.warning(e)
                    await log(settings, 'Moder was not deleted')
                else:
                    await bot.send_message(message.chat.id, 'Модератор успешно удалён из списка')
                    await log(settings, f'The moder {message.text} is removed by {message.chat.id}')
                    delete_state(message.chat.id)
            else:
                await bot.send_message(message.chat.id, 'Такого id в списках модеров не обнаружено! '
                                                        'Выберите правильный id!')
                set_state(message.chat.id, 52)

        elif get_state(message.chat.id) == 61:
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.Settings.time_zone_text + str(settings.time_zone))
            user_markup.row(Menu.Settings.channel_name_text + str(settings.channel_name))
            user_markup.row(Menu.Settings.threshold_xp_text + str(settings.threshold_xp))
            user_markup.row(Menu.Settings.help_edit_text)
            user_markup.row(Menu.Settings.footer_edit_text)
            user_markup.row(Menu.Settings.log_files_download_text)
            user_markup.row(Menu.Settings.copy_db_download_text)
            user_markup.row(Menu.Settings.create_copy_db_text)
            user_markup.row(Menu.Settings.restore_db_text)
            user_markup.row(Menu.Settings.check_emoji_text)
            user_markup.row(Menu.Settings.bad_emoji_text)
            user_markup.row(Menu.main_menu)

            settings.help_text = message.text
            settings.help_text_entities = message

            help_phrase_obj = Phrase.get_or_none(phrase='help_phrase')
            if help_phrase_obj is not None:
                help_phrase_obj.phrase_text = settings.help_text
                help_phrase_obj.phrase_text_entities = settings.help_text_entities
                help_phrase_obj.save()
            else:
                Phrase.create(phrase='help_text',
                              phrase_text=settings.help_text,
                              phrase_text_entities=settings.help_text_entities)

            await bot.send_message(message.chat.id, 'Добавлено новое сообщение помощи', reply_markup=user_markup)
            delete_state(message.chat.id)

        elif get_state(message.chat.id) == 62:
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.Settings.time_zone_text + str(settings.time_zone))
            user_markup.row(Menu.Settings.channel_name_text + str(settings.channel_name))
            user_markup.row(Menu.Settings.threshold_xp_text + str(settings.threshold_xp))
            user_markup.row(Menu.Settings.help_edit_text)
            user_markup.row(Menu.Settings.footer_edit_text)
            user_markup.row(Menu.Settings.log_files_download_text)
            user_markup.row(Menu.Settings.copy_db_download_text)
            user_markup.row(Menu.Settings.create_copy_db_text)
            user_markup.row(Menu.Settings.restore_db_text)
            user_markup.row(Menu.Settings.check_emoji_text)
            user_markup.row(Menu.Settings.bad_emoji_text)
            user_markup.row(Menu.main_menu)

            settings.footer_text = message.text
            settings.footer_text_entities = message

            footer_phrase_obj = Phrase.get_or_none(phrase='footer_phrase')
            if footer_phrase_obj is not None:
                footer_phrase_obj.phrase_text = settings.footer_text
                footer_phrase_obj.phrase_text_entities = settings.footer_text_entities
                footer_phrase_obj.save()
            else:
                Phrase.create(phrase='footer_phrase',
                              phrase_text=settings.footer_text,
                              phrase_text_entities=settings.footer_text_entities)

            await bot.send_message(message.chat.id, 'Добавлен новый footer', reply_markup=user_markup)
            delete_state(message.chat.id)

        elif get_state(message.chat.id) == 63:
            if message.text.isdigit():
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.Settings.time_zone_text + str(settings.time_zone))
                user_markup.row(Menu.Settings.channel_name_text + str(settings.channel_name))
                user_markup.row(Menu.Settings.threshold_xp_text + str(settings.threshold_xp))
                user_markup.row(Menu.Settings.help_edit_text)
                user_markup.row(Menu.Settings.footer_edit_text)
                user_markup.row(Menu.Settings.log_files_download_text)
                user_markup.row(Menu.Settings.copy_db_download_text)
                user_markup.row(Menu.Settings.create_copy_db_text)
                user_markup.row(Menu.Settings.restore_db_text)
                user_markup.row(Menu.Settings.check_emoji_text)
                user_markup.row(Menu.Settings.bad_emoji_text)
                user_markup.row(Menu.main_menu)

                settings.threshold_xp = int(message.text)

                change_settings(settings)

                await bot.send_message(message.chat.id, 'Добавлен новый порог', reply_markup=user_markup)
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.main_menu)

                await bot.send_message(message.chat.id, 'Введите ЧИСЛО', reply_markup=user_markup)

        elif get_state(message.chat.id) == 65:
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.Settings.time_zone_text + str(settings.time_zone))
            user_markup.row(Menu.Settings.channel_name_text + str(settings.channel_name))
            user_markup.row(Menu.Settings.threshold_xp_text + str(settings.threshold_xp))
            user_markup.row(Menu.Settings.help_edit_text)
            user_markup.row(Menu.Settings.footer_edit_text)
            user_markup.row(Menu.Settings.log_files_download_text)
            user_markup.row(Menu.Settings.copy_db_download_text)
            user_markup.row(Menu.Settings.create_copy_db_text)
            user_markup.row(Menu.Settings.restore_db_text)
            user_markup.row(Menu.Settings.check_emoji_text)
            user_markup.row(Menu.Settings.bad_emoji_text)
            user_markup.row(Menu.main_menu)

            try:
                with open(files.reserve_db_folder + message.text, 'rb') as db:
                    db_bytes = db.read()
                    with open(files.main_db, 'wb') as rdb:
                        rdb.write(db_bytes)
            except Exception as e:
                logging.error(e)
                await bot.send_message(message.chat.id, "Ошибка при восстановлении резервной копии")
            else:
                await bot.send_message(message.chat.id, 'Данные были восстановлены', reply_markup=user_markup)
                delete_state(message.chat.id)

        elif get_state(message.chat.id) == 71:
            emoji_list = find_emoji(message.text)
            if len(emoji_list):
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.Settings.time_zone_text + str(settings.time_zone))
                user_markup.row(Menu.Settings.channel_name_text + str(settings.channel_name))
                user_markup.row(Menu.Settings.threshold_xp_text + str(settings.threshold_xp))
                user_markup.row(Menu.Settings.help_edit_text)
                user_markup.row(Menu.Settings.footer_edit_text)
                user_markup.row(Menu.Settings.log_files_download_text)
                user_markup.row(Menu.Settings.copy_db_download_text)
                user_markup.row(Menu.Settings.create_copy_db_text)
                user_markup.row(Menu.Settings.restore_db_text)
                user_markup.row(Menu.Settings.check_emoji_text)
                user_markup.row(Menu.Settings.bad_emoji_text)
                user_markup.row(Menu.main_menu)

                for emoji in emoji_list:
                    if add_emoji_as_pattern(emoji):
                        await bot.send_message(message.chat.id,
                                               '`Плохой` эмоджи добавлен', reply_markup=user_markup)
                    else:
                        await bot.send_message(message.chat.id,
                                               'Такой `Плохой` эмоджи уже есть', reply_markup=user_markup)
                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.main_menu)

                await bot.send_message(message.chat.id, 'Введите ЭМОДЖИ', reply_markup=user_markup)

        elif get_state(message.chat.id) == 70:
            emoji_list = find_emoji(message.text)
            if len(emoji_list):
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.Settings.time_zone_text + str(settings.time_zone))
                user_markup.row(Menu.Settings.channel_name_text + str(settings.channel_name))
                user_markup.row(Menu.Settings.threshold_xp_text + str(settings.threshold_xp))
                user_markup.row(Menu.Settings.help_edit_text)
                user_markup.row(Menu.Settings.footer_edit_text)
                user_markup.row(Menu.Settings.log_files_download_text)
                user_markup.row(Menu.Settings.copy_db_download_text)
                user_markup.row(Menu.Settings.create_copy_db_text)
                user_markup.row(Menu.Settings.restore_db_text)
                user_markup.row(Menu.Settings.check_emoji_text)
                user_markup.row(Menu.Settings.bad_emoji_text)
                user_markup.row(Menu.main_menu)

                for emoji in emoji_list:
                    EMOJI_OFFSET = 1 if emoji_count(message.text) else 0
                    entities_list = [{"type": "strikethrough",
                                      "offset": 0,
                                      "length": len("Checking")},
                                     {"type": "text_link",
                                      "offset": len(f"Checking emoji {emoji} "
                                                    "for offset via ") + EMOJI_OFFSET,
                                      "length": len("link"),
                                      "url": "http://google.com/"},
                                     {"type": "underline",
                                      "offset": len(f"Checking emoji {emoji} "
                                                    "for offset via link. "
                                                    "Double ") + EMOJI_OFFSET,
                                      "length": len("checking")}]
                    entities = []

                    for entity in entities_list:
                        if entity["type"] == "text_link":
                            entity = MessageEntity(type=entity["type"],
                                                   offset=entity["offset"],
                                                   length=entity["length"], url=entity["url"])
                            entities.append(entity)
                        elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                                "email", "phone_number", "bold", "italic", "underline",
                                                "strikethrough", "code", "pre"]:
                            entity = MessageEntity(type=entity["type"],
                                                   offset=entity["offset"],
                                                   length=entity["length"])
                            entities.append(entity)
                    # result = emoji.encode('unicode-escape').decode('ASCII')
                    # await bot.send_message(message.chat.id, result, reply_markup=user_markup)
                    await bot.send_message(message.chat.id, f"Checking emoji {emoji} "
                                                            "for offset via link. "
                                                            "Double checking offset",
                                           entities=entities,
                                           reply_markup=user_markup)

                delete_state(message.chat.id)
            else:
                user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
                user_markup.row(Menu.main_menu)

                await bot.send_message(message.chat.id, 'Введите ЭМОДЖИ', reply_markup=user_markup)
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


async def bot_inline(bot: Bot, callback_query: CallbackQuery, settings: Settings):
    current_user = object

    for table in [Admin, Author, BlockedUser]:
        for obj in table.select():
            if obj.profile.user_id == callback_query.message.chat.id:
                current_user = obj
                break

    if isinstance(current_user, BlockedUser):
        await bot.send_message(callback_query.message.chat.id, "Вы были заблокированы администратором бота!")
        delete_state(callback_query.message.chat.id)
    elif isinstance(current_user, (Admin, Author)) or callback_query.message.chat.id == SUPER_ADMIN_ID:
        if callback_query.data == 'Вернуться в главное меню':
            if get_state(callback_query.message.chat.id):
                delete_state(callback_query.message.chat.id)
            if get_chat_value_message(callback_query.message.chat.id):
                delete_chat_value_message(callback_query.message.chat.id)

            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.posts)
            user_markup.row(Menu.lists)
            if current_user.permissions == 'admin_permissions':
                user_markup.row(Menu.settings)

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
            await bot.send_message(callback_query.message.chat.id, 'Нужно ли что-то сделать для участия?',
                                   reply_markup=key)

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
            user_markup.row(Menu.MenuPosts.EditMenu.edit_name, Menu.MenuPosts.EditMenu.edit_desc)
            user_markup.row(Menu.MenuPosts.EditMenu.edit_date, Menu.MenuPosts.EditMenu.edit_needs)
            user_markup.row(Menu.MenuPosts.EditMenu.edit_site)
            user_markup.row(Menu.MenuPosts.EditMenu.edit_twitter, Menu.MenuPosts.EditMenu.edit_discord)
            user_markup.row(Menu.MenuPosts.EditMenu.edit_banner, Menu.MenuPosts.EditMenu.edit_hashtags)
            user_markup.row(Menu.main_menu)
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
            unposted_post = get_chat_value_message(callback_query.message.chat.id)
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
            footer_text_entities = json.loads(str(settings.footer_text_entities))

            count_string_track = 0

            entity = MessageEntity(type="bold",
                                   offset=count_string_track,
                                   length=len(str(unposted_post['post_name'])) +
                                          emoji_count(str(unposted_post['post_name'])))
            entity_list.append(entity)

            if "entities" in name_entities:
                entity_list = entity_read(name_entities, entity_list, count_string_track)

            count_string_track += len(str(unposted_post['post_name'])) + len("\n\n") + \
                                  emoji_count(str(unposted_post['post_name']))

            if "entities" in description_entities:
                entity_list = entity_read(description_entities, entity_list, count_string_track)

            count_string_track += len(str(unposted_post['post_desc'])) + len("\n\n") + \
                                  emoji_count(str(unposted_post['post_desc']))

            if unposted_post['what_needs'] != '':
                count_string_track += len(str('✅ '))

                if "entities" in what_needs_entities:
                    entity_list = entity_read(what_needs_entities, entity_list, count_string_track)

                count_string_track += len(str(unposted_post['what_needs'])) + len("\n\n") + \
                                      emoji_count(str(unposted_post['what_needs']))

            if unposted_post['post_date'] != '':
                count_string_track += len(str('📆 ')) + 1

                if "entities" in date_entities:
                    entity_list = entity_read(date_entities, entity_list, count_string_track)

                count_string_track += len(str(unposted_post['post_date'])) + len("\n\n") + \
                                      emoji_count(str(unposted_post['post_date']))

            if unposted_post['site'] != '' or unposted_post['twitter'] != '' or unposted_post['discord'] != '':
                count_string_track += len(str("🔗 ")) + 1
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
                                               offset=count_string_track + len("| "),
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
                                               offset=count_string_track + len("| "),
                                               length=len("Discord"),
                                               url=f"{unposted_post['discord']}")
                        entity_list.append(entity)
                        count_string_track += len("| Discord")
                count_string_track += len("\n\n")

            count_string_track += len(str(unposted_post['hashtags'])) + len("\n\n")

            entity = MessageEntity(type="italic",
                                   offset=count_string_track,
                                   length=len('Автор'))
            entity_list.append(entity)

            count_string_track += len(f"Автор: @{unposted_post['author_name']}\n")

            if "entities" in footer_text_entities:
                entity_list = entity_read(footer_text_entities, entity_list, count_string_track)

            count_string_track += len(f"{settings.footer_text}")

            if type(unposted_post['pic_post']) is tuple:
                if unposted_post['pic_post'][0] == '':
                    try:
                        message_result = await bot.send_message(settings.channel_name, text, entities=entity_list)
                    except Exception as e:
                        logging.warning(e)
                    else:
                        await log(settings,
                            f"Post {str(unposted_post['post_name'])} is posted by {callback_query.message.chat.id}")

                        post_for_pos = Post.get(Post.post_name == str(unposted_post['post_name']))
                        post_for_pos.message_id = message_result.message_id
                        post_for_pos.status = 1
                        post_for_pos.save()

                        try:
                            await bot.forward_message(chat_id=settings.group_forward_id,
                                                      from_chat_id=settings.channel_name,
                                                      message_id=message_result.message_id)
                        except Exception as e:
                            logging.warning(e)
                else:
                    photo = open(unposted_post['pic_post'][0], 'rb')
                    try:
                        message_result = await bot.send_photo(settings.channel_name,
                                                              photo, caption=text, caption_entities=entity_list)
                    except Exception as e:
                        logging.warning(e)
                    else:
                        await log(settings,
                            f"Post {str(unposted_post['post_name'])} is posted by {callback_query.message.chat.id}")

                        post_for_pos = Post.get(Post.post_name == str(unposted_post['post_name']))
                        post_for_pos.message_id = message_result.message_id
                        post_for_pos.status = 1
                        post_for_pos.save()

                        try:
                            await bot.forward_message(chat_id=settings.group_forward_id,
                                                      from_chat_id=settings.channel_name,
                                                      message_id=message_result.message_id)
                        except Exception as e:
                            logging.warning(e)
            else:
                if unposted_post['pic_post'] == '':
                    try:
                        message_result = await bot.send_message(settings.channel_name, text, entities=entity_list)
                    except Exception as e:
                        logging.warning(e)
                    else:
                        await log(settings,
                            f"Post {str(unposted_post['post_name'])} is posted by {callback_query.message.chat.id}")

                        post_for_pos = Post.get(Post.post_name == str(unposted_post['post_name']))
                        post_for_pos.message_id = message_result.message_id
                        post_for_pos.status = 1
                        post_for_pos.save()

                        try:
                            await bot.forward_message(chat_id=settings.group_forward_id,
                                                      from_chat_id=settings.channel_name,
                                                      message_id=message_result.message_id)
                        except Exception as e:
                            logging.warning(e)
                else:
                    photo = open(unposted_post['pic_post'], 'rb')
                    try:
                        message_result = await bot.send_photo(settings.channel_name,
                                                              photo, caption=text, caption_entities=entity_list)
                    except Exception as e:
                        logging.warning(e)
                    else:
                        await log(settings,
                            f"Post {str(unposted_post['post_name'])} is posted by {callback_query.message.chat.id}")

                        post_for_pos = Post.get(Post.post_name == str(unposted_post['post_name']))
                        post_for_pos.message_id = message_result.message_id
                        post_for_pos.status = 1
                        post_for_pos.save()

                        try:
                            await bot.forward_message(chat_id=settings.group_forward_id,
                                                      from_chat_id=settings.channel_name,
                                                      message_id=message_result.message_id)
                        except Exception as e:
                            logging.warning(e)

            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            user_markup.row(Menu.posts)
            user_markup.row(Menu.lists)
            if current_user.permissions == 'admin_permissions':
                user_markup.row(Menu.settings)

            await bot.send_message(callback_query.message.chat.id, 'Пост был размещен на канале.',
                                   reply_markup=user_markup)

            delete_chat_value_message(callback_query.message.chat.id)
            delete_state(callback_query.message.chat.id)

        elif callback_query.data == 'Вернуться в меню размещения':
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            user_markup = ReplyKeyboardMarkup(resize_keyboard=True)
            a = 0
            for post in Post.select():
                if not post.status:
                    a += 1
                    user_markup.row(str(post.post_name))

            if a == 0:
                await bot.send_message(callback_query.message.chat.id, 'Не размещенных постов нет!',
                                       reply_markup=user_markup)
            else:
                user_markup.row(Menu.main_menu)
                await bot.send_message(callback_query.message.chat.id, 'Какой пост хотите разместить?',
                                       parse_mode='Markdown', reply_markup=user_markup)
                set_state(callback_query.message.chat.id, 90)

            delete_chat_value_message(callback_query.message.chat.id)
    else:
        entity_list = []
        entity = MessageEntity(type="text_link",
                               offset=len("У вас недостаточно опыта для доступа к боту, пожалуйста, "
                                          "проявите больше активностей в сообществе "),
                               length=len('HareCrypta'),
                               url='https://t.me/harecrypta_chat')
        entity_list.append(entity)
        await bot.send_message(callback_query.message.chat.id,
                               "У вас недостаточно опыта для доступа к боту, пожалуйста, "
                               "проявите больше активностей в сообществе HareCrypta.",
                               entities=entity_list, disable_web_page_preview=True)
