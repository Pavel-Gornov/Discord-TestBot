from discord.ext import commands
import discord
from storage import *
import datetime
import math

COG_NAME: final = "экономики"
ECONOMY_EMOJIS = {"p1-1": "<:p1_1:1180851390462050354>",
                  "p1-0": "<:p1_0:1180851387714773043>",
                  "p2-1": "<:p2_1:1180851382501244998>",
                  "p2-0": "<:p2_0:1180851391732928604>",
                  "p3-1": "<:p3_1:1180851385936379914>",
                  "p3-0": "<:p3_0:1180851383587569685>",
                  "xp": "<:xp:1181316539014729842>",
                  "t1": "<:t1_1:1181317290365567066>",
                  "t0": "<:t1_0:1181318824369344573>",
                  "arrow_right": "<:arrow_right:1184914573292228719>",
                  "arrow_down": "<:arrow_down:1184914574659563700>",
                  "space": "<:space:1184930883917070396>"}


class BusinessUI:
    def __init__(self, user_id: int, buttons=None):
        self.user_data = economy_data[str(user_id)]["business"]
        self.embed = self._make_embed()
        if datetime.datetime.now() - datetime.datetime.fromtimestamp(
                self.user_data["last_collection"]) < datetime.timedelta(minutes=1):
            if buttons:
                buttons = (buttons[0], False, buttons[2])
            else:
                buttons = (True, False, True)
        self.view = BusinessView(user_id, buttons)

    def _make_embed(self):
        if self.user_data:
            dt = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.user_data["last_collection"])
            embed = discord.Embed(
                title=self.user_data["name"],
                description=self.user_data["desc"])
            embed.add_field(name="Статистика", value=f"Общая прибыль: {self.user_data['revenue']} 🪙\n"
                                                     f"Накоплено в хранилище: {min(dt.seconds, 10000)}/10000 🪙")
            if "img" in self.user_data.keys():
                embed.set_image(url=self.user_data["img"])
            return embed
        return None


class BusinessView(discord.ui.View):
    def __init__(self, author_id: int, buttons=None):
        super().__init__(timeout=300, disable_on_timeout=True)
        self.author_id = author_id
        if buttons:
            for i in range(len(buttons)):
                if buttons[i] is not None:
                    if buttons[i]:
                        self.children[i].disabled = False
                    else:
                        self.children[i].disabled = True
            n = 0
            for i in range(len(buttons)):
                if buttons[i] is None:
                    self.children.pop(n)
                else:
                    n += 1

    async def on_timeout(self):
        if self.children:
            self.clear_items()
        await super().on_timeout()

    @discord.ui.button(label="Закрыть окно", style=discord.ButtonStyle.red, custom_id="close")
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Собрать прибыль", emoji="🪙", style=discord.ButtonStyle.gray, custom_id="collect")
    async def collect(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            embed = make_business_collect_popup(economy_data[str(interaction.user.id)]["business"])
            await interaction.response.send_message(embed=embed, ephemeral=True)
            b_ui = BusinessUI(self.author_id)
            await interaction.message.edit(embed=b_ui.embed, view=b_ui.view)
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)

    @discord.ui.button(label="Навыки", style=discord.ButtonStyle.primary, custom_id="skills")
    async def skills(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            bs_ui = BusinessSkillsUI(self.author_id)
            await interaction.response.edit_message(embed=bs_ui.embed, view=bs_ui.view)
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)


