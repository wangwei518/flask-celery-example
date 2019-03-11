import os
import random
import time
# from flask import Flask, request, render_template, session, flash, redirect, \
#     url_for, jsonify, Response
import flask
import requests
from flask_mail import Mail, Message
from celery import Celery
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
def CreateIp(payload):
    """Background create ip from request"""
    try:
        item = payload['data']['attributes']
        repo_path = item['path']
        repo_name = item['repo']
    except KeyError:
        return {'status' : 1, 'message' : 'payload format error, payload=%s' % (payload)}
    else:
        pass

    c = []
    c.append('/bin/mkdir -p %s' % (repo_path))

    repo_branch = 'master'
    if 'branch' in item.keys():
        if item['branch'] != '':
            repo_branch = item['branch']

    c.append('/usr/local/git/bin/git clone --branch %s %s %s' % (repo_branch, repo_name, repo_path))

    if 'tag' in item.keys():
        if item['tag'] != '':
            repo_tag = item['tag']
            c.append('/usr/local/git/bin/git checkout %s' % (repo_tag))

    shell_cmd = ';'.join(c)
    status.output = subprocess.getstatusoutput(shell_cmd)
    if status != 0:
        return {'status': status, 'message' : output}

    if 'callback' in item.keys():
        url = item['callback']
        r = requests.get(url)
        if r.status_code == 200 or r.status_code==201:
            return {'status': 0, 'message' : ''}
        else:
            return {'status': r.status_code, 'message' : 'requests status_code=%d' % (r.status_code)}



@celery.task
def RemoveIp(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)

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
    data = flask.request.get_json()
    print(data)
    CreateIp.apply_async(args=[data], countdown=5)
    try:
        data =
    except KeyError:

    else:

    res = {
        'links': {
            'self': flask.request.url,
        },
        'data': data,
    }
    return flask.jsonify(res)

    #{'project' : request.json['project']}
    #user        = request.json['user']
    #path        = request.json['path']
    #repo        = request.json['repo']
    #branch      = request.json['branch']
    #tag         = request.json['tag']
    #callback    = request.json['callback']


@app.route('/api/v1/ip/<id>', methods=['DELETE'])
def apiDeleteIpById():
    res = {
        'links': {
            'self': flask.request.url,
        },
        'data': [],
    }
    return flask.jsonify(res)

@app.route('/api/v1/ip', methods=['GET'])
def apiGetAllIp():
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

if __name__ == '__main__':
    app.run(debug=True)
