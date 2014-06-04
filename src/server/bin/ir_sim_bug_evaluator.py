#!/usr/bin/python2.7
"""Handle the test for duplicate detection.

As an executive script, it conducts tests by:
    [script] [config] [mode] [target_file] [drop_rate]/[log file]
mode: 'w' for generating test case,
      'r' for reading test case file and do experiment
target_file: in 'w' mode, it defines the output test case file
             in 'r' mode, it defines the input test case file
drop_rate: only for 'w' mode, 0.0 will generate complete bug
log_file: only for 'r' mode, the outputing log file

To generate an incomplete test case file, for example:
    [script] ../data/test/bug_test.cfg w ../data/test/inc_test.tst 0.6
To conduct experiment on the test file:
    [script] ../data/test/bug_test.cfg r ../data/test/inc_test.tst ../data/test/log/inc
"""

__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2014-1-3'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-18'

class IRSimBugEvaluator(object):
    """ Tester of Duplication Detection"""

    def generate_test_file(self, filename, drop_rate):
        """Generate incomplete bug reports and save in filename.
        Format:
            original_bug_id[[sep]]inc_summary[[sep]]inc_description

        Args:
            filename: str, output filename
            drop_rate: float, 0.0 for complete bug
        """
        
        from ir_config import IRConfig
        from ir_duplicate_group import IRDuplicateGroup

        # file
        outfile = open(filename, 'w')
        # begin test
        test_cases = [
            ('small group',
                 0, IRConfig.get_instance().get_int('bug_small_group_size_max'),
                 IRConfig.get_instance().get_int('bug_small_group_sample_num')),

            ('middle group',
             IRConfig.get_instance().get_int('bug_small_group_size_max'),
             IRConfig.get_instance().get_int('bug_middle_group_size_max'),
             IRConfig.get_instance().get_int('bug_middle_group_sample_num')),
            ('large group',
             IRConfig.get_instance().get_int('bug_middle_group_size_max'),
             99999,
             IRConfig.get_instance().get_int('bug_large_group_sample_num'))
                ]

        duplicate_group = IRDuplicateGroup()
        for test_case in test_cases:
            group = duplicate_group.get_duplicate_group_information(
                test_case[1], test_case[2])
            self.__generate_sample_over_a_list(outfile, group, test_case[3],
                                               drop_rate)
        outfile.close()

    def generate_testcases_over_bugid_files(self, input_file, output_file, drop_rate):
        infile = open(input_file, 'r')
        outfile = open(output_file, 'w')
        for line in infile:
            bug_id = int(line)
            report = self.__generate_single_bug(bug_id, drop_rate)
            outfile.write("%s\n" % report.to_string())
        outfile.close()
        infile.close()

    def __generate_single_bug(self, bug_id, drop_rate):
        """Generate an incomplete bug report text.
        
        Args:
            bug_id: int, original bug id.
            drop_rate: float, 0.0 for not drop, 1.0 for totally drop.
        
        Returns:
            IRReport
        """
        from ir_text import IRText
        from ir_term_count import IRTermCount
        from ir_report import IRReport

        # get description and summary
        summary, description = IRText.get_summary_and_description_of_bug(bug_id)
        create_ts, product = IRText.get_basic_info_of_bug(bug_id)
        if drop_rate > 0.001:
            summary, description = \
                IRTermCount.create_incomplete_report(summary, description, drop_rate)
            print description
        new_report = IRReport(summary, description)
        new_report.set_stacktrace(IRText.get_stacktrace_of_bug(bug_id))
        new_report.set_dummy_bug_id(bug_id)
        new_report.set_basic_info(create_ts, product)
        return new_report
    
    def do_test_over_file(self, filename):
        """Do test over the file.

        Args:
            filename: str, the input file which generated by 
                generate_incomplete_test_file.
        """
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_duplicate_group import IRDuplicateGroup
        from ir_text import IRText
        from ir_term_count import IRTermCount
        from ir_tfidf import IRTFIDF
        from ir_report import IRReport
        from ir_document_count import IRDocumentCount

        IRText.cache_all_data()
        IRTFIDF.cache_all_data()
        IRDocumentCount.cache_all_data()

        remove_self_bug_id = IRConfig.get_instance().get_bool('remove_self_bug_id', True)

        sim_tot_precision = 0.0
        sim_tot_recall = 0.0
        sim_bi_tot_recall = 0.0
        sim_tot_size = 0

        dup_tot_precision = 0.0
        dup_tot_recall = 0.0
        dup_bi_toto_recall = 0.0
        dup_num = 0
        test_num = 0

        infile = open(filename, 'r')
        for line in infile:
            IRLog.get_instance().println('----test----')
            test_num += 1
            line.strip()
            new_report = IRReport.from_string(line)
            ori_report = IRReport(new_report.get_dummy_bug_id())
            #IRLog.get_instance().println('Summary')
            #IRTermCount.show_dict_compare(ori_report.get_summary_termcount(),
            #                              new_report.get_summary_termcount())
            #IRLog.get_instance().println('Description')
            #IRTermCount.show_dict_compare(ori_report.get_description_termcount(),
            #                              new_report.get_description_termcount())
            # do test for single
            similarities, duplicates = new_report.similarities_and_duplicates()
            sim_ids = [sim[0] for sim in similarities]
            dup_ids = [dup[0] for dup in duplicates]
            IRLog.get_instance().println('Sim ids: %s' % str(sim_ids))
            IRLog.get_instance().println('Dup ids: %s' % str(dup_ids))
            # evaluate sim
            sim_hit, sim_nothit, real_duplicates = \
                IRDuplicateGroup.is_in_same_duplicate_group(
                    new_report.get_dummy_bug_id(), sim_ids, remove_self_bug_id)
            # some group contain only one
            if real_duplicates.__len__() == 0:
                test_num -= 1
                continue
            
            precision, recall = self.__report_result(
                new_report.get_dummy_bug_id(), sim_hit, sim_nothit, real_duplicates)

            sim_tot_precision += precision
            sim_tot_recall += recall
            sim_tot_size += sim_ids.__len__()
            sim_bi_tot_recall += 1 if recall > 0.0 else 0

            if dup_ids.__len__() > 0:
                dup_num += 1
                dup_hit, dup_nothit, real_duplicates = \
                        IRDuplicateGroup.is_in_same_duplicate_group(
                                new_report.get_dummy_bug_id(), dup_ids, remove_self_bug_id)
                precision, recall = self.__report_result(
                        new_report.get_dummy_bug_id(), dup_hit, dup_nothit, real_duplicates)
                dup_tot_precision += precision
                dup_tot_recall += recall
                dup_bi_toto_recall += 1 if recall > 0.0 else 0
        # general conclusion
        if dup_num == 0:
            dup_num = 1.0
        IRLog.get_instance().println(','.join(['#cases', 'sim pre', 'sim rec', 'sim birec', 'sim size',\
                '#dup', 'dup pre', 'dup rec', 'dup birec']))
        IRLog.get_instance().println(','.join([str(test_num), \
                str(sim_tot_precision/test_num), str(sim_tot_recall/test_num), str(sim_bi_tot_recall/test_num), str(float(sim_tot_size)/test_num), \
                str(dup_num), \
                str(dup_tot_precision/dup_num), str(dup_tot_recall/dup_num), str(dup_bi_toto_recall/dup_num)]))
        infile.close()

    @classmethod
    def get_report_from_test_file(cls, filename, bug_id):
        from ir_report import IRReport
        infile = open(filename, 'r')
        for line in infile:
            raw = line.split(IRReport.separator)
            dummy_bug_id = int(raw[5])
            if bug_id == dummy_bug_id:
                return IRReport.from_string(line.strip())
        return None
    
    def __generate_sample_over_a_list(self, infile, group_ids, sample_num, drop_rate):
        """
        Conduct evaluation over the bugs within the groups in group ids

        group_ids: a list of group_ids
        sample_num: the number of bugs being sampled
        drop_rate: the probability of chance to drop a word
        """
        from ir_log import IRLog
        sampling_bugs = self.__get_sample_bugs_within_groups(group_ids, sample_num)
        for bug_id in sampling_bugs:
            new_report = \
                    self.__generate_single_bug(bug_id, drop_rate)
            IRLog.get_instance().println('%d' % bug_id)
            infile.write('%s\n' % (new_report.to_string()))

    def __report_result(self, bug_id, hit, nothit, duplicates):
        """
        Print the evaluation result.

        hit: actual duplicates found by algorithm
        notthis: actual non-duplicates, but are detected as duplicate by algorithm
        Return: precision, recall
        """
        from ir_log import IRLog
        total =  hit.__len__() + nothit.__len__()
        if total == 0:
            precision = 0.0
        else:
            precision = float(hit.__len__())/(hit.__len__() + nothit.__len__())
        if duplicates.__len__() == 0:
            recall = 0.0
        else:
            recall = float(hit.__len__())/duplicates.__len__()
        IRLog.get_instance().println('Bug %d, precision %f, recall %f, ' \
                'duplicate size %d' \
                % (bug_id,
                   precision,
                   recall,
                   duplicates.__len__()), 2)
        IRLog.get_instance().println('Hit %d duplicates: %s' \
                % (hit.__len__(), ','.join([str(bug_id) for bug_id in hit])), 1)
        IRLog.get_instance().println('Hit %d nonduplicates: %s' \
                % (nothit.__len__(), ','.join([str(bug_id) for bug_id in nothit])), 1)
        IRLog.get_instance().println('Actual %d duplicates: %s' \
                % (duplicates.__len__(), ','.join([str(bug_id) for bug_id in duplicates])), 1)
        return precision, recall

    def __get_sample_bugs_within_groups(self, group_ids, sample_num):
        """
        Get the randomly sampled bug ids within group_ids.
        
        group_ids: a list of group_ids
        sample_num: the number of bugs being sampled
        """

        import random
        from ir_duplicate_group import IRDuplicateGroup
        duplicate_group = IRDuplicateGroup()

        if sample_num <= 0 or group_ids.__len__() == 0:
            return []

        sample_bugs = []
        for sample_index in range(0, sample_num):
            group_index = random.randrange(0, group_ids.__len__())
            group_id = group_ids[group_index]
            bugs = duplicate_group.get_bugs_in_group(group_id)
            bug = bugs[random.randrange(0, bugs.__len__())]
            sample_bugs.append(bug)
        return sample_bugs

