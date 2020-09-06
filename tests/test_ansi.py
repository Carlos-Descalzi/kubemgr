from unittest import TestCase
from kubemgr.util import ansi


class TestAnsi(TestCase):

    def test_len(self):
        self.assertEqual(5,len(ansi.begin().reverse().write('hello').reset()))
        self.assertEqual(5,len(ansi.begin().bold().reverse().write('hello').reset()))
        self.assertEqual(5,len(ansi.begin().clrscr().reverse().write('hello').reset()))
        self.assertEqual(0,len(ansi.begin().reverse().write('').reset()))
