import glob
import os

from apt_repo import APTSources, APTRepository


class PKGhelper:
    source_list = '/etc/apt/sources.list'
    local_repo = 'packages/'

    def __init__(self, package_list):
        self.package_list = package_list
        self.found_pkg_list = dict()
        self.undiscovered_pkg = list()
        try:
            self.check()
        except Exception as e:
            print(str(e))

    def check(self, package_list: list=None):
        """
        checks for packages passed by the package_list list in the network repository.
        If the package is not found in the network repository, it searches in the local packages directory

        :param package_list: list of packages names for check
        :return: puts to list.found_pkg_list[package] dictionary with data about the location of the package.
            For example:
            self.found_pkg_list['mc'] = {'path': None, 'source': 'repo', 'type': None} - if package mc consists in network repository
            self.found_pkg_list['wv'] = {'path': 'packages/wv', 'source': 'local', 'type': 'dir'} - if package wv consists in packages/ and you need to install all the packages from the directory packages/wv/
            self.found_pkg_list['antiword'] = {'path': 'packages/antiword_0.37-11+b1_amd64.deb', 'source': 'local', 'type': 'file'} - if deb-file of package antiword consists in packages/
        """
        package_list = package_list if package_list else self.package_list
        if not package_list: return False
        # check local package repository
        for package in package_list:
            path = glob.glob(self.local_repo + package + '*')[0]
            if not path:
                # check network repository
                if not self.check_apt(package):
                    self.undiscovered_pkg.append(package)
                    continue
                self.found_pkg_list[package] = {'path': None, 'source': 'repo', 'type': None}
            else:
                pkg_type = 'dir' if os.path.isdir(path) else 'file'
                self.found_pkg_list[package] = {'path': path, 'source': 'local', 'type': pkg_type}

    def check_apt(self, package: str, source_list: str=None) -> list:
        """
        сhecks for the presence of the package in the network repository.

        :param package: package name
        :param source_list: path to apt sources.list (default: '/etc/apt/sources.list')
        :return: list of packages found
        """
        if not source_list: source_list = self.source_list
        if isinstance(source_list, str):
            if os.path.isfile(source_list):
                sources = APTSources([APTRepository.from_sources_list_entry(line.replace('\n', '')) for line in
                                      open(source_list, "r").readlines() if line != '\n' and line[0] != '#'])
            else:
                sources = APTSources([APTRepository.from_sources_list_entry(source_list)])
        if isinstance(source_list, list):
            sources = APTSources([APTRepository.from_sources_list_entry(source) for source in source_list])
        pkg_list = [(pkg.package, pkg.version) for pkg in sources.get_packages_by_name(package)]
        return pkg_list

    def get_path(self, package: str) -> str:
        """

        :param package: package name
        :return: path to package files in directory packages/
        """
        return self.found_pkg_list[package]['path']

    def type(self, package: str) -> str:
        """

        :param package: package name
        :return: information about what a package is:
            'file' - for deb file
            'dir' - for  directory with deb files in directory packages/
        """
        return self.found_pkg_list[package]['type']

    def source(self, package: str) -> str:
        """

        :param package: package name
        :return: information about the location of the package:
            'repo' - if the package is found in network repository
            'local' - if the package is found in directory packages/
        """
        return self.found_pkg_list[package]['source']
