#!/usr/bin/python2.7
"""
Author:
    Jialiang Xie
Date:
    2014-3-5
"""

from test_base import TestBase

class TestIRSentence(TestBase):
    """
    Test IR Sentence. Executed by Nose.
    """

    def test_create_new_sentence(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_sentence import IRSentence

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        bug_id = 10000
        description_text = 'When I was openning history folder, the f**king' \
                ' Firefox just crashed!'
        sent = IRSentence(description_text, bug_id)
        assert description_text == sent.get_text()
        assert bug_id == sent.get_bug_id()
        assert sent.contain_term('folder')
        sent.get_termcount()
        sent.get_tfidf()
        IRLog.get_instance().stop_log()

    def test_get_sentence_from_description(self):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_sentence import IRSentence

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        bug_id = 10000
        description = 'Version: 12.43\n'\
                      'Distribution: Gnome 12.03\n'\
                      '\n'\
                      'Steps to repreduce:\n'\
                      '1. Open firefox.\n'\
                      '2. Click Option\n'\
                      '3. Open firefox\n'\
                      '\n'\
                      'Additional information:\n'\
                      'This is really crazy when it crashed.'
        IRLog.get_instance().println('Description: %s' % (description))
        sentences = IRSentence.get_sentence_from_description(description, bug_id)
        for sentence in sentences:
            IRLog.get_instance().println('S1: %s' % (sentence.get_text()))

    def test_cluster_sentences(test):
        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_sentence import IRSentence

        IRLog.get_instance().start_log()
        IRConfig.get_instance().load('../data/test/bug_test.cfg')
        bug_id = 10000
        description = 'Version: 12.43\n'\
                      'Distribution: Gnome 12.03\n'\
                      '\n'\
                      'Steps to repreduce:\n'\
                      '1. Open firefox.\n'\
                      '2. Click Option\n'\
                      '3. Open firefox\n'\
                      '\n'\
                      'Additional information:\n'\
                      'This is really crazy when it crashed.'
        sentences = IRSentence.get_sentence_from_description(description, bug_id)
        group_id, selected_id = IRSentence.cluster_sentences(sentences, 3)
        groups = []
        for i in range(3):
            groups.append([])
        index = 0
        for id in group_id:
            groups[id].append(index)
            index += 1
        index = 0
        for group in groups:
            IRLog.get_instance().println('Group %d. Representative: %s' % \
                    (index, sentences[selected_id[index]].get_text()))
            for id in group:
                IRLog.get_instance().println(sentences[id].get_text())
            index += 1
