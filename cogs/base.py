import random
from typing import Optional

import discord
import aiohttp
from discord.ext import commands

from storage import *

COG_NAME: final = "основных команд"


class BaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль {COG_NAME} успешно загружен!")

    @commands.command(aliases=["error", "hstat" "httpstat", "сеть", "код", "статус"], help="command_http_info")
    async def http(self, ctx, status_code: Optional[int] = 200):
        if status_code in REQUEST_CODES:
            await ctx.reply(f"https://http.cat/{status_code}")
        else:
            await ctx.reply("Нет такого кода.")

    @commands.command(aliases=["ava", "ава", "аватарка", "аватар"], help="command_avatar_info")
    async def avatar(self, ctx, user: Optional[discord.Member]):
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

    @commands.command(aliases=["c", "кот", "Кот", "Cat", "🐱"], help="command_cat_info")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cat(self, ctx):
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.thecatapi.com/v1/images/search?mime_types=jpg,png") as response:
                    response = await response.json()
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайный Кот")
            embed.set_image(url=response[0]["url"])
        await ctx.reply(embed=embed)

    @commands.command(aliases=["d", "собака", "Пёс", "Собака", "Dog", "🐶"], help="command_dog_info")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dog(self, ctx):
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.thedogapi.com/v1/images/search?mime_types=jpg,png") as response:
                    response = await response.json()
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Собака")
            embed.set_image(url=response[0]["url"])
        await ctx.reply(embed=embed)

    @commands.command(aliases=["лиса", "лис", "Fox", "Лис", "Лиса", "🦊"], help="command_fox_info")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def fox(self, ctx):
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://randomfox.ca/floof") as response:
                    response = await response.json()
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Лиса")
            embed.set_image(url=response["image"])
        await ctx.reply(embed=embed)


def setup(bot: discord.Bot):
    bot.add_cog(BaseCommands(bot))
