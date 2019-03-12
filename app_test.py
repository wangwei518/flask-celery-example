import os
import re
import sys
import json
import requests


#URL_BASE = 'http://10.0.93.132:5000'
URL_BASE = 'http://127.0.0.1:5000'

def GetAllIp():
    url = URL_BASE+'/api/v1/ip'
    headers = {
        'Content-Type'  : 'application/vnd.api+json',
        'Accept'        : 'application/vnd.api+json',
    }
    r = requests.get(url, headers=headers)
    print('url=%s, r_stats=%d, r_text=%s' % (url, r.status_code, r.text))

def AddIp():
    url = URL_BASE+'/api/v1/ip'
    headers = {
        'Content-Type'  : 'application/vnd.api+json',
        'Accept'        : 'application/vnd.api+json',
    }
    payload = {
        'data': {
            'type' : 'ip',
            'attributes' : {
                'project'   : 'orca',
                'user'      : 'hank.wang',
                'path'      : '/proj/Orca/N_DigitalIP/uart_r1p0_01_000',
                'repo'      : 'http://10.0.93.132:3000/orca/manifests.git',
                'branch'    : '',
                'tag'       : '',
                'callback'  : 'http://127.0.0.1:5000/hook?id=4321&task_id=123456&status=200',
            }
        }
    }
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    print('url=%s, r_stats=%d, r_text=%s' % (url, r.status_code, r.text))

def DelelteIp():
    url = URL_BASE+'/api/v1/ip'
    headers = {
        'Content-Type'  : 'application/vnd.api+json',
        'Accept'        : 'application/vnd.api+json',
    }
    payload = {
        'data': {
            'type' : 'ip',
            'attributes' : {
                'project'   : 'orca',
                'user'      : 'hank.wang',
                'path'      : '/proj/Orca/N_DigitalIP/uart_r1p0_01_000',
                'callback'  : 'http://127.0.0.1:5000/hook?id=4321&task_id=123456&status=200',
            }
        }
    }
    r = requests.delete(url, data=json.dumps(payload), headers=headers)
    print('url=%s, r_stats=%d, r_text=%s' % (url, r.status_code, r.text))


def main():
    if 0:
        GetAllIp()
    if 0:
        AddIp()
    if 1:
        DelelteIp()

if __name__ == '__main__':
    main()
