import discord
from discord.ext import commands
import os

# Đặt intents để bot có thể đọc nội dung tin nhắn
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")

async def main():
    # Tải các extension cần thiết
    await bot.load_extension("addmoney")
    await bot.load_extension("bank")
    await bot.load_extension("bj")
    await bot.load_extension("cash")
    await bot.load_extension("claim")
    await bot.load_extension("coinflip")
    await bot.load_extension("give")
    await bot.load_extension("daily")
    await bot.load_extension("hhelp")
    await bot.load_extension("hlevel")
    await bot.load_extension("hpage")
    await bot.load_extension("inventory")
    await bot.load_extension("profile")
    await bot.load_extension("shop")
    await bot.load_extension("top")
    await bot.load_extension("vatpham")
    await bot.load_extension("xoso")

# Thay vì sử dụng asyncio.run(), hãy gọi bot.run() trực tiếp
if __name__ == "__main__":
    # Lấy token từ biến môi trường (thêm token vào môi trường Render)
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    if TOKEN is None:
        print("Error: No token found.")
    else:
        bot.run(TOKEN)
