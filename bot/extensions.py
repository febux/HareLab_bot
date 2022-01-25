import sqlite3
import files
import yaml
import logging

# set logging level
logging.basicConfig(filename=files.system_log, format='%(levelname)s:%(name)s:%(asctime)s:%(message)s',
                    datefmt='%d.%m.%Y %I:%M:%S %p', level=logging.INFO)


# класс по настройке бота
class Settings:
    def __init__(self):
        self.file_settings_local = open(files.settings_local, 'r')  # открываем файл для чтения
        self.settings = yaml.safe_load(self.file_settings_local)
        self.time_zone = str(self.settings['Settings_local']['TimeZone'])
        self.threshold_xp = int(self.settings['Settings_local']['ThresholdXP'])
        self.file_settings_local.close()

        self.file_settings_global = open(files.settings_global, 'r')  # открываем файл для чтения
        self.settings_global = yaml.safe_load(self.file_settings_global)
        self.channel_name = str(self.settings_global['Settings_channel']['ChannelName'])
        self.channel_id = str(self.settings_global['Settings_channel']['ChannelID'])
        self.url_csv = f'https://combot.org/c/{self.channel_id}/chat_users/v2?csv=yes&limit=3000&skip=0'
        self.token = self.settings_global['Settings_bot']['Token']
        logging.info('Token was set')
        self.file_settings_global.close()

        con = sqlite3.connect(files.main_db)
        cursor = con.cursor()
        cursor.execute("SELECT phrase, phrase_text, phrase_text_entities FROM phrases "
                       "WHERE phrase = 'help_text';")
        for phrase, phrase_text, phrase_text_entities in cursor.fetchall():
            self.help_text = phrase_text
            self.help_text_entities = phrase_text_entities
        logging.info('Help phrase is got')

        cursor.execute("SELECT phrase, phrase_text, phrase_text_entities FROM phrases "
                       "WHERE phrase = 'footer_text';")
        for phrase, phrase_text, phrase_text_entities in cursor.fetchall():
            self.footer_text = phrase_text
            self.footer_text_entities = phrase_text_entities
        logging.info('Footer phrase is got')

        con.close()

        self.url_one_time_link = ''
        self.session = None
