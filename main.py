import os
import datetime
import json

import discord
from dotenv import load_dotenv
from markdown_it.rules_core import inline
from rich.console import Console
from discord import Client, Intents, app_commands, Object, Interaction, Embed, Message

load_dotenv()
console = Console()


class AnthraxUtilsClient(Client):
    def __init__(self):
        intents = Intents.default()
        intents.message_content = True
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

@client.event
async def on_message(message: Message):
    if message.author.id == 767047725333086209:
        if "what commands" in message.content.lower():
            help_msg = help_embed()
            await message.channel.send(embed=help_msg)

# TODO: Find cleaner way to select date, maybe 3 int inputs for day, month, year?
# TODO: Add back species to the description and function declaration once elder stuff is done
@client.tree.command(name="calculate-age", description="Calculate the age of your dino, using their birthdate.")
@app_commands.describe(day="The day the dinosaur was born", month="The month the dinosaur was born",
                       year="The year the dinosaur was born")
async def calculate_age(interaction: Interaction, day: int, month: int, year: int):
    # Getting the lifestages for the selected species.
    # lifestages = []
    # for spec in client.lifespans:
    #     if spec["species"].lower() == species.lower():
    #         lifestages = spec["lifeStages"]
    #         break

    try:
        print(f"Calculating age for {interaction.user.display_name}...")

        # The date of the first shutdown event. TODO: Find better way to handle subtracting shutdowns, maybe a csv of shutdown end dates?
        shutdown_date = datetime.date(2025, 10, 12)

        birth_date = datetime.datetime.fromisoformat(
            f"{year}-{"0" + str(month) if month < 10 else month}-{"0" + str(day) if day < 10 else day}")
        difference = (datetime.date.today() - birth_date.date()).days

        # Check if birthdate is in the future
        if difference < 0:
            await interaction.response.send_message("Birth date cannot be in the future!", ephemeral=True)
            return

        # If the dino was born before the first shutdown, subtract 15 days from the age.
        # TODO: Please improve this hacky solution. Maybe loop through the shutdown dates in a list and subtract accordingly? I feel bad using a magic number lol
        if shutdown_date > datetime.date.today():
            difference -= 15
        age = difference // 7

        # current_lifestage = None
        # for stage in lifestages:
        #     if age >= stage["minAge"]:
        #         current_lifestage = stage

        # Section for checking what season the dino was born in.
        birth_season_key = None
        seasons = {
            "spring": ":cherry_blossom:",
            "summer": ":sun:",
            "autumn": ":maple_leaf:",
            "fall": ":maple_leaf:",
            "winter": ":snowflake:",
        }
        # Snagging the 20 messages
        try:
            async for message in client.get_guild(1374722200053088306).get_channel(1383845771232678071).history(
                    limit=20, around=birth_date):
                # If the message date is within 1 day of the birthdate, check for season keywords
                if message.created_at.date() <= birth_date.date():
                    for key in seasons.keys():
                        if key in message.content.lower():
                            birth_season_key = key
                            break
                    # Break outta the loop once we have our first match
                    if birth_season_key:
                        break
        # To catch discord errors (Things like impossible dates, etc.) Will just default to "Unknown" if error occurs.
        except Exception as e:
            print(f"Error fetching birth season messages: {e}")

        embed = Embed(
            # title=f"{current_lifestage["stage"] + " " if current_lifestage else ""}{species.title()}'s Age",
            title=f"Dinosaur's Age",
            description=f"""\
Age in Weeks: `{age} week(s)`
Age in in-game years: `{age // 4} year(s)`
Birth Season: `{birth_season_key.title() if birth_season_key else "Unknown"}` {seasons.get(birth_season_key, "")}
""",
            color=discord.Color.greyple(),
        )
        embed.add_field(
            name="Today's Date",
            value=datetime.date.today().strftime("%d-%m-%Y"),
            inline=True,
        )
        embed.add_field(
            name="Birthdate",
            value=f"{birth_date.strftime("%d-%m-%Y")}",
            inline=True
        )

        # if current_lifestage:
        #     embed.add_field(name="Current Life-stage", value=current_lifestage["stage"], inline=False)

        embed.set_footer(text="Each in-game year is 4 weeks long.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except ValueError as e:
        await interaction.response.send_message("Invalid date format. Please check that your inputs are actual dates!.",
                                                ephemeral=True)
        return


# TODO: Uncomment once elder stuff is working
# @calculate_age.autocomplete("species")
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
    await interaction.response.send_message(embed=help_embed(), ephemeral=True)


def help_embed():
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
    return embed


# == Running the bot ==
client.run(os.getenv("TOKEN"))
