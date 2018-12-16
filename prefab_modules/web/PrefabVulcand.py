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

        export goDir={DIR_TEMP}/vulcandgoDir

        if [ ! -d {DIR_BASE}/go ]; then
            mkdir -p {DIR_BASE}/go
        fi

        go get -d github.com/vulcand/vulcand

        cd {DIR_BASE}/go/src/github.com/vulcand/vulcand
        CGO_ENABLED=0 go build -a -ldflags '-s' -installsuffix nocgo .
        GOOS=linux go build -a -tags netgo -installsuffix cgo -ldflags '-w' -o ./vulcand .
        GOOS=linux go build -a -tags netgo -installsuffix cgo -ldflags '-w' -o ./vctl/vctl ./vctl
        GOOS=linux go build -a -tags netgo -installsuffix cgo -ldflags '-w' -o ./vbundle/vbundle ./vbundle

        mkdir -p /build/vulcand
        cp {DIR_BASE}/go/src/github.com/vulcand/vulcand/vulcand {DIR_BASE}/bin/
        cp {DIR_BASE}/go/src/github.com/vulcand/vulcand/vctl/vctl {DIR_BASE}/bin/
        cp {DIR_BASE}/go/src/github.com/vulcand/vulcand/vbundle/vbundle {DIR_BASE}/bin/

        rm -rf {DIR_BASE}/go

        '''
        C = self.prefab.bash.replaceEnvironInText(C)
        self.prefab.core.run(C, profile=True)
        self.prefab.bash.addPath("{DIR_BASE}/bin")
