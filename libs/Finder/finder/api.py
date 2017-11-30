# -*- coding: utf-8 -*-

import os
import queue
import threading
import logging as log

from .schema import FinderSchema, DataSchema, ErrorSchema
from .utils import (
    is_kernel_file,
    is_executable,
    is_readable,
    is_image,
    is_audio,
    is_video
)

log.basicConfig(format='%(message)s', level=log.INFO)

lock = threading.Lock


class FileReader(threading.Thread):
    """Thread class for finding the given pattern in a given file.

    Args:
        path (str): File path.
        pattern (str): A string to be searched in the given file path.

    .. versionadded:: 1.0.0
    """
    def __init__(self, path=None, pattern=None, _queue=None):
        self.path = path
        self.pattern = pattern
        self._queue = _queue
        threading.Thread.__init__(self)

    def run(self):
        """Runs methods for reading the file and searching the pattern in a
        line of text from the file.
        """
        items = []
        error = []
        pattern_found = False
        errors_occurred = False

        try:
            for line_number, line in read(self.path):
                if search(line, self.pattern):
                    items.append(self.set_data(line_number, line))
                    pattern_found = True
        except PermissionError as exc:
            error.append(self.make_error(type='PermissionError',
                                         message=exc,
                                         extra=None))
            errors_occurred = True
        except OSError as exc:
            error.append(self.make_error(type='OSError',
                                         message=exc,
                                         extra='File might be a kernel file'))
            errors_occurred = True
        except UnicodeDecodeError as exc:
            # TODO: Support all the file encodings.
            error.append(self.make_error(type='UnicodeDecodeError',
                                         message=exc,
                                         extra=None))
            errors_occurred = True

        if pattern_found or errors_occurred:
            # Serialize to a JSON-encoded string.
            response = FinderSchema().dumps({'path': self.path,
                                             'total_items': len(items),
                                             'items': items,
                                             'error': error})

            self._queue.put(response.data)

    def set_data(self, line_number, line):
        """Returns the serialized data."""
        data = {'line_number': line_number,
                'line': line}

        return DataSchema().dump(data).data

    def make_error(self, type, message, extra):
        """Returns the error serialized data."""
        error = {'type': type,
                 'message': message,
                 'extra': extra}

        return ErrorSchema().dump(error).data


def find(*paths, **kwargs):
    """Main method for finding the pattern in the given file paths.

    Args:
        paths (list): List of paths to be walked through.
        kwargs (str): Positional arguments.

    .. versionadded:: 1.0.0
    """
    pattern = kwargs.get('pattern', None)
    _queue = queue.Queue()

    for path in iterfiles(*paths):
        reader = FileReader(path, pattern, _queue)
        reader.start()
        reader.join()

        while not _queue.empty():
            yield _queue.get()


def search(text=None, pattern=None):
    """Searches the given pattern in the given text.

    Args:
        text (str): Text in which the pattern needs to be searched.
        pattern (str): A string to be searched in the given `text`.

    Returns:
        bool: A boolean value stating whether the pattern is found in the
            given text or not.

    .. versionadded:: 1.0.0
    """
    return True if pattern in text else False


def read(path):
    """Yields line by line from the file path provided.

    Args:
        path (str): File path provided.

    Yields:
        int: Line number.
        str: Line of text corresponding to the line number from the file.

    .. versionadded:: 1.0.0
    """
    with open(path, 'r', encoding='utf-8') as fp:
        count = 0

        for line in fp:
            count += 1
            yield (count, line.strip('\n'))


def iterfiles(*paths):
    """Yields all the non-executable file paths in a given directory.

    Args:
        paths (list): List of paths to be walked through.

    Yields:
        path (str): File path (files in the given directory path).

    .. versionadded:: 1.0.0
    """
    for path in paths:
        path = os.path.expanduser(path) if not os.path.isabs(path) else path

        if not os.path.exists(path):
            log.info("{path} is not a valid path. Please provide a valid path."
                     .format(path=path))
            continue

        if os.path.isfile(path) and not is_executable(path):
            yield path
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)

                    if (os.path.isfile(file_path) and
                            is_readable(file_path) and
                            not is_image(file_path) and
                            not is_executable(file_path) and
                            not is_kernel_file(file_path) and
                            not is_audio(file_path) and
                            not is_video(file_path)):
                        yield file_path
