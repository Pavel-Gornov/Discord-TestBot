import datetime
import json
import math
import multiprocessing
from random import choice

import discord
import numexpr
import requests
from discord.ext import commands
from typing import Callable, Optional

from storage import *


@commands.command(aliases=["error", "hstat" "httpstat", "сеть", "код", "статус"])
async def http(ctx, num: Optional[int] = 200):
    if num in REQUEST_CODES:
        await ctx.reply(f"https://http.cat/{num}")
    else:
        await ctx.reply("Нет такого кода.")


@commands.command(aliases=["ava", "ава", "аватарка", "аватар"])
async def avatar(ctx, user: Optional[discord.Member] = None):
    author = None
    if user:
        author = user
    else:
        author = ctx.message.author
    if author:
        embed = discord.Embed(color=COLOR_CODES[1], title=f'Аватар {author}', description=f"id: {author.id}")
        embed.set_image(url=author.avatar.url)
        await ctx.reply(embed=embed)


@commands.command(aliases=["hi", "hey", "привет", "прив", "приветствие"])
async def hello(ctx):
    author = ctx.message.author
    await ctx.send(f'{choice(GREETINGS_LIST)}, {author.mention}!')


@commands.command(aliases=["m", "я"])
async def me(ctx, *args):
    if ctx.message.author.id in whitelist and args:
        s = str()
        for i in args:
            s += i + " "
        if ctx.message.reference:
            await ctx.send(s, reference=ctx.message.reference)
        else:
            await ctx.send(s)
        await ctx.message.delete()
    else:
        print("Nope")


# Камень, ножницы, бумага
@commands.command(aliases=["кмн", "кнб", "rpc", "roshambo"])
async def rps(ctx, user_chose=None):
    bot_choice = choice(EMOJIS)
    if not user_chose:
        user_chose = choice(EMOJIS)
        await ctx.reply(embed=rps_results_embed(user_chose, bot_choice, random=True))
    else:
        if user_chose.lower() in ["к", "r", "rock", "🪨", "камень"]:
            user_chose = "🪨"
        elif user_chose.lower() in ["б", "p", "paper", "📜", "бумага"]:
            user_chose = "📜"
        elif user_chose.lower() in ["н", "s", "scissors", "✂", "ножницы", "✂️"]:
            user_chose = "✂"
        if user_chose:
            await ctx.reply(embed=rps_results_embed(user_chose, bot_choice))
        else:
            user_chose = choice(EMOJIS)
            await ctx.reply(embed=rps_results_embed(user_chose, bot_choice, random=True))


def rps_results(ch1, ch2):
    if ch1 == ch2:
        return "**Ничья**"
    elif ch1 == "🪨" and ch2 == "✂" or ch1 == "✂" and ch2 == "📜" or ch1 == "📜" and ch2 == "🪨":
        return "**Пользователь Победил!**"
    else:
        return "**Бот Победил!**"


def rps_results_embed(user_chose, bot_choice, random=False):
    embed = discord.Embed(colour=COLOR_CODES[1], title="Результаты:")
    s = ""
    if random:
        s = " (выбран случайно)"
    embed.add_field(name="Ваш выбор:", value=f"{user_chose}{s}\n")
    embed.add_field(name="Выбор бота:", value=f"{bot_choice}\n")
    embed.description = f"{rps_results(user_chose, bot_choice)}"
    return embed


# Картинки с животными!
def api(tag, title):
    json_res = None
    if tag == "cat":
        response = requests.get("https://api.thecatapi.com/v1/images/search?mime_types=jpg,png")
        json_res = json.loads(response.text)[0]["url"]
    elif tag == "dog":
        response = requests.get("https://api.thedogapi.com/v1/images/search?mime_types=jpg,png")
        json_res = json.loads(response.text)[0]["url"]
    elif tag == "fox":
        response = requests.get("https://randomfox.ca/floof")
        json_res = json.loads(response.text)["image"]
    embed = discord.Embed(color=COLOR_CODES[1], title=title)
    embed.set_image(url=json_res)
    return embed


@commands.command(aliases=["c", "кот", "Кот", "Cat", "🐱"])
async def cat(ctx, *title):
    s = str()
    for i in title:
        s += i + " "
    if s:
        t = s
    else:
        t = "Случайный Кот"
    await ctx.reply(embed=api("cat", t))


@commands.command(aliases=["d", "собака", "Пёс", "Собака", "Dog", "🐶"])
async def dog(ctx, *title):
    s = str()
    for i in title:
        s += i + " "
    if s:
        t = s
    else:
        t = "Случайная Собака"
    await ctx.reply(embed=api("dog", t))


@commands.command(aliases=["лиса", "лис", "Fox", "Лис", "Лиса", "🦊"])
async def fox(ctx, *title):
    s = str()
    for i in title:
        s += i + " "
    if s:
        t = s
    else:
        t = "Случайная Лиса"
    await ctx.reply(embed=api("fox", t))


@commands.command(aliases=["счёт", "калькулятор", "подсчёт", "к"])
async def calc(ctx, *args):
    async with ctx.channel.typing():
        s = str()
        for i in args:
            s += i + " "
        s = s.replace("π", str(math.pi)).replace("E", str(math.e))
        res = "Произошла ошибка."
        try:
            res = run_until(7, numexpr.evaluate, s)
            if not res and str(res) != "False":
                res = "Ответ не был получен"
            elif str(res) == "True" or str(res) == "False":
                res = f"Результат: {D[str(res)]}"
            elif "j" in str(res):
                res = f"Результат: {res}"
            else:
                res = round(float(res), 7)
                if str(res).split(".")[-1] == "0":
                    res = int(res)
                res = f"Результат: {res}"
        except Exception as e:
            print(e)
    await ctx.reply(res)


def run_until(seconds: int, func: Callable, *args):
    """Run a function until timeout in seconds reached."""
    with multiprocessing.Pool(processes=2) as pool:
        result = pool.apply_async(func, [*args])
        try:
            result.get(timeout=seconds)
            return result.get()
        except multiprocessing.TimeoutError:
            pass


def makeDSTimestamp(year, month, day, hour, minute, second, timezone, mode):
    dt = datetime.datetime(year, month, day, hour, minute, second,
                           tzinfo=datetime.timezone(datetime.timedelta(hours=timezone)))
    return f"<t:{int(dt.timestamp())}:{mode[0]}>"
