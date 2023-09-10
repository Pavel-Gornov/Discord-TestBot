from discord.ext import commands
from discord import Option, Member, Embed
from main import json_data
from storage import *

# TODO: Доделать этот моудль
COG_NAME: final = "экономики"


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль {COG_NAME} успешно загружен!")

    @commands.slash_command(name='баланс', description='Баланс пользователя.', guild_ids=GUILD_IDS)
    async def bal_(self, ctx, user: Option(Member, description='Участник сервера', required=False)):
        user = user if user else ctx.author
        embed = Embed(colour=user.colour)
        embed.set_author(name=user.name, icon_url=user.avatar.url)
        if str(user.id) in json_data:
            balance = json_data[str(user.id)]
            embed.description = f"**Статистика**\n" \
                                f"🪙 {balance}"
        else:
            if user == ctx.author:
                json_data[str(ctx.author.id)] = 0
                balance = 0
                embed.description = f"**Статистика**\n" \
                                    f"🪙 {balance}"
            else:
                embed.description = "Нет записи о пользователе."
        await ctx.respond(embed=embed)

    @commands.slash_command(name='таблица-лидеров', description='В разработке', guild_ids=GUILD_IDS)
    async def lb_(self, ctx):
        embed = Embed(colour=COLOR_CODES["bot"])
        embed.set_author(name="Таблица лидеров", icon_url=self.bot.user.avatar.url)
        s = ""
        data = sorted(json_data.items(), key=lambda x: x[1], reverse=True)
        for i in range(min(5, len(json_data))):
            s += f"**{i + 1}. {self.bot.get_user(int(data[i][0]))}** • 🪙{data[i][1]}\n"
        if str(ctx.author.id) in json_data:
            user = (str(ctx.author.id), json_data[(str(ctx.author.id))])
            s += f"Вы на {data.index(user) + 1} месте."
        else:
            s += "Вас в этом списке нет."
        embed.description = s
        await ctx.respond(embed=embed)

    @commands.command(aliases=["баланс", "бал", "стат", "stat", "bal"])
    async def balance(self, ctx, user_id=None):
        user = ctx.author
        if user_id:
            try:
                user = self.bot.get_user(int(user_id)) if user_id.isdigit() else self.bot.get_user(int(user_id[2:-1]))
            except Exception as e:
                user = None
                print(e)
                await ctx.send("Произошла ошибка")
        if user:
            embed = Embed(colour=user.colour)
            embed.set_author(name=user.name, icon_url=user.avatar.url)
            if str(user.id) in json_data:
                balance = json_data[str(user.id)]
                embed.description = f"**Статистика**\n" \
                                    f"🪙{balance}"
            else:
                if user == ctx.author:
                    json_data[str(ctx.author.id)] = 0
                    balance = 0
                    embed.description = f"**Статистика**\n" \
                                        f"🪙{balance}"
                else:
                    embed.description = "Нет записи о пользователе."
            await ctx.send(embed=embed)

    @commands.command(aliases=["лидеры", "лид", "lb", "табл"])
    async def leaderboard(self, ctx):
        embed = Embed(colour=COLOR_CODES["bot"])
        embed.set_author(name="Таблица лидеров", icon_url=self.bot.user.avatar.url)
        s = ""
        data = sorted(json_data.items(), key=lambda x: x[1], reverse=True)
        for i in range(min(5, len(json_data))):
            s += f"**{i + 1}. {self.bot.get_user(int(data[i][0]))}** • 🪙{data[i][1]}\n"
        if str(ctx.author.id) in json_data:
            user = (str(ctx.author.id), json_data[(str(ctx.author.id))])
            s += f"Вы на {data.index(user) + 1} месте."
        else:
            s += "Вас в этом списке нет."
        embed.description = s
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Economy(bot))
