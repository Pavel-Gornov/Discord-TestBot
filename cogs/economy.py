from discord.ext import commands
import discord
from storage import *
import datetime
import math

# TODO: Доделать этот моудль
COG_NAME: final = "экономики"


def make_business_ui(user_data: dict):
    if user_data:
        embed = discord.Embed(
            title=user_data["name"],
            description=user_data["desc"])
        embed.add_field(name="Статистика", value=f"Расчётная прибыль: {user_data['revenue']} 🪙\n"
                                                 f"Всего циклов: 0 🔄")
        embed.set_image(url=user_data["img"])
        return embed
    return None


def make_business_skills_ui(user_data: dict):
    if user_data:
        level = int(math.log((user_data["xp"] * 0.8 / 100) + 1, 1.8)) + 1
        xp_current = round(user_data["xp"] - ((100 * (1.8 ** (level - 1) - 1)) / 0.8))
        xp_next = round(100 * (1.8 ** (level - 1)))
        embed = discord.Embed(title=f"**Навыки** ({user_data['name']})",
                              description=f"Текущий уровень предприятия: {level}\nОпыт: {xp_current}/{xp_next} 🔵\nОчки навыков: {user_data['sp']} 🔱")
        embed.add_field(name="Ветка навыков: Производство", value="🟢 → ◽️ → ◽️ → ◽️ → ◽️ → ◽️ → ◽️ → ◽️\n"
                                                                  f"({user_data['upgrades']['T1']} из 8) Следующий - 100 🪙",
                        inline=False)
        # embed.add_field(name="Ветка навыков: Технологии", value="🟢➡️◻️➡️◻️\n"
        #                                                         "⬇️ㅤ  ⬇️\n"
        #                                                         "◻️➡️◻️", inline=False)
        return embed
    return None


def make_business_collect_ui(user_data: dict):
    if user_data:
        dt = datetime.datetime.now() - datetime.datetime.fromtimestamp(user_data["last_collection"])
        embed = discord.Embed(title=f"Результат", description=f"Получено: {dt.seconds} 🪙")
        user_data["last_collection"] = datetime.datetime.now().timestamp()
        user_data['revenue'] += dt.seconds
        return embed
    return None


class BusinessSkillsView(discord.ui.View):
    def __init__(self, author_id: int, buttons=None):
        super().__init__(timeout=300)
        self.author_id = author_id

    @discord.ui.button(label="Закрыть окно", style=discord.ButtonStyle.red, custom_id="close")
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.primary, custom_id="skills")
    async def skills(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            embed = make_business_ui(economy_data[str(interaction.user.id)]["business"])
            await interaction.response.edit_message(embed=embed, view=BusinessView(self.author_id))
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)


class BusinessView(discord.ui.View):
    def __init__(self, author_id: int, buttons=None):
        super().__init__(timeout=300)
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

    @discord.ui.button(label="Закрыть окно", style=discord.ButtonStyle.red, custom_id="close")
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            await interaction.message.delete()
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)

    @discord.ui.button(label="Собрать прибыль", emoji="🪙", style=discord.ButtonStyle.gray, custom_id="collect")
    async def collect(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            embed = make_business_collect_ui(economy_data[str(interaction.user.id)]["business"])
            await interaction.response.send_message(embed=embed)
            embed = make_business_ui(economy_data[str(interaction.user.id)]["business"])
            await interaction.message.edit(embed=embed, view=BusinessView(self.author_id))
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)

    @discord.ui.button(label="Навыки", style=discord.ButtonStyle.primary, custom_id="skills")
    async def skills(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            embed = make_business_skills_ui(economy_data[str(interaction.user.id)]["business"])
            await interaction.response.edit_message(embed=embed, view=BusinessSkillsView(self.author_id))
        else:
            await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом", ephemeral=True)


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль {COG_NAME} успешно загружен!")

    @commands.slash_command(name="бизнес")
    @discord.commands.guild_only()
    async def business(self, ctx):
        if str(ctx.author.id) in economy_data:
            user_data = economy_data[str(ctx.author.id)]["business"]
            embed = make_business_ui(user_data)
            # t = (datetime.datetime.now() - datetime.datetime.fromtimestamp(user_data["last_collection"])) >= datetime.timedelta(seconds=10)
            view = BusinessView(ctx.author.id)
            await ctx.respond(view=view, embed=embed)
        else:
            view = BusinessView(ctx.author.id, (True, None, None))
            await ctx.respond(embed=discord.Embed(title="Пустова-то тут.",
                                                  description=f"У вас нет бизнеса. Используйте </бизнес-создать:1178417237443481712>"),
                              view=view)

    @commands.slash_command(name="бизнес-создать")
    @discord.commands.guild_only()
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
        economy_data[author_id]["business"]["name"] = name
        economy_data[author_id]["business"]["desc"] = description
        economy_data[author_id]["business"]["xp"] = 0
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
