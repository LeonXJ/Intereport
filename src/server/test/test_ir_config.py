__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2013-12-30'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-13'

from test_base import TestBase

class TestIRConfig(TestBase):
    """
    Test IR Config System. Executed by Nose.
    """

    def test_config(self):
        import ir_config as config

        # get IRConfig instance
        fig = config.IRConfig.get_instance()
        assert fig is not None

        # load from config file
        # create config file
        config_file = 'test_ir_config.cfg'
        out_file = open(config_file, 'w+')
        # string
        string_key = 'string_key'
        string_value = 'a brown fox jumps over a lazy dog.'
        out_file.write('%s:=%s\n' % (string_key, string_value))
        # int
        int_key = 'int_key'
        int_value = 960
        out_file.write('%s:=%d\n' % (int_key, int_value))
        # float
        float_key = 'float key'
        float_value = 3.14159
        out_file.write('%s:=%f\n' % (float_key, float_value))
        # bool
        bool_key = 'bool_key'
        bool_value = True
        out_file.write('%s:=%d\n' % (bool_key, bool_value))
        # comment
        out_file.write('#this is a comment\n')
        out_file.write('     #this is also a comment\n')
        # illegal line
        out_file.write('this line is illegal\n')
        out_file.close()
        # load and test
        fig.load(config_file)
        assert string_value == fig.get(string_key)
        assert int_value == fig.get_int(int_key)
        assert float_value == fig.get_float(float_key)
        assert bool_value == fig.get_bool(bool_key)
        # clean up
        import os
        os.remove(config_file)

        # test set and get value
        set_key = 'set_key'
        set_value = 'set_value'
        fig.set(set_key, set_value)
        assert fig.get(set_key) == set_value
