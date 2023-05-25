import math
import multiprocessing
from random import randint

import numexpr
from discord import Option
from typing import Callable

from commands import *

bot = commands.Bot(command_prefix=SETTINGS['prefix'], intents=discord.Intents.all())

json_data = {}


# Модуль "Экономики"
def json_load():
    global json_data
    with open("data.json", mode="r", encoding="utf-8") as f:
        a = json.load(f)
        print(a)
        json_data = a


def json_save():
    with open("data.json", mode="w", encoding="utf-8") as f:
        f.write(json.dumps(json_data, indent=2))


@bot.slash_command(name='баланс', description='В разработке', guild_ids=guild_ids)
async def bal(ctx, user: Option(discord.Member, description='Участник сервера', required=False)):
    print(json_data)
    user = user if user else ctx.author
    embed = discord.Embed(colour=user.colour)
    embed.set_author(name=user.name, icon_url=user.avatar.url)
    if str(user.id) in json_data:
        balance = json_data[str(user.id)]
        embed.description = f"**Статистика**\n" \
                            f"🪙 {balance}"
    else:
        if user == ctx.author:
            json_data[str(ctx.author.id)] = 0
            balance = 0
            embed.description = f"**Статистика**\n" \
                                f"🪙 {balance}"
        else:
            embed.description = "Нет записи о пользователе."
    await ctx.respond(embed=embed)


@bot.slash_command(name='таблица-лидеров', description='В разработке', guild_ids=guild_ids)
async def lb(ctx):
    embed = discord.Embed(colour=COLOR_CODES[1])
    embed.set_author(name="Таблица лидеров", icon_url=bot.user.avatar.url)
    s = ""
    data = sorted(json_data.items(), key=lambda x: x[1], reverse=True)
    for i in range(min(5, len(json_data))):
        s += f"**{i + 1}. {bot.get_user(int(data[i][0]))}** • 🪙{data[i][1]}\n"
    if str(ctx.author.id) in json_data:
        user = (str(ctx.author.id), json_data[(str(ctx.author.id))])
        s += f"Вы на {data.index(user) + 1} месте."
    else:
        s += "Вас в этом списке нет."
    embed.description = s
    await ctx.respond(embed=embed)


@bot.command(aliases=["баланс", "бал", "стат", "stat", "bal"])
async def bal_(ctx, user_id=None):
    user = ctx.author
    if user_id:
        try:
            user = bot.get_user(int(user_id)) if user_id.isdigit() else bot.get_user(int(user_id[2:-1]))
        except Exception as e:
            user = None
            print(e)
            await ctx.send("Произошла ошибка")
    if user:
        embed = discord.Embed(colour=user.colour)
        embed.set_author(name=user.name, icon_url=user.avatar.url)
        if str(user.id) in json_data:
            balance = json_data[str(user.id)]
            embed.description = f"**Статистика**\n" \
                                f"🪙{balance}"
        else:
            if user == ctx.author:
                json_data[str(ctx.author.id)] = 0
                balance = 0
                embed.description = f"**Статистика**\n" \
                                    f"🪙{balance}"
            else:
                embed.description = "Нет записи о пользователе."
        await ctx.send(embed=embed)


@bot.command(aliases=["лидеры", "лид", "lb", "табл", "leaderboard"])
async def lb_(ctx):
    embed = discord.Embed(colour=COLOR_CODES[1])
    embed.set_author(name="Таблица лидеров", icon_url=bot.user.avatar.url)
    s = ""
    data = sorted(json_data.items(), key=lambda x: x[1], reverse=True)
    for i in range(min(5, len(json_data))):
        s += f"**{i + 1}. {bot.get_user(int(data[i][0]))}** • 🪙{data[i][1]}\n"
    if str(ctx.author.id) in json_data:
        user = (str(ctx.author.id), json_data[(str(ctx.author.id))])
        s += f"Вы на {data.index(user) + 1} месте."
    else:
        s += "Вас в этом списке нет."
    embed.description = s
    await ctx.send(embed=embed)


def run_until(seconds: int, func: Callable, *args):
    """Run a function until timeout in seconds reached."""
    with multiprocessing.Pool(processes=2) as pool:
        result = pool.apply_async(func, [*args])
        try:
            result.get(timeout=seconds)
            return result.get()
        except multiprocessing.TimeoutError:
            pass


# События
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("Discord"))
    print(f'{bot.user.name} запустился и готов к работе!')


@bot.event
async def on_message(message):
    if message.author != bot.user:
        if bot.user.mention in message.content:
            aut = message.author
            print(aut.mention)
        if message.content.startswith("t:") and message.author.id in whitelist:
            if message.reference:
                await message.channel.send(message.content[2:], reference=message.reference)
            else:
                await message.channel.send(message.content[2:])
            await message.delete()
    await bot.process_commands(message)


# /-команды
@bot.slash_command(name='тест', description='Что-то делает.', guild_ids=guild_ids)
async def test_(ctx):
    await ctx.respond('Успешный тест!')


