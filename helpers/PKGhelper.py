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

    def check(self, package_list=None):
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

    def check_apt(self, package, source_list=None):
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

    def get_path(self, package):
        return self.found_pkg_list[package]['path']

    def type(self, package):
        return self.found_pkg_list[package]['type']

    def source(self, package):
        return self.found_pkg_list[package]['source']
