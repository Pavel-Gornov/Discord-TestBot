import random
from typing import Optional

import discord
import aiohttp
from discord.ext import commands

from lib.utils import get_guild_lang
from storage import *

COG_NAME: final = "основных команд"


class BaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль {COG_NAME} успешно загружен!")

    @commands.command(aliases=["сервер", "guild", "серв"], description="command_server_description",
                      help="command_server_examples", brief="command_server_args")
    @discord.commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def server(self, ctx: commands.Context, *, guild: commands.GuildConverter = None):
        language = get_guild_lang(ctx.guild)
        if guild is None:
            guild = ctx.guild

        bot_count = len([m for m in guild.members if m.bot])
        embed = discord.Embed(title=LOCAL["server_title"][language].format(guild.name),
                              description=LOCAL["server_description"][language].format(
                                  guild.description if guild.description else LOCAL['description_none'][language]),
                              colour=COLOR_CODES["bot"])
        embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name=LOCAL["server_members_name"][language],
                        value=LOCAL["server_members_value"][language].format(guild.member_count,
                                                                             guild.member_count - bot_count, bot_count))
        temp = round(guild.filesize_limit / 1024 ** 2)
        embed.add_field(name=LOCAL["server_miscellaneous_name"][language],
                        value=LOCAL["server_miscellaneous_value"][language].format(guild.premium_tier,
                                                                                   guild.premium_subscription_count,
                                                                                   LOCAL["server_size_large"][
                                                                                       language] if guild.large else
                                                                                   LOCAL["server_size_small"][language],
                                                                                   25 if temp == 8 else temp))
        embed.add_field(name=LOCAL["server_channels_name"][language],
                        value=LOCAL["server_channels_value"][language].format(
                            len(guild.channels) - len(guild.categories), len(guild.text_channels),
                            len(guild.voice_channels), len(guild.forum_channels),
                            len([c for c in guild.text_channels if c.news])))
        embed.add_field(name=LOCAL["server_owner_name"][language], value=f"{guild.owner.mention}")
        embed.add_field(name=LOCAL["server_verification_level_name"][language],
                        value=f"{LOCAL[f'verification_{str(guild.verification_level)}'][language]}")
        embed.add_field(name=LOCAL["server_created_at_name"][language],
                        value=f"<t:{int(guild.created_at.timestamp())}:D>\n<t:{int(guild.created_at.timestamp())}:R>")
        embed.set_footer(text=LOCAL["server_footer"][language].format(guild.id, guild.preferred_locale))

        await ctx.reply(embed=embed)

    @commands.command(aliases=["error", "hstat" "httpstat", "сеть", "код", "статус"],
                      description="command_http_description", help="command_http_examples", brief="command_http_args")
    async def http(self, ctx: commands.Context, status_code: Optional[int] = 200):
        if status_code in REQUEST_CODES:
            await ctx.reply(f"https://http.cat/{status_code}")
        else:
            await ctx.reply("Нет такого кода.")

    @commands.command(aliases=["pfp", "ava", "ава", "аватарка", "аватар"], description="command_avatar_description",
                      help="command_avatar_examples", brief="command_avatar_args")
    async def avatar(self, ctx: commands.Context, user: Optional[discord.User]):
        if user is None:
            user = ctx.message.author
        embed = discord.Embed(color=COLOR_CODES["bot"], title=f'Аватар {user}', description=f"id: {user.id}")
        embed.set_image(url=user.avatar.url)
        await ctx.reply(embed=embed)

    @commands.command(aliases=["rand", "ранд", "случайный", "случ"], description="command_random_description",
                      help="command_random_examples", brief="command_random_args")
    async def random(self, ctx: commands.Context, *, args):
        await ctx.reply(random.choice(args.split(";")))

    @commands.command(aliases=["m", "я", "сообщение"], description="command_me_description", help="command_me_examples",
                      brief="command_me_args", hidden=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def me(self, ctx: commands.Context, *, message):
        await ctx.send(message, reference=ctx.message.reference)
        await ctx.message.delete()

    @commands.command(aliases=["hi", "hey", "Привет", "привет", "приветствие"], description="command_hello_description",
                      hidden=True)
    async def hello(self, ctx: commands.Context):
        await ctx.send(f'{random.choice(GREETINGS_LIST)}, {ctx.message.author.mention}!')

    @commands.command(aliases=["кот", "Кот", "Cat", "🐱"], description="command_cat_description")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cat(self, ctx: commands.Context):
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.thecatapi.com/v1/images/search?mime_types=jpg,png") as response:
                    response = await response.json()
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайный Кот")
            embed.set_image(url=response[0]["url"])
        await ctx.reply(embed=embed)

    @commands.command(aliases=["собака", "Пёс", "Собака", "Dog", "🐶"], description="command_dog_description")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dog(self, ctx: commands.Context):
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.thedogapi.com/v1/images/search?mime_types=jpg,png") as response:
                    response = await response.json()
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Собака")
            embed.set_image(url=response[0]["url"])
        await ctx.reply(embed=embed)

    @commands.command(aliases=["лиса", "лис", "Fox", "Лис", "Лиса", "🦊"], description="command_fox_description")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def fox(self, ctx: commands.Context):
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get("https://randomfox.ca/floof") as response:
                    response = await response.json()
            embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Лиса")
            embed.set_image(url=response["image"])
        await ctx.reply(embed=embed)


def setup(bot: discord.Bot):
    bot.add_cog(BaseCommands(bot))
