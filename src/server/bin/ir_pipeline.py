#!/usr/bin/python2.7
"""
Author:
    Xie Jialiang
Date:
    2014-1-21
Usage:
    python2.7 ir_pipeline [config file]
"""

class IRArtifact(object):
    """
    Represents a file or a collection in mongodb.
    This class provide Makefile-like functions. Use get_artifact() to auto \
            update all its dependencies and get the updated version of the 
            artifact.
    How to use:
    1) define dependencies and generate rule in the constructor.
    2) call get_artifact() to get updated version of the artifact.
    """

    def __init__(self, id, dependencies=None, action=None):
        """
        id: the id for the artifact. see the derivertives.
        dependencies: the artifacts being depended by this one.
        action: the function to generate this artifact.
        """
        if not dependencies: dependencies = []

        self.id = id
        self.dependencies = {}
        for dependency in dependencies:
            self.dependencies[dependency.id] = dependency
        self.action = action

    def is_success(self):
        """
        virtual. if this artifact was generated correctly.
        """
        
        return True

    def get_modified_time(self):
        """
        virtual. get the time the current artificat being modified.
        """
        
        return 0

    def get_artifact(self):
        """
        Check whether all the dependencies are updated. (If not, update
            the dependencies recursively)
        Check whether this artifact needs updating.
        """

        # get all the dependencies
        for key, value in self.dependencies.items():
            value.get_artifact()
        # need update ?
        if self.action is not None and self.__need_update():
            self.action()
            if not self.is_success():
                from ir_log import IRLog
                IRLog.get_instance().println("Fail to generate %s." % self.id)
                assert False

    def __need_update(self):
        """
        Check if this artifact needs updating.
        if this artifact is newer than all its dependencies, return False.
        else, True.
        """

        from ir_log import IRLog
        if not self.is_success():
            return True
        # out_file is success here
        ts_out = self.get_modified_time()
        if ts_out is None:
            return True
        # ts_out != None
        last_ts_in = ts_out - 10 # assume we do not need to update
        for key, value in self.dependencies.items():
            IRLog.get_instance().println("%s %d <- %s %d" % \
                    (self.id, ts_out, key, value.get_modified_time()))
            last_ts_in = max(last_ts_in, value.get_modified_time())
        return last_ts_in > ts_out

class IRFile(IRArtifact):
    """
    """

    def __init__(self, id, dependencies, action):
        """
        id: the filename (including path) of the file in config file.
        """

        from ir_config import IRConfig
        IRArtifact.__init__(self, IRConfig.get_instance().get(id),
                            dependencies, action)
        

    def is_success(self):
        """
        Take it as success if the file exists.
        """

        import os
        if os.path.exists(self.id):
            return True
        else:
            return False

    def get_modified_time(self):
        """
        get the time of the modification.
        Return: if filename exists, return the time in 
            seconds since 1970.
                else, return None
        """

        if self.is_success():            
            import os
            return os.path.getmtime(self.id)
        else:
            return -1

class IRCollection(IRArtifact):
    """
    """

    def __init__(self, id, dependencies, action):
        """
        id: the name of the collection in config file.
        """
        
        IRArtifact.__init__(self, id, dependencies, action)

    def is_success(self):
        ts, success = self.__get_collection_status()
        return success

    def get_modified_time(self):
        ts, success = self.__get_collection_status()
        return ts
        
    def __get_collection_status(self):
        from ir_config import IRConfig
        from ir_mongodb_helper import IRMongodbHelper
        db_name = IRConfig.get_instance().get('bug_db_name')
        ts, success = IRMongodbHelper.get_instance().get_collection_status(
                'bug_db_name', self.id)
        return ts, success

