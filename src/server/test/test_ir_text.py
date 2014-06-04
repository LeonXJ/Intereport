#!/usr/bin/python2.7
"""
Author:
    Jialiang Xie
Date:
    2013-12-30
"""

from test_base import TestBase

class TestIRText(TestBase):
    """
    Test IR Text. Executed by Nose.
    """
    
    def test_cache_all_data(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_text import IRText
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRText.cache_all_data()

    def test_get_summary_and_description_of_bug(self):

        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_text import IRText
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        summary, description = IRText.get_summary_and_description_of_bug(100000)
        IRLog.get_instance().println('summary: %s' % (summary))
        IRLog.get_instance().println('description: %s' % (description))

    def test_get_stacktrace_text_of_bug(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_text import IRText
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        stacktrace_text = IRText.get_stacktrace_text_of_bug(104400)
        IRLog.get_instance().println('stacktrace_text: %s' % (stacktrace_text))

    def test_parse_info_level1(self):
        #import sys
        #sys.path.append('../bin/')
        from ir_log import IRLog
        from ir_text import IRText
        from ir_config import IRConfig
        from ir_mongodb_helper import IRMongodbHelper

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        assert None != IRConfig.get_instance()
        IRText.parse_info_level1('../data/test/info_level1_test')
        IRLog.get_instance().stop_log()

        con = IRMongodbHelper.get_instance().get_connection()
        db = con[IRConfig.get_instance().get('bug_db_name')]
        assert None != db
        col = db[IRConfig.get_instance().get('bug_text_collection_name')]
        assert None != col
        # in the test data, we have 1000 in total.
        # within, 40 have no resolution, 154 are incomplete
        assert 833 == col.count()
        assert 'gnome is full of bugs ! (100000 currently)' == \
                col.find({'bug_id':100000})[0]["summ"]
        
        res = col.find({"summ":{'$regex':'(&gt)|(&lt)|(&quot)|(&apo)s|(&amp)'}})
        assert res.count() == 0
        
    def test_parse_dump_file(self):
        from ir_log import IRLog
        from ir_text import IRText
        from ir_config import IRConfig
        from ir_mongodb_helper import IRMongodbHelper

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        assert None != IRConfig.get_instance()
        IRText.parse_dump_file('../data/test/dump_file_test')
        IRLog.get_instance().stop_log()

        con = IRMongodbHelper.get_instance().get_connection()
        db = con[IRConfig.get_instance().get('bug_db_name')]
        assert None != db
        col = db[IRConfig.get_instance().get('bug_text_collection_name')]
        assert None != col

        assert 1000 == col.count()

#if __name__ == '__main__':
#
#    test = TestIRText()
#    test.setUp()
#    test.test_parse_info_level1()
