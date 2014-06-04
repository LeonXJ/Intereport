#!/usr/bin/python2.7
"""Bug duplicate group.


"""

__author__      = 'leonxj@gmail.com (Jialiang Xie) and Qimu Zheng'
__date__        = '2014-1-2'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-18'

class IRDuplicateGroup(object):
    """Group dopulicate bugs.
    """

    @classmethod
    def parse_info_level0(cls, info_level0_filename = None):
        """Generate duplicate group database from info level0.
        
        Args:
            info_level0_filename: str, If not given, the parameter will be 
                loaded from config file.
        """

        from ir_log import IRLog
        from ir_log import IRProgressBar
        max_group_id = 0
        bug2group = {}
        group2bug = {}
        incomplete_bug = []
        cur_bug = -1
        is_cur_incomplete = False
        if None == info_level0_filename:
            from ir_config import IRConfig
            info_level0_filename = IRConfig.get_instance(). \
                    get('bug_info_level0_filename')
        in_file = open(info_level0_filename, 'r')
        # count the lines
        IRLog.get_instance().println('Counting line number of info level0')
        line_count = sum(1 for line in in_file)
        in_file.seek(0)
        
        progress_bar = IRProgressBar(line_count, 'Read info level0', False, 0, 1) 
        line_num = 0
        # The lines may contain useful information: bug_id, resolution and dup_id
        # bug_id: current bug
        # resolution: the resolution of the current bug
        # dup_id: the duplicate of current bug
        # strategy:
        # 1. drop when resolution is INCOMPLETE
        # 2. (1) if both dup_id and cur_bug are in no group, assign a new group id
        #       for them
        #    (2) if only of dup_id or cur_bug is in group, assign the group id 
        #       to the other
        #    (3) if both of them are in (different) group, merge the groups
        for line in in_file:
            line_num += 1
            progress_bar.set_value(line_num)
            line = line.strip()
            if line.startswith('<bug_id>'):
                cur_bug = int(cls.__get_contain(line))
                is_cur_incomplete = False
            elif line.startswith('<resolution>INCOMPLETE'):
                is_cur_incomplete = True
                incomplete_bug.append(cur_bug)
            elif line.startswith('<dup_id>'):
                if is_cur_incomplete:
                    # ignore this one
                    continue
                dup_bug = int(cls.__get_contain(line))
                cur_bug_group = -1
                dup_bug_group = -1
                if cur_bug in bug2group:
                    cur_bug_group = bug2group[cur_bug]
                if dup_bug in bug2group:
                    dup_bug_group = bug2group[dup_bug]
                if cur_bug_group == -1 and dup_bug_group == -1:
                    # (1) assign a new group id
                    group_id = max_group_id
                    max_group_id += 1
                    bug2group[cur_bug] = group_id
                    bug2group[dup_bug] = group_id
                    group2bug[group_id] = [cur_bug, dup_bug]
                elif cur_bug_group != -1 and dup_bug_group != -1 and cur_bug_group != dup_bug_group:
                    # (3) merge small group to the large
                    conserve_group = cur_bug_group
                    remove_group = dup_bug_group
                    if group2bug[cur_bug_group].__len__() < \
                        group2bug[dup_bug_group].__len__():
                        conserve_group = dup_bug_group
                        remove_group = cur_bug_group
                    for bug in group2bug[remove_group]:
                        bug2group[bug] = conserve_group
                    group2bug[conserve_group].extend(group2bug.pop(remove_group))
                else:
                    # (2) assign the group id
                    if cur_bug_group == -1:
                        group2bug[dup_bug_group].append(cur_bug)
                        bug2group[cur_bug] = dup_bug_group
                    else:
                        group2bug[cur_bug_group].append(dup_bug)
                        bug2group[dup_bug] = cur_bug_group
        in_file.close()
        # remove incomplete bugs
        for bug in incomplete_bug:
            if bug in bug2group:
                group = bug2group[bug]
                bug2group.__delitem__(bug)
                group2bug[group].remove(bug)
                if group2bug[group].__len__() == 0:
                    del group2bug[group]

        cls.__store_to_mongodb(bug2group, group2bug)
    
    @classmethod
    def parse_dump_dup_file(cls, dump_dup_file = None):
        """Generate duplicate group database from dump dup_file
        
        Args:
            dump_dup_file: str
        """

        from ir_log import IRLog
        from ir_log import IRProgressBar
        if None == dump_dup_file:
            dump_dup_file = IRConfig.get_instance(). \
                    get('bug_dump_dup_filename')
        in_file = open(dump_dup_file, 'r')
        # count the lines
        IRLog.get_instance().println('Counting line number of info level0')
        line_count = sum(1 for line in in_file)
        in_file.seek(0)
        
        progress_bar = IRProgressBar(line_count, 'Read sql duplicate file', False, 0, 1) 
        line_num = 0
        groups = {}
        for line in in_file:
            line_num += 1
            progress_bar.set_value(line_num)
            line = line.strip()
            info = line.split("|")
            origin = int(info[0])
            target = int(info[1])
            if not origin in groups:
                groups[origin] = [origin]
            if not target in groups[origin]:
                groups[origin].append(target)
        in_file.close()

        index = 0
        bug2group = {}
        group2bug = {}
        for key, group in groups.items():
            group2bug[index] = group
            for bug in group:
                bug2group[bug] = index
            index += 1

        cls.__store_to_mongodb(bug2group, group2bug)

    @classmethod
    def __get_contain(cls, string):
        """Return the contain between <id> and </id>.
        
        Args:
            string: str, An xml element
            
        Returns:
            str, The inner text of the element"""

        beg = string.find('>')
        tail = string.find('<', beg, -1)
        return string[beg+1:tail]
    
    @classmethod
    def __store_to_mongodb(cls, bug2group, group2bug):
        """Store duplicate group information into Mongodb.
        
        Args:
            bug2group: dict, {bug_id -> group_id}
            group2bug: dict, {group_id -> [bug_id]}
        """

        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection

        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        bug_group_name = IRConfig.get_instance().get('bug_group_name')
        duplicate_collection = IRCollection(
            'bug_db_name', 'bug_duplicate_collection_name', 'w')
        def iter_bug_group(bug):
            duplicate_collection.insert({ bug_id_name : bug,
                                          bug_group_name : bug2group[bug] })
        IRProgressBar.execute_iteration_for_dict(bug2group, iter_bug_group,
                                                 "Store to db")
        duplicate_collection.create_index([(bug_id_name, IRCollection.ASCENDING)])
        duplicate_collection.create_index([(bug_group_name, IRCollection.ASCENDING)])
        duplicate_collection.close()

        # duplicate group size collection
        group_name = IRConfig.get_instance().get('bug_group_name')
        group_size_name = IRConfig.get_instance().get('bug_group_size')
        duplicate_group_count_collection = IRCollection(
            'bug_db_name', 'bug_duplicate_group_count_collection_name',
            'w')
        line_num = 0
        for group, bugs in group2bug.items():
            line_num += 1
        def iter_group_bug(group):
            duplicate_group_count_collection.insert({group_name : group,
                                                     group_size_name : group2bug[group].__len__()})
        IRProgressBar.execute_iteration_for_dict(group2bug, iter_group_bug,
                                                 'Store Index')
        duplicate_group_count_collection.create_index(
            [(group_name, IRCollection.ASCENDING)])
        duplicate_group_count_collection.close()

    @classmethod
    def get_duplicate_group_information(cls, group_size_min, group_size_max):
        """Calculate the size of duplicate group.

        Args:
            group_size_min: int, The minimum size of wanted group.
            group_size_max: int, The maximum size of wanted group.

        Returns:
            [int], [group_id]
        """

        from ir_log import IRLog
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection

        duplicate_group_count_collection = IRCollection(
            'bug_db_name', 'bug_duplicate_group_count_collection_name', 'r')
        group_name = IRConfig.get_instance().get('bug_group_name')
        group_size_name = IRConfig.get_instance().get('bug_group_size')
        result = duplicate_group_count_collection.find({group_size_name : \
                {"$gt":group_size_min, "$lt":group_size_max}})
        return [group[group_name] for group in result]

    @classmethod
    def get_bugs_in_group(cls, group_id):
        """Get bugs in a group.

        Args:
            group_id: int

        Returns:
            [int], [bug_id]
        """
        
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection
        
        duplicate_collection =IRCollection(
            'bug_db_name', 'bug_duplicate_collection_name', 'r')
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        group_name = IRConfig.get_instance().get('bug_group_name')
        find_result = duplicate_collection.find({group_name : group_id})
        return [bug[bug_id_name] for bug in find_result]

    @classmethod
    def get_group_of_bug(cls, bug_id):
        """Get the group id of a bug.

        Args:
            bug_id: int

        Returns:
            int, group_id
        """

        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection

        duplicate_collection = IRCollection(
            'bug_db_name', 'bug_duplicate_collection_name', 'r')
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        group_name = IRConfig.get_instance().get('bug_group_name')

        result = duplicate_collection.find({bug_id_name : bug_id})
        if result.count() == 0:
            return None
        else:
            return result[0][group_name]

    @classmethod
    def is_in_same_duplicate_group(cls, aim_bug_id, similarities, remove_self = False):
        """Judge what bugs in similarities are actual duplicates.
        
        Args:
            bug_id: int, the bug defining the group id.
            similarities: [int], the bugs waiting to be judged

        Returns:
            [[int], [int], [int]], [[bugs in the same group with bug_id],
                                     [bugs in the different group with bug_id],
                                     [all the bugs in bug_id's group]]
        """
        
        from ir_config import IRConfig
        from ir_text import IRText

        group_id = cls.get_group_of_bug(aim_bug_id)
        if group_id is not None:
            duplicate_group = IRDuplicateGroup()
            bugs = duplicate_group.get_bugs_in_group(group_id)
            if remove_self:
                bugs.remove(aim_bug_id)
        else:
            if remove_self:
                bugs = []
            else:
                bugs = [aim_bug_id]
        if remove_self and aim_bug_id in similarities:
            similarities.remove(aim_bug_id)
        sim_set = set(similarities)
        bug_set = set(bugs)
        hit = list(sim_set & bug_set)
        nothit = list(sim_set - bug_set)
        
        return hit, nothit, bugs

    @classmethod
    def show_distribution_on_product_and_create_ts(cls):
        """Show the distribution of create time and number of products on
        each duplicate group.
        """
        from ir_log import IRLog
        from ir_log import IRProgressBar
        from ir_config import IRConfig
        from ir_mongodb_helper import IRCollection

        bug2group_collection = IRCollection(
            'bug_db_name', 'bug_duplicate_collection_name', 'r')
        basic_collection = IRCollection(
            'bug_db_name', 'bug_basic_collection_name', 'r')
        bug_id_name = IRConfig.get_instance().get('bug_id_name')
        group_name = IRConfig.get_instance().get('bug_group_name')
        product_name = IRConfig.get_instance().get('bug_product_name')
        create_ts_name = IRConfig.get_instance().get('bug_create_ts_name')

        group_ids = bug2group_collection.distinct(group_name)
        progress_bar = IRProgressBar(group_ids.__len__(), "group", False, 0, 1)
        group_num = 0
        for group_id in group_ids:
            group_num += 1
            progress_bar.set_value(group_num)
            bugs = bug2group_collection.find({group_name : group_id})
            min_ts = 9999999999
            max_ts = -1000
            product_set = set()
            for bug in bugs:
                bug_id = bug[bug_id_name]
                basic = basic_collection.find({bug_id_name : bug_id})
                if basic.count() == 0:
                    continue
                ts = basic[0][create_ts_name]
                product = basic[0][product_name]
                # ts
                if ts > max_ts:
                    max_ts = ts
                if ts < min_ts:
                    min_ts = ts
                # product
                product_set.add(product)
            IRLog.get_instance().println('ts span:%d;product number:%d' \
                    % (max_ts - min_ts, product_set.__len__()), 2)

if __name__ == '__main__':

    import sys
    from ir_log import IRLog
    from ir_config import IRConfig

    config = sys.argv[1]
    mode = sys.argv[2]
    IRLog.get_instance().start_log()
    IRConfig.get_instance().load(sys.argv[1])
    filename = None
    if sys.argv.__len__() > 3:
        filename = sys.argv[3]
    if mode == "level1":
        IRDuplicateGroup.parse_info_level0(filename)
    elif mode == "sql":
        IRDuplicateGroup.parse_dump_dup_file(filename)
    elif mode == "stat":
        IRDuplicateGroup.show_distribution_on_product_and_create_ts()
    else:
        IRLog.get_instance().println("Error parameter %s" % mode)
    #duplicate_group.store_to_mongodb()
    IRLog.get_instance().stop_log()
