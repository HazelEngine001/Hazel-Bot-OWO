import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect("users.db")
c = conn.cursor()

# Tên item mapping (giống shop.py)
ITEM_NAMES = {
    "lootbox": "🎁 Lootbox",
    "gem": "💎 Gem",
    "lucky": "🍀 Lucky Charm",
    "energy": "🔋 Energy Drink"
}

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if not (content.startswith("hinv") or content.startswith("h inv")):
            return

        user_id = str(message.author.id)
        username = message.author.name

        # Lấy dữ liệu inventory
        c.execute("SELECT item_key, quantity FROM inventory WHERE user_id = ?", (user_id,))
        rows = c.fetchall()

        if not rows:
            await message.channel.send("🎒 Túi đồ của bạn đang trống.")
            return

        embed = discord.Embed(
            title=f"🎒 Túi đồ của {username}",
            color=0x7289DA
        )

        for item_key, quantity in rows:
            name = ITEM_NAMES.get(item_key, item_key)
            embed.add_field(name=name, value=f"Số lượng: `{quantity}`", inline=True)

        embed.set_footer(text="Dùng `hmở <item>` để sử dụng vật phẩm (nếu hỗ trợ).")
        embed.timestamp = message.created_at

        await message.channel.send(embed=embed)

# Setup
async def setup(bot):
    await bot.add_cog(Inventory(bot))
