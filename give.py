import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

class Give(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.content.lower().startswith(("hgive", "h give")):
            return

        parts = message.content.strip().split()
        if len(parts) < 3:
            await message.channel.send("❌ Cú pháp: `hgive @user <số tiền>`")
            return

        try:
            recipient = message.mentions[0]
        except IndexError:
            await message.channel.send("❌ Bạn phải **tag** người nhận tiền.")
            return

        try:
            amount = int(parts[-1])
        except ValueError:
            await message.channel.send("❌ Số tiền không hợp lệ.")
            return

        if amount <= 0:
            await message.channel.send("❌ Số tiền phải lớn hơn 0.")
            return

        sender_id = str(message.author.id)
        recipient_id = str(recipient.id)

        if sender_id == recipient_id:
            await message.channel.send("❌ Không thể gửi tiền cho chính bạn.")
            return

        # Lấy hoặc tạo người gửi
        c.execute("SELECT balance FROM users WHERE user_id = ?", (sender_id,))
        sender_data = c.fetchone()
        if not sender_data:
            await message.channel.send("❌ Bạn chưa có tài khoản.")
            return

        sender_balance = sender_data[0]
        if sender_balance < amount:
            await message.channel.send("💸 Bạn không đủ tiền để gửi.")
            return

        # Lấy hoặc tạo người nhận
        c.execute("SELECT balance FROM users WHERE user_id = ?", (recipient_id,))
        recipient_data = c.fetchone()
        if recipient_data:
            recipient_balance = recipient_data[0]
        else:
            recipient_balance = 1000
            c.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                      (recipient_id, recipient.name, recipient_balance))

        # Giao dịch
        sender_balance -= amount
        recipient_balance += amount

        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (sender_balance, sender_id))
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (recipient_balance, recipient_id))
        conn.commit()

        await message.channel.send(
            f"✅ {message.author.mention} đã gửi **{amount}** 💰 cho {recipient.mention}.\n"
            f"📤 Số dư còn lại: **{sender_balance}**"
        )

# Setup Cog
async def setup(bot):
    await bot.add_cog(Give(bot))
