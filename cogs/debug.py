import datetime

from discord.ext import commands
from storage import *
import discord

COG_NAME: final = "отлидки"


class Test(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль {COG_NAME} успешно загружен!")

    @commands.command(aliases=["шестерни", "модули", "расширения"])
    @commands.is_owner()
    async def cog(self, ctx):
        await ctx.reply(self.bot.cogs)

    @commands.slash_command(name='тест', description='Что-то делает.')
    async def test_(self, ctx):
        await ctx.respond('Успешный тест!')

    @commands.command(aliases=["пинг"])
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.slash_command(name='очистка', description='Очищает сообщения, почеменные, как "офф-топ"', guild_ids=GUILD_IDS)
    @discord.commands.default_permissions(administrator=True)
    @discord.commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clear_(self, ctx: discord.ApplicationContext, number: discord.Option(int, min_value=0, max_value=1000, default=100, required=False),
                     channel: discord.Option(discord.TextChannel, required=False)):
        channel = channel if channel else ctx.channel
        msgs = list()
        async for x in channel.history(limit=number):
            if ((x.content.startswith("//") or x.content.startswith("(("))
                    #and "⭐" not in [i.emoji for i in x.reactions]
                    and datetime.datetime.now(x.created_at.tzinfo) - x.created_at <= datetime.timedelta(days=14) and not x.pinned):
                msgs.append(x)
        await ctx.respond(f"Будет удлено {len(msgs)} сообщений.", delete_after=10)
        for i in range(0, len(msgs), 100):
            await channel.delete_messages(msgs[i:i+100], reason="Очистка")


def setup(bot):
    bot.add_cog(Test(bot))
