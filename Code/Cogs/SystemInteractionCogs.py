import sys
import traceback
from discord.ext import commands
from Code.Cogs.Base import ConfiguredCog


class UserInteractionCog(ConfiguredCog):
    """A Cog class meant to passively watch for events on the server.

    Methods
    -------
    on_command_error    Watches for uncaught errors and handles them appropriately.
    """

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, exception: commands.errors):
        """Watches for uncaught errors and outputs the error to the console, as normal, while also emitting a more
           user-friendly message to the discord server.

        Inspired by https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612

        Parameters
        ----------
        ctx:        discord.ext.commands.Context    The context of the server messages.
        exception:  discord.ext.commands.errors     The exception that was passed up the chain.
        """

        # Verify that a local handler hasn't already interfaced with the error
        if hasattr(ctx.command, 'on_error'):
            command = ctx.command
            self.logger.debug(f'Ignoring exception in command {command}, as another module has already handled it.')
            return

        if isinstance(exception, (commands.MissingRole, commands.MissingAnyRole)) or \
           isinstance(exception, commands.CommandNotFound):
            exception_type = type(exception)
            self.logger.warning(f'Passing exception of type {exception_type} to public users.')
            return await ctx.send(str(exception))

        # Output the default exception to the console since it wasn't handled elsewhere
        command = ctx.command
        self.logger.error(f'Skipping exception in command {command}.')
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)
        return await ctx.send('An internal error occurred while processing your command.')
