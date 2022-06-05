import codecs
import logging
from logging.handlers import RotatingFileHandler
import shelve
from typing import Type, Union, List, Dict

import yaml
import pendulum
import re

from aiogram import Bot
from aiogram.types import MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton, Message, InputMediaPhoto
from aiogram.utils.json import json

import files
from extensions import Settings, SUPER_ADMIN_ID
from models import User, Author, Admin, BlockedUser


# Create handlers
console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(files.system_log, mode='a',
                                   maxBytes=2048000, backupCount=2,
                                   encoding='utf-8', delay=True)


logging.basicConfig(
    format="%(asctime)s::[%(levelname)s]::%(name)s::(%(filename)s).%(funcName)s(%(lineno)d)::%(message)s",
    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO, handlers=(file_handler, console_handler)
)


async def do_reserve_copy_db(settings: Settings):
    current_time = pendulum.now(settings.time_zone)
    try:
        with open(files.main_db, 'rb') as db:
            db_bytes = db.read()
            with open(f'{files.reserve_db_folder}reserve_copy_'
                      f'({current_time.date()}__'
                      f'{current_time.time().hour}_{current_time.time().minute}).db', 'wb') as rdb:
                rdb.write(db_bytes)
    except Exception as e:
        logging.error(e)
    else:
        logging.info('Reserve copy of DB was created')


# запись в файл логирования
async def log(settings: Settings, text: str):
    time = str(pendulum.now(settings.time_zone))
    with codecs.open(files.working_log, 'a', encoding='utf-8') as f:
        f.write(time + '    | ' + text + '\n')


def entity_read(entities: MessageEntity, entity_list: List, count_string_track: int) -> List:
    for entity in entities["entities"]:
        entity_values_list = list(entity.values())

        if entity["type"] == "text_link":
            entity = MessageEntity(type=entity_values_list[0],
                                   offset=count_string_track + entity_values_list[1],
                                   length=entity_values_list[2], url=entity_values_list[3])
        elif entity["type"] in ["mention", "url", "hashtag", "cashtag", "bot_command",
                                "email", "phone_number", "bold", "italic", "underline",
                                "strikethrough", "code", "pre"]:
            entity = MessageEntity(type=entity_values_list[0],
                                   offset=count_string_track + entity_values_list[1],
                                   length=entity_values_list[2])
        entity_list.append(entity)
    return entity_list


def deEmojify(text: str) -> str:
    regrex_pattern = re.compile(pattern="["
                                        u"\U0001F601-\U0001F64F"  # emoticons
                                        u"\U0001F30D-\U0001F567"  # symbols & pictographs
                                        u"\U0001F681-\U0001F6C5"  # transport & map symbols
                                        u"\U0001F004-\U0001F5FF"  # uncategorized
                                        u"\U000026FD"  # gas station
                                        u"\U000024C2-\U0001F251"  # flags
                                        u"\U0001F926-\U0001F937"
                                        u"\U0001F000-\U0001FFFF"
                                        "]+", flags=re.UNICODE)
    return regrex_pattern.sub(r'', text)


def emoji_count(text: str) -> int:
    pattern = "["
    with codecs.open(files.emoji_patterns, encoding='utf-8') as f:
        for line in f.readlines():
            pattern += line
    pattern += "]+"
    regrex_pattern = re.compile(pattern=pattern, flags=re.UNICODE)
    return len(regrex_pattern.findall(text))


def find_emoji(text: str) -> List:
    return re.findall(r'[^\w\s,]', text)


def add_emoji_as_pattern(text: str) -> bool:
    add_emoji_flag = True
    text = text + "\n"
    with codecs.open(files.emoji_patterns, mode='r', encoding='utf-8') as f:
        for line in f.readlines():
            if line == text:
                add_emoji_flag = False
    if add_emoji_flag:
        with codecs.open(files.emoji_patterns, mode='a', encoding='utf-8') as f:
            f.write(text)
    return add_emoji_flag


