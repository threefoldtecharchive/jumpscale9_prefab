from js9 import j
from time import sleep


app = j.tools.prefab._getBaseAppClass()


class CuisineS3Server(app):
    NAME = 's3server'

    def install(self, start=False, storageLocation="/data/", metaLocation="/meta/"):
        """
        put backing store on /storage/...
        """
        self.prefab.package.mdupdate()
        self.prefab.package.install('build-essential')
        self.prefab.package.install('python2.7')

        self.prefab.core.dir_ensure('/opt/code/github/scality')
        path = self.prefab.development.git.pullRepo('https://github.com/scality/S3.git', ssh=False)
        profile = self.prefab.bash.profileDefault
        profile.addPath(self.prefab.core.dir_paths['BINDIR'])
        profile.save()
        self.prefab.core.run('cd {} && npm install --python=python2.7'.format(path), profile=True)
        self.prefab.core.dir_remove('$JSAPPSDIR/S3', recursive=True)
        self.prefab.core.dir_ensure('$JSAPPSDIR')
        self.prefab.core.run('mv {} $JSAPPSDIR/'.format(path))

        cmd = 'S3DATAPATH={data} S3METADATAPATH={meta} npm start'.format(
            data=storageLocation,
            meta=metaLocation,
        )

        content = self.prefab.core.file_read('$JSAPPSDIR/S3/package.json')
        pkg = j.data.serializer.json.loads(content)
        pkg['scripts']['start_location'] = cmd

        content = j.data.serializer.json.dumps(pkg, indent=True)
        self.prefab.core.file_write('$JSAPPSDIR/S3/package.json', content)

        if start:
            self.start()

    def start(self, name=NAME):
        path = j.sal.fs.joinPaths(j.dirs.JSAPPSDIR, 'S3')
        self.prefab.core.run('cd {} && npm run start_location'.format(path), profile=True)

    def test(self):
        # put/get file over S3 interface using a python S3 lib
        raise NotImplementedError
