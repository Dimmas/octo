# -*- coding: utf-8 -*-
import os
import paramiko


class LANhelper:
    port = 22

    def __init__(self, ip_address, user, pwd):
        self.ip = self.__ip_address = ip_address
        self._user = user
        self._pwd = pwd

        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # setup ssh-client connection to remote host
    def connect(self):
        try:  # try connect to remote host
            self.__client.connect(hostname=self.__ip_address, username=self._user, password=self._pwd, port=self.port)
            return True
        except Exception:
            return False

    # exec_command on remote host
    # used two parameters: cmd, lambda-function
    # lambda uses three parameters: responce after command executing, cmd, ip
    def exec_command(self, cmd, fn=False):
        stdin, stdout, stderr = self.__client.exec_command(cmd)
        data = stdout.read() + stderr.read()
        data = data.decode('utf8', 'ignore')
        if fn:
            return fn(data, cmd, self)
        return data

    # exec_command on remote host without responce
    # used two parameters: cmd, lambda-function
    # lambda uses two parameters: cmd, ip
    def silent_exec_command(self, cmd, fn=False):
        self.__client.exec_command(cmd)
        if fn:
            return fn(cmd, self)
        return True

    # check for a  package on a  remote host system
    def check_package(self, package_name):
        data = self.exec_command(f'dpkg -s  {package_name}')
        if 'Status: install ok installed' in data:
            return True
        elif f'пакет «{package_name}» не установлен' in data:
            return False

    # uninstall package_list from remote host
    def purge_package(self, package_list):
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

    # install packages to host
    def install_package(self, pkg):
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

    # copy file from host to octo
    def export_file(self, local_path, remote_path):
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

    # copy file from octo to host
    def import_file(self, remote_path, local_path):
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
