# cogs/chat_relay.py
import discord
from discord.ext import commands, tasks
import emoji
import asyncio
from utils import helper_functions as hf
from state import save_state
from config import CHAT_LOG_CHANNEL_ID

class ChatRelayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_log_channel_id = CHAT_LOG_CHANNEL_ID
        self.previous_line_count = 0
        self.just_started = False
        self.send_chat_log.start()

    def cog_unload(self):
        self.send_chat_log.cancel()

    @tasks.loop(seconds=5)
    async def send_chat_log(self):
        if not self.bot.shard_manager.is_world_running():
            return

        cluster = self.bot.state["current_cluster"]
        is_beta = self.bot.state["is_beta"]
        path = hf.get_chat_log_path(cluster, is_beta)
        if not path.exists():
            return

        current_count = hf.get_log_file_length(cluster, is_beta)

        if self.just_started:
            if current_count < self.previous_line_count - 20:
                self.just_started = False
            return

        if current_count <= self.previous_line_count:
            return

        if current_count - self.previous_line_count > 80:
            return

        lines = path.read_text(errors="ignore").splitlines()
        new_lines = lines[self.previous_line_count:]

        channel = self.bot.get_channel(self.chat_log_channel_id)
        if not channel:
            return

        for line in new_lines:
            line = line[12:].strip()
            if line.startswith(("[System Message] @", "[Whisper]", "[Say]")):
                continue
            await channel.send(line)

        self.previous_line_count = current_count

    @send_chat_log.before_loop
    async def before_send_chat_log(self):
        await self.bot.wait_until_ready()
        # reset count when server starts
        if self.bot.shard_manager.is_world_running():
            cluster = self.bot.state["current_cluster"]
            is_beta = self.bot.state["is_beta"]
            self.previous_line_count = hf.get_log_file_length(cluster, is_beta)
            self.just_started = True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id != self.chat_log_channel_id:
            return

        clean_msg = emoji.demojize(message.clean_content)
        full_msg = f"@{message.author.display_name}: {clean_msg}"
        self.bot.shard_manager.send_announce(full_msg)

    # @app_commands.command(name="relink_chatlog", description="Relink chat log monitoring (useful after restart)")
    # async def relink_chatlog(self, interaction: discord.Interaction):
    #     cluster = self.bot.state["current_cluster"]
    #     is_beta = self.bot.state["is_beta"]
    #     self.previous_line_count = hf.get_log_file_length(cluster, is_beta)
    #     self.just_started = False
    #     self.send_chat_log.restart()
    #     await interaction.response.send_message("Chat log relinked successfully.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ChatRelayCog(bot))
