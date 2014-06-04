"""
Author:
    Jialiang Xie
Date:
    2014-1-2
"""

from test_base import TestBase

class TestIRDocumentCount(TestBase):
    """
    Test IR Document Count. Executed by Nose.
    """

    def test_generate_document_count(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_document_count import IRDocumentCount

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')

        IRDocumentCount.batch_generate_document_count()
        IRLog.get_instance().stop_log()
      
    def test_cache_all_data(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_document_count import IRDocumentCount

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRDocumentCount.cache_all_data()

    def test_get_documentcount(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_document_count import IRDocumentCount

        IRLog.get_instance().start_log()
        summary, description = IRDocumentCount.get_documentcount('click')
        IRLog.get_instance().println('\'click\', Document Count of summary: %d, description: %d' % (summary, description))

        assert summary == IRDocumentCount.get_documentcount(
            'click', IRConfig.get_instance().get('bug_summary_name'))
        assert description == IRDocumentCount.get_documentcount(
            'click', IRConfig.get_instance().get('bug_description_name'))
    

        
