"""A module for tools intended for general server management."""
from enum import Enum
from datetime import datetime, timedelta

from src.cogs.base import ConfiguredCog
from src.data import data_access

from discord import Member
from discord.ext import commands


class WarnAction(Enum):
    """An enumeration class containing all the possible warning actions that
    can be taken."""

    APPLY = 'apply'  # create a warning for a user
    RESOLVE = 'resolve'  # remove the oldest warning
    UNDO = 'undo'  # remove the newest warning
    VIEW = 'view'  # display warning count


class UserWarnCog(ConfiguredCog):
    """A class supporting the warning functionality."""

    config_name = 'warn'

    @commands.command()
    @commands.has_any_role(*ConfiguredCog.config['mod_roles'])
    async def warn(self,
                   ctx: commands.Context,
                   action: str, *user_name_list: str):
        """The origin point for the `warn` command.

        :param ctx:             The command context.
        :param action:          The string action to execute. Should correlate
                                to an action in the `WarnAction` enumeration.
        :param user_name_list:  A list of strings, denoting either a user's
                                nickname, or their discord ID. This list will
                                be joined by spaces and compared against the
                                server's member list, first by trying to
                                convert it to an integer and searching by
                                unique ID, then by querying the list of
                                nicknames by the joined string.
        """

        # join all the arguments after the action together,
        # in case we are looking for a display name that has a space
        user_name_query = ' '.join(user_name_list)
        action = action.lower()

        # Finds all the members that match the query
        # (either a discord ID or a display name)
        member_matches = self._find_discord_member(user_name_query)

        if not member_matches:
            await ctx.send(f'No user by the name or id of `{user_name_query}` '
                           f'could be found. Please check your spelling and '
                           f'try again.')

        elif len(member_matches) > 1:
            await ctx.send(self._multi_member_found_message(user_name_query,
                                                            member_matches))

        else:
            target_member = member_matches[0]

            # remove outdated warnings for the found user
            self._remove_outdated_warnings(target_member)

            if action == WarnAction.APPLY.value:
                warning_count = self._warn_member(target_member)
                message = (f'The user "{user_name_query}" has now been '
                           f'warned, for a total of {warning_count} times.')
            elif action in (WarnAction.RESOLVE.value, WarnAction.UNDO.value):
                warning_count = self._remove_warning(target_member, action)
                message = (f'The user "{user_name_query}" has now '
                           f'been unwarned, they now have {warning_count} '
                           f'warnings.')
            elif action == WarnAction.VIEW.value:
                warning_count = self._view_user_warnings(target_member)
                message = (f'The user "{user_name_query}" has {warning_count} '
                           f'warnings.')
            else:
                message = (f'Unknown warning command `{action}`, '
                           f'please re-enter your command and try again.')

            await ctx.send(message)

    def _remove_outdated_warnings(self, target_member: Member):
        """Queries the database for warnings pertaining to the specified member
        and deletes ones that are outdated.

        :param target_member:   The member to look for when removing outdated
                                warnings.
        """

        warning_duration = self.config['warning_duration_days']

        if warning_duration <= 0:
            # If duration set in the config is zero or less,
            # we assume warnings are permanent.
            return

        member_id = target_member.id
        user_warnings = data_access.lookup_warnings_by_discord_id(member_id)

        for warning in user_warnings:
            warning_max_date = (datetime.now() -
                                timedelta(days=warning_duration))
            if (warning is not None and
                    warning_max_date > warning.Warning_Stamp):
                data_access.delete_warning(warning.Warning_Id)

    @staticmethod
    def _warn_member(target_member: Member) -> int:
        """Saves a new warning in the database for the member specified.

        Please note that this method will add a member row to the database if
        it cannot find one, before continuing onwards to add a warning to that
        member.

        :param target_member:   The member to add a warning to.

        :return:    The number of total warnings assigned to the member.
        """

        target_id = target_member.id
        user_warnings = data_access.lookup_warnings_by_discord_id(target_id)
        warning_count = user_warnings.count()

        # Find the user in the db so that we can attach a warning to it
        # (should add a user if none found)
        db_user_id = data_access.find_user_id_by_discord_id(target_member.id)

        # Add the new warning
        data_access.add_warning(db_user_id)
        warning_count += 1

        return warning_count

    @staticmethod
    def _remove_warning(target_member: Member, action: str) -> int:
        """Deletes a warning in the database for the member specified.

        :param target_member:   The member to add a warning to.
        :param action:          The action to perform. MUST be either
                                `WarnAction.RESOLVE` or `WarnAction.UNDO`.

        :return:    The number of total warnings assigned to the member.

        :except ValueError: When the action argument is not a valid string.
        """

        target_id = target_member.id
        user_warnings = data_access.lookup_warnings_by_discord_id(target_id)
        warning_count = user_warnings.count()

        if warning_count == 0:
            # no warnings, so nothing to remove.
            return warning_count

        if action == WarnAction.RESOLVE.value:
            # Remove the oldest index
            delete_newest = False
        elif action == WarnAction.UNDO.value:
            # Remove the newest index
            delete_newest = True
        else:
            raise ValueError('The action argument must be a valid removal '
                             'WarnAction.')

        data_access.delete_warning_by_discord_id(target_member.id,
                                                delete_newest)
        warning_count -= 1

        return warning_count

    @staticmethod
    def _view_user_warnings(target_member: Member) -> int:
        """Finds the number of warnings in the database for the member
        specified.

        :param target_member:   The member to add a warning to.

        :return:    The number of total warnings assigned to the member.
        """

        target_id = target_member.id
        warning_rows = data_access.lookup_warnings_by_discord_id(target_id)

        if warning_rows.first() is None:
            count = 0
        else:
            count = warning_rows.count()

        return count

    def _find_discord_member(self, user_query: str) -> list:
        """Finds the discord information for the users matching the provided
        query.

        This method will attempt to convert the query into an integer and grab
        the user via the id first. If that fails, it will take the raw string
        provided and attempt to find all users with the matching nickname. In
        the event that it finds more than member that matches the query, it
        will return all of them.

        :param user_query:  The query to search for, either an integer discord
                            ID or a member nickname.

        :return:    A list of `discord.Member` instances, each one relating to
                    a member that matched the query, or an empty list, if no
                    matches were found.
        """
        member_matches = []

        # try to lookup by ID first, as it'll be faster
        try:
            member_matches.append(self.bot.get_user(int(user_query)))
        except ValueError:
            # couldn't cast the user to an integer,
            # so ignore that type of error.
            pass

        # couldn't find by ID, attempt to look up by display name
        if not member_matches:
            member_matches = []
            for member in self.bot.get_all_members():
                member_already_in_match_list = False
                if (member.display_name.upper() == user_query.upper() or
                        (member.nick is not None and
                         member.nick.upper() == user_query.upper()) or
                        member.name.upper() == user_query.upper()):
                    # Only add a member if the ID (which is unique to a discord
                    # user) isn't already in the list
                    for member_match in member_matches:
                        if member.id == member_match.id:
                            member_already_in_match_list = True
                            break
                    if not member_already_in_match_list:
                        member_matches.append(member)

        return member_matches

    @staticmethod
    def _multi_member_found_message(user_search_query: str,
                                    member_matches: list) -> str:
        """Builds a message listing out all members found with the user search
        query provided.

        :param user_search_query:   The search query that was used to find all
                                    the members listed.
        :param member_matches:      A list of `discord.Member` instances, each
                                    relating to a member that matched the
                                    search query.

        :return:    A user-friendly error message reporting all the matches
                    found with the given error message.
        """

        multiple_found_message = (f'Multiple users by the identifier '
                                  f'"{user_search_query}" were found. '
                                  f'Displaying as\n *<display name>* '
                                  f'(*<account name>*), **id:** *<id>*:\n\n')

        for member in member_matches:
            uid = member.id
            name = member.name
            display_name = member.display_name
            name_message = f'- {display_name} ({name}), **id:** {uid}\n'
            multiple_found_message += name_message

        multiple_found_message += ('\nPlease try again, using the unique id '
                                   'for the user you wish to warn.')

        return multiple_found_message
