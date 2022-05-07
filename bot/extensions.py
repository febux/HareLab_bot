from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import files
import yaml
import logging

from models import Phrase

# set logging level
logging.basicConfig(filename=files.system_log, format='%(levelname)s:%(name)s:%(asctime)s:%(message)s',
                    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO)


# класс по настройке бота
class Settings:
    threshold_xp: int
    time_zone: str

    channel_name: str
    group_id: int
    group_forward_id: int

    url_csv: str
    token: str

    help_text: str
    help_text_entities: str

    footer_text: str
    footer_text_entities: str

    url_one_time_link: str = ''
    session: Session

    def get_local_settings(self):
        file_settings_local = open(files.settings_local, 'r')  # открываем файл для чтения
        settings = yaml.safe_load(file_settings_local)
        self.time_zone = str(settings['Settings_local']['TimeZone'])
        self.threshold_xp = int(settings['Settings_local']['ThresholdXP'])
        file_settings_local.close()

    def get_global_settings(self):
        file_settings_global = open(files.settings_global, 'r')  # открываем файл для чтения
        settings_global = yaml.safe_load(file_settings_global)
        self.channel_name = str(settings_global['Settings_channel']['ChannelName'])
        self.group_id = int(settings_global['Settings_channel']['GroupID'])
        self.group_forward_id = int(settings_global['Settings_channel']['GroupForwardID'])
        self.url_csv = f'https://combot.org/c/{self.group_id}/chat_users/v2?csv=yes&limit=3000&skip=0'
        self.token = settings_global['Settings_bot']['Token']

        self.session = Session()
        retry = Retry(total=3, connect=3, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        logging.info('Token was set')
        file_settings_global.close()

    def get_phrases(self):
        help_phrase, help_phrase_created = Phrase.get_or_create(phrase='help_text',
                                                                defaults={'phrase_text': 'help',
                                                                          'phrase_text_entities': '{}'})
        self.help_text = help_phrase.phrase_text
        self.help_text_entities = help_phrase.phrase_text_entities
        logging.info('Help phrase is got')

        footer_phrase, footer_phrase_created = Phrase.get_or_create(phrase='footer_text',
                                                                    defaults={'phrase_text': 'footer',
                                                                              'phrase_text_entities': '{}'})
        self.footer_text = footer_phrase.phrase_text
        self.footer_text_entities = footer_phrase.phrase_text_entities
        logging.info('Footer phrase is got')
