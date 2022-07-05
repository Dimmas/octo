#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

import argparse
import os

from helpers.NEThelper import *
from helpers.DBhelper import File
from helpers.YAMLhelper import YAMLhelper

networks = YAMLhelper().get_networks()  # list of lan with ip_range, user_name, user_pass
net = NEThelper(networks)
net.hard = True # abort task queue execution if at least one task failed


# let's describe the exception handling process in the method net.start_task()
@net.start_task
def start_task(e):
    pwd = False
    if isinstance(e, EmptyPwdException):
        usr = e.usr
    if isinstance(e, EmptyUsrException):
        if env_usr == 'default':
            total_account = YAMLhelper().get_user()
            if not total_account:
                usr = input(f'enter username for {e.lan}: ')
            else:
                usr = total_account['usr']
                if 'pwd' in total_account:
                    pwd = total_account['pwd']
        else:
            usr = env_usr
            if env_pwd != 'default':
                pwd = env_pwd
    if not pwd:
        import getpass
        pwd = getpass.getpass(f'enter password for {usr}@{e.lan}: ')
    return {'usr': usr, 'pwd': pwd}


def install():
    net.task_name = 'install'
    net.add_task(['package', 'install', ['antiword', 'python-libxslt1', 'odt2txt', 'wv', 'docx2txt']])  # delivery to each host required packages for recoll
    net.add_task(['cmd', 'sudo mkdir /root/.recoll', lambda responce, cmd, lh: f'{lh.ip} {str(cmd)}: {str(responce)}'])
    net.add_task(['file', 'import', ['/root/.recoll/recoll.conf', 'exfiles/recoll.conf']])  # delivery to each host recoll.conf
    net.add_task(['file', 'import', ['/var/spool/cron/crontabs/root', 'exfiles/root']])  # delivery to each host cron task for daily indexindg files
    net.add_task(['cmd', 'sudo service cron reload', lambda responce, cmd, lh: f'{lh.ip} {cmd}: {responce}'])
    net.add_task(['scmd', 'sudo RECOLL_CONFDIR="/root/.recoll" recollindex', lambda cmd, lh: f'{lh.ip} {str(cmd)} - was srtarted'])  # hands start task for indexing files on remote host
    return start_task()


def search(request):
    net.task_name = 'search'
    net.add_task(['cmd', f'recollq -m \'request\'', push_db])
    return start_task()


def reload_cron():
    net.task_name = 'reload_cron'
    net.add_task(['file', 'import', ['/var/spool/cron/crontabs/root', 'exfiles/root']])  # delivery to each host cron task for daily indexindg files
    net.add_task(['cmd', 'sudo service cron reload', lambda responce, cmd, lh: f'{lh.ip} {cmd} : {responce}'])
    return start_task()


def index():
    net.task_name = 'octo_index'
    net.add_task(['scmd', 'sudo RECOLL_CONFDIR="/root/.recoll" recollindex', lambda cmd, lh: f'{lh.ip} {str(cmd)}\n'])  # hands start task for indexing files on remote host
    return start_task()


# recording results of searching to DB
def push_db(responce, cmd, lh):
    def write_db(prop):
        prop['ip'] = lh.ip
        prop['rcludi'] = prop['rcludi'].replace('|', '')
        expansion = os.path.splitext(prop['rcludi'])[1]
        fn = lambda responce, cmd, lh: None if prop['rcludi'] in responce else responce  # return None if octo can't get file content
        if expansion == '.odt':
            prop['text'] = lh.exec_command('odt2txt "' + prop['rcludi'] + '"', fn)
        if expansion == '.docx':
            prop['text'] = lh.exec_command('docx2txt "' + prop['rcludi'] + '" -', fn)
        if expansion == '.doc':
            prop['text'] = lh.exec_command('antiword "' + prop['rcludi'] + '"', fn)
        file_record = File({'url': prop['url'], 'ip': lh.ip})  # check DB for existing record width this properties
        return file_record.add(prop)

    fcount = 0
    prop = {}  # file properties parsed from recoll output
    fields = File.properties  # read fields for file object
    for line in responce.split('\n'):
        par = line.split(' = ')
        if par[0] in fields:
            if par[0] in prop.keys():
                if write_db(prop): fcount += 1
                prop = {}
            prop[par[0]] = par[1]
    if write_db(prop): fcount += 1  # write to DB last result, or the only result
    return f'{lh.ip} scan completed ({str(fcount)} results)'


if __name__ == '__main__':
    # Check OS Environment for Docker
    action = os.getenv('OCTO_MODE', 'default')
    request = os.getenv('OCTO_REQUEST', 'default')
    env_usr = os.getenv('OCTO_USR', 'default')
    env_pwd = os.getenv('OCTO_PWD', 'default')

    # Check CLI parameters
    if action == 'default':
        parser = argparse.ArgumentParser(
            description='Octo - network search and classified service. Designed for classifying texts by meaning')
        parser.add_argument('action', type=str, nargs='?', default='default',
                            help='[install] - install octo to hosts in LAN'
                                 '[search] - search for files on LAN by the occurrence of keywords'
                                 '[rc] - change cron tab and reload cron service'
                                 '[index] - start indexing file system on hosts of the LAN')
        parser.add_argument('request', type=str, nargs='?', default='default', help='Search query')
        args = parser.parse_args()
        action = args.action
        request = args.request
        action = int(input('ACTIONS:\ninstall octo - 1\nscan hosts - 2\nreload cron - 3\nindex hosts - 4\nEnter action: '))

    if action == 1 or action == 'install':
        print('*** Start install octo ***')
        print(f'Install Octo is completed successfully on {str(install())} hosts')
    if action == 2 or action == 'search':
        if request == 'default':
            request = input('Enter a search query: ')
        print('*** Start scan network hosts ***')
        print(f'Scan is completed on {str(search(request))} hosts')
    if action == 3 or action == 'rc':
        print('*** Start reload cron  on network hosts ***')
        print(f'reload_cron is completed on {str(reload_cron())} hosts')
    if action == 4 or action == 'index':
        print('*** Start index hosts ***')
        print(f'Indexing is completed on {str(index())} hosts')

