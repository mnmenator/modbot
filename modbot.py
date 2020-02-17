# modbot.py
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix='!')

def bot_cli():
    async def predicate(ctx):
        if ctx.message.channel.name != "bot-cli":
            raise commands.DisabledCommand()
        return True
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

@bot.command()
@commands.has_role("Admin")
@bot_cli()
async def hello(ctx):
    await ctx.send("Hello World!")

@hello.error
async def hello_error(ctx, error):
    if isinstance(error, commands.NoPrivateMessage):
        return
    elif isinstance(error, commands.MissingRole):
        await ctx.message.delete()
        print("Someone other than an admin attempted this command!")
    elif isinstance(error, commands.DisabledCommand):
        await ctx.message.delete()
        print("Someone tried to execute this command outside of the cli channel!")

    for member in ctx.guild.members:
        if "Admin" in [role.name for role in member.roles]:
            print(member.display_name)

bot.run(token)
