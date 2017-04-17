from JumpScale import j

app = j.tools.cuisine._getBaseAppClass()


class CuisineRestic(app):

    NAME = 'restic'

    def _init(self):
        self.BUILDDIR = self.core.replace("$BUILDDIR/restic")
        self.CODEDIR = self.core.replace("$GOPATHDIR/src/github.com/restic/restic")

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        super().reset()
        self.core.dir_remove(self.BUILDDIR)
        self.core.dir_remove(self.CODEDIR)

    def build(self, install=True, reset=False):
        if reset is False and (self.isInstalled() or self.doneGet('build')):
            return

        if reset:
            self.reset()

        self.cuisine.development.golang.install()

        # build
        url = "https://github.com/restic/restic/"
        self.cuisine.development.git.pullRepo(url, dest=self.CODEDIR, ssh=False, depth=1)

        build_cmd = 'cd {dir}; go run build.go -k -v'.format(dir=self.CODEDIR)
        self.cuisine.core.run(build_cmd, profile=True)

        self.doneSet("build")

        if install:
            self.install()

    def install(self, reset=False):
        """
        download, install, move files to appropriate places, and create relavent configs
        """

        if self.doneGet("install") and not reset:
            return

        self.cuisine.core.file_copy(self.CODEDIR + '/restic', '$BINDIR')

        self.doneSet("install")

    def getRepository(self, path, password):
        """
        @return ResticRepository object. If the repo doesn't exist yet, it will
                be created and initialized
        """
        return ResticRepository(path, password, self.cuisine)


class ResticRepository:
    """This class represent a restic repository used for backup"""

    def __init__(self, path, password, cuisine):
        self.path = path
        self.__password = password
        self._cuisine = cuisine

        if not self._exists():
            self.initRepository()

    def _exists(self):
        test_file = j.sal.fs.joinPaths(self.path, 'config')
        return self._cuisine.core.file_exists(test_file)

    def _run(self, cmd, env=None, die=True, showout=True):
        env = {
            'RESTIC_REPOSITORY': self.path,
            'RESTIC_PASSWORD': self.__password
        }
        if env:
            env.update(env)
        return self._cuisine.core.run(cmd=cmd, env=env, die=die, showout=showout)

    def initRepository(self):
        """
        initialize the repository at self.path location
        """
        cmd = '$BINDIR/restic init'
        self._run(cmd)

    def snapshot(self, path, tag=None):
        """
        @param path: directory/file to snapshot
        @param tag: tag to add to the snapshot
        """
        cmd = '$BINDIR/restic backup {} '.format(path)
        if tag:
            cmd += " --tag {}".format(tag)
        self._run(cmd)

    def restore_snapshot(self, snapshot_id, dest):
        """
        @param snapshot_id: id of the snapshot to restore
        @param dest: path where to restore the snapshot to
        """
        cmd = '$BINDIR/restic restore --target {dest} {id} '.format(dest=dest, id=snapshot_id)
        self._run(cmd)

    def list_snapshots(self):
        """
        @return: list of dict representing a snapshot
        { 'date': '2017-01-17 16:15:28',
          'directory': '/optvar/cfg',
          'host': 'myhost',
          'id': 'ec853b5d',
          'tags': 'backup1'
        }
        """
        cmd = '$BINDIR/restic snapshots'
        _, out, _ = self._run(cmd, showout=False)

        snapshots = []
        for line in out.splitlines()[2:]:
            ss = list(self._chunk(line))

            snapshot = {
                'id': ss[0],
                'date': ' '.join(ss[1:3]),
                'host': ss[3]
            }
            if len(ss) == 6:
                snapshot['tags'] = ss[4]
                snapshot['directory'] = ss[5]
            else:
                snapshot['tags'] = ''
                snapshot['directory'] = ss[4]
            snapshots.append(snapshot)

        return snapshots

    def check_repo_integrity(self):
        """
        @return: True if integrity is ok else False
        """
        cmd = '$BINDIR/restic check'
        rc, _, _ = self._run(cmd)
        if rc != 0:
            return False
        return True

    def _chunk(self, line):
        """
        passe line and yield each word separated by space
        """
        word = ''
        for c in line:
            if c == ' ':
                if word:
                    yield word
                    word = ''
                continue
            else:
                word += c
        if word:
            yield word
