#!/usr/bin/python2.7
"""
Author:
    Jialiang Xie
Date:
    2014-1-2
"""

from test_base import TestBase

class TestIRTFIDF(TestBase):
    """
    Test IR TFIDF. Executed by Nose.
    """

    def test_cache_all_data(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRTFIDF.cache_all_data()
        IRLog.get_instance().stop_log()


    def test_batch_generate_tfidf(self):
        #import sys
        #sys.path.append('../bin/')
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRTFIDF.batch_generate_tfidf()
        IRLog.get_instance().stop_log()

    def test_calcualte_tfidf_for_report_termcount_tfidf(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        
        summary = {'firefox':5, 'chrome':12}
        description = {'max':10, 'min':30, 'fix':10}
        summary_tfidf, description_tfidf = \
            IRTFIDF.calculate_tfidf_for_report_termcount(summary, description)
        summary_sum = 0.0
        for term, tfidf in summary_tfidf.items():
            summary_sum += tfidf ** 2 
        description_sum = 0.0
        for term, tfidf in description_tfidf.items():
            description_sum += tfidf ** 2
        # print summary_sum, description_sum
        assert (summary_sum - 1.0) ** 2 < 0.00001
        assert (description_sum - 1.0) ** 2 < 0.00001

    def test_calculate_tfidf_for_report_termcount_bidf(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRConfig.get_instance().set('tfidf_algorithm', 'bidf')
        summary = {'firefox':5, 'chrome':12}
        description = {'max':10, 'min':30, 'fix':10}
        summary_tfidf, description_tfidf = \
            IRTFIDF.calculate_tfidf_for_report_termcount(summary, description)
        IRLog.get_instance().println('Summary')
        IRTFIDF.show_dict_compare(summary_tfidf, summary_tfidf)
        IRLog.get_instance().println('Description')
        IRTFIDF.show_dict_compare(description_tfidf, description_tfidf)
        IRLog.get_instance().stop_log()

    def test_get_tfidf_of_bug(self):
        #import sys
        #sys.path.append('../bin/')
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        summary, description = IRTFIDF.get_tfidf_of_bug(100000)
        IRLog.get_instance().println('Summary tfidf: %s' % (str(summary)))
        IRLog.get_instance().println('Description tfidf: %s' % (str(description)))
        IRLog.get_instance().stop_log()

    def test_show_dict_compare(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        
        summary_a, description_a = IRTFIDF.get_tfidf_of_bug(100000)
        summary_b, description_b = IRTFIDF.get_tfidf_of_bug(100200)
        IRLog.get_instance().println('Summary 100000 vs 100200')
        IRTFIDF.show_dict_compare(summary_a, summary_b, summary_name)
        IRLog.get_instance().println('Description 100000 vs 100200')
        IRTFIDF.show_dict_compare(description_a, description_b)
        IRLog.get_instance().println('Summary 100000 vs 100000')
        IRTFIDF.show_dict_compare(summary_a, summary_a)
        IRLog.get_instance().println('Description 100000 vs 100000')
        IRTFIDF.show_dict_compare(description_a, description_a, description_name)

    def test_tfidf_asm_similarity(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF
        
        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        
        vec_a = {'firefox':1, 'chrome':1}
        vec_b = {'firefox':1, 'chrome':1, 'ie':1}
        vec_c = {'firefox':1, 'windows':1, 'linux':1}

        delta = 0.0001
        assert abs(1.0 - IRTFIDF.tfidf_asm_similarity(vec_a, vec_b)) < delta
        assert abs(0.5 - IRTFIDF.tfidf_asm_similarity(vec_a, vec_c)) < delta
        assert IRTFIDF.tfidf_asm_similarity(vec_a, vec_b) > \
                IRTFIDF.tfidf_asm_similarity(vec_a, vec_b, None, ['ie'], 100)

    def test_get_squared_length(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        summary = {'firefox':0.4, 'chrome':0.6}
        assert abs(IRTFIDF.get_squared_length(summary) - 0.52 ) < 0.00001
