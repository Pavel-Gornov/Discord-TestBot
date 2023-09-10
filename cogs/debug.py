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
    @discord.commands.default_permissions(administrator=True)
    async def cog(self, ctx):
        await ctx.reply(self.bot.cogs)

    @commands.slash_command(name='тест', description='Что-то делает.', guild_ids=GUILD_IDS)
    async def test_(self, ctx):
        await ctx.respond('Успешный тест!')


def setup(bot):
    bot.add_cog(Test(bot))
