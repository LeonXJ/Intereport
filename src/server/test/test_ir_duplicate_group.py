#!/usr/bin/python2.7
"""
Author:
    Jialiang Xie
Date:
    2014-1-2
"""

from test_base import TestBase

class TestIRDuplicateGroup(TestBase):
    """
    Test IR Duplicate Group. Executed by Nose.
    """

    def test_parse_info_level0(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        from ir_duplicate_group import IRDuplicateGroup

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        duplicate_group = IRDuplicateGroup()
        duplicate_group.parse_info_level0('../data/test/info_level0_test')
        
        #test if incomplete bugs have been removed
        bug2group = IRCollection(
            'bug_db_name', 'bug_duplicate_collection_name', 'r')
        assert bug2group is not None
        res = bug2group.find({'bug_id':102500})
        assert res.count() == 0
        
        IRLog.get_instance().stop_log()

    def test_get_duplicate_group_information(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_duplicate_group import IRDuplicateGroup

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        duplicate_group = IRDuplicateGroup()
        group_ids = duplicate_group.get_duplicate_group_information(3,10)
        IRLog.get_instance().println('Groups with size between %d, %d: %s' \
                % (0, 100, ' '.join([str(group_id) for group_id in group_ids])))
        IRLog.get_instance().stop_log()

    def test_get_bugs_in_group(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_duplicate_group import IRDuplicateGroup

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        duplicate_group = IRDuplicateGroup()
        bug_ids = duplicate_group.get_bugs_in_group(1)
        IRLog.get_instance().println('Group %d has bugs: ' % (1) + \
                ' '.join([str(bug_id) for bug_id in bug_ids]))
        IRLog.get_instance().stop_log()

    def test_is_in_same_duplicate_group(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_duplicate_group import IRDuplicateGroup

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        hit, nothit, duplicates = \
                IRDuplicateGroup.is_in_same_duplicate_group(100000, [(100000, 0.93)])
        IRLog.get_instance().println(
                'Hit: %s' % (','.join([str(bug_id) for bug_id in hit])))
        IRLog.get_instance().println(
                'Not Hit: %s' % (','.join([str(bug_id) for bug_id in nothit])))
        IRLog.get_instance().println(
                'Actual Duplicate: %s' % (','.join([str(bug_id) for bug_id in duplicates])))
        IRLog.get_instance().stop_log()

    def test_parse_dump_dup_file(self):
        
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        from ir_duplicate_group import IRDuplicateGroup

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        duplicate_group = IRDuplicateGroup()
        duplicate_group.parse_dump_dup_file('../data/test/dump_dup_file_test')
        
        bug2group = IRCollection(
            'bug_db_name', 'bug_duplicate_collection_name', 'r')
        assert bug2group is not None

        bug_ids = duplicate_group.get_bugs_in_group(1) 
        IRLog.get_instance().println('In dump-dup_file_test: Group %d has bugs: ' % (1) + \
                    ' '.join([str(bug_id) for bug_id in bug_ids]))
        IRLog.get_instance().stop_log()
