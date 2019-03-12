import os
import random
import time
# from flask import Flask, request, render_template, session, flash, redirect, \
#     url_for, jsonify, Response
import flask
import requests
import subprocess
from flask_mail import Mail, Message
from celery import Celery, uuid
from flask_cors import CORS

class MyResponse(flask.Response):
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response,(list,dict)):
            response = flask.jsonify(response)
        return super(flask.Response, cls).force_type(response, environ)

class MyFlask(flask.Flask):
        response_class = MyResponse

def after_request(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, PATCH, OPTIONS, HEAD'
    # response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, x-token'
    response.headers['Access-Control-Allow-Headers'] = '*'
    return response

# app = MyFlask(__name__)
# cors = CORS(app,supports_credentials=True)
# app.after_request(after_request)

app = flask.Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'top-secret!'

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'flask@example.com'

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


# Initialize extensions
mail = Mail(app)

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)


@celery.task
def send_async_email(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)


@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}

@celery.task
def CreateIp(reqAttributes):
    """Background create ip from request"""
    try:
        repo_path = reqAttributes['path']
        repo_name = reqAttributes['repo']
        repo_branch = reqAttributes['branch']
        repo_branch = reqAttributes['tag']
        repo_callback = reqAttributes['callback']
    except KeyError:
        if 'path' not in reqAttributes:
            return {'status' : 1, 'message' : 'payload format error, payload=%s' % (reqAttributes)}
        if 'repo' not in reqAttributes:
            return {'status' : 1, 'message' : 'payload format error, payload=%s' % (reqAttributes)}
        if 'branch' not in reqAttributes:
            repo_branch = 'master'
        if 'tag' not in reqAttributes:
            repo_tag = None
        if 'callback' not in reqAttributes:
            repo_callback = None
    else:
        if reqAttributes['branch'] == '':
            repo_branch = 'master'
        if reqAttributes['tag'] == '':
            repo_tag = None
        if reqAttributes['callback'] == '':
            repo_callback = None

    c = []
    c.append('/bin/mkdir -p %s' % (repo_path))
    c.append('/usr/local/git/bin/git clone --branch %s %s %s' % (repo_branch, repo_name, repo_path))

    if repo_tag:
        c.append('/usr/local/git/bin/git checkout %s' % (repo_tag))

    shell_cmd = ';'.join(c)
    status,output = subprocess.getstatusoutput(shell_cmd)
    if status != 0:
        return {'status': status, 'message' : output}

    if repo_callback:
        r = requests.get(repo_callback)
        if r.status_code==200 or r.status_code==201:
            return {'status': 0, 'message' : 'hook success, url=%s' % (repo_callback)}
        else:
            return {'status': r.status_code, 'message' : 'hook fail, url=%s' % (repo_callback)}



@celery.task
def RemoveIp(reqAttributes):
    """Background task to send an email with Flask-Mail."""
    try:
        repo_path = reqAttributes['path']
        repo_callback = reqAttributes['callback']
    except KeyError:
        if 'path' not in reqAttributes:
            return {'status' : 1, 'message' : 'payload format error, payload=%s' % (reqAttributes)}
        if 'callback' not in reqAttributes:
            repo_callback = None
    else:
        pass

    c = []
    c.append('/bin/rm -rf %s' % (repo_path))
    shell_cmd = ';'.join(c)
    status,output = subprocess.getstatusoutput(shell_cmd)

    if status != 0:
        return {'status': status, 'message' : output}

    if repo_callback:
        r = requests.get(repo_callback)
        if r.status_code==200 or r.status_code==201:
            return {'status': 0, 'message' : 'hook success, url=%s' % (repo_callback)}
        else:
            return {'status': r.status_code, 'message' : 'hook fail, url=%s' % (repo_callback)}



@celery.task
def ListIp(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)

@celery.task
def UpdateIp(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)


