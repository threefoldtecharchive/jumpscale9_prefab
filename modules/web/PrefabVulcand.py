from Jumpscale import j


app = j.tools.prefab._getBaseAppClass()

class PrefabVulcand(app):

    def build(self, reset=False):
        if reset is False and self.isInstalled():
            return
        C = '''
        #!/bin/bash
        set -e
        source /bd_build/buildconfig
        set -x

        export goDir=$TMPDIR/vulcandgoDir

        if [ ! -d $GOPATHDIR ]; then
            mkdir -p $GOPATHDIR
        fi

        go get -d github.com/vulcand/vulcand

        cd $GOPATHDIR/src/github.com/vulcand/vulcand
        CGO_ENABLED=0 go build -a -ldflags '-s' -installsuffix nocgo .
        GOOS=linux go build -a -tags netgo -installsuffix cgo -ldflags '-w' -o ./vulcand .
        GOOS=linux go build -a -tags netgo -installsuffix cgo -ldflags '-w' -o ./vctl/vctl ./vctl
        GOOS=linux go build -a -tags netgo -installsuffix cgo -ldflags '-w' -o ./vbundle/vbundle ./vbundle

        mkdir -p /build/vulcand
        cp $GOPATHDIR/src/github.com/vulcand/vulcand/vulcand $BASEDIR/bin/
        cp $GOPATHDIR/src/github.com/vulcand/vulcand/vctl/vctl $BASEDIR/bin/
        cp $GOPATHDIR/src/github.com/vulcand/vulcand/vbundle/vbundle $BASEDIR/bin/

        rm -rf $GOPATHDIR

        '''
        C = self.prefab.bash.replaceEnvironInText(C)
        self.prefab.core.run(C, profile=True)
        self.prefab.bash.addPath("$BASEDIR/bin")
