import logging
import sqlite3
import shelve
import yaml
import pendulum

from aiogram.types import MessageEntity, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.json import json

import files
from config import admin_id

# set logging level
logging.basicConfig(filename=files.system_log, format='%(levelname)s:%(name)s:%(asctime)s:%(message)s',
                    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO)


# запись в файл логирования
async def log(text):
    time = str(pendulum.now())
    try:
        with open(files.working_log, 'a', encoding='utf-8') as f:
            f.write(time + '    | ' + text + '\n')
    except:
        with open(files.working_log, 'w', encoding='utf-8') as f:
            f.write(time + '    | ' + text + '\n')


def get_author_list():
    authors_list = []
    a = 0

    con = sqlite3.connect(files.main_db)
    cursor = con.cursor()
    try:
        cursor.execute("SELECT id, username, experience FROM authors;")
    except:
        cursor.execute("CREATE TABLE IF NOT EXISTS authors (id INT, username TEXT, experience INT );")
        cursor.execute("SELECT id, username, experience FROM authors;")

    for id_a, name, exp in cursor.fetchall():
        a += 1
        author = (id_a, name, exp)
        authors_list.append(author)

    con.close()
    return authors_list


def get_admin_list():
    admins_list = []
    a = 0

    con = sqlite3.connect(files.main_db)
    cursor = con.cursor()
    try:
        cursor.execute("SELECT id, username FROM admins;")
    except:
        cursor.execute("CREATE TABLE IF NOT EXISTS admins (id INT, username TEXT);")
        cursor.execute("SELECT id, username FROM admins;")

    for id_a, name in cursor.fetchall():
        a += 1
        admin = (id_a, name)
        admins_list.append(admin)

    con.close()
    return admins_list


def get_moder_list():
    moders_list = []
    a = 0

    con = sqlite3.connect(files.main_db)
    cursor = con.cursor()
    try:
        cursor.execute("SELECT id, username FROM moders;")
    except:
        cursor.execute("CREATE TABLE IF NOT EXISTS moders (id INT, username TEXT);")
        cursor.execute("SELECT id, username FROM moders;")

    for id_m, name in cursor.fetchall():
        a += 1
        moder = (id_m, name)
        moders_list.append(moder)

    con.close()
    return moders_list


def new_author(settings, his_id, his_username, experience=None):
    con = sqlite3.connect(files.main_db)
    cursor = con.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS authors (id INT, username TEXT, experience INT );")
    if experience is None:
        experience = 0
        try:
            cursor.execute("INSERT INTO authors (id, username, experience) "
                           f"VALUES ({str(his_id)}, '{str(his_username)}', {str(experience)});")
        except:
            cursor.execute(f"UPDATE authors SET experience = {str(experience)} WHERE id = {str(his_id)};")
    elif experience >= settings.threshold_xp:
        try:
            cursor.execute("INSERT INTO authors (id, username, experience) "
                           f"VALUES ({str(his_id)}, '{str(his_username)}', {str(experience)});")
        except:
            cursor.execute(f"UPDATE authors SET experience = {str(experience)} WHERE id = {str(his_id)};")

    con.commit()
    con.close()


def new_admin(his_id, his_username):
    con = sqlite3.connect(files.main_db)
    cursor = con.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS admins (id INT, username TEXT);")
    cursor.execute(f"INSERT OR IGNORE INTO admins (id, username) VALUES ({str(his_id)}, '{str(his_username)}');")

    con.commit()
    con.close()


def new_moder(his_id, his_username):
    con = sqlite3.connect(files.main_db)
    cursor = con.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS moders (id INT, username TEXT);")
    cursor.execute(f"INSERT OR IGNORE INTO moders (id, username) VALUES ({str(his_id)}, '{str(his_username)}');")

    con.commit()
    con.close()


def set_state(chat_id, state):
    with shelve.open(files.state_bd) as bd:
        bd[str(chat_id)] = state


def get_state(chat_id):
    with shelve.open(files.state_bd) as bd:
        try:
            state_num = bd[str(chat_id)]
        except:
            return False
        else:
            return state_num


def delete_state(chat_id):
    with shelve.open(files.state_bd) as bd:
        del bd[str(chat_id)]


def new_blocked_user(his_id):
    pass


def check_message(message):
    with shelve.open(files.bot_message_bd) as bd:
        if message in bd:
            return True
        else:
            return False


def set_chat_value_message(message, mode, pic_src=''):
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


def get_chat_value_message(message):
    with shelve.open(files.bot_message_bd) as bd:
        try:
            value = bd[str(message.chat.id)]
        except:
            return False
        else:
            return value


def delete_chat_value_message(message):
    with shelve.open(files.bot_message_bd) as bd:
        del bd[str(message.chat.id)]


def del_id(table, id_for_del):
    con = sqlite3.connect(files.main_db)
    cursor = con.cursor()

    cursor.execute(f"DELETE FROM {str(table)} WHERE id = {str(id_for_del)};")
    con.commit()
    con.close()


# изменение настроек бота и запись в файл настроек
def change_settings(settings):
    new_settings = {
        'Settings_local':
            {
                'ThresholdXP': settings.threshold_xp,
                'TimeZone': settings.time_zone
            }
                    }
    with open(files.settings_local, 'w') as f:
        yaml.dump(new_settings, f)


