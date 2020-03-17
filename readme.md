# Manageable

A friendly, easy-to-use discord management bot.

Created by Ben Schwabe, originally for a worldbuilding Discord server. Feature backlog can be found [here](https://trello.com/b/RgsfkGX1/manageable)

# Command List
Currently, Manageable has these commands:

| Command                                      | Description                                                                                                                                                                                                                                                                                  |
| :------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `help <optional: command>`                   | DMs a paginated display enumerating all the available bot commands, or a single command's details if specified.                                                                                                                                                                              |
| `tag <optional: name>`                       | Posts an embed in chat with the given details provided in the config file.                                                                                                                                                                                                                   |
| `warn <apply;resolve;undo;view> <user>`      | _mod only:_ Performs the specified action to the defined user. Actions can be `apply` to give a user another warning, `resolve` remove the oldest warning for that user, `undo` to remove the newest warning for that user, and `view` to display the amount of warnings given to that user. |

## Setup

##### 1) Install Python
First, make sure that you have Python 3.4 or above installed. This code was tested on Python 3.8, however, and it is recommended you use that version if possible. Python can be downloaded [here](https://www.python.org/).

##### 2) Install Package Requirements
Once you have confirmed that Python is installed correctly, install the necessary python packages by running `pip install -r requirements.txt`. This will install all necessary python requirements to your system for Manageable to run.

##### 3) Set Up the Bot Account
After that, you'll need to configure Manageable to run on your server. Go to the [Discord Developer Portal](https://discordapp.com/developers/applications/) and follow [these instructions](https://discordpy.readthedocs.io/en/latest/discord.html) to create a bot account and add it to your server. Take note of the bot's token, as you'll need it later.

_**Permissions:**_

Manageable will need these permissions to run. Omitting any of these permissions may cause the bot to not function correctly.

| Requirement   | Reason                                                                          |
| :-------------| :------------------------------------------------------------------------------ |
| View Channels | The bot needs to be able to see the channels so it can watch them for commands. |
| Send Messages | The bot needs to be able to send server message and DMs to respond to commands. |
| Embed Links   | The bot needs to be able to embed links to display some commands correctly.     |
| Add Reactions | The bot uses reactions to control pagination of its help command.               |

##### 4) Configure the Bot Functionality
Open `config.json`, located in the `Config` folder. Paste in the bot's token you received from discord in the `token` line, and configure any other information desired. Documentation for the configuration file is found in a later section.

##### 5) Run the Bot
In the root directory of Manageable, execute `manageable.py`. If everything is set up correctly, you should see the bot appear online in the server you've invited it to.

## Config.json
This is the main json configuration file for Manageable, and contains all the basic, configurable parameters to tweak Manageable's functionality. Below is a description of each parameter.

* `/token`: A string token given by Discord after configuring your bot with their developer portal. Be sure not to share this token with anyone.
* `/command_prefix`: A string prefix to address the bot so that it knows a command is being run.
* `/mod_roles`: A string list of all the role names (case sensitive) that you'd like to be able to execute Manageable's moderator-only commands.
* `/help_commands_per_page`: An integer denoting how many commands you'd like the help command to display per page.
* `/content/codex_links/color`: A hexadecimal color value, with a hash tag (`#`) in front of it, denoting what color to make the codex link embeds
* `/content/codex_links/world_anvil`: A string URL pointing to the [World Anvil](https://www.worldanvil.com/) codex link.
* `/content/codex_links/google_doc`: A string URL pointing to the [Google Docs](https://docs.google.com) codex link.
