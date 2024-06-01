import base64
import io
import json
import aiohttp
import discord
from discord.ext import commands, tasks
from Token import public_key, secret_key
from lib.utils import Color

COG_NAME = "API Кандинского"

MODEL_ID = 4
STYLES = {
    "Кандинский": "KANDINSKY", "Kandinsky": "KANDINSKY",
    "Детальное фото": "UHD", "Detailed photo": "UHD", "Uhd": "UHD",
    "Аниме": "ANIME", "Anime": "ANIME",
    "Свой стиль": "DEFAULT", "No style": "DEFAULT", "Default": "DEFAULT"
}


class Query(commands.Converter):
    def __init__(self, text, width, height, style):
        self._text = text
        self._width = width
        self._height = height
        self._style = style

    @classmethod
    async def convert(cls, ctx=None, argument=None):
        width = 1024
        height = 1024
        style = "DEFAULT"
        text = ""
        for i in argument.split():
            if "x" in i:
                temp = i.split("x")
                if temp[0].isdigit() and temp[1].isdigit():
                    width = int(temp[0])
                    height = int(temp[1])
                else:
                    text += i + " "
            elif "стиль:" in i.lower():
                temp = STYLES.get(i.split(":")[1].capitalize())
                if temp:
                    style = temp
            else:
                text += i + " "

        return cls(text[:-1], width, height, style)

    def get_json(self) -> dict:
        return {"type": "GENERATE", "style": self._style, "width": self._width, "height": self._height, "num_images": 1,
                "negativePromptUnclip": "яркие цвета, кислотность, высокая контрастность",
                "generateParams": {
                    "query": self._text}}

    @property
    def text(self):
        return self._text

    @property
    def size(self):
        return f"{self._width}x{self._height}"

    def __str__(self):
        return f"Запрос: {self._text}, Размеры: {self._width}x{self._height}, Стиль: {self._style}"


class KandinskyAPI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.request_queue = {}
        self.header = {'X-Key': f'Key {public_key}', 'X-Secret': f'Secret {secret_key}'}
        self.check_requests.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Модуль {COG_NAME} успешно загружен!")

    @commands.command(aliases=["картинка", "магия", "нейросеть"], description="command_image_description",
                      help="command_image_examples", brief="command_image_args")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def image(self, ctx: commands.Context, *, query: Query = None):
        if query:
            files = aiohttp.FormData()
            files.add_field(name='params', value=json.dumps(query.get_json()), content_type='application/json')
            files.add_field(name='model_id', value=str(MODEL_ID))

            embed = discord.Embed(title="Начинаю обработку...",
                                  description=f"**Запрос:** {query.text}\n**Размеры изображения:** {query.size}",
                                  color=Color.BOT)
            embed.add_field(name="Запрос на обработку от:", value=ctx.author.mention)
            m = await ctx.reply(embed=embed)
            async with aiohttp.ClientSession("https://api-key.fusionbrain.ai") as session:
                async with session.post(url="/key/api/v1/text2image/run", data=files,
                                        headers=self.header) as response:
                    response_json = await response.json()
            if response.ok:
                self.request_queue[response_json['uuid']] = (m, ctx.author)
            else:
                await m.edit(
                    embed=discord.Embed(title="Произошла ошибка", description="Не удалось запустить обработку.",
                                        color=Color.ERROR))
        else:
            await ctx.reply(embed=discord.Embed(title="Ошибка аргумента",
                                                description="Аргументы для запроса указаны не верно или отсутствуют.",
                                                color=Color.ERROR))

    @tasks.loop(seconds=30)
    async def check_requests(self):
        if len(self.request_queue) > 0:
            iterator = self.request_queue.copy()
            async with aiohttp.ClientSession("https://api-key.fusionbrain.ai") as session:
                for k, v in iterator.items():
                    async with session.get(url=f"/key/api/v1/text2image/status/{k}", headers=self.header) as response:
                        response_json = await response.json()
                    if response.ok:
                        if response_json["status"] == "DONE":
                            self.request_queue.pop(k)
                            file_content = io.BytesIO(base64.b64decode(response_json["images"][0]))
                            await v[0].reply(f"{v[1].mention}, Генерация завершена!", file=discord.File(filename="generated.png", fp=file_content))
                        elif response_json["status"] == "FAIL":
                            self.request_queue.pop(k)
                            await v[0].edit(embed=discord.Embed(title="Ошибка создания", description="Что-то пошло не так.", color=Color.ERROR))


def setup(bot):
    bot.add_cog(KandinskyAPI(bot))
