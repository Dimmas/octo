# -*- coding: utf-8 -*-
import os
import paramiko
import helpers.PKGhelper as PKGhelper


class LANhelper:
    port = 22

    def __init__(self, ip_address, user, pwd):
        self.ip = self.__ip_address = ip_address
        self._user = user
        self._pwd = pwd

        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self) -> bool:
        """
        setup ssh-client connection to remote host

        :return: true if ssh connection to the host is successfully established and false if there is no such connection
        """
        try:
            self.__client.connect(hostname=self.__ip_address, username=self._user, password=self._pwd, port=self.port)
            return True
        except Exception:
            return False

    def exec_command(self, cmd: str, fn=False) -> str:
        """
        executing a terminal command on a remote host.

        :param cmd: command to the remote host to execute in the terminal
        :param fn: а function for processing the result returned after executing a command in a terminal on a remote host.
            The callback function accepts three parameters: the result of executing a terminal command on a remote host, the command itself, and an object of the helpers.LANhelper.
        :return: the result of executing a terminal command on a remote host.
        """
        stdin, stdout, stderr = self.__client.exec_command(cmd)
        data = stdout.read() + stderr.read()
        data = data.decode('utf8', 'ignore')
        if fn:
            return fn(data, cmd, self)
        return data

    def silent_exec_command(self, cmd: str, fn=False) -> bool:
        """
        executing a terminal command on a remote host in silent mode.

        :param cmd: command to the remote host to execute in the terminal
        :param fn: а function for processing the result returned after executing a command in a terminal on a remote host.
            The callback function accepts two parameters: a terminal command on a remote host, the command itself, and an object of the helpers.LANhelper.
        :return: Returns true if the task was run on a remote host and false otherwise.
        """
        self.__client.exec_command(cmd)
        if fn:
            return fn(cmd, self)
        return True

    # check for a  package on a  remote host system
    def check_package(self, package_name: str) -> bool:
        """
        checks whether the specified package is installed on the remote host

        :param package_name: package name
        :return: true - if the package is installed on the remote host and false otherwise.
        """
        data = self.exec_command(f'dpkg -s  {package_name}')
        if 'Status: install ok installed' in data:
            return True
        elif f'пакет «{package_name}» не установлен' in data:
            return False

    def purge_package(self, package_list: list) -> bool:
        """
        uninstall packages from remote host

        :param package_list: list of packages to remove
        :return: true if all packages are successfully deleted and false otherwise.
        """
        result = True
        for package in package_list:
            if self.check_package(package):
                self.exec_command(f'sudo dpkg -r {package}')
                if self.check_package(package):
                    print(f'{self.__ip_address} error: {package} not removed')
                    result = False
                else:
                    print(f'{self.__ip_address} package removed')
            else:
                print(f'{self.__ip_address} {package} package is missing')
        return result

    def install_package(self, pkg: PKGhelper) -> bool:
        """
        install packages to remote host

        :param pkg: object of helpers.PKGhelper
        :return: true if all packages are successfully installed and false otherwise.
        """
        result = True
        for package in pkg.found_pkg_list:
            if self.check_package(package):
                print(f'{self.__ip_address} {package} installed')
            else:
                if pkg.source(package) == 'repo':
                    self.exec_command(f'sudo apt-get --assume-yes install {package}')
                else:
                    pkg_path = pkg.get_path(package)
                    try:
                        self.import_file(pkg_path, pkg_path)
                        if pkg.type(package) == 'file':
                            self.exec_command(f'sudo dpkg -i {pkg_path}')
                        else:
                            self.exec_command(f'sudo dpkg -i {pkg_path}/*')
                    except Exception as e:
                        print(str(e))

                if self.check_package(package):
                    print(f'{self.__ip_address} {package} installed')
                else:
                    print(f'{self.__ip_address} error: {package} not installed')
                    result = False
        return result

    def export_file(self, local_path: str, remote_path: str) -> bool:
        """
        copy file from remote host to host with octo

        :param local_path: path to file on host with octo
        :param remote_path: path to file on remote host
        :return: true if the file export was successful and false otherwise.
        """
        sftp = self.__client.open_sftp()
        try:
            file_name = local_path.split('/')[-1]
            sftp.get(remote_path, file_name)
        except Exception as e:
            sftp.close()
            print(f'{self.__ip_address} {remote_path} file not exported: {str(e)}')
            return False
        print(f'{self.__ip_address} {remote_path} file exported success')
        sftp.close()
        return True

    def import_file(self, remote_path: str, local_path: str) -> bool:
        """
        copy file from host with octo to remote host

        :param remote_path: path to file on remote host
        :param local_path: path to file on host with octo
        :return: true if the file import was successful and false otherwise.
        """
        sftp = self.__client.open_sftp()
        try:
            path = os.path.split(local_path)
            # creat directory for importing file on host
            pf = ''
            for p in path[0].split('/'):
                pf += p + '/'
                try:
                    sftp.mkdir(pf)
                except IOError:
                    pass

            file_name = path[1]
            # recursive import files from subcategories
            if os.path.isdir(remote_path):
                for f in os.listdir(remote_path):
                    self.import_file(f'{local_path}/{f}', f'{remote_path}/{f}')
            else:
                sftp.put(local_path, file_name)
                self.exec_command(f'sudo mv {file_name} {remote_path}')
        except Exception as e:
            sftp.close()
            print(f'{self.__ip_address} {local_path} file not imported: {str(e)}')
            return False
        print(f'{self.__ip_address} {local_path} file was imported success')
        sftp.close()
        return True

    # close connection
    def __del__(self):
        self.__client.close()
