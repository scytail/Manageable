import json
from enum import Enum
from discord.ext import commands
from Cogs.ConfiguredCog import ConfiguredCog


class Action(Enum):
    INCREASE = 'increase'
    DECREASE = 'decrease'
    VIEW = 'view'


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
            if action == Action.INCREASE.value:
                warning_count = self._warn_member(member_matches, action)
                message = f'The user "{user_name_query}" has now been warned, for a total of {warning_count} times.'
            elif action == Action.DECREASE.value:
                warning_count = self._warn_member(member_matches, action)
                message = f'The user "{user_name_query}" has now been unwarned, for a total of {warning_count} times.'
            elif action == Action.VIEW.value:
                warning_count = self._warn_member(member_matches, action)
                message = f'The user "{user_name_query}" has {warning_count} warnings.'
            else:
                message = f'Unknown warning command `{action}`, please re-enter your command and try again.'

            await ctx.send(message)

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
    def _warn_member(member_matches: list, action: str) -> int:
        with open('Data/userwarn.json', 'r') as user_warnings_file:
            user_warnings = json.load(user_warnings_file)

        # Create an entry if one doesn't exist
        json_member_id = str(member_matches[0].id)
        if json_member_id in user_warnings:
            warning_count = user_warnings[json_member_id]['warning_count']
        else:
            warning_count = 0
            user_warnings[json_member_id] = {}

        # Modify the warning count
        if action == Action.INCREASE.value:
            warning_count += 1
        elif action == Action.DECREASE.value:
            warning_count -= 1
            if warning_count < 0:
                warning_count = 0
        elif action == Action.VIEW:
            return warning_count

        user_warnings[json_member_id]['warning_count'] = warning_count

        # dump everything to the file
        with open('Data/userwarn.json', 'w') as user_warnings_file:
            json.dump(user_warnings, user_warnings_file)

        return warning_count