class IRPipeline(object):
    """
    Pipeline
    """
    @classmethod
    def do_remove_bad_reports(cls, config_file):

        from ir_log import IRLog
        from ir_log import IRProgressBar
        from ir_config import IRConfig
        import ir_mongodb_helper
        from ir_text import IRText

        
        config = IRConfig.get_instance()
        config.load(config_file)
        bug_id_name = config.get('bug_id_name')
        bug_description_name = config.get('bug_description_name')
        text_cursor = IRText.get_iterator(None)
        remove_ids = []
        def iter_text(item):
            if IRText.is_drop_report(item[bug_description_name]):
                remove_ids.append(item[bug_id_name])
                IRLog.get_instance().println('Remove report#=%d' % item[bug_id_name], 3)
        IRProgressBar.execute_iteration_for_cursor(text_cursor, iter_text)

        # remove from all database
        def remove_from_collection(collection_cfg_name):
            collection =ir_mongodb_helper.IRCollection( \
                'bug_db_name', collection_cfg_name, 'a')
            collection.remove({'bug_id':{'$in':remove_ids}})
            collection.close()

        remove_from_collection('bug_text_collection_name')
        remove_from_collection('bug_tfidf_collection_name')
        remove_from_collection('bug_duplicate_collection_name')
    
    @classmethod
    def do_gnome_preprocess(cls, cfg_file_name):
        """
        """

        from ir_log import IRLog
        from ir_config import IRConfig

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load(cfg_file_name)

        cfgfile = IRFile('cfg_file_name', {}, None)
        
        infolevel1 = IRFile(
            'bug_info_level1_filename', {}, None)
        from ir_text import IRText
        exetext = IRFile('exe_text', {}, None)
        text = IRCollection("bug_text_collection_name",
                            [exetext, cfgfile, infolevel1], IRText.parse_info_level1)
        
        from ir_term_count import IRTermCount
        exetermcount = IRFile('exe_term_count', {}, None)
        termcount = IRCollection("bug_termcount_collection_name",
                                 [exetermcount, cfgfile, text], IRTermCount.batch_generate_term_count)
        
        from ir_document_count import IRDocumentCount
        exedocumentcount = IRFile('exe_document_count', {}, None)
        documentcount = IRCollection("bug_documentcount_collection_name",
                                     [exedocumentcount, cfgfile, termcount], IRDocumentCount.batch_generate_document_count)
        
        from ir_tfidf import IRTFIDF
        exetfidf = IRFile('exe_tfidf', {}, None)
        tfidf = IRCollection("bug_tfidf_collection_name",
                             [exetfidf, cfgfile, termcount, documentcount], IRTFIDF.batch_generate_tfidf)
        
        infolevel0 = IRFile('bug_info_level0_filename', {}, None)
        from ir_duplicate_group import IRDuplicateGroup
        exeduplicategroup = IRFile('exe_duplicate_group', {}, None)
        duplicategroup = IRCollection("bug_duplicate_group_count_collection_name",
                                      [exeduplicategroup, cfgfile, infolevel0], IRDuplicateGroup.parse_info_level0)
        
        tfidf.get_artifact()
        duplicategroup.get_artifact()

    @classmethod
    def do_mozilla_preprocess(cls, cfg_file_name):
        """
        """

        from ir_log import IRLog
        from ir_config import IRConfig

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load(cfg_file_name)

        cfgfile = IRFile('cfg_file_name', {}, None)

        dump_text = IRFile(
            'bug_dump_text_filename', {}, None)

        from ir_text import IRText
        exetext = IRFile('exe_text', {}, None)
        text = IRCollection("bug_text_collection_name",
                            [exetext, cfgfile, dump_text], IRText.parse_dump_file)

        from ir_term_count import IRTermCount
        exetermcount = IRFile('exe_term_count', {}, None)
        termcount = IRCollection("bug_termcount_collection_name",
                                 [exetermcount, cfgfile, text], IRTermCount.batch_generate_term_count)

        from ir_document_count import IRDocumentCount
        exedocumentcount = IRFile('exe_document_count', {}, None)
        documentcount = IRCollection("bug_documentcount_collection_name",
                                     [exedocumentcount, cfgfile, termcount], IRDocumentCount.batch_generate_document_count)

        from ir_tfidf import IRTFIDF
        exetfidf = IRFile('exe_tfidf', {}, None)
        tfidf = IRCollection("bug_tfidf_collection_name",
                             [exetfidf, cfgfile, termcount, documentcount], IRTFIDF.batch_generate_tfidf)

        basic = IRFile('bug_dump_basic_filename', {}, None)
        from ir_duplicate_group import IRDuplicateGroup
        exeduplicategroup = IRFile('exe_duplicate_group', {}, None)
        duplicategroup = IRCollection("bug_duplicate_group_count_collection_name",
                                      [exeduplicategroup, cfgfile, basic], IRDuplicateGroup.parse_dump_dup_file)

        tfidf.get_artifact()
        duplicategroup.get_artifact()

if __name__ == '__main__':
    import sys
    if sys.argv[1] == "gnome":
        IRPipeline.do_gnome_preprocess(sys.argv[2])
    elif sys.argv[1] == "mozilla":
        IRPipeline.do_mozilla_preprocess(sys.argv[2])
    elif sys.argv[1] == "clean":
        IRPipeline.do_remove_bad_reports(sys.argv[2])
