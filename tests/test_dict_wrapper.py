from unittest import TestCase
from kubemgr.views.format import DictWrapper
class DictWrapperTestCase(TestCase):

    def test_wrap(self):
        data = {
            'a' : 1
        }

        wrapper = DictWrapper(data)

        self.assertEqual(1,wrapper.a)

        wrapper = DictWrapper({
            'a' : {
                'b' : 1
            }
        })

        self.assertEqual(1,wrapper.a.b)
