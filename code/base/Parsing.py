# pylint: skip-file
"""A Module for constructing and parsing the dice rolling language."""
from sly import Lexer, Parser
from random import randint
from typing import Tuple
from math import ceil


class DiceLexer(Lexer):
    tokens = {NUMBER, PLUS, MINUS, TIMES, DIVIDE, LEFT_PARENTHESES, RIGHT_PARENTHESES, DIE_ROLL}
    ignore = ' \t'

    # Tokens
    NUMBER = r'\d+'

    # Special symbols
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    LEFT_PARENTHESES = r'\('
    RIGHT_PARENTHESES = r'\)'
    DIE_ROLL = r'd'

    # Ignored pattern
    ignore_newline = r'\n+'

    # Extra action for newlines
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        self.index += 1


class DiceParser(Parser):
    tokens = DiceLexer.tokens

    precedence = (
        ('left', PLUS, MINUS),
        ('left', TIMES, DIVIDE),
        ('right', UNARY_MINUS),
        ('left', DIE_ROLL)
    )

    def __init__(self):

        # Used to log all steps for later output
        self.step_log: list = []

    @_('expr')
    def statement(self, p) -> Tuple[list, float]:
        """Exit point of the expression when everything else is evaluated.

        :return:    A tuple with a list of the steps and the final value.
        """

        return_data = (self.step_log, float(p.expr))
        self.step_log = []  # reset the step log so we don't store the steps between rolls

        return return_data

    @_('expr DIE_ROLL expr')
    def expr(self, p):
        number_of_dice = ceil(p.expr0)
        die_max_value = ceil(p.expr1)

        # log if the ceiling actually impacted the numbers
        if isinstance(p.expr0, float) and not p.expr0.is_integer():
            self.step_log.append(f'ceil({p.expr0})={number_of_dice}')
        if isinstance(p.expr1, float) and not p.expr1.is_integer():
            self.step_log.append(f'ceil({p.expr1})={die_max_value}')

        if number_of_dice < 0:
            # mathematical results (like (2-3)d4) don't get parsed like
            # hard-coded negatives (like -1d4), so we need to manually handle it
            invert_result = True
            number_of_dice = abs(number_of_dice)
        else:
            invert_result = False

        roll_total = 0
        die_values = []
        die_min_value = 1
        for _ in range(number_of_dice):
            if die_max_value > 0:
                # roll between 1 and max value
                die_value = randint(die_min_value, die_max_value)
            elif die_max_value < 0:
                # roll between max value, and -1
                die_min_value = -1
                die_value = randint(die_max_value, die_min_value)
            else:
                # tf is a d0? just spit back zero.
                die_value = 0

            die_values.append(die_value)
            roll_total += die_value

        step_string = f'{number_of_dice}d{die_max_value}={roll_total}('
        crit_success_count = 0
        crit_fail_count = 0
        for die_value in die_values:
            step_string += f'🎲'
            if die_value == die_max_value:
                crit_success_count += 1
            elif die_value == die_min_value:
                crit_fail_count += 1
            step_string += f'{die_value} '

        step_string = step_string[:-1] + ')'  # remove trailing space and add a closing parentheses
        # Uncomment to output crit successes and failures (makes things way more cluttered though)
        # step_string += f'\nCRIT SUCCESS: {crit_success_count}, CRIT FAIL: {crit_fail_count}'0
        self.step_log.append(step_string)

        # Invert the result if needed (we process this as though we ran through the UNARY_MINUS process for clarity.)
        if invert_result:
            step_string = f'-({roll_total})={-roll_total}'
            roll_total = -roll_total
            self.step_log.append(step_string)

        return roll_total

    @_('expr PLUS expr')
    def expr(self, p):
        result = p.expr0 + p.expr1
        self.step_log.append(f'{p.expr0}+{p.expr1}={result}')
        return result

    @_('expr MINUS expr')
    def expr(self, p):
        result = p.expr0 - p.expr1
        self.step_log.append(f'{p.expr0}-{p.expr1}={result}')
        return result

    @_('expr TIMES expr')
    def expr(self, p):
        result = p.expr0 * p.expr1
        self.step_log.append(f'{p.expr0}*{p.expr1}={result}')
        return result

    @_('expr DIVIDE expr')
    def expr(self, p):
        result = p.expr0 / p.expr1
        self.step_log.append(f'{p.expr0}/{p.expr1}={result}')
        return result

    @_('MINUS expr %prec UNARY_MINUS')
    def expr(self, p):
        result = -p.expr
        self.step_log.append(f'-({p.expr})={result}')
        return result

    @_('LEFT_PARENTHESES expr RIGHT_PARENTHESES')
    def expr(self, p):
        return p.expr

    @_('NUMBER')
    def expr(self, p):
        return int(p.NUMBER)
