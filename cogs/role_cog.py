import discord
from discord.ext import commands
import yaml
from config import OWNER_ID

VERBOSE = False

class RoleCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.data = yaml.safe_load(open('data/role_management.yaml'))
    
    def save_data(self):
        with open('data/role_management.yaml', 'w') as f:
            f.write(yaml.dump(self.data))
    
    def manager_check(self, guild_id, id):
        result = self.data['managers'].get(guild_id, [])
        if id in result or id == OWNER_ID: return True
        else: return False
    
    # # Commands -------------------------------------
    
    role = discord.SlashCommandGroup("role", "Work with roles")
    
    # ------------------------------------------------
    
    async def roles_ac(self, ctx):
        if self.manager_check(ctx.interaction.guild.id, ctx.interaction.user.id):
            options = [r for r in ctx.interaction.guild.roles if r.is_assignable()]
            choices = [r.name for r in options if ctx.value.lower() in r.name.lower()][:25]
            return choices
        else: return [""]
    
    @role.command(description="Enable a Command Role")
    @discord.option("role", autocomplete=roles_ac, description="Role to allow opt into.")
    async def manage(self, ctx, role:str):
        if not self.manager_check(ctx.guild.id, ctx.user.id):
            await ctx.response.send_message(
                f"Only role managers can add enable new roles to be added. Sorry!", ephemeral=True)
            
        role_id, ds_role = get_role_id_from_name(ctx, role)
        
        # Get the assignable roles, adding the guild if it's not been added before.
        if ctx.guild.id not in self.data['assignable']: 
            self.data['assignable'][ctx.guild.id] = []
        assignable = self.data['assignable'][ctx.guild.id]
        
        # Check that this role can be assigned.
        if not ds_role.is_assignable():
            await ctx.respond(
                f"I don't have permission to manage that role. Sorry!", ephemeral=True)
        
        # If role not assignable currently, make it assignable.
        elif role_id not in assignable:
            assignable.append(role_id)
            await ctx.respond(
                f"{role} can now be self added by users.", ephemeral=True)
        # Role is assignable, so make it unassignable.
        else:
            assignable.remove(role_id)
            await ctx.respond(
                f"{role} can no longer be self added by users.", ephemeral=True)
        self.save_data()

    # ------------------------------------------------

    async def add_roles_ac(self, ctx):
        assignable = self.data['assignable'][ctx.interaction.guild.id]
        options = [r for r in ctx.interaction.guild.roles if r.id in assignable]
        choices = [r.name for r in options if ctx.value.lower() in r.name.lower()][:25]
        return choices

    @role.command(description="Opt into a Role")
    @discord.option("role", autocomplete=add_roles_ac, description="Role to opt into.")
    async def toggle(self, ctx, role:str):
        role_id, ds_role = get_role_id_from_name(ctx, role)
        has_role = [r.id for r in ctx.user.roles if r.id == role_id]
        
        assignable = self.data['assignable'].get(ctx.guild.id, [])

        if role_id not in assignable: 
            await ctx.response.send_message(
            f"{ds_role.name} isn't a role I can manage, sorry!", ephemeral=True)
        elif not has_role and role_id: 
            await ctx.user.add_roles(ds_role)
            await ctx.response.send_message(
            f"Added role {ds_role.name}.", ephemeral=True)
        elif has_role: 
            await ctx.user.remove_roles(ds_role)
            await ctx.response.send_message(
            f"Removed role {ds_role.name}.", ephemeral=True)

    # ------------------------------------------------

    async def manager_ac(self, ctx):
        if self.manager_check(ctx.interaction.guild.id, ctx.interaction.user.id):
            options = [r for r in ctx.interaction.guild.members]
            choices = [r.display_name for r in options if ctx.value.lower() in r.name.lower() or ctx.value.lower() in r.display_name.lower()][:25]
            return choices
        else: return [""]

    @role.command(description="Add a user who can configure opt in roles.")
    @discord.option("user", autocomplete=manager_ac, description="User to allow management")
    async def manager(self, ctx, user:str):
        if ctx.user.id != OWNER_ID:
            await ctx.respond(f"Only the owner can add or remove managers!", ephemeral=True)
        member = [m for m in ctx.guild.members if 
                    m.name == user or m.display_name == user][0]
        if member:            
            # Add Guild if it's never been used before, then get the manager list.
            if ctx.guild.id not in self.data['managers']: 
                self.data['managers'][ctx.guild.id] = []
            managers = self.data['managers'][ctx.guild.id]
            
            # Add user as a manager if they aren't in the list.
            if member.id not in managers:
                managers.append(member.id)
                await ctx.respond(
                    f"User {member.display_name} can now manage roles.", ephemeral=True)
            
            # Remove the user as a manager if they are.
            else:
                managers.remove(member.id)
                await ctx.respond(
                    f"User {member.display_name} can no longer manage roles.", ephemeral=True)
            self.save_data()
        else:
            await ctx.respond(
                f"I don't know who {user} is? ", ephemeral=True)

# ----------------------------------------------------

def setup(bot):
  bot.add_cog(RoleCog(bot))

# Support Discord Functions

def get_role_id_from_name(ctx, role):
    roles = ctx.guild.roles
    ds_role = [r for r in roles if r.name == role][0]
    role_id = ds_role.id
    return role_id, ds_role

# Non Discord Functions

