import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect("users.db")
c = conn.cursor()

# Tạo bảng nếu chưa có
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 1000,
    claimed_reward INTEGER DEFAULT 0
)
''')
conn.commit()

class Claim(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()
        if not (content.startswith("hclaim") or content.startswith("h claim")):
            return

        user_id = str(message.author.id)
        username = message.author.name

        # Lấy hoặc tạo user
        c.execute("SELECT balance, claimed_reward FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()

        if row:
            balance, claimed = row
        else:
            balance = 1000
            claimed = 0
            c.execute("INSERT INTO users (user_id, username, balance, claimed_reward) VALUES (?, ?, ?, ?)", (user_id, username, balance, claimed))
            conn.commit()

        if claimed:
            await message.channel.send("❌ Bạn đã nhận phần thưởng trước đó rồi!")
            return

        # Cộng thưởng
        balance += 500
        c.execute("UPDATE users SET balance = ?, claimed_reward = 1 WHERE user_id = ?", (balance, user_id))
        conn.commit()

        # Gửi thông báo
        embed = discord.Embed(
            title="🎁 Bạn đã nhận phần thưởng!",
            description="> 💰 +500 Coins\n> 🎁 +1 Lootbox (ảo 😄)",
            color=0x00FF00
        )
        embed.add_field(name="Tổng số dư mới", value=f"💳 {balance}", inline=False)
        embed.set_footer(text="Bạn chỉ có thể nhận phần thưởng này một lần!")
        embed.timestamp = message.created_at

        await message.channel.send(embed=embed)

# Setup cog
async def setup(bot):
    await bot.add_cog(Claim(bot))
