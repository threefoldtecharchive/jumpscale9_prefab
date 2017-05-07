from setuptools import setup
from setuptools.command.install import install as _install
from setuptools.command.develop import develop as _develop
import os


def _post_install(libname, libpath):
    from JumpScale9 import j
    j.tools.jsloader.copyPyLibs()

    # ensure plugins section in config
    if 'plugins' not in j.application.config:
        j.application.config['plugins'] = {}

    # add this plugin to the config
    j.application.config['plugins'][libname] = libpath

    moduleList = {}

    for name, path in j.application.config['plugins'].items():
        if j.sal.fs.exists(path, followlinks=True):
            moduleList = j.tools.jsloader.findModules(path=path, moduleList=moduleList)
            # link libs to location for hostos
            j.do.copyTree(path,
                          "/root/gig/python_libs/%s" % libname,
                          overwriteFiles=True,
                          ignoredir=['*.egg-info',
                                     '*.dist-info',
                                     "*JumpScale*",
                                     "*Tests*",
                                     "*tests*"],

                          ignorefiles=['*.egg-info',
                                       "*.pyc",
                                       "*.so",
                                       ],
                          rsync=True,
                          recursive=True,
                          rsyncdelete=True,
                          createdir=True)

    # DO NOT AUTOPIP the deps are now installed while installing the libs
    j.application.config["system"]["autopip"] = False
    j.application.config["system"]["debug"] = True

    j.tools.jsloader.generate(path=path, moduleList=moduleList)
    j.tools.jsloader.generate(path=path, moduleList=moduleList, codecompleteOnly=True)

    j.do.initEnv()


class install(_install):

    def run(self):
        _install.run(self)
        libname = self.config_vars['dist_name']
        libpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), libname)
        self.execute(_post_install, (libname, libpath), msg="Running post install task")


class develop(_develop):

    def run(self):
        _develop.run(self)
        libname = self.config_vars['dist_name']
        libpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), libname)
        self.execute(_post_install, (libname, libpath), msg="Running post install task")


setup(
    name='JumpScale9Prefab',
    version='9.0.0',
    description='Automation framework for cloud workloads remote sal, sal= system abstraction layer',
    url='https://github.com/Jumpscaler/prefab9',
    author='GreenItGlobe',
    author_email='info@gig.tech',
    license='Apache',
    packages=['JumpScale9Prefab'],
    install_requires=[
        'JumpScale9>=9.0.0',
        'paramiko>=2.1.2',
        'asyncssh>=1.9.0',
    ],
    cmdclass={
        'install': install,
        'develop': develop,
        'developement': develop
    },
)
