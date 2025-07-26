import discord
from discord.ext import commands
from random import sample
import yaml

VERBOSE = False

class TrainerCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.data = yaml.safe_load(open('data/trainer_rewards.yaml'))
    
    # ---------------------------------------------------------------------------------
    
    trainer = discord.SlashCommandGroup("trainer", "Trainer Commands for Pokerole")
    
    async def class_autocomplete(self, ctx):
        return [n for n in self.data['Class'] if ctx.value.lower() in n.lower()][:25]
    
    async def rank_autocomplete(self, ctx):
        return [n for n in self.data['Rank'] if ctx.value.lower() in n.lower()][:25]
    
    @trainer.command(description="Get Poke Awarded After a Battle")
    @discord.option("tclass", autocomplete=class_autocomplete, description="Trainer's Class/Type")
    @discord.option("trank", autocomplete=rank_autocomplete, description="Trainer's Pokerole Rank")
    async def reward(self, ctx, tclass:str, trank:str):
        try:
            cash = self.data['Class'][tclass]
            multi = self.data['Rank'][trank]
            await ctx.respond(f"After your fight with a *{trank} {tclass}*,\n You got ***{cash*multi}*** *({cash}+{multi})* for winning!")
        except Exception as e:
            await ctx.respond(f"There was a problem... I had an {e.args[0]}")

def setup(bot):
    bot.add_cog(TrainerCog(bot))

# Non Discord Functions
