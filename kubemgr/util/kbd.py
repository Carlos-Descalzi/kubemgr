make_keystroke = lambda x: sum(
    [i * (100 ** ((len(x) - 1) - n)) for n, i in enumerate(x)]
)

KEY_UP = make_keystroke([27, 91, 65])
KEY_DOWN = make_keystroke([27, 91, 66])
KEY_RIGHT = make_keystroke([27, 91, 67])
KEY_LEFT = make_keystroke([27, 91, 68])
KEY_PGUP = make_keystroke([27, 91, 53])
KEY_PGDN = make_keystroke([27, 91, 54])
KEY_HOME = make_keystroke([27, 91, 72])

KEY_ESC = 27
KEY_TAB = 9
KEY_ENTER = 13
