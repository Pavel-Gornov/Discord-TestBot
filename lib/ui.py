from discord.ui import *
from discord import Interaction, SelectOption, Embed
from lib.utils import TBS, CONFIG, Color, get_guild_lang, DB


class SettingsView(View):
    class SettingsSelect(Select):
        def __init__(self, language: str):
            # TODO: Продумать больше настроек и внести строки TBS
            placeholder = "Выберите то, что хотите изменить."
            options = [
                SelectOption(label="Язык", description="Сменить язык Бота на этом сервере.", emoji="🌐", value="1",
                             default=False),
                SelectOption(label="Строка 2", description="Описание 2", emoji="🫥", value="Значение 2", default=False),
                SelectOption(label="Строка 3", description="Описание 3", emoji="🫥", value="Значение 3", default=True),
            ]
            super().__init__(min_values=1, max_values=1, options=options, placeholder=placeholder)

        async def callback(self, interaction: Interaction):
            language = get_guild_lang(interaction.guild)
            if self.view.author_id == interaction.user.id:
                if self.values[0] == "1":
                    embed = Embed(title="Выбор языка", colour=Color.BOT)
                    view = LanguageChangingView(interaction.user.id, language)
                    await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом.",
                                                        ephemeral=True)

    def __init__(self, author_id: int, language: str):
        self.author_id = author_id
        super().__init__(timeout=300, disable_on_timeout=True)
        self.add_item(self.SettingsSelect(language))


class LanguageChangingView(View):
    class LanguageChangingSelector(Select):
        def __init__(self, language: str):
            placeholder = "Какой язык выберите?"
            options = []
            # TODO: Расписать языки по отдельным файлам и добавить недостающие строки.
            for lang in CONFIG.LANGUAGES:
                options.append(SelectOption(label=lang, value=lang, emoji="🌐", default=(lang == language)))
            super().__init__(min_values=1, max_values=1, options=options, placeholder=placeholder)

        async def callback(self, interaction: Interaction):
            if self.view.author_id == interaction.user.id:
                # TODO: Позаботиться о безопасности.
                DB.change_server_settings(interaction.guild.id, lang=self.values[0])
                await interaction.response.send_message(f"Похоже, что Вы выбрали: {self.values[0]}")
            else:
                await interaction.response.send_message("Вы не можете взаимодействовать с этим интерфейсом.",
                                                        ephemeral=True)

    def __init__(self, author_id: int, language: str):
        self.author_id = author_id
        super().__init__(timeout=300, disable_on_timeout=True)
        self.add_item(self.LanguageChangingSelector(language))
