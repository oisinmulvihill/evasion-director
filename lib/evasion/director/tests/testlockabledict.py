import unittest

from evasion.director import lockabledict


class LockableDictionaryTestCase(unittest.TestCase):

    def setUp(self):
        self.dict = lockabledict.LockableDict()
        
    def tearDown(self):
        self.dict = None
        
    def testSimpleOperations(self):
        """Tests to see if basic operations work.

        """
        self.dict['a_key'] = 'a_data'
        self.dict['b_key'] = 'b_data'

        assert self.dict['a_key'] == 'a_data'
        assert self.dict['b_key'] == 'b_data'

        del self.dict['a_key']

        def t():
            self.dict['a_key']
        
        self.assertRaises(KeyError, t)

        
if __name__ == "__main__":
    unittest.main(defaultTest="suite")

