"""
ir_template_tools.py

IR Gnome Template tools

IRTemplateTools filter out the known template
"""

__author__ = 'Qimu Zheng'
__date__ = '2014-3-4'

class IRTemplateTools(object):
    """
    Interface provided:
    filter
    """

    to_filter = [  r"what were you doing when the application crashed\?",
                   r"version:",
                   r"description:",
                   r"distribution:",
                   r"package:",
                   r"severity:",
                   r"priority:[^\n]*\n",
                   r"gnome-distributor:",
                   r"version:",
                   r"synopsis:",
                   r"bugzilla-product:",
                   r"bugzilla-component:[^\n]*\n",
                   r"bugzilla-version:",
                   r"description:",
                   r"description of problem:",
                   r"description of the crash:",
                   r"steps to reproduce",
                   r"additional information:",
                   r"unknown reporter: [^,]*, changed to [^\.]*\.",
                   r"setting qa contact to the default for this product.",
                   r"this bug either had no qa contact or an invalid one."
                ]
    compiled_filter = None

    @classmethod
    def get_compiled_filter(cls):
        if cls.compiled_filter is None:
            import re
            cls.compiled_filter = [ re.compile(template, re.I) \
                    for template in cls.to_filter]
        return cls.compiled_filter

    @classmethod
    def filter(cls, text):
        compiled_filter = cls.get_compiled_filter()
        for template in compiled_filter:
            text = template.sub(' ', text)
        return text
        
