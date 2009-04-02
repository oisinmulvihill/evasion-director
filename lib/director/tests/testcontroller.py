"""
"""
import pprint
import unittest
import StringIO

import director


testcfg = StringIO.StringIO("""
[director] 
somevalue = 123
""")

testfilecfg = StringIO.StringIO(testcfg)


class DirectorTC(unittest.TestCase):    

        
    def testRequiredConfigSection(self):
        """Test that the evasion section is present in the given config file.
        """
        # Check that no setup done is caught:
        self.assertRaises(director.config.ConfigNotSetup, director.config.get_cfg)

        # Check we don't get and problems with files...
        testcfg = StringIO.StringIO("""
[director] 
somevalue = 123
""")
        director.config.set_cfg(testcfg)
        director.config.get_cfg()

        # Reset now check no '[director]' section is caught:
        director.config.clear()
        testcfg = StringIO.StringIO("""
[no section] 
somevalue = 123

[director] 
# Not valid, I look for director
abc = 321

""")
        self.assertRaises(director.config.ConfigInvalid, director.config.set_cfg, testcfg)

        
    def testdirectorConfig(self):
        """Test the configuration set and machinery
        """
        # Check that no setup done is caught:
        self.assertRaises(director.config.ConfigNotSetup, director.config.get_cfg)

        # Check we don't get and problems with files...
        director.config.set_cfg(testcfg)
        director.config.get_cfg()

        # Reset and Check were ok with dicts
        director.config.clear()
        director.config.set_cfg(dict(director={'somevalue':123}))

        # Reset and Check we don't get and problems:
        director.config.clear()
        self.assertRaises(director.config.ConfigNotSetup, director.config.get_cfg)
        director.config.c = ""
        director.config.c
        
