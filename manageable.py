from discord.ext.commands.bot import Bot
from Cogs.ConfiguredCog import ConfiguredCog
from Cogs.SystemInteractionCogs import UserInteractionCog
from Cogs.MessagingCog import SendMessageCog
from Cogs.ModToolsCog import DisciplineCog


if __name__ == '__main__':
    # Build the bot
    print('Constructing Manageable bot...')
    discord_bot = Bot(ConfiguredCog.config['command_prefix'])
    discord_bot.remove_command('help')  # We are providing our own help command

    # Add the necessary cogs
    print('Attaching functionality...')
    discord_bot.add_cog(UserInteractionCog(discord_bot))
    discord_bot.add_cog(SendMessageCog(discord_bot))
    discord_bot.add_cog(DisciplineCog(discord_bot))

    # Run the bot
    print('Launching Manageable with the specified bot token.')
    discord_bot.run(ConfiguredCog.config['token'])
