
from jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabBuild(base):
    """
    A prefab module to build packages from source.
    """

    def build(self, name, repo, branch='master', pre_build=None, make_clean=False, cmake=False, cmake_args=None,
              make=False, make_install=False, post_build=None):
        """
        Build a package from source
        :param name: the name of the package
        :param repo: the git url of the repo
        :param branch: the repo branch to use for building. Defaults to master
        :param pre_build: list of strings of commands to run after cloning and before building
        :param make_clean: boolean indicating whether to run make clean or not
        :param cmake: boolean indicating whether to run cmake or not
        :param cmake_args: a list of arguments to the cmake command
        :param make: boolean indicating whether to run make or not
        :param make_install: boolean indicating whether to run make install or not
        :param post_build: list of strings of commands to run after building
        :return:
        """
        if not j.data.types.string.check(name):
            raise j.exceptions.Input(
                'name should be a string. Received a %s' % type(name))
        if not j.data.types.string.check(repo):
            raise j.exceptions.Input(
                'repo should be a string. Received a %s' % type(repo))
        if not j.data.types.string.check(branch):
            raise j.exceptions.Input(
                'branch should be a string. Received a %s' % type(branch))
        if pre_build and not j.data.types.list.check(pre_build):
            raise j.exceptions.Input(
                'pre_build should be a list. Received a %s' % type(pre_build))
        elif pre_build:
            for pre_cmd in pre_build:
                if not j.data.types.string.check(pre_cmd):
                    raise j.exceptions.Input(
                        'pre_build should only contain strings. Received a %s' % type(pre_cmd))
        if post_build and not j.data.types.list.check(post_build):
            raise j.exceptions.Input(
                'post_build should be a list. Received a %s' % type(post_build))
        elif post_build:
            for post_cmd in post_build:
                if not j.data.types.string.check(post_cmd):
                    raise j.exceptions.Input(
                        'post_build should only contain strings. Received a %s' % type(post_cmd))
        if not j.data.types.bool.check(make_clean):
            raise j.exceptions.Input(
                'make_clean should be a boolean. Received a %s' % type(make_clean))
        if not j.data.types.bool.check(cmake):
            raise j.exceptions.Input(
                'cmake should be a boolean. Received a %s' % type(cmake))
        if cmake_args and not j.data.types.list.check(cmake_args):
            raise j.exceptions.Input(
                'cmake_args should be a list. Received a %s' % type(cmake_args))
        elif cmake_args:
            for cmake_arg in cmake_args:
                if not j.data.types.string.check(cmake_arg):
                    raise j.exceptions.Input(
                        'cmake_args should only contain strings. Received a %s' % type(cmake_arg))
        if not j.data.types.bool.check(make):
            raise j.exceptions.Input(
                'make should be a boolean. Received a %s' % type(make))
        if not j.data.types.bool.check(make_install):
            raise j.exceptions.Input(
                'make_install should be a boolean. Received a %s' % type(make_install))

        commands = list()
        if pre_build:
            commands.extend(pre_build)
        if make_clean:
            commands.append('make clean')
        if cmake:
            self.prefab.system.package.install('cmake,libicu-dev')
            if cmake_args:
                commands.append('cmake {args} .'.format(args=' '.join(cmake_args)))
            else:
                commands.append('cmake .')
        if make:
            commands.append('make')
        if make_install:
            commands.append('make install')
        if post_build:
            commands.extend(post_build)

        command = """
                set -ex
                pushd /tmp
                rm -rf {name}
                git clone -b {branch} {repo} {name}
                pushd {name}
                {commands}
                popd
                popd
                """.format(name=name, branch=branch, repo=repo, commands='\n'.join(commands))
        self.core.run(command)
