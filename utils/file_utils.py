# Copyright (C) 2017 Les Fees Speciales
# voeu@les-fees-speciales.coop
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Name: file_utils

Description: Basic lib for file manipulation using only system commands
author: "LFS",
version: (0, 0, 1),
wiki_url: "",
category: "System file manipulation"
"""

#
# Todo:
# - set a Project name to get the reference root
# - define log_type ? DEBUG, INFO, WARNING, ERROR, CRITICAL
#

import os
import shutil
import platform
import re
from datetime import datetime, date, time
from glob import glob


def get_scene_and_shot(filepath):
    """
    Search Scene number, Shot number for a given filename.
    Return None if no filename found
    """
    pattern = "S([0-9]+)[/_]P([0-9]+)"
    matches = re.findall(pattern, filepath)
    if not matches:
        return
    return [int(m) for m in matches[0]]


def get_last_modified(filepath):
    """Get the last modified file in a given directory.
    If the specified path is a file,
    get the last modified file in the parent directory.
    """
    if os.path.isfile(filepath):
        dirpath, filename = os.path.split(filepath)
    else:
        dirpath = filepath
    files = os.listdir(dirpath)
    files.sort(key=lambda f: os.path.getmtime(os.path.join(dirpath, f)),
               reverse=True)
    return os.path.join(dirpath, files[0])


def get_latest_version(filepath):
    """
    Return the latest existing version and
    the next version name possible of a file
    """
    # Get file name pattern from pathdir
    filedir, filename = os.path.split(filepath)
    extension = '.' + filename.split('.')[-1]
    root = get_root()
    try:
        pattern = filedir.split(root)[1].replace("/", "_")[1:] + "_"
    except:
        print('File name in root project')
        return '', ''
    # Find all version numbers
    matches = [re.findall(pattern+'v([0-9]+)' + extension, f)
               for f in sorted(os.listdir(filedir))]
    matches.extend([re.findall(pattern+'v([0-9]+)_REF' + extension, f)
                    for f in sorted(os.listdir(filedir))])
    m = list(filter(None, matches))
    if m == []:
        print('File name different from nomenclature, '
              'care if it is a project file')
        return '', ''
    # From matches, find padding and sort numbers
    padding = 1
    number_lengths = [len(i[0]) for i in m]
    if not number_lengths:
        number_lengths = [2]
        m = [['00']]
    padding = max(number_lengths)
    numbers = [int(i[0]) for i in m]
    numbers = sorted(numbers)

    # Find latest and next number
    latest_number = str(numbers[-1]).zfill(padding)
    next_number = str(numbers[-1]+1).zfill(padding)

    # return latest and next version filename
    latest_version = os.path.join(
        filedir, "%sv%s" % (pattern, latest_number)) + extension
    next_version = os.path.join(
        filedir, "%sv%s" % (pattern, next_number)) + extension
    return latest_version, next_version


def get_latest_version_by_number(filepath):
    """
    Return the latest existing version and
    the next version name possible of a file
    """
    pattern = "_v([0-9]+)"
    rexp = re.compile(pattern)
    glob_pattern = rexp.sub('_v*', filepath)
    try:
        latest_version = sorted(glob(glob_pattern))[-1]
    except IndexError:
        latest_version = next_version = rexp.sub('_v01', filepath)
        return latest_version, next_version

    # print(rexp.search(filepath).groups())
    v = int(rexp.search(latest_version).groups()[0])
    v1 = v+1
    next_version = rexp.sub('_v%02i' % v1, filepath)

    return latest_version, next_version


def create_backup(filepath, subdir=''):
    """Create a backup version of a file and returns its name."""
    filedir, filename = os.path.split(filepath)
    if subdir != '':
        filedir = filedir + subdir
        if not os.path.exists(filedir):
            os.makedirs(filedir)
    latest_version, next_version = get_latest_version(filepath)
    if latest_version == '' and next_version == '':
        print('backup file created, clean manualy backup files')
        filedir, filename = os.path.split(filepath)
        if subdir != '':
            filedir = filedir + subdir
        extension = '.' + filename.split('.')[-1]
        next_version = (os.path.join(filedir, filename.split('.')[0])
                        + '_backup_v001' + extension)
        if os.path.isfile(next_version):
            i = 2
            while os.path.isfile(next_version):
                next_version = (os.path.join(filedir, filename.split('.')[0])
                                + '_backup_v' + str(i).zfill(3)
                                + extension)
                i += 1

    copy(filepath, next_version)
    update_log(filepath, 'Backup: ' + filename,
               comment='Save to '+next_version)
    return next_version


def create_ref(filepath):
    """Copy _REF and create a REF version."""
    latest_version, next_version = get_latest_version(filepath)
    filedir, filename = os.path.split(latest_version)
    ref_version = os.path.join(filedir, filename.split('.')[0]
                               + '_REF.' + filename.split('.')[-1])
    copy(filepath, ref_version)
    update_log(filepath, 'REF: ' + filename)
    return ref_version


def copy(filepath, new_file):
    """Copy file with shutil."""
    return shutil.copyfile(filepath, new_file)


def update_log(filepath, action, comment='', log_type='LOG'):
    """Update the log file."""
    filedir, filename = os.path.split(filepath)
    log_file = filedir+'/.log'
    try:
        f = open(log_file, 'a')
    except:
        return 'Could not open the log file'

    name = platform.node()
    time = str(datetime.now()).split('.')[0]
    message = ','.join([time.split(' ')[0],
                        time.split(' ')[-1],
                        name,
                        log_type,
                        action, comment+'\n'])
    f.write(message)
    f.close()
    return message, log_file


def filter_log(filepath, date='', computer='', action='', log_type=''):
    """Read the log file with filter."""
    filedir, filename = os.path.split(filepath)
    log_file = filedir+'/.log'
    try:
        f = open(log_file, 'r')
    except:
        return 'Could not open the log file'

    filtered_lines = list(f)
    f.close()
    key_list = [date, computer, action, log_type]
    for param in key_list:
        if param != '':
            filtered_lines = [re.search(param, l) for l in filtered_lines]
            filtered_lines = list(filter(None, filtered_lines))
            filtered_lines = [fl.string for fl in filtered_lines]
    for log in filtered_lines:
        print(log)
    return filtered_lines
