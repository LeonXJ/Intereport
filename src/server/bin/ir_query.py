#!/usr/bin/python2.7
"""Get the summary and description and return the top n similarities.

Usage:
    py [config file] [summary] [description] [top n]
Output:
    list of bug ids with top n similarities
"""

__author__ = 'leonxj@gmail.com (Jialiang Xie)'
__date__ = '2014-2-20'

class IRQuery(object):

    @classmethod
    def query(cls, summary, description, top_n):

        from ir_term_count import IRTermCount
        from ir_tfidf import IRTFIDF
        summary_bow, description_bow = \
            IRTermCount.calculate_term_count(summary, description)
        summary_tfidf, description_tfidf = \
            IRTFIDF.calculate_tfidf_for_report_termcount(summary_bow,
                                                         description_bow)
        similarities = \
            IRTFIDF.get_top_n_similarity_over_all(summary_tfidf,
                                                  description_tfidf,
                                                  top_n)
        return similarities


if __name__ == '__main__':
    
    import sys
    from ir_log import IRLog
    from ir_config import IRConfig
    from ir_term_count import IRTermCount
    from ir_tfidf import IRTFIDF

    IRLog.get_instance().set_stdout(False)
    IRConfig.get_instance().load(sys.argv[1])
    summary = sys.argv[2]
    description = sys.argv[3]
    top_n = int(sys.argv[4])
    query = IRQuery()
    similarities = query.query(summary, description, top_n)
    
    print ';'.join(str(similarity[0]) for similarity in similarities)
