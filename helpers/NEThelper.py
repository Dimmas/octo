# !/usr/bin/python3.5
# -*- coding: utf-8 -*-

import os
from concurrent.futures import ThreadPoolExecutor
from helpers import LANhelper as lh, PKGhelper as ph, YAMLhelper as yh


class NEThelper:
    __actions = {'package': 'install, purge', 'file': 'import, export', 'cmd': False, 'scmd': False}  # dict of acceptable actions
    task_name = 'default'
    tsk_report_dir = 'tsk_reports/'

    def __init__(self, lan_list):
        self._lan_list = lan_list
        self._task_list = list()
        self.__success_list = set()

    # get ip of hosts, where tasks were completed from task file. Fill self.__success_list
    def _get_success_list(self):
        try:
            with open(self.tsk_report_dir+self.task_name) as success_file:
                self.__success_list = {ip.strip() for ip in success_file.readlines()}
        except Exception:
            self.__success_list = set()
        return self.__success_list

    # save self.__success_list to task file
    def _save_success_list(self, ip):
        self.__success_list.add(ip)
        try:
            with open(self.tsk_report_dir+self.task_name, 'w') as success_file:
                success_file.writelines('%s\n' % ip for ip in self.__success_list)
        except Exception:
            return False
        return True

    # check available actions in __actions dictionary and normalize parameters
    def _prepare_task(self, task):
        action, *other = task
        if not action in self.__actions.keys():
            return False
        if 'cmd' in action:
            if len(other) < 2:  # if lambda is not passed, then add to task one element
                task.append(False)
            return task
        event, param_list = other
        if not event in self.__actions.get(action):
            return False
        return task

    def add_task(self, task):
        task = self._prepare_task(task)
        if task:
            self._task_list.append(task)
            return True
        return False

    # start task_list for lan_list
    # parameter hard means that if any task fails, the following tasks on the host stop running
    def start_task(self, hard=False):
        for lan in self._lan_list:
            return self.start_task_list(lan, hard)

    # start task_list for lan_list in loopback
    # parameter hard means that if any task fails, the following tasks on the host stop running
    def loopback_task(self, hard=False):
        while True:
            return self.start_task()

    # start task for lan
    # parameter hard means that if any task fails, the following tasks on the host stop running
    def start_task_list(self, lan, hard=False):
        lan, ip_range, user, pwd = lan

        def host_tasks(ip, lan=lan, user=user, pwd=pwd):
            ip = lan + str(ip)  # generate next ip
            if ip in self._get_success_list():  # if host was completed on previous loop, than go to next host
                print(ip + ' ready')
                return True
            host = lh.LANhelper(ip, user, pwd)
            if host.connect():
                for task in self._task_list:
                    action, event, param_list = task
                    if action == 'package':
                        if event == 'install':
                            pkg = ph.PKGhelper(param_list)
                            if pkg.undiscovered_pkg:
                                print('packages ' + str(pkg.undiscovered_pkg) + ' not found')
                            if not pkg.found_pkg_list:
                                break
                            if not host.install_package(pkg) and hard:
                                break
                        if event == 'purge':
                            if not host.purge_package(param_list) and hard:
                                break
                    if action == 'file':
                        remote_path, local_path = param_list
                        if event == 'import':
                            if not host.import_file(remote_path, local_path) and hard:
                                break
                        if event == 'export':
                            if not host.export_file(local_path, remote_path) and hard:
                                break
                    if action == 'cmd':
                        print(host.exec_command(event, param_list))
                    if action == 'scmd':
                        print(host.silent_exec_command(event, param_list))
                else:
                    self._save_success_list(ip)  # if all tasks were completed, than add ip of host to success_list
            else:
                print(ip + ' connection refused')

        with ThreadPoolExecutor(16) as exe:
            exe.map(host_tasks, list(ip_range), timeout=120)

        return len(self.__success_list)


if __name__ == '__main__':

    settings = yh.YAMLhelper()
    networks = settings.get_networks()  # list of lan with ip_range, user_name, user_pass
    lan = NEThelper(networks)

    # reading and check action
    while True:
        action = int(input('Для работы с пакетами нажмите 1, файлами - 2, командами - 3: '))
        if not action in range(1, 4):
            print('ошибка ввода данных')
        else:
            break

    if action == 1:
        while True:
            event = int(input('Для установки пакетов нажмите 1, удаления - 2: '))
            if not event in range(1, 3):
                print('ошибка ввода данных')
            else:
                action += event * 10
                break
    if action == 2:
        while True:
            event = int(input('Для копирования файлов с удаленного хоста нажмите 1, на удаленный хост - 2: '))
            if not event in range(1, 3):
                print('ошибка ввода данных')
            else:
                action += event * 10
                break
    if action == 3:
        cmd = input('Введите команду для удаленного хоста: ')
        lan.add_task(['cmd', cmd])

    if action == 11 or action == 21:
        while True:
            package_list = input('ВВедите названия пакетов (через пробел): ').split(' ')
            error = False
            for package in package_list:
                data = os.popen('apt search ' + package + ' | grep -i ^' + package + '\/ ').read()
                if not package in data:
                    print(package + ' отсутствует в репозитории. Проверьте правильность имени пакета.')
                    error = True
            if not error:
                break
        if action == 11:
            lan.add_task(['package', 'install', package_list])
        if action == 21:
            lan.add_task(['package', 'purge', package_list])
    if action == 12:
        local_path = input('Введите путь к локальному каталогу назначения: ')
        remote_path = input('Введите путь к файлу на удаленном хосте: ')
        lan.add_task(['file', 'export', [local_path, remote_path]])
    if action == 22:
        remote_path = input('Введите путь к каталогу назначения на удаленном хосте: ')
        local_path = input('Введите путь к локальному файлу: ')
        lan.add_task(['file', 'import', [remote_path, local_path]])
