#!/usr/bin/python2.7
"""Calculate and Get termcount.
As a python executive script, batch calculate termcount from text in mongodb:
    ./[script] [config file]

To batch calculate termcount from text:
    IRTermCount.batch_generate_term_count()

To calculate termcount of a given text:
    tc_summary, tc_description = \
        IRTermCount.calculate_term_count(summary, description)

To query the termcount of an bug:
    summary, description = IRTermCount.get_termcount_of_bug(100100)

Also, you can compare two BoWs by:
    IRTermCount.show_dict_compare(BoW1, BoW2)
"""

__author__ = 'leonxj@gmail.com (Jialiang Xie)'
__date__ = '2013-12-31'
__reviewer__ = 'leonxj@gmail.com (Jialiang Xie)'
__review_date = '2014-3-17'

class IRTermCount(object):
    """
    Calculate term count from plain text.
    """

    __word_net_lemmatizer = None
    __tokenizer = None
    __snowball_stemmer = None
    __porter_stemmer = None
    __lancaster_stemmer = None
    __stopword_set = None
    __is_cache = False
    __cache_term_count = {}


    __synlists = [['email','mail','e-mail','message'],
                ['spacebar', 'space'],
                ['click', 'press'],
                ['compose', 'write'],
                ['directory', 'folder']]
    __syndict = None

    @classmethod
    def set_is_cache(cls, is_cache):
        cls.__is_cache = is_cache

    @classmethod
    def cache_all_data(cls):
        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
      
        cls.__is_cache = True
        bug_name = IRConfig.get_instance(). \
                get('bug_id_name', 'bug_id')
        summary_name = IRConfig.get_instance(). \
                    get('bug_summary_name', 'summ')
        description_name = IRConfig.get_instance(). \
                    get('bug_description_name', 'desc')
        def iter_term_count(bug):
            cls.__cache_term_count[bug[bug_name]] = \
                (bug[summary_name], bug[description_name])
        IRProgressBar.execute_iteration_for_cursor(cls.get_iterator({}),
                                                   iter_term_count, "Caching Term Count")

    @classmethod
    def batch_generate_term_count(cls):
        """Generate term count for text in mongodb database,
            and store to database.
        """
        from ir_log import IRProgressBar
        from ir_text import IRText
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        # config
        bug_id_name = IRConfig.get_instance().get('bug_id_name', 'bug_id')
        summary_name = IRConfig.get_instance().get('bug_summary_name', 'summ')
        description_name = IRConfig.get_instance().\
                get('bug_description_name', 'desc')
        
        termcount_collection = IRCollection(
            'bug_db_name', 'bug_termcount_collection_name', 'w')
        def iter_text(bug):
            summary_bow, description_bow = cls.calculate_term_count(
                bug[summary_name], bug[description_name])
            termcount_collection.insert({
                bug_id_name : bug[bug_id_name],
                summary_name : summary_bow,
                description_name : description_bow })
        IRProgressBar.execute_iteration_for_cursor(IRText.get_iterator({}),
                                                   iter_text, "From Text to Term Count")
        termcount_collection.create_index([(bug_id_name, IRCollection.ASCENDING)])
        termcount_collection.close()

    @classmethod
    def calculate_term_count(cls, summary, description):
        """Calculate term count for a single report text.
        
        Args:
            summary: str, The summary text.
            description: str, The description text.

        Returns:
            dict, dict: BoW of summary, BoW of description
        """
        description_bow = cls.get_bow(description, True)
        summary_bow = cls.get_bow(summary, False)
        return summary_bow, description_bow

    @classmethod
    def get_iterator(cls, arg=None):
        """Get iterator of termcounts fulfiling arg.
        
        Args:
            arg: dict, Condiction.
            
        Returns:
            cursor
        """
        if not arg: arg = {}
        from ir_mongodb_helper import IRCollection
        termcount_collection = IRCollection(
            'bug_db_name', 'bug_termcount_collection_name', 'r')
        return termcount_collection.find(arg)
    
    @classmethod
    def show_dict_compare(cls, dicta, dictb, log_level = 1):
        """Compare the print two BoW.

        Args:
            dicta: dict, term -> count
            dictb: dict
            log_level: int
        """

        from ir_log import IRLog
        keys = set()
        if None != dicta:
            for key in dicta:
                keys.add(key)
        if None != dictb:
            for key in dictb:
                keys.add(key)
        # sort by common num
        common_num = []
        for key in keys:
            counta = 0
            countb = 0
            if None != dicta:
                if key in dicta:
                    counta = dicta[key]
            if None != dictb:
                if key in dictb:
                    countb = dictb[key]
            common_num.append((key, min(counta, countb), counta, countb))
        common_num.sort(cmp=lambda a,b:cmp(a[1],b[1]), reverse=True)
        # print it out
        for item in common_num:
            IRLog.get_instance().println('%16s\t%8d\t%8d' \
                        % (item[0], item[2], item[3]), log_level)

    @classmethod
    def get_termcount_of_bug(cls, bug_id):
        """Get termcount of a bug

        Args:
            bug_id: int

        Returns:
            [dict, dict], [termcount of summary, termcount of description]
        """

        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        if cls.__is_cache:
            if bug_id in cls.__cache_term_count:
                return cls.__cache_term_count[bug_id]
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        termcount_collection = IRCollection(
            'bug_db_name', 'bug_termcount_collection_name', 'r')
        res = termcount_collection.find({bug_id_name : bug_id})
        summary = {}
        description = {}
        if res.count() > 0:
            summary = res[0][summary_name]
            description = res[0][description_name]
        if cls.__is_cache:
            cls.__cache_term_count[bug_id] = (summary, description)
        return summary, description

    @classmethod
    def do_tokenization(cls, text):
        """Tokenize the text. For tester
        >>> from ir_config import IRConfig
        >>> IRConfig.get_instance().load('../data/test/bug_test.cfg')
        >>> IRTermCount.do_tokenization('mouse-down')
        ['mouse-down']
        >>> IRTermCount.do_tokenization('set_background_color()')
        ['set_background_color']

        Args:
            text: str

        Returns:
            [str]
        """
        return cls.__do_tokenize(text)



    @classmethod
    def __insert_into_dict(cls, dict_from, dict_to, inner_key):
        """Insert into a two levels dict.

        Args:
            dict_from: list/dict, terms to be inserted
            dict_to: dict, term -> (inner_key -> value)
            inner_key: object
        """

        for key in dict_from:    
            if not key in dict_to:
                dict_to[key] = {}
            if not inner_key in dict_to[key]:
                dict_to[key][inner_key] = 0
            dict_to[key][inner_key] += 1

    @classmethod
    def get_bow(cls, text, remove_template):
        """Get a dict where key=word and value=freqency
        
        Args:
            text: str, data to be dealt with
            stemming: boolean, Turn on or off the stemming option
            remove_template: boolean

        Returns:
            dict, term -> count
        """
        
        #from collections import Counter
        import collections
        import re

        bags = {}
        if None == text:
            return bags
        if remove_template:
            from ir_template_tools import IRTemplateTools
            text = IRTemplateTools.filter(text)
        #words = re.split(sep, text)
        words = cls.__do_tokenize(text)
        words = cls.do_stemming(words)
        bags = dict(collections.Counter(words))
        bags = cls.__remove_stop_words(bags)
        bags = cls.__syn_expand(bags)
        return bags

    @classmethod
    def __get_syndict(cls):
        if cls.__syndict is None:
            # build from synlist
            cls.__syndict = dict()
            for index, synlist in enumerate(cls.__synlists):
                stemmed_synlist = cls.do_stemming(synlist)
                cls.__synlists[index] = stemmed_synlist
                for term in stemmed_synlist:
                    cls.__syndict[term] = index
        return cls.__synlists, cls.__syndict

    @classmethod
    def __syn_expand(cls, bags):
        synlists, syndict = cls.__get_syndict()
        new_bags = dict()
        for term, count in bags.iteritems():
            if term in syndict:
                synlist = synlists[syndict[term]]
                for syn in synlist:
                    if syn not in bags:
                        new_bags[syn] = count
            new_bags[term] = count
        return new_bags



    @classmethod
    def __do_synmap(cls, words):
        return [cls.__synset[word] if word in cls.__synset else word for word
                in words]

    @classmethod
    def __do_tokenize(cls, doc):
        """Tokenize the paragraph.

        Args:
            doc: str, the text

        Returns: 
            list, the list of tokens.
        """
        
        if None == cls.__tokenizer:
            from ir_config import IRConfig
            from nltk.tokenize import RegexpTokenizer
            token_exp = IRConfig.get_instance().get('text_token_regexp')
            cls.__tokenizer = RegexpTokenizer(token_exp)
        return cls.__tokenizer.tokenize(doc)
   
    @classmethod
    def do_stemming(cls, words):
        from ir_config import IRConfig
        cfg_stemmer = IRConfig.get_instance().get('stemmer', 'lancaster')
        if cfg_stemmer == 'porter':
            stemmer = cls.__get_porter_stemmer()
        elif cfg_stemmer == 'lancaster':
            stemmer = cls.__get_lancaster_stemmer()
        elif cfg_stemmer == 'snowball':
            stemmer = cls.__get_snowball_stemmer()
        return [stemmer.stem(word) for word in words]

    @classmethod
    def __get_snowball_stemmer(cls):
        """Get snowball stemmer.

        Returns:
            snowball stemmer.
        """
        if None == cls.__snowball_stemmer:
            from nltk.stem.snowball import SnowballStemmer
            cls.__snowball_stemmer = SnowballStemmer('english')
        return cls.__snowball_stemmer

    @classmethod
    def __get_lancaster_stemmer(cls):
        """Get the Lancaster stemmer.

        Returns:
            Lancaster stemmer
        """
        if None == cls.__lancaster_stemmer:
            from nltk.stem.lancaster import LancasterStemmer
            cls.__lancaster_stemmer = LancasterStemmer()
        return cls.__lancaster_stemmer

    @classmethod
    def __get_porter_stemmer(cls):
        """Get the Porter stemmer.

        Returns:
            Porter stemmer
        """
        if None == cls.__porter_stemmer:
            from nltk.stem.porter import PorterStemmer
            cls.__porter_stemmer = PorterStemmer()
        return cls.__porter_stemmer

    @classmethod
    def __remove_stop_words(cls, bags):
        """Remove the stop words.

        Args:
            bags: dict, term -> count
        
        Returns:
            dict, term -> count
        """
        
        import nltk 
        res = {}
        for word in bags.keys():
            # stop words in nltk
            if word.__len__() < 3 or \
                word in cls.__get_stopword_set():
                continue
            else:
                res[word] = bags[word]
        return res

    @classmethod
    def __get_stopword_set(cls):
        if cls.__stopword_set is None:
            import nltk
            cls.__stopword_set = nltk.corpus.stopwords.words('english')
            cls.__stopword_set += set( \
                    cls.do_stemming(['please', 'bug', 'report', 'try',
                                     'doesn']) )
        return cls.__stopword_set

    @classmethod
    def create_incomplete_report(cls, summary, description, drop_rate):
        """Create the text of an incomplete report.
    
        Args:
            summary: str, the text of summary
            description: str, the text of description
            drop_rate: float, 0.0 for not drop and 1.0f for totally drop.
        
        Returns:
            [str, str], [summary, description]
        """
        return [cls.__random_drop_words(summary, drop_rate, True),
                cls.__random_drop_words(description, drop_rate, True)]

    @classmethod
    def __random_drop_words(cls, text, drop_rate, remove_template):
        """randomly drop words.
        
        Args:
            text: str, the text.
            drop_rate: float

        Returns:
            str, text
        """
        from random import uniform
        if None == text:
            return ''
        
        if remove_template:
            from ir_template_tools import IRTemplateTools
            text = IRTemplateTools.filter(text)
        words = cls.__do_tokenize(text)
        words = filter(lambda x: uniform(0,1) > drop_rate, words)
        return ' '.join(words)


if __name__ == '__main__':
    import sys
    from ir_config import IRConfig

    IRConfig.get_instance().load(sys.argv[1])
    IRTermCount.batch_generate_term_count()
    
