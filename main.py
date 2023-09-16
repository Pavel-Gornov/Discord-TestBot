import os
import random

import requests
from discord import Option
from lib.utils import makeDSTimestamp, get_guild_lang
from lib import mnl_mod, mnllib
from discord.ext import commands
import discord
from storage import *

bot = commands.Bot(command_prefix=commands.when_mentioned_or(SETTINGS['prefix']), intents=discord.Intents.all())


class CustomHelpCommand(commands.HelpCommand):
    def cog_filter(self, string):
        for cog in self.context.bot.cogs:
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
                    cog_name = LOCAL["help_no_сategory"][language]
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
            title=f'{LOCAL["cogs"][cog.qualified_name][language] or LOCAL["help_no_сategory"][language]}:',
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


@bot.slash_command(name="help")
async def help_(ctx):
    language = get_guild_lang(ctx.guild)
    embed = discord.Embed(title=LOCAL["help_help"][language])
    for i in bot.application_commands:
        if isinstance(i, discord.SlashCommand):
            embed.add_field(name=i.name, value=i.mention)
    await ctx.respond(embed=embed)


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
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Эта команда предназначеня только для серверов.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        raise error


@bot.slash_command(name=LOCAL["command_avatar_name"][DEFULT_LANG],
                   description=LOCAL["command_avatar_description"][DEFULT_LANG],
                   name_localizations=LOCAL["command_avatar_name"],
                   description_localizations=LOCAL["command_avatar_description"])
async def avatar_(ctx, member: Option(discord.Member, name=LOCAL["command_avatar_option_member_name"][DEFULT_LANG],
                                      description=LOCAL["command_avatar_option_member_description"][DEFULT_LANG],
                                      name_localizations=LOCAL["command_avatar_option_member_name"],
                                      description_localizations=LOCAL["command_avatar_option_member_description"],
                                      required=False),
                  ephemeral: Option(str, name=LOCAL["command_avatar_option_ephemeral_name"][DEFULT_LANG],
                                    description=LOCAL["command_avatar_option_ephemeral_description"][DEFULT_LANG],
                                    name_localizations=LOCAL["command_avatar_option_ephemeral_name"],
                                    description_localizations=LOCAL["command_avatar_option_ephemeral_description"],
                                    choices=(discord.OptionChoice(name=LOCAL["option_choice_yes"][DEFULT_LANG],
                                                                  name_localizations=LOCAL["option_choice_yes"],
                                                                  value="False"),
                                             discord.OptionChoice(name=LOCAL["option_choice_no"][DEFULT_LANG],
                                                                  name_localizations=LOCAL["option_choice_no"],
                                                                  value="True")), required=False)):
    author = member if member else ctx.author
    embed = discord.Embed(color=COLOR_CODES["bot"], title=f'Аватар {author}', description=f"id: {author.id}")
    embed.set_image(url=author.avatar.url)
    await ctx.respond(embed=embed, ephemeral=bool(ephemeral))


@bot.slash_command(name=LOCAL["command_dice_name"][DEFULT_LANG],
                   description=LOCAL["command_dice_description"][DEFULT_LANG],
                   name_localizations=LOCAL["command_dice_name"],
                   description_localizations=LOCAL["command_dice_description"])
async def dice_(ctx, sides: Option(int, name=LOCAL["command_dice_option_sides_name"][DEFULT_LANG],
                                   description=LOCAL["command_dice_option_sides_description"][DEFULT_LANG],
                                   name_localizations=LOCAL["command_dice_option_sides_name"],
                                   description_localizations=LOCAL["command_dice_option_sides_description"],
                                   required=False, default=6, min_value=1)):
    await ctx.respond(random.randint(1, sides))


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
async def vote_(ctx,
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

        mnl_e = mnllib.__ENGINES__['default']()
        mnl_e.load_module(mnllib.modules.MnLBaseModule())
        fio = mnl_mod.MnLFakeIOModule()
        mnl_e.load_module(fio)

        try:
            mnl_e.run(code_input)
            embed = discord.Embed(colour=COLOR_CODES["success"], title="Вывод программы:", description=fio.stdout)
        except mnllib.exceptions.MnLParserError as pe:
            embed = discord.Embed(colour=COLOR_CODES["error"], title="Ошибка при выполненни программы!",
                                  description=f"Parser error: {pe.message} / {pe.string}")
        except mnllib.exceptions.MnLExecutorError as ee:
            embed = discord.Embed(colour=COLOR_CODES["error"], title="Ошибка при выполненни программы!",
                                  description=f"Executor error: {ee.message} / token #{ee.tokenid}: "
                                              f"{mnl_e.strparset(ee.token)} / {str(type(ee.exc))[8:-2]} - {ee.exc}")
        except mnllib.exceptions.MnLSecurityError as se:
            embed = discord.Embed(colour=COLOR_CODES["error"], title="Ошибка при выполненни программы!",
                                  description=f"Security error: code {se.code}")
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
    await ctx.reply(embed=embed)


@bot.message_command(name="Аватар пользователя")
async def avatar_msg_command(ctx, message):
    user = message.author
    embed = discord.Embed(color=COLOR_CODES["bot"], title=f'Аватар {user}', description=f"id: {user.id}")
    embed.set_image(url=user.avatar.url)
    await ctx.respond(embed=embed, ephemeral=True)


def main():
    for f in os.listdir("./cogs"):
        if f.endswith(".py") and f != "economy.py":
            bot.load_extension("cogs." + f[:-3])

    bot.help_command = CustomHelpCommand(
        command_attrs={'name': "help", 'aliases': ["helpme", "помощь", "хелп"], 'help': "commnad_help_help"})

    bot.run(SETTINGS['token'])


if __name__ == "__main__":
    main()
