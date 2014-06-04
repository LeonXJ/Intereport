#!/usr/bin/python2.7
"""
Author:
    Jialiang Xie
Date:
    2013-12-27
"""

class TestBase(object):
    """
    The base class of Nose tester.
    """

    def setUp(self):
        import sys
        sys.path.append('../bin/')
