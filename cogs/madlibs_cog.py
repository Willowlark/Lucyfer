from discord.ext import commands
import discord
from random import choice
import re
import yaml

DEBUG = False
VERBOSE = False

class MadlibCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.tableset = self._load_tables()
    
    table = discord.SlashCommandGroup("table", "Interact with random tables.")
    
    async def game_autocomplete(self, ctx: discord.AutocompleteContext):
        choices = [c for c in self._all_sources() if ctx.value.lower() in c.lower()][:25]
        return choices
    
    async def table_autocomplete(self, ctx: discord.AutocompleteContext):
        options = self._all_titles(ctx.options['game'])
        choices = [c for c in options if ctx.value.lower() in c.lower()][:25]
        return choices
    
    @table.command(description="Roll on a Random Table")
    @discord.option("game", autocomplete=game_autocomplete, description="System / Game the Table is for.")
    @discord.option("table", autocomplete=table_autocomplete, description="Table to roll on.")
    @discord.option("number", default=1, description="Number of times to roll on the table.")
    async def roll(self, ctx, game:str, table:str, number:int):
        reroller = self.RerollTableView()
        reroller.set_values(self, game, table, number)
        try:
            text = self._table_roll_gen(game, table, number)
            await ctx.respond(f"Rolled: {text}.", view=reroller)
        except Exception as e:
            await ctx.respond(
                f"There was a problem... I had an {e.args[0]}")

    # @table.command() # Create a slash command
    # async def button(self, ctx):
    #     await ctx.respond("This is a button!", view=RerollTableView()) # Send a message with our View class that contains the button

    @table.command(description="Print a table as Markdown.")
    @discord.option("game", autocomplete=game_autocomplete, description="System / Game the Table is for.")
    @discord.option("table", autocomplete=table_autocomplete, description="Table to print.")
    async def print(self, ctx, game:str, table:str):
        try:
            table_id = self._find_table(game, table)
            result = self._markdown(table_id)
            await ctx.respond(f"Here's your table:\n\n### {table}\n\n```\n{result}\n```")
        except Exception as e:
            await ctx.respond(f"There was a problem... I had an {e.args[0]}")
    
    @table.command(description="Reload the tables databse.")
    async def reload(self, ctx: discord.ApplicationContext):
        self.tableset = self._load_tables()
        await ctx.respond('reloaded.')

# # Non Discord Functions

    def _load_tables(self):
        x = yaml.safe_load(open('data/tables.yaml'))
        print(x)
        return x
    
    def _table_roll_gen(self, game, table, number):
        table_id = self._find_table(game, table)
        results = []
        for i in range(number):
            results.append(f'*{self._yaml_table(table_id)}*')
        result = '\n'.join(results)
        if number > 1: result = '\n'+result
        return result
    
    def _all_sources(self):
        return set([self.tableset[table][0]['source'] for table in self.tableset])
    
    def _all_titles(self,source_filter = None):
        if not source_filter:
            return set([self.tableset[table][0]['title'] for table in self.tableset])
        else: 
            choices = [self.tableset[table][0] for table in self.tableset]
            return [c['title'] for c in choices if source_filter.lower() in c['source'].lower()]
        
    def _find_table(self, source, title):
        return [table for table in self.tableset if self.tableset[table][0]['source'] == source and self.tableset[table][0]['title'] == title][0]
        
    def _yaml_table(self, table, log={}):
        REPLACE_PATTERN = f'<(.*?)#?(\d+)?>'
        # Search for Human Readable match from Table
        if table not in self.tableset:
            raise Exception("UnknownTableNameError")
        if DEBUG: print([x for x in self.tableset[table] if type(x) != dict])
        result = choice([x for x in self.tableset[table] if type(x) != dict])
        for replace_target, replace_id in re.findall(REPLACE_PATTERN, result):
            if replace_id not in log:
                r = self._yaml_table(replace_target, log)
                result = re.sub(REPLACE_PATTERN, r, result, count=1)
            else:
                result = re.sub(REPLACE_PATTERN, log[replace_id], result, count=1)
            
            if replace_id: log[replace_id] = r
        return result
    
    def _markdown(self, table):
        ops = [x for x in self.tableset[table] if type(x) != dict]
        op_cnt = len(ops)
        try:
            dimensions = self._die_codify(op_cnt)
            if type(dimensions) == int: dimensions = [1, dimensions]
        except:
            return f"Can't Make Table for {table} with {op_cnt} Options"

        cols = []
        for c in range(0, dimensions[0]):
            cols.append(ops[c*dimensions[1]:c*dimensions[1]+dimensions[1]])        
        
        # The 'd' column is automatically added through the dimension sizes.
        if dimensions[0] == 3: headers = '|d|1-2|3-4|5-6|'
        elif dimensions[0] == 2: headers = '|d|1-3|4-6|'
        else: 
            headers = '|'.join([f'{i}' for i in range(1,dimensions[0]+1)])
            headers = f'|d|{headers}|'
        divider = '|---'*(dimensions[0]+1) + '|' #+1 for the d column
        mdrows = []
        row_cnt = 0
        for i in zip(*cols):
            row_cnt+=1
            mdrows.append(f'|{row_cnt}|'+'|'.join(i)+'|')
        output = headers+'\n'+divider+'\n'
        output += '\n'.join(mdrows)
        # print(output)
        return output
        
    def _die_codify(self, op_cnt):
        for d in [20, 12, 10, 8, 6, 4, 3, 2]:
            if op_cnt % d == 0: # Even divides only, can't have fraction tables.
                slice_size = op_cnt/d
                if slice_size == 1: # Base Case, options fit in a single column.
                    return 1, d
                else: # d is the column size, die_codify for a row wise
                    nxt = self._die_codify(slice_size) 
                    if nxt[0] == 1: 
                        return nxt[1], d
                    else:
                        raise Exception("Weird Case Found, 3 dimensions")
        raise Exception(f"Can't Make Table for {op_cnt} Options")

    class RerollTableView(discord.ui.View): 
        
        def set_values(self, parent, game, table, number):
            self.caller = parent
            self.game = game
            self.table = table
            self.number = number
        @discord.ui.button(label="Reroll", style=discord.ButtonStyle.primary) 
        async def button_callback(self, button, interaction):
            await interaction.response.send_message(f"Rolled {self.caller._table_roll_gen(self.game, self.table, self.number)}") 

def setup(bot):
    bot.add_cog(MadlibCog(bot))


            
if __name__ == '__main__':
    m = MadlibCog('bot')
    print(m._all_sources())
    print(m._all_titles('Forgotten Ballad'))
    print(m._find_table('Forgotten Ballad', 'Instrument'))
    print(m._yaml_table('forgotten_ballad_relic'))
    print(m._markdown('forgotten_ballad_weapon'))
    print(m._markdown('forgotten_ballad_instrument'))
    print(m._markdown('atla_air_nomad_names'))