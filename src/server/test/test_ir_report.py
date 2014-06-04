#!/usr/bin/python2.7
"""
Author:
    Jialiang Xie
Date:
    2014-1-2
"""

from test_base import TestBase

class TestIRReport(TestBase):
    """
    Test IR Report. Executed by Nose.
    """

    def test_create_new_report(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        summary_text = 'Firefox crashed'
        description_text = 'When I was openning history folder, the f**king' \
                ' Firefox just crashed!'
        report = IRReport(summary_text, description_text)
        assert summary_text == report.get_summary_text()
        assert description_text == report.get_description_text()
        report.get_summary_and_description_tfidf()
        report.get_summary_and_description_tfidf_squared_length()
        IRLog.get_instance().stop_log()

    def test_create_new_report_from_string(self):
        from nose.tools import eq_
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport
        from ir_term_count import IRTermCount

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        summary_text = 'Firefox crashed'
        description_text = 'When I was openning history folder, the f**king' \
                ' Firefox just crashed!\n'
        report = IRReport(summary_text, description_text)
        report.set_basic_info(12345, 'core')
        report.set_penalty_terms(IRTermCount.do_stemming(['ie', 'explore']))
        report.set_exclude_report_ids([100100])
        report.set_dummy_bug_id(12345)
        report.set_skip_terms(IRTermCount.do_stemming(['new','please']))
        # save to text
        text = report.to_string()
        IRLog.get_instance().println('Serialized report: %s' % (text))
        # load from text
        new_report = IRReport.from_string(text)

        assert new_report.get_summary_text() == report.get_summary_text()
        eq_(new_report.get_description_text().strip(), report.get_description_text().strip())
        assert new_report.get_create_ts() == report.get_create_ts()
        assert new_report.get_product() == report.get_product()
        assert new_report.get_dummy_bug_id() == report.get_dummy_bug_id()
        assert new_report.get_penalty_terms() == report.get_penalty_terms()
        assert new_report.get_exclude_report_ids() == report.get_exclude_report_ids()
        eq_(new_report.get_skip_terms(), report.get_skip_terms())
        IRLog.get_instance().stop_log()

    def test_top_n_similarity_over_all(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        report = IRReport(100000)
        bugs_similarities = report.top_n_similarity_over_all(10)
        IRLog.get_instance().println('Bugs with top similarities with bug %d: %s' \
                % (100000, str(bugs_similarities)))
        IRLog.get_instance().stop_log()

    def test_similarity_with(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRConfig.get_instance().set('tfidf_algorithm', 'tfidf')
        report_a = IRReport(100000)
        report_b = IRReport(100200)
        IRLog.get_instance().println('TFIDF similarity between %d and %d is %f' % \
                (100000, 100200, report_a.similarity_with(report_b)[0]))
        
        IRConfig.get_instance().set('tfidf_algorithm', 'bidf')
        report_a = IRReport(100000)
        report_b = IRReport(100200)
        IRLog.get_instance().println('Bidf similarity between %d and %d is %f' % \
                (100000, 100200, report_a.similarity_with(report_b)[0]))

        IRConfig.get_instance().set('scoring_strategy', 'weighted')
        IRConfig.get_instance().set('bug_summary_ratio', 0.25)
        IRConfig.get_instance().set('bug_description_ratio', 0.25)
        IRConfig.get_instance().set('bug_stacktrace_ratio', 0.5)
        IRLog.get_instance().println('Bidf (Weighted Scoring) similarity '
                                     'between '
                                     '%d and %d '
                                     'is %f' % \
                (100000, 100200, report_a.similarity_with(report_b)[0]))

        IRConfig.get_instance().set('scoring_strategy', 'heuristic')
        IRConfig.get_instance().set('bug_summary_ratio', 0.5)
        IRConfig.get_instance().set('bug_description_ratio', 0.5)
        IRLog.get_instance().println('Bidf (Heuristic Scoring) similarity '
                                     'between '
                                     '%d and %d '
                                     'is %f' % \
                (100000, 100200, report_a.similarity_with(report_b)[0]))

        IRConfig.get_instance().set('scoring_strategy', 'distweighted')
        IRConfig.get_instance().set('bug_summary_ratio', 0.5)
        IRConfig.get_instance().set('bug_description_ratio', 0.5)
        IRLog.get_instance().println('Bidf (Heuristic Scoring) similarity '
                                     'between '
                                     '%d and %d '
                                     'is %f' % \
                (100000, 100200, report_a.similarity_with(report_b)[0]))

    def test_binary_search_less(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        report = IRReport('','')
        array1 = range(10,0,-1)
        assert 8 == report.binary_search_less(array1, lambda x:x, 3)
        assert 0 == report.binary_search_less(array1, lambda x:x, 11)
        assert 10 == report.binary_search_less(array1, lambda x:x, 1)
        array2 = []
        assert -1 == report.binary_search_less(array2, lambda x:x, 1)

    def test_similarities_and_duplicates(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        report = IRReport(100000)
        similarities, duplicates = report.similarities_and_duplicates()
        IRLog.get_instance().println('Report %d' % (100000))
        IRLog.get_instance().println('%d Similar Reports: %s' % (similarities
               .__len__(), ','.join([str(item[0]) for item in similarities])))
        IRLog.get_instance().println('%d Duplicate Reports: %s' % (duplicates
               .__len__(), ','.join([str(item[0]) for item in duplicates])))
        IRLog.get_instance().stop_log()
