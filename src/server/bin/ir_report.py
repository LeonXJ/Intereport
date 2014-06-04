"""Bug report

If the bug_id is given, it will get information from database.
Otherwise it calculate the information from: 
    summary, description, stacktrace
"""

__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2014-2-28'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-18'

class IRReport(object):
    """
    Representation of Report information.
    """

    separator = ';'
    term_separator = ','
    newline = '[[NEWLINE]]'
    semicolon = '[[SEMICOLON]]'

    def __init__(self, bug_id_or_summary,
                 description = None):
        """Declare a report.
           If bug_id_or_summary is int, the rest args should be None. 

        Args:
            bug_id_or_summary: int/str
            description: str
            stacktrace: str
        """
        if description is None:
            self.__bug_id = int(bug_id_or_summary)
            self.__summary_text = None
            self.__description_text = None
        elif description is not None:
            self.__bug_id = None
            self.__summary_text = bug_id_or_summary
            from ir_gnome_st_tools import IRSTTools
            self.__description_text, self.__stacktrace = \
                    IRSTTools.filter(description)
        else:
            assert False
        self.__stacktrace_text = None
        self.__summary_termcount = None
        self.__description_termcount = None
        self.__stacktrace = None
        self.__summary_tfidf = None
        self.__description_tfidf = None
        self.__allow_cache = True
        self.__summary_squared_length = None
        self.__description_squared_length = None
        self.__product = None
        self.__create_ts = None
        self.__penalty_terms = []
        self.__dummy_bug_id = None
        self.__exclude_report_ids = []
        self.__skip_terms = []

    @classmethod
    def from_string(cls, text):
        """Get a report instance from string.

        Args:
            text: str, it should follow the format:
            create_ts;product;summary;raw_description;penalty;dummy_bug_id;exclude_report_ids;skip_terms

        Returns:
            IRReport
        """
        from ir_term_count import IRTermCount
        from ir_gnome_st_tools import IRSTTools

        fields = text.strip().split(cls.separator)
        summary = cls.__untranslate_special_character(fields[2])
        raw_description = cls.__untranslate_special_character(fields[3])
        description, stacktrace = IRSTTools.filter(raw_description)
       
        new_report = IRReport(summary, description)
        new_report.set_stacktrace(stacktrace)
        new_report.set_basic_info(int(fields[0]), fields[1])
        # penalty
        if fields.__len__() > 4 and fields[4].__len__() > 0:
            penalty = fields[4].split(cls.term_separator)
            new_report.set_penalty_terms(penalty)
        # dummpy report id
        if fields.__len__() > 5 and fields[5].__len__() > 0:
            new_report.set_dummy_bug_id(int(fields[5]))
        # exclude dups
        if fields.__len__() > 6 and fields[6].__len__() > 0:
            exclude_report_ids_str = fields[6].split(cls.term_separator)
            new_report.set_exclude_report_ids( \
                    [int(id) for id in exclude_report_ids_str])
        # skip terms
        if fields.__len__() > 7 and fields[7].__len__() > 0:
            skip_terms = fields[7].split(cls.term_separator)
            new_report.set_skip_terms(skip_terms)
        
        return new_report

    def to_string(self):
        res = [str(self.get_create_ts()),
               str(self.get_product()),
               self.__translate_special_character(self.get_summary_text()),
               self.__translate_special_character(
                   '%s %s' % (self.get_description_text(),
                              self.get_stacktrace_text()))]
        # penalty
        penalty = self.get_penalty_terms()
        if penalty is not None:
            res.append(self.term_separator.join(penalty))
        else:
            res.append('')
        # dummy bugs
        dummy_bug_id = self.get_dummy_bug_id()
        if dummy_bug_id is not None:
            res.append(str(dummy_bug_id))
        else:
            res.append('')
        # exclude dups
        exclude_report_ids = self.get_exclude_report_ids()
        if exclude_report_ids is not None:
            text_ids = [str(id) for id in exclude_report_ids]
            res.append(self.term_separator.join(text_ids))
        else:
            res.append('')
        # skip terms
        skip_terms = self.get_skip_terms()
        if skip_terms is not None:
            res.append(self.term_separator.join(skip_terms))
        else:
            res.append('')
        return self.separator.join(res)

    def set_allow_cache(self, allow_cache):
        """If cache result from database.
        
        Args:
            allow_cache: bool
        """
        self.__allow_cache = allow_cache

    def get_bug_id(self):
        return self.__bug_id

    def get_basic_info(self):
        if self.__bug_id is None:
            return self.__create_ts, self.__product
        else:
            if self.__allow_cache and \
                            self.__create_ts is not None and \
                            self.__product is not None:
                return self.__create_ts, self.__product
            from ir_text import IRText
            create_ts, product = IRText.get_basic_info_of_bug(self.__bug_id)
            if self.__allow_cache:
                self.__create_ts, self.__product = (create_ts, product)
            return create_ts, product

    # only use for sim and debug
    def set_basic_info(self, create_ts, product):
        self.set_create_ts(create_ts)
        self.set_product(product)

    def get_create_ts(self):
        create_ts, product = self.get_basic_info()
        return create_ts

    def set_product(self, product):
        self.__product = product

    def set_create_ts(self, create_ts):
        self.__create_ts = create_ts

    def get_product(self):
        create_ts, product = self.get_basic_info()
        return product

    def get_summary_and_description_text(self):
        if self.__bug_id is None:
            return [self.__summary_text, self.__description_text]
        else:
            if self.__allow_cache and \
                            self.__summary_text is not None and \
                            self.__description_text is not None:
                return [self.__summary_text, self.__description_text]
            from ir_text import IRText
            summary, description = \
                    IRText.get_summary_and_description_of_bug(self.__bug_id)
            if self.__allow_cache:
                self.__summary_text, self.__description_text = \
                        summary, description
            return summary, description
    
    def get_summary_text(self):
        """Notice: you'd better use get_summary_and_description if you want
            both summary and description.
        """
        summary, description = self.get_summary_and_description_text()
        return summary

    def get_description_text(self):
        summary, description = self.get_summary_and_description_text()
        return description

    def get_stacktrace_text(self):
        if self.__allow_cache and self.__stacktrace_text is not None:
            return self.__stacktrace_text
        from ir_gnome_st_tools import IRSTTools
        stacktrace_text = IRSTTools.to_string(self.get_stacktrace())
        if self.__allow_cache:
            self.__stacktrace_text = stacktrace_text
        return stacktrace_text

    # only use for sim and debugger
    def set_stacktrace(self, stacktrace):
        self.__stacktrace = stacktrace

    def get_stacktrace(self):
        if self.__bug_id is None:
            return self.__stacktrace
        else:
            if self.__allow_cache and self.__stacktrace is not None:
                return self.__stacktrace
            from ir_text import IRText
            stack = IRText.get_stacktrace_of_bug(self.__bug_id)
            if self.__allow_cache:
                self.__stacktrace = stack
            return stack

    def get_summary_and_description_termcount(self):
        if self.__bug_id is None:
            if self.__summary_termcount is None or \
                            self.__description_termcount is None:
                self.__update_summary_and_description_termcount_from_text()
            return [self.__summary_termcount, self.__description_termcount]
        else:
            if self.__allow_cache and \
                            self.__summary_termcount is not None and \
                            self.__description_termcount is not None:
                return [self.__summary_termcount, self.__description_termcount]
            from ir_term_count import IRTermCount
            summary, description = \
                    IRTermCount.get_termcount_of_bug(self.__bug_id)
            if self.__allow_cache:
                self.__summary_termcount, self.__description_termcount = \
                        summary, description
            return summary, description

    def get_summary_termcount(self):
        """Notice: you'd better use get_summary_and_description_termcount 
            if you want both summary and description.
        """
        summary_termcount, description_termcount = \
                self.get_summary_and_description_termcount()
        return summary_termcount

    def get_description_termcount(self):
        """Notice: you'd better use get_summary_and_description_termcount 
            if you want both summary and description.
        """
        summary_termcount, description_termcount = \
                self.get_summary_and_description_termcount()
        return description_termcount

    def get_summary_and_description_tfidf(self):
        if self.__bug_id is None:
            if self.__summary_tfidf is None or \
                            self.__description_tfidf is None:
                self.__update_summary_and_description_tfidf_from_termcount()
            return [self.__summary_tfidf, self.__description_tfidf]
        else:
            if self.__allow_cache and \
                            self.__summary_tfidf is not None and \
                            self.__description_tfidf is not None:
                return [self.__summary_tfidf, self.__description_tfidf]
            from ir_tfidf import IRTFIDF
            summary_tfidf, description_tfidf = \
                IRTFIDF.get_tfidf_of_bug(self.__bug_id)
            if self.__allow_cache:
                self.__summary_tfidf, self.__description_tfidf = \
                        summary_tfidf, description_tfidf
            return [summary_tfidf, description_tfidf]

    def get_summary_and_description_tfidf_squared_length(self):
        from ir_tfidf import IRTFIDF
        if self.__summary_squared_length is None or \
                        self.__description_squared_length is None:
            summary, description = self.get_summary_and_description_tfidf()
            self.__summary_squared_length = \
                    IRTFIDF.get_squared_length(summary)
            self.__description_squared_length = \
                    IRTFIDF.get_squared_length(description)
        return self.__summary_squared_length, self.__description_squared_length

    def similarity_with(self, other_report):
        """
        Returns:
            [float, float, float, float], [total score, summary, \
                                           description, stacktrace]
        """
        from ir_config import IRConfig
        from ir_tfidf import IRTFIDF
        from ir_gnome_st_tools import IRSTTools


        summary_ratio = IRConfig.get_instance().get_float('bug_summary_ratio')
        description_ratio = IRConfig.get_instance().get_float('bug_description_ratio')
        stacktrace_ratio = IRConfig.get_instance().get_float('bug_stacktrace_ratio')

        summary_tfidf_a, description_tfidf_a = \
                self.get_summary_and_description_tfidf()
        summary_tfidf_b, description_tfidf_b = \
                other_report.get_summary_and_description_tfidf()

        tfidf_algorithm = IRConfig.get_instance().get('tfidf_algorithm')
        stacktrace_algorithm = IRConfig.get_instance().get('stacktrace_algorithm')
        if tfidf_algorithm == 'tfidf':
            summary_similarity = IRTFIDF.tfidf_similarity(
                summary_tfidf_a, summary_tfidf_b)
            description_similarity = IRTFIDF.tfidf_similarity(
                description_tfidf_a, description_tfidf_b)
        elif tfidf_algorithm == 'bidf':
            summary_squared_length, description_squared_length = \
                    self.get_summary_and_description_tfidf_squared_length()
            summary_similarity = IRTFIDF.tfidf_asm_similarity(
                summary_tfidf_a, summary_tfidf_b, summary_squared_length)
            description_similarity = IRTFIDF.tfidf_asm_similarity(
                description_tfidf_a, description_tfidf_b,
                description_squared_length,
                self.__penalty_terms)

        if self.__stacktrace is None or \
                self.__stacktrace.__len__() == 0 or \
                self.__stacktrace[0].__len__() == 0:
            stacktrace_similarity = 1.0
        else:
            stacktrace_similarity = IRSTTools.compare_stackinfo(
                self.get_stacktrace(), other_report.get_stacktrace(),
                stacktrace_algorithm)

        scoring_strategy = IRConfig.get_instance().get('scoring_strategy',
                                                       'heuristic')
        if scoring_strategy == 'weighted':
            score = self.__weighted_scoring(summary_similarity,
                                            description_similarity, stacktrace_similarity)
        elif scoring_strategy == 'heuristic':
            score = self.__heuristic_scoring(summary_similarity,
                                            description_similarity, stacktrace_similarity)
        elif scoring_strategy == 'distweighted':
            score = self.__distweighted_scoring(summary_similarity,
                                            description_similarity, stacktrace_similarity)
        else:
            assert False, 'invalid scoring strategy'
        return [score,
                summary_similarity,
                description_similarity,
                stacktrace_similarity]

    def __weighted_scoring(self, summary_similarity, description_similarity,
                           stacktrace_similarity):
        from ir_config import IRConfig
        summary_ratio = IRConfig.get_instance().get_float('bug_summary_ratio')
        description_ratio = IRConfig.get_instance().get_float('bug_description_ratio')
        stacktrace_ratio = IRConfig.get_instance().get_float('bug_stacktrace_ratio')
        return summary_similarity * summary_ratio + \
                description_similarity * description_ratio + \
                stacktrace_similarity * stacktrace_ratio

    def __heuristic_scoring(self, summary_similarity, description_similarity,
                            stacktrace_similarity):
        from ir_config import IRConfig
        summary_ratio = IRConfig.get_instance().get_float('bug_summary_ratio')
        description_ratio = IRConfig.get_instance().get_float('bug_description_ratio')
        nl_threshold = IRConfig.get_instance().get_float(
            'bug_nl_threshold')
        stacktrace_threshold = IRConfig.get_instance().get_float('bug_stacktrace_threshold')
        nl_similarity = summary_similarity * summary_ratio + \
                   description_similarity * description_ratio
        if nl_similarity > nl_threshold:
            if stacktrace_similarity > stacktrace_threshold:
                return 0.75 + 0.25 * (nl_similarity * 0.5 + \
                       stacktrace_similarity * 0.5)
            else:
                return 0.5 + 0.25 * nl_similarity
        else:
            if stacktrace_similarity > stacktrace_threshold:
                return 0.25 + 0.25 * stacktrace_similarity
            else:
                return 0.25 * (nl_similarity * 0.5 + stacktrace_similarity *
                               0.5)
    
    def __distweighted_scoring(self, summary_similarity, description_similarity,
                            stacktrace_similarity):
        from ir_config import IRConfig
        
        primary_ratio = IRConfig.get_instance().get_float('bug_primary_ratio')
        summary_ratio = IRConfig.get_instance().get_float('bug_summary_ratio')
        description_ratio = IRConfig.get_instance().get_float('bug_description_ratio')
        nl_similarity = summary_similarity * summary_ratio + \
                   description_similarity * description_ratio
      
        if self.__stacktrace is None or \
                self.__stacktrace.__len__() == 0 or \
                self.__stacktrace[0].__len__() == 0:
            return primary_ratio * nl_similarity + (1.0 - primary_ratio)

        if nl_similarity > stacktrace_similarity:
            return primary_ratio * nl_similarity + (1.0 - primary_ratio) * stacktrace_similarity
        else:
            return primary_ratio * stacktrace_similarity + (1.0 - primary_ratio) * nl_similarity

    def top_n_similarity_over_all(self, n):
        """Calculate the similarities over all reports in database.
        
        Args:
            n: int, The reports with top n scores

        Returns:
            [(bug_id, (score, ...))], sorted list 
        """
        
        similarities = self.similarity_over_all().items()
        if similarities.__len__() == 0:
            return []
        similarities.sort(key=lambda x:x[1][0], reverse = True)
        self.__show_similarity_distribution(similarities)
        self.__show_duplicate_position(similarities)
        if similarities.__len__() < n:
            return similarities
        return similarities[:n]

    def similarities_and_duplicates(self):
        """Calculate the similarities over all existing reports and return
        the similar reports and duplicate reports.

        Returns:
            [bug_id],[bug_id], [similar report ids],[duplicate report ids]
        """
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_duplicate_group import IRDuplicateGroup
        similar_threshold = IRConfig.get_instance().get_float(
            'bug_similar_threshold', 0.7)
        duplicate_num = IRConfig.get_instance().get_int(
            'bug_duplicate_number', 5)
        duplicate_threshold = IRConfig.get_instance().get_int(
            'bug_duplicate_threshold', 10)
        max_similar_number = IRConfig.get_instance().get_int(
            'bug_similar_max', 10000000)
        similar_threshold_percent = IRConfig.get_instance().get_float(
            'bug_similar_threshold_percent', 0.8)
        no_similar_threshold = IRConfig.get_instance().get_float(
            'bug_no_similar_threshold', 0.65)

        similarities = self.similarity_over_all().items()
        if similarities.__len__() == 0:
            return [], []
        similarities.sort(key=lambda  x:x[1][0], reverse = True)
        # report scoring
        IRLog.get_instance().println('Max score report: %s' % str(similarities[0]))
        if similarities.__len__() > 1:
            IRLog.get_instance().println('Second score report: %s' % str(similarities[1]))

        # find cutting edge of similar reports
        max_score = similarities[0][1][0]
        min_score = similarities[-1][1][0]
        IRLog.get_instance().println('max score:%f, min score: %f' %(max_score, min_score))
        IRLog.get_instance().println('no threshold:%f' % no_similar_threshold)
        if max_score < no_similar_threshold:
            return [], []

        similar_threshold_percent_cut = min_score + (max_score - min_score) *\
                                        similar_threshold_percent
        print 'cut:', similar_threshold_percent_cut

        cut_position = min(max_similar_number, self.__binary_search_less(similarities, lambda x:x[1][
            0], similar_threshold_percent_cut))
        IRLog.get_instance().println('Get %d similar reports.' % cut_position)
        # find number of duplicate groups in similar reports
        group_set = set()
        for report in similarities[:cut_position]:
            group_set.add(IRDuplicateGroup.get_group_of_bug(report[0]))
        if None in group_set:
            group_set.remove(None)
        duplicate_reports = []
        if group_set.__len__() <= duplicate_threshold:
            duplicate_reports = similarities[:min(cut_position, duplicate_num)]
        return similarities[:cut_position], duplicate_reports

    def binary_search_less(self, sorted_array, func, target):
        return self.__binary_search_less(sorted_array, func, target)

    def __binary_search_less(self, sorted_array, func, target):
        """Search for the position in sorted_array where the value right less than target.

        Args:
            sorted_array: list
            func: function, get the value of an element in sorted_array
            target: object, target value

        Returns:
            int, the position. -1 if sorted_array.__len__() == 0
        """
        left = 0
        right = sorted_array.__len__() - 1
        if right == -1:
            return -1
        mid = 0
        while left < right:
            mid = (left + right) /2
            num_left = func(sorted_array[left])
            num_right = func(sorted_array[right-1])
            num_mid = func(sorted_array[mid])
            if num_mid >= target:
                left = mid + 1
            elif num_mid < target:
                right = mid
        if func(sorted_array[left]) >= target:
            return left+1
        else:
            return left
       
    def __show_similarity_distribution(self, sorted_similarities):
        """Show the distribtuion of similarities.

        Args:
            sorted_similarities: [(bug_id, (score, ...))]
        """
        from ir_log import IRLog
        tot = sorted_similarities.__len__()
        # number of near top
        print sorted_similarities[0]
        max_score = sorted_similarities[0][1][0]
        min_score = sorted_similarities[-1][1][0]
        score_span = 0.1
        near_threshold = max_score - (max_score - min_score) * score_span
        near_one_number = 0
        for item in sorted_similarities:
            if item[1][0] > near_threshold:
                near_one_number += 1
            else:
                break
        IRLog.get_instance().println('%d in %d (%f) reports have score ' \
                'greater than %f (%f of the score span)' % \
                (near_one_number, tot, float(near_one_number)/tot,
                 near_threshold, score_span))
        # quantiles
        quantiles = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        for quan in quantiles:
            pos = int(quan * tot)
            if pos >= tot:
                pos = tot-1
            IRLog.get_instance().println('Top %d: %f' \
                    % (int(quan*100), sorted_similarities[pos][1][0]))

    def __show_duplicate_position(self, sorted_similarities):
        if self.__dummy_bug_id is None:
            return
        from ir_duplicate_group import IRDuplicateGroup
        group_id = IRDuplicateGroup.get_group_of_bug(self.get_dummy_bug_id())
        if group_id is None:
            return
        from ir_log import IRLog
        dups = set(IRDuplicateGroup.get_bugs_in_group(group_id))
        found = 0
        for index, item in enumerate(sorted_similarities):
            bug_id = item[0]
            if bug_id in dups:
                found += 1
                IRLog.get_instance().println('Dup# %d in Pos %d, score %f' % \
                                             (bug_id, index, item[1][0]))
        IRLog.get_instance().println('%d out of %d duplicates' % \
                (found, dups.__len__()))

    def similarity_over_all(self):
        """Calculate similarity between bug (summary, description) over
         all.

        Returns:
            dict, {bug_id -> [score, summary_score, description_score, stacktrace_score]}
        """

        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        from ir_text import IRText
        from ir_tfidf import IRTFIDF

        logger = IRLog.get_instance()
        search_time_span = 2 * 3600 * 24 * 365
        
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        
        create_ts_name = IRConfig.get_instance().get('bug_create_ts_name')
        product_name = IRConfig.get_instance().get('bug_product_name')

        basic_collection = IRCollection(
            'bug_db_name', 'bug_basic_collection_name', 'r')
        
        reports2scan = basic_collection.find({
            product_name : self.get_product(),
            create_ts_name : {'$gt' : self.get_create_ts() - search_time_span},
            bug_id_name : {'$nin' : self.__exclude_report_ids} })
        result = {}
        IRLog.get_instance().println('Comparing with %d reports.' \
                % (reports2scan.count()) )
        
        print self.__summary_text
        print self.__description_text

        for report in reports2scan:
            bug_id = report[bug_id_name]
            if bug_id == self.get_dummy_bug_id():
                continue
            # because we don't want to load stacktrace in case of self.__stacktrace 
            #    being none, we create and fill the info of report manually
            other_report = IRReport("", "")
            other_report.__summary_tfidf, other_report.__description_tfidf = \
                    IRTFIDF.get_tfidf_of_bug(bug_id)
            # if self.__stacktrace is empty, we don't need to do this
            if self.get_stacktrace() is not None and \
                    self.get_stacktrace().__len__() > 0:
                other_report.__stacktrace = IRText.get_stacktrace_of_bug(bug_id)
            if other_report.__stacktrace is None:
                other_report.__stacktrace = []
            result[bug_id] = self.similarity_with(other_report)

        return result
    
    def set_penalty_terms(self, penalty_terms):
        self.__penalty_terms = penalty_terms

    def add_penalty_term(self, penalty_term):
        self.__penalty_terms.append(penalty_term)

    def get_penalty_terms(self):
        return self.__penalty_terms

    def set_skip_terms(self, skip_terms):
        self.__skip_terms = skip_terms

    def add_skip_term(self, skip_term):
        self.__skip_terms.append(skip_term)

    def get_skip_terms(self):
        return self.__skip_terms

    def set_exclude_report_ids(self, report_ids):
        self.__exclude_report_ids = report_ids

    def add_exclude_report_id(self, report_id):
        self.__exclude_report_ids.append(report_id)
   
    def get_exclude_report_ids(self):
        return self.__exclude_report_ids

    def set_dummy_bug_id(self, dummy_bug_id):
        self.__dummy_bug_id = dummy_bug_id

    def get_dummy_bug_id(self):
        return self.__dummy_bug_id

    @classmethod
    def __translate_special_character(cls, text):
        """Translate '\n' ';' into self.newline and self.semicolon

        Args:
            text: str

        Returns:
            str
        """
        return text.replace('\n', cls.newline).replace(';', cls.semicolon)

    @classmethod
    def __untranslate_special_character(cls, text):
        """Reverse translation_specail_character.

        Args:
            text: str

        Returns:
            str
        """
        return text.replace(cls.newline, '\n').replace(cls.semicolon, ';')

    def __update_stacktrace_from_text(self):
        from ir_gnome_st_tools import IRSTTools
        desc, stack = IRSTTools.filter(self.get_stacktrace_text())
        if stack is None:
            stack = []
        self.__stacktrace = stack

    def __update_summary_and_description_termcount_from_text(self):
        from ir_term_count import IRTermCount
        summary_text, description_text = self.get_summary_and_description_text()
        summary_termcount, description_termcount = \
            IRTermCount.calculate_term_count(summary_text, description_text)
        if self.__summary_termcount is None:
            self.__summary_termcount = summary_termcount
        if self.__description_termcount is None:
            self.__description_termcount = description_termcount

    def __update_summary_and_description_tfidf_from_termcount(self):
        from ir_tfidf import IRTFIDF
        
        summary_termcount, description_termcount = \
                self.get_summary_and_description_termcount()
        summary_tfidf, description_tfidf = \
            IRTFIDF.calculate_tfidf_for_report_termcount(summary_termcount,
                                                         description_termcount)
        if self.__summary_tfidf is None:
            self.__summary_tfidf = summary_tfidf
        if self.__description_tfidf is None:
            self.__description_tfidf = description_tfidf
    
