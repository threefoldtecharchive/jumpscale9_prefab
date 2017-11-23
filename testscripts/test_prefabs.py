from multiprocessing import Process
from js9 import j
import logging


# set the logger level
j.logger.set_level(logging.INFO)

def prefab_module(module, name):
    print ('** starting test', name)
    for method in ['build', 'install', 'start', 'stop']:
        if hasattr(module, method):
            print("\t", method, name)
            getattr(module, method)()

def runInParallel(fns):
    proc = []
    for fn in fns:
        p = Process(target=fn[0], args=fn[1:])
        p.start()
        proc.append(p)
    for p in proc:
        p.join()
        
def main():
    to_run = list()
    for category in [item for item in dir(j.tools.prefab.local) if not item.startswith('_') and 'core' not in item]:
        cat = getattr(j.tools.prefab.local, category)
        for module in [item for item in dir(cat) if not item.startswith('_')]:
            mod = getattr(cat, module)
            to_run.append((prefab_module, mod, module))
    runInParallel(to_run)

if __name__ == '__main__':
    main()