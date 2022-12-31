# Manageable

A friendly, easy-to-use discord management bot.

Created by Ben Schwabe, originally for a world-building Discord server. Feature backlog can be found [here](https://trello.com/b/RgsfkGX1/manageable)

## Command List
Currently, Manageable has these commands:

| Command                                        | Description                                                                                                                                                                                                                                                                                  |
|:-----------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `help <optional: command>`                     | DMs a paginated display enumerating all the available bot commands, or a single command's details if specified.                                                                                                                                                                              |
| `tag <optional: name>`                         | Posts an embed in chat with the given details provided in the config file. The tag name is *not* case sensitive                                                                                                                                                                              |
| `warn <apply;resolve;undo;view> <user>`        | _mod only:_ Performs the specified action to the defined user. Actions can be `apply` to give a user another warning, `resolve` remove the oldest warning for that user, `undo` to remove the newest warning for that user, and `view` to display the amount of warnings given to that user. |
| `role <add;remove;list> <optional: role_name>` | Performs the specified action with the role (when provided) to the calling user. Actions can be `add` to add a specified role to yourself, `remove` to remove the specified role from yourself, and `list` to list all the available roles that can be added/removed with the command.       |
| `accept`                                       | When called from a config-set channel, assigns a config-set role to the requesting user and deletes their message from the chat.                                                                                                                                                             |
| `gimme`                                        | When the cookie hunt game is enabled and a cookie is dropped, claims the cookie and adds a point to the user.                                                                                                                                                                                |
| `sugar <optional: high>`                       | Lists the number of cookies that the asking user has. If the option `high` is appended, lists the high scores of cookie collectors.                                                                                                                                                          |
| `forcedrop`                                    | _mod only:_ Forces the bot to drop a cookie immediately and resets the drop randomizer.                                                                                                                                                                                                      |
| `roll <dice>`                                  | Calculates a role with the specified dice syntax. Exact syntax will be documented below.                                                                                                                                                                                                     |
| `r <dice>`                                     | An alias for the `roll` command.                                                                                                                                                                                                                                                             |

Additionally, Manageable also has these additional features:

| Feature           | Description                                                                                                                                         |
|:------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------|
| Daily Prompts     | Pulls the daily prompt from [r/SketchDaily](https://reddit.com/r/sketchdaily) and announces it in a specified channel.                              |
| Feature Disabling | Any feature or command can be selectively disabled in the config if the functionality is not needed.                                                |
| Cookie Hunt       | Drops a cookie in a randomly selected channel for claiming with the `gimme` command at a random interval. Play for high scores and bragging rights! |

## Setup

##### 1) Install Python
First, make sure that you have Python 3.4 or above installed. This code was tested on Python 3.9, however, and it is recommended you use that version if possible. Python can be downloaded [here](https://www.python.org/).

##### 2) Install Package Requirements
Once you have confirmed that Python is installed correctly, install the necessary python packages by running `pip install -r requirements.txt`. This will install all necessary python requirements to your system for Manageable to run.

##### 3) Set Up the Bot Account
After that, you'll need to configure Manageable to run on your server. Go to the [Discord Developer Portal](https://discordapp.com/developers/applications/) and follow [these instructions](https://discordpy.readthedocs.io/en/latest/discord.html) to create a bot account and add it to your server. Take note of the bot's token, as you'll need it later.

_**Permissions:**_

Manageable will need these permissions to run. Omitting any of these permissions may cause the bot to not function correctly.

| Requirement     | Reason                                                                          |
|:----------------|:--------------------------------------------------------------------------------|
| Manage Roles    | The bot needs to be able to manage roles to add and remove roles from users.    |
| View Channels   | The bot needs to be able to see the channels so it can watch them for commands. |
| Send Messages   | The bot needs to be able to send server message and DMs to respond to commands. |
| Manage Messages | The bot needs to be able to delete messages for the `accept` command            |
| Embed Links     | The bot needs to be able to embed links to display some commands correctly.     |
| Add Reactions   | The bot uses reactions to control pagination of its help command.               |

_**Intents:**_ 

On top of the above permissions,the following privileged intents are required for the bot to function:

* `Server Members`: Manageable needs to view the full list of members to work (such as monitoring reacts on the help message, assigning cookies, and applying warnings).
* `Message Content`: Manageable uses a customizable command prefix (set in the `command_prefix` entry in the config file) to trigger its command system. This intent is required to allow the bot to trigger the prefix properly.

Please make sure these Privileged Intents are enabled on the Discord Developer Dashboard.

##### 4) Configure the Bot Functionality
Open `config.json`, located in the `Config` folder. Paste in the bot's token you received from discord in the `token` line, and configure any other information desired. Documentation for the configuration file is found in a later section.

##### 5) Run the Bot
In the root directory of Manageable, execute `manageable.py`. If everything is set up correctly, you should see the bot appear online in the server you've invited it to.

## Other Documentation

### Config.json
This is the main json configuration file for Manageable, and contains all the basic, configurable parameters to tweak the bot's functionality. Below is a description of each parameter.

* `/token`: A string token given by Discord after configuring your bot with their developer portal. Be sure not to share this token with anyone.
* `/command_prefix`: A string prefix to address the bot so that it knows a command is being run.
* `/mod_roles`: A string list of all the role names (case-sensitive) that you'd like to be able to execute Manageable's moderator-only commands.
* `/help_commands_per_page`: An integer denoting how many commands you'd like the help command to display per page.
* `/warning_duration_days`: An integer denoting how many days you'd like warnings to persist before removal. Setting this value to zero means warnings will never decay.
* `/verbose_logging`: A boolean value indicating whether to allow more verbose logging in the debug.log file. This does not impact console logging.
* `/content/features`: A dictionary of commands matched with a boolean on whether the feature is enabled (true) or disabled (false). Do not remove items from this unless you know what you are doing.
* `/content/tags`: A dictionary of tags, where the tag name is the key, and the value is a dictionary, configured by the following values:
    * `color`: _(optional)_ A hexadecimal value in the format `#000000`, denoting the color of the tag's embed.
    * `title`: _(required)_ A string value denoting the title of the embed. The discord command is *not* case-sensitive, so be careful of tags with the same name.
    * `url`: _(optional)_ A valid URL to which the embed will create a clickable link.
    * `description`: _(optional)_ A string denoting the description text of the discord embed
* `/content/role_whitelist`: A list of strings representing all the role names (below the bot's role on the guild) that the bot can add or remove from users that request them.
* `/content/airlock_channel`: The string name of the guild channel that the bot will watch the `accept` command for.
* `/content/airlock_release_role`: The string name of the guild role (which must be below the bot's role) that will be assigned to the user when calling the `accept` command.
* `/content/cookie_hunt_hour_variance`: A two-item list of integers, with the first item being the minimum amount of hours to wait before dropping a cookie for the cookie hunt, and the second item being the maximum amount of hours to wait before dropping a cookie. 
* `/content/cookie_hunt_allowed_channels`: A list of all the text channel names that the bot can randomly select to drop a cookie into for the cookie hunt.  
* `/content/cookie_hunt_goal`: A positive integer goal for the certain number of cookies any user needs to collect to wih the game and reset the points for everyone.
* `/content/cookie_hunt_winner_role`: The string name of the guild role (which must be below the bot's role) that will be assigned to the winner of the cookie hunt game. **Please note** that when a new winner is assigned, all other guild users with this role will lose it.
* `/content/dice_result_embed_color`: A hexadecimal value in the format `#000000`, denoting the color of the dice result's embed.

### Dice Roller Syntax

The dice rolling feature tries to maintain a relatively expected and standard mathematical syntax. All steps, along with the result, will be outputted to discord. The following operations are supported:

* `xdy`: Rolls a `y`-sided die `x` times, returning an integer.
  * If `x` is negative, the roll will be evaluated like `-(xdy)`.
  * If `y` is negative, the die will be simulated from `y` to `-1`.
  * If `x` or `y` are not integers, they will be raised to the nearest integer (using a `ceiling` function, which will be denoted in the outputted steps)
  * If `x` or `y` is `0`, the die roll will be 0.
* `x+y`: Adds `y` to `x`.
* `x-y`: Subtracts `y` from `x`.
* `x*y`: Multiplies `x` by `y`.
* `x/y`: Divides `x` by `y`.
* `(x)`: Prioritizes the calculation `x` within the parentheses.

The order of operations is as follows (any equivalent operations are done left-to-right):

1. `d`
2. `()`
3. `*`,`/`
4. `+`,`-`