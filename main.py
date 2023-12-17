import os
import random

import aiohttp
from discord import Option

from lib.utils import get_guild_lang, is_emoji
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
    for cog in bot.cogs.values():
        commands_list = list()
        for c in cog.walk_commands():
            if isinstance(c, discord.SlashCommand):
                if ctx.guild:
                    if c.guild_ids:
                        if ctx.guild.id in c.guild_ids:
                            commands_list.append(c.mention)
                    else:
                        commands_list.append(c.mention)
                else:
                    if not c.guild_only:
                        commands_list.append(c)
        embed.add_field(name=cog.qualified_name, value=" ".join(commands_list), inline=False)
    commands_list = list()
    for c in bot.application_commands:
        if isinstance(c, discord.SlashCommand) and c.cog is None:
            if ctx.guild:
                if c.guild_ids:
                    if ctx.guild.id in c.guild_ids:
                        commands_list.append(c.mention)
                else:
                    commands_list.append(c.mention)
            else:
                if not c.guild_only:
                    commands_list.append(c)
    embed.add_field(name="None", value=" ".join(commands_list), inline=False)
    await ctx.respond(embed=embed)


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


@bot.slash_command(name=LOCAL["command_server_name"][DEFAULT_LANG], description=LOCAL["command_server_description"][DEFAULT_LANG],
                   name_localizations=LOCAL["command_server_name"], description_localizations=LOCAL["command_server_description"])
@discord.commands.guild_only()
@commands.cooldown(1, 5, commands.BucketType.user)
async def server_(ctx: discord.ApplicationContext):
    language = get_guild_lang(ctx.guild)
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
                                                                               LOCAL["server_size_large"][language] if guild.large else LOCAL["server_size_small"][language],
                                                                               25 if temp == 8 else temp))
    embed.add_field(name=LOCAL["server_channels_name"][language],
                    value=LOCAL["server_channels_value"][language].format(len(guild.channels) - len(guild.categories), len(guild.text_channels),
                    len(guild.voice_channels), len(guild.forum_channels), len([c for c in guild.text_channels if c.news])))
    embed.add_field(name=LOCAL["server_owner_name"][language], value=f"{guild.owner.mention}")
    embed.add_field(name=LOCAL["server_verification_level_name"][language],
                    value=f"{LOCAL[f'verification_{str(guild.verification_level)}'][language]}")
    embed.add_field(name=LOCAL["server_created_at_name"][language],
                    value=f"<t:{int(guild.created_at.timestamp())}:D>\n<t:{int(guild.created_at.timestamp())}:R>")
    embed.set_footer(text=LOCAL["server_footer"][language].format(guild.id, guild.preferred_locale))

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
