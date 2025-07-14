import discord
from discord.ext import commands
import sqlite3
import random
import asyncio
import time  # <== Thêm thư viện time để quản lý cooldown

# Lưu cooldown của từng user
user_cooldowns = {}  # user_id: timestamp

GIF_LINKS = {
    "flipping": "https://media.tenor.com/UTgK0rCiKLMAAAAi/ultimate-coin-flip-lucky-louie-flip.gif",
    "head": "https://i.imgur.com/hOidl0u.png",
    "tails": "https://i.imgur.com/Z2lHqjq.png"
}

# SQLite setup
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 1000
)''')
conn.commit()

class Coinflip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()

        # Nhận lệnh bắt đầu bằng h, có cf
        if not content.startswith("h"):
            return

        content = content[1:].strip()

        if content.startswith("cf"):
            content = content[2:].strip()
        elif content.startswith(" cf"):
            content = content[3:].strip()
        else:
            return

        bet_arg = content.replace(" ", "")
        if not bet_arg:
            await message.channel.send("❌ Bạn chưa nhập số tiền cược.")
            return

        user_id = str(message.author.id)
        username = message.author.name

        # ===== KIỂM TRA COOLDOWN =====
        now = time.time()
        last_play = user_cooldowns.get(user_id, 0)
        cooldown_seconds = 15

        if now - last_play < cooldown_seconds:
            wait_time = int(cooldown_seconds - (now - last_play))
            await message.channel.send(f"🕒 Vui lòng chờ **{wait_time} giây** trước khi chơi lại.")
            return

        # Truy vấn DB
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            balance = row[0]
        else:
            balance = 1000
            c.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)", (user_id, username, balance))
            conn.commit()

        # Xử lý số tiền
        if bet_arg == "all":
            bet = balance
        else:
            try:
                bet = int(bet_arg)
            except ValueError:
                await message.channel.send("❌ Số tiền cược không hợp lệ.")
                return

        if bet <= 0:
            await message.channel.send("❌ Số tiền phải lớn hơn 0.")
            return

        if bet > balance:
            await message.channel.send("💸 Bạn không đủ tiền để cược.")
            return

        # ===== CẬP NHẬT THỜI GIAN CHƠI =====
        user_cooldowns[user_id] = time.time()

        # Random mặt coin
        choice = random.choice(["head", "tails"])
        result = random.choice(["head", "tails"])
        win = result == choice
        reward = bet * 2 if win else 0
        balance += reward if win else -bet

        # Embed flipping
        flipping_embed = discord.Embed(description=f"🪙 Coin is flipping... (Bạn chọn ngẫu nhiên: **{choice}**)", color=0xFFFF00)
        flipping_embed.set_thumbnail(url=GIF_LINKS["flipping"])
        flipping_msg = await message.channel.send(embed=flipping_embed)
        await asyncio.sleep(3)

        # Cập nhật DB
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id))
        conn.commit()

        # Kết quả
        result_embed = discord.Embed(
            title=f"You {'Won' if win else 'Lost'}!",
            description=f"> Kết quả: `{result}`\n> Bạn chọn: `{choice}`\n\nBạn {'nhận' if win else 'mất'} 💰 {reward if win else -bet}",
            color=0x00FF00 if win else 0xFF0000
        )
        result_embed.set_thumbnail(url=GIF_LINKS[result])
        result_embed.add_field(name="💳 Số dư còn lại", value=f"{balance}", inline=True)
        result_embed.timestamp = message.created_at
        await flipping_msg.edit(embed=result_embed)

# Setup Cog
async def setup(bot):
    await bot.add_cog(Coinflip(bot))
