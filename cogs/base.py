import math
import random
import numexpr
from typing import Optional

import discord
import requests
from discord.commands import option
from discord.ext import commands

from storage import *
from lib.utils import run_until

COG_NAME: final = "основых команд"


class BaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль {COG_NAME} успешно загружен!")

    @commands.command(aliases=["error", "hstat" "httpstat", "сеть", "код", "статус"])
    async def http(self, ctx, num: Optional[int] = 200):
        if num in REQUEST_CODES:
            await ctx.reply(f"https://http.cat/{num}")
        else:
            await ctx.reply("Нет такого кода.")

    @commands.command(aliases=["ava", "ава", "аватарка", "аватар"])
    async def avatar(self, ctx, user: Optional[discord.Member] = None):
        author = user if user else ctx.message.author
        embed = discord.Embed(color=COLOR_CODES["bot"], title=f'Аватар {author}', description=f"id: {author.id}")
        embed.set_image(url=author.avatar.url)
        await ctx.reply(embed=embed)

    @discord.commands.message_command(name="Аватар пользователя")
    async def avatar_msg_command(self, ctx, message):
        user = message.author
        embed = discord.Embed(color=COLOR_CODES["bot"], title=f'Аватар {user}', description=f"id: {user.id}")
        embed.set_image(url=user.avatar.url)
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.command(aliases=["rand", "randint", "ранд", "случайный", "случ"])
    async def random(self, ctx, *, arg):
        await ctx.reply(random.choice(arg.split(";")))

    @commands.command(aliases=["m", "я"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def me(self, ctx, *, arg):
        await ctx.send(arg, reference=ctx.message.reference)
        await ctx.message.delete()

    @commands.command(aliases=["hi", "hey", "Привет", "привет", "приветствие"])
    async def hello(self, ctx):
        await ctx.send(f'{random.choice(GREETINGS_LIST)}, {ctx.message.author.mention}!')

    @commands.slash_command(name="кубик", name_localizations=LOCAL["command_dice_name"],
                            description_localizations=LOCAL["command_dice_description"], guild_ids=GUILD_IDS)
    @option(name="sides", type=int, default=6, name_localizations=LOCAL["command_dice_option_sides_name"],
            description_localizations=LOCAL["command_dice_option_sides_description"], required=False)
    async def dice_(self, ctx, sides):
        await ctx.respond(random.randint(1, sides))

    @commands.command(aliases=["счёт", "калькулятор", "подсчёт", "к"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def calc(self, ctx, *, arg):
        async with ctx.channel.typing():
            arg = arg.replace("π", str(math.pi)).replace("E", str(math.e))
            try:
                res = run_until(7, numexpr.evaluate, arg)
                await ctx.reply(f"Результат: {res}")
            except Exception as e:
                print(e)
        await ctx.reply("Произошла ошибка.")

    @commands.command(aliases=["c", "кот", "Кот", "Cat", "🐱"])
    async def cat(self, ctx):
        async with ctx.channel.typing():
            response = requests.get("https://api.thecatapi.com/v1/images/search?mime_types=jpg,png")
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайный Кот")
            embed.set_image(url=response.json()[0]["url"])
        await ctx.reply(embed=embed)

    @commands.command(aliases=["d", "собака", "Пёс", "Собака", "Dog", "🐶"])
    async def dog(self, ctx):
        async with ctx.channel.typing():
            response = requests.get("https://api.thedogapi.com/v1/images/search?mime_types=jpg,png")
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Собака")
            embed.set_image(url=response.json()[0]["url"])
        await ctx.reply(embed=embed)

    @commands.command(aliases=["лиса", "лис", "Fox", "Лис", "Лиса", "🦊"])
    async def fox(self, ctx):
        async with ctx.channel.typing():
            response = requests.get("https://randomfox.ca/floof")
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Лиса")
            embed.set_image(url=response.json()["image"])
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(BaseCommands(bot))
