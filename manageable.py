from discord.ext.commands.bot import Bot
import Code.Cogs.Base as Base
from Code.Cogs.ModToolsCogs import UserWarnCog
from Code.Cogs.MessagingCogs import HelpCog, TagCog
from Code.Cogs.SystemInteractionCogs import UserInteractionCog


if __name__ == '__main__':
    # Build the bot
    Base.ConfiguredCog.logger.info('Constructing Manageable bot...')
    Base.ConfiguredCog.logger.debug(f'Building bot.')
    discord_bot = Bot(Base.ConfiguredCog.config['command_prefix'])

    Base.ConfiguredCog.logger.debug('Removing help command.')
    discord_bot.remove_command('help')  # We are providing our own help command

    # Add the necessary cogs
    Base.ConfiguredCog.logger.info('Attaching functionality...')
    Base.ConfiguredCog.logger.debug('Adding UserInteraction Cog.')
    discord_bot.add_cog(UserInteractionCog(discord_bot))

    Base.ConfiguredCog.logger.debug('Adding Help Cog.')
    discord_bot.add_cog(HelpCog(discord_bot))

    Base.ConfiguredCog.logger.debug('Adding Tag Cog.')
    discord_bot.add_cog(TagCog(discord_bot))

    Base.ConfiguredCog.logger.debug('Adding UserWarn Cog.')
    discord_bot.add_cog(UserWarnCog(discord_bot))

    # Run the bot
    Base.ConfiguredCog.logger.warning('Launching Manageable with the specified bot token.')
    discord_bot.run(Base.ConfiguredCog.config['token'])
