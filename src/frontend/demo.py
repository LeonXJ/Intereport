import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, render_template, request, session, g
from socket import *    
import time

handler = RotatingFileHandler('/home/zhengqm/ir_demo/logfile', maxBytes=500000, backupCount=1)
handler.setLevel(logging.INFO)


app = Flask(__name__)
app.config.update(dict(
    SECRET_KEY='[]@#$%^&*--inter_report--#$%^&*'
))

app.debug = True
app.logger.addHandler(handler)

# Global args
SERVICE_ADDR = "192.168.0.5"
SERVICE_PORT = 5051
SESSION_ID = "session_id"

# Recieve args
SESSION_STATE = "session_state"
KEYWORD = "keyword"
SENTENCES = 'sentences'
DUPLICATES = 'duplicates'
PRODUCT = 'product'
CREATE_TS = 'create_ts'
SUMMARY = 'summary'
DESCRIPTION = 'description'
PENALTY = 'penalty'
SKIP = 'skip'
IGNORE = 'ignore'
MAX_SENTENCES = 'max_sentences'
MAX_DUPLICATES = 'max_duplicates'
REPORT_LINK = 'report_link'

# Send args

SET_REPORT_INFO = "set_report_info"
SET_REPORT_BASIC_INFO = "set_report_basic_info"
DO_RECOMMEND = "do_recommend"
APPEND_PENALTY = "add_penalty"
SKIP_KEYWORD = "add_skip_term"
APPEND_IGNORE = "add_exclude"

NEWLINE = '[[NEWLINE]]'
SEMICOLON = '[[SEMICOLON]]'

REPORT_STRING_SEP = ';'


def time_to_int(time_str):
    components = time_str.split('-')
    year = int(components[0])
    month = int(components[1])
    day = int(components[2])
    secs = time.mktime((year, month, day, 0, 0, 0, 0, 0, 0))
    return int(secs) 

@app.route('/')
def index():
    return render_template('index.html')

def explain_arg_pack(args):
    return jsonify(keyword=args[KEYWORD], sentences=args[SENTENCES], duplicates=args[DUPLICATES],\
            tip=give_tip(args[DUPLICATES].__len__(), args[SENTENCES].__len__()), \
            penalty=args[PENALTY], skip=args[SKIP], ignore=args[IGNORE])

@app.route('/_submit')
def submit():
    """
    TODO:
    What fields should args contain?

    """
    from time import sleep
    args = {}
    
    if not SESSION_ID in session:
        render_template('error.html', msg="No valid session_id")

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((SERVICE_ADDR, SERVICE_PORT))

    # Set session_id
    session_id = session[SESSION_ID]
    args[SESSION_ID] = session_id
    args[DO_RECOMMEND] = 1

    # Get report information
    term = request.args.get('term', "default", type=str)
    product = request.args.get('product', "default", type=str)
    date = request.args.get('date', "default", type=str)
    summary = request.args.get('summary', "default", type=str)
    description = request.args.get('description', "default", type=str)
    report_info = build_report_info(product, date, summary, description, '')
    args[SET_REPORT_BASIC_INFO] = report_info
    
    args_str = str(args)
    app.logger.info("Receive Submit: " + args_str)
    sock.send(args_str)

    buf = sock.recv(65535)
    sock.close()

    args = eval(buf)
    
    return explain_arg_pack(args)

@app.route('/_notsure')
def notsure():

    from time import sleep
    args = {}

    if not SESSION_ID in session:
        render_template('error.html', msg="No valid session_id")

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((SERVICE_ADDR, SERVICE_PORT))

    # Set session_id
    session_id = session[SESSION_ID]
    args[SESSION_ID] = session_id
    args[DO_RECOMMEND] = 1

    # Get report information
    term = request.args.get('term', "default", type=str)

    args[SKIP_KEYWORD] = term

    app.logger.info("Skip: " + term)
    
    args_str = str(args)
    sock.send(args_str)

    buf = sock.recv(65535)
    sock.close()
    app.logger.info("Receive: "+buf)
    args = eval(buf)
    return explain_arg_pack(args) 

@app.route('/_notmine')
def notmine():

    from time import sleep
    args = {}

    if not SESSION_ID in session:
        render_template('error.html', msg="No valid session_id")

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((SERVICE_ADDR, SERVICE_PORT))

    # Set session_id
    session_id = session[SESSION_ID]
    args[SESSION_ID] = session_id
    args[DO_RECOMMEND] = 1

    # Get report information
    ignore_id = request.args.get('ignore_id', "default", type=int)

    args[APPEND_IGNORE] = ignore_id

    app.logger.info("ignore: " + str(ignore_id))
    
    args_str = str(args)
    sock.send(args_str)

    buf = sock.recv(65535)
    sock.close()
    app.logger.info("Receive: "+buf)
    args = eval(buf)
    return explain_arg_pack(args) 