if __name__ == '__main__':
    import sys
    import os
    from ir_log import IRLog
    from ir_config import IRConfig

    reload(sys)
    sys.setdefaultencoding('utf-8')

    bin_path = sys.path[0]
    os.chdir(bin_path)
    
    # switch mode
    assert sys.argv.__len__() >= 5
    config = sys.argv[1]
    IRConfig.get_instance().load(config)
    mode = sys.argv[2]
    target_file = sys.argv[3]
    
    if mode == 'w':
        drop_rate = float(sys.argv[4])
        evl = IRSimBugEvaluator()
        evl.generate_test_file(target_file, drop_rate)
        import shutil
        import time
        shutil.copyfile(target_file, target_file + 
            '.' + time.strftime('%Y%m%d.%H%M', time.localtime(time.time()))) 
    elif mode == 'r':
        import time
        log_org = sys.argv[4]
        IRLog.get_instance().start_log(True, log_org)
        evl = IRSimBugEvaluator()
        evl.do_test_over_file(target_file)
        IRLog.get_instance().stop_log()
    
        import shutil
        import time
        shutil.copyfile(log_org, log_org + \
                '.' + time.strftime('%Y%m%d.%H%M', time.localtime(time.time())))   
    elif mode == 'g':
        out_file = sys.argv[4]
        drop_rate = float(sys.argv[5])
        evl = IRSimBugEvaluator()
        evl.generate_testcases_over_bugid_files(target_file, out_file, drop_rate)