class BusinessSkillsUI:
    def __init__(self, user_id: int, buttons=None):
        self.user_data = economy_data[str(user_id)]["business"]
        self.embed = self._make_embed()
        self.view = BusinessSkillsView(user_id, buttons)

    def _make_embed(self):
        if self.user_data:
            level = int(math.log((self.user_data["xp"] * 0.8 / 100) + 1, 1.8)) + 1
            xp_current = round(self.user_data["xp"] - ((100 * (1.8 ** (level - 1) - 1)) / 0.8))
            xp_next = round(100 * (1.8 ** (level - 1)))
            embed = discord.Embed(title=f"**Навыки** ({self.user_data['name']})",
                                  description=f"Текущий уровень предприятия: {level}\n"
                                              f"Опыт: {xp_current}/{xp_next} {ECONOMY_EMOJIS['xp']}\n"
                                              f"Очки навыков: {self.user_data['sp']} 🔱\n"
                                              f"{self._progress_bar(xp_current / xp_next)} ур.{level + 1}")
            embed.add_field(name="Ветка навыков: Производство",
                            value=f"{self._t1_bar()}\n"
                                  f"({self.user_data['upgrades']['T1']} из 8) Следующий - 100 🪙",
                            inline=False)
            embed.add_field(name="Ветка навыков: Развитие",
                            value=f"{ECONOMY_EMOJIS['t1']}{ECONOMY_EMOJIS['arrow_right']}{ECONOMY_EMOJIS['t0']}\n"
                                  f"{ECONOMY_EMOJIS['arrow_down']}{ECONOMY_EMOJIS['space']}{ECONOMY_EMOJIS['arrow_down']}\n"
                                  f"{ECONOMY_EMOJIS['t0']}",
                            inline=False)
            return embed
        return None

    def _progress_bar(self, num: float, length: int = 10) -> str:
        bar = ""
        t = num * length
        bar += (ECONOMY_EMOJIS[f"p1-{int(t >= 1)}"])
        for i in range(2, length):
            bar += (ECONOMY_EMOJIS[f"p2-{int(t >= i)}"])
        bar += (ECONOMY_EMOJIS[f"p3-{int(t >= length)}"])
        return bar

    def _t1_bar(self):
        level = self.user_data['upgrades']['T1']
        bar = ""
        for i in range(8):
            if level > i:
                bar += ECONOMY_EMOJIS['t1']
            else:
                bar += ECONOMY_EMOJIS['t0']
            if i < 7:
                bar += "→"
        return bar


class BusinessSkillsView(discord.ui.View):
    def __init__(self, author_id: int, buttons=None):
        super().__init__(timeout=300, disable_on_timeout=True)
        self.author_id = author_id
        if buttons:
            for i in range(len(buttons)):
                if buttons[i] is not None:
                    if buttons[i]:
                        self.children[i].disabled = False
                    else:
                        self.children[i].disabled = True
            n = 0
            for i in range(len(buttons)):
                if buttons[i] is None:
                    self.children.pop(n)
                else:
                    n += 1

    async def on_timeout(self):
        self.clear_items()
        await super().on_timeout()

    @discord.ui.button(label="Закрыть окно", style=discord.ButtonStyle.red, custom_id="close")
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.primary, custom_id="back")
    async def skills(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            b_ui = BusinessUI(user_id=self.author_id)
            await interaction.response.edit_message(embed=b_ui.embed, view=b_ui.view)
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)
        self.stop()


class BusinessSkillsBranchMainUI:
    def __init__(self, user_id: int, buttons=None):
        self.user_data = economy_data[str(user_id)]["business"]
        self.embed = self._make_embed()
        self.view = BusinessSkillsBranchMainView(user_id, buttons)

    def _make_embed(self):
        embed = discord.Embed(title="Ветка 1", description=f"{ECONOMY_EMOJIS['t1']}")
        return embed


class BusinessSkillsBranchMainView(discord.ui.View):
    def __init__(self, author_id: int, buttons=None):
        super().__init__(timeout=300, disable_on_timeout=True)
        self.author_id = author_id
        if buttons:
            for i in range(len(buttons)):
                if buttons[i] is not None:
                    if buttons[i]:
                        self.children[i].disabled = False
                    else:
                        self.children[i].disabled = True
            n = 0
            for i in range(len(buttons)):
                if buttons[i] is None:
                    self.children.pop(n)
                else:
                    n += 1

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.primary, custom_id="back")
    async def skills(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            b_ui = BusinessSkillsUI(user_id=self.author_id)
            await interaction.response.edit_message(embed=b_ui.embed, view=b_ui.view)
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)
        self.stop()