async def get_csv(bot, settings):
    try:
        csv = settings.session.get(settings.url_csv).text
    except:
        logging.info('Session was closed')
        await bot.send_message(admin_id, 'Данные не могут быть обновлены!\n'
                                         'Вставьте ссылку с одноразовым ключом для доступа к csv файлу! '
                                         'Получите её у Combot по команде /onetime.')
        with shelve.open(files.state_bd) as bd:
            bd[str(admin_id)] = 55
        return False
    else:
        with open('csv.csv', "w", encoding='utf-8') as file:
            file.write(csv)

        with open('csv.csv', encoding='utf-8') as file:
            for line in file.readlines():
                if "<!DOCTYPE html>" in line:
                    settings.session.close()
                    settings.session = None
                    await bot.send_message(admin_id, 'Данные не могут быть обновлены!\n'
                                                     'Вставьте действительную '
                                                     'ссылку с одноразовым ключом для доступа к csv файлу! '
                                                     'Получите её у Combot по команде /onetime.')
                    with shelve.open(files.state_bd) as bd:
                        bd[str(admin_id)] = 55
                    return False
                else:
                    line = line.split(',')
                    if int(line[0]) == 5064416622:
                        continue
                    elif int(line[0]) == 777000:
                        continue
                    elif int(line[0]) == 136817688:
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


async def preview(bot, message, preview_post, settings):
    '''preview'''
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
    footer_text_entities = json.loads(settings.footer_text_entities)

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
                           length=len(preview_post['post_name']))
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

    count_string_track += len(str(preview_post['post_name'])) + len("\n\n")

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

    count_string_track += len(str(preview_post['post_desc'])) + len("\n\n")

    if preview_post['what_needs'] != '':
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

        count_string_track += len(str(preview_post['what_needs'])) + len("\n\n")

    if preview_post['post_date'] != '':
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

        count_string_track += len(str(preview_post['post_date'])) + len("\n\n")

    if preview_post['site'] != '' or preview_post['twitter'] != '' or preview_post['discord'] != '':
        count_string_track += len("🔗 ") + 1
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

    inline_status = InlineKeyboardMarkup()
    inline_status.add(InlineKeyboardButton(text=f"Статус: {'размещён' if preview_post['status'] else 'не размещён'}",
                                           callback_data='status'))

    try:
        if type(preview_post['pic_post']) is tuple:
            if preview_post['pic_post'][0] == '':
                await bot.send_message(message.chat.id, text, entities=entity_list, reply_markup=inline_status)
                return True
            else:
                photo = open(preview_post['pic_post'][0], 'rb')
                await bot.send_photo(message.chat.id, photo, caption=text, caption_entities=entity_list,
                                     reply_markup=inline_status)
                return True
        else:
            if preview_post['pic_post'] == '':
                await bot.send_message(message.chat.id, text, entities=entity_list, reply_markup=inline_status)
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


async def edit_post(bot, message, edited_post, settings, edit_picture):
    '''preview'''
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
    footer_text_entities = json.loads(settings.footer_text_entities)

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
                           length=len(edited_post['post_name']))
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

    count_string_track += len(str(edited_post['post_name'])) + len("\n\n")

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

    count_string_track += len(str(edited_post['post_desc'])) + len("\n\n")

    if edited_post['what_needs'] != '':
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

        count_string_track += len(str(edited_post['what_needs'])) + len("\n\n")

    if edited_post['post_date'] != '':
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

        count_string_track += len(str(edited_post['post_date'])) + len("\n\n")

    if edited_post['site'] != '' or edited_post['twitter'] != '' or edited_post['discord'] != '':
        count_string_track += len("🔗 ") + 1
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

    try:
        if edit_picture:
            if type(edited_post['pic_post']) is tuple:
                if edited_post['pic_post'][0] == '':
                    return True
                else:
                    photo = open(edited_post['pic_post'][0], 'rb')
                    await bot.edit_message_media(media=photo, chat_id=settings.channel_name,
                                                 message_id=edited_post['message_id'])
                    return True
            else:
                if edited_post['pic_post'] == '':
                    return True
                else:
                    photo = open(edited_post['pic_post'], 'rb')
                    await bot.edit_message_media(media=photo, chat_id=settings.channel_name,
                                                 message_id=edited_post['message_id'])
                    return True
        else:
            if type(edited_post['pic_post']) is tuple:
                if edited_post['pic_post'][0] == '':
                    await bot.edit_message_text(chat_id=settings.channel_name, message_id=edited_post['message_id'],
                                                text=text, entities=entity_list)
                    return True
                else:
                    await bot.edit_message_caption(chat_id=settings.channel_name, message_id=edited_post['message_id'],
                                                   caption=text, caption_entities=entity_list)
                    return True
            else:
                if edited_post['pic_post'] == '':
                    await bot.edit_message_text(chat_id=settings.channel_name, message_id=edited_post['message_id'],
                                                text=text, entities=entity_list)
                    return True
                else:
                    await bot.edit_message_caption(chat_id=settings.channel_name, message_id=edited_post['message_id'],
                                                   caption=text, caption_entities=entity_list)
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

