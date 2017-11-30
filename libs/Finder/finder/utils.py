# -*- coding: utf-8 -*-

import os

from .extensions import (
    IMAGE_FORMATS,
    VIDEO_FORMATS,
    AUDIO_FORMATS,
    KERNEL_DIRS
)


def split_params(params):
    """Returns a list of values from a given string of comma-separated values.
    """
    return params.split(',')


def file_extension(path):
    """Returns the file extension of the given file path."""
    return path.split(os.path.sep)[-1].split('.')[-1]


def is_executable(path):
    """Validates whether a given file path is binary or not.

    Args:
        path (str): File path.

    Returns:
        bool: True if the file is a binary else False.

    .. versionadded:: 1.0.0
    """
    return os.access(path, os.X_OK)


def is_readable(path):
    """Validates whether a given file path is readable or not.

    Args:
        path (str): File path.

    Returns:
        bool: True if the file is readable else False.

    .. versionadded:: 1.0.0
    """
    return os.access(path, os.R_OK)


def is_image(path):
    """Validates whether a given file path is image or not.

    Args:
        path (str): File path.

    Returns:
        bool: True if the file is an image else False.

    .. versionadded:: 1.0.0
    """
    extension = file_extension(path)

    return extension in IMAGE_FORMATS


def is_video(path):
    """Validates whether a given file path is a video or not.

    Args:
        path (str): File path.

    Returns:
        bool: True if the file is a video else False.

    .. versionadded:: 1.0.0
    """
    extension = file_extension(path)

    return extension in VIDEO_FORMATS


def is_audio(path):
    """Validates whether a given file path is a audio or not.

    Args:
        path (str): File path.

    Returns:
        bool: True if the file is a audio else False.

    .. versionadded:: 1.0.0
    """
    extension = file_extension(path)

    return extension in AUDIO_FORMATS


def is_kernel_file(path):
    """Validates whether the file path is a kernel file or not.

    Args:
        path (str): File path.

    Returns:
        bool: True if the file path is a kernel file else False.

    .. versionadded:: 1.0.0
    """
    return any([path.startswith(parent_dir) for parent_dir in KERNEL_DIRS])
