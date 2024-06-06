import json
import datetime
import sqlite3
from typing import Callable

import discord


class Config:
    def __init__(self):
        self.data = {"LANGUAGES": ("ru", "en-US"), "DEFAULT_LANGUAGE": "ru", "PREFIX": "|", "TOKEN": "", "COGS": ()}

    def __getattr__(self, item):
        return self.data.get(item, None)

    def load(self, filename: str):
        with open(filename, mode="r", encoding="utf-8") as f:
            self.data = json.load(f)


CONFIG = Config()


class TBStrings:
    def __init__(self):
        self.data = None

    def __getitem__(self, item: str) -> dict:
        return self.data.get(item)

    def __call__(self, string_id: str, language: str = None) -> str:
        s = self.data.get(string_id, None)
        if s:
            if language in s.keys():
                return s.get(language)
            return s.get(CONFIG.DEFAULT_LANGUAGE)
        return ""

    def load(self, filename: str):
        with open(filename, mode="r", encoding="utf-8") as f:
            self.data = json.load(f)


TBS = TBStrings()


class DBManager:
    def __init__(self):
        self.con: sqlite3.Connection = None
        self.cur: sqlite3.Cursor = None

    def get_server_settings(self, server_id: int):
        self.cur.execute(f"SELECT * FROM settings WHERE id = {server_id}")
        result = self.cur.fetchone()
        return result

    def change_server_settings(self, server_id, **changes):
        self.cur.execute(f"SELECT * FROM settings WHERE id = {server_id}")
        result = self.cur.fetchone()
        if result:
            temp = list()
            for k, v in changes.items():
                if isinstance(v, str):
                    temp.append(f'{k} = "{v}"')
                else:
                    temp.append(f'{k} = {v}')
            self.cur.execute(f"UPDATE settings SET {', '.join(temp)} WHERE id = {server_id}")
        else:
            self.cur.execute(f"INSERT {', '.join(changes.keys())} INTO settings VALUES {', '.join(changes.values())}")
        self.con.commit()

    def load(self, filename: str):
        self.con = sqlite3.connect(filename)
        self.cur = self.con.cursor()


DB = DBManager()


class Color:
    BOT = 0xFFF7ED
    SUCCESS = 0x66bb6a
    ERROR = 0xf03431


def makeDSTimestamp(year, month, day, hour, minute, second, timezone, mode):
    dt = datetime.datetime(year, month, day, hour, minute, second,
                           tzinfo=datetime.timezone(datetime.timedelta(hours=timezone)))
    return f"<t:{int(dt.timestamp())}:{mode[0]}>"


# TODO: Добавить настройки языка сервера и использовать их в этой функции.
def get_guild_lang(guild: discord.Guild) -> str:
    if guild:
        if DB:
            s = DB.get_server_settings(guild.id)
            if s and s[1] is not None:
                return s[1]
        elif guild.preferred_locale in CONFIG.LANGUAGES:
            return guild.preferred_locale
    return CONFIG.DEFAULT_LANGUAGE


def is_emoji(string):
    range_min = 127744
    range_max = 129782
    range_min_2 = 126980
    range_max_2 = 127569
    range_min_3 = 169
    range_max_3 = 174
    range_min_4 = 8205
    range_max_4 = 12953
    if string:
        for a_char in string:
            char_code = ord(a_char)
            if range_min <= char_code <= range_max:
                return True
            elif range_min_2 <= char_code <= range_max_2:
                return True
            elif range_min_3 <= char_code <= range_max_3:
                return True
            elif range_min_4 <= char_code <= range_max_4:
                return True
        return False
    else:
        return False


def alpha() -> Callable:
    def inner(command: Callable):
        if isinstance(command, discord.ApplicationCommand):
            command.guild_ids = CONFIG.TESTING_GUILDS
        else:
            command.__guild_ids__ = CONFIG.TESTING_GUILDS
        return command

    return inner
