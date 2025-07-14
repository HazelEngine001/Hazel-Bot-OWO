import discord
from discord.ext import commands
import sqlite3

conn = sqlite3.connect('users.db')
c = conn.cursor()

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.shop_items = {
            "lootbox": {"name": "🎁 Lootbox", "price": 500, "desc": "Mở để nhận phần thưởng ngẫu nhiên!"},
            "gem": {"name": "💎 Gem", "price": 1000, "desc": "Dùng để nâng cấp vật phẩm."},
            "lucky": {"name": "🍀 Lucky Charm", "price": 800, "desc": "Tăng tỉ lệ thắng coinflip!"},
            "energy": {"name": "🔋 Energy Drink", "price": 300, "desc": "Khôi phục thời gian cooldown daily."}
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()
        user_id = str(message.author.id)
        username = message.author.name

        # ===== SHOP HIỂN THỊ =====
        if content.startswith("hshop") or content.startswith("h shop"):
            embed = discord.Embed(
                title="🛒 Cửa Hàng Vật Phẩm",
                description="Dùng `hmua <tên>` để mua nếu có hỗ trợ!",
                color=0x3498db
            )

            for key, item in self.shop_items.items():
                embed.add_field(
                    name=f"{item['name']} — 💰 {item['price']}",
                    value=item['desc'],
                    inline=False
                )

            embed.set_footer(text="Shop này chỉ mang tính hiển thị. Mua hàng cần lệnh riêng.")
            embed.timestamp = message.created_at
            await message.channel.send(embed=embed)
            return

        # ===== MUA ITEM =====
        if content.startswith("hmua") or content.startswith("h mua"):
            args = content.split()
            if len(args) < 2:
                await message.channel.send("❌ Dùng đúng cú pháp: `hmua <tên vật phẩm>`")
                return

            item_key = args[1].lower()
            if item_key not in self.shop_items:
                await message.channel.send("❌ Vật phẩm không tồn tại trong shop.")
                return

            item = self.shop_items[item_key]

            # Lấy người dùng từ DB
            c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            if row:
                balance = row[0]
            else:
                balance = 1000
                c.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)", (user_id, username, balance))
                conn.commit()

            if balance < item["price"]:
                await message.channel.send("💸 Bạn không đủ tiền để mua vật phẩm này.")
                return

            # Trừ tiền
            balance -= item["price"]
            c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id))
            conn.commit()

            await message.channel.send(f"✅ Bạn đã mua thành công **{item['name']}** với giá {item['price']} 💰!")

# Setup cog
async def setup(bot):
    await bot.add_cog(Shop(bot))
