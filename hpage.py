import discord
from discord.ext import commands
import sqlite3
import math

CATEGORIES = {
    "weapon": [
        {"id": 101, "name": "Bronze Sword", "emoji": "⚔️", "price": 300, "owned": False},
        {"id": 102, "name": "Silver Spear", "emoji": "🔱", "price": 500, "owned": True},
        {"id": 103, "name": "Iron Axe", "emoji": "🪓", "price": 450, "owned": False},
        {"id": 104, "name": "Magic Wand", "emoji": "✨", "price": 650, "owned": False},
    ],
    "ring": [
        {"id": 201, "name": "Diamond Ring", "emoji": "💍", "price": 1000, "owned": False},
        {"id": 202, "name": "Gold Ring", "emoji": "💛", "price": 800, "owned": False},
    ],
    "wallpaper": [
        {"id": 301, "name": "Mountain View", "emoji": "🖼️", "price": 250, "owned": False},
        {"id": 302, "name": "Ocean Theme", "emoji": "🖼️", "price": 300, "owned": True},
        {"id": 303, "name": "Sunset Glow", "emoji": "🌇", "price": 350, "owned": False},
        {"id": 304, "name": "Forest Dream", "emoji": "🌲", "price": 400, "owned": False},
    ]
}

conn = sqlite3.connect("users.db")
c = conn.cursor()

class HPage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if not (content.startswith("hpage") or content.startswith("h page")):
            return

        args = content.split()
        if len(args) < 2:
            await message.channel.send("❌ Dùng đúng cú pháp: `hpage weapon|ring|wallpaper [trang]`")
            return

        category = args[1]
        page = int(args[2]) if len(args) >= 3 and args[2].isdigit() else 1

        items = CATEGORIES.get(category)
        if not items:
            await message.channel.send("❌ Không tìm thấy danh mục này!")
            return

        items_per_page = 2
        total_pages = math.ceil(len(items) / items_per_page)

        if page < 1 or page > total_pages:
            await message.channel.send(f"❌ Trang phải từ 1 đến {total_pages}.")
            return

        start = (page - 1) * items_per_page
        end = start + items_per_page
        items_page = items[start:end]

        embed = discord.Embed(
            title=f"📦 Danh mục: {category.capitalize()}",
            description="Dùng `hmua <id>` để mua vật phẩm.",
            color=0x3498db
        )

        for item in items_page:
            name = f"{item['emoji']} {item['name']}"
            if item.get("owned"):
                name = f"~~{name}~~ ✅"
            embed.add_field(
                name=f"ID: `{item['id']}`",
                value=f"{name}\n💰 {item['price']} coin",
                inline=False
            )

        embed.set_footer(text=f"Trang {page} / {total_pages}")
        embed.timestamp = message.created_at
        await message.channel.send(embed=embed)

# Setup
async def setup(bot):
    await bot.add_cog(HPage(bot))