@app.route('/_never')
def never():
    """
    TODO:
    What fields should args contain?

    """
    from time import sleep
    args = {}

    if not SESSION_ID in session:
        render_template('error.html', msg="No valid session_id")

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((SERVICE_ADDR, SERVICE_PORT))

    # Set session_id
    session_id = session[SESSION_ID]
    args[SESSION_ID] = session_id
    args[DO_RECOMMEND] = 1

    # Get report information
    term = request.args.get('term', "default", type=str)

    args[APPEND_PENALTY] = term

    app.logger.info("Append: " + term)
    
    args_str = str(args)
    sock.send(args_str)

    buf = sock.recv(65535)
    sock.close()
    
    app.logger.info("Receive: "+ buf)
    args = eval(buf)
    return explain_arg_pack(args)

def give_tip(dup_length, sim_length = 5):
    if dup_length > 0:
        return 'Some existing reports are quite alike.'
    elif sim_length > 0:
        return 'Could you give us more information?'
    else:
        return 'Your report is perfect! Please submit!'

def get_report_info(report_text):
    fields = report_text.strip().split(';')
    summary = recover_special_character(fields[2])

@app.route('/submit_report', methods=['GET', 'POST'])
def submit_report():
    """Show the submit page"""

    if not SESSION_ID in session:
        render_template('error.html', msg="No valid session_id")

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((SERVICE_ADDR, SERVICE_PORT))

    is_duplicate = False
    dup_id=0
    if 'dup_id' in request.args:
        dup_id = request.args['dup_id']
        is_duplicate = True

    # Set session_id
    session_id = session[SESSION_ID]
    args = {SESSION_ID : session_id}
    
    args_str = str(args)
    sock.send(args_str)
    buf = sock.recv(65535)
    sock.close()
    args = eval(buf)

    return render_template('submit.html', product=args[PRODUCT], \
        summary=args[SUMMARY], description=args[DESCRIPTION], \
        is_duplicate=is_duplicate, duplicate=dup_id)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """
    Create a new report.
    Send: date;product;summary;description+stacktrace;;;;
    """
    product = ""
    summary = ""
    if request.method == "POST":
        create_ts = request.form['date']
        product = request.form['product'].lower()
        summary = request.form['summary']
        description = request.form['description']
        stacktrace = request.form['stacktrace']

    else:
        return render_template('error.html', msg="Get method on /feedback denied")


    app.logger.info(":".join([create_ts, product, summary, description, stacktrace]))


    app.logger.info("Connecting " + SERVICE_ADDR + " " + str(SERVICE_PORT))
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((SERVICE_ADDR, SERVICE_PORT))

    # Build args
    args = {}
    args[SESSION_ID] = -1
    report_info = build_report_info(product, create_ts, summary, description, stacktrace)
    args[SET_REPORT_INFO] = report_info
    args[DO_RECOMMEND] = 1
    args_str = str(args)

    app.logger.info(args_str)
    # Send
    sock.send(args_str)

    # Recieve result
    buf = sock.recv(65535)
    app.logger.info("Recieve:" + buf)
    args = eval(buf)

    session[SESSION_ID] = args[SESSION_ID]
    # recommend
    tip = give_tip(args[DUPLICATES].__len__(), args[SENTENCES].__len__())

    return render_template('ir_feedback.html', \
            keyword=args[KEYWORD], sentences=args[SENTENCES], duplicates=args[DUPLICATES], \
            tip=tip, max_sentences=args[MAX_SENTENCES], max_duplicates=args[MAX_DUPLICATES], \
            create_ts=create_ts, product=args[PRODUCT], \
            summary=args[SUMMARY], description=args[DESCRIPTION], stacktrace=stacktrace, \
            penalty=args[PENALTY], skip=args[SKIP], ignore=args[IGNORE], \
            report_link=args[REPORT_LINK])

def build_report_info(product, date, summary, description, stacktrace, penalty = ''):
    date = str(time_to_int(date))
    template = "Distribution: Ubuntu 6.10 (edgy)\nGnome Release: 2.16.1 2006-10-02 (Ubuntu)\nBugBuddy Version: 2.16.0\n\n"
    return  ";".join([ date, \
                       product, \
                       translate_special_character(summary), \
                       translate_special_character('%s\n%s\n%s' % (description, template, stacktrace)), \
                    ])

def translate_special_character(raw):
    return raw.replace("\n", NEWLINE).replace(";", SEMICOLON)

def recover_special_character(raw):
    result =  raw.replace(NEWLINE, "\n").replace(SEMICOLON, ";")
    return result

def add_penalty(penalty, raw = ""):
    if raw == "":
        return penalty
    else:
        return raw + "," + penalty



if __name__ == "__main__":
    app.run()
