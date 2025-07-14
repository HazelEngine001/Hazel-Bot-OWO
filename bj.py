import discord
from discord.ext import commands
import random

# Định nghĩa bộ bài (sử dụng điểm, không cần suit)
deck_values = {
    "A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10
}
deck_cards = list(deck_values.keys())

active_games = {}  # Lưu ván chơi theo user_id

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def draw_card(self):
        return random.choice(deck_cards)

    def calculate_points(self, hand):
        points = sum(deck_values[card] for card in hand)
        # Hạ A từ 11 xuống 1 nếu cần
        aces = hand.count("A")
        while points > 21 and aces:
            points -= 10
            aces -= 1
        return points

    async def end_game(self, user_id):
        if user_id in active_games:
            del active_games[user_id]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content.lower().strip()
        if not (content.startswith("hbj") or content.startswith("h bj")):
            return

        user_id = message.author.id
        if user_id in active_games:
            await message.channel.send("🚫 Bạn đang chơi 1 ván rồi! Kết thúc trước khi chơi tiếp.")
            return

        # Khởi tạo ván chơi
        player_hand = [self.draw_card(), self.draw_card()]
        dealer_hand = [self.draw_card(), self.draw_card()]

        active_games[user_id] = {
            "player": player_hand,
            "dealer": dealer_hand,
            "message": None
        }

        await self.show_game(message.channel, message.author)

    async def show_game(self, channel, user):
        game = active_games[user.id]
        player = game["player"]
        dealer = game["dealer"]

        player_points = self.calculate_points(player)
        dealer_display = dealer[0] + ", ❓"

        embed = discord.Embed(
            title=f"🃏 Blackjack - {user.display_name}",
            description=(
                f"**Bài của bạn:** {', '.join(player)} (Tổng: {player_points})\n"
                f"**Bài của Dealer:** {dealer_display}\n\n"
                "👊 để **rút bài** | 🛑 để **dừng**"
            ),
            color=0x00ff99
        )

        sent_msg = await channel.send(embed=embed)
        game["message"] = sent_msg

        await sent_msg.add_reaction("👊")
        await sent_msg.add_reaction("🛑")

        def check(reaction, user_check):
            return (
                user_check.id == user.id and
                str(reaction.emoji) in ["👊", "🛑"] and
                reaction.message.id == sent_msg.id
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "👊":
                await self.hit(user, channel)
            else:
                await self.stand(user, channel)
        except:
            await channel.send("⏱️ Hết giờ. Ván chơi kết thúc.")
            await self.end_game(user.id)

    async def hit(self, user, channel):
        game = active_games[user.id]
        game["player"].append(self.draw_card())

        if self.calculate_points(game["player"]) > 21:
            await channel.send(f"💥 **{user.mention} BÙM! Quá 21 điểm! Bạn thua rồi.**")
            await self.end_game(user.id)
        else:
            await self.show_game(channel, user)

    async def stand(self, user, channel):
        game = active_games[user.id]
        player_score = self.calculate_points(game["player"])
        dealer_hand = game["dealer"]

        while self.calculate_points(dealer_hand) < 17:
            dealer_hand.append(self.draw_card())

        dealer_score = self.calculate_points(dealer_hand)

        result = f"🧑‍💼 **Dealer:** {', '.join(dealer_hand)} ({dealer_score})\n" \
                 f"🧑 **Bạn:** {', '.join(game['player'])} ({player_score})\n"

        if dealer_score > 21 or player_score > dealer_score:
            result += f"🎉 **{user.mention} bạn thắng!**"
        elif dealer_score == player_score:
            result += f"🤝 **{user.mention} hòa với Dealer.**"
        else:
            result += f"💸 **{user.mention} bạn thua rồi.**"

        await channel.send(result)
        await self.end_game(user.id)

# Setup
async def setup(bot):
    await bot.add_cog(Blackjack(bot))
