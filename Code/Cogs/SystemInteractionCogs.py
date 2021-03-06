from enum import Enum
import traceback
from discord.ext import commands
from discord import Role, Guild, Member, Message
from typing import Optional
from Code.Cogs.Base import ConfiguredCog


class RequestAction(Enum):
    """An enumeration class containing all the possible role request actions that can be taken."""

    ADD = 'add'  # add a role to the user
    REMOVE = 'remove'  # remove a role from the user
    LIST = 'list'  # list all the possible roles


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
        self.logger.error(f'Skipping exception in command {command}: {exception}')
        self.logger.info(traceback.format_exc())
        return await ctx.send('An internal error occurred while processing your command.')


class RoleRequestCog(ConfiguredCog):
    """A Cog class meant to add and remove roles from users that request them.

    Methods
    -------
    role                    The origin point for the `role` command.
    find_role_in_guild      Searches for the name of a role in the bot's guild.
    member_contains_role    Checks to see if a given member has a certain role or not.
    """

    @commands.command()
    async def role(self, ctx: commands.Context, action: str, *target_role_list: str):
        """The origin point for the `role` command.

        Parameters
        ----------
        ctx:                discord.ext.commands.Context    The command context.
        action:             str                             The string action to execute. Should correlate to an action
                                                            in the `RequestAction` enumeration.
        target_role_list:   List[str]                       A list of strings, denoting the desired role to perform the
                                                            action (or ignored, depending on the action). This list will
                                                            be joined by spaces.
        """

        role_query = ' '.join(target_role_list)
        action = action.lower()

        if action == RequestAction.ADD.value:
            # find role
            role = self.find_role_in_guild(role_query, ctx.guild)
            if not role:
                await ctx.send(f'No role by the name of `{role_query}` exists in this guild. '
                               f'Please check your spelling and try again.')
                return

            # make sure it's allowed to be manipulated
            if not self._validate_role_against_whitelist(role):
                await ctx.send("You are not allowed to interact with this role.")
                return

            # add role to user
            if self.member_contains_role(role.name, ctx.author):
                message = f'You already have that role.'
            else:
                await ctx.author.add_roles(role, reason='Role added via Manageable bot instance.')
                message = f'You now have the `{role.name}` role.'
        elif action == RequestAction.REMOVE.value:
            # find role
            role = self.find_role_in_guild(role_query, ctx.guild)
            if not role:
                await ctx.send(f'No role by the name of `{role_query}` exists in this guild. '
                               f'Please check your spelling and try again.')
                return

            # make sure it's allowed to be manipulated
            if not self._validate_role_against_whitelist(role):
                await ctx.send("You are not allowed to interact with this role.")
                return

            # remove role from user
            if self.member_contains_role(role.name, ctx.author):
                await ctx.author.remove_roles(role, reason='Role removed via Manageable bot instance.')
                message = f'You no longer have the `{role.name}` role.'
            else:
                message = f'You do not have that role.'
        elif action == RequestAction.LIST.value:
            # list all available roles
            message = "__**Available roles to add/remove:**__"
            for role_name in self.config["content"]["role_whitelist"]:
                if self.find_role_in_guild(role_name, ctx.guild):
                    message += f"\n{role_name}"
        else:
            message = f'Unknown role command `{action}`, please re-enter your command and try again.'

        await ctx.send(message)

    @staticmethod
    def find_role_in_guild(role_name_query: str, guild: Guild) -> Optional[Role]:
        """Finds a role with the provided name in a guild.

        Notes
        -----
        Please note that this will find the first (lowest) role with the provided name. Be careful if the guild has
        multiple roles with the same role name. Also keep in mind that the role search IS case sensitive.

        Parameters
        ----------
        role_name_query:    str             The name of the role to search the guild for
        guild:              discord.Guild   The guild to validate the role name against

        Returns
        -------
        Optional[Role]  Returns the role in the class, or None if no role exists in the guild
        """
        for role in guild.roles:
            if role.name == role_name_query:
                # found the role with the provided name
                return role

        # didn't find the role
        return None

    def _validate_role_against_whitelist(self, role: Role) -> bool:
        """Validates that the given role is in the config whitelist for allowed role interactions

        Parameters
        ----------
        role:   discord.Role    The role to validate against the whitelist configuration

        Returns
        -------
        bool    True if the case-sensitive role name is listed in the config, False otherwise.
        """
        # Check the whitelist to make sure we are allowed to add this role
        if role.name not in self.config["content"]["role_whitelist"]:
            return False
        return True

    @staticmethod
    def member_contains_role(role_name_query: str, member: Member) -> bool:
        """Validates that the provided member has a role with the given name.

        Parameters
        ----------
        role_name_query:    str             The name of the role to search the guild for
        member:             discord.Member  The guild to validate the role name against

        Returns
        -------
        bool    Returns True if the member contains the role, or False otherwise
        """
        for role in member.roles:
            if role.name == role_name_query:
                # found the role with the provided name
                return True

        # didn't find the role
        return False


class AirlockCog(ConfiguredCog):
    """A class supporting the airlock functionality (including the `accept` command)

    Methods
    -------
    accept
    """

    @commands.command()
    async def accept(self, ctx: commands.context):
        """The origin point for the accept command

        Parameters
        ----------
        ctx:    discord.ext.commands.context    The command context.
        """

        # Check to make sure the command comes from a predefined channel.
        # If it doesn't, the command fails silently.
        airlock_channel_name = ConfiguredCog.config['content']['airlock_channel']
        if ctx.guild is None or ctx.channel.name != airlock_channel_name:
            self.logger.debug(f"Airlock release command was attempted to be called from an invalid location.")
            await ctx.send(f'This command can only be accessed from the #{airlock_channel_name} channel.')
            return

        # Give the message sender a predefined role
        role_name = ConfiguredCog.config['content']['airlock_release_role']
        role = RoleRequestCog.find_role_in_guild(role_name, ctx.guild)
        if not role:
            self.logger.error(f"Encountered an issue attempting to resolve the airlock role specified in the config.")
            await ctx.send(f"There was an issue finding the role to give to the sender.")
            return

        if RoleRequestCog.member_contains_role(role.name, ctx.author):
            self.logger.warning(f'{ctx.author.name} requested an airlock release when they already had the role.')
            await ctx.send('You already have the airlock release role.')
            return
        else:
            self.logger.debug(f'Released {ctx.author.name} from the airlock.')
            await ctx.author.add_roles(role, reason='User requested release from the airlock channel.')

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """Watches for any messages sent in the airlock channel, and deletes them after five seconds.

           Parameters
           ----------
           message:     discord.Message     The message that was sent in a place that the bot can see
           """
        airlock_channel_name = ConfiguredCog.config['content']['airlock_channel']
        airlock_channel_delete_delay = 5.0  # delay in seconds

        if message.guild is not None and message.channel.name == airlock_channel_name:
            # delete any messages coming into the airlock channel
            self.logger.debug('Deleting a message in the airlock channel.')
            await message.delete(delay=airlock_channel_delete_delay)
