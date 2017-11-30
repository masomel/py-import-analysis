#!/usr/bin/env python

import os
import sys
import comb.combd
import importlib
import traceback
from cliez.loader import ArgLoader


def main():
    useage = (
        "Useage  comb [--root packages-root]  slot-package.slot-module",
        "",
        "   slot-package.slot-module        same as python package.module",
        "Options:",
        ("--root:", "find package.module in root path"),
        "",
        ("--sleep:", "set sleep time,default is 2s."),
        ("--sleep-max:", "set max sleep time, default is 60s."),
        ("--threads:", "set slot threads num,default is 10."),
        ("--once", "execute once and exit."),
        ("--no-daemon", "set comb works in no daemon mode."),

        "",
        ("--help", "print help document", '-h'),
        ("--debug", "debug mode"),

        "More:",
        "You can view https://github.com/kbonez/comb/blob/master/README.md 'How to use comb' to get more info."
    )


    # parse loader
    a = ArgLoader(options=useage)

    # call comb help manual with Highest priority
    if a.options['--help'] is True and len(a.argv) == 1:
        print(a)
        sys.exit(0)


    # set debug flag, this will bind to combd.
    _debug = False
    if a.options['--debug'] is True:
        _debug = True


    # bind root path
    runtime_path = a.options['--root']

    if runtime_path:
        sys.path.append(os.path.realpath(runtime_path))


    # if set SLOTPATH environment...
    user_path = os.getenv('SLOTPATH')
    if user_path:
        user_path_list = user_path.split(':')
        for path in user_path_list:
            sys.path.append(os.path.realpath(path))

    try:
        module_name = a.argv[1]
    except:
        print("illegal option,please set your slot-module-path,use -h to get help.")
        sys.exit(1)

    try:
        current_module = importlib.import_module(module_name)
    except:
        if _debug:
            print(traceback.format_exc())
        else:
            print("load slot-module `", module_name, "`,fail, you can set --debug option to check it.")
        sys.exit(-1)


    # set default value
    _threads_num = int(a.options['--threads']) if a.options['--threads'] else 10

    if sys.version_info < (3,0):
        _sleep = int(a.options['--sleep']) if a.options['--sleep'] else 2
    else:
        _sleep = float(a.options['--sleep']) if a.options['--sleep'] else 2

    _sleep_max = int(a.options['--sleep-max']) if a.options['--sleep-max'] else 60
    _once = a.options['--once'] if a.options['--once'] else False

    _no_daemon = a.options['--no-daemon'] if a.options['--no-daemon'] else False


    extra_options = None

    if hasattr(current_module.Slot, 'options') and callable(current_module.Slot.options):
        extra_options = current_module.Slot.options()

    if extra_options:
        b = ArgLoader(options=extra_options, sys_argv=a.argv[1:])
    else:
        b = None

    # if set --help and argument,call slot document
    if a.options['--help'] is True and extra_options.__len__():
        print(b)
        sys.exit(0)

    comb.combd.Start(current_module.Slot, extra_loader=b, sleep_cycle=_sleep, debug=_debug, sleep_max=_sleep_max, thread_nums=_threads_num, once=_once,no_daemon=_no_daemon)


pass

if __name__ == '__main__':
    main()