def make_business_collect_popup(user_data: dict):
    if user_data:
        dt = datetime.datetime.now() - datetime.datetime.fromtimestamp(user_data["last_collection"])
        if dt > datetime.timedelta(minutes=1):
            r = min(dt.seconds, 10000)
            xp = r / 25
            level = int(math.log((user_data["xp"] * 0.8 / 100) + 1, 1.8)) + 1
            level2 = int(math.log(((user_data["xp"] + xp) * 0.8 / 100) + 1, 1.8)) + 1
            embed = discord.Embed(title=f"Результат", description=f"Получено: {r} 🪙 {xp} {ECONOMY_EMOJIS['xp']}")
            if level2 - level > 0:
                embed.add_field(name="Новый уровень!", value=f"Достигнут {level2}-й уровень!")
            user_data["last_collection"] = datetime.datetime.now().timestamp()
            user_data['revenue'] += r
            user_data['xp'] += xp
            return embed
        else:
            embed = discord.Embed(title=f"Результат", description=f"Вы не можете собрать прибыль сейчас.")
            return embed
    return None


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль {COG_NAME} успешно загружен!")

    @commands.slash_command(name="бизнес", guild_ids=[1076117733428711434, 1055895511359574108])
    @discord.commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def business(self, ctx):
        if str(ctx.author.id) in economy_data:
            user_data = economy_data[str(ctx.author.id)]["business"]
            b_ui = BusinessUI(ctx.author.id)
            await ctx.respond(view=b_ui.view, embed=b_ui.embed)
        else:
            view = BusinessView(ctx.author.id, (True, None, None))
            await ctx.respond(embed=discord.Embed(title="Пустова-то тут.",
                                                  description=f"У вас нет бизнеса. Используйте </бизнес-создать:1178417237443481712>"),
                              view=view)

    @commands.slash_command(name="бизнес-создать", guild_ids=[1055895511359574108, 1076117733428711434])
    @discord.commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def business_1(self, ctx,
                         name: discord.Option(str, max_length=30, default="Предприятие без названия", required=False),
                         description: discord.Option(str, max_length=200, default="", required=False),
                         img: discord.Option(str, max_length=200, required=False, default=None)):
        author_id = str(ctx.author.id)
        if str(ctx.author.id) in economy_data:
            view = Confirm()
            await ctx.respond("У вас уже есть бизнес. Уверены, что хотите создать его заново?", view=view,
                              ephemeral=True)
            await view.wait()
            if not view.value:
                return
        economy_data[author_id] = {"business": {}}
        economy_data[author_id]["business"]["name"] = name
        economy_data[author_id]["business"]["desc"] = description
        economy_data[author_id]["business"]["xp"] = 0
        economy_data[author_id]["business"]["sp"] = 0
        economy_data[author_id]["business"]["last_collection"] = datetime.datetime.now().timestamp()
        economy_data[author_id]["business"]["revenue"] = 0
        economy_data[author_id]["business"]["upgrades"] = {"T1": 1}
        try:
            if img:
                img = img.split("?")[0]
                if img.startswith("https://") and (img.endswith(".png") or img.endswith(".jpg")):
                    economy_data[author_id]["business"]["img"] = img
        except Exception as e:
            print(e)
        await ctx.respond(embed=discord.Embed(title="Успех!",
                                              description=f"Предприятие {name} было успешно зарегистрировано. Владелец: {ctx.author.mention}",
                                              color=COLOR_CODES["success"]))


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="Да", style=discord.ButtonStyle.green)
    async def confirm_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Подтверждено.", view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label="Нет", style=discord.ButtonStyle.red)
    async def cancel_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Отменено.", view=None)
        self.value = False
        self.stop()


def setup(bot):
    bot.add_cog(Economy(bot))