@bot.slash_command(name='аватар', description='Фото профиля пользователя.', guild_ids=guild_ids)
async def avatar_(ctx, user: Option(discord.Member, description='Участник сервера', required=False),
                  visible: Option(str, description='Отображать для всех?', choices=("Да", "Нет"), required=False)):
    author = user if user else ctx.author
    embed = discord.Embed(color=COLOR_CODES[1], title=f'Аватар {author}', description=f"id: {author.id}")
    embed.set_image(url=author.avatar.url)
    if visible == "Да":
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name='img', description='Присылает случайное изображение.', guild_ids=guild_ids)
async def img_(ctx, type: Option(str, description='Тип животного', choices=("Коты", "Собаки", "Лисы"), required=True),
               name: Option(str, description='Название Embed`а с изображением', required=False)):
    try:
        title = "Случайный Кот"
        t = "cat"
        if type == "Коты":
            title = "Случайный Кот"
            t = "cat"
        elif type == "Собаки":
            title = "Случайная Собака"
            t = "dog"
        elif type == "Лисы":
            title = "Случайная Лиса"
            t = "fox"
        if name:
            title = name
        await ctx.respond(embed=api(t, title))
    except Exception as e:
        print(e)


@bot.slash_command(name='rpc', description='Камень, ножницы, бумага!', guild_ids=guild_ids)
async def rpc_(ctx,
               item: Option(str, description='Ваш выбор', choices=("Камень", "Ножницы", "Бумага"), required=True)):
    d = {"Камень": "🪨", "Ножницы": "✂", "Бумага": "📜"}
    user_choice = d[item]
    bot_choice = choice(EMOJIS)
    await ctx.respond(embed=rps_results_embed(user_choice, bot_choice))


@bot.slash_command(name='сообщение', description="Отправка сообщений от лица бота.", guild_ids=guild_ids)
async def massage_(ctx,
                   text: Option(str, description='Ваше сообщение.', required=True),
                   channel_id: Option(str, description='id канала.', required=False)):
    if ctx.author.id in whitelist:
        if channel_id:
            channel = bot.get_channel(int(channel_id))
            await channel.send(text)
        else:
            await ctx.send(text)
        await ctx.respond("Успешно. :white_check_mark:", ephemeral=True)


@bot.slash_command(name='голосование', description="Отправка голосования от лица бота.",
                   guild_ids=guild_ids)
async def massage_(ctx,
                   text: Option(str, description='Текст (";" между строками, "—" между вариантами)', required=True),
                   channel_id: Option(str, description='id канала.', required=False),
                   visible: Option(str, description='Отображать для всех?', choices=("Да", "Нет"), required=False)):
    if ctx.author.id in whitelist:
        try:
            visible = visible != "Да"
            text = text.split(";")
            res = []
            s = ""
            for i in text:
                if "—" in i:
                    res.append(i.split("—"))
                s += i + "\n"
            if channel_id:
                channel = bot.get_channel(int(channel_id))
                message = await channel.send(s)
            else:
                message = await ctx.send(s)
            await ctx.respond("Успешно. :white_check_mark:", ephemeral=visible)
            if res:
                for i in res:
                    await message.add_reaction(i[0].replace(" ", ""))
            else:
                await message.add_reaction('✅')
                await message.add_reaction('❌')
        except Exception as e:
            print(e)


@bot.slash_command(name='кубик', description='Тупо кубик', guild_ids=guild_ids)
async def dice_(ctx, num: Option(int, description='Количество граней кубика', required=False)):
    if not num:
        await ctx.respond(randint(1, 6))
    else:
        await ctx.respond(randint(1, num))


@bot.command(aliases=["rand", "random", "randint", "ранд", "случайный", "случ"])
async def rand_(ctx, *args):
    if args:
        try:
            args2 = [1, 6]
            for i in args:
                if i.isdigit():
                    args2.append(int(i))
                if len(args2) == 4:
                    break
            if len(args2) == 4:
                args2.pop(0)
                args2.pop(0)
            elif len(args2) == 3:
                args2.pop(1)
            await ctx.send(randint(min(args2), max(args2)))
        except Exception as e:
            print(e)
    else:
        await ctx.send(randint(1, 6))


@bot.command(aliases=["calc", "счёт", "калькулятор", "подсчёт", "к"])
async def calc_(ctx, *args):
    s = str()
    for i in args:
        s += i + " "
    s = s.replace("π", str(math.pi))
    s = s.replace("E", str(math.e))
    try:
        res = run_until(7, numexpr.evaluate, s)
        if str(res) == "True" or str(res) == "False":
            d = {"True": "Выражение Истинно", "False": "Выражение Ложно"}
            await ctx.reply(f"Результат: {d[str(res)]}")
        elif res or res == 0:
            if "j" in str(res):
                await ctx.reply(f"Результат: {res}")
            else:
                res = round(float(res), 7)
                if str(res).split(".")[-1] == "0":
                    res = int(res)
                await ctx.reply(f"Результат: {res}")
        else:
            await ctx.reply(f"Ответ не был получен")
    except Exception as e:
        print(e)
        if str(e) == "int too big to convert":
            res = run_until(5, eval, s)
            await ctx.reply(f"Результат: {res}")


if __name__ == "__main__":
    try:
        json_load()
        bot.add_command(http)
        bot.add_command(hello)
        bot.add_command(me)
        bot.add_command(avatar)
        bot.add_command(rps)
        bot.add_command(cat)
        bot.add_command(dog)
        bot.add_command(fox)
        bot.run(SETTINGS['token'])
    finally:
        json_save()