def del_id(table: Type[Union[Admin, Author]], id_for_del: int) -> None:
    for obj in table.select():
        if obj.profile.user_id == id_for_del:
            obj.delete_instance()


def get_blocked_user_list() -> List:
    blocked_users_list = []

    for blocked_user in BlockedUser.select():
        obj = (
            blocked_user.profile.user_id,
            blocked_user.profile.username,
            blocked_user.who_blocked
        )
        blocked_users_list.append(obj)

    return blocked_users_list


def get_author_list() -> List:
    authors_list = []

    for author in Author.select():
        obj = (author.profile.user_id, author.profile.username, author.experience)
        authors_list.append(obj)

    return authors_list


def get_admin_list() -> List:
    admins_list = []

    for admin in Admin.select().where(Admin.permissions == 'admin_permissions'):
        obj = (admin.profile.user_id, admin.profile.username)
        admins_list.append(obj)

    return admins_list


def get_moder_list() -> List:
    moders_list = []

    for moder in Admin.select().where(Admin.permissions == 'moder_permissions'):
        obj = (moder.profile.user_id, moder.profile.username)
        moders_list.append(obj)

    return moders_list


def new_author(settings: Settings, his_id: int, his_username: str, experience: int = None) -> str:
    if his_id in [his_id for item in get_blocked_user_list() if his_id in item]:
        del_id(BlockedUser, his_id)

    if experience is None or experience >= settings.threshold_xp:
        if experience is None:
            experience = 0

        user, user_created = User.get_or_create(user_id=his_id, username=his_username)

        try:
            author, author_created = Author.get_or_create(profile_id=user,
                                                          permissions='author_permissions',
                                                          experience=experience)
        except Exception as e:
            logging.error(e)
            return 'Данный пользователь уже состоит в другой группе'
        else:
            if author_created:
                return 'Новый автор успешно добавлен'
            else:
                author.experience = experience
                author.save()
                return 'Профиль автора был обновлён'


def new_admin(his_id: int, his_username: str) -> str:
    user, user_created = User.get_or_create(user_id=his_id, username=his_username)

    try:
        admin, admin_created = Admin.get_or_create(profile=user, permissions='admin_permissions')
    except Exception as e:
        logging.error(e)
        return 'Данный пользователь уже состоит в другой группе'
    else:
        if admin_created:
            return 'Новый админ успешно добавлен'
        else:
            return 'Такой админ уже существует'


def new_moder(his_id: int, his_username: str) -> str:
    user, user_created = User.get_or_create(user_id=his_id, username=his_username)

    try:
        moder, moder_created = Admin.get_or_create(profile=user, permissions='moder_permissions')
    except Exception as e:
        logging.error(e)
        return 'Данный пользователь уже состоит в другой группе'
    else:
        if moder_created:
            return 'Новый модератор успешно добавлен'
        else:
            return 'Такой модератор уже существует'


def new_blocked_user(his_id: int, his_username: str, who_blocked_username: str) -> str:
    user, user_created = User.get_or_create(user_id=his_id, username=his_username)

    try:
        blocked_user, blocked_user_created = BlockedUser.get_or_create(
            profile_id=user,
            who_blocked=who_blocked_username
        )
    except Exception as e:
        logging.error(e)
    else:
        if blocked_user_created:
            return 'Пользователь успешно заблокирован'
        else:
            return 'Пользователь уже заблокирован'


def set_state(chat_id: int, state: int) -> None:
    with shelve.open(files.state_bd) as bd:
        bd[str(chat_id)] = state


def get_state(chat_id: int) -> Union[bool, object]:
    with shelve.open(files.state_bd) as bd:
        try:
            state_num = bd[str(chat_id)]
        except Exception as e:
            return False
        else:
            return state_num


def delete_state(chat_id: int) -> None:
    with shelve.open(files.state_bd) as bd:
        del bd[str(chat_id)]


