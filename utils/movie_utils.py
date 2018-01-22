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

import os
import sys
import platform
import subprocess

OS = platform.system()

bins = {'Linux':
        {'ffmpeg': 'ffmpeg',
         'convert': 'convert'},
        'Windows':
        {'ffmpeg': '"C:\\bin\\ffmpeg\\ffmpeg.exe"',
         'convert': '"C:\\Program Files\\ImageMagick-6.9.3-Q16\\convert.exe"'},
        'Darwin':
        {'ffmpeg': '/Applications/ffmpeg',
         'convert': "/opt/ImageMagick/bin/convert"}}


def convert_images(image_dir, image_name, output_dir, output_name,
                   frame_rate=24, frame_start=1, input_extension='png',
                   sound=None):
    """Use FFMPEG to convert an image sequence to a movie."""
    print("### Preparing ffmpeg arguments")
    args = [bins[OS]['ffmpeg']]
    args.extend(['-r', '%i' % frame_rate,
                 '-f', 'image2',
                 '-start_number', "%i" % (frame_start),
                 '-i', '"%s.%s"' % (os.path.join(image_dir, image_name + "%04d"), input_extension)])

    if sound is not None:
        args.extend(["-i", '"%s"' % sound])
        args.extend(["-map", "0:0", "-map", "1:0"])
        # Sound encoding: AAC
        args.extend(["-c:a", "aac", "-b:a", "128k", "-strict", "-2"])

    # Video encoding: Motion jpg
    args.extend(['-vcodec', 'mjpeg', '-q:v', '3'])

    args.extend(['-y', '"%s.mov"' % (os.path.join(output_dir, output_name))])
    print("### fffmpeg arguments : %s" % str(args))
    j = " ".join(args)

    print("### ffmpeg command :\n%s\n" % j)

    if OS == "Windows":
        print("### launching the ffmpeg command through windows .bat file")
        # Create intermediate .bat file, else error occurs...
        j = j.replace("/", "\\").replace("%", "%%")
        batPath = "%s/ffmpeg.bat" % (tmpFolder)
        f = open(batPath, 'w')
        f.write(j)
        f.close()
        os.system(batPath.replace('/', '\\'))
    else:
        print("### launching the ffmpeg command")
        os.system(j)


def play_file(filepath):
    """From https://stackoverflow.com/a/435669/4561348"""
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', filepath))
    elif os.name == 'nt':
        os.startfile(filepath)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', filepath))
