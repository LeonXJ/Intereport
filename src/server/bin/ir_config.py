"""Config agent for loading and setting global configuration.

IRConfig load configuration from file. It can be accessed anywhere. The config
file should be like:

    database_name:=mongodb_test
    # this is a comment line

Any line which violates the format will be ignored.
To load the config file:

    config = IRConfig.get_instance()
    config.load('config.cfg')
    db_name = config.get('database_name')
    config.set('global_var', 12)
    var = config.get('global_var')
"""

__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2013-12-27'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-13'

class IRConfig(object):
    """Config Agent."""

    __ir_config = None

    @classmethod
    def get_instance(cls):
        if cls.__ir_config is None:
            cls.__ir_config = IRConfig()
        return cls.__ir_config

    def __init__(self):
        self.__config = {}

    def load(self, config_file):
        """Load config from config_file.

        Args:
            config_file: str, Filepath of config file.
        """
        from ir_log import IRLog
        in_file = open(config_file)
        line_num = 0
        for line in in_file:
            line = line.strip()
            # '#' for comment
            if line[0] == '#':
                continue
            fields = line.split(':=')
            line_num += 1
            if fields.__len__() !=  2:
                IRLog.get_instance().println('Load config file error: %s, in ' \
                        'line %d: %s' % (config_file, line_num, line))
                continue
            else:
                self.__config[fields[0]] = fields[1]

    def set(self, name, value):
        """Set global variable.

        Args:
            name: str, Name of variable.
            value: object, The value of variable.
        """
        self.__config[name] = value

    def get(self, name, default_value = None):
        """Get the variable with the given name.
        
        Args:
            name: str, Name of the variable.
            default_value: object, Backup value, see Returns

        Returns:
            object, if variable with the given name is found, return the 
                variable. if the name is not found, return default_value if
                default_value != None. Otherwise, throw exception.
        """
        if name in self.__config:
            return self.__config[name]
        else:
            if None != default_value:
                return default_value
            else:
                assert ( None != self.__config[name]) or (None != default_value)

    def get_int(self, name, default_value = None):
        """Get the int value with the given name."""
        try:
            res = self.get(name, default_value)
            return int(res)
        except ValueError:
            from ir_log import IRLog
            IRLog.get_instance().println('Could not convert %d to int.' \
                    % (self.get(name)))
            return default_value

    def get_float(self, name, default_value = None):
        """Get the float value with the given name."""
        try:
            res = self.get(name, default_value)
            return float(res)
        except ValueError:
            from ir_log import IRLog
            IRLog.get_instance().println('Could not convert %d to float.' \
                    % (self.get(name)))
            return default_value

    def get_bool(self, name, default_value = None):
        """Get the boolean value with the given name."""
        try:
            res = self.get(name, default_value)
            return bool(res)
        except ValueError:
            from ir_log import IRLog
            IRLog.get_instance().println('Could not convert %d to bool.' \
                    % (self.get(name)))
            return default_value
