from discord.ext import commands
import discord
import random
import re
import sys
from simpleeval import simple_eval
from itertools import product

VERBOSE = False

class DiceCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(description="Roll Dice")
    @discord.option("dice", 
                    type=discord.SlashCommandOptionType.string, 
                    description="Supports Advantage, Top X, Fudge dice, Coin dice, XdY.")
    async def roll(self, ctx, dice:str):
        og, rolls, total = parse(dice)
        await ctx.respond(
            f"Rolled `{og}` and got {total}!\nThe rolls were: *{rolls}*")

def setup(bot):
    bot.add_cog(DiceCog(bot))

# Non Discord Functions

def _adv_roll(match):
    n, s, t = match.groups()
    n = int(n) if n else 1
    s = int(s)
    
    rolls = []
    for x in range(0, n):
        roll1 = random.randint(1, s)
        roll2 = random.randint(1, s)
        higher = roll1 if roll1 >= roll2 else roll2
        lower = roll1 if roll1 < roll2 else roll2
        if t == 'a': higher = f"**{higher}**"
        if t == 'd': lower = f"**{lower}**"
        rolls.append(f"({higher},{lower})")
    return f"({'+'.join([str(x) for x in rolls])})"

def _top_roll(match):
    n, s, cnt = match.groups()
    n = int(n) if n else 1
    s = int(s)
    cnt = int(cnt) if int(cnt) > 0 else 1
    
    rolls = []
    for x in range(0, n):
        roll = random.randint(1, s)
        rolls.append(roll)
    
    rolls = sorted(rolls,reverse=True)
    rolls = [str(x) for x in rolls]
    cnt = cnt if cnt < len(rolls) else len(rolls)
    rolls = [f"**{x}**" for x in rolls[:cnt]]+rolls[cnt:]
    return f"({'+'.join(rolls)})"

def _bool_roll(match):
    n, s, op, comp = match.groups()
    n = int(n) if n else 1
    s = int(s)
    comp = int(comp) if int(comp) > 0 else 1
    
    rolls = []
    for x in range(0, n):
        roll = random.randint(1, s)
        rolls.append(roll)
    
    rolls = [f"**{x}**" if simple_eval(str(x)+op+str(comp)) else f"{x}" for x in rolls]
    rolls = sorted(rolls, key=len, reverse=True)
    return f"[{'+'.join(rolls)}]"

def _basic_roll(match):
    # print(match.groups())
    n, s = match.groups()
    n = int(n) if n else 1
    s = int(s)
    
    rolls = []
    for x in range(0, n):
        roll = random.randint(1, s)
        rolls.append(roll)
    return f"({'+'.join([str(x) for x in rolls])})"

def _fudge_roll(match):
    n = match.groups()[0]
    n = int(n) if n else 4
    
    sides = [-1, -1, 0, 0, 1, 1]
    rolls = []
    for x in range(0, n):
        roll = sides[random.randint(0, 5)]
        rolls.append(roll)
    
    return f"({'+'.join([str(x) for x in rolls])})"

def _coin_flip(match):
    n = match.groups()[0]
    n = int(n) if n else 1
    
    sides = [0, 1]
    rolls = []
    for x in range(0, n):
        roll = sides[random.randint(0, 1)]
        rolls.append(roll)
    
    return f"({'+'.join([str(x) for x in rolls])})"

def _eval_bool(match):
    s = match.groups()[0]
    # Remove the dropped rolls from the bolded notation rolls
    s = re.sub('(?<=\d\*\*)((?:\+\d+)+)',r'',s) 
    # Removes all bolded numbers (Top rolls) and replaces with One
    s = re.sub('\*\*(\d+)\*\*', r'1', s)
    s = re.sub('\[', '(', s)
    s = re.sub('\]', ')', s)
    return s
   
def parse(diestring):
    if VERBOSE: print('input', diestring)
    # Parse Dice notation
    die = "(\d*)d(\d+)"
    
    rawstring = re.sub(f'{die}(a|d)', _adv_roll, diestring) # 1d20a 3d6d
    rawstring = re.sub(f'{die}\^(\d+)', _top_roll, rawstring) # 4d6^3 
    rawstring = re.sub(f'{die}(<|>|<=|>=|==)(\d+)', _bool_roll, rawstring)
    rawstring = re.sub(f'{die}', _basic_roll, rawstring)
    rawstring = re.sub(f'(\d*)dF', _fudge_roll, rawstring)
    rawstring = re.sub(f'(\d*)dC', _coin_flip, rawstring)
    if VERBOSE: print('Rolling Finished', rawstring)
    
    # Compress Advantage/Disadvantage before doing math, removing Bolding and unused roll
    evalstring = re.sub('\(\*\*([0-9]+)\*\*,[0-9]+\)|\([0-9]+,\*\*([0-9]+)\*\*\)', r"\1\2",rawstring)
    if VERBOSE: print('adv/disadv calc', evalstring)
    # Removes all underscore numbers (Successes) and replaces with one
    evalstring = re.sub('(\[.*?\])', _eval_bool, evalstring)
    if VERBOSE: print('boolean calc', evalstring)
    # Remove the dropped rolls from the bolded and underscore notation rolls
    evalstring = re.sub('(?<=\d\*\*)((?:\+\d+)+)',r'',evalstring) 
    # Removes all bolded numbers (Top rolls) and replaces with the raw number
    evalstring = re.sub('\*\*(\d+)\*\*', r'\1', evalstring)
    if VERBOSE: print('Top X calc', evalstring)
    # Split when using literal combine notation ||
    evalstrings = evalstring.split('||')
    evalstring = ''
    for e in evalstrings:
        evalstring += str(simple_eval(e))
    total = int(simple_eval(evalstring))
    
    return diestring, rawstring, total
    
    # 1d20a+2d8+4d6^3+4d6>3
    # ((**9**,6))+(5+2)+(**6**+**5**+**3**+2)
    # (9)+(5+2)+(**6**+**5**+**3**+2)
    # (9)+(5+2)+(**6**+**5**+**3**)
    # (9)+(5+2)+(6+5+3)

def _die_faces(match):
    # print(match.groups())
    n, s = match.groups()
    n = int(n) if n else 1
    s = int(s)
    
    return f"({','.join([str(x) for x in [i for i in range(n, (n*s)+1)]])})"

def faces(diestring):
    if VERBOSE: print('Permutations', diestring)
    # Parse Dice notation
    die = "(\d*)d(\d+)"
    
    rawstring = re.sub(f'{die}', _die_faces, diestring)
    if VERBOSE: print('Rolls Replaced:', rawstring)
    
    # Split when using literal combine notation ||
    evalstrings = rawstring.split('||')
    # print(evalstrings)
    products = []
    for e in evalstrings:
        faces = re.sub(f'\(|\)', '', e)
        products.append([int(x) for x in faces.split(',')])
    if VERBOSE: print("Products:", products)
    
    total = [int(''.join([str(y) for y in x])) for x in product(*products)]
    # total = list(chain(*total))
    if VERBOSE: print("Total is:", total)
    
    return total
    
if __name__ == "__main__":
    VERBOSE = True
    faces(''.join(sys.argv[1:]))