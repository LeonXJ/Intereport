"""Logging system for outputing and tracing

IRLog (Singleton) is the agent of logging. It can output to file and/or stdout.

For example:
    irlog = IRLog.get_instance()
    irlog.get_instance().start_log(True, 'log.txt')
    irlog.get_instance().println('IRLog outputs')

    prgbar = IRProgressBar(1000)
    prgbar.set_value(250)
    prgbar.set_value(1000)
    
    irlog.get_instance().stop_log()
"""

__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2013-12-27'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-13'

class IRLog(object):
    """
    Log system as Singleton.
    IRLog should not depend on other modules.
    """

    __ir_log = None

    @classmethod
    def get_instance(cls):
        if cls.__ir_log is None:
            cls.__ir_log = IRLog()
        return cls.__ir_log

    def __init__(self):
        self.__is_stdout = True
        self.__logfile = None
        self.__logio = None

    # Deprecated
    def set_stdout(self, is_stdout):
        """Set whether output to stdout.

        Args:
            is_stdout: boolean, Output to stdout?
        """
        self.__is_stdout = is_stdout

    # Deprecated
    def set_logfile(self, logfile):
        """Set log file. Should be called before start_log.
        
        Args:
            logfile: str, The path of log file.
        """
        self.__logfile = logfile

    def start_log(self, is_stdout = True, logfile = None):
        """Start logging.
        
        Args:
            is_stdout: boolean, If print to standard ouput.
            logfile: str, The path of log file.

        """
        if self.__logio is not None:
            print 'Error: starting log more than once.'
            assert False
        self.__is_stdout = is_stdout
        self.__logfile = logfile
        if self.__logfile is not None:
            self.__logio = open(self.__logfile, 'w')

    def stop_log(self):
        """Stop logging."""
        if self.__logio is not None:
            self.__logio.close()
            self.__logio = None

    def println(self, msg, msg_level = 0):
        """Print a line. Should be called between start_log() and stop_log().

        Args:
            msg: str, Information to be printed.
            msg_level: int, Importance.
        """
        content = '[level %d] %s' % (msg_level, msg)
        if self.__is_stdout:
            print content
        if self.__logio is not None:
            self.__logio.write(content + '\n')

class IRProgressBar(object):
    """
    Show the progress. It should be used in the closure of
        IRLog.get_instance().start_log() and IRLog.get_instance().end_log().
    The progress bar will be shown as: 
        [[caption] [percent with digital]% [current_value]/[max_value]]
    For example: 
        [loading 34.50% 345/10000]
    """
    
    __epsilon = 0.00001

    def __init__(self, max_value, caption = '', verbose = False, digital = 0,
                 msg_level = 0):
        """Constructor.
        
        Args:
            max_value: int, The max value of the progress bar.
            caption: str, The caption of the progress bar.
            verbose: boolean, If False, the output of set_value() which 
                produces the same rounded percentages will be suppressed.
            digital: int, The precision of progress being displayed.
        """
        self.__max_value = max_value
        self.__verbose = verbose
        self.__digital = digital
        self.__current_value = 0.0
        self.__current_percent = 0.0
        self.__caption = caption
        self.__msg_level = msg_level

    def set_value(self, value):
        """Set progress.

        Args:
            value: int, The progress within [0, max_value]
        """
        self.__current_value = value
        new_percent = round(float(self.__current_value) * 100.0 / self.__max_value,
                            self.__digital)
        if self.__verbose == True or (new_percent - self.__current_percent) ** 2 > self.__epsilon:
            IRLog.get_instance().println(
                '[%s %f%%, %f/%f]' % (self.__caption, new_percent,
                                      self.__current_value, self.__max_value),
                self.__msg_level)
            self.__current_percent = new_percent

    @classmethod
    def execute_iteration_for_cursor(cls, cursor, func,
                                     title = '', verbose = False, msg_level = 0):
        """Apply func through cursor"""
        if cursor is None:
            return
        cls.__execute_iteration(cursor, func, cursor.count(),
                                title, verbose, msg_level)

    @classmethod
    def execute_iteration_for_file(cls, infile, func,
                                   title = '', verbose = False, msg_level = 0):
        if infile is None:
            return
        line_count = sum(1 for line in infile)
        infile.seek(0)
        cls.__execute_iteration(infile, func, line_count,
                                title, verbose, msg_level)

    @classmethod
    def execute_iteration_for_dict(cls, dictionary, func,
                                   title = '', verbose = False, msg_level = 0):
        if dictionary is None:
            return
        cls.__execute_iteration(dictionary, func,
                                dictionary.__len__(), title, verbose, msg_level)

    @classmethod
    def __execute_iteration(cls, iterator, func,
                            size, title, verbose, msg_level):
        bar = IRProgressBar(size, title, verbose, msg_level)
        prg = 0
        for ele in iterator:
            prg += 1
            bar.set_value(prg)
            func(ele)

