#!/usr/bin/python2.7
"""
Author:
    Jialiang Xie
Date:
    2013-12-30
"""

from test_base import TestBase

class TestIRSimBugEvaluator(TestBase):
    """
    Test IR Sim Bug Evaluator. Executed by Nose.
    """

    def test_generate_and_test_incomplete_test_file(self):
        from ir_config import IRConfig
        from ir_sim_bug_evaluator import IRSimBugEvaluator

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        evl = IRSimBugEvaluator()
        evl.generate_test_file('incomplete_test_file', 0.6)
        evl.do_test_over_file('incomplete_test_file')


    def test_generate_and_test_complete_test_file(self):
        from ir_config import IRConfig
        from ir_sim_bug_evaluator import IRSimBugEvaluator

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        evl = IRSimBugEvaluator()
        evl.generate_test_file('complete_test_file', 0.0)
        evl.do_test_over_file('complete_test_file')
