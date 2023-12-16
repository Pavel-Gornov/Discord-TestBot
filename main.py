import os
import random

import aiohttp
from discord import Option

from lib.utils import makeDSTimestamp, get_guild_lang, is_emoji
from discord.ext import commands
import discord
from storage import *

bot = commands.Bot(command_prefix=commands.when_mentioned_or(SETTINGS['prefix']), intents=discord.Intents.all())


class CustomHelpCommand(commands.HelpCommand):
    def cog_filter(self, string):
        for cog in self.context.bot.cogs:
            if cog in LOCAL["cogs"].keys():
                if string in LOCAL["cogs"][cog].values():
                    return cog
        return string

    async def command_callback(self, ctx, *, command=None):
        if command:
            command = self.cog_filter(command)
        await super().command_callback(ctx=ctx, command=command)

    def get_command_signature(self, command):
        return f"{self.context.clean_prefix}{command.qualified_name} {command.signature}"

    async def send_bot_help(self, mapping):
        language = get_guild_lang(self.context.guild)

        embed = discord.Embed(title=LOCAL["help_help"][language], colour=COLOR_CODES["bot"])
        embed.set_thumbnail(url=BOT_ICON_URL)
        for cog, bot_commands in mapping.items():
            command_signatures = list()
            for c in bot_commands:
                if isinstance(c, discord.ext.commands.Command):
                    if c.aliases:
                        command_signatures.append(
                            f"`{self.context.clean_prefix}{c.qualified_name}` {c.signature}")
                    else:
                        command_signatures.append(f"`{self.context.clean_prefix}{c.qualified_name}`")
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", None)
                if cog_name:
                    cog_name = LOCAL["cogs"][cog.qualified_name][language]
                else:
                    cog_name = LOCAL["help_no_category"][language]
                embed.add_field(name=f"{cog_name}:", value="\n\t".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        language = get_guild_lang(self.context.guild)

        embed = discord.Embed(title=f"{LOCAL['help_command'][language]} {self.get_command_signature(command)}",
                              colour=COLOR_CODES["bot"])
        embed.set_thumbnail(url=BOT_ICON_URL)
        if command.help:
            embed.description = LOCAL[command.help][language]
        else:
            embed.description = LOCAL["help_no_info"][language]
        if command.aliases:
            embed.add_field(name=LOCAL["help_aliases"][language],
                            value=f'{command.qualified_name}, {", ".join(command.aliases)}',
                            inline=False)

        await self.get_destination().send(embed=embed)

    # TODO: Добавить группы команд для полноценной работы данной части команды
    async def send_group_help(self, group):
        language = get_guild_lang(self.context.guild)

        embed = discord.Embed(title=self.get_command_signature(group), description=group.help, color=COLOR_CODES["bot"])
        embed.set_thumbnail(url=BOT_ICON_URL)

        filtered_commands = await self.filter_commands(group.commands)

        if filtered_commands:
            for command in filtered_commands:
                embed.add_field(name=self.get_command_signature(command),
                                value=LOCAL[command.help][language] if command.help else LOCAL["help_no_info"][
                                    language])

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        language = get_guild_lang(self.context.guild)

        embed = discord.Embed(
            title=f'{LOCAL["cogs"][cog.qualified_name][language] or LOCAL["help_no_category"][language]}:',
            description=cog.description,
            color=COLOR_CODES["bot"])
        embed.set_thumbnail(url=BOT_ICON_URL)

        filtered_commands = await self.filter_commands(cog.get_commands())

        if filtered_commands:
            for command in filtered_commands:
                embed.add_field(name=self.get_command_signature(command),
                                value=LOCAL[command.help][language] if command.help else LOCAL["help_no_info"][
                                    language])

        await self.get_destination().send(embed=embed)

    def command_not_found(self, string):
        language = get_guild_lang(self.context.guild)

        return LOCAL["help_command_not_found"][language].format(string)


@bot.slash_command(name="help", description="")
async def help_(ctx: discord.ApplicationContext):
    language = get_guild_lang(ctx.guild)
    embed = discord.Embed(title=LOCAL["help_help"][language])
    commands_list = list()
    for i in bot.application_commands:
        if i not in commands_list and isinstance(i, discord.SlashCommand):
            if ctx.guild:
                if i.guild_ids:
                    if ctx.guild.id in i.guild_ids:
                        embed.add_field(name=i.name, value=i.mention)
                else:
                    embed.add_field(name=i.name, value=i.mention)
            else:
                if not i.guild_only:
                    embed.add_field(name=i.name, value=i.mention)
            commands_list.append(i)
    await ctx.respond(embed=embed)


@bot.slash_command(name="метка-времени", description="Что-то делает")
async def time_(ctx, year: Option(int, description="Год для даты", required=False) = 1970,
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
    print(f"Бот находиться на {len(bot.guilds)} серверах.")
    print(f'{bot.user.name} запустился и готов к работе!')


@bot.event
async def on_message(message):
    if message.author != bot.user:
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
        embed = discord.Embed(color=COLOR_CODES["error"], title=f'Произошла ошибка!',
                              description=f"Вы сможете использовать эту команду повторно через {round(error.retry_after, 2)} секунд")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.NoPrivateMessage):
        embed = discord.Embed(color=COLOR_CODES["error"], title=f'Произошла ошибка!',
                              description=f"Эта команда предназначена только для серверов.")
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        raise error


@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(color=COLOR_CODES["error"], title=f'Произошла ошибка!',
                              description=f"Вы сможете использовать эту команду повторно через {round(error.retry_after, 2)} секунд")
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        raise error


@bot.slash_command(name=LOCAL["command_avatar_name"][DEFAULT_LANG],
                   description=LOCAL["command_avatar_description"][DEFAULT_LANG],
                   name_localizations=LOCAL["command_avatar_name"],
                   description_localizations=LOCAL["command_avatar_description"])
async def avatar_(ctx, member: Option(discord.Member, name=LOCAL["command_avatar_option_member_name"][DEFAULT_LANG],
                                      description=LOCAL["command_avatar_option_member_description"][DEFAULT_LANG],
                                      name_localizations=LOCAL["command_avatar_option_member_name"],
                                      description_localizations=LOCAL["command_avatar_option_member_description"],
                                      required=False),
                  ephemeral: Option(str, name=LOCAL["command_avatar_option_ephemeral_name"][DEFAULT_LANG],
                                    description=LOCAL["command_avatar_option_ephemeral_description"][DEFAULT_LANG],
                                    name_localizations=LOCAL["command_avatar_option_ephemeral_name"],
                                    description_localizations=LOCAL["command_avatar_option_ephemeral_description"],
                                    choices=(discord.OptionChoice(name=LOCAL["option_choice_yes"][DEFAULT_LANG],
                                                                  name_localizations=LOCAL["option_choice_yes"],
                                                                  value="1"),
                                             discord.OptionChoice(name=LOCAL["option_choice_no"][DEFAULT_LANG],
                                                                  name_localizations=LOCAL["option_choice_no"],
                                                                  value="0")), required=False)):
    author = member if member else ctx.author
    embed = discord.Embed(color=COLOR_CODES["bot"], title=f'Аватар {author}', description=f"id: {author.id}")
    embed.set_image(url=author.avatar.url)
    ephemeral = True if ephemeral == "1" else False
    await ctx.respond(embed=embed, ephemeral=ephemeral)


@bot.slash_command(name=LOCAL["command_dice_name"][DEFAULT_LANG],
                   description=LOCAL["command_dice_description"][DEFAULT_LANG],
                   name_localizations=LOCAL["command_dice_name"],
                   description_localizations=LOCAL["command_dice_description"])
async def dice_(ctx, sides: Option(int, name=LOCAL["command_dice_option_sides_name"][DEFAULT_LANG],
                                   description=LOCAL["command_dice_option_sides_description"][DEFAULT_LANG],
                                   name_localizations=LOCAL["command_dice_option_sides_name"],
                                   description_localizations=LOCAL["command_dice_option_sides_description"],
                                   required=False, default=6, min_value=1)):
    await ctx.respond(random.randint(1, sides))


@bot.slash_command(name="кот", description="", name_localizations=None, description_localizations=None)
@commands.cooldown(1, 5, commands.BucketType.user)
async def cat_(ctx: discord.ApplicationContext):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search?mime_types=jpg,png") as response:
            response = await response.json()
    embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайный Кот")
    embed.set_image(url=response[0]["url"])
    await ctx.respond(embed=embed)


@bot.slash_command(name="пёс", description="", name_localizations=None, description_localizations=None)
@commands.cooldown(1, 5, commands.BucketType.user)
async def dog_(ctx: discord.ApplicationContext):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thedogapi.com/v1/images/search?mime_types=jpg,png") as response:
            response = await response.json()
    embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Собака")
    embed.set_image(url=response[0]["url"])
    await ctx.respond(embed=embed)


@bot.slash_command(name="лис", description="", name_localizations=None, description_localizations=None)
@commands.cooldown(1, 5, commands.BucketType.user)
async def fox_(ctx: discord.ApplicationContext):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://randomfox.ca/floof") as response:
            response = await response.json()
    embed = discord.Embed(color=COLOR_CODES["bot"], title="Случайная Лиса")
    embed.set_image(url=response["image"])
    await ctx.respond(embed=embed)


@bot.slash_command(name='сообщение', description="Отправка сообщений от лица бота.")
@discord.commands.default_permissions(administrator=True)
async def message_(ctx: discord.ApplicationContext,
                   text: Option(str, description='Ваше сообщение.', required=True),
                   channel: Option(discord.TextChannel, description='Канал для отправки сообщения.', required=False)):
    channel = channel if channel else ctx.channel
    await channel.send(text)
    await ctx.respond("Успешно. :white_check_mark:", ephemeral=True)


@bot.slash_command(name='голосование', description="Отправка голосования от лица бота.")
@discord.commands.default_permissions(administrator=True)
@discord.commands.guild_only()
async def vote_(ctx: discord.ApplicationContext,
                text: Option(str, description='Текст сообщения. (";" для переноса строки, "-" между вариантами)',
                             required=True),
                channel: Option(discord.TextChannel, required=False),
                file: Option(discord.Attachment, required=False, default=None)):
    channel = channel if channel else ctx.channel
    file = await file.to_file() if file else None
    text = text.replace(";", "\n")
    reactions = []
    for i in text.split("\n"):
        if "-" in i:
            e = i.split()[0].replace(" ", "")
            if e.startswith("<:") and e.endswith(">") or is_emoji(e):
                reactions.append(e)
    if not reactions:
        reactions = ['✅', '❌']
    message = await channel.send(text.replace(" - ", " — "), file=file)
    for i in reactions:
        await message.add_reaction(i)
    await ctx.respond(embed=discord.Embed(title="Успешно! :white_check_mark:", colour=COLOR_CODES["success"]),
                      ephemeral=True)


@bot.slash_command(name='сервер', description="Информация о сервере. (в разработке)")
@discord.commands.guild_only()
async def server_(ctx: discord.ApplicationContext):
    guild = ctx.guild
    bot_count = len([m for m in guild.members if m.bot])
    embed = discord.Embed(title=f"Сервер {guild.name}", description=f"Описание: {guild.description}",
                          colour=COLOR_CODES["bot"])
    embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Участники:", value=f":globe_with_meridians: Всего: **{guild.member_count}** \n"
                                                     f":green_circle: Люди: **{guild.member_count - bot_count}**\n"
                                                     f":gear: Боты: **{bot_count}**")
    embed.add_field(name="Разное:", value=f'🟪 Уровень буста: **{guild.premium_tier}**\n'
                                          f'🟣 Количество бустов: **{guild.premium_subscription_count}**\n'
                                          f':label: Тип сервера: **{"Большой" if guild.large else "Малый"}**\n'
                                          f'💾 Файлы: до {round(guild.filesize_limit / 1024 ** 2)} Мб')
    embed.add_field(name="Каналы:", value=f"🗄️ Всего: **{len(guild.channels) - len(guild.categories)}**\n"
                                          f"💬 Текстовые: **{len(guild.text_channels)}**\n"
                                          f"🔊 Голосовые: **{len(guild.voice_channels)}**\n"
                                          f"🗃️ Форумы: **{len(guild.forum_channels)}**\n"
                                          f"📣 Объявления: **{len([c for c in guild.text_channels if c.news])}**")
    embed.add_field(name="Владелец:", value=f"{guild.owner.mention}")
    embed.add_field(name="Уровень проверки:", value=f"{guild.verification_level}")
    embed.add_field(name="Дата основания:", value=f"<t:{int(guild.created_at.timestamp())}:D>\n"
                                                  f"<t:{int(guild.created_at.timestamp())}:R>")
    embed.set_footer(text=f"ID: {guild.id}")

    await ctx.respond(embed=embed)


@bot.message_command(name="Аватар пользователя")
async def avatar_msg_command(ctx, message):
    user = message.author
    embed = discord.Embed(color=COLOR_CODES["bot"], title=f'Аватар {user}', description=f"id: {user.id}")
    embed.set_image(url=user.avatar.url)
    await ctx.respond(embed=embed, ephemeral=True)


def main():
    for f in os.listdir("./cogs"):
        if f.endswith("py"):
            bot.load_extension("cogs." + f[:-3])

    bot.help_command = CustomHelpCommand(
        command_attrs={'name': "help", 'aliases': ["helpme", "помощь", "хелп"], 'help': "command_help_info"})

    bot.run(SETTINGS['token'])
    with open("economy.json", mode="w", encoding="utf-8") as f:
        f.write(json.dumps(economy_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
