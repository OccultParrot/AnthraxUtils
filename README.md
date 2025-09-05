# AnthraxUtils

Table of Contents

- [Installation](#installation)
- [Setting up Environment Variables](#setting-up-environment-variables)
- [Bot Tips](#bot-tips)
  - [Adding Commands](#commands)
  - [Added Events](#events)
  - [UI Stuff](#ui-stuff)
- [Git Stuff](#commits-and-pushes-and-pulls)


## Installation

Copy the SSH link in the code button and open your terminal

Change directory to where you want your code to be (C:/Dev for me)

**Clone** the repository with the link

cd into the cloned repo and set up your virtual environment

then install packages and have fun coding!!!

Full command workflow
```Bash
# Change directory (cd) to your root
cd C:/Dev
# Clone repo
git clone git@github.com:OccultParrot/AnthraxUtils.git

# Change directory (cd) to the cloned repo
cd AnthraxUtils
# Set up virtual environment (venv)
python -m venv .venv

# Installing packages
.venv/Scripts/pip install -r "requirements.txt"

# To run the code:
# *READ SETTING UP ENV VARS FIRST!!*
.venv/Scripts/python main.py
```

## Setting up Environment Variables

In the repos directory, make a file named `.env`.

In that file add the following information:
```dotenv
TOKEN=Your Discord Bot Token
GUILD_ID=The Server of the ID you want bot in
```

(You can also just duplicate the `.env.example` file and rename it to `.env`)

How do I get the bot token you may ask? Go to the [Discord Developer Portal](https://discord.com/developers/) and make a new application! 
Then in the bot section you can get your bot token! There is a few config stuff thats weird, I can help with that.

## Bot Tips

Here are some helpful tips to get started writing stuff for a bot!

### Commands

It's *easy* to add a command to the bot! 
All you do is write an asynchronous function and add a decorator denoting it as a command!

Here is a **basic** example!

```py
# This part is already done in the main.py file
client = AnthraxUtilsClient()

# The function decorator (Basically tells the bot this is a command, and information about it)
@client.tree.command(
    name="Hello World",
    description="Replies with Hello World"
)
# The function that will run when command is called
async def hello_world(interaction: Interaction): # All commands take an interaction parameter
    # Replying to the command with "Hello World!"
    # When we do stuff with interactions, we usually have to "await" them
    # This is also true for sending messages with a channel object, and a lot more
    await interaction.response.send_message("Hello World!")
```

There is a lot of stuff we can use to make commands more interesting, like taking options from the user!
Lets take a look at adding options. To add an option to a command, we use the @app_commands.describe decorator,
which we use to add descriptions to options, along with some other stuff!

Here is it in action!

```py
@client.tree.command(
    name="Add",
    description="Adds two numbers together!"
)
@app_commands.describe(a="First number to add together")
@app_commands.describe(b="The second number to add together")
async def add_numbers(interaction: Interaction, a: int, b: int):
    c = a + b
    await interaction.response.send_message(f"{a} + {b} = {c}!")
```

We can specify the type of value we want from the user in the definition of the function. 
Say we want to take a user from the server, all you would do is something like this:
```py
async def get_user(interaction: Interaction, member: discord.Member):
```
This will **Automatically** make it so when the user runs the command they have to specify the user! Isnt that cool!
And we can use that to have the user select a Channel, Role, Emoji, boolean, integer, float, etc, etc! Super cool!

You can also make specific options for the user, like in my roulette game they could click red, black, 1-12, etc, etc. If you wanna know how to do that, just ask me! The commands section is a little long already and I want to move onto more stuff!

### Events
Events are done really similarly to commands, but rather than the user running the command, 
the event looks for if that thing has occured! Take `on_message` for example! 
This event will run everytime a message is sent in *any* channel on *any* server the bot is on!
Lets see how thats done!

```py
# Just like commands we have to add a decorator to let the bot know that its an event
@client.event
# The name of this function is really important, for it tells the bot what event to run it for
async def on_message(message: discord.Message):
    # on_message also triggers when the bot sends a message, so if the author is the bot we return
    if message.author.id == client.user.id:
        return
    # Prints the author and the message to the terminal
    print(f"<{message.author.display_name}> {message.content}")
```

Really easy! To see all the events you can catch, check out [the docs](https://discordpy.readthedocs.io/en/latest/api.html#event-reference)!

### UI Stuff

How to make buttons and stuff! Cool. Completed. Ask me later.

## Commits and Pushes and Pulls

This part is really important, for this is how we collaborate!

**Everytime** you are gonna start coding, run `git pull origin main` so you have the most up-to-date version of the code!
How git works is when you change something, and you want to push it to the repository, you package it up in a commit. 
Once you have made all your commits, you can push it to the repo! I often make commits as I code,
and once I am done with a major part I push it to main. The reason I make so many commits is so that if I break something its easy to roll back to the last commit!

Let's take a look at first adding files to be commited! You can run `git status` to see the current state of all the files.

If you are wanting to commit one or two files but not *all* the ones you have changed, you can specify the path in the command,
or you can just do `-A` to select them all

Then, once you have added them to the list of ones to be commited, you run `git commit -m "message"` where the message part is your description of what changed. 
This important so that if something broke we can see where we are rolling back to.

Once commited, just push to main!

Let's see that in action.
```bash

# Adding all changed files to the list of files to be commited
git add -A
# Commiting with a little message
git commit -m "Added Hello World command"
# Pushing to main
git push origin main
```

If you have a file or directory you don't want to ever be commited, add it to the `.gitignore` file.

Actual git push I just did:
```bash

Tommy@DESKTOP-KVEMU9J MINGW64 /c/Dev/PYTHON/AnthraxUtils (main)
$ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        new file:   .env.example

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   .env.example
        modified:   .gitignore
        modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        main.py


Tommy@DESKTOP-KVEMU9J MINGW64 /c/Dev/PYTHON/AnthraxUtils (main)
$ git add -A
warning: in the working copy of '.env.example', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'README.md', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'main.py', CRLF will be replaced by LF the next time Git touches it

Tommy@DESKTOP-KVEMU9J MINGW64 /c/Dev/PYTHON/AnthraxUtils (main)
$ git commit -m "Added boiler plate, Wrote docs"
[main 6e3f7ad] Added boiler plate, Wrote docs
 4 files changed, 205 insertions(+), 1 deletion(-)
 create mode 100644 .env.example
 create mode 100644 main.py

Tommy@DESKTOP-KVEMU9J MINGW64 /c/Dev/PYTHON/AnthraxUtils (main)
$ git push origin main
Enumerating objects: 9, done.
Counting objects: 100% (9/9), done.
Delta compression using up to 12 threads
Compressing objects: 100% (5/5), done.
Writing objects: 100% (6/6), 3.60 KiB | 1.80 MiB/s, done.
Total 6 (delta 1), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (1/1), completed with 1 local object.
To github.com:OccultParrot/AnthraxUtils.git
   933972f..6e3f7ad  main -> main
```