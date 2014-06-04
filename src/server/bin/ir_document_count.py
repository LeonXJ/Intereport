#!/usr/bin/python2.7
"""Calculate document count.

As an executive script, you can batch calculate document count
by reading from term_count database:

    [script] [config]
"""

__author__ = 'leonxj@gmail.com (Jialiang Xie)'
__reviewer__ = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-17'

class IRDocumentCount(object):
    """Calculate term count over documents."""

    __is_cache = True
    __cache_document_count = {}

    @classmethod
    def batch_generate_document_count(cls):
        """Batch calculate term count over documents.
        Input is from mongodb, termcount collection.
        """

        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection 
        from ir_term_count import IRTermCount

        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        term_name = IRConfig.get_instance().get('bug_term_name')
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        # Calculate document count and stored in document_count
        document_count = {}
        def iter_term_count(bug):
            for term in bug[summary_name]:
                if not term in document_count:
                    document_count[term] = {term_name:term, summary_name:0,
                                            description_name:0}
                document_count[term][summary_name] += 1
            for term in bug[description_name]:
                if not term in document_count:
                    document_count[term] = {term_name:term, summary_name:0,
                                            description_name:0}
                document_count[term][description_name] += 1
        IRProgressBar.execute_iteration_for_cursor(IRTermCount.get_iterator({}),
                                                   iter_term_count, "Counting Document Count")
        # Write to db
        documentcount_collection = IRCollection(
            'bug_db_name', 'bug_documentcount_collection_name', 'w')
        def write_to_mongo(term):
            documentcount_collection.insert(document_count[term])
        IRProgressBar.execute_iteration_for_dict(document_count, write_to_mongo,
                                                 "Write to database")
        documentcount_collection.create_index([(bug_id_name, IRCollection.ASCENDING)])
        documentcount_collection.close()

    @classmethod
    def set_is_cache(cls, is_cache):
        cls.__is_cache = is_cache

    @classmethod
    def cache_all_data(cls):
        """Load all document count into memory.
        
        """
        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        # config
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        term_name = IRConfig.get_instance().get('bug_term_name')
        
        cls.__is_cache = True
        documentcount_collection = IRCollection(
            'bug_db_name', 'bug_documentcount_collection_name', 'r')
        def iter_document_count(term):
            summary = term[summary_name] if summary_name in term else 0
            description = term[description_name] if description_name in term else 0
            cls.__cache_document_count[term[term_name]] = \
                    (summary, description)
        IRProgressBar.execute_iteration_for_cursor(
            documentcount_collection.find({}), iter_document_count,
            "Caching Document Count")

    @classmethod
    def get_documentcount(cls, term, field = None, documentcount_collection = None):
        """Get documentcount of a term.

        Args:
            term, str

        Returns:
            if field == None: (int, int), (summary document count, description document count)
            else: int, the document count of corresponding field
        """

        if cls.__is_cache and term in cls.__cache_document_count:
            if field is None:
                return cls.__cache_document_count[term]
            else:
                from ir_config import IRConfig
                summary_name = IRConfig.get_instance().get('bug_summary_name')
                description_name = IRConfig.get_instance().get('bug_description_name')
                if field == summary_name:
                    return cls.__cache_document_count[term][0]
                elif field == description_name:
                    return cls.__cache_document_count[term][1]
                else:
                    return 0
        # load from db
        from ir_mongodb_helper import IRCollection
        from ir_config import IRConfig
        term_name = IRConfig.get_instance().get('bug_term_name')
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        if documentcount_collection is None:
            documentcount_collection = IRCollection(
                'bug_db_name', 'bug_documentcount_collection_name', 'r')
        res = documentcount_collection.find({term_name : term})
        summary = 0
        description = 0
        if res.count() > 0:
            if summary_name in res[0]:
                summary = res[0][summary_name]
            if description_name in res[0]:
                description = res[0][description_name]
        if cls.__is_cache:
           cls.__cache_document_count[term] = (summary, description)
        # return value
        if field is None:
            return summary, description
        elif field == summary_name:
            return summary
        elif field == description_name:
            return description
        else:
            return 0

if __name__ == '__main__':
    import sys
    from ir_log import IRLog
    from ir_config import IRConfig

    IRLog.get_instance().start_log()
    IRConfig.get_instance().load(sys.argv[1])
    IRDocumentCount.batch_generate_document_count()
    IRLog.get_instance().stop_log()


