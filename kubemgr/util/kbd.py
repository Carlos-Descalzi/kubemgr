keystroke = lambda x: sum( [i * (100 ** n) for n, i in enumerate(reversed(x))])
keystroke_from_str = lambda x: keystroke(list(map(ord,x)))

KEY_UP = keystroke([27, 91, 65])
KEY_DOWN = keystroke([27, 91, 66])
KEY_RIGHT = keystroke([27, 91, 67])
KEY_LEFT = keystroke([27, 91, 68])
KEY_PGUP = keystroke([27, 91, 53])
KEY_PGDN = keystroke([27, 91, 54])
KEY_HOME = keystroke([27, 91, 72])

KEY_ESC = 27
KEY_TAB = 9
KEY_ENTER = 13
