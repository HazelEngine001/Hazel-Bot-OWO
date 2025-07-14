import discord
from discord.ext import commands
import sqlite3

# Khởi tạo DB nếu chưa có
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 1000,
    bank_balance INTEGER DEFAULT 0,
    last_daily REAL DEFAULT 0
)''')
conn.commit()

class Bank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()

        # Nhận các dạng: hbank, Hbank, h bank, H bank
        if not (content.startswith("hbank") or content.startswith("h bank")):
            return

        user_id = str(message.author.id)
        username = message.author.name

        # Lấy hoặc tạo user
        c.execute("SELECT balance, bank_balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            balance, bank_balance = row
        else:
            balance = 1000
            bank_balance = 0
            c.execute("INSERT INTO users (user_id, username, balance, bank_balance) VALUES (?, ?, ?, ?)",
                      (user_id, username, balance, bank_balance))
            conn.commit()

        # Gửi embed hiển thị số dư
        embed = discord.Embed(title="🏦 Bank Balance", color=0x00FF00)
        embed.add_field(name="💰 Ví", value=f"{balance}", inline=True)
        embed.add_field(name="🏦 Ngân hàng", value=f"{bank_balance}", inline=True)
        embed.set_footer(text="Dùng lệnh gửi/rút để chuyển tiền giữa ví và ngân hàng.")
        embed.timestamp = message.created_at

        await message.channel.send(embed=embed)

# Setup cog
async def setup(bot):
    await bot.add_cog(Bank(bot))
