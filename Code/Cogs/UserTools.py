from enum import Enum
from discord.ext import commands
from discord import Role, Embed
from Code.Cogs.Base import ConfiguredCog
from typing import Union


class RequestAction(Enum):
    """An enumeration class containing all the possible role request actions that can be taken."""

    ADD = 'add'  # add a role to the user
    REMOVE = 'remove'  # remove a role from the user
    LIST = 'list'  # list all the possible roles


class RoleRequestCog(ConfiguredCog):
    """A Cog class meant to add and remove roles from users that request them."""

    @commands.command()
    async def role(self, ctx: commands.Context, action: str, *target_role_list: str):
        """The origin point for the `role` command.

        :param ctx:                 The command context.
        :param action:              The string action to execute. Should correlate to an action in the `RequestAction`
                                    enumeration.
        :param target_role_list:    A list of strings, denoting the desired role to perform the action (or ignored,
                                    depending on the action). This list will be joined by spaces.
        """

        role_query = ' '.join(target_role_list)
        action = action.lower()

        if ctx.guild is None:
            message = 'This command must be used from a guild. Please go to the guild you wish to use the command on' \
                      'and try again.'
        else:
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

    def _validate_role_against_whitelist(self, role: Role) -> bool:
        """Validates that the given role is in the config whitelist for allowed role interactions.

        :param role:    The role to validate against the whitelist configuration

        :return:    True if the case-sensitive role name is listed in the config, False otherwise.
        """
        # Check the whitelist to make sure we are allowed to add this role
        if role.name not in self.config["content"]["role_whitelist"]:
            return False
        return True


class TagCog(ConfiguredCog):
    """A class supporting the `tag` command functionality."""

    @commands.command()
    async def tag(self, ctx: commands.Context, tag_name: Union[str, None] = None):
        """The origin point for the `tag` command.

        :param ctx:         The command context.
        :param tag_name:    The key string of the tag to query the config for.
        """

        if tag_name is not None:
            tag_data = None
            for tag in ConfiguredCog.config['content']['tags']:
                # Check the tag, agnostic of case.
                if tag.lower() == tag_name.lower():
                    tag_name = tag
                    tag_data = ConfiguredCog.config['content']['tags'][tag_name]
                    break

            # Throw an error since we didn't find a tag
            if tag_data is None:
                await ctx.send(f'The tag `{tag_name}` was not found.')
                return

            # Build tag data
            color = ConfiguredCog.convert_color(self._get_tag_data_safe(tag_data, 'color'))

            title = self._get_tag_data_safe(tag_data, 'title')
            if title is None:
                # Tag title isn't set, but is required, set it to the tag name
                title = tag_name

            url = self._get_tag_data_safe(tag_data, 'url')
            description = self._get_tag_data_safe(tag_data, 'description')

            # Send embed
            message = Embed(color=color, title=title, url=url, description=description)
        else:
            # Send list of tags
            message = Embed(title='Available Tags',
                            description='Please do `tag <tag_name>` to display the tag contents.')
            for tag_name in ConfiguredCog.config['content']['tags'].keys():
                title = self._get_tag_data_safe(ConfiguredCog.config['content']['tags'][tag_name], 'title')
                if title is None:
                    # Tag title isn't set, but is required, set it to the tag name
                    title = tag_name

                message.add_field(name=tag_name, value=title)

        await ctx.send(embed=message)

    @staticmethod
    def _get_tag_data_safe(tag_data: dict[str, str], tag_name: str) -> Union[str, None]:
        """Looks up the tag name from a dictionary of tag data and fail safely if it can't be found.

        :param tag_data:    A dictionary of tags and their data, where the keys are strings referencing the tag's name,
                            and the values are dictionaries denoting the data to build the tag.
        :param tag_name:    The key to query in the provided data.

        :return:    If the tag name is found in the data's keys, return the corresponding dictionary value. If the
                    tag's name was not found in the data's keys, return `None`.
        """

        try:
            return tag_data[tag_name]
        except KeyError:
            return None
