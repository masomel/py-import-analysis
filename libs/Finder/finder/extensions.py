# -*- coding: utf-8 -*-
# All the extensions specified below are non-readable content. It's better to
# avoid these in our search method. This is the place where you can update the
# non-readable file extensions.

# Images are not readable content. Any image extension that is not readable
# need to be added here in this array.
IMAGE_FORMATS = [
    'bmp',
    'dib',
    'tif',
    'tiff',
    'gif',
    'jpe',
    'jpg',
    'jpeg',
    'jif',
    'jfif',
    'jfi',
    'jp2',
    'jpf',
    'jpm',
    'jpx',
    'j2k',
    'j2c',
    'mj2',
    'fpx',
    'pcd',
    'png',
    'pbm',
    'pgm',
    'ppm',
    'pnm',
    'webp',
    'heif',
    'heic',
    'bpg'
]


# Videos are not readable content. Any video extension that is not readable
# need to be added here in this array.
VIDEO_FORMATS = [
    'webm',
    'mkv',
    'flv',
    'vob',
    'ogv',
    'ogg',
    'drc',
    'gifv',
    'mng',
    'avi',
    'mov',
    'qt',
    'wmv',
    'yuv',
    'rm',
    'rmvb',
    'asf',
    'amv',
    'mp4',
    'm4p',
    'm4v',
    'mpg',
    'mp2',
    'mpeg',
    'mpe',
    'mpv',
    'm2v',
    'm4v',
    'svi',
    '3gp',
    '3g2',
    'mxf',
    'roq',
    'nsv',
    'f4v',
    'f4p',
    'f4a',
    'f4b'
]


# Audios are not readable content. Any audio extension that is not readable
# need to be added here in this array.
AUDIO_FORMATS = [
    'aa',
    'aac',
    'aax',
    'act',
    'aiff',
    'amr',
    'ape',
    'au',
    'awb',
    'dct',
    'dss',
    'dvf',
    'flac',
    'gsm',
    'iklax',
    'ivs',
    'm4a',
    'm4b',
    'mmf',
    'mp3',
    'mpc',
    'msv',
    'ogg',
    'oga',
    'mogg',
    'opus',
    'ra',
    'rm',
    'raw',
    'sln',
    'tta',
    'vox',
    'wav',
    'wma',
    'wv'
]


# Some of the kernel files are dynamically generated based on the process
# running such as the files in '/proc' filesystem. These files are basically
# kernel files and the content of these files is generated on the go.
# Searching these files would be complex and the memory would be running out
# if we read these files. It is better we avoid searching these directories.
KERNEL_DIRS = ['/proc']
