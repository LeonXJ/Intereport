#!/usr/bin/python2.7
"""
Author:
    Jialiang Xie
Date:
    2014-3-4
"""

from test_base import TestBase

class TestIRRecommender(TestBase):
    """
    Test IR Recommender. Executed by Nose.
    """

    def test_get_report_difference(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport
        from ir_recommender import IRRecommender

        IRConfig.get_instance().load('../data/test/bug_test.cfg')

        new_report = IRReport('apple for summary', 'linux description')
        sim_report = IRReport('apple of ghost crashed', 'description linux wow')

        (diff_sum, diff_desc) = \
                IRRecommender.get_report_difference(new_report, sim_report)
        IRLog.get_instance().println('New summary: %s' \
                % (new_report.get_summary_text()))
        IRLog.get_instance().println('Sim summary: %s' \
                % (sim_report.get_summary_text()))
        IRLog.get_instance().println('New description: %s' \
                % (new_report.get_description_text()))
        IRLog.get_instance().println('Sim description: %s' \
                % (sim_report.get_description_text()))
        IRLog.get_instance().println('Diff of summary: %s' % (diff_sum))
        IRLog.get_instance().println('Diff of description: %s' % (diff_desc))
        assert diff_sum == {'ghost', 'crash'}
        assert diff_desc == {'wow'}

    def test_get_report_differences(self):

        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport
        from ir_recommender import IRRecommender

        IRConfig.get_instance().load('../data/test/bug_test.cfg')

        new_report = IRReport('apple for summary', 'linux description')
        sim_reports = [
            IRReport('apple of ghost crashed', 'description linux wow'),
            IRReport(100000),
            IRReport(100200) ]

        diffs = \
                IRRecommender.get_all_reports_difference(new_report, sim_reports)
        for diff in diffs:
            IRLog.get_instance().println('Diff of summary: %s' % (diff[0]))
            IRLog.get_instance().println('Diff of description: %s' % (diff[1]))

    def test_get_term_by_simple_entropy(self):

        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport
        from ir_recommender import IRRecommender

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        diff = [(set([]), {'a', 'b', 'c', 'd'}),
                (set([]), {'a', 'b', 'c'}),
                (set([]), {'a', 'b'}),
                (set([]), {'a'})]
        #assert 'c' == IRRecommender.get_term_by_simple_entropy(diff)
