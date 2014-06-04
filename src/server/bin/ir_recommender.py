#!/usr/bin/python2.7
"""

"""

__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2014-3-4'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-18'

class IRRecommender(object):
    """
    IRRecommender
    """

    @classmethod
    def do_recommend(cls, new_report):
        
        import time
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_report import IRReport
        from ir_sentence import IRSentence

        print 'DO_RECOMMEND', str(new_report.get_stacktrace())

        IRLog.get_instance().println('Finding similar reports')
        start_t = time.time()
        sim_bug_ids, dup_bug_ids = new_report.similarities_and_duplicates()
        similar_t = time.time()
        IRLog.get_instance().println('Found %d similar reports and %d duplicate reports in %fs' \
                % (sim_bug_ids.__len__(), dup_bug_ids.__len__(), similar_t - start_t))

        sim_bugs = [IRReport(sim_bug_id[0]) for sim_bug_id in sim_bug_ids]
        duplicate_packs = [cls.get_report_text_by_bug_id(dup_bug_id[0])
                                  for dup_bug_id in dup_bug_ids]
        IRLog.get_instance().println('Duplicate reports: %s' % ','.\
                join([str(dup_bug_id[0]) for dup_bug_id in dup_bug_ids]))

        IRLog.get_instance().println('Extracting key term')
        deltas = cls.get_all_reports_difference(new_report, sim_bugs)
        term = cls.get_term_by_simple_entropy(deltas, sim_bug_ids, new_report
                                              .get_penalty_terms())
        term_t = time.time()
        keyword = term
        IRLog.get_instance().println('Choose term: %s in %fs' \
                % (term, term_t - similar_t))
        # pick out candidate sentences
        max_sentences_number = 1000
        cur_sentences_number = 0
        IRLog.get_instance().println('Extracting sentences')
        candidate_sentences = []
        for index, delta in enumerate(deltas):
            if not term in delta[1]:
                continue
            # term in this report
            sentences = IRSentence.get_sentence_from_description(
                sim_bugs[index].get_description_text(), 
                sim_bugs[index].get_bug_id())
            for sentence in sentences:
                if sentence.contain_term(term):
                    candidate_sentences.append(sentence)
                    cur_sentences_number += 1
            if cur_sentences_number > max_sentences_number:
                break
        sent_t = time.time()
        IRLog.get_instance().println('Extracted %d sentences from %d reports in %fs' \
                % (candidate_sentences.__len__(), deltas.__len__(),
                   sent_t - term_t))
        # cluster sentences
        IRLog.get_instance().println('Clustering sentences')
        selected_sentences_num = IRConfig.get_instance().get_int('bug_sentence_number')
        if candidate_sentences.__len__() > selected_sentences_num:
            clusters, sentence_ids = IRSentence.cluster_sentences(
                candidate_sentences, selected_sentences_num)
        else:
            clusters = [x for x in xrange(candidate_sentences.__len__())]
            sentence_ids = clusters
        clust_t = time.time()
        IRLog.get_instance().println('Finished clustering in %fs' \
                % (clust_t - sent_t))
        # pick out the sentences nearest to centroid in each group
        #pick_group = set()
        #for index, cluster in enumerate(clusters):
        #    if cluster in pick_group:
        #        continue
        #    pick_group.add(cluster)
        #    if pick_group.__len__() == selected_sentences_num:
        #        break
        #    IRLog.get_instance().println("Recommend: %s" \
        #            % (candidate_sentences[index].get_text()))
        sentence_packs = []
        sentence_report_ids = []
        for sentence_id in sentence_ids:
            IRLog.get_instance().println("Recommend (Report#: %d): %s" \
                    % ( candidate_sentences[sentence_id].get_bug_id(), 
                        candidate_sentences[sentence_id].get_text()) )
            sentence_packs.append((candidate_sentences[sentence_id].get_bug_id(),
                                   candidate_sentences[sentence_id].get_text())
                                  )
            sentence_report_ids.append(candidate_sentences[sentence_id].get_bug_id())
        IRLog.get_instance().println('Recommending finished in %fs' \
                % (time.time() - start_t))

        return keyword, sentence_packs, duplicate_packs

    @classmethod
    def get_report_text_by_bug_id(cls, id):
        from ir_report import IRReport
        report = IRReport(id)
        summary_text, description_text = report.get_summary_and_description_text()
        return id, summary_text, description_text

    @classmethod
    def do_recommend_cmd(cls, cmd_text):
        """Do recommend from cmd_text

        Args:
            cmd_text: str, the text follows the standard format,
                  create_ts;product;summary;raw_description
        """
        from ir_report import IRReport
        new_report = IRReport.from_string(cmd_text.strip())
        cls.do_recommend(new_report)


    @classmethod
    def start_shell(cls):
        """Start a shell that do recommending interactively"""
        from ir_log import IRLog
        from ir_tfidf import IRTFIDF
        from ir_document_count import IRDocumentCount
        from ir_report import IRReport

        IRLog.get_instance().println("Starting Intereport...")
        IRTFIDF.cache_all_data()
        IRDocumentCount.cache_all_data()
        IRLog.get_instance().println("Intereport Started. Waiting for input")

        new_report = None
        while 1:
            cmd = raw_input("Input command:").strip()
            if cmd == 'exit':
                IRLog.get_instance().println('Exiting')
                break
            elif cmd == 'new':
                IRLog.get_instance().println('Creating New Report')
                import time
                cur_time = -1
                while cur_time < 0:
                    try:
                        cur_time = int(time.mktime(time.strptime(
                            raw_input("Input Time (e.g., 2011-05-05): "),
                            '%Y-%m-%d')))
                    except:
                        cur_time = -1
                product = raw_input("Input Product: ")
                summary = raw_input("Summary: ")
                raw_description = raw_input("Description:\n")
                new_report = IRReport.from_string(IRReport.separator.join([
                    str(cur_time), product.lower(), summary, raw_description,
                    '', '']))
                cls.__print_report(new_report)
            elif cmd == 'do':
                IRLog.get_instance().println('Do Recommending')
                if new_report is None:
                    IRLog.get_instance().println('Error! Please create '
                                                 'report first.')
                else:
                    cls.do_recommend(new_report)
            elif cmd == 'ls':
                IRLog.get_instance().println('Show Current Report')
                if new_report is None:
                     IRLog.get_instance().println('Error! Please create '
                                                  'report first.')
                else:
                    cls.__print_report(new_report)
            elif cmd == 'ad':
                IRLog.get_instance().println('Appending Description')
                if new_report is None:
                     IRLog.get_instance().println('Error! Please create '
                                                  'report first.')
                else:
                    append_description = raw_input("Append Description:\n")
                    description =' '.join([new_report.get_description_text(),
                                           append_description])
                    dummy_report = IRReport(new_report.get_summary_text(),
                                            description)
                    dummy_report.set_stacktrace(new_report.get_stacktrace())
                    dummy_report.set_basic_info(new_report.get_create_ts(),
                                                new_report.get_product())
                    dummy_report.set_penalty_terms(new_report.get_penalty_terms())
                    dummy_report.set_dummy_bug_id(new_report.get_dummy_bug_id())
                    new_report = dummy_report
                    IRLog.get_instance().println('Description: %s' % description)
            elif cmd == 'ap':
                IRLog.get_instance().println('Appending Penalties')
                if new_report is None:
                    IRLog.get_instance().println('Error! Please create '
                                                 'report first.')
                else:
                    raw = []
                    while raw.__len__() < 1:
                        raw = raw_input('Input Penalties (split by \',\'):').split(',')
                    from ir_term_count import IRTermCount
                    penalty = new_report.get_penalty_terms()
                    if penalty is None:
                        penalty = []
                    penalty += IRTermCount.do_stemming(raw)
                    new_report.set_penalty_terms(penalty)
                    print len(penalty), penalty
                    IRLog.get_instance().println('Penalties: %s' % \
                                                     (', '.join(penalty)))
            elif cmd == 'sd':
                IRLog.get_instance().println('Set Dummy Bug ID')
                if new_report is None:
                    IRLog.get_instance().println('Error! Please create '
                                                 'report first.')
                else:
                    bug_id = -1
                    while bug_id <= 0:
                        try:
                            bug_id = int(raw_input('Dummy Bug ID: '))
                        except:
                            bug_id = -1
                    new_report.set_dummy_bug_id(bug_id)
                    IRLog.get_instance().println('Dummy Bug ID: %d' % bug_id)
            elif cmd == 'help':
                cls.__show_help()
            else:
                IRLog.get_instance().println('Error! Unkown command: %s' \
                                                % cmd)
                cls.__show_help()
        # end of while 1
        IRLog.get_instance().println("Bye")

    @classmethod
    def __raw_lines__(cls, msg):
        """
        Allow user to input several lines for convenient debugging
        Ending with "[[;;]]"

        (Description may need more lines of input for debugging?)
        """
        print msg,
        result = ""
        ending = "[[;;]]"
        while True:
            temp = raw_input()
            if temp == ending:
                break
            result += (temp + "\n")
        return result

    @classmethod
    def __print_report(cls, report):
        from ir_log import IRLog
        if report is None:
            IRLog.get_instance().println('None')
            return
        import time
        IRLog.get_instance().println('Product: %s' % (report.get_product()))
        IRLog.get_instance().println('Create Time: %s, %d' \
            % (time.strftime('%Y-%m-%d', time.localtime(report.get_create_ts())),
               report.get_create_ts()))
        IRLog.get_instance().println('Summary: %s' \
                                     % (report.get_summary_text()))
        IRLog.get_instance().println('Description: %s' \
                                     % (report.get_description_text()))
        IRLog.get_instance().println('Stacktrace: %s' \
                                     % (report.get_stacktrace_text()))
        IRLog.get_instance().println('Penalties: %s' \
                                     % (','.join(report.get_penalty_terms())))
        dummy_bug_id = report.get_dummy_bug_id()
        if dummy_bug_id is not None:
            IRLog.get_instance().println('Dummay: %d' % dummy_bug_id)

    @classmethod
    def __show_help(cls):
        from ir_log import IRLog
        IRLog.get_instance().println('new: create new report')
        IRLog.get_instance().println('do: do recommending for current report')
        IRLog.get_instance().println('ad: append description to current report')
        IRLog.get_instance().println('ap: append penalties to current report')
        IRLog.get_instance().println('help: show help')
        IRLog.get_instance().println('exit: exit')

    @classmethod
    def get_all_reports_difference(cls, new_report, similar_reports):
        """Get the difference of terms of each reports in similar_reports.
        For each similar report, return the key difference of its summary
        and description respectly

        Args:
            new_report: IRReport, The new report.
            similar_reports: [IRReport], The similar report.

        Returns:
            [(set, set)], [(diff of summary, diff of description)]
        """

        diff = []
        for similar in similar_reports:
            diff.append(cls.get_report_difference(
                new_report, similar))
        return diff

    @classmethod
    def get_report_difference(cls, new_report, similar_report):
        """Get the difference of terms of reports in similar_reports.
        return the dict difference of its summary and description respectly

        Args:
            new_report: IRReport, The new report.
            similar_report: IRReport, The similar report.

        Returns:
            (set, set), (diff of summary, diff of description)
        """

        new_summary_termcount, new_description_termcount = \
                new_report.get_summary_and_description_termcount()
        
        sim_summary_termcount, sim_description_termcount = \
                similar_report.get_summary_and_description_termcount()

        diff_summary = cls.__get_dict_difference(
            new_summary_termcount, sim_summary_termcount)
        diff_description = cls.__get_dict_difference(
            new_description_termcount, sim_description_termcount)
        # still, we don't want the term in summary to be recommended
        diff_description -= set(new_summary_termcount.keys())
        # skip the skip_terms in new report
        diff_description -= set(new_report.get_skip_terms())
        # and product should not be recommended
        from ir_term_count import IRTermCount
        product = new_report.get_product()
        if product is not None:
            product_term = IRTermCount.do_stemming([product])[0]
            if product_term in diff_description:
                diff_description.remove(product_term)
        return diff_summary, diff_description

    @classmethod
    def get_term_by_simple_entropy(cls, diff, sim_bug_ids, penalty_terms =
    None):
        """Get the best term which has most entropy in diff.
            

        Args:
            diff: [(set, set)], generated by get_all_reports_difference

        Retruns:
            str, The term
        """

        termcount = {}
        max_score = -1.0
        max_score_term = None
        # count the occurance of term
        total_score = 0.0
        for index, delta in enumerate(diff):
            total_score += sim_bug_ids[index][1][0]
            # only account for
            for term in delta[1]:
                if penalty_terms is not None and term in penalty_terms:
                    continue
                if not term in termcount:
                    termcount[term] = 0.0
                termcount[term] += sim_bug_ids[index][1][0]
        # calcualte the value and pick the most
        from ir_config import IRConfig
        from ir_document_count import IRDocumentCount
        from ir_tfidf import IRTFIDF
        description_name = IRConfig.get_instance().get('bug_description_name')
        # debug use
        scoreboard = []
        # /debug use
        from math import log
        for term in termcount:
            bg_score = termcount[term] / total_score
            ig_score = -2.0 * abs(float(termcount[term]) / total_score - 0.5) + 1
            idf = IRTFIDF.get_unit_idf(IRDocumentCount.get_documentcount(term, \
                    description_name))
            score = ig_score * idf
            scoreboard.append((term, score, ig_score, idf))
            if score > max_score:
                max_score = score
                max_score_term = term
        scoreboard.sort(cmp=lambda x,y:cmp(x[1],y[1]), reverse=True)
        from ir_log import IRLog
        IRLog.get_instance().println('Candidate keywords: %s' % ','.join(['word','score','ig_score','idf']))
        IRLog.get_instance().println('\n'.join([ \
                ','.join([t[0],str(t[1]), str(t[2]), str(t[3])]) for t in scoreboard[:10] \
                ]))
        return max_score_term

    @classmethod
    def __get_dict_difference(cls, primary, secondary):
        """Return a set containing elements in secondary but not in
        primary.

        Args:
            primary: dict, {term -> termcount}
            secondary: dict, {term -> termcount}

        Returns:
            set, A set of terms
        """

        return set(secondary.keys()) - set(primary.keys())

