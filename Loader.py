import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")

async def main():
    # Load extension đúng cách (phải await)
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











    # Dán token của bạn ở đây
    TOKEN = "MTM5NDAyNjgxMjc5OTA2MjA3Ng.Gp4GwB.S1D6zuOLWZ-gFQwd7bupkMir7ZpBje1J5k7zkU"
    await bot.start(TOKEN)

# Chạy bot đúng cách với asyncio
asyncio.run(main())
