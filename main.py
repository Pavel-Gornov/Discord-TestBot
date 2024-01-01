import os
import random
import aiohttp
import discord
from lib.utils import get_guild_lang, is_emoji, tbsl, Color
from discord.ext import commands
from settings import *
from Token import *

BOT_ICON_URL = "https://media.discordapp.net/attachments/1055896512053399623/1150820899231109271/-.png"


class CustomHelpCommand(commands.HelpCommand):
    def cog_filter(self, string):
        for cog in self.context.bot.cogs:
            if cog in tbsl("cogs").keys():
                if string in tbsl("cogs", cog).values():
                    return cog
        return string

    async def command_callback(self, ctx, *, command=None):
        if command:
            command = self.cog_filter(command)
        await super().command_callback(ctx=ctx, command=command)

    async def send_bot_help(self, mapping):
        language = get_guild_lang(self.context.guild)

        embed = discord.Embed(title=tbsl("help_help", language), colour=Color.BOT.value)
        embed.set_thumbnail(url=BOT_ICON_URL)
        for cog, bot_commands in mapping.items():
            command_signatures = list()
            for c in bot_commands:
                if isinstance(c, discord.ext.commands.Command) and not c.hidden:
                    if c.aliases:
                        command_signatures.append(
                            f"`{self.context.clean_prefix}{c.qualified_name}` {tbsl(c.brief, language)}")
                    else:
                        command_signatures.append(f"`{self.context.clean_prefix}{c.qualified_name}`")
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", None)
                if cog_name:
                    cog_name = tbsl("cogs", cog.qualified_name)[language]
                else:
                    cog_name = tbsl("help_no_category", language)
                embed.add_field(name=f"{cog_name}:", value="\n\t".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        language = get_guild_lang(self.context.guild)

        embed = discord.Embed(
            title=f"{tbsl('help_command', language)} `{self.context.clean_prefix}{command.qualified_name}` {tbsl(command.brief, language)}",
            colour=Color.BOT.value)
        embed.set_thumbnail(url=BOT_ICON_URL)
        if command.description:
            embed.description = tbsl(command.description, language)
        else:
            embed.description = tbsl("help_no_info", language)
        if command.help:
            s = ""
            for i in tbsl(command.help, language).split("\n"):
                s += f"`{self.context.clean_prefix}{command.qualified_name}` {i}\n"
            embed.add_field(name="Примеры использования:",
                            value=s, inline=False)

        if command.aliases:
            embed.add_field(name=tbsl("help_aliases", language),
                            value=f'{command.qualified_name}, {", ".join(command.aliases)}', inline=False)

        await self.get_destination().send(embed=embed)

    # TODO: Добавить группы команд для полноценной работы данной части команды
    async def send_group_help(self, group):
        language = get_guild_lang(self.context.guild)

        embed = discord.Embed(title=self.get_command_signature(group), description=group.help, color=Color.BOT.value)
        embed.set_thumbnail(url=BOT_ICON_URL)

        filtered_commands = await self.filter_commands(group.commands)

        if filtered_commands:
            for command in filtered_commands:
                embed.add_field(name=self.get_command_signature(command),
                                value=tbsl(command.help, language) if command.help else tbsl("help_no_info",
                                                                                             language))
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        language = get_guild_lang(self.context.guild)

        embed = discord.Embed(
            title=f'{tbsl("cogs", cog.qualified_name)[language] or tbsl("help_no_category", language)}:',
            description=cog.description,
            color=Color.BOT.value)
        embed.set_thumbnail(url=BOT_ICON_URL)

        filtered_commands = await self.filter_commands(cog.get_commands())

        if filtered_commands:
            for command in filtered_commands:
                embed.add_field(
                    name=f"`{self.context.clean_prefix}{command.qualified_name}` {tbsl(command.brief, language)}",
                    value=tbsl(command.description, language) if command.description else tbsl("help_no_info",
                                                                                               language))
        await self.get_destination().send(embed=embed)

    def command_not_found(self, string):
        language = get_guild_lang(self.context.guild)
        return tbsl("help_command_not_found", language).format(string)


bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), intents=discord.Intents.all(),
                   help_command=CustomHelpCommand(
                       command_attrs={'name': "help", 'aliases': ["helpme", "помощь", "хелп"],
                                      'help': "command_help_examples", 'description': "command_help_description",
                                      'brief': "command_help_args"}))


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
async def on_message(message: discord.Message):
    if message.author != bot.user:
        if message.content.startswith("t:") and message.author.id == bot.owner_id:
            if message.reference:
                await message.channel.send(message.content[2:], reference=message.reference)
            else:
                await message.channel.send(message.content[2:])
            await message.delete()
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(color=Color.ERROR.value, title=f'Произошла ошибка!',
                              description=f"Вы сможете использовать эту команду повторно через {round(error.retry_after, 2)} секунд")
        await ctx.reply(embed=embed)
    elif isinstance(error, commands.NoPrivateMessage):
        embed = discord.Embed(color=Color.ERROR.value, title=f'Произошла ошибка!',
                              description=f"Эта команда предназначена только для серверов.")
        await ctx.reply(embed=embed)
    elif isinstance(error, commands.errors.GuildNotFound):
        embed = discord.Embed(color=Color.ERROR.value, title=f'Произошла ошибка!',
                              description=f'Сервер "{error.argument}" не найден.')
        await ctx.reply(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        raise error


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(color=Color.ERROR.value, title=f'Произошла ошибка!',
                              description=f"Вы сможете использовать эту команду повторно через {round(error.retry_after, 2)} секунд")
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        raise error


@bot.slash_command(name=tbsl("command_avatar_name", DEFAULT_LANG),
                   description=tbsl("command/_avatar_description", DEFAULT_LANG),
                   name_localizations=tbsl("command_avatar_name"),
                   description_localizations=tbsl("command/_avatar_description"))
async def avatar_(ctx: discord.ApplicationContext,
                  member: discord.Option(discord.Member, required=False,
                                         name=tbsl("command/_avatar_option_member_name", DEFAULT_LANG),
                                         description=tbsl("command/_avatar_option_member_description", DEFAULT_LANG),
                                         name_localizations=tbsl("command/_avatar_option_member_name"),
                                         description_localizations=tbsl("command/_avatar_option_member_description")),
                  ephemeral: discord.Option(str, name=tbsl("command/_avatar_option_ephemeral_name", DEFAULT_LANG),
                                            description=tbsl("command/_avatar_option_ephemeral_description",
                                                             DEFAULT_LANG),
                                            name_localizations=tbsl("command/_avatar_option_ephemeral_name"),
                                            description_localizations=tbsl(
                                                "command/_avatar_option_ephemeral_description"),
                                            choices=(discord.OptionChoice(name=tbsl("option_choice_yes", DEFAULT_LANG),
                                                                          name_localizations=tbsl("option_choice_yes"),
                                                                          value="1"),
                                                     discord.OptionChoice(name=tbsl("option_choice_no", DEFAULT_LANG),
                                                                          name_localizations=tbsl("option_choice_no"),
                                                                          value="0")), required=False)):
    author = member if member else ctx.author
    embed = discord.Embed(color=Color.BOT.value, title=f'Аватар {author}', description=f"id: {author.id}")
    embed.set_image(url=author.avatar.url)
    ephemeral = True if ephemeral == "1" else False
    await ctx.respond(embed=embed, ephemeral=ephemeral)


@bot.slash_command(name=tbsl("command/_dice_name", DEFAULT_LANG),
                   description=tbsl("command/_dice_description", DEFAULT_LANG),
                   name_localizations=tbsl("command/_dice_name"),
                   description_localizations=tbsl("command/_dice_description"))
async def dice_(ctx: discord.ApplicationContext,
                sides: discord.Option(int, name=tbsl("command/_dice_option_sides_name", DEFAULT_LANG),
                                      description=tbsl("command/_dice_option_sides_description", DEFAULT_LANG),
                                      name_localizations=tbsl("command/_dice_option_sides_name"),
                                      description_localizations=tbsl("command/_dice_option_sides_description"),
                                      required=False, default=6, min_value=1)):
    await ctx.respond(random.randint(1, sides))


@bot.slash_command(name="кот", description="", name_localizations=None, description_localizations=None)
@commands.cooldown(1, 5, commands.BucketType.user)
async def cat_(ctx: discord.ApplicationContext):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search?mime_types=jpg,png") as response:
            response = await response.json()
    embed = discord.Embed(color=Color.BOT.value, title="Случайный Кот")
    embed.set_image(url=response[0]["url"])
    await ctx.respond(embed=embed)


@bot.slash_command(name="пёс", description="", name_localizations=None, description_localizations=None)
@commands.cooldown(1, 5, commands.BucketType.user)
async def dog_(ctx: discord.ApplicationContext):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thedogapi.com/v1/images/search?mime_types=jpg,png") as response:
            response = await response.json()
    embed = discord.Embed(color=Color.BOT.value, title="Случайная Собака")
    embed.set_image(url=response[0]["url"])
    await ctx.respond(embed=embed)


@bot.slash_command(name="лис", description="", name_localizations=None, description_localizations=None)
@commands.cooldown(1, 5, commands.BucketType.user)
async def fox_(ctx: discord.ApplicationContext):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://randomfox.ca/floof") as response:
            response = await response.json()
    embed = discord.Embed(color=Color.BOT.value, title="Случайная Лиса")
    embed.set_image(url=response["image"])
    await ctx.respond(embed=embed)


@bot.slash_command(name='сообщение', description="Отправка сообщений от лица бота.")
@discord.commands.default_permissions(administrator=True)
async def message_(ctx: discord.ApplicationContext,
                   text: discord.Option(str, description='Ваше сообщение.', required=True),
                   channel: discord.Option(discord.TextChannel, description='Канал для отправки сообщения.',
                                           required=False)):
    channel = channel if channel else ctx.channel
    await channel.send(text)
    await ctx.respond("Успешно. :white_check_mark:", ephemeral=True)


@bot.slash_command(name='голосование', description="Отправка голосования от лица бота.")
@discord.commands.default_permissions(administrator=True)
@discord.commands.guild_only()
async def vote_(ctx: discord.ApplicationContext,
                text: discord.Option(str,
                                     description='Текст сообщения. (";" для переноса строки, "-" между вариантами)',
                                     required=True),
                channel: discord.Option(discord.TextChannel, required=False),
                file: discord.Option(discord.Attachment, required=False, default=None)):
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
    await ctx.respond(embed=discord.Embed(title="Успешно! :white_check_mark:", colour=Color.SUCCESS.value),
                      ephemeral=True)


@bot.slash_command(name='сервер', description="Информация о сервере. (в разработке)")
@discord.commands.guild_only()
@commands.cooldown(1, 5, commands.BucketType.user)
async def server_(ctx: discord.ApplicationContext):
    language = get_guild_lang(ctx.guild)
    guild = ctx.guild
    bot_count = len([m for m in guild.members if m.bot])
    embed = discord.Embed(title=tbsl("server_title", language).format(guild.name),
                          description=tbsl("server_description", language).format(
                              guild.description if guild.description else tbsl('description_none', language)),
                          colour=Color.BOT.value)
    embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name=tbsl("server_members_name", language),
                    value=tbsl("server_members_value", language).format(guild.member_count,
                                                                        guild.member_count - bot_count, bot_count))
    temp = round(guild.filesize_limit / 1024 ** 2)
    embed.add_field(name=tbsl("server_miscellaneous_name", language),
                    value=tbsl("server_miscellaneous_value", language).format(guild.premium_tier,
                                                                              guild.premium_subscription_count,
                                                                              tbsl("server_size_large",
                                                                                   language) if guild.large else
                                                                              tbsl("server_size_small", language),
                                                                              25 if temp == 8 else temp))
    embed.add_field(name=tbsl("server_channels_name", language),
                    value=tbsl("server_channels_value", language).format(len(guild.channels) - len(guild.categories),
                                                                         len(guild.text_channels),
                                                                         len(guild.voice_channels),
                                                                         len(guild.forum_channels),
                                                                         len([c for c in guild.text_channels if
                                                                              c.news])))
    embed.add_field(name=tbsl("server_owner_name", language), value=f"{guild.owner.mention}")
    embed.add_field(name=tbsl("server_verification_level_name", language),
                    value=f"{tbsl(f'verification_{str(guild.verification_level)}', language)}")
    embed.add_field(name=tbsl("server_created_at_name", language),
                    value=f"<t:{int(guild.created_at.timestamp())}:D>\n<t:{int(guild.created_at.timestamp())}:R>")
    embed.set_footer(text=tbsl("server_footer", language).format(guild.id, guild.preferred_locale))

    await ctx.respond(embed=embed)


