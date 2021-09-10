#!/usr/bin/python3
# -*- coding: utf-8 -*-

import NEThelper as nh
import DBoctopus as db
import argparse
import os

lan_list = [['0.0.0.', range(2, 16), 'local_host_admin', 'pass']]  # list of lan with ip_range, user_name, user_pass
lan = nh.NEThelper(lan_list)

def install():
    lan.task_name = 'octo_install'
    lan.add_task(['package', 'install', ['antiword', 'python-libxslt1']]) # delivery to each host required packages for recoll
    lan.add_task(['cmd', 'sudo mkdir /root/.recoll', lambda responce, cmd, ip: ip + ' '+str(cmd)+': '+str(responce)])
    lan.add_task(['file', 'import', ['/root/.recoll/recoll.conf', '/root/.recoll/recoll.conf']])  # delivery to each host recoll.conf
    lan.add_task(['file', 'import', ['/etc/crontab', '/etc/crontab']])  # delivery to each host cron task for daily indexindg files
    lan.add_task(['cmd', 'sudo service cron reload', lambda responce, cmd, ip: ip+' '+cmd+' : '+responce])
    lan.add_task(['scmd', 'sudo RECOLL_CONFDIR="/root/.recoll" recollindex', lambda cmd, ip: ip +' ' + str(cmd) +' - was srtarted'])  # hands start task for indexing files on remote host
    return lan.start_task(True)


def search(request):
    lan.task_name = 'octo_search'
    lan.add_task(['cmd', 'sudo recollq -m \'' + request + '\'', flush_db])
    return lan.start_task(True)


def reload_cron():
    lan.task_name = 'octo_cron_restart'
    lan.add_task(['file', 'import', ['/etc/crontab', '/etc/crontab']]) # delivery to each host cron task for daily indexindg files
    lan.add_task(['cmd', 'sudo service cron reload', lambda responce, cmd, ip: ip +' '+ cmd +' : '+responce])
    return lan.start_task(True)


def index():
    lan.task_name = 'octo_index'
    lan.add_task(['scmd', 'sudo RECOLL_CONFDIR="/root/.recoll" recollindex', lambda cmd, ip: ip +' '+str(cmd) +' \n']) # hands start task for indexing files on remote host
    return lan.start_task(True)

# recording results of searching to DB
def flush_db(responce, cmd, ip):
    i = fcount = 0
    prop = {}  # file properties parsed from recoll output
    fields = db.File.properties  # read fields for file object
    for line in responce.split('\n'):
        fo = line.split(' = ')
        if fo[0] in fields:
            i += 1
            prop[fo[0]] = fo[1]
            if i == len(fields):
                prop['ip'] = ip
                file_record = db.File({'url': prop['url'], 'ip': ip}) #check DB for existing record width this properties
                if file_record.add(prop): fcount += 1
                i = 0
                prop = {}
    return ip + ' scaning complete ('+str(fcount)+' results)'


if __name__ == '__main__':
    # Check OS Environment for Docker
    action = os.getenv('OCTO_MODE', 'default')
    request = os.getenv('OCTO_REQUEST', 'default')

    # Check CLI parameters
    if action == 'default':
        parser = argparse.ArgumentParser(description='Octo - network search and classified service. Designed for classifying texts by meaning')
        parser.add_argument('action', type=str, nargs='?', default='default', help='[install] - install octo to hosts in LAN'
                                                                                   '[search] - search for files on LAN by the occurrence of keywords'
                                                                                   '[rc] - change cron tab and reload cron service'
                                                                                   '[index] - start indexing file system on hosts of the LAN')
        parser.add_argument('request', type=str, nargs='?', default='default', help='Search query')
        args = parser.parse_args()
        action = args.action
        request = args.request

    if action == 'default':
        action = int(input('Выберите действие:\nустановка octo - 1\nсканирование хостов - 2\nreload cron - 3\nindex hosts - 4\nВведите действие: '))

    if action == 1 or action == 'install':
        print('*** Старт установки octo ***')
        print('Установка Octo выполнена успешно на ' + str(install()) + ' узлах')
    if action == 2 or action == 'search':
        if request == 'default':
            request = input('Введите поисковый запрос: ')
        print('*** Старт сканирования хостов сетей ***')
        print('Сканирование выполнено на ' + str(search(request)) + ' узлах')
    if action == 3 or action == 'rc':
        print('*** Старт reload cron на хостах ***')
        print('reload_cron выполнено на ' + str(reload_cron()) + ' узлах')
    if action == 4 or action == 'index':
        print('*** Старт индексирования хостов ***')
        print('Индексирование выполнено на ' + str(index()) + ' узлах')
