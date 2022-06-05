import logging
from logging.handlers import RotatingFileHandler

from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import files
import yaml
from dotenv import dotenv_values
import os

from models import Phrase

# Create handlers
console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(files.system_log, mode='a',
                                   maxBytes=2048000, backupCount=2,
                                   encoding='utf-8', delay=True)

logging.basicConfig(
    format="%(asctime)s::[%(levelname)s]::%(name)s::(%(filename)s).%(funcName)s(%(lineno)d)::%(message)s",
    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO, handlers=(file_handler, console_handler)
)

# считывание переменных среды
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    config = dotenv_values(dotenv_path)
    SUPER_ADMIN_ID = int(config['SUPER_ADMIN_ID'])
    TOKEN = config['TOKEN']
    TOTAL_RETRIES = int(config['TOTAL_RETRIES'])
    CONNECT_RETRY = int(config['CONNECT_RETRY'])
    TIME_BETWEEN_ATTEMPTS = int(config['TIME_BETWEEN_ATTEMPTS'])
    TIME_FOR_CONNECT = int(config['TIME_FOR_CONNECT'])
    TIME_DATA_REC = int(config['TIME_DATA_REC'])
else:
    logging.error('There is no .env file to config project!')

CHAT_MODE_PRIVATE = 'private'


# класс по настройке бота
class Settings:
    threshold_xp: int
    time_zone: str

    channel_name: str
    group_id: int
    group_forward_id: int

    url_csv: str

    help_text: str
    help_text_entities: str

    footer_text: str
    footer_text_entities: str

    url_one_time_link: str = ''
    session: Session = Session()
    time_for_connect: int = 3
    time_for_data_rec: int = 3

    def get_local_settings(self):
        with open(files.settings_local, 'r') as file_settings_local:  # открываем файл для чтения
            settings = yaml.safe_load(file_settings_local)
            self.time_zone = str(settings['Settings_local']['TimeZone'])
            self.threshold_xp = int(settings['Settings_local']['ThresholdXP'])

    def get_global_settings(self):
        with open(files.settings_global, 'r') as file_settings_global:  # открываем файл для чтения
            settings_global = yaml.safe_load(file_settings_global)
            self.channel_name = str(settings_global['Settings_channel']['ChannelName'])
            self.group_id = int(settings_global['Settings_channel']['GroupID'])
            self.group_forward_id = int(settings_global['Settings_channel']['GroupForwardID'])
            self.url_csv = f'https://combot.org/c/{self.group_id}/chat_users/v2?csv=yes&limit=3000&skip=0'

    def set_session_settings(
            self,
            total_retries: int,
            connect_retry: int,
            time_between_attempts: int,
            time_for_connect: int,
            time_for_data_rec: int,
    ):
        # настройка таймаута и повтора подключения для сессии
        self.session = Session()
        self.time_for_connect = time_for_connect
        self.time_for_data_rec = time_for_data_rec
        retry = Retry(total=total_retries, connect=connect_retry, backoff_factor=time_between_attempts)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def get_phrases(self):
        help_phrase, help_phrase_created = Phrase.get_or_create(phrase='help_phrase',
                                                                defaults={'phrase_text': 'help',
                                                                          'phrase_text_entities': '{}'})
        self.help_text = help_phrase.phrase_text
        self.help_text_entities = help_phrase.phrase_text_entities
        logging.info('Help phrase is got')

        footer_phrase, footer_phrase_created = Phrase.get_or_create(phrase='footer_phrase',
                                                                    defaults={'phrase_text': 'footer',
                                                                              'phrase_text_entities': '{}'})
        self.footer_text = footer_phrase.phrase_text
        self.footer_text_entities = footer_phrase.phrase_text_entities
        logging.info('Footer phrase is got')


class Menu:
    posts = 'Посты'

    class MenuPosts:
        add_new_post = 'Добавить новый пост'
        delete_post = 'Удалить пост'
        edit_post = 'Редактирование постов'

        class EditMenu:
            edit_name = 'Изменить тему'
            edit_desc = 'Изменить описание'
            edit_date = 'Изменить дату 📆'
            edit_needs = 'Изменить требования ✅'
            edit_site = 'Изменить сайт проекта 🌐'
            edit_twitter = 'Изменить твиттер 🐦'
            edit_discord = 'Изменить дискорд 👾'
            edit_banner = 'Изменить баннер 🖼'
            edit_hashtags = 'Изменить хэштеги #️⃣'

        posting = 'Размещение постов'

    lists = 'Списки'

    class ListsMenu:
        authors_list = 'Список авторов'

        class AuthorMenu:
            add_new = 'Добавить нового автора'
            delete = 'Удалить автора'

        blocked_authors_lists = 'Удалённые авторы'
        moders_lists = 'Список модераторов'

        class ModerMenu:
            add_new = 'Добавить нового модератора'
            delete = 'Удалить модератора'

        admins_lists = 'Список админов'

        class AdminMenu:
            add_new = 'Добавить нового админа'
            delete = 'Удалить админа'

    settings = 'Настройки бота'

    class Settings:
        time_zone_text = 'Часовой пояс: '
        channel_name_text = 'Название канала: '
        threshold_xp_text = 'Порог опыта авторам: '
        help_edit_text = 'Изменить выводное сообщение команды /help'
        footer_edit_text = 'Изменить нижнюю подпись для постов'
        log_files_download_text = 'Скачать лог файл'
        copy_db_download_text = 'Скачать резервную копию БД'
        create_copy_db_text = 'Создать резервную копию БД'
        restore_db_text = 'Восстановить данные из резервной копии'
        check_emoji_text = 'Проверить эмоджи'
        bad_emoji_text = 'Добавить `плохой` эмоджи'

    main_menu = '🏠 Главное меню'
    back = 'Назад'
