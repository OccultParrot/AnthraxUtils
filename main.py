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
        console.print(f"Loaded [yellow i]{len(self.lifespans)}[/] lifespan entries.", style="green")


client = AnthraxUtilsClient()


# == Add events and commands here! ==
@client.event
async def on_ready():
    console.print(f"Logged in as [green]{client.user.name}[/green]", justify="center")


# TODO: Find cleaner way to select date, maybe 3 int inputs for day, month, year?
@client.tree.command(name="calculate-age", description="Calculate the age of your dino, using their birthdate.")
@app_commands.describe(day="The day the dinosaur was born", month="The month the dinosaur was born",
                       year="The year the dinosaur was born", species="Select the species")
async def calculate_age(interaction: Interaction, day: int, month: int, year: int, species: str):
    # Getting the lifestages for the selected species.
    lifestages = []
    for spec in client.lifespans:
        if spec["species"].lower() == species.lower():
            lifestages = spec["lifeStages"]
            break

    try:
        print(f"Calculating age for {interaction.user.display_name}...")

        # The date of the first shutdown event. TODO: Find better way to handle subtracting shutdowns, maybe a csv of shutdown end dates?
        shutdown_date = datetime.date(2025, 10, 12)

        birth_date = datetime.datetime.fromisoformat(
            f"{year}-{"0" + str(month) if month < 10 else month}-{"0" + str(day) if day < 10 else day}").date()
        difference = abs((birth_date - datetime.date.today()).days)
        
        # If the dino was born before the first shutdown, subtract 15 days from the age.
        # TODO: Please improve this hacky solution. Maybe loop through the shutdown dates in a list and subtract accordingly? I feel bad using a magic number lol
        if shutdown_date < datetime.date.today():
            difference -= 15
        age = difference // 7

        embed = Embed(
            title="Age of Dino",
            description=f"""\
Age in Weeks: `{age} week(s)`
Age in in-game years: `{age // 4} year(s)`
""",
            color=discord.Color.greyple(),
        )
        embed.add_field(
            name="Today's Date",
            value=datetime.date.today().strftime("%d-%m-%Y"),
            inline=True,
        )
        embed.add_field(
            name="Birthdate", value=birth_date.strftime("%d-%m-%Y"), inline=True
        )
        embed.set_footer(text="Each in-game year is 4 weeks long.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except ValueError as e:
        await interaction.response.send_message("Invalid date format. Please use DD-MM-YYYY.", ephemeral=True)
        return


@calculate_age.autocomplete("species")
async def species_autocomplete(_: Interaction, current: str) -> list[app_commands.Choice[str]]:
    """
    Autocomplete for species field in /calculate-age command
    :param _: The discord interaction *(discarded)*
    :param current: The current query
    :return: An arroy of app_commands.Choice objects, limited to 25 results because discord does not allow more to be used in command choices
    """
    filtered = [
        s for s in client.lifespans
        if current.lower() in s["species"].lower()
    ]

    return [
        app_commands.Choice(name=s["species"], value=s["species"].title())
        for s in filtered[:25]
    ]


@client.tree.command(name="help", description="Lists all available commands")
async def help_command(interaction: Interaction):
    embed = Embed(
        title="AnthraxUtils Commands",
        description="Here are all the commands available in AnthraxUtils!",
        color=discord.Color.greyple(),
    )
    commands = {
        "help": "... You are using it rn lol",
        "calculate_age": "Calculates how old the dinosaur is from the given date.",
    }

    for name in commands:
        embed.add_field(name=name, value=commands[name], inline=True)

    embed.set_footer(
        text="If you have any ideas for more quality of life commands, DM OccultParrot!"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# == Running the bot ==
client.run(os.getenv("TOKEN"))
