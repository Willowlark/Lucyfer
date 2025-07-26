import discord
import os # default module
from config import BOT_TOKEN

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = discord.Bot(intents=intents)

cogs_list = [
    'dice_cog',
    'madlibs_cog',
    'role_cog',
    'trainer_cog'
]
for cog in cogs_list:
    bot.load_extension(f'cogs.{cog}')

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="pokerolefaq", description="Share the Pokerole FAQ")
async def pokerolefaq(ctx: discord.ApplicationContext):
    await ctx.respond('Check the FAQ here: https://wiki.aurii.us/doku.php?id=pokerole-server:server_faq')

bot.run(BOT_TOKEN) # run the bot with the token
