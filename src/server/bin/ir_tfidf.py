#!/usr/bin/python2.7
"""Calculate TFIDF.

As an executive script, you can batch calculate TFIDF for
    bugs in intereport:

    [script] [config]
"""

__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2014-1-2'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-17'

class IRTFIDF(object):
    """
    Calculate TFIDF, i.e. Term frequency Inversed Document Frequencey.
    """

    __is_cache = True
    __cache = {}
    __total_report_number = None

    @classmethod
    def set_is_cache(cls, is_cache):
        """Set if cache data.
            
        Args:
            cache: boolean
        """
        cls.__is_cache = is_cache

    @classmethod
    def cache_all_data(cls):
        """Load all TFIDF into memory."""
        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        tfidf_collection = IRCollection(
            'bug_db_name', 'bug_tfidf_collection_name', 'r')
        cls.set_is_cache(True)
        cls.__cache = {}
        def iter_tfidf(bug):
            cls.__cache[bug[bug_id_name]] = (bug[summary_name],
                                             bug[description_name])
        IRProgressBar.execute_iteration_for_cursor(tfidf_collection.find(),
                                                   iter_tfidf, "Caching TFIDF")

    @classmethod
    def calculate_tfidf_for_report_termcount(cls,
                                             summary_termcount,
                                             description_termcount):
        """Calculate TFIDF for single report.
        
        Args:
            summary_termcount: dict, {term -> termcount}
            description_termcount: dict, {term -> termcount}

        Returns:
            [dict, dict], [tfidf of summary, tfidf of description]
        """
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        documentcount_collection = IRCollection(
            'bug_db_name', 'bug_documentcount_collection_name', 'r')
        total_document = cls.get_total_report_number()
        summary_tfidf = cls.calculate_tfidf(
            summary_termcount,
            IRConfig.get_instance().get('bug_summary_name'),
            total_document,
            documentcount_collection)
        description_tfidf = cls.calculate_tfidf(
            description_termcount,
            IRConfig.get_instance().get('bug_description_name'),
            total_document,
            documentcount_collection)
        return summary_tfidf, description_tfidf

    @classmethod
    def calculate_tfidf(cls, termcount, field_name, document_num,
                        documentcount_collection = None, algorithm = None):
        """Calculate TFIDF for a BoW.

        Args:
            termcount: dict, {term -> count}
            field_name: str, 'summary' or 'description', in order to get 
                document count
            document_num: int, Total number of documents
            algorithm: str, 'tfidf' for term-frequency and normalized tfidf.
                            'bidf' for 0-1 counting without normalized
                            if None, fetch config from file
        Returns:
            dict, {term -> tfidf}
        """
        from math import sqrt
        from ir_document_count import IRDocumentCount

        #total_termcount = cls.__get_total_number_of_terms(termcount)
        # calcualte raw tfidf
        if algorithm is None:
            from ir_config import IRConfig
            algorithm = IRConfig.get_instance().get('tfidf_algorithm')
        
        tfidfs = {}
        length_2 = 0
        #total_termcount = cls.__get_total_number_of_terms(termcount)
        # calculate raw tfidf
        if algorithm is None:
            from ir_config import IRConfig
            algorithm = IRConfig.get_instance().get('tfidf_algorithm')
        for term, count in termcount.items():
            documentcount = IRDocumentCount.get_documentcount(term, field_name,
                                                              documentcount_collection)
            idf = cls.get_idf(documentcount)
            # Warning: there're two types of tf: term count or term frequency
            #   We need to compare their performance
            # If we normalize the vector, we just use occurrence of term
            if algorithm == 'tfidf':
                tfidf = float(count) * idf #/ total_termcount
                length_2 += tfidf ** 2
            elif algorithm == 'bidf':
                tfidf = (1 if count > 0 else 0) * idf
            tfidfs[term] = tfidf
        # normalize raw tfidf
        if algorithm == 'tfidf':
            length = sqrt(length_2)
            if abs(length) > 0.0001:
                for term in tfidfs:
                    tfidfs[term] /= length
        return tfidfs

    @classmethod
    def __get_total_number_of_terms(cls, termcount):
        """Get total number of terms in termcount.
        
        Args:
            termcount: dict, {term -> count}

        Returns:
            int, Total number of terms
        """
        total = 0
        for term, count in termcount.items():
            total += count
        return total

    @classmethod
    def batch_generate_tfidf(cls):
        """Batch calculate TFIDF."""

        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        from ir_document_count import IRDocumentCount
        from ir_term_count import IRTermCount
        # get config
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        tfidf_algorithm = IRConfig.get_instance().get('tfidf_algorithm')
        # prepare collections
        IRDocumentCount.cache_all_data()
        tfidf_collection = IRCollection(
            'bug_db_name', 'bug_tfidf_collection_name', 'w')
        # batch calculate tfidf
        termcount_iterator = IRTermCount.get_iterator()
        bug_count = termcount_iterator.count()
        def iter_term_count(bug):
            summary_tfidf = cls.calculate_tfidf(bug[summary_name],
                                                summary_name, bug_count, None, tfidf_algorithm)
            description_tfidf = cls.calculate_tfidf(bug[description_name],
                                                    description_name, bug_count, None, tfidf_algorithm)
            tfidf_collection.insert({bug_id_name : bug[bug_id_name],
                                     summary_name : summary_tfidf,
                                     description_name : description_tfidf})
        IRProgressBar.execute_iteration_for_cursor(termcount_iterator,
                                                   iter_term_count, "Calculating TFIDF")
        tfidf_collection.create_index([(bug_id_name, IRCollection.ASCENDING)])
        tfidf_collection.close()

    @classmethod
    def get_tfidf_of_bug(cls, bug_id):
        """Get tfidf of a bug.

        Args:
            bug_id: int

        Returns:
            [dict, dict], [TFIDF of summary, TFIDF of description]
        """

        if cls.__is_cache:
            if bug_id in cls.__cache:
                return cls.__cache[bug_id]
        # load from db
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        tfidf_collection = IRCollection(
            'bug_db_name', 'bug_tfidf_collection_name', 'r')
        find_result = tfidf_collection.find({bug_id_name : bug_id})
        summary = {}
        description = {}
        if find_result.count() > 0:
            summary = find_result[0][summary_name]
            description = find_result[0][description_name]
        if cls.__is_cache:
            cls.__cache[bug_id] = (summary, description)
        return summary, description

    @classmethod
    def show_dict_compare(cls, dicta, dictb, field_name = 'summ',
                          log_level = 1):
        """Compare and print the tfidf of two tfidf.
        tfidf sorted.

        Args:
            dicta: dict, TFIDF
            dictb: dict, TFIDF
            field_name: str, summary or description?
            log_level: int
        """

        from ir_log import IRLog
        from ir_mongodb_helper import IRCollection
        from ir_document_count import IRDocumentCount

        documentcount_collection = IRCollection(
            'bug_db_name', 'bug_documentcount_collection_name', 'r')
        keys = set()
        if None != dicta:
            for key in dicta:
                keys.add(key)
        if None != dictb:
            for key in dictb:
                keys.add(key)
        # sort by product
        product = []
        for key in keys:
            tfidf_a = 0.0
            tfidf_b = 0.0
            if (None != dicta) and (key in dicta):
                tfidf_a = dicta[key]
            if (None != dictb) and (key in dictb):
                tfidf_b = dictb[key]
            documentcount = IRDocumentCount.get_documentcount(
                key, field_name, documentcount_collection)
            idf = cls.get_idf(documentcount)
            product.append((key, tfidf_a*tfidf_b, tfidf_a, tfidf_b, documentcount, idf))
        product.sort(cmp=lambda a,b:cmp(a[1],b[1]), reverse = True)
        # print it out
        IRLog.get_instance().println('%16s\t%8s\t%8s\t%8s\t%8s\t%8s' \
                % ('term', 'tfidf a', 'tfidf b', 'doccount', 'idf', 'sim'))
        for item in product:
            IRLog.get_instance().println('%16s\t%8f\t%8f\t%8d\t%8f\t%8f' \
                    % (item[0], item[2], item[3], item[4], item[5], item[1]), log_level)
    
    @classmethod
    def tfidf_similarity(cls, a, b):
        """Calculate the vectors' angular similarity.

        Args:
            a: dict, {term -> tfidf}
            b: dict, {term -> tfidf}

        Returns:
            float, the angular similarity
        """
        similarity = 0.0
        if a.__len__() > b.__len__():
            primary = b
            secondary = a
        else:
            primary = a
            secondary = b
        for term in primary:
            if term in secondary:
                similarity += primary[term] * secondary[term]
        return similarity

    @classmethod
    def tfidf_asm_similarity(cls, primary, secondary, primary_squared_length = None,
                             penalty_terms = None, penalty_weight = None):
        """Calculate asymatrics similarity between primary and secondary.
            Return the simiarity value between 0.0 and 1.0. 
              asm_similarity = tfidf_similarity / primary_squared_length

        Args:
            primary: dict, {term -> tfidf}
            secondary: dict, {term -> tfidf}
            primary_squared_length: float. If None, calculate here.

        Returns:
            float
        """
        
        if primary_squared_length is None:
            primary_squared_length = cls.get_squared_length(primary)
        if abs(primary_squared_length) < 0.000001:
            return 1.0
        penalty = 0.0
        if penalty_terms is not None:
            if penalty_weight is None:
                from ir_config import IRConfig
                penalty_weight = IRConfig.get_instance().get_float('penalty_weight')
            for term in penalty_terms:
                if term in secondary:
                    penalty += secondary[term]
            penalty *= penalty_weight
        return max(0.0, (cls.tfidf_similarity(primary, secondary) - penalty) / primary_squared_length)

    @classmethod
    def get_squared_length(cls, tfidf):
        """Get the squred length of tfidf.

        Args:
            dict, TFIDF

        Returns:
            float
        """

        length2 = 0.0
        for term, score in tfidf.items():
            length2 += score ** 2
        return length2

    @classmethod
    def get_idf(cls, document_count):
        """Calculate IDF.

        Args:
            total_document_number: int
            document_count: int

        Returns:
            float, IDF
"""
        from math import log
        return log(float(cls.get_total_report_number()+1) / (1 + document_count))

    @classmethod
    def get_unit_idf(cls, document_count):
        from math import log
        return cls.get_idf(document_count) / cls.get_idf(0)


    @classmethod
    def get_total_report_number(cls):
        """Get the total number of reports.

        Returns:
            int
        """
        if cls.__is_cache and cls.__total_report_number is not None:
            return cls.__total_report_number
        from ir_mongodb_helper import IRCollection
        tc_collection = IRCollection(
            'bug_db_name', 'bug_termcount_collection_name', 'r')
        total_report_number = tc_collection.count()
        if cls.__is_cache:
            cls.__total_report_number = total_report_number
        return total_report_number


if __name__ == "__main__":
    import sys
    from ir_log import IRLog
    from ir_config import IRConfig

    IRLog.get_instance().start_log()
    IRConfig.get_instance().load(sys.argv[1])
    IRTFIDF.batch_generate_tfidf()
    IRLog.get_instance().stop_log()
    
