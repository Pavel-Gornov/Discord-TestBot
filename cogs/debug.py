import datetime
import discord
from discord.ext import commands
from lib.utils import makeDSTimestamp

COG_NAME = "отладки"


def number_declension(n: int, string_id: str = None) -> str:
    if n == 1 or str(n)[-1] == "1":
        return f"{n} сообщение"
    elif n in (2, 3, 4) or str(n)[-1] in ("2", "3", "4"):
        return f"{n} сообщения"
    return f"{n} сообщений"


class Test(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль {COG_NAME} успешно загружен!")

    @commands.command(aliases=["шестерни", "модули", "расширения"], hidden=True)
    @commands.is_owner()
    async def cog(self, ctx):
        await ctx.reply(self.bot.cogs)

    @commands.command(aliases=["пинг"], hidden=True)
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.slash_command(name='тест', description='Что-то делает.')
    @commands.is_owner()
    async def test_(self, ctx: discord.ApplicationContext):
        channel = ctx.channel
        msgs = list()
        async for x in channel.history(limit=200):
            if ((x.content.startswith("//") or x.content.startswith("((") or x.content.endswith(
                    "//")) or x.content.startswith(">>") and not x.pinned):
                msgs.append(x)
        m = await ctx.respond(f"Успешный тест!\nБудет удалено {number_declension(len(msgs))}.", delete_after=10)
        m = await m.original_response()
        await m.add_reaction("✅")
        for i in msgs[::-1]:
            await i.delete(reason="Очистка")

    @commands.slash_command(name='очистка', description='Очищает сообщения, помеченные, как "офф-топ"',
                            guild_ids=None
                            # [1076117733428711434, 1055895511359574108, 1144672479399391393]
                            )
    @discord.commands.default_permissions(manage_messages=True, read_message_history=True)
    @discord.commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clear_(self, ctx: discord.ApplicationContext,
                     number: discord.Option(int, min_value=0, max_value=1000, default=100, required=False),
                     channel: discord.Option(discord.TextChannel, required=False)):
        channel = channel if channel else ctx.channel
        msgs = list()
        async for x in channel.history(limit=number):
            if ((x.content.startswith("//") or x.content.startswith("((") or x.content.endswith("//")) or x.content.startswith(">>")
                    and datetime.datetime.now(x.created_at.tzinfo) - x.created_at <= datetime.timedelta(
                        days=14) and not x.pinned):
                msgs.append(x)
        await ctx.respond(f"Будет удалено {number_declension(len(msgs))}.", delete_after=10)
        for i in range(0, len(msgs), 100):
            print(msgs)
            await channel.delete_messages(msgs[i:i + 100], reason="Очистка")

    @commands.slash_command(name="метка-времени", description="Что-то делает")
    @commands.is_owner()
    async def time_(self, ctx, year: discord.Option(int, description="Год для даты", required=False) = 1970,
                    month: discord.Option(int, description="Номер месяца года", required=False) = 1,
                    day: discord.Option(int, description="Номер дня месяца", required=False) = 1,
                    hour: discord.Option(int, description="Час дня", required=False) = 0,
                    minute: discord.Option(int, description="Минута часа", required=False) = 0,
                    second: discord.Option(int, description="Секунда минуты", required=False) = 0,
                    timezone: discord.Option(int, description="Временная зона GMT+n", required=False) = 0,
                    mode: discord.Option(str, description="Тип отображения", choices=("R — Оставшееся время",
                                                                                      "d — Короткая запись даты только цифрами",
                                                                                      "D — Дата с подписью месяца словом",
                                                                                      "f — Дата и время",
                                                                                      "F — Полные день недели, дата и время",
                                                                                      "t — Часы и минуты",
                                                                                      "T — Часы, минуты и секунды"),
                                         required=False) = "R"):
        await ctx.respond(makeDSTimestamp(year, month, day, hour, minute, second, timezone, mode))


def setup(bot):
    bot.add_cog(Test(bot))
