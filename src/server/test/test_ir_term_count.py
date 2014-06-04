#!/usr/bin/python2.7
"""
Author:
    Jialiang Xie
Date:
    2013-12-30
"""

from test_base import TestBase

class TestIRTermCount(TestBase):
    """
    Test IR TermCount. Executed by Nose.
    """

    def test_single_report_term_count(self):
        #import sys
        #sys.path.append('../bin/')
        from ir_config import IRConfig
        from ir_term_count import IRTermCount

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        summary = 'This is a test of calculation for single report term count.'
        description = 'This is the description of the test report. Just a test.'
        summary_BoW, description_BoW = \
                IRTermCount.calculate_term_count(summary, description)
        assert summary_BoW['calcul'] == 1
        assert description_BoW['test'] == 2
        
    def test_get_termcount_of_bug(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_term_count import IRTermCount

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        summary, description = IRTermCount.get_termcount_of_bug(100000)
        assert None != summary
        assert None != description
        IRLog.get_instance().println('Summary')
        IRTermCount.show_dict_compare(summary, {})
        IRLog.get_instance().println('Description')
        IRTermCount.show_dict_compare(description, {})

    def test_batch_report_term_count(self):
        from ir_config import IRConfig
        from ir_mongodb_helper import IRMongodbHelper
        from ir_term_count import IRTermCount

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRTermCount.batch_generate_term_count()
        # simple size test
        con = IRMongodbHelper.get_instance().get_connection()
        db = con[IRConfig.get_instance().get('bug_db_name')]
        text_collection = db[IRConfig.get_instance().\
                get('bug_text_collection_name')]
        termcount_collection = db[IRConfig.get_instance().\
                get('bug_termcount_collection_name')]
        assert text_collection.count() == termcount_collection.count()

    def test_cache_all(self):
        from ir_config import IRConfig
        from ir_term_count import IRTermCount

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRTermCount.cache_all_data()

    def test_create_incomplete_report(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_term_count import IRTermCount

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        summary = 'This is a test of calculation for single report term count.'
        description = 'This is the description of the test report. Just a test.'
        summary_BoW, description_BoW = \
                IRTermCount.calculate_term_count(summary, description)
        inc_summary, inc_description = \
                IRTermCount.create_incomplete_report(summary, description, 0.4)
        inc_summary_bow, inc_description_bow = \
                IRTermCount.calculate_term_count(inc_summary, inc_description)
        IRLog.get_instance().println('Original Summary: %s' % (summary))
        IRLog.get_instance().println('Original Description: %s' % (description))
        IRLog.get_instance().println('Incomplete Summary: %s' % (inc_summary))
        IRLog.get_instance().println('Incomplete Description: %s' % (inc_description))
        IRLog.get_instance().println('Compare original BoW with incomplete BoW')
        IRLog.get_instance().println('%16s\t%8s\t%8s' % ('Summary', 'Ori', 'Inc'))
        IRTermCount.show_dict_compare(summary_BoW, inc_summary_bow)
        IRLog.get_instance().println('%16s\t%8s\t%8s' % ('Description', 'Ori', 'Inc'))
        IRTermCount.show_dict_compare(description_BoW, inc_description_bow)

    def test_tokenization(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_term_count import IRTermCount
        from nose.tools import assert_equals

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        tests = ['mouse-down', 'set_background_color()']
        expects = [['mouse-down'], ['set_background_color']]
        for index, test in enumerate(tests):
            assert_equals(expects[index], IRTermCount.do_tokenization(test))

    def test_stemming(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_term_count import IRTermCount

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        tests = ['discrimination', 'disgusting', 'visualization', 'configuration']
        stemmers = ['porter', 'lancaster', 'snowball']
        for test in tests:
            out = []
            for stemmer in stemmers:
                IRConfig.get_instance().set('stemmer', stemmer)
                out_token = IRTermCount.do_stemming([test])
                out.append(':'.join([stemmer, out_token[0]]))
            IRLog.get_instance().println('%s > %s' % (test, ', '.join(out)))
