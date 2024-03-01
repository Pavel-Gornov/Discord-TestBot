import socket
import select
from discord.ext import commands, tasks


class PingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((socket.gethostname(), 3000))
        self.s.listen()
        self.listen_ping.start()

    @tasks.loop(seconds=1)
    async def listen_ping(self):
        ready, _, _ = select.select([self.s], [], [], 0)
        if not ready:
            return
        try:
            self.s.settimeout(0.02)
            conn, _ = self.s.accept()
        except:
            return
        try:
            conn.settimeout(0.02)
            conn.recv(1024)
        except:
            pass
        conn.send(b"pong")
        conn.close()

    def cog_unload(self):
        self.listen_ping.cancel()
        self.s.close()


def setup(bot):
    bot.add_cog(PingCog(bot))
