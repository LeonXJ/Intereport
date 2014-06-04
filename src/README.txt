Intereport Readme
by Leon Xie and Qimu Zheng
==================================
1. Introduction
Intereport is a project aim to provide interactive bug report experience
via machine learning approaches

2. Directory Layout
1) ./data, its sub-folder should be project name, e.g.:
	./data/mozilla
2) ./bin, put scripts here
3) ./test, put nose test scripts here

3. Code Snippets
1) Config and output log
You can decide the way of logging. To config log output, you can access IRLog
Singleton at the beginning of your entrance script:
'''
from ir_log import IRLog
IRLog.get_instance().set_logfile('../data/log.log')
IRLog.start_log()
...
IRLOG.stop_log()
'''
Then, you can use the log system anywhere by:
'''
IRLog.get_instance().println('This is a log information', 2)
'''
The second parameter stands for the logging level. While it is quite arbitary,
we recommend to use 0 for routine log (e.g., db open), 1 for task related log
(e.g., progress report), 2 for high level abstraction of level 1 (e.g., precison,
recall).

2) Show your Progress
You can use IRProgressBar to present your progress once you start IRLog
system.
'''
from ir_log import IRProgressBar
progress_bar = IRProgressBar(1000, 'Progress', False, 0, 1)
for i in range(1,1001):
    progress_bar.set_value(i)
'''
In the constructor, the first parameter represents the max value, the second
is the title of your ProgressBar, the third decides whether to use verbose
mode (output the progress everytime you call set_value()), the forth tells the
digitals of percentage (e.g., 0 for 10% and 1 for 10.2%). Outside verbose mode,
the progress will not be printed if the digitals of precentage dosen't change.
The last parameter is log level.

3) Get Config
With IRConfig, you can get config anywhere. To use IRConfig, at the entrance
of your script:
'''
from ir_config import IRConfig
IRConfig.get_instance().load('../data/test/bug_test.cfg')
'''
Then, you can freely access to the config:
'''
str_config = IRConfig.get_instance().get('name_of_config', 'values_if_not_found')
int_config = IRConfig.get_instance().get('name_of_int', 88)
'''
The second paremeter is not compulsary. In that case, IRConfig returns None if
the config can not be found.
Note: IRConfig can also be used to keep global varibles (not recommend):
'''
IRConfig.get_instance().set('varible_name_in_str', '343')
int_var = IRConfig.get_int('varible_name_in_str')
'''
4) Access Mongodb
IRMongodbHelper helps you access mongodb anywhere:
'''
from ir_mongodb_helper import IRMongodbHelper
connection = IRMongodbHelper.get_instance().get_connection()
collection =
IRMongodbHelper.get_instance().get_collection('db_name_in_config_file',
'collection_name_in_config_file', False)
'''
The last paremeter of get_collection tells whether to drop the existing
collection. Use True if you wanna create a new collection.


