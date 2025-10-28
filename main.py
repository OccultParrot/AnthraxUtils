import os
import datetime
import json

import discord
from dotenv import load_dotenv
from rich.console import Console
from discord import Client, Intents, app_commands, Object, Interaction, Embed

load_dotenv()
console = Console()


class AnthraxUtilsClient(Client):
    def __init__(self):
        intents = Intents.default()
        super().__init__(intents=intents)

        self.lifespans = {}
        self.load_configs()

        self.guild_id = Object(id=os.getenv("GUILD_ID"))
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=self.guild_id)
        await self.tree.sync(guild=self.guild_id)

    def load_configs(self):
        with open("config/lifespans.json", "r") as f:
            self.lifespans = json.load(f)


client = AnthraxUtilsClient()


# == Add events and commands here! ==
@client.event
async def on_ready():
    console.print(f"Logged in as [green]{client.user.name}[/green]", justify="center")


@client.tree.command(name="calculate-age", description="Calculate the age of your dino, using their birthdate.")
@app_commands.describe(birthdate="In YYYY-MM-DD format", species="Select the species")
@app_commands.choices(species=[
    app_commands.Choice(name=species["species"].title(), value=species["species"]) for species in client.lifespans
])
async def calculate_age(interaction: Interaction, birthdate: str, species: app_commands.Choice[str]):
    lifestages = []
    for spec in client.lifespans:
        if spec["species"] == species.value:
            lifestages = spec["lifeStages"]
            break
    try:
        birth_date = datetime.datetime.fromisoformat(birthdate).date()
        difference = abs((birth_date - datetime.date.today()).days)
        age = difference // 7

        embed = Embed(title="Age of Dino", description=f"""\
Age in Weeks: `{age} week(s)`
Age in in-game years: `{age // 4} year(s)`
""", color=discord.Color.greyple())
        embed.add_field(name="Today's Date", value=datetime.date.today().strftime("%d-%m-%Y"), inline=True)
        embed.add_field(name="Birthdate", value=birth_date.strftime("%d-%m-%Y"), inline=True)
        for stage in lifestages:
            stage_name = stage["title"]
            stage_age = stage["minAge"]
            if age >= stage_age:
                embed.add_field(name=f"Life Stage: {stage_name}", value=f"Reached at {stage_age} week(s)", inline=False)
        embed.set_footer(text="Each in-game year is 4 weeks long.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except ValueError as e:
        await interaction.response.send_message("Invalid date format. Please use DD-MM-YYYY.", ephemeral=True)
        return


# == Running the bot ==
client.run(os.getenv("TOKEN"))
