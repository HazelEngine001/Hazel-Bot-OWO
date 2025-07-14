import discord
from discord.ext import commands
import sqlite3
import datetime

# Kết nối với SQLite
conn = sqlite3.connect('users.db')
c = conn.cursor()

def format_money(amount):
    return "{:,}".format(amount)

class Cash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.strip().lower()
        if not (content.startswith("hcash") or content.startswith("h cash")):
            return

        user_id = str(message.author.id)
        username = message.author.name

        # Lấy hoặc tạo user
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()

        if row:
            balance = row[0]
        else:
            balance = 1000
            c.execute("INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)",
                      (user_id, username, balance))
            conn.commit()

        # Lấy giờ hiện tại theo giờ Việt Nam (UTC+7)
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
        current_time = now.strftime('%H:%M:%S')

        # Tạo embed đẹp với các hiệu ứng
        embed = discord.Embed(
            description=f"💳 **| {message.author.mention}**, bạn hiện đang có\n**<:cowoncy:416043450337853441> ```{format_money(balance)} cowoncy```**",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name="Số dư tài khoản", icon_url=message.author.display_avatar.url)
        embed.set_footer(text="💼 Kiểm tra tiền xài chơi thôi 😎", icon_url="https://youriconlink.com/icon.png")
        embed.set_thumbnail(url="https://youriconlink.com/thumbnail.png")
        embed.add_field(name="💬 Thời gian kiểm tra:", value=f"```{current_time}```", inline=False)
        
        # Thêm dấu "!" vào sau thông báo
        embed.add_field(name="🎯 Dùng cowoncy cho các hoạt động", value="Chơi game, vote, tặng quà... !", inline=False)
        embed.add_field(name="💡 Cách kiếm cowoncy", value="Làm quest, vote cho bot, tham gia các sự kiện!", inline=False)

        # Để đẹp hơn nữa, có thể thêm nền hoặc hình ảnh.
        embed.set_image(url="https://yourbackgroundimage.com/image.png") 

        await message.channel.send(embed=embed)

# Setup Cog
async def setup(bot):
    await bot.add_cog(Cash(bot))
