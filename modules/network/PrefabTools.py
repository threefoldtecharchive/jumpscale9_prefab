from js9 import j

base = j.tools.prefab._getBaseClass()

class PrefabTools(base):

    def download(
            self,
            url,
            to="",
            overwrite=True,
            retry=3,
            timeout=0,
            login="",
            passwd="",
            minspeed=0,
            multithread=False,
            expand=False,
            minsizekb=40,
            removeTopDir=False):
        """
        download from url
        @return path of downloaded file
        @param to is destination
        @param minspeed is kbytes per sec e.g. 50, if less than 50 kbytes during 10 min it will restart the download (curl only)
        @param when multithread True then will use aria2 download tool to get multiple threads  (NOT IMPLEMENTED YET)
        @param removeTopDir : if True and there is only 1 dir in the destination then will move files away from the one dir to parent (often in tgz the top dir is not relevant)
        """
        return self.core.file_download(url=url,to=to,overwrite=overwrite,\
            retry=retry,timeout=timeout,login=login,passwd=passwd,minspeed=minspeed,multithread=multithread,
            expand=expand,minsizekb=minsizekb,removeTopDir=removeTopDir)