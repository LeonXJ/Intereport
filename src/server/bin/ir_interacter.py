#!/usr/bin/python2.7

__author__ = 'Jialiang Xie (leonxj@gmail.com)'
__date__ = '2014-4-11'

# feedback
TEXT_LIMIT_LENGTH = 512

# signal
SIGNAL_BREAK = -1
SIGNAL_CONTINUE = 0
# state
STATE_ALIVE = 'alive'
STATE_EXPIRED = 'expired'
# info
INFO_ERROR = 'error'
ERROR_INVALID_MSGPACK = 'invalid message'
ERROR_NEED_SESSION_ID = 'need session id'
ERROR_SESSION_NOT_FOUND = 'session not found'
INFO_HELP = 'help'

# server side
SERVER_STATE = 'server_state'

# server commands
SERVER_SHUTDOWN = 'server_shutdown'
def server_shutdown(msg, res):
    from ir_log import IRLog
    IRLog.get_instance().println('Server will be shutdown')
    return SIGNAL_BREAK

SERVER_CACHE = 'server_cache'
def server_cache(msg, res):
    from ir_log import IRLog
    from ir_text import IRText
    from ir_tfidf import IRTFIDF
    from ir_document_count import IRDocumentCount
    IRLog.get_instance().println('Server is caching data')
    IRText.cache_all_data()
    IRTFIDF.cache_all_data()
    IRDocumentCount.cache_all_data()
    IRLog.get_instance().println('Server cached data')
    return SIGNAL_CONTINUE

SERVER_HELP = 'server_help'
def server_help(msg, res):
    res[INFO_HELP] = { 'server command' : SERVER_COMMANDS.keys(), \
                       'set session' : SET_COMMANDS.keys(), \
                       'do session' : CTL_COMMANDS.keys() }
    return SIGNAL_CONTINUE

SERVER_COMMANDS = { SERVER_SHUTDOWN : server_shutdown, \
                    SERVER_CACHE : server_cache, \
                    SERVER_HELP : server_help }

# session info
SESSION_ID = 'session_id'
SESSION_STATE = 'session_state'
# feedback recommend
FEEDBACK_KEYWORD = 'keyword'
FEEDBACK_SENTENCES = 'sentences'
FEEDBACK_DUPLICATES = 'duplicates'
# feedback report info
FEEDBACK_PRODUCT = 'product'
FEEDBACK_CREATE_TS = 'create_ts'
FEEDBACK_SUMMARY = 'summary'
FEEDBACK_DESCRIPTION = 'description'
FEEDBACK_PENALTY = 'penalty'
FEEDBACK_SKIP = 'skip'
FEEDBACK_IGNORE = 'ignore'
FEEDBACK_MAX_SENTENCES = 'max_sentences'
FEEDBACK_MAX_DUPLICATES = 'max_duplicates'
FEEDBACK_REPORT_LINK = 'report_link'
# session setting commands
SET_REPORT_INFO = 'set_report_info'
def set_report_info(report, msg):
    from ir_report import IRReport
    new_report = IRReport.from_string(msg.strip())
    return new_report

SET_REPORT_BASIC_INFO = 'set_report_basic_info'
def set_report_basic_info(report, msg):
    from ir_report import IRReport
    new_report = IRReport.from_string(msg.strip())
    new_report.set_stacktrace(report.get_stacktrace())
    new_report.set_penalty_terms(report.get_penalty_terms())
    new_report.set_skip_terms(report.get_skip_terms())
    new_report.set_exclude_report_ids(report.get_exclude_report_ids())
    return new_report

ADD_PENALTY = 'add_penalty'
def add_penalty(report, msg):
    from ir_term_count import IRTermCount
    report.add_penalty_term(msg)
    return report

ADD_EXCLUDE_REPORT = 'add_exclude'
def add_exclude_report(report, msg):
    report.add_exclude_report_id(int(msg))
    return report

ADD_SKIP_TERM = 'add_skip_term'
def add_skip_term(report, msg):
    report.add_skip_term(msg)
    return report

