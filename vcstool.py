#!/usr/bin/env python

from __future__ import print_function

import argparse
import os
import subprocess
import sys
import rosinstall.multiproject_cmd as multiproject_cmd
import os
from rosinstall.config import Config, realpath_relation
from rosinstall.config_yaml import PathSpec

_PULL = 'pull'
_DIFF = 'diff'
_STAT = 'status'
_PUSH = 'push'

verbs = [
    _PUSH,
    _DIFF,
    _STAT,
    _PUSH
]

VCS_FILES = {
    'git': '.git',
    'hg': '.hg',
    'svn': '.svn',
}


# TODO use vcstools
def get_path_specs_from_filesystem(directory):
    path_specs = []
    for root, dirs, files in os.walk(directory, topdown=True):
        for vcs_type, vcs_file in VCS_FILES.items():
            if vcs_file in dirs or vcs_file in files:
                for dir_name in list(dirs):
                    # Do not process subdirectories
                    dirs.remove(dir_name)
                path_specs.append(PathSpec(local_name=root, scmtype=vcs_type, path=root, uri='/<not set>'))
                break
    return path_specs


def get_filesystem_config(basepath):
    base_path_specs = get_path_specs_from_filesystem(basepath)
    config = Config(base_path_specs, basepath)
    return config


def main(sysargs=None):
    '''
    Lightweight recursive vcs invocation tool.
    will call given command type on all SCm directories it finds under a given folder.
    '''
    global jobs
    parser = argparse.ArgumentParser(description="Batch VCS abstraction tool")
    add = parser.add_argument
    add('verb', help="VCS action to take")
    add('directory', default=os.getcwd(), nargs='?',
        help="Directory on which to search")
    args = parser.parse_args(sysargs)

    verb = args.verb
    if verb not in verbs:
        print("Invalid verb '%s', must be in %s" % (verb, str(verbs)))
        return 1
    directory = os.path.abspath(args.directory)

    # Walk the directory
    if not os.path.exists(directory):
        print("Path '%s' does not exist." % directory)
        return 1
    print("Doing %s on: %s" % (verb, directory))
    config = get_filesystem_config(directory)
    if verb == _STAT:
        statuslist = multiproject_cmd.cmd_status(config)
        allstatus = ""
        for entrystatus in statuslist:
            if entrystatus['status'] is not None:
                allstatus += entrystatus['status']
        print(allstatus, end='')
    if verb == _DIFF:
        difflist = multiproject_cmd.cmd_diff(config)
        alldiff = []
        for entrydiff in difflist:
            if entrydiff['diff'] is not None and entrydiff['diff'] != '':
                alldiff.append(entrydiff['diff'])
        print('\n'.join(alldiff))
    if verb == _PULL:
        multiproject_cmd.cmd_update(config)
    # if verb == _PUSH
        # TODO: extend classes or use workaround
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
