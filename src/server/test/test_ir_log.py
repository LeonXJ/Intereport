__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2013-12-27'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-13'

from test_base import TestBase

class TestIRLog(TestBase):
    """
    Test IR Log System. Executed by Nose.
    """

    def test_log(self):
        import ir_log as log

        ir_log = log.IRLog.get_instance()
        assert ir_log is not None

        # without logfile
        ir_log.start_log(True)
        # test std out
        ir_log.println('Testing IRLog with default message level.')
        ir_log.println('Testing IRLog with message level 2.', 2)
        ir_log.stop_log()
        # test file
        log_file = 'ir_log_test.log'
        ir_log.start_log(False, log_file)
        test_line = 'Output log to file.'
        ir_log.println(test_line)
        ir_log.stop_log()
        in_file = open(log_file)
        for line in in_file:
            assert line.strip()== '[level 0] ' + test_line
        in_file.close()
        import os
        os.remove(log_file)

    def test_progress_bar(self):
        from ir_log import IRLog
        from ir_log import IRProgressBar

        IRLog.get_instance().start_log(True)
        title = 'ProgressBar Output Not Verbose'
        bar = IRProgressBar(1000, title, False, 0, 1)
        assert bar is not None
        for i in range(0,1001):
            bar.set_value(i)
        title = 'ProgressBar Output Verbose'
        bar = IRProgressBar(1000, title, True, 1, 0)
        assert bar is not None
        for i in range(0,1001):
            bar.set_value(i)
        IRLog.get_instance().start_log()

    def test_execute_iteration_for_cursor(self):
        from ir_log import IRProgressBar
        import pymongo

        con = pymongo.Connection('127.0.0.1', 27017)
        col = con['bug_gnome_test']['text']

        def func(ele):
            print ele
        IRProgressBar.execute_iteration_for_cursor(
            col.find(), func, 'Text')

    def test_execute_iteration_for_file(self):
        from ir_log import IRProgressBar

        file = open('test.tmp', 'w')
        file.write('\n'.join(['One', 'Two', 'III', '4', '5']))
        file.close()

        def func(ele):
            print ele
        file = open('test.tmp', 'r')
        IRProgressBar.execute_iteration_for_file(file, func, 'Text')

    def test_execute_iteration_for_dict(self):
        from ir_log import IRProgressBar

        dictionary = {1:1, 2:2, 3:3, 4:4, 5:5}
        def func(ele):
            print ele, dictionary[ele]
        IRProgressBar.execute_iteration_for_dict(dictionary, func, 'Dict')