SET_COMMANDS = { SET_REPORT_INFO : set_report_info, \
                 SET_REPORT_BASIC_INFO : set_report_basic_info, \
                 ADD_PENALTY : add_penalty, \
                 ADD_EXCLUDE_REPORT : add_exclude_report, \
                 ADD_SKIP_TERM : add_skip_term }

# session do commands
CTL_RECOMMEND = 'do_recommend'
def do_recommend(report, res):
    from ir_recommender import IRRecommender
    res[FEEDBACK_KEYWORD], res[FEEDBACK_SENTENCES], res[FEEDBACK_DUPLICATES] \
        = IRRecommender.do_recommend(report)
    # truncate duplicate text
    res[FEEDBACK_DUPLICATES] = [__truncate_texts(text, TEXT_LIMIT_LENGTH) \
            for text in res[FEEDBACK_DUPLICATES]]
    return SIGNAL_CONTINUE

def __truncate_texts(text, limit_length):
    if text.__len__() > limit_length:
        return text[:limit_length] + ' ...'
    else:
        return text


CTL_SUBMIT = 'do_submit'
def do_submit(report, res):
    return SIGNAL_BREAK

CTL_CANCEL = 'do_cancel'
def do_cancel(report, res):
    return SIGNAL_BREAK

CTL_COMMANDS = { CTL_RECOMMEND : do_recommend, \
                 CTL_SUBMIT : do_submit, \
                 CTL_CANCEL : do_cancel }

class IRSender(object):

    BUFFER_SIZE = 65536

    @classmethod
    def send(cls, msg):
        import socket
        from ir_log import IRLog
        from ir_config import IRConfig

        server_ip = IRConfig.get_instance().get('server_ip')
        server_port = IRConfig.get_instance().get_int('server_port')

        logger = IRLog.get_instance()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((server_ip, server_port))
        s.send(msg)
        logger.println('Sent message: %s' % msg)
        data = s.recv(cls.BUFFER_SIZE)
        logger.println('Received message: %s' % data)
        s.close()
        return data

class IRDispatcher(object):
    """
    Listen to port and dispatch info
    """

    BUFFER_SIZE = 16384

    def __init__(self):
        self.__sessions = dict()

    def start(self):
        import socket
        from ir_log import IRLog
        from ir_config import IRConfig

        logger = IRLog.get_instance()
        config = IRConfig.get_instance()
        logger.println("Starting Intereport...")
        server_ip = config.get('server_ip')
        server_port = config.get_int('server_port')
        buffer_size = config.get_int('transfer_buffer_size')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((server_ip, server_port))
        s.listen(1)
        logger.println('Server started. Waiting for connection')
        server_state = STATE_ALIVE
        while server_state == STATE_ALIVE:
            conn, addr = s.accept()
            logger.println('Connection address: %s' % str(addr))
            # read message and prepare pack
            received_str = conn.recv(buffer_size)
            logger.println('Received message: %s' % received_str)
            msg_error = False
            respack = dict()
            try:
                msgpack = eval(received_str)
            except Exception:
                msgpack = None

            respack_dispatched = False
            if msgpack is None:
                respack[INFO_ERROR] = ERROR_INVALID_MSGPACK
                logger.println('Error! Cannot get pack', 2)
                msg_error = True
            # server control
            has_server_command = False
            if not msg_error:
                for key, value in msgpack.items():
                    if key in SERVER_COMMANDS:
                        has_server_command = True
                        signal = SERVER_COMMANDS[key](value, respack)
                        if signal == SIGNAL_BREAK:
                            server_state = STATE_EXPIRED
                if has_server_command:
                    # server control is exclusive
                    respack[SERVER_STATE] = server_state
                    conn.send(str(respack))
                    respack_dispatched = True
                    continue
            # session
            if not msg_error and SESSION_ID in msgpack:
                if msgpack[SESSION_ID] == -1:
                    # start a new session
                    session_id = self.generate_session_id()
                    session = IRSession(session_id, self)
                    self.__sessions[session_id] = session
                    msgpack[SESSION_ID] = session_id
                    session.daemon = True
                    session.start()
                # dispatch
                session_id = msgpack[SESSION_ID]
                if not session_id in self.__sessions:
                    logger.println('Error! Cannot find session %d' %
                                       session_id, 2)
                    respack[INFO_ERROR] = ERROR_SESSION_NOT_FOUND
                    msg_error = True
                else:
                    msgpack['respack'] = respack
                    msgpack['connection'] = conn
                    logger.println('Dispatch msgpack to session %d' % session_id)
                    self.__sessions[session_id].enqueue(msgpack)
                    respack_dispatched = True
            else:
                logger.println('Error! No session_id in msgpack', 2)
                respack[INFO_ERROR] = ERROR_NEED_SESSION_ID
                msg_error = True
            if not respack_dispatched or msg_error:
                conn.send(str(respack))

        logger.println('Bye')
        logger.stop_log()

    def generate_session_id(self):
        id = 1
        while id in self.__sessions:
            id += 1
        return id

    def remove_session(self, id):
        if id in self.__sessions:
            from ir_log import IRLog
            IRLog.get_instance().println('Session %d expired' % id)
            del self.__sessions[id]

