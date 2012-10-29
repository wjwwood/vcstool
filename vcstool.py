#!/usr/bin/env python

from __future__ import print_function

import argparse
import os
import subprocess
import sys

verbs = [
    'pull',
    'diff',
    'status',
    'push'
]

git_cmds = {
    'pull':   'git pull',
    'diff':   'git diff',
    'status': 'git status',
    'push':   'git push',
}

hg_cmds = {
    'pull':   'hg pull -u',
    'diff':   'hg diff',
    'status': 'hg status',
    'push':   'hg push',
}

svn_cmds = {
    'pull':   'svn up',
    'diff':   'svn diff',
    'status': 'svn status',
    'push':   '',
}

cmds = {
    'git': git_cmds,
    'hg': hg_cmds,
    'svn': svn_cmds
}

vcs_files = {
    'git': '.git',
    'hg': '.hg',
    'svn': '.svn',
}

jobs = {}


def find(file_name):
    path = os.getenv('PATH')
    for directory in path.split(':'):
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            return file_path
    raise OSError("Could not find {0}: No such file or ".format(file_name) +
                  "directory")


def kick_off(vcs_type, verb, directory):
    global jobs
    cmd = cmds[vcs_type][verb].split()
    if not cmd:
        cmd = ['echo', '"' + verb + ' Not implemented for ' + vcs_type + '"']
    cmd[0] = find(cmd[0])
    p = subprocess.Popen(cmd, shell=False, cwd=directory,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    jobs[p.pid] = {
        'name': os.path.basename(os.path.normpath(directory)),
        'type': vcs_type,
        'p': p
    }


def main(sysargs=None):
    global jobs
    parser = argparse.ArgumentParser(description="Batch VCS abstraction tool")
    add = parser.add_argument
    add('verb', help="VCS action to take")
    add('directory', default=os.getcwd(), nargs='?',
        help="Directory on which to search")
    args = parser.parse_args(sysargs)

    verb = args.verb
    if verb not in verbs:
        print("Invalid verb '" + verb + "', must be in " + str(verbs))
        return 1
    directory = os.path.abspath(args.directory)

    # Walk the directory
    if not os.path.exists(directory):
        print("Path '" + directory + "' does not exist.")
        return 1
    print("Doing " + verb + " on:", directory)
    for root, dirs, files in os.walk(directory, topdown=True):
        for vcs_type, vcs_file in vcs_files.items():
            if vcs_file in dirs or vcs_file in files:
                for dir_name in list(dirs):
                    # Do not process subdirectories
                    dirs.remove(dir_name)
                kick_off(vcs_type, verb, root)

    # Wait for all process to finish
    while jobs:
        if os.name == 'posix':
            pid, retcode = os.wait()
        else:
            pid, retcode = os.waitpid(jobs.keys()[0], 0)
        if pid in jobs:
            job = jobs[pid]
            print("===\033[32m\033[1m", job['name'], "\033[0m(" +
                  job['type'] + ") ===")
            print(job['p'].stdout.read())
            if retcode != 0:
                print("\033[31mError exitcode '" + str(retcode) + "'\033[0m")
            del jobs[pid]
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
