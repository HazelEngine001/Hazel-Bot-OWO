import discord
from discord.ext import commands, tasks
import random
import asyncio
import datetime

# Giả lập ví cowoncy
user_bets = {}  # {user_id: amount}
max_bet = 250_000
jackpot_bonus = 500
lottery_end_time = None

class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_lottery_end.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if content.startswith("hxoso") or content.startswith("h xoso"):
            args = content.split()
            if len(args) == 1:
                await self.display_status(message.channel, message.author)
                return

            user_id = message.author.id
            if args[1] == "all":
                amount = 1000  # Giả lập: mỗi người có 1000
            else:
                try:
                    amount = int(args[1])
                except ValueError:
                    await message.channel.send("❌ Số tiền không hợp lệ!")
                    return

            if amount <= 0:
                await message.channel.send("❌ Số tiền phải lớn hơn 0!")
                return

            prev = user_bets.get(user_id, 0)
            if prev >= max_bet:
                await message.channel.send("🚫 Bạn đã cược tối đa 250.000 cowoncy hôm nay!")
                return

            if amount + prev > max_bet:
                amount = max_bet - prev

            user_bets[user_id] = prev + amount

            global lottery_end_time
            if lottery_end_time is None:
                lottery_end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

            await message.channel.send(embed=self.create_embed(message.author, amount))

    async def display_status(self, channel, user):
        total = sum(user_bets.values())
        user_bet = user_bets.get(user.id, 0)
        chance = (user_bet / total * 100) if total > 0 else 100
        chance = round(chance, 2)

        embed = discord.Embed(title=f"🎰 Xổ Số - {user.display_name}")
        embed.add_field(name="Bạn đã cược", value=f"```{user_bet} cowoncy```", inline=True)
        embed.add_field(name="Tỉ lệ thắng", value=f"```{chance}%```", inline=True)
        embed.add_field(name="Số người tham gia", value=f"```{len(user_bets)} người```", inline=True)
        embed.add_field(name="Tổng jackpot", value=f"```{total + jackpot_bonus} cowoncy```", inline=True)
        embed.add_field(name="Thời gian còn lại", value=f"```{self.time_left()}```", inline=True)
        await channel.send(embed=embed)

    def create_embed(self, user, amount):
        total = sum(user_bets.values())
        user_total = user_bets[user.id]
        chance = round(user_total / total * 100, 2) if total > 0 else 100

        embed = discord.Embed(
            title=f"🎟️ {user.display_name} tham gia Xổ Số",
            description="Bạn đã cược và tăng cơ hội trúng jackpot!",
            color=0x00ff88
        )
        embed.add_field(name="Bạn vừa cược", value=f"```{amount} cowoncy```", inline=True)
        embed.add_field(name="Tổng bạn đã cược", value=f"```{user_total} cowoncy```", inline=True)
        embed.add_field(name="Tỉ lệ thắng hiện tại", value=f"```{chance}%```", inline=True)
        embed.add_field(name="Tổng jackpot", value=f"```{total + jackpot_bonus} cowoncy```", inline=True)
        embed.add_field(name="Thời gian còn lại", value=f"```{self.time_left()}```", inline=True)
        return embed

    def time_left(self):
        global lottery_end_time
        if lottery_end_time is None:
            return "Chưa bắt đầu"
        now = datetime.datetime.utcnow()
        remaining = lottery_end_time - now
        if remaining.total_seconds() <= 0:
            return "0h 0m 0s"
        return str(remaining).split('.')[0]  # HH:MM:SS

    @tasks.loop(seconds=10)
    async def check_lottery_end(self):
        global lottery_end_time
        if lottery_end_time and datetime.datetime.utcnow() >= lottery_end_time:
            if not user_bets:
                lottery_end_time = None
                return

            winner_id = random.choices(list(user_bets.keys()), weights=list(user_bets.values()), k=1)[0]
            winner = self.bot.get_user(winner_id)
            total = sum(user_bets.values()) + jackpot_bonus

            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        try:
                            await channel.send(f"🎉 Chúc mừng {winner.mention} đã thắng xổ số và nhận được **{total} cowoncy**! 🤑")
                            break
                        except:
                            continue

            user_bets.clear()
            lottery_end_time = None

async def setup(bot):
    await bot.add_cog(Lottery(bot))