if __name__ == '__main__':

    import sys
    from ir_log import IRLog
    from ir_config import IRConfig
    from ir_text import IRText
    from ir_sim_bug_evaluator import IRSimBugEvaluator
    from ir_report import IRReport

    reload(sys)
    sys.setdefaultencoding('utf-8')
    
    IRLog.get_instance().start_log(True, 'recommend.log')
    config = sys.argv[1]
    IRConfig.get_instance().load(config)
    mode = sys.argv[2]

    new_report = None
    if mode == 'file':
        test_file = sys.argv[3]
        bug_id = int(sys.argv[4])
        from ir_sim_bug_evaluator import IRSimBugEvaluator
        new_report = IRSimBugEvaluator.get_report_from_test_file(test_file, bug_id)
        if new_report is None:
            IRLog.get_instance().println('Error! Cannot find report %d in %s' % \
                    (bug_id, test_file))
        else:
            if sys.argv.__len__() > 5:
                from ir_term_count import IRTermCount
                penalty_terms_raw = sys.argv[4].split(',')
                penalty_terms = set(IRTermCount.do_stemming(penalty_terms_raw))
                IRLog.get_instance().println('%d penalty terms: %s:' \
                    % (penalty_terms.__len__(), ','.join(penalty_terms)))
                new_report.set_penalty_terms(penalty_terms)
    elif mode == 'text':
        text = sys.argv[3]
        new_report = IRReport.from_string(text)
    elif mode == 'inte':
        IRRecommender.start_shell()
        exit()
    else:
        IRLog.get_instance().println('Error! Known mode %s' % mode)
    from ir_tfidf import IRTFIDF
    from ir_document_count import IRDocumentCount
    IRTFIDF.cache_all_data()
    IRDocumentCount.cache_all_data()
    IRRecommender.do_recommend(new_report)
    IRLog.get_instance().stop_log()
