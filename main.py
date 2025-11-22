import datetime
import json
import os

import discord
from discord import Client, Intents, app_commands, Object, Interaction, Embed, Message
from dotenv import load_dotenv
import asyncio
from rich.console import Console
from supabase import Client as SupabaseClient

load_dotenv()
console = Console()

CACHE_REFRESH_INTERVAL = 300  # seconds


class AnthraxUtilsClient(Client):
    def __init__(self):
        intents = Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        self.lifespans = {}
        self.load_configs()

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()
        console.print("Commands synced globally", style="green")

    def load_configs(self):
        with open("config/lifespans.json", "r") as f:
            self.lifespans = json.load(f)
        console.print(f"Loaded [yellow i]{len(self.lifespans)}[/] lifespan entries.", style="green")

    async def refresh_cache(self):
        pass


class StickyModal(discord.ui.Modal):
    def __init__(self, callback):
        super().__init__(title="Create Sticky Message")
        self.content = discord.ui.TextInput(label="Message Content", style=discord.TextStyle.paragraph, required=True,
                                            max_length=2000)
        self.add_item(self.content)
        self.callback = callback

    async def on_submit(self, interaction: Interaction, /) -> None:
        await self.callback(self.content.value, interaction)


class DBClient(SupabaseClient):
    listened_channels: list[int] = []
    stickied_messages: list = []

    def __init__(self):
        # Setting up database connection
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        super().__init__(url, key)

        self.refresh_cache()

    async def start_cache_refresh(self):
        asyncio.create_task(self.refresh_cache_task())

    async def refresh_cache_task(self):
        print("Starting cache refresh task...")
        while True:
            console.log("Refreshing cache...")
            self.refresh_cache()
            await asyncio.sleep(CACHE_REFRESH_INTERVAL)  # Refresh every 60 seconds

    def refresh_cache(self):
        self.listened_channels = self.fetch_listened_channels()
        self.stickied_messages = self.fetch_sticky_messages()

    def fetch_sticky_messages(self):
        try:
            data = self.table("sticky_messages").select("*").execute()
            return data.data
        except Exception as e:
            console.print(f"Error fetching sticky messages: {e}", style="red")
            return []

    def fetch_listened_channels(self):
        try:
            data = self.fetch_sticky_messages()
            return list(set([msg["channel_id"] for msg in data]))
        except Exception as e:
            console.print(f"Error fetching listened channels: {e}", style="red")
            return []

    def post_sticky_message(self, message_id: int, channel_id: int, guild_id: int, content: str):
        try:
            data = {
                "message_id": message_id,
                "channel_id": channel_id,
                "guild_id": guild_id,
                "content": content
            }
            response = self.table("sticky_messages").insert(data).execute()
            return response.data
        except Exception as e:
            console.print(f"Error posting sticky message: {e}", style="red")
            return None

    def refresh_sticky_message(self, old_id: int, new_id: int):
        try:
            response = self.table("sticky_messages").update({"message_id": new_id}).eq("message_id", old_id).execute()
            return response.data
        except Exception as e:
            console.print(f"Error refreshing sticky message: {e}", style="red")
            return None

    def delete_sticky_message(self, message_id: int):
        try:
            response = self.table("sticky_messages").delete().eq("message_id", message_id).execute()
            return response.data
        except Exception as e:
            console.print(f"Error deleting sticky message: {e}", style="red")
            return None


client = AnthraxUtilsClient()
db_client = DBClient()


# == Add events and commands here! ==
@client.event
async def on_ready():
    console.print(f"Logged in as [green]{client.user.name}[/green]", justify="center")
    await db_client.start_cache_refresh()

    for sticky in db_client.stickied_messages:
        try:
            channel = client.get_channel(sticky["channel_id"])
            message = await channel.fetch_message(sticky["message_id"])
            old_id = message.id
            await message.delete()

            # Sending new sticky message
            new_message = await channel.send(sticky["content"])

            # Update DB and cache
            db_client.refresh_sticky_message(old_id, new_message.id)
            db_client.refresh_cache()
        except Exception as e:
            console.print(
                f"Error in refreshing sticky message ID {sticky['message_id']} in channel ID {sticky['channel_id']}: {e}",
                style="red")


@client.event
async def on_message(message: Message):
    if message.author.id == client.user.id:
        return

    if message.channel.id in db_client.listened_channels:
        for sticky in db_client.stickied_messages:
            if sticky["channel_id"] == message.channel.id:
                # Getting old message and deleting it
                old_message = await message.channel.fetch_message(sticky["message_id"])
                old_id = old_message.id
                await old_message.delete()

                # Sending new sticky message
                new_message = await message.channel.send(sticky["content"])

                # Update DB and cache
                db_client.refresh_sticky_message(old_id, new_message.id)
                db_client.refresh_cache()


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


@client.tree.command(name="make-sticky", description="Creates a message that stays on the bottom of the discord chat.")
async def make_sticky(interaction: Interaction):
    if not (interaction.user.guild_permissions.administrator or interaction.user.id == 767047725333086209):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    await interaction.response.send_modal(StickyModal(create_sticky_message))


async def create_sticky_message(content: str, interaction: Interaction):
    guild_id = interaction.guild.id
    channel_id = interaction.channel.id
    sticky_msg = await interaction.channel.send(content)
    db_client.post_sticky_message(sticky_msg.id, channel_id, guild_id, content)
    db_client.refresh_cache()

    await interaction.response.send_message("Sticky message created!", ephemeral=True)


@client.tree.command(name="remove-sticky", description="Removes selected sticky message from the channel.")
@app_commands.describe(message_id="The ID of the sticky message to remove")
async def remove_sticky(interaction: Interaction, message_id: str):
    if not (interaction.user.guild_permissions.administrator or interaction.user.id == 767047725333086209):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    message_id = int(message_id)
    await interaction.response.send_message("Removing sticky message...", ephemeral=True)
    message = await interaction.channel.fetch_message(message_id)
    await message.delete()
    db_client.delete_sticky_message(message_id)
    db_client.refresh_cache()

    await interaction.edit_original_response(content="Sticky message removed!")


@remove_sticky.autocomplete("message_id")
async def remove_sticky_autocomplete(interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
    filtered = [
        s for s in db_client.stickied_messages
        if str(s["message_id"]).startswith(current) and s["channel_id"] == interaction.channel.id
    ]
    return [
        app_commands.Choice(
            name=f"ID: {s['message_id']} | Content: {s['content'][:30]}{"..." if len(s['content']) > 30 else ""}",
            value=str(s["message_id"]))
        for s in filtered[:25]
    ]


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
