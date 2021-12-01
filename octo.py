#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import os
from helpers import NEThelper as nh, DBhelper as db, YAMLhelper as yh

networks = yh.YAMLhelper().get_networks()  # list of lan with ip_range, user_name, user_pass
lan = nh.NEThelper(networks)


def install():
    lan.task_name = 'install'
    lan.add_task(['package', 'install', ['antiword', 'python-libxslt1', 'odt2txt', 'wv', 'docx2txt']])  # delivery to each host required packages for recoll
    lan.add_task(['cmd', 'sudo mkdir /root/.recoll', lambda responce, cmd, lh: lh.ip + ' ' + str(cmd) + ': ' + str(responce)])
    lan.add_task(['file', 'import', ['/root/.recoll/recoll.conf', 'exfiles/recoll.conf']])  # delivery to each host recoll.conf
    lan.add_task(['file', 'import', ['/var/spool/cron/crontabs/root', 'exfiles/root']])  # delivery to each host cron task for daily indexindg files
    lan.add_task(['cmd', 'sudo service cron reload', lambda responce, cmd, lh: lh.ip + ' ' + cmd + ' : ' + responce])
    lan.add_task(['scmd', 'sudo RECOLL_CONFDIR="/root/.recoll" recollindex', lambda cmd, lh: lh.ip + ' ' + str(cmd) + ' - was srtarted'])  # hands start task for indexing files on remote host
    return lan.start_task(True)


def search(request):
    lan.task_name = 'search'
    lan.add_task(['cmd', 'sudo recollq -m \'' + request + '\'', push_db])
    return lan.start_task(True)


def reload_cron():
    lan.task_name = 'reload_cron'
    lan.add_task(['file', 'import', ['/var/spool/cron/crontabs/root', 'exfiles/root']])  # delivery to each host cron task for daily indexindg files
    lan.add_task(['cmd', 'sudo service cron reload', lambda responce, cmd, lh: lh.ip + ' ' + cmd + ' : ' + responce])
    return lan.start_task(True)


def index():
    lan.task_name = 'octo_index'
    lan.add_task(['scmd', 'sudo RECOLL_CONFDIR="/root/.recoll" recollindex', lambda cmd, lh: lh.ip + ' ' + str(cmd) + ' \n'])  # hands start task for indexing files on remote host
    return lan.start_task(True)


# recording results of searching to DB
def push_db(responce, cmd, lh):
    def write_db(prop):
        prop['ip'] = lh.ip
        prop['rcludi'] = prop['rcludi'].replace('|', '')
        expansion = os.path.splitext(prop['rcludi'])[1]
        fn = lambda responce, cmd, lh: None if prop['rcludi'] in responce else responce  # return None if octo can't get file content
        if expansion == '.odt':
            prop['text'] = lh.exec_command('sudo odt2txt "' + prop['rcludi'] + '"', fn)
        if expansion == '.docx':
            prop['text'] = lh.exec_command('sudo docx2txt "' + prop['rcludi'] + '" -', fn)
        if expansion == '.doc':
            prop['text'] = lh.exec_command('sudo antiword "' + prop['rcludi'] + '"', fn)
        file_record = db.File({'url': prop['url'], 'ip': lh.ip})  # check DB for existing record width this properties
        return file_record.add(prop)

    fcount = 0
    prop = {}  # file properties parsed from recoll output
    fields = db.File.properties  # read fields for file object
    for line in responce.split('\n'):
        fo = line.split(' = ')
        if fo[0] in fields:
            if fo[0] in prop.keys():
                if write_db(prop): fcount += 1
                prop = {}
            prop[fo[0]] = fo[1]
    if write_db(prop): fcount += 1  # write to DB last result, or the only result
    return lh.ip + ' scan completed (' + str(fcount) + ' results)'


if __name__ == '__main__':
    # Check OS Environment for Docker
    action = os.getenv('OCTO_MODE', 'default')
    request = os.getenv('OCTO_REQUEST', 'default')

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
        print('Install Octo is completed successfully on ' + str(install()) + ' hosts')
    if action == 2 or action == 'search':
        if request == 'default':
            request = input('Enter a search query: ')
        print('*** Start scan network hosts ***')
        print('Scan is completed on ' + str(search(request)) + ' hosts')
    if action == 3 or action == 'rc':
        print('*** Start reload cron  on network hosts ***')
        print('reload_cron is completed on ' + str(reload_cron()) + ' hosts')
    if action == 4 or action == 'index':
        print('*** Start index hosts ***')
        print('Indexing is completed on ' + str(index()) + ' hosts')
