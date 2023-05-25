from random import choice

import discord
import requests
import json
from discord.ext import commands

from storage import *


@commands.command(aliases=["error", "hstat" "httpstat", "сеть", "код"])
async def http(ctx, num=None):
    if num:
        if int(num) in REQUEST_CODES:
            await ctx.reply(f"https://http.cat/{num}")
        else:
            await ctx.reply("Нет такого кода.")


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


@commands.command(aliases=["ava", "ава", "аватарка"])
async def avatar(ctx):
    author = ctx.message.author
    embed = discord.Embed(color=COLOR_CODES[1], title=f'Аватар {author}', description=f"id: {author.id}")
    embed.set_image(url=author.avatar.url)
    await ctx.reply(embed=embed)


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
