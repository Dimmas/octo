from ipaddress import IPv4Network
from concurrent.futures import ThreadPoolExecutor
from helpers import LANhelper as lh, PKGhelper as ph


class NEThelper:
    __actions = {'package': 'install, purge', 'file': 'import, export', 'cmd': False, 'scmd': False}  # dict of acceptable actions
    task_name = 'default'
    tsk_report_dir = 'tsk_reports/'
    hard = False # parameter hard means that if any task fails, the following tasks on the host stop running

    def __init__(self, networks):
        self._networks = networks
        self._task_list = list()
        self.__success_list = set()

    def _get_success_list(self) -> set:
        """
        get ip of hosts, where tasks were completed from task file (tsk_reports/self.task_name). Fill self.__success_list

        :return: a list of ip addresses of hosts on which the task was completed successfully.
        """
        try:
            with open(self.tsk_report_dir+self.task_name) as success_file:
                self.__success_list = {ip.strip() for ip in success_file.readlines()}
        except Exception:
            self.__success_list = set()
        return self.__success_list

    def _save_success_list(self, ip: str) -> bool:
        """
        saves the ip addresses of the hosts on which the tasks were completed successfully to a file.
        The file is named = tsk_reports/self.task_name. When the task is restarted, hosts with ip addresses from the file are skipped.

        :param ip: the ip address of the host where all tasks were completed successfully.
        :return: true if writing to the file is successful and false otherwise.
        """
        self.__success_list.add(ip)
        try:
            with open(self.tsk_report_dir+self.task_name, 'w') as success_file:
                success_file.writelines(f'{ip}\n' for ip in self.__success_list)
        except Exception:
            return False
        return True

    def _prepare_task(self, task: list):
        """
        check available actions in __actions dictionary and normalize parameters

        :param task: the list is a formalized representation of the task
        :return: normalize parameters or false, if actions is not exists in __actions
        """
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

    def add_task(self, task: list) -> bool:
        """
        Checks the array representation of the task and adds it to the task queue for subsequent execution on the network nodes.

        :param task: the list is an image of the task.
            Examples:
                ['package', 'install', ['antiword', 'python-libxslt1', 'odt2txt', 'wv', 'docx2txt']]
                ['package', 'purge', ['antiword', 'python-libxslt1', 'odt2txt', 'wv', 'docx2txt']]
                ['file', 'import', ['/some_path/somefile', 'exfiles/somefile']]
                ['file', 'export', ['/some_path/somefile', 'exfiles/somefile']]
                ['cmd', 'sudo service cron reload', lambda responce, cmd, lh: f'{lh.ip} {cmd}: {responce}']
        :return: result of adding a task to the queue
        """
        task = self._prepare_task(task)
        if task:
            self._task_list.append(task)
            return True
        return False


    def start_task(self, fn) -> int:
        """
        task queue execution starts for each of the ip networks

        :param fn: callback function for exception handling
        :return: number of hosts on which all tasks were completed successfully
        """
        def wrapped():
            for lan in self._networks:
                try:
                    return self.start_task_list(**lan)
                except Exception as e:
                    return self.start_task_list(lan=lan['lan'], **fn(e))
        return wrapped


    def start_task_list(self, **lan_param) -> int:
        """
        Bypasses network nodes and executes a queue of tasks on each.

        :param lan_param: ip network address with a prefix, usr - the user's login, pwd - his password
        :return: number of hosts on which all tasks were completed successfully
        """
        if not 'usr' in lan_param:
            raise EmptyUsrException(lan_param)
        if not 'pwd' in lan_param:
            raise EmptyPwdException(lan_param)

        lan = IPv4Network(lan_param['lan'])
        ip_range = [str(ip) for ip in lan.hosts()]

        def host_tasks(ip, user=lan_param['usr'], pwd=lan_param['pwd']):
            if ip in self._get_success_list():  # if host was completed on previous loop, than go to next host
                print(f'{ip} ready')
                return True
            host = lh.LANhelper(ip, user, pwd)
            if host.connect():
                for task in self._task_list:
                    action, event, param_list = task
                    if action == 'package':
                        if event == 'install':
                            pkg = ph.PKGhelper(param_list)
                            if pkg.undiscovered_pkg:
                                print(f'packages {str(pkg.undiscovered_pkg)} not found')
                            if not pkg.found_pkg_list:
                                break
                            if not host.install_package(pkg) and self.hard:
                                break
                        if event == 'purge':
                            if not host.purge_package(param_list) and self.hard:
                                break
                    if action == 'file':
                        remote_path, local_path = param_list
                        if event == 'import':
                            if not host.import_file(remote_path, local_path) and self.hard:
                                break
                        if event == 'export':
                            if not host.export_file(local_path, remote_path) and self.hard:
                                break
                    if action == 'cmd':
                        print(host.exec_command(event, param_list))
                    if action == 'scmd':
                        print(host.silent_exec_command(event, param_list))
                else:
                    self._save_success_list(ip)  # if all tasks were completed, than add ip of host to success_list
            else:
                print(f'{ip} connection refused')

        with ThreadPoolExecutor(16) as exe:
            exe.map(host_tasks, ip_range, timeout=120)

        return len(self.__success_list)


class EmptyUsrException(Exception):
    def __init__(self, lan_param):
        self.lan = lan_param['lan']
        super().__init__()


class EmptyPwdException(Exception):
    def __init__(self, lan_param):
        self.lan = lan_param['lan']
        self.usr = lan_param['usr']
        super().__init__()

