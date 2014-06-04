#!/usr/bin/python2.7
"""
Author:
    Xie Jialiang
Date:
    2014-1-9
Usage:
    python2.7 ir_debugger [config file]
"""

class IRDebugger(object):
    """
    Debuger.
    """

    @classmethod
    def compare(cls, bug_a, bug_b):
        """
        compare the calculation of two bugs (both in db).
        """

        from ir_report import IRReport
        report_a = IRReport(bug_a)
        report_b = IRReport(bug_b)
        title_a = 'indb' + str(bug_a)
        title_b = 'indb' + str(bug_b)
        # compare text
        cls.print_text(title_a, report_a)
        cls.print_text(title_b, report_b)
        # compare term frequency
        cls.compare_and_print_termcount(title_a, report_a, title_b, report_b)
        # compare tfidf
        cls.compare_and_print_tfidf(title_a, report_a, title_b, report_b)
        # similarity
        cls.print_similarity_score(report_a, report_b)

    @classmethod
    def compare_with_sim_file(cls, bug_a, filename, bug_b):
        """Warning: bug_a acts as bug in database, bug_b acts as new report."""

        from ir_sim_bug_evaluator import IRSimBugEvaluator
        from ir_report import IRReport

        title_a = "indb" + str(bug_a)
        title_b = "file" + str(bug_b)
        report_a = IRReport(bug_a)
        report_b = IRSimBugEvaluator.get_report_from_test_file(filename, bug_b)

        # text
        cls.print_text(title_a, report_a)
        cls.print_text(title_b, report_b)
        # term frequency
        cls.compare_and_print_termcount(
            title_a, report_a, title_b, report_b)
        # tfidf
        cls.compare_and_print_tfidf(title_a, report_a, title_b, report_b)
        # similarity
        cls.print_similarity_score(report_b, report_a)


    @classmethod
    def print_text(cls, title, report, log_level = 1):
        """Print the text section of report.

        Args:
            title: str, Title representing this report.
            report: IRReport
            log_level: int
        """
        from ir_log import IRLog
        IRLog.get_instance().println('[Text][%s]' % title, log_level)
        
        summary, description = report.get_summary_and_description_text()
        stacktrace = report.get_stacktrace_text()
        IRLog.get_instance().println('[Text][Summary][%s] %s' % (title, summary),
                                     log_level)
        IRLog.get_instance().println('[Text][Description][%s] %s' \
                % (title, description), log_level)
        IRLog.get_instance().println('[Text][Stacktrace][%s] %s' % (title, stacktrace),
                                     log_level)
        
    @classmethod
    def compare_and_print_termcount(cls, title_a, report_a,
                                    title_b, report_b):
        from ir_log import IRLog
        from ir_term_count import IRTermCount
        summary_a, description_a = \
                report_a.get_summary_and_description_termcount()
        summary_b, description_b = \
                report_b.get_summary_and_description_termcount()
        IRLog.get_instance().println('[Termcount][Summary][%s][%s]' \
                % (title_a, title_b))
        IRTermCount.show_dict_compare(summary_a, summary_b)
        IRLog.get_instance().println('[Termcount][Description][%s][%s]' \
                % (title_a, title_b))
        IRTermCount.show_dict_compare(description_a, description_b)

    @classmethod
    def compare_and_print_tfidf(cls, title_a, report_a,
                                title_b, report_b):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF
        
        summary_field_name = IRConfig.get_instance().get('bug_summary_name')
        description_field_name = IRConfig.get_instance().get('bug_description_name')
        summary_a, description_a = report_a.get_summary_and_description_tfidf()
        summary_b, description_b = report_b.get_summary_and_description_tfidf()
        IRLog.get_instance().println('[TFIDF][Summary][%s][%s]' \
                % (title_a, title_b))
        IRTFIDF.show_dict_compare(summary_a, summary_b, summary_field_name)
        IRLog.get_instance().println('[TFIDF][Description][%s][%s]' \
                % (title_a, title_b))
        IRTFIDF.show_dict_compare(description_a, description_b, description_field_name)

    @classmethod
    def print_similarity_score(cls, report_a, report_b):
        """Warning: report_a is primary! It is critial in asymatric algorithm"""

        from ir_log import IRLog

        total, summary, description, stacktrace = \
                report_a.similarity_with(report_b)
        IRLog.get_instance().println('[Similarity] %f '\
                '=[Summary]%f[Description]%f[Stacktrace]%f' \
                % (total, summary, description, stacktrace))

if __name__ == '__main__':
    import sys
    from ir_config import IRConfig

    IRConfig.get_instance().load(sys.argv[1])
    if sys.argv.__len__() == 4:
        IRDebugger.compare(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv.__len__() == 5:
        IRDebugger.compare_with_sim_file(int(sys.argv[2]),
                                         sys.argv[3], int(sys.argv[4]))
