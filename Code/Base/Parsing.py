from sly import Lexer, Parser
from random import randint


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
        print(f'Illegal character "{t.value[0]}"')
        self.index += 1


class DiceParser(Parser):
    tokens = DiceLexer.tokens

    precedence = (
        ('left', PLUS, MINUS),
        ('left', TIMES, DIVIDE),
        ('right', UNARY_MINUS),
        ('left', DIE_ROLL)
    )

    @_('expr')
    def statement(self, p):
        """Exit point of the expression when everything else is evaluated."""
        return(p.expr)

    @_('expr DIE_ROLL expr')
    def expr(self, p):
        number_of_dice = p.expr0
        die_max_value = p.expr1

        if number_of_dice < 0:
            # mathematical results (like (2-3)d4) don't get parsed like
            # hard-coded negatives (like -1d4), so we need to manually handle it
            invert_result = True
            number_of_dice = abs(number_of_dice)
        else:
            invert_result = False

        roll_total = 0
        for i in range(number_of_dice):
            if die_max_value > 0:
                # roll between 1 and max value
                roll_total += randint(1, die_max_value)
            elif die_max_value < 0:
                # roll between max value, and -1
                roll_total += randint(die_max_value, -1)
            else:
                # tf is a d0? just spit back zero.
                roll_total += 0

        if invert_result:
            return -roll_total
        else:
            return roll_total

    @_('expr PLUS expr')
    def expr(self, p):
        return p.expr0 + p.expr1

    @_('expr MINUS expr')
    def expr(self, p):
        return p.expr0 - p.expr1

    @_('expr TIMES expr')
    def expr(self, p):
        return p.expr0 * p.expr1

    @_('expr DIVIDE expr')
    def expr(self, p):
        return p.expr0 / p.expr1

    @_('MINUS expr %prec UNARY_MINUS')
    def expr(self, p):
        return -p.expr

    @_('LEFT_PARENTHESES expr RIGHT_PARENTHESES')
    def expr(self, p):
        return p.expr

    @_('NUMBER')
    def expr(self, p):
        return int(p.NUMBER)
