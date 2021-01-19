from discord.ext.commands.bot import Bot
from discord import Intents
import Code.Cogs.Base as Base
from Code.Cogs.ModToolsCogs import UserWarnCog
from Code.Cogs.MessagingCogs import HelpCog, TagCog
from Code.Cogs.SystemInteractionCogs import UserInteractionCog, RoleRequestCog, AirlockCog


if __name__ == '__main__':
    # Build the bot
    Base.ConfiguredCog.logger.info('Constructing Manageable bot...')
    Base.ConfiguredCog.logger.debug(f'Building bot.')

    intents = Intents.default()
    # We need the member intent for the warn command
    require_member_intent = Base.is_cog_enabled('warn', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'UserWarn Cog check resulted in: {require_member_intent} (for privileged intent).')
    if require_member_intent:
        intents.members = True

    discord_bot = Bot(Base.ConfiguredCog.config['command_prefix'], intents=intents)

    Base.ConfiguredCog.logger.debug('Removing built-in help command.')
    discord_bot.remove_command('help')  # We are providing our own help command

    # Add the necessary cogs
    Base.ConfiguredCog.logger.info('Attaching functionality...')

    # Do not disable
    Base.ConfiguredCog.logger.debug('Adding UserInteraction Cog.')
    discord_bot.add_cog(UserInteractionCog(discord_bot))

    # Do not disable
    Base.ConfiguredCog.logger.debug('Adding Help Cog.')
    discord_bot.add_cog(HelpCog(discord_bot))

    enable_cog = Base.is_cog_enabled('tag', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'Tag Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding Tag Cog.')
        discord_bot.add_cog(TagCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping Tag Cog.')

    enable_cog = Base.is_cog_enabled('warn', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'UserWarn Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding UserWarn Cog.')
        discord_bot.add_cog(UserWarnCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping UserWarn Cog.')

    enable_cog = Base.is_cog_enabled('role', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'RoleRequest Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding RoleRequest Cog.')
        discord_bot.add_cog(RoleRequestCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping RoleRequest Cog.')

    enable_cog = Base.is_cog_enabled('airlock', Base.ConfiguredCog.config)
    Base.ConfiguredCog.logger.debug(f'Airlock Cog check resulted in: {enable_cog}.')
    if enable_cog or enable_cog is None:
        Base.ConfiguredCog.logger.debug('Adding Airlock Cog.')
        discord_bot.add_cog(AirlockCog(discord_bot))
    else:
        Base.ConfiguredCog.logger.debug('Skipping Airlock Cog.')

    # Run the bot
    Base.ConfiguredCog.logger.warning('Launching Manageable with the specified bot token.')
    discord_bot.run(Base.ConfiguredCog.config['token'])