import threading
import Queue
class IRSession(threading.Thread):
    """
    A session.
    """
    TIMEOUT = None

    def __init__(self, id, dispatcher):
        from ir_report import IRReport
        
        threading.Thread.__init__(self)
        self.__id = id
        self.__msg_queue = Queue.Queue(maxsize = 10)
        self.__report = IRReport('','')
        self.__dispatcher = dispatcher

    def enqueue(self, msgpack):
        self.__msg_queue.put(msgpack)

    def run(self):
        from ir_log import IRLog
        session_state = STATE_ALIVE
        while session_state == STATE_ALIVE:
            try:
                msgpack = self.__msg_queue.get(True)
                # do something to msgpack
                conn = msgpack['connection']
                respack = msgpack['respack']
                respack[SESSION_ID] = msgpack[SESSION_ID]
                # set phase
                for key, value in msgpack.items():
                    if key in SET_COMMANDS:
                        self.__report = SET_COMMANDS[key](self.__report, value)
                # do phase
                signal = SIGNAL_CONTINUE
                for key, value in msgpack.items():
                    if key in CTL_COMMANDS:
                        signal = CTL_COMMANDS[key](self.__report, respack)
                        if signal == SIGNAL_BREAK:
                            session_state = STATE_EXPIRED
                self.__pack_report_info(respack)
                IRLog.get_instance().println('Send message: %s' % str(respack))
                conn.send(str(respack))
            except Queue.Empty:
                from ir_log import IRLog
                IRLog.get_instance().println('Session %d time out' % self.__id,
                                             2)
                break
        self.__dispatcher.remove_session(self.__id)

    def __pack_report_info(self, respack):
        respack[FEEDBACK_PRODUCT] = self.__report.get_product()
        respack[FEEDBACK_CREATE_TS] = self.__report.get_create_ts()
        respack[FEEDBACK_SUMMARY] = self.__report.get_summary_text()
        respack[FEEDBACK_DESCRIPTION] = self.__report.get_description_text()
        respack[FEEDBACK_PENALTY] = self.__report.get_penalty_terms()
        respack[FEEDBACK_SKIP] = self.__report.get_skip_terms()
        respack[FEEDBACK_IGNORE] = self.__report.get_exclude_report_ids()
        from ir_config import IRConfig
        respack[FEEDBACK_MAX_SENTENCES] = IRConfig.get_instance().get_int(
            'bug_sentence_number')
        respack[FEEDBACK_MAX_DUPLICATES] = IRConfig.get_instance().get_int(
            'bug_duplicate_number')
        respack[FEEDBACK_REPORT_LINK] = IRConfig.get_instance().get(
                'bugzilla_report_link')

if __name__ == '__main__':
    import sys
    from ir_log import IRLog
    from ir_config import IRConfig
    config = sys.argv[1]
    IRLog.get_instance().start_log()
    IRConfig.get_instance().load(config)
    mode = sys.argv[2]
    if mode == 'client':
        msg = sys.argv[3]
        IRSender.send(msg)
    elif mode == 'server':
        dispatcher = IRDispatcher()
        dispatcher.start()
    IRLog.get_instance().stop_log()

