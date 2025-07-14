import discord
from discord.ext import commands
import sqlite3
import random
import time

# Khởi tạo database nếu chưa có
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 1000,
    last_daily REAL DEFAULT 0
)''')
conn.commit()

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()

        # Các định dạng chấp nhận: hdaily, Hdaily, h daily, H daily
        if not (content.startswith("hdaily") or content.startswith("h daily")):
            return

        user_id = str(message.author.id)
        username = message.author.name
        now = time.time()
        cooldown_seconds = 24 * 60 * 60  # 24 giờ

        # Lấy hoặc tạo user
        c.execute("SELECT balance, last_daily FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            balance, last_daily = row
        else:
            balance = 1000
            last_daily = 0
            c.execute("INSERT INTO users (user_id, username, balance, last_daily) VALUES (?, ?, ?, ?)", (user_id, username, balance, last_daily))
            conn.commit()

        # Kiểm tra cooldown
        if now - last_daily < cooldown_seconds:
            remaining = int(cooldown_seconds - (now - last_daily))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await message.channel.send(f"⏳ Bạn cần chờ **{hours} giờ {minutes} phút** để nhận quà daily tiếp theo.")
            return

        # Cập nhật thưởng
        reward = random.randint(50, 150)
        balance += reward
        last_daily = now
        c.execute("UPDATE users SET balance = ?, last_daily = ? WHERE user_id = ?", (balance, last_daily, user_id))
        conn.commit()

        # Gửi embed kết quả
        embed = discord.Embed(
            title=f"{username} đã nhận daily 💰",
            description=f"> Bạn nhận được: **{reward}** coin!",
            color=0x00FF00
        )
        embed.add_field(name="💳 Số dư hiện tại", value=f"{balance}", inline=True)
        embed.set_footer(text="Hãy quay lại sau 24 giờ để nhận tiếp!")
        embed.timestamp = message.created_at

        await message.channel.send(embed=embed)

# Bắt buộc cho extension
async def setup(bot):
    await bot.add_cog(Daily(bot))
