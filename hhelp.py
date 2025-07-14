import discord
from discord.ext import commands

class HHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if content not in ["hhelp", "h help", "Hhelp", "H help"]:
            return

        embed = discord.Embed(
            title="📖 Danh sách lệnh bot",
            description="Tất cả các lệnh hiện có",
            color=0x00ffff
        )

        # Các nhóm lệnh đã được phân nhóm
        embed.add_field(name="💰 Tiền tệ:", value="`hcash`, `hbank`, `hgive`, `hdaily`, `hclaim`", inline=False)
        embed.add_field(name="🎮 Chơi game:", value="`hcf`, `h coinflip`, `hcoin`, `hxoso`, `hslots`, `hbj`", inline=False)  # Thêm `hbj` vào đây
        embed.add_field(name="🧍 Hồ sơ:", value="`hprofile`, `hlevel`, `hlb`, `hstats`", inline=False)
        embed.add_field(name="🛍️ Mua sắm:", value="`hshop`, `hmua`, `hvatpham`, `hinv`, `htrangbi`, `hpage`", inline=False)
        embed.add_field(name="🖼️ Hình nền:", value="`hwallpaper`, `h profile set frame`, `hprofile set frame <id>`", inline=False)
        embed.add_field(name="🏆 Xếp hạng:", value="`htop`, `hlb`", inline=False)

        # Footer
        embed.set_footer(text="Prefix không cần ? | Bot by Uwu Team")

        # Gửi embed
        await message.channel.send(embed=embed)

# Setup Cog
async def setup(bot):
    await bot.add_cog(HHelp(bot))
