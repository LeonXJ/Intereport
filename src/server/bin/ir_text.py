#!/usr/bin/python2.7

"""Deal with the raw text of bug.
As a script, to parse Bugzilla info level1/mysql dump:
    ./[.py] [config_filename] [level1/mysql] [file to be parsed]

As a python class, to get the text of a bug:
    summary, description = IRText.get_summary_and_description_of_bug(100100)
"""

__author__ = 'Qimu Zheng'
__date__ = '2013-12-30'
__reviewer__ = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-17'

class IRText(object):
    """
    Extract text (summary and description) and insert into mongo db.
    """

    __is_cache = False
    __cache_summary_description = {}
    __cache_stacktrace = {}
    __drop_report_regexp = None

    @classmethod
    def set_is_cache(cls, is_cache):
        """Set if cache data.
            
        Args:
            cache: boolean
        """
        cls.__is_cache = is_cache

    @classmethod
    def cache_all_data(cls):
        """Load all data into memory."""
        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        # get config
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        stacktrace_name = IRConfig.get_instance().get('bug_stacktrace_name')
        # caching data 
        cls.set_is_cache(True)
        text_collection = \
                IRCollection('bug_db_name', 'bug_text_collection_name', 'r')
        cls.__cache_summary_description = {}
        cls.__cache_stacktrace = {}
        def iter_func(bug):
            cls.__cache_summary_description[bug[bug_id_name]] = \
                    (bug[summary_name], bug[description_name])
            cls.__cache_stacktrace[bug[bug_id_name]] = bug[stacktrace_name]
        IRProgressBar.execute_iteration_for_cursor(
            text_collection.find(), iter_func, 'Caching Text Data')
        text_collection.close()

    @classmethod
    def get_iterator(cls, arg):
        """Get the cursor to the items fulfill arg.

        Args:
            arg: dict, condition

        Returns:
            cursor
        """
        from ir_mongodb_helper import IRCollection
        text_collection = IRCollection(
            'bug_db_name', 'bug_text_collection_name', 'r')
        return text_collection.find(arg)

    
    @classmethod
    def get_basic_info_of_bug(cls, bug_id):
        """Get basic info from mongodb.

        Args:
            bug_id: int

        Returns:
            (int, str): (create_ts, product)
        """
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        create_ts_name = IRConfig.get_instance().get('bug_create_ts_name')
        product_name = IRConfig.get_instance().get('bug_product_name')
        basic_collection = IRCollection(
            'bug_db_name', 'bug_basic_collection_name', 'r')
        res = basic_collection.find({bug_id_name : bug_id})
        if res.count() > 0:
            return res[0][create_ts_name], res[0][product_name]
        else:
            return -1, ''

    @classmethod
    def get_summary_and_description_of_bug(cls, bug_id):
        """Get summary and description from mongodb.

        Args:
            bug_id: int

        Returns:
            [str, str], [summary, description]
        """
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        if cls.__is_cache:
            if bug_id in cls.__cache_summary_description:
                return cls.__cache_summary_description[bug_id]
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        summary_name = IRConfig.get_instance().get('bug_summary_name')
        description_name = IRConfig.get_instance().get('bug_description_name')
        text_collection = IRCollection(
            'bug_db_name', 'bug_text_collection_name', 'r')
        res = text_collection.find({bug_id_name : bug_id})
        summary = ''
        description = ''
        if res.count() > 0:
            summary = res[0][summary_name]
            description = res[0][description_name]
        if cls.__is_cache:
            cls.__cache_summary_description[bug_id] = (summary, description)
        return summary, description

    @classmethod
    def get_stacktrace_text_of_bug(cls, bug_id):
        """Get stacktrace text via restoring from [[]] style.

        Args:
            bug_id: int

        Returns:
            str
        """
        res = ''
        threads = cls.get_stacktrace_of_bug(bug_id)
        if threads is not None:
            thread_texts = []
            for thread in threads:
                thread_texts.append('\n'.join(thread))
            res = '\n'.join(thread_texts)
        return res

    @classmethod
    def get_stacktrace_of_bug(cls, bug_id):
        """Get stacktrace from mongodb.

        Args:
            bug_id: int

        Returns:
            [[str]], [[signature]]
        """
        if cls.__is_cache:
            if bug_id in cls.__cache_stacktrace:
                return cls.__cache_stacktrace[bug_id]
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        stacktrace_name = IRConfig.get_instance().get('bug_stacktrace_name')
        text_collection = IRCollection(
            'bug_db_name', 'bug_text_collection_name', 'r')
        res = text_collection.find({bug_id_name : bug_id})
        stacktrace = []
        if res.count() > 0:
            stacktrace = res[0][stacktrace_name]
        if cls.__is_cache:
            cls.__cache_stacktrace[bug_id] = stacktrace
        return stacktrace

    @classmethod
    def parse_info_level1(cls, info_level1_filename = None):
        """Extract text and insert into mongo db

        info_level1_filename: str, Filename of info level1. If this parameter
            is not given, bug_info_level1_filename will be fetched from
            config file
        """

        import pymongo
        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        from ir_gnome_st_tools import IRSTTools
        # get config
        bug_id_name = IRConfig.get_instance().get('bug_id_name', 'bug_id')
        summary_name = IRConfig.get_instance().get('bug_summary_name', 'summ')
        description_name = IRConfig.get_instance().get('bug_description_name', 'desc')
        stacktrace_name = IRConfig.get_instance().get('bug_stacktrace_name')
        create_ts_name = IRConfig.get_instance().get('bug_create_ts_name')
        product_name = IRConfig.get_instance().get('bug_product_name')
        # collections
        collection = IRCollection(
            'bug_db_name', 'bug_text_collection_name', 'w')
        collection_basic = IRCollection(
            'bug_db_name', 'bug_basic_collection_name', 'w')
        community_name = IRConfig.get_instance().get('community')
        
        # load and insert text file
        if None == info_level1_filename :
            info_level1_filename = IRConfig.get_instance().\
                    get('bug_info_level1_filename')
        in_file = open(info_level1_filename, 'r')
        
        def func_each_line(line):
            bug_id, summary, description, resolution, create_ts, product = \
                    cls.__extract_information_from_info_level1_line(line)
            
            if resolution is not None and resolution != "INCOMPLETE":
                # post process description
                description, stacktrace = \
                        cls.extract_raw_description_info(description,
                                                         community_name)
                # drop the report whose description containing stacktrace info
                if cls.is_drop_report(description):
                    from ir_log import IRLog
                    IRLog.get_instance().println('Drop report#=%d because it '\
                            'contains unrecognizable stacktrace.' % bug_id, 3)
                    return
                
                collection.insert({ bug_id_name : bug_id,
                                    summary_name: summary,
                                    description_name : description,
                                    stacktrace_name : stacktrace })
                collection_basic.insert({ bug_id_name : bug_id,
                                          create_ts_name : create_ts,
                                          product_name : product })
        IRProgressBar.execute_iteration_for_file(in_file, func_each_line,
                                                 "Parsing Infolevel 1")
        in_file.close()
        collection.create_index([(bug_id_name, IRCollection.ASCENDING)])
        collection_basic.create_index([ (bug_id_name, IRCollection.ASCENDING),
                                        (create_ts_name, IRCollection.ASCENDING),
                                        (product_name, IRCollection.ASCENDING) ])
        collection.close()
        collection_basic.close()
    
    @classmethod
    def is_drop_report(cls, description):
        return cls.get_drop_report_regexp().search(description) is not None

    @classmethod
    def get_drop_report_regexp(cls):
        if cls.__drop_report_regexp == None:
            import re
            from ir_config import IRConfig
            drop_regexp = IRConfig.get_instance().get('drop_report_regexp')
            cls.__drop_report_regexp = re.compile(drop_regexp)
        return cls.__drop_report_regexp


    @classmethod
    def extract_raw_description_info(cls, description, community_name = None):
        """Extract natural language section and other sections from description.

        Args:
            raw_description: str, Raw description

        Returns:
            [str, str], [natural section, stacktrace section]
        """
        from ir_gnome_st_tools import IRSTTools
        if community_name is None:
            from ir_config import IRConfig
            community_name = IRConfig.get_instance().get('communtiy')
        if community_name == 'gnome':
            return IRSTTools.filter(description)
        else:
            return [description, []]

    @classmethod
    def __extract_information_from_info_level1_line(cls, line):
        """Extract information in need (they're summary and description by far) 
            from line.

        Args:
            line: str, A line in info_level0
        
        Returns: 
            (int, str, str, str, int, str), \
                    (bug_id, summary, description, resolution, \
                    create_ts, product)
        """

        fields = line.split(";")[1:]
        # Review: I suppose it might not be an efficient way to find summary
        #   and description. Maybe you can try to scan through the fields and 
        #   break when summary and description are found?
        info = { field.split("=")[0]:field.split("=")[1] for field in fields}
        bug_id_tag = 'Bug#'
        description_tag = "long:1:text"
        summary_tag = "short_desc"
        resolution_tag = "resolution"
        product_tag = "product"
        create_ts_tag = "creation_ts"
        
        bug_id = int(cls.__try_get(info, bug_id_tag, '-1'))

        if bug_id == 476547:
            print 'here'

        create_ts = int(cls.__try_get(info, create_ts_tag, '0'))
        product = cls.__try_get(info, product_tag, '').lower()
        resolution = cls.__try_get(info, resolution_tag, None)
        
        summary = cls.__try_get(info, summary_tag, '')
        summary = cls.__change_special_character(summary).lower()
        description = cls.__try_get(info, description_tag, '')
        description = cls.__change_special_character(description).lower()
        
        return bug_id, summary, description, resolution, create_ts, product

    @classmethod
    def parse_dump_file(cls, dump_filename = None):
        """Extract text from mysql dump and insert into mongo db

        dump_filename: str, Filename of dump file. If this parameter
            is not given, dump_filename will be fetched from
            config file
        """

        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection

        # get key name
        bug_id_name = IRConfig.get_instance().get('bug_id_name', 'bug_id')
        summary_name = IRConfig.get_instance().get('bug_summary_name', 'summ')
        description_name = IRConfig.get_instance().get('bug_description_name', 'desc')
        # collection
        collection = IRCollection(
            'bug_db_name', 'bug_text_collection_name', 'w')

        # load and insert text file
        if None == dump_filename :
            dump_filename = IRConfig.get_instance().\
                    get('bug_dump_text_filename')
        in_file = open(dump_filename, 'r')
        
        def iter_for_line(line):
            bug_id, summary, description = \
                    cls.__extract_summary_and_description_from_dump_file_line(line)
            collection.insert({ bug_id_name : int(bug_id),
                                summary_name: summary,
                                description_name : description }) 
        IRProgressBar.execute_iteration_for_file(in_file, iter_for_line,
                                                 'Parsing Dump')
        in_file.close()
        collection.create_index([(bug_id_name, IRCollection.ASCENDING)])
        collection.close()

    @classmethod
    def parse_dump_basic_file(cls, dump_filename = None):
        # Not finished yet
        """Extract basic information mysql dump and insert into mongo db

        dump_filename: str, Filename of dump file. If this parameter
            is not given, dump_filename will be fetched from
            config file
        """

        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection


        bug_id_name = IRConfig.get_instance().get('bug_id_name', 'bug_id')
        product_name = IRConfig.get_instance().get('bug_product_name', 'product')
        create_ts_name = IRConfig.get_instance().get('bug_create_ts_name', 'ts')

        collection = IRCollection(
            'bug_db_name', 'bug_basic_collection_name', 'w')

        # load and insert text file
        if None == dump_filename :
            dump_filename = IRConfig.get_instance().\
                    get('bug_dump_basic_filename')
        in_file = open(dump_filename, 'r')
        
        def iter_for_line(line):
            # TODO here
            bug_id, product, ts = cls.__extract_basic_from_dump_file_line__(line)

            collection.insert({ bug_id_name : int(bug_id),
                                product_name: product,
                                create_ts_name : int(ts) })

        IRProgressBar.execute_iteration_for_file(in_file, iter_for_line,
                                                 'Parsing Dump Basic')
        in_file.close()
        collection.create_index([(bug_id_name, IRCollection.ASCENDING)])
        collection.close()

    @classmethod
    def __try_get(cls, diction, key, backup):
        """Try to get diction[key]. If key is not in diction, return backup.

        Args:
            diction: dict
            key: object
            backup: object

        Returns:
            object
        """
        if diction is None or not key in diction:
            return backup
        else:
            return diction[key]

    @classmethod
    def __extract_summary_and_description_from_dump_file_line(cls, line):
        """Extract summary and description from line.

        Args:
            line: str, A line of dump_file
        
        Returns: 
            [int, str, str], [bug_id, summary, description]
        """

        fields = line.split("|")
        bug_id = fields[0]
        summary = cls.__change_special_character(fields[1])
        description = cls.__change_special_character(fields[2])
        
        return bug_id, summary, description


    @classmethod
    def __extract_basic_from_dump_file_line__(cls, line):
        line = line.strip()
        fields = line.split("|")
        return fields[0], fields[1], fields[2]
    
    @classmethod
    def __change_special_character(cls, text):
        """
        Convert html character encoding to plain text encoding.
        
        Args:
            text: str
        
        Returns:
            str, the converted string
        """

        text = text.replace("NEWLINE", "\n")
        text = text.replace("SEMICOLON", ';')
        text = text.replace("EQUAL", ';')
        text = text.replace("&quot;","\"")
        text = text.replace("&apos;","\'")
        text = text.replace("&lt;","<")
        text = text.replace("&gt;",">")
        text = text.replace("&amp;","&")
        
        return text

if __name__ == '__main__':
    import sys
    from ir_log import IRLog
    from ir_config import IRConfig

    config = sys.argv[1]
    mode = sys.argv[2]
    IRLog.get_instance().start_log()
    IRConfig.get_instance().load(sys.argv[1])
    if mode == 'level1':
        info_level1_filename = None
        if sys.argv.__len__() >= 2:
            info_level1_filename = sys.argv[3]
        IRText.parse_info_level1(info_level1_filename)
    elif mode == 'sqltext':
        dump_file = None
        if sys.argv.__len__() >= 2:
            dump_file = sys.argv[3]
        IRText.parse_dump_file(dump_file)
    elif mode == 'sqlbasic':
        dump_file = None
        if sys.argv.__len__() >= 2:
            dump_file = sys.argv[3]
        IRText.parse_dump_basic_file(dump_file)
    else:
        IRLog.get_instance().println("Error parameter %s" % mode)
    IRLog.get_instance().stop_log()
    