def set_chat_value_message(message: Message, mode: int, pic_src: str = '') -> None:
    if mode == 1:
        with shelve.open(files.bot_message_bd) as bd:
            bd[str(message.chat.id)] = {
                'author_id': str(message.chat.id),
                'author_name': str(message.chat.username),
                'post_name': str(message.text),
                'name_entities': str(message)
            }

    elif mode == 2:
        with shelve.open(files.bot_message_bd) as bd:
            temp_dict = bd[str(message.chat.id)]
            temp_dict.update({'post_desc': str(message.text), 'desc_entities': str(message)})
            bd[str(message.chat.id)] = temp_dict

    elif mode == 3:
        if 'Есть ли дата проведения события или дедлайн?' in message.text:
            temp_text = ''
            temp_entities = {}
        else:
            temp_text = message.text
            temp_entities = message

        with shelve.open(files.bot_message_bd) as bd:
            temp_dict = bd[str(message.chat.id)]
            temp_dict.update({'post_date': str(temp_text), 'date_entities': str(temp_entities)})
            bd[str(message.chat.id)] = temp_dict

    elif mode == 4:
        if 'Нужно ли что-то сделать для участия?' in message.text:
            temp_text = ''
            temp_entities = {}
        else:
            temp_text = message.text
            temp_entities = message

        with shelve.open(files.bot_message_bd) as bd:
            temp_dict = bd[str(message.chat.id)]
            temp_dict.update({'what_needs': str(temp_text), 'what_needs_entities': str(temp_entities)})
            bd[str(message.chat.id)] = temp_dict

    elif mode == 5:
        if 'Есть ли сайт у проекта?' in message.text:
            temp_text = ''
        else:
            temp_text = message.text

        with shelve.open(files.bot_message_bd) as bd:
            temp_dict = bd[str(message.chat.id)]
            temp_dict.update({'site': str(temp_text)})
            bd[str(message.chat.id)] = temp_dict

    elif mode == 6:
        if 'Есть ли твиттер у проекта?' in message.text:
            temp_text = ''
        else:
            temp_text = message.text

        with shelve.open(files.bot_message_bd) as bd:
            temp_dict = bd[str(message.chat.id)]
            temp_dict.update({'twitter': str(temp_text)})
            bd[str(message.chat.id)] = temp_dict

    elif mode == 7:
        if 'Есть ли дискорд у проекта?' in message.text:
            temp_text = ''
        else:
            temp_text = message.text

        with shelve.open(files.bot_message_bd) as bd:
            temp_dict = bd[str(message.chat.id)]
            temp_dict.update({'discord': str(temp_text)})
            bd[str(message.chat.id)] = temp_dict

    elif mode == 8:
        with shelve.open(files.bot_message_bd) as bd:
            temp_dict = bd[str(message.chat.id)]
            temp_dict.update({'pic_post': str(pic_src)})
            bd[str(message.chat.id)] = temp_dict

    elif mode == 9:
        with shelve.open(files.bot_message_bd) as bd:
            temp_dict = bd[str(message.chat.id)]
            temp_dict.update({'hashtags': str(message.text), 'status': 0})
            bd[str(message.chat.id)] = temp_dict


def get_chat_value_message(chat_id: int) -> Union[bool, object, Dict]:
    with shelve.open(files.bot_message_bd) as bd:
        try:
            value = bd[str(chat_id)]
        except Exception as e:
            return False
        else:
            return value


def delete_chat_value_message(chat_id: int) -> None:
    with shelve.open(files.bot_message_bd) as bd:
        del bd[str(chat_id)]


# изменение настроек бота и запись в файл настроек
def change_settings(settings: Settings) -> None:
    new_settings = {
        'Settings_local':
            {
                'ThresholdXP': settings.threshold_xp,
                'TimeZone': settings.time_zone
            }
    }
    with open(files.settings_local, 'w') as f:
        yaml.dump(new_settings, f)


