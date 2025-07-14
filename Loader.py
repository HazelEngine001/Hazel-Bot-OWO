import discord
from discord.ext import commands, tasks
import asyncio
import os

# Đặt intents để bot có thể đọc nội dung tin nhắn
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")

# Cơ chế retry nếu bị rate limited (HTTP 429)
async def load_extensions():
    extensions = [
        "addmoney", "bank", "bj", "cash", "claim", "coinflip", 
        "give", "daily", "hhelp", "hlevel", "hpage", "inventory", 
        "profile", "shop", "top", "vatpham", "xoso"
    ]
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            print(f"Loaded extension: {extension}")
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print(f"Rate limited. Waiting to retry loading extension {extension}...")
                await asyncio.sleep(60)  # Đợi 60 giây trước khi thử lại
                await load_extensions()  # Retry loading the extensions
                break

async def main():
    # Load các extension
    await load_extensions()

    # Dán token của bạn ở đây (Lấy từ biến môi trường)
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN is None:
        print("Error: No token found.")
    else:
        await bot.start(TOKEN)

# Chạy bot đúng cách với asyncio
if __name__ == "__main__":
    asyncio.run(main())
