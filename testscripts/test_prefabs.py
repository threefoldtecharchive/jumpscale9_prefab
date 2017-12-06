#!/usr/bin/env python
"""
Module to do basic healthcheck test for prefab modules
The test will do the following:
1. Load all the prefab modules registred in the j.tools.prefab.local hook, only the core module will be skipped
2. For each module, build, instal, start, stop methods will be called if exist
3. Collect and report errors
"""

from js9 import j
import multiprocessing as mp
import logging
import traceback


# set the logger level
j.logger.set_level(logging.ERROR)

PROCESS_TIMEOUT = 15 * 60 # 15 minutes timeout per process

class Process(mp.Process):
    """
    Wrapping the mulitprocessing Process class to be able to easily access process exception, credit to:
    https://stackoverflow.com/a/33599967
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize process object
        """
        mp.Process.__init__(self, *args, **kwargs)
        # create a pip between the parent and the child processes
        self._pconn, self._cconn = mp.Pipe()
        self._exception = None


    def run(self):
        """
        Main run method
        """
        try:
            mp.Process.run(self)
            self._cconn.send(None)
        except Exception:
            tb = traceback.format_exc()
            self._cconn.send(tb)

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception

    @exception.setter
    def exception(self, value):
        self._exception = value


def prefab_module(module, name):
    print ('** starting test', name)
    for method in ['build', 'install', 'start', 'stop']:
        if hasattr(module, method):
            print("\t", method, name)
            name = '{}.{}()'.format(name, method)
            try:
                getattr(module, method)()
            except Exception as _:
                raise RuntimeError('Error while running {}'.format(name))



def run_in_parallel(fns):
    proc = []
    for fn in fns:
        p = Process(target=fn[0], args=fn[1:])
        p.start()
        proc.append((p, fn[1], fn[2]))

    for p in proc:
        p[0].join(PROCESS_TIMEOUT)
        # if process is still alive after the timeout, we terminate and set the exception as timeout exception
        if p[0].is_alive():
            p[0].terminate()
            p[0].exception = 'Job timed out after {} seconds'.format(PROCESS_TIMEOUT)

    # collect errors
    errors = []
    for p in proc:
        if p[0].exception:
            errors.append('Errors while running {}()'.format(p[2]))
            errors.append(p[0].exception)
            errors.append('\n')
    if errors:
        raise RuntimeError('Errors: {}'.format('\n'.join(errors)))

def run(fns):
    errors = []
    for fn in fns:
        p = Process(target=fn[0], args=fn[1:])
        p.start()
        p.join(PROCESS_TIMEOUT)
        # if process is still alive after the timeout, we terminate and set the exception as timeout exception
        if p.is_alive():
            p.terminate()
            p.exception = 'Job timed out after {} seconds'.format(PROCESS_TIMEOUT)
        if p.exception:
            errors.append('Errors while running {}()'.format(fn[2]))
            errors.append(p.exception)
            errors.append('\n')
    if errors:
        raise RuntimeError('Errors: {}'.format('\n'.join(errors)))


def main():
    to_run = list()
    name = 'j.tools.prefab.local'
    for category in [item for item in dir(j.tools.prefab.local) if not item.startswith('_') and 'core' not in item]:
        cat = getattr(j.tools.prefab.local, category)
        cat_name = '{}.{}'.format(name, category)
        for module in [item for item in dir(cat) if not item.startswith('_')]:
            mod = getattr(cat, module)
            module_name = '{}.{}'.format(cat_name, module)
            to_run.append((prefab_module, mod, module_name))

    # run_in_parallel(to_run)
    run(to_run)

if __name__ == '__main__':
    main()
