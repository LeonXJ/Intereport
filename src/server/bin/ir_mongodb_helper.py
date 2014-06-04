"""Agent of Mongodb.

IRMongodbHelper is the agent of mongodb. It keeps tracks of the operations
on the database. It provides metadata of collections.

To operate on a collection, you can use IRCollection:
    
    ir_collection = IRCollection('db_cfg_name', 'collection_cfg_name', 'w')
    ir_collection.insert({'bug_id' : 36910})
    ir_collection.close()

    # read database
    ir_collection = IRCollection('db_cfg_name', 'collection_cfg_name', 'r')
    ir_collection.find({'bug_id' : 36910})
    ir_collection.close()

You can check the last modification to the collection:

    last_modified_time, is_succeed = \
        dbhelper.get_collection_status('db_name', 'bug_text_collection_name')

"""

__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2013-12-27'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-17'

class IRMongodbHelper(object):
    """Agent of Mongodb."""

    __ir_mongodb_helper = None
    __default_host = 'localhost'
    __default_port = 27017
    # for meta data
    #   Meta data keeps track of the operation to other collections,
    #   including, time of last modification, if the last modification succeed
    __meta_collection_name = 'meta_data'
    __meta_key_name = 'name'
    __meta_lastmodified_name = 'lastmodified'
    __meta_success_name = 'success'


    @classmethod
    def get_instance(cls):
        if cls.__ir_mongodb_helper is None:
            cls.__ir_mongodb_helper = IRMongodbHelper()
        return cls.__ir_mongodb_helper

    def __init__(self):
        self.__connection = None

    def get_connection(self):
        """Get the connection, using db_host and db_port set in config file."""
        if self.__connection is None:
            import pymongo
            from ir_config import IRConfig
            self.__connection = pymongo.Connection(
                    IRConfig.get_instance().get('db_host', self.__default_host), 
                    IRConfig.get_instance().get_int('db_port', self.__default_port))
        return self.__connection

    # Deprecated
    def get_collection(self, db_cfg_name, collection_cfg_name, is_clean = False):
        """Get a collection. 
        
        Args:
            db_cfg_name: str, Config name of database in config file
            collection_cfg_name: str, Config name of collection_cfg_name in 
                config file. 
            is_clean: boolean, Whether to clean the old collection
                Set the last parameter to True if you wanna drop
        
        Returns:
            Collection, the wanted collection.
        """
        from ir_config import IRConfig
        connection = self.get_connection()
        db_name = IRConfig.get_instance().get(db_cfg_name)
        collection_name = IRConfig.get_instance().get(collection_cfg_name)
        collection = connection[db_name][collection_name]
        if is_clean:
            self.__assert_collection_change(db_cfg_name,
                                            collection_cfg_name, False)
            collection.drop()
        return collection

    # Deprecate
    def assert_modification_intention(self, db_cfg_name, collection_cfg_name):
        """Announce the agent about your intention to modify the collection.

        Args:
            db_cfg_name: str, Config name of database in config file
            collection_cfg_name: str, Config name of collection_cfg_name in 
                config file. 
        """
        return self.__assert_collection_change(db_cfg_name,
                                               collection_cfg_name, False)

    # Deprecate
    def assert_modification_done1(self, db_cfg_name, collection_cfg_name):
        """Tell the agent you've finished modifying.
        
        Args:
            db_cfg_name: str, Config name of database in config file
            collection_cfg_name: str, Config name of collection_cfg_name in 
                config file. 
        """
        return self.__assert_collection_change(db_cfg_name,
                                               collection_cfg_name, True)

    def update_meta(self, db_name, collection_name, is_finished):
        """Tell the agent the collection will be/has been modified.

        Args:
            db_cfg_name: str, Config name of database in config file
            collection_cfg_name: str, Config name of collection_cfg_name in 
                config file. 
            is_finished: boolean, Whether the change is about finished 
                modifying. If not, it is the intention to modify.
        """
        import time
        from ir_config import IRConfig
        meta_collection = self.__get_meta_collection(db_name)
        res = self.__find_collection_in_meta(db_name, collection_name)
        if res.count() > 0:
            meta_collection.update({self.__meta_key_name : collection_name},
                                   {'$set' : {self.__meta_lastmodified_name : int(time.time()),
                           self.__meta_success_name : is_finished}}) 
        else:
            meta_collection.insert({self.__meta_key_name : collection_name,
                                    self.__meta_lastmodified_name : int(time.time()),
                                    self.__meta_success_name : is_finished})


    def __assert_collection_change(self, db_cfg_name, collection_cfg_name, 
                            is_finished):
        """Tell the agent the collection will be/has been modified.

        Args:
            db_cfg_name: str, Config name of database in config file
            collection_cfg_name: str, Config name of collection_cfg_name in 
                config file. 
            is_finished: boolean, Whether the change is about finished 
                modifying. If not, it is the intention to modify.
        """
        import time
        from ir_config import IRConfig
        db_name = IRConfig.get_instance().get(db_cfg_name)
        collection_name = IRConfig.get_instance().get(collection_cfg_name)
        meta_collection = self.__get_meta_collection(db_name)
        res = self.__find_collection_in_meta(db_name, collection_name)
        if res.count() > 0:
            meta_collection.update({self.__meta_key_name : collection_name},
                                   {'$set' : {self.__meta_lastmodified_name : int(time.time()),
                           self.__meta_success_name : is_finished}}) 
        else:
            meta_collection.insert({self.__meta_key_name : collection_name,
                                    self.__meta_lastmodified_name : int(time.time()),
                                    self.__meta_success_name : is_finished})

    def get_collection_status(self, db_cfg_name, collection_cfg_name):
        """
        Get the status of collection.
        
        Args:
            db_cfg_name: str, Config name of database in config file
            collection_cfg_name: str, Config name of collection_cfg_name in 
                config file. 
        
        Return: int, boolean, If exists, return [last modified time, 
            is last modified success], else, return [None, None]
        """
        from ir_config import IRConfig
        db_name = IRConfig.get_instance().get(db_cfg_name)
        collection_name = IRConfig.get_instance().get(collection_cfg_name)
        res = self.__find_collection_in_meta(db_name, collection_name)
        if res.count() > 0:
            return res[0][self.__meta_lastmodified_name], \
                   res[0][self.__meta_success_name]
        else:
            return None, None

    def __find_collection_in_meta(self, db_name, collection_name):
        """Find the information of the collection in meta data.

        Args:
            db_cfg_name: str, Config name of database in config file
            collection_cfg_name: str, Config name of collection_cfg_name in 
                config file. 
        
        Returns:
            Cursor, the cursor of the information of the collection.
        """
        meta_collection = self.__get_meta_collection(db_name)
        return meta_collection.find({self.__meta_key_name : collection_name})
    
    def __get_meta_collection(self, db_name):
        """Get the meta collection.

        Args:
            db_cfg_name: str, Config name of database in config file

        Returns:
            Collection, the meta collection.
        """
        connection = self.get_connection()
        return connection[db_name][self.__meta_collection_name]