@bot.slash_command(name="help", description="")
async def help_(ctx: discord.ApplicationContext):
    language = get_guild_lang(ctx.guild)
    embed = discord.Embed(title=tbsl("help_help", language))
    commands_lists = {None: []}
    for cog in bot.cogs.keys():
        commands_lists[cog] = []
    for c in bot.walk_application_commands():
        if isinstance(c, discord.SlashCommand):
            if ctx.guild:
                if c.guild_ids:
                    if ctx.guild.id in c.guild_ids:
                        i = c.cog if not c.cog else c.cog.qualified_name
                        if c.mention not in commands_lists[i]:
                            commands_lists[i].append(c.mention)
                else:
                    commands_lists[c.cog if not c.cog else c.cog.qualified_name].append(c.mention)
            else:
                if not c.guild_only:
                    commands_lists[c.cog if not c.cog else c.cog.qualified_name].append(c.mention)
    for k, v in commands_lists.items():
        if v:
            embed.add_field(name=str(k), value=" ".join(v), inline=False)
    await ctx.respond(embed=embed)


@bot.message_command(name="Аватар пользователя")
async def avatar_msg_command(ctx: discord.ApplicationContext, message: discord.Message):
    user = message.author
    embed = discord.Embed(color=Color.BOT.value, title=f'Аватар {user}', description=f"id: {user.id}")
    embed.set_image(url=user.avatar.url)
    await ctx.respond(embed=embed, ephemeral=True)


def main():
    for f in os.listdir("./cogs"):
        if f.endswith("py") and not f == "economy.py":
            bot.load_extension("cogs." + f[:-3])
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
