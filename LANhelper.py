# -*- coding: utf-8 -*-

import paramiko

class LANhelper:
        port = 22
        
        def __init__(self, ip_address, user, pwd):
                self.__ip_address = ip_address
                self._user = user
                self._pwd = pwd

                self.__file_buffer = '/home/' + user + '/'
                self.__client = paramiko.SSHClient()
                self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                                

        #  setup ssh-client connection to remote host
        def connect(self):
                try: # try to connect to remote host
                        self.__client.connect(hostname=self.__ip_address, username = self._user, password = self._pwd, port = self.port)
                        return True
                except Exception:
                        return False


        # exec_command on remote host
        # used two parameters: cmd, lambda-function
        # lambda eses three parameters: responce after command executing, cmd, ip
        def exec_command(self, cmd, fn = False):
                stdin, stdout, stderr = self.__client.exec_command(cmd)
                data = stdout.read() + stderr.read()
                data = data.decode('utf8', 'ignore')
                if fn:
                        return fn(data, cmd, self.__ip_address)
                return data


        # exec_command on remote host without responce
        # used two parameters: cmd, lambda-function
        # lambda uses two parameters: cmd, ip
        def silent_exec_command(self, cmd, fn = False):
                self.__client.exec_command(cmd)
                if fn:
                        return fn(cmd, self.__ip_address)
                return True


        # check for a  package on a  remote host system
        def check_package(self, package_name):
                data = self.exec_command('dpkg -s  ' + package_name)
                if 'Status: install ok installed' in data:
                        return True
                elif 'пакет «'+package_name+'» не установлен' in data:
                        return False


        # uninstall package_list from remote host
        def purge_package(self, package_list):
                rezult = True
                for package in package_list:
                        if self.check_package(package):
                                self.exec_command('sudo dpkg -r ' + package)
                                if self.check_package(package):
                                        print(self.__ip_address + ' error: ' + package + ' not removed')
                                        rezult = False
                                else:
                                        print(self.__ip_address + ' ' + package + ' removed')
                        else:
                                print(self.__ip_address + ' ' + package + ' package is missing')
                return rezult


        # install package_list tohost remote 
        def  install_package(self, package_list):
                rezult = True
                for package in package_list:
                        if self.check_package(package):
                                print( self.__ip_address + ' ' + package + ' installed')
                        else:
                                data = self.exec_command('sudo apt-get --assume-yes install ' + package)
                                if 'Не удалось найти пакет '+ package in data:
                                        print(self.__ip_address + ' ' + package + ' not founded in repository')
                                        rezult = False
                                if self.check_package(package):
                                        print(self.__ip_address + ' ' + package + ' installed')    
                                else:
                                        print(self.__ip_address + ' error: ' + package + ' not installed')
                                        rezult = False
                return rezult


        # copy file to remote host from local mashine
        def export_file(self, local_path, remote_path):
                sftp = self.__client.open_sftp()
                try:
                        file_name = local_path.split('/')[-1]
                        sftp.get(remote_path, self.__file_buffer + file_name)
                        self.exec_command('sudo mv ' + self.__file_buffer + file_name + ' ' + local_path)
                except Exception as e:
                        sftp.close()
                        print(self.__ip_address + ' ' + remote_path + ' file wasn\'t exported: ' + str(e))
                        return False
                print(self.__ip_address + ' ' + remote_path + ' file was exported success')
                return True


        # copy file from remote host to local mashine
        def import_file(self, remote_path, local_path):
                sftp = self.__client.open_sftp()
                try:
                        file_name = remote_path.split('/')[-1]
                        sftp.put(local_path, self.__file_buffer + file_name)
                        self.exec_command('sudo mv ' + self.__file_buffer + file_name + ' ' + remote_path)
                except Exception as e:
                        sftp.close()
                        print(self.__ip_address + ' ' + local_path + ' file wasn\'t imported: ' + str(e))
                        return False
                print(self.__ip_address + ' ' + local_path + ' file was imported success')
                return True


        # close connection
        def __del__(self):
                        self.__client.close()
