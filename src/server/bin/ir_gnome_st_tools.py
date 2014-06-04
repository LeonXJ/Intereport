"""
ir_gnome_st_tools.py

IR Gnome stacktrace tools

IRSTTools extracts nature language section and stacktrace section from 
description of bug report. It also compare two stacktraces.
Given a description in str:

    desc1, stacktrace1 = IRSTtools.filter(description1)
    desc2, stacktrace2 = IRSTtools.filter(description2)
    # compare stacktrace
    similarity = IRSTtools.compare_stackinfo(stacktrace1, stacktrace2)

Note that similarity is a float between 0.0 and 1.0
"""

__author__ = 'Qimu Zheng'
__date__ = '2014-2-27'

class IRSTTools(object):
    """
        Stacktrace Tools

        Interfaces provided:

            filter
            compare_stackinfo

    """

    @classmethod
    def filter(cls, text):
        """
        Extrace nature language section and stacktrace section from description
            of bug report.

        Args:
            text: str, All the description
        
        Returns:
            [str, str], [natural language section, stacktrace section]

        """
        import re

        lowered = text.lower()

        # 1. Bugbuddy
        # 370280
        dis = lowered.find("distribution")
        rel = lowered.find("gnome release")
        bby = lowered.find("bugbuddy")
        desc = text
        stacktrace = []

        if dis != -1 and rel != -1 and bby != -1 and rel - dis < 100 and bby - rel < 100:
            stacktrace = lowered[dis:]
            desc = text[:dis]
            return desc, cls.__retrieve_stackinfo__(stacktrace)


        # 2. Bugzilla gnome template (?)
        # E.g.  94625 101700
        # Important template!
        if lowered.find("package") != -1 and lowered.find("version")!= -1\
          and lowered.find("synopsis") != -1 and lowered.find("debugging information")!= -1:
            pos = lowered.find("debugging information")
            desc = text[:pos]
            stacktrace = lowered[pos:]
            return desc, cls.__retrieve_stackinfo__( stacktrace)

        # 3. 662101 666515 Unknown Template
        stack_pattern = re.compile(r"thread \d+ \(thread")
        result = stack_pattern.search(lowered)
        if result is not None:
            pos = result.start()
            desc = text[:pos]
            stacktrace = []
            return desc, stacktrace
        
        return desc,stacktrace

    @classmethod
    def __retrieve_stackinfo__(cls, all_info):
        """
        Retrieve stacktrace information in a naive way

        Args:
            All the bugbuddy information
        Output:
            [
                [fun1, fun2, fun3] # function name in this thread  
                [fun1, fun2, fun3]
                [fun1, ...]
            ]

        """
        if all_info is None:
            return []

        if all_info.find("traceback (most recent call last)") != -1:
            return cls.__retrieve_pystack__(all_info)


        start = all_info.find("\n#")
        stacktrace = all_info[start:]
        threads = stacktrace.split("\n\n")

        from ir_config import IRConfig
        algorithm = IRConfig.get_instance().get(
            'stacktrace_algorithm', 'weight')
        if algorithm == 'signal':
            info = [cls.__retrieve_trace_signal__(threads)]
        else:
            info = map(cls.__retrieve_trace__, threads)
        return info

    @classmethod
    def __retrieve_pystack__(cls, all_info):
        # Extract the stacktrace for python program failure
        start = all_info.find("traceback (most recent call last)")
        stack = all_info[start:]
        sigs = []
        items = stack.split(" ")
        for i, item in enumerate(items):
            if item == "in":
                sigs.append(items[i+1].strip("\n"))
        return [sigs]

    @classmethod
    def __retrieve_trace__(cls, thread):
        """
        Input:
            All information in a thread
        Output:
            [ fun1, fun2, fun3, ...]
        """
        start = thread.find("#0")
        traces = thread[start + 1 :].split("#")
        sigs = map(cls.__retrieve_sig__, traces)
        return sigs

    @classmethod
    def __retrieve_trace_signal__(cls, threads):
        if threads.__len__() == 0:
            return []
        thread = threads[0]
        start_i = thread.find('#0')
        traces = thread[start_i + 1:].split('#')
        handler_mark = '<signal handler called>'
        handler_index = -1
        for index in xrange(traces.__len__()-1, 0, -1):
            if handler_mark  in traces[index]:
                handler_index = index
                break
        sigs = map(cls.__retrieve_sig__, traces[handler_index+1:])
        ignore_set = {'abort', 'raise', 'kernel_vsyscall', '??', 'unknown'}
        return [sig for sig in sigs if not sig in ignore_set]


    @classmethod
    def __retrieve_sig__(cls, record):
        """
        Input:
            (bug#=101700) 1  0xb7150803 in poll () from /lib/tls/i686/cmov/libc
            .so.6\\nno symbol table info available.\\n
            (bug#=611997) 5  boxed_nodes_cmp (p1=0x7fff4fa3d210, p2=0x1d1c29f8) at
            /tmp/buildd/glib2.0-2.22.4/gobject/gboxed.c:79
        Output:
            poll
            boxed_nodes_cmp

        Naive retrieve for now
        """
        words = record.split(" ")
        if "in" in words:
            try:
                pos = words.index("in") + 1
                return words[pos]
            except Exception, e:
                return "unknown"
        elif "at" in words:
            try:
                return words[1]
            except Exception, e:
                return "unknown"
        else:
            return "unknown"

    @classmethod
    def compare_stackinfo(cls, st1, st2, algorithm = 'signal'):
        """Compare the stacktraces.

        Args:
            st1: str, Stacktrace extracted by IRSTTools.filter
                    st2: str, same as st1
            algorithm: str, 'weight' or 'max'

        Returns:
            float, Similarity between 0.0 and 1.0. If either of the args is 
                None, the function returns 0.0
        """

        if algorithm == 'signal':
            return cls.stacktrace_asm_similarity(st1, st2)

        if st1 == [] or st2 == []:
            return 0.0
        try:
            length = min(len(st1), len(st2))
            if length == 0:
                return 0.0

            if algorithm == 'weight':
                weight = 0
                points = 0.0
            elif algorithm == 'max':
                max_ratio = 0.0

            for i in range(length):
                sst1 = set(st1[i])
                sst1.discard('??')
                sst1.discard('unknown')
                sst2 = set(st2[i])
                sst2.discard('??')
                sst2.discard('unknown')
                intersection = sst1 & sst2
                union = sst1 | sst2
                
                inter_len = len(intersection)
                union_len = len(union)
                if algorithm == 'weight':
                    points += inter_len
                    weight += union_len
                elif algorithm == 'max':
                    ratio = inter_len * 1.0 / union_len
                    if ratio > max_ratio:
                        max_ratio = ratio
            
            if algorithm == 'weight': 
                if weight == 0:
                    return 0.0
                else:
                    points /= weight
                return points
            elif algorithm == 'max':
                return max_ratio
            else:
                assert False

        except Exception, e:
            return 0.0

    @classmethod
    def stacktrace_asm_similarity(cls, primary, secondary):
        if primary.__len__() == 0 or primary[0].__len__() == 0:
            return 1.0
        elif secondary.__len__() == 0:
            return 0.0
        if primary[0].__len__() == 0:
            return 1.0
        pri_thread = set(primary[0])
        sec_thread = set(secondary[0])
        common = pri_thread & sec_thread
        return float(common.__len__()) / pri_thread.__len__()

    @classmethod
    def to_string(cls, st):
        #Template
        if st is None or len(st) == 0:
            return ""
        join_str = "\n"
        template = "Distribution: Ubuntu 6.10 (edgy)\nGnome Release: 2.16.1 2006-10-02 (Ubuntu)\nBugBuddy Version: 2.16.0\n\n"
        str_arr = map(cls.__thread_to_string__, st)
        return template + join_str.join(str_arr)

    @classmethod
    def __thread_to_string__(cls, thread):
        if len(thread) == 0:
            return ""
        join_str = "\n"
        thread_str = map(cls.__sig_to_string__, thread)
        return "\n" + join_str.join(thread_str)

    @classmethod
    def __sig_to_string__(cls, sig):
        prefix = "#2  0xb588f19f in "
        suffix = " ()"
        return prefix + sig + suffix

