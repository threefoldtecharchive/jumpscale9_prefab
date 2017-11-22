from multiprocessing import Process
from js9 import j


def prefab_module(module, name):
    print ('** starting test', name)
    for method in ['build', 'install', 'start', 'stop']:
        if hasattr(module, method):
            print("\t", method, name)
            getattr(module, method)()

def runInParallel(*fns):
    proc = []
    for fn in fns:
        p = Process(target=fn)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()

if __name__ == '__main__':
    to_run = list()
    for category in dir(j.tools.prefab.local):
        if category.startswith('_'):
            continue
        cat = getattr(j.tools.prefab.local, category)
        for module in dir(cat):
            if module.startswith('_'):
                continue
            if 'core' in category:
                continue
            mod = getattr(cat, module)
            to_run.append(prefab_module(mod, module))

    runInParallel(to_run)