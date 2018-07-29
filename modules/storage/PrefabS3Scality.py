from jumpscale import j
from time import sleep


app = j.tools.prefab._getBaseAppClass()


class PrefabS3Scality(app):
    NAME = 's3scality'

    def install(self, start=False, storageLocation="/data/", metaLocation="/meta/"):
        """
        put backing store on /storage/...
        """
        self.prefab.system.package.mdupdate()
        self.prefab.system.package.install('build-essential')
        self.prefab.system.package.install('python2.7')
        self.prefab.core.dir_ensure(storageLocation)
        self.prefab.core.dir_ensure(metaLocation)

        self.prefab.core.dir_ensure('/opt/code/github/scality')
        path = self.prefab.tools.git.pullRepo('https://github.com/scality/S3.git', ssh=False)
        profile = self.prefab.bash.profileDefault
        profile.addPath(self.prefab.core.dir_paths['BINDIR'])
        profile.save()
        self.prefab.runtimes.nodejs.install()
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
        nodePath = '$BASEDIR/node/lib/node_modules'
        # Temporary. Should be removed after updating the building process
        self.prefab.core.dir_ensure('/data/data')
        self.prefab.core.dir_ensure('/data/meta')
        # Temporary. npm install should be added to install() function after updating the building process
        if not self.prefab.core.dir_exists('%s/npm-run-all' % nodePath):
            self.prefab.core.run('npm install npm-run-all')
        nodePath = self.prefab.core.replace('$BASEDIR/node/lib/node_modules/s3/node_modules:%s' % nodePath)
        if self.prefab.bash.profileDefault.envGet('NODE_PATH') != nodePath:
            self.prefab.bash.profileDefault.envSet("NODE_PATH", nodePath)
            self.prefab.bash.profileDefault.addPath(self.prefab.core.replace("$BASEDIR/node/bin/"))
            self.prefab.bash.profileDefault.save()
        path = j.sal.fs.joinPaths(j.dirs.JSAPPSDIR, 'S3')
        self.prefab.core.run('cd {} && npm run start_location'.format(path), profile=True)

    def test(self):
        # put/get file over S3 interface using a python S3 lib
        raise NotImplementedError
