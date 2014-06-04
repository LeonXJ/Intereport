"""
Author:
    Jialiang Xie
Date:
    2014-1-9
"""

from test_base import TestBase

class TestIRDebugger(TestBase):
    """
    Test IR Debugger. Executed by Nose.
    """

    def test_compare(self):
        from ir_config import IRConfig
        from ir_debugger import IRDebugger

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRDebugger.compare(100000, 100200)

