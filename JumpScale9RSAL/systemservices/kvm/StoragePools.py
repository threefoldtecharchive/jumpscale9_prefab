from JumpScale import j


class StoragePools:
    """This class give you access to storage pools related actions from the kvm sal over cuisine"""

    def __init__(self, controller):
        self._controller = controller
        self._storage_controller = j.sal.kvm.StorageController(controller)

    def create(self, name, start=True):
        """
        create a new storage pool

        @param name string: name of the storage pool
        @param start bool: start pool after creation
        """
        pool = j.sal.kvm.Pool(self._controller, name)
        if not pool.is_created:
            pool.create(start=start)
        if start:
            pool.start()
        return pool

    def list(self):
        """
        list all storage pools
        """
        return self._storage_controller.list_pools()

    def list_disks(self, pool_name):
        """
        list all disks from the pool with name `pool_name`
        """
        pool = self.get_by_name(pool_name)
        return pool.list_disks()

    def get_by_name(self, name):
        """
        return a storage pool object if exists

        @param name str: name of the pool
        """
        return j.sal.kvm.Pool.get_by_name(self._controller, name)
