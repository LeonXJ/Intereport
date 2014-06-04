#!/usr/bin/python2.7

from test_base import TestBase

class TestIRSTTools(TestBase):
    """
    Test Gnome stacktrace tools. Executed by Nose
    """

    def test_filter(self):

        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_mongodb_helper import IRMongodbHelper
        from ir_gnome_st_tools import IRSTTools
        from ir_text import IRText
        import pymongo

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRText.parse_info_level1('../data/test/info_level1_test')
        
        con = IRMongodbHelper.get_instance().get_connection()
        db = con[IRConfig.get_instance().get('bug_db_name')]
        assert None != db
        col = db[IRConfig.get_instance().get('bug_text_collection_name')]
        assert None != col
        # Maybe a bug here:
        # The test of filter (originally) depends on parse_info_level1
        # But parse_info_level1 seems to invoke filter...
        for bug in col.find():
            # TODO: it's not correct. no stacktrace in desc
            desc, stack = IRSTTools.filter(bug["desc"])      


        IRLog.get_instance().stop_log()

    def test_compare_stackinfo(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_mongodb_helper import IRMongodbHelper
        from ir_gnome_st_tools import IRSTTools
        from ir_text import IRText
        from random import randint
        import pymongo

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRText.parse_info_level1('../data/test/stacktrace_test')
        
        con = IRMongodbHelper.get_instance().get_connection()
        db = con[IRConfig.get_instance().get('bug_db_name')]
        assert None != db
        col = db[IRConfig.get_instance().get('bug_text_collection_name')]
        assert None != col

        bugs = col.find()
        total = col.count()
        st1 = bugs[0]["stacktrace"]

        for i in range(total):
            st2 = bugs[i]["stacktrace"]
            result_weight = IRSTTools.compare_stackinfo(st1, st2, 'weight')
            result_max = IRSTTools.compare_stackinfo(st1, st2, 'max')
            IRLog.get_instance().println('Weight: %f, Max: %f' \
                    % (result_weight, result_max))

        IRLog.get_instance().stop_log()

    def test_asm_similarity(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_gnome_st_tools import IRSTTools

        raw_descritpion = '''
Distribution: Ubuntu 6.10 (edgy)
Gnome Release: 2.16.1 2006-10-02 (Ubuntu)
BugBuddy Version: 2.16.0


#0  __libc_waitpid at ../sysdeps/unix/sysv/linux/waitpid.c line 41
#1 IA__g_spawn_sync at /tmp/buildd/glib2.0-2.22.4/glib/gspawn.c line 386
#2 IA__g_spawn_command_line_sync at /tmp/buildd/glib2.0-2.22.4/glib/gspawn.c
line 700
#3 ?? from /usr/lib/gtk-2.0/modules/libgnomebreakpad.so
#4 <signal handler called>
#5 boxed_nodes_cmp at /tmp/buildd/glib2.0-2.22.4/gobject/gboxed.c line 79
#6 g_bsearch_array_lookup_fuzzy at /tmp/buildd/glib2.0-2.22
.4/glib/gbsearcharray.h line 163
#7 boxed_proxy_collect_value at /tmp/buildd/glib2.0-2.22.4/gobject/gboxed.c
line 360
#8 IA__g_signal_emit_valist at /tmp/buildd/glib2.0-2.22.4/gobject/gsignal.c
line 2955
'''

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        IRConfig.get_instance().set('stacktrace_algorithm','signal')

        des, stack = IRSTTools.filter(raw_descritpion)
        epsilon = 0.001
        print stack
        assert stack[0].__len__() == 4
        assert abs(IRSTTools.compare_stackinfo(stack, stack, 'signal') - 1.0)\
               < epsilon
        assert abs(IRSTTools.compare_stackinfo([[]], stack, 'signal') -1.0) <\
               epsilon
        assert abs(IRSTTools.compare_stackinfo([], stack, 'signal') - 1.0) < epsilon
        assert abs(IRSTTools.compare_stackinfo(stack, [], 'signal') - 0.0) < epsilon

