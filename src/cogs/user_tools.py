"""A module containing tools that a discord user might need."""
from enum import Enum
from typing import Union

from src.cogs.base import ConfiguredCog

from discord.ext import commands
from discord import Role, Embed


class RequestAction(Enum):
    """An enumeration class containing all the possible role request actions
    that can be taken."""

    ADD = 'add'  # add a role to the user
    REMOVE = 'remove'  # remove a role from the user
    LIST = 'list'  # list all the possible roles


class RoleRequestCog(ConfiguredCog):
    """A Cog class meant to add and remove roles from users that request
    them."""

    config_name = 'role'

    @commands.command()
    async def role(self,
                   ctx: commands.Context,
                   action: str,
                   *target_role_list: str):
        """The origin point for the `role` command.

        :param ctx:                 The command context.
        :param action:              The string action to execute. Should
                                    correlate to an action in the
                                    `RequestAction` enumeration.
        :param target_role_list:    A list of strings, denoting the desired
                                    role to perform the action (or ignored,
                                    depending on the action). This list will
                                    be joined by spaces.
        """

        role_query = ' '.join(target_role_list)
        action = action.lower()

        if ctx.guild is None:
            message = ('This command must be used from a guild. Please go to '
                       'the guild you wish to use the command on '
                       'and try again.')
            await ctx.send(message)
            return

        if action == RequestAction.ADD.value:
            message = await self._add_role(ctx, role_query)
        elif action == RequestAction.REMOVE.value:
            message = await self._remove_role(ctx, role_query)
        elif action == RequestAction.LIST.value:
            message = self._build_role_list_message(ctx)
        else:
            message = (f'Unknown role command `{action}`, please re-enter '
                       f'your command and try again.')

        await ctx.send(message)

    async def _add_role(self, ctx: commands.Context, role_query: str) -> str:
        """Adds the role requested to the user, if possible.

        :param ctx:         The command context.
        :param role_query:  The role query the user inputted.

        :return:    The resulting message to send back to the user.
        """
        # find role
        role = self.find_role_in_guild(role_query, ctx.guild)
        if not role:
            return (f'No role by the name of `{role_query}` exists in this '
                    f'guild. Please check your spelling and try again.')

        # make sure it's allowed to be manipulated
        if not self._validate_role_against_whitelist(role):
            return 'You are not allowed to interact with this role.'

        if self.member_contains_role(role.name, ctx.author):
            return 'You already have that role.'

        # add role to user
        reason = 'Role added via Manageable bot instance.'
        await ctx.author.add_roles(role, reason=reason)
        return f'You now have the `{role.name}` role.'

    async def _remove_role(self,
                           ctx: commands.Context,
                           role_query: str) -> str:
        """Removes the role requested from the user, if possible.

        :param ctx:         The command context.
        :param role_query:  The role query the user inputted.
        :return:    The resulting message to send back to the user.
        """
        # find role
        role = self.find_role_in_guild(role_query, ctx.guild)
        if not role:
            return (f'No role by the name of `{role_query}` exists in this '
                    f'guild. Please check your spelling and try again.')

        # make sure it's allowed to be manipulated
        if not self._validate_role_against_whitelist(role):
            return 'You are not allowed to interact with this role.'

        if not self.member_contains_role(role.name, ctx.author):
            return 'You do not have that role.'

        # remove role from user
        reason = 'Role removed via Manageable bot instance.'
        await ctx.author.remove_roles(role, reason=reason)
        return f'You no longer have the `{role.name}` role.'

    def _build_role_list_message(self, ctx: commands.Context) -> str:
        """ Builds a human-readable list of all the roles available to
        manipulate with the `role` command.

        :param ctx: The command context.
        :return:    A human-readable message listing the roles available.
        """
        message = '__**Available roles to add/remove:**__'
        for role_name in self.config['content']['role_whitelist']:
            if self.find_role_in_guild(role_name, ctx.guild):
                message += f'\n{role_name}'

        return message

    def _validate_role_against_whitelist(self, role: Role) -> bool:
        """Validates that the given role is in the config whitelist for allowed
        role interactions.

        :param role:    The role to validate against the whitelist
                        configuration.

        :return:    True if the case-sensitive role name is listed in the
                    config, False otherwise.
        """
        # Check the whitelist to make sure we are allowed to add this role
        if role.name not in self.config["content"]["role_whitelist"]:
            return False
        return True


class TagCog(ConfiguredCog):
    """A class supporting the `tag` command functionality."""

    config_name = 'tag'

    @commands.command()
    async def tag(self,
                  ctx: commands.Context,
                  tag_name: Union[str, None] = None):
        """The origin point for the `tag` command.

        :param ctx:         The command context.
        :param tag_name:    The key string of the tag to query the config for.
        """

        if tag_name is not None:
            tag_data = None
            tag_list = ConfiguredCog.config['content']['tags']
            for tag in tag_list:
                # Check the tag, agnostic of case.
                if tag.lower() == tag_name.lower():
                    tag_name = tag
                    tag_data = tag_list[tag_name]
                    break

            # Throw an error since we didn't find a tag
            if tag_data is None:
                await ctx.send(f'The tag `{tag_name}` was not found.')
                return

            # Build tag data
            tag_color = self._get_tag_data_safe(tag_data, 'color')
            color = ConfiguredCog.convert_color(tag_color)

            title = self._get_tag_data_safe(tag_data, 'title')
            if title is None:
                # Tag title isn't set, but is required, set it to the tag name
                title = tag_name

            url = self._get_tag_data_safe(tag_data, 'url')
            description = self._get_tag_data_safe(tag_data, 'description')

            # Send embed
            message = Embed(color=color,
                            title=title,
                            url=url,
                            description=description)
        else:
            # Send list of tags
            description = ('Please do `tag <tag_name>` '
                           'to display the tag contents.')
            message = Embed(title='Available Tags',
                            description=description)
            tag_list = ConfiguredCog.config['content']['tags']
            for tag_id in tag_list.keys():
                title = self._get_tag_data_safe(tag_list[tag_id], 'title')
                if title is None:
                    # Tag title isn't set, but is required,
                    # so set it to the tag name
                    title = tag_id

                message.add_field(name=tag_id, value=title)

        await ctx.send(embed=message)

    @staticmethod
    def _get_tag_data_safe(tag_data: dict[str, str],
                           tag_name: str) -> Union[str, None]:
        """Looks up the tag name from a dictionary of tag data and fail safely
        if it can't be found.

        :param tag_data:    A dictionary of tags and their data, where the keys
                            are strings referencing the tag's name,
                            and the values are dictionaries denoting the data
                            to build the tag.
        :param tag_name:    The key to query in the provided data.

        :return:    If the tag name is found in the data's keys, return the
                    corresponding dictionary value. If the tag's name was not
                    found in the data's keys, return `None`.
        """

        try:
            return tag_data[tag_name]
        except KeyError:
            return None
