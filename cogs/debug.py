from discord.ext import commands
from storage import *
import discord

COG_NAME: final = "отлидки"


class Test(commands.Cog):
    def __init__(self, bot):
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


def setup(bot):
    bot.add_cog(Test(bot))
