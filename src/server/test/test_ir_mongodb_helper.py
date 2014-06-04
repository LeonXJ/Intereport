__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2013-12-30'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-13'


from test_base import TestBase

class TestMongodbHelper(TestBase):
    """
    Test IR Mongodb Helper. Executed by Nose.
    """

    def test_dbhelper(self):
        from ir_mongodb_helper import IRMongodbHelper

        dbhelper = IRMongodbHelper.get_instance()
        assert dbhelper is not None

        # insert test db into mongodb
        con = dbhelper.get_connection()
        assert con is not None

    def test_get_collection_status(self):
        
        from ir_config import IRConfig
        from ir_mongodb_helper import IRMongodbHelper
        dbhelper = IRMongodbHelper.get_instance()


        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        collection = dbhelper.get_collection(
            'bug_db_name',
            'bug_mongodb_helper_collection_name',
                True)
        ts, success = dbhelper.get_collection_status(
            'bug_db_name',
            'bug_mongodb_helper_collection_name')
        assert success == False

        db_name = IRConfig.get_instance().get('bug_db_name')
        collection_name = IRConfig.get_instance(). \
                get('bug_mongodb_helper_collection_name')
        dbhelper.update_meta( db_name, collection_name, True)
        ts, success = dbhelper.get_collection_status(
            'bug_db_name',
            'bug_mongodb_helper_collection_name')
        assert success == True

    def test_ir_collection(self):

        from ir_mongodb_helper import IRCollection
        from ir_config import IRConfig
        import pymongo

        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        db_cfg_name = 'bug_db_name'
        collection_cfg_name = 'bug_mongodb_helper_collection_name'
        # create empty collection
        ircollection = IRCollection(db_cfg_name, collection_cfg_name, 'w')
        assert None != ircollection
        ircollection.insert({'abc':'abc'})
        ircollection.close()
        
        # access existing collection
        ircollection = IRCollection(db_cfg_name, collection_cfg_name, 'r')
        assert None != ircollection
        ircollection.close()
        # test result
        connection = pymongo.Connection(IRConfig.get_instance().get('db_host'),
                                        IRConfig.get_instance().get_int('db_port'))
        db_name = IRConfig.get_instance().get(db_cfg_name)
        collection_name = IRConfig.get_instance().get(collection_cfg_name)
        assert connection[db_name][collection_name].find({'abc':'abc'}).count() > 0

        ircollection = IRCollection(db_cfg_name, collection_cfg_name, 'w')
        ircollection.clean()
        ircollection.close()
