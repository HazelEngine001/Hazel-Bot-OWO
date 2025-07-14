import discord
from discord.ext import commands

class ItemDescribe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Danh sách mô tả chi tiết từng vật phẩm
        self.items = {
            "lootbox": {
                "name": "🎁 Lootbox",
                "description": "Hộp quà chứa phần thưởng ngẫu nhiên như tiền, gem hoặc vật phẩm quý.",
                "price": 500,
                "rarity": "Phổ biến",
                "usage": "Không thể bán lại, chỉ mở."
            },
            "gem": {
                "name": "💎 Gem",
                "description": "Một viên ngọc dùng để nâng cấp vật phẩm hoặc đổi lấy quà hiếm.",
                "price": 1000,
                "rarity": "Hiếm",
                "usage": "Dùng khi nâng cấp vật phẩm hoặc đổi gem."
            },
            "lucky": {
                "name": "🍀 Lucky Charm",
                "description": "Vật phẩm may mắn giúp tăng tỉ lệ thắng khi chơi coinflip.",
                "price": 800,
                "rarity": "Trung bình",
                "usage": "Tự động kích hoạt khi coinflip."
            },
            "energy": {
                "name": "🔋 Energy Drink",
                "description": "Giảm thời gian chờ các lệnh như `daily`, `work`.",
                "price": 300,
                "rarity": "Phổ biến",
                "usage": "Tự động dùng nếu cooldown còn dài."
            }
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()
        if not (content.startswith("hvatpham") or content.startswith("h vatpham")):
            return

        args = content.split()
        if len(args) < 2:
            await message.channel.send("❌ Dùng đúng cú pháp: `hvatpham <tên vật phẩm>`")
            return

        item_key = args[1].lower()
        item = self.items.get(item_key)

        if not item:
            await message.channel.send("❌ Vật phẩm không tồn tại.")
            return

        embed = discord.Embed(
            title=f"{item['name']} - Thông tin chi tiết",
            description=item['description'],
            color=0x9b59b6
        )
        embed.add_field(name="💰 Giá", value=f"{item['price']} coin", inline=True)
        embed.add_field(name="🎯 Độ hiếm", value=item['rarity'], inline=True)
        embed.add_field(name="📦 Cách dùng", value=item['usage'], inline=False)
        embed.set_footer(text="Mô tả vật phẩm từ hệ thống")
        embed.timestamp = message.created_at

        await message.channel.send(embed=embed)

# Setup
async def setup(bot):
    await bot.add_cog(ItemDescribe(bot))
