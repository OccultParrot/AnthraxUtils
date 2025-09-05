import os

from dotenv import load_dotenv
from rich.console import Console
from discord import Client, Intents, app_commands, Object

load_dotenv()
console = Console()

class AnthraxUtilsClient(Client):
    def __init__(self):
        intents = Intents.default()
        super().__init__(intents=intents)
        
        self.guild_id = Object(id=os.getenv("GUILD_ID"))
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=self.guild_id)
        await self.tree.sync(guild=self.guild_id)
        
client = AnthraxUtilsClient()

# == Add events and commands here! ==
@client.event
async def on_ready():
    console.print(f"Logged in as [green]{client.user.name}[/green]", justify="center")

# == Running the bot ==
client.run(os.getenv("TOKEN"))
    