@app.route('/', methods=['GET', 'POST'])
def index():
    if flask.request.method == 'GET':
        return flask.render_template('index.html', email=flask.session.get('email', ''))
    email = flask.request.form['email']
    flask.session['email'] = email

    # send the email
    msg = Message('Hello from Flask',
                  recipients=[flask.request.form['email']])
    msg.body = 'This is a test email sent from a background Celery task.'
    if flask.request.form['submit'] == 'Send':
        # send right away
        send_async_email.delay(msg)
        flask.flash('Sending email to {0}'.format(email))
    else:
        # send in one minute
        send_async_email.apply_async(args=[msg], countdown=60)
        flask.flash('An email will be sent to {0} in one minute'.format(email))

    return flask.redirect(flask.url_for('index'))


@app.route('/longtask', methods=['POST'])
def longtask():
    task = long_task.apply_async()
    return flask.jsonify({}), 202, {'Location': flask.url_for('taskstatus',
                                                  task_id=task.id)}


@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return flask.jsonify(response)

@app.route('/api/v1/ip', methods=['POST'])
def apiAddIp():

    try:
        reqPayload = flask.request.get_json()
        reqAttributes = reqPayload['data']['attributes']
    except:
        resPayload = {
            'errors'    : [
                {
                    'status'    : '422',
                    'source'    : '',
                    'title'     : '',
                    'detail'    : 'invalid request json format',
                }
            ]
        }
        return flask.jsonify(resPayload), 422
    else:
        task_id = uuid()
        CreateIp.apply_async(args=[reqAttributes], countdown=5, task_id=task_id)
        reqPayload['links'] = {'self' : flask.request.url}
        reqPayload['data']['task_id'] = task_id
        return flask.jsonify(reqPayload)


@app.route('/api/v1/ip', methods=['DELETE'])
def apiDeleteIpByPath():
    try:
        reqPayload = flask.request.get_json()
        reqAttributes = reqPayload['data']['attributes']
    except:
        resPayload = {
            'errors'    : [
                {
                    'status'    : '422',
                    'source'    : '',
                    'title'     : '',
                    'detail'    : 'invalid request json format',
                }
            ]
        }
        return flask.jsonify(resPayload), 422
    else:
        task_id = uuid()
        RemoveIp.apply_async(args=[reqAttributes], countdown=5, task_id=task_id)
        reqPayload['links'] = {'self' : flask.request.url}
        reqPayload['data']['task_id'] = task_id
        return flask.jsonify(reqPayload), 201


@app.route('/api/v1/ip', methods=['GET'])
def apiGetAllIp():

    # c = []
    # c.append('cd %s' % (''))
    # c.append('git describe --always')
    # shell_cmd = ';'.join(c)

    # status.output = subprocess.getstatusoutput(shell_cmd)

    if status != 0:
        return {'status': status, 'message' : output}

    res = {
        'links': {
            'self': flask.request.url,
        },
        'data': [],
    }
    return flask.jsonify(res)

@app.route('/api/v1/ip/<id>', methods=['GET'])
def apiGetIpById():
    res = {
        'links': {
            'self': flask.request.url,
        },
        'data': [],
    }
    return flask.jsonify(res)

@app.route('/api/v1/ip/<id>', methods=['PUT','PATCH'])
def apiUpdateIpById():
    res = {
        'links': {
            'self': flask.request.url,
        },
        'data': [],
    }
    return flask.jsonify(res)

@app.route('/hook', methods=['GET'])
def ApiGetHook():
    try:
        reqId       = flask.request.args.get('id')
        reqTaskId   = flask.request.args.get('task_id')
        reqStatus   = flask.request.args.get('status')
    except:
        reqId = ''
        reqTaskId = ''
        reqStatus = ''
    else:
        print('[hook] debug, id=%s, task_id=%s, status=%s' % (reqId, reqTaskId, reqStatus))

    res = {
        'links': {
            'self': flask.request.url,
        },
        'data': [],
    }
    return flask.jsonify(res),200

if __name__ == '__main__':
    app.run(debug=True)
