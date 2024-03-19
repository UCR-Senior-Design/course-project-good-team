# test_runner.py
import unittest
from button_tests import ButtonTests 
from database_tests import DataBaseTests
from pagetitle_tests import PageTitleTests

class TestSuite(unittest.TestSuite):
    def run(self, result, debug=False):
        super(TestSuite, self).run(result, debug=debug)
        # You can capture and aggregate results here

if __name__ == '__main__':
    suite = unittest.TestSuite()

    # Add tests to test suite
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ButtonTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(DataBaseTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PageTitleTests))

    # Run the test suite
    unittest.TextTestRunner().run(suite)