async def get_csv(bot: Bot, settings: Settings) -> bool:
    try:
        csv = settings.session.get(
            settings.url_csv,
            timeout=(settings.time_for_connect, settings.time_for_data_rec)
        ).text
    except Exception as e:
        logging.error(e)
        settings.session.close()
        logging.error('Session was closed')
        await bot.send_message(SUPER_ADMIN_ID, 'Данные не могут быть обновлены!\n'
                                               'Невозможно получить csv файл!\n'
                                               'Вставьте ссылку с одноразовым ключом для доступа к csv файлу! '
                                               'Получите её у Combot по команде /onetime.')
        set_state(SUPER_ADMIN_ID, 55)
        return False
    else:
        with open('csv.csv', "w", encoding='utf-8') as file:
            file.write(csv)

        with open('csv.csv', encoding='utf-8') as file:
            for line in file.readlines():
                if "<!DOCTYPE html>" in line:
                    settings.session.close()
                    logging.error('Session was closed')
                    await bot.send_message(SUPER_ADMIN_ID, 'Данные не могут быть обновлены!\n'
                                                           'Нет авторизации!\n'
                                                           'Вставьте ссылку с одноразовым '
                                                           'ключом для доступа к csv файлу! '
                                                           'Получите её у Combot по команде /onetime.')
                    set_state(SUPER_ADMIN_ID, 55)
                    return False
                else:
                    line = line.split(',')
                    if int(line[0]) == 5064416622:
                        continue
                    elif int(line[0]) == 777000:
                        continue
                    elif int(line[0]) == 136817688:
                        continue
                    elif int(line[0]) in [int(line[0]) for item in get_blocked_user_list() if int(line[0]) in item]:
                        continue
                    elif int(line[0]) in [int(line[0]) for item in get_admin_list() if int(line[0]) in item]:
                        continue
                    elif int(line[0]) in [int(line[0]) for item in get_moder_list() if int(line[0]) in item]:
                        continue
                    else:
                        try:
                            new_author(settings, int(line[0]), line[2], int(line[5]))
                        except ValueError:
                            pass
        return True


