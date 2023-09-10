import os

import requests
from discord import Option
from lib.utils import makeDSTimestamp
from lib import mnl_mod, mnllib
from discord.ext import commands
import discord
from storage import *

bot = commands.Bot(command_prefix=commands.when_mentioned_or(SETTINGS['prefix']), intents=discord.Intents.all())


@bot.slash_command(name="метка-времени", description="Что-то делает", guild_ids=GUILD_IDS)
async def time(ctx, year: Option(int, description="Год для даты", required=False) = 1970,
               month: Option(int, description="Номер месяца года", required=False) = 1,
               day: Option(int, description="Номер дня месяца", required=False) = 1,
               hour: Option(int, description="Час дня", required=False) = 0,
               minute: Option(int, description="Минута часа", required=False) = 0,
               second: Option(int, description="Секунда минуты", required=False) = 0,
               timezone: Option(int, description="Временная зона GMT+n", required=False) = 0,
               mode: Option(str, description="Тип отображения", choices=("R — Оставшееся время",
                                                                         "d — Короткая запись даты только цифрами",
                                                                         "D — Дата с подписью месяца словом",
                                                                         "f — Дата и время",
                                                                         "F — Полные день недели, дата и время",
                                                                         "t — Часы и минуты",
                                                                         "T — Часы, минуты и секунды"),
                            required=False) = "R"):
    await ctx.respond(makeDSTimestamp(year, month, day, hour, minute, second, timezone, mode))


@bot.event
async def on_connect():
    if bot.auto_sync_commands:
        await bot.sync_commands()
    print(f'{bot.user.name} запускается...')


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game("Discord"))
    print(f'{bot.user.name} запустился и готов к работе!')


@bot.event
async def on_disconnect():
    print(f"{bot.user.name} отключён.")


@bot.event
async def on_message(message):
    if message.author != bot.user:
        if bot.user.mention in message.content:
            print(message.author.mention)
        if message.content.startswith("t:") and message.author.id in whitelist:
            if message.reference:
                await message.channel.send(message.content[2:], reference=message.reference)
            else:
                await message.channel.send(message.content[2:])
            await message.delete()
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Вы сможете использовать эту команду повторно через {round(error.retry_after, 2)} секунд")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        raise error


@bot.slash_command(name='аватар', description='Фото профиля пользователя.', guild_ids=GUILD_IDS)
async def avatar_(ctx, user: Option(discord.Member, description='Участник сервера', required=False),
                  visible: Option(str, description='Отображать для всех?', choices=("Да", "Нет"), required=False)):
    author = user if user else ctx.author
    embed = discord.Embed(color=COLOR_CODES["bot"], title=f'Аватар {author}', description=f"id: {author.id}")
    embed.set_image(url=author.avatar.url)
    if visible == "Да":
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name='api', description='Присылает случайное изображение.', guild_ids=GUILD_IDS)
@discord.option(name="img_type", type=str, description='Тип животного', choices=("Коты", "Собаки", "Лисы"),
                required=True)
@discord.option(name="name", type=str, description='Название Embed`а с изображением', required=False)
async def img_(ctx, img_type, name=None):
    if not name:
        name = {"Коты": "Случайный Кот", "Собаки": "Случайная Собака", "Лисы": "Случайная Лиса"}[img_type]
    embed = discord.Embed(color=COLOR_CODES["bot"], title=name)
    if img_type == "Коты":
        response = requests.get("https://api.thecatapi.com/v1/images/search?mime_types=jpg,png")
        embed.set_image(url=response.json()[0]["url"])
    elif img_type == "Собаки":
        response = requests.get("https://api.thedogapi.com/v1/images/search?mime_types=jpg,png")
        embed.set_image(url=response.json()[0]["url"])
    else:
        response = requests.get("https://randomfox.ca/floof")
        embed.set_image(url=response.json()["image"])
    await ctx.respond(embed=embed)


@bot.slash_command(name='сообщение', description="Отправка сообщений от лица бота.", guild_ids=GUILD_IDS)
async def message_(ctx,
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
                   guild_ids=GUILD_IDS)
@discord.commands.default_permissions(administrator=True)
@discord.commands.guild_only()
async def message_(ctx,
                   text: Option(str, description='Текст (";" между строками, "—" между вариантами)', required=True),
                   channel_id: Option(str, description='id канала.', required=False),
                   visible: Option(str, description='Отображать для всех?', choices=("Да", "Нет"), required=False)):
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


@bot.command(aliases=["мнл"])
@commands.cooldown(1, 5, commands.BucketType.user)
async def mnl(ctx, *, arg):
    async with ctx.channel.typing():
        code_input = arg.replace("```", "")

        mnl_e = mnllib.MnLExecutor()
        fio = mnl_mod.MnLFakeIOModule()
        mnl_e.load_module(mnllib.MnLBaseModule())
        mnl_e.load_module(fio)

        try:
            mnl_e.run(code_input)
            embed = discord.Embed(colour=COLOR_CODES["success"], title="Вывод программы:", description=fio.stdout)
        except mnllib.MnLParserError as pe:
            embed = discord.Embed(colour=COLOR_CODES["error"], title="Ошибка при выполненни программы!",
                                  description=f"Parser error: {pe.message} / {pe.string}")
        except mnllib.MnLExecutorError as ee:
            embed = discord.Embed(colour=COLOR_CODES["error"], title="Ошибка при выполненни программы!",
                                  description=f"Executor error: {ee.message} / token #{ee.tokenid}: "
                                              f"{mnl_e.strparset(ee.token)} / {str(type(ee.exc))[8:-2]} - {ee.exc}")
        except mnllib.MnLSecurityError as se:
            embed = discord.Embed(colour=COLOR_CODES["error"], title="Ошибка при выполненни программы!",
                                  description=f"Security error: code {se.code}")
            print(se.message)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    await ctx.reply(embed=embed)


# noinspection PyTypeChecker
def main():
    for f in os.listdir("./cogs"):
        if f.endswith(".py") and f != "economy.py":
            bot.load_extension("cogs." + f[:-3])
    print("Модули успешно загружены!")

    bot.run(SETTINGS['token'])


if __name__ == "__main__":
    main()
