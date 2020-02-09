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
            await ctx.message.delete()
            raise commands.DisabledCommand()
        return True
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

@bot.command()
@bot_cli()
@commands.has_role("Admin")
async def hello(ctx):
    await ctx.send("Hello World!")

@hello.error
async def hello_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        print("Someone other than an admin attempted this command!")
    elif isinstance(error, commands.NoPrivateMessage):
        print("Someone tried to execute this command in a private message!")
    elif isinstance(error, commands.DisabledCommand):
        print("Someone tried to execute this command outside of the cli channel!")

bot.run(token)