async def preview(bot: Bot, message: Message, preview_post: Dict, settings: Settings) -> bool:
    """preview"""
    entity_list = []
    text = f"{preview_post['post_name']}\n\n" \
           f"{preview_post['post_desc']}\n\n"

    if preview_post['what_needs'] != '':
        text += f"✅ {preview_post['what_needs']}\n\n"

    if preview_post['post_date'] != '':
        text += f"📆 {preview_post['post_date']}\n\n"

    if preview_post['site'] != '' or preview_post['twitter'] != '' or preview_post['discord'] != '':
        text += "🔗 "
        if preview_post['site'] != '':
            text += "Сайт проекта "
        if preview_post['twitter'] != '':
            if preview_post['site'] == '':
                text += "Twitter "
            else:
                text += "| Twitter "
        if preview_post['discord'] != '':
            if preview_post['site'] == '' and preview_post['twitter'] == '':
                text += "Discord"
            else:
                text += "| Discord"
        text += "\n\n"

    text += f"{preview_post['hashtags']}\n\n" \
            f"Автор: @{preview_post['author_name']}\n" \
            f"{settings.footer_text}"

    name_entities = json.loads(str(preview_post['name_entities']))
    description_entities = json.loads(str(preview_post['desc_entities']))
    date_entities = json.loads(str(preview_post['date_entities']))
    what_needs_entities = json.loads(str(preview_post['what_needs_entities']))
    footer_text_entities = json.loads(str(settings.footer_text_entities))

    if type(preview_post['pic_post']) is tuple:
        if preview_post['pic_post'][0] == '':
            text_format_char = 4096
        else:
            text_format_char = 1024
    else:
        if preview_post['pic_post'] == '':
            text_format_char = 4096
        else:
            text_format_char = 1024

    count_string_track = 0

    entity = MessageEntity(type="bold",
                           offset=count_string_track,
                           length=len(str(preview_post['post_name'])) +
                                  emoji_count(str(preview_post['post_name'])))
    entity_list.append(entity)

    if "entities" in name_entities:
        entity_list = entity_read(name_entities, entity_list, count_string_track)

    count_string_track += len(str(preview_post['post_name'])) + len("\n\n") + \
                          emoji_count(str(preview_post['post_name']))

    if "entities" in description_entities:
        entity_list = entity_read(description_entities, entity_list, count_string_track)

    count_string_track += len(str(preview_post['post_desc'])) + len("\n\n") + \
                          emoji_count(str(preview_post['post_desc']))

    if preview_post['what_needs'] != '':
        count_string_track += len(str('✅ '))

        if "entities" in what_needs_entities:
            entity_list = entity_read(what_needs_entities, entity_list, count_string_track)

        count_string_track += len(str(preview_post['what_needs'])) + len("\n\n") + \
                              emoji_count(str(preview_post['what_needs']))

    if preview_post['post_date'] != '':
        count_string_track += len(str('📆 ')) + 1

        if "entities" in date_entities:
            entity_list = entity_read(date_entities, entity_list, count_string_track)

        count_string_track += len(str(preview_post['post_date'])) + len("\n\n") + \
                              emoji_count(str(preview_post['post_date']))

    if preview_post['site'] != '' or preview_post['twitter'] != '' or preview_post['discord'] != '':
        count_string_track += len(str("🔗 ")) + 1
        if preview_post['site'] != '':
            entity = MessageEntity(type="text_link",
                                   offset=count_string_track,
                                   length=len("Сайт проекта"),
                                   url=f"{preview_post['site']}")
            entity_list.append(entity)
            count_string_track += len("Сайт проекта ")
        if preview_post['twitter'] != '':
            if preview_post['site'] == '':
                entity = MessageEntity(type="text_link",
                                       offset=count_string_track,
                                       length=len("Twitter"),
                                       url=f"{preview_post['twitter']}")
                entity_list.append(entity)
                count_string_track += len("Twitter ")
            else:
                entity = MessageEntity(type="text_link",
                                       offset=count_string_track + len("| "),
                                       length=len("Twitter"),
                                       url=f"{preview_post['twitter']}")
                entity_list.append(entity)
                count_string_track += len("| Twitter ")
        if preview_post['discord'] != '':
            if preview_post['site'] == '' and preview_post['twitter'] == '':
                entity = MessageEntity(type="text_link",
                                       offset=count_string_track,
                                       length=len("Discord"),
                                       url=f"{preview_post['discord']}")
                entity_list.append(entity)
                count_string_track += len("Discord")
            else:
                entity = MessageEntity(type="text_link",
                                       offset=count_string_track + len("| "),
                                       length=len("Discord"),
                                       url=f"{preview_post['discord']}")
                entity_list.append(entity)
                count_string_track += len("| Discord")
        count_string_track += len("\n\n")

    count_string_track += len(str(preview_post['hashtags'])) + len("\n\n")

    entity = MessageEntity(type="italic",
                           offset=count_string_track,
                           length=len('Автор'))
    entity_list.append(entity)

    count_string_track += len(f"Автор: @{preview_post['author_name']}\n")

    if "entities" in footer_text_entities:
        entity_list = entity_read(footer_text_entities, entity_list, count_string_track)

    count_string_track += len(f"{settings.footer_text}")

    inline_status = InlineKeyboardMarkup()
    inline_status.add(InlineKeyboardButton(text=f"Статус: {'размещён' if preview_post['status'] else 'не размещён'}",
                                           callback_data='status'))

    try:
        if type(preview_post['pic_post']) is tuple:
            if preview_post['pic_post'][0] == '':
                await bot.send_message(message.chat.id, text, entities=entity_list, reply_markup=inline_status,
                                       disable_web_page_preview=True)
                return True
            else:
                photo = open(preview_post['pic_post'][0], 'rb')
                await bot.send_photo(message.chat.id, photo, caption=text, caption_entities=entity_list,
                                     reply_markup=inline_status)
                return True
        else:
            if preview_post['pic_post'] == '':
                await bot.send_message(message.chat.id, text, entities=entity_list, reply_markup=inline_status,
                                       disable_web_page_preview=True)
                return True
            else:
                photo = open(preview_post['pic_post'], 'rb')
                await bot.send_photo(message.chat.id, photo, caption=text, caption_entities=entity_list,
                                     reply_markup=inline_status)
                return True
    except Exception as e:
        logging.error(e)
        if str(e) == 'Media_caption_too_long':
            await bot.send_message(message.chat.id, 'Пост слишком большой, нужно его сократить.\n'
                                                    f'Сейчас количество символов: {len(text)}.\n'
                                                    f'Должно быть: {text_format_char}')
            return False
        if str(e) == 'Message is too long':
            await bot.send_message(message.chat.id, 'Пост слишком большой, нужно его сократить.\n'
                                                    f'Сейчас количество символов: {len(text)}.\n'
                                                    f'Должно быть: {text_format_char}')
            return False


