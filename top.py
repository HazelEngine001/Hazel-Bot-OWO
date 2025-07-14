import discord
from discord.ext import commands
import sqlite3

# Kết nối đến DB
conn = sqlite3.connect('users.db')
c = conn.cursor()

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()

        # Chấp nhận: htop, Htop, h top, H top
        if not (content.startswith("htop") or content.startswith("h top")):
            return

        try:
            # Lấy top 10 user theo balance giảm dần
            c.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT 10")
            top_users = c.fetchall()

            embed = discord.Embed(
                title="🏆 Top 10 Người Giàu Nhất",
                description="Dựa trên số tiền trong ví (💰 balance)",
                color=0xFFD700  # Màu vàng
            )

            for index, (user_id, username, balance) in enumerate(top_users, start=1):
                name_display = username or f"ID {user_id}"
                embed.add_field(
                    name=f"{index}. {name_display}",
                    value=f"💰 {balance}",
                    inline=False
                )

            embed.set_footer(text="Cạnh tranh lành mạnh nhé 😄")
            embed.timestamp = message.created_at

            await message.channel.send(embed=embed)

        except Exception as e:
            print("❌ Lỗi lấy bảng xếp hạng:", e)
            await message.channel.send("⚠️ Đã xảy ra lỗi khi lấy bảng xếp hạng.")

# Setup cog
async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