class IRCollection(object):

    import pymongo
    ASCENDING = pymongo.ASCENDING

    def __init__(self, db_cfg_name, collection_cfg_name, mode = 'r'):
        """Constructor. Open a collection. 
        Warning: please load config file before do this.

        Args:
            db_cfg_name: str
            collection_cfg_name: str
            mode: str, 'r' for Read, 'w' for Overwrite, 'a' for Append.
        """
        from ir_config import IRConfig
        connection = IRMongodbHelper.get_instance().get_connection()
        self.__db_name = IRConfig.get_instance().get(db_cfg_name)
        self.__collection_name = IRConfig.get_instance().get(collection_cfg_name)
        self.__mode = mode
        self.__collection = connection[self.__db_name][self.__collection_name]
        self.__is_closed = False
        if mode != 'r':
            IRMongodbHelper.get_instance().update_meta(
                self.__db_name, self.__collection_name, False)
        if mode == 'w':
            self.__collection.drop()

    def __del__(self):
        if (self.__mode == 'w' or self.__mode == 'a') \
                and self.__is_closed == False:
            from ir_log import IRLog
            IRLog.get_instance().println('Error! Collection in modifying mode '
                                         'is destoried before being closed.')
            assert False

    def close(self):
        """Close the collection. It is essential for collection 
        in 'w'/'a' mode.
        """
        if self.__mode == 'w' or self.__mode == 'a':
            IRMongodbHelper.get_instance().update_meta(
                self.__db_name, self.__collection_name, True)
        self.__is_closed = True

    def find(self, arg=None):
        if not arg: arg = {}
        self.__is_collection_close()
        return self.__collection.find(arg)
    
    def distinct(self, arg):
        self.__is_collection_close()
        return self.__collection.distinct(arg)

    def insert(self, arg):
        self.__is_modification_legal_in_current_mode()
        self.__collection.insert(arg)

    def update(self, arg):
        self.__is_modification_legal_in_current_mode()
        self.__collection.update(arg)

    def count(self):
        return self.__collection.count()
    
    def create_index(self, arg):
        self.__is_modification_legal_in_current_mode()
        self.__collection.create_index(arg)

    def clean(self):
        self.__is_modification_legal_in_current_mode()
        self.__collection.drop()

    def remove(self, args):
        self.__is_modification_legal_in_current_mode()
        self.__collection.remove(args)

    def __is_modification_legal_in_current_mode(self):
        """Check if current mode supports modifying operation."""
        self.__is_collection_close()
        if self.__mode == 'r':
            from ir_log import IRLog
            IRLog.get_instance().println(
                'Error! Cannot write to collection being opened in read mode.')
            assert False

    def __is_collection_close(self):
        """Check if the operation is conducted after the collection is closed."""
        if self.__is_closed:
            from ir_log import IRLog
            IRLog.get_instance().println(
                'Error! Cannot write to closed collection.')
            assert False

