import json
from enum import Enum
from discord.ext import commands
from Cogs.ConfiguredCog import ConfiguredCog
from datetime import datetime


class Action(Enum):
    APPLY = 'apply'  # create a warning for a user
    RESOLVE = 'resolve'  # remove oldest warning
    UNDO = 'undo'  # remove newest warning
    VIEW = 'view'  # display warning count


class DisciplineCog(ConfiguredCog):
    @commands.command()
    @commands.has_any_role(*ConfiguredCog.config['mod_roles'])
    async def warn(self, ctx: commands.context, action: str, *user_name_list: str):
        user_name_query = ' '.join(user_name_list)
        action = action.lower()

        member_matches = self._lookup_member(user_name_query)

        if not member_matches:
            await ctx.send(f'No user by the name or id of `{user_name_query}` could be found. '
                           f'Please check your spelling and try again.')

        elif len(member_matches) > 1:
            await ctx.send(self._multi_member_found_message(user_name_query, member_matches))

        else:
            self._remove_outdated_warnings()

            if action == Action.APPLY.value:
                warning_count = self._warn_member(member_matches)
                message = f'The user "{user_name_query}" has now been warned, for a total of {warning_count} times.'
            elif action == Action.RESOLVE.value or \
                    action == Action.UNDO.value:
                warning_count = self._remove_warning(member_matches, action)
                message = f'The user "{user_name_query}" has now been unwarned, for a total of {warning_count} times.'
            elif action == Action.VIEW.value:
                warning_count = self._view_user_warnings(member_matches)
                message = f'The user "{user_name_query}" has {warning_count} warnings.'
            else:
                message = f'Unknown warning command `{action}`, please re-enter your command and try again.'

            await ctx.send(message)

    def _warn_member(self, member_matches: list) -> int:
        user_warnings = self._load_warning_data()

        json_member_id = str(member_matches[0].id)
        if json_member_id in user_warnings:
            warning_count = len(user_warnings[json_member_id])
        else:
            # Create an entry if one doesn't exist so we can add the warning
            warning_count = 1
            user_warnings[json_member_id] = []

        '''
        userwarnings.json
        {
        'json_member_id' : [
        {'timestamp': <datetime>}
        ]
        }
        '''
        user_warnings[json_member_id].append({'timestamp': datetime.now()})

        # dump everything to the file
        with open('Data/userwarn.json', 'w') as user_warnings_file:
            json.dump(user_warnings, user_warnings_file)

        return warning_count

    def _remove_warning(self, member_matches: list, action: str) -> int:
        user_warnings = self._load_warning_data()

        json_member_id = str(member_matches[0].id)
        if json_member_id in user_warnings:
            warning_count = len(user_warnings[json_member_id]) - 1
        else:
            # No member found, therefore no warnings
            return 0

        oldest_warning = (-1, datetime.now())
        newest_warning = (-1, datetime.min)
        for warning_index in range(len(user_warnings[json_member_id])):
            warning_datetime = user_warnings[json_member_id]['timestamp']

            if warning_datetime < oldest_warning[1]:
                oldest_warning = (warning_index, warning_datetime)
            if warning_datetime > newest_warning[1]:
                newest_warning = (warning_index, warning_datetime)

        if action == Action.RESOLVE.value:
            # Remove the oldest index
            user_warnings[json_member_id].pop(oldest_warning[0])
        elif action == Action.UNDO.value:
            # Remove the newest index
            user_warnings[json_member_id].pop(newest_warning[0])

        # dump everything to the file
        with open('Data/userwarn.json', 'w') as user_warnings_file:
            json.dump(user_warnings, user_warnings_file)

        return warning_count

    def _view_user_warnings(self, member_matches: list) -> int:
        user_warnings = self._load_warning_data()

        json_member_id = str(member_matches[0].id)
        if json_member_id in user_warnings:
            return len(user_warnings[json_member_id])
        else:
            # No member found, therefore no warnings
            return 0

    def _remove_outdated_warnings(self):
        # remove outdated warnings based on a config option
        raise NotImplementedError

    def _lookup_member(self, user: str) -> list:
        member_matches = []

        # try to lookup by ID first, as it'll be faster
        try:
            member_matches.append(self.bot.get_user(int(user)))
        except ValueError:
            # couldn't cast the user to an integer, so ignore that type of error.
            pass

        # couldn't find by ID, attempt to look up by display name
        if not member_matches:
            member_matches = []
            for member in self.bot.get_all_members():
                if member.display_name.upper() == user.upper() or \
                        (member.nick is not None and member.nick.upper() == user.upper()) or \
                        member.name.upper() == user.upper():
                    member_matches.append(member)

        return member_matches

    @staticmethod
    def _multi_member_found_message(user_search_query: str, member_matches: list) -> str:
        multiple_found_message = f'Multiple users by the identifier "{user_search_query}" were found. Displaying as\n'
        multiple_found_message += f'*<display name>* (*<account name>*), **id:** *<id>*:\n\n'

        for member in member_matches:
            uid = member.id
            name = member.name
            display_name = member.display_name
            multiple_found_message += f'- {display_name} ({name}), **id:** {uid}\n'

        multiple_found_message += f'\nPlease try again, using the unique id for the user you wish to warn.'

        return multiple_found_message

    @staticmethod
    def _load_warning_data() -> dict:
        with open('Data/userwarn.json', 'r') as user_warnings_file:
            user_warnings = json.load(user_warnings_file)

        return user_warnings
