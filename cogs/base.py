import math
import random
import numexpr
from typing import Optional

import discord
import requests
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

    @commands.command(aliases=["error", "hstat" "httpstat", "сеть", "код", "статус"], help="commnad_http_info")
    async def http(self, ctx, status_code: Optional[int] = 200):
        if status_code in REQUEST_CODES:
            await ctx.reply(f"https://http.cat/{status_code}")
        else:
            await ctx.reply("Нет такого кода.")

    @commands.command(aliases=["ava", "ава", "аватарка", "аватар"], help="command_avatar_info")
    async def avatar(self, ctx, user: Optional[discord.Member] = None):
        author = user if user else ctx.message.author
        embed = discord.Embed(color=COLOR_CODES["bot"], title=f'Аватар {author}', description=f"id: {author.id}")
        embed.set_image(url=author.avatar.url)
        await ctx.reply(embed=embed)

    @commands.command(aliases=["rand", "ранд", "случайный", "случ"], help="command_random_info")
    async def random(self, ctx, *, args):
        await ctx.reply(random.choice(args.split(";")))

    @commands.command(aliases=["m", "я", "сообщение"], help="command_me_info")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def me(self, ctx, *, message):
        await ctx.send(message, reference=ctx.message.reference)
        await ctx.message.delete()

    @commands.command(aliases=["hi", "hey", "Привет", "привет", "приветствие"], help="command_hello_info")
    async def hello(self, ctx):
        await ctx.send(f'{random.choice(GREETINGS_LIST)}, {ctx.message.author.mention}!')

    @commands.command(aliases=["счёт", "калькулятор", "подсчёт", "calc", "вычислить"], help="command_calculate_info")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def calculate(self, ctx, *, expression):
        async with ctx.channel.typing():
            expression = expression.replace("π", str(math.pi)).replace("E", str(math.e))
            try:
                res = run_until(7, numexpr.evaluate, expression)
                await ctx.reply(f"Результат: {res}")
            except Exception as e:
                print(e)
        await ctx.reply("Произошла ошибка.")

    @commands.command(aliases=["c", "кот", "Кот", "Cat", "🐱"], help="commnad_cat_info")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cat(self, ctx):
        async with ctx.channel.typing():
            response = requests.get("https://api.thecatapi.com/v1/images/search?mime_types=jpg,png")
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайный Кот")
            embed.set_image(url=response.json()[0]["url"])
        await ctx.reply(embed=embed)

    @commands.command(aliases=["d", "собака", "Пёс", "Собака", "Dog", "🐶"], help="commnad_dog_info")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dog(self, ctx):
        async with ctx.channel.typing():
            response = requests.get("https://api.thedogapi.com/v1/images/search?mime_types=jpg,png")
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Собака")
            embed.set_image(url=response.json()[0]["url"])
        await ctx.reply(embed=embed)

    @commands.command(aliases=["лиса", "лис", "Fox", "Лис", "Лиса", "🦊"], help="commnad_fox_info")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def fox(self, ctx):
        async with ctx.channel.typing():
            response = requests.get("https://randomfox.ca/floof")
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Лиса")
            embed.set_image(url=response.json()["image"])
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(BaseCommands(bot))
