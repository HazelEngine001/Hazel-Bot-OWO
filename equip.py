import discord
from discord.ext import commands
import sqlite3
import random

conn = sqlite3.connect("users.db")
c = conn.cursor()

class Equip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if not (content.startswith("htrangbi") or content.startswith("h trangbi")):
            return

        args = content.split()
        if len(args) < 2:
            await message.channel.send("❌ Dùng đúng cú pháp: `htrangbi <tên item>`")
            return

        item_key = args[1].lower()
        user_id = str(message.author.id)
        username = message.author.name

        # Kiểm tra item tồn tại trong inventory
        c.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_key = ?", (user_id, item_key))
        row = c.fetchone()

        if not row or row[0] <= 0:
            await message.channel.send("❌ Bạn không có vật phẩm này để sử dụng.")
            return

        # Trừ item 1 đơn vị
        c.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_key = ?", (user_id, item_key))

        # Logic sử dụng vật phẩm
        if item_key == "gem":
            result_text = "💎 Bạn đã dùng 1 **Gem** để nâng cấp vật phẩm!"
        elif item_key == "lootbox":
            reward = random.randint(200, 800)
            c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            balance = c.fetchone()[0] + reward
            c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id))
            result_text = f"🎁 Bạn mở Lootbox và nhận được **{reward} coin**!"
        elif item_key == "lucky":
            result_text = "🍀 Lucky Charm đã được kích hoạt! Bạn sẽ may mắn hơn khi chơi coinflip."
        elif item_key == "energy":
            result_text = "🔋 Bạn đã uống Energy Drink! Cooldown daily sẽ giảm."
        else:
            result_text = f"📦 Bạn đã sử dụng vật phẩm `{item_key}`!"

        conn.commit()

        embed = discord.Embed(
            title="🎒 Vật phẩm đã được sử dụng",
            description=result_text,
            color=0x00ff99
        )
        embed.set_footer(text=f"Người dùng: {username}")
        embed.timestamp = message.created_at
        await message.channel.send(embed=embed)

# Setup
async def setup(bot):
    await bot.add_cog(Equip(bot))