async def edit_post(bot: Bot, message: Message, edited_post: Dict, settings: Settings, edit_picture: bool) -> bool:
    """preview"""
    entity_list = []
    text = f"{edited_post['post_name']}\n\n" \
           f"{edited_post['post_desc']}\n\n"

    if edited_post['what_needs'] != '':
        text += f"✅ {edited_post['what_needs']}\n\n"

    if edited_post['post_date'] != '':
        text += f"📆 {edited_post['post_date']}\n\n"

    if edited_post['site'] != '' or edited_post['twitter'] != '' or edited_post['discord'] != '':
        text += "🔗 "
        if edited_post['site'] != '':
            text += "Сайт проекта "
        if edited_post['twitter'] != '':
            if edited_post['site'] == '':
                text += "Twitter "
            else:
                text += "| Twitter "
        if edited_post['discord'] != '':
            if edited_post['site'] == '' and edited_post['twitter'] == '':
                text += "Discord"
            else:
                text += "| Discord"
        text += "\n\n"

    text += f"{edited_post['hashtags']}\n\n" \
            f"Автор: @{edited_post['author_name']}\n" \
            f"{settings.footer_text}"

    name_entities = json.loads(str(edited_post['name_entities']))
    description_entities = json.loads(str(edited_post['desc_entities']))
    date_entities = json.loads(str(edited_post['date_entities']))
    what_needs_entities = json.loads(str(edited_post['what_needs_entities']))
    footer_text_entities = json.loads(str(settings.footer_text_entities))

    if type(edited_post['pic_post']) is tuple:
        if edited_post['pic_post'][0] == '':
            text_format_char = 4096
        else:
            text_format_char = 1024
    else:
        if edited_post['pic_post'] == '':
            text_format_char = 4096
        else:
            text_format_char = 1024

    count_string_track = 0

    entity = MessageEntity(type="bold",
                           offset=count_string_track,
                           length=len(str(edited_post['post_name'])) +
                                  emoji_count(str(edited_post['post_name'])))
    entity_list.append(entity)

    if "entities" in name_entities:
        entity_list = entity_read(name_entities, entity_list, count_string_track)

    count_string_track += len(str(edited_post['post_name'])) + len("\n\n") + \
                          emoji_count(str(edited_post['post_name']))

    if "entities" in description_entities:
        entity_list = entity_read(description_entities, entity_list, count_string_track)

    count_string_track += len(str(edited_post['post_desc'])) + len("\n\n") + \
                          emoji_count(str(edited_post['post_desc']))

    if edited_post['what_needs'] != '':
        count_string_track += len(str('✅ '))

        if "entities" in what_needs_entities:
            entity_list = entity_read(what_needs_entities, entity_list, count_string_track)

        count_string_track += len(str(edited_post['what_needs'])) + len("\n\n") + \
                              emoji_count(str(edited_post['what_needs']))

    if edited_post['post_date'] != '':
        count_string_track += len(str('📆 ')) + 1

        if "entities" in date_entities:
            entity_list = entity_read(date_entities, entity_list, count_string_track)

        count_string_track += len(str(edited_post['post_date'])) + len("\n\n") + \
                              emoji_count(str(edited_post['post_date']))

    if edited_post['site'] != '' or edited_post['twitter'] != '' or edited_post['discord'] != '':
        count_string_track += len(str("🔗 ")) + 1
        if edited_post['site'] != '':
            entity = MessageEntity(type="text_link",
                                   offset=count_string_track,
                                   length=len("Сайт проекта"),
                                   url=f"{edited_post['site']}")
            entity_list.append(entity)
            count_string_track += len("Сайт проекта ")
        if edited_post['twitter'] != '':
            if edited_post['site'] == '':
                entity = MessageEntity(type="text_link",
                                       offset=count_string_track,
                                       length=len("Twitter"),
                                       url=f"{edited_post['twitter']}")
                entity_list.append(entity)
                count_string_track += len("Twitter ")
            else:
                entity = MessageEntity(type="text_link",
                                       offset=count_string_track + len("| "),
                                       length=len("Twitter"),
                                       url=f"{edited_post['twitter']}")
                entity_list.append(entity)
                count_string_track += len("| Twitter ")
        if edited_post['discord'] != '':
            if edited_post['site'] == '' and edited_post['twitter'] == '':
                entity = MessageEntity(type="text_link",
                                       offset=count_string_track,
                                       length=len("Discord"),
                                       url=f"{edited_post['discord']}")
                entity_list.append(entity)
                count_string_track += len("Discord")
            else:
                entity = MessageEntity(type="text_link",
                                       offset=count_string_track + len("| "),
                                       length=len("Discord"),
                                       url=f"{edited_post['discord']}")
                entity_list.append(entity)
                count_string_track += len("| Discord")
        count_string_track += len("\n\n")

    count_string_track += len(str(edited_post['hashtags'])) + len("\n\n")

    entity = MessageEntity(type="italic",
                           offset=count_string_track,
                           length=len('Автор'))
    entity_list.append(entity)

    count_string_track += len(f"Автор: @{edited_post['author_name']}\n")

    if "entities" in footer_text_entities:
        entity_list = entity_read(footer_text_entities, entity_list, count_string_track)

    count_string_track += len(f"{settings.footer_text}")

    try:
        if edit_picture:
            if type(edited_post['pic_post']) is tuple:
                if edited_post['pic_post'][0] == '':
                    return True
                else:
                    photo = InputMediaPhoto(open(edited_post['pic_post'][0], 'rb'))
                    await bot.edit_message_media(media=photo, chat_id=settings.channel_name,
                                                 message_id=edited_post['message_id'])
                    return True
            else:
                if edited_post['pic_post'] == '':
                    return True
                else:
                    photo = InputMediaPhoto(open(edited_post['pic_post'], 'rb'))
                    await bot.edit_message_media(media=photo, chat_id=settings.channel_name,
                                                 message_id=edited_post['message_id'])
                    return True
        else:
            if type(edited_post['pic_post']) is tuple:
                if edited_post['pic_post'][0] == '':
                    await bot.edit_message_text(chat_id=settings.channel_name, message_id=edited_post['message_id'],
                                                text=text, entities=entity_list, disable_web_page_preview=True)
                    return True
                else:
                    await bot.edit_message_caption(chat_id=settings.channel_name, message_id=edited_post['message_id'],
                                                   caption=text, caption_entities=entity_list)
                    return True
            else:
                if edited_post['pic_post'] == '':
                    await bot.edit_message_text(chat_id=settings.channel_name, message_id=edited_post['message_id'],
                                                text=text, entities=entity_list, disable_web_page_preview=True)
                    return True
                else:
                    await bot.edit_message_caption(chat_id=settings.channel_name, message_id=edited_post['message_id'],
                                                   caption=text, caption_entities=entity_list)
                    return True
    except Exception as e:
        logging.error(e)
        if str(e) == 'Media_caption_too_long' or str(e) == 'Message is too long':
            await bot.send_message(message.chat.id, 'Пост слишком большой, нужно его сократить.\n'
                                                    f'Сейчас количество символов: {len(text)}.\n'
                                                    f'Должно быть: {text_format_char}')
            return False
