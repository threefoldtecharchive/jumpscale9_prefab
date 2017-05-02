# prefab.btrfs

The `prefab.btrfs` module handles **btrfs** operations.

Examples for methods in `btrfs`:

- Adding a device to a filesystem using **deviceAdd**:

```python
prefab.btrfs.deviceAdd('\', device)
```

- Getting free data percentage using **getSpaceUsageDataFree**:

```python
prefab.btrfs.getSpaceUsageDataFree()
```

- Checking if subvolume exists in the given path using **subvolumeExists**:

  ```python
  prefab.btrfs.subvolumeExists('/')
  ```

```
!!!
title = "Prefab.btrfs"
date = "2017-04-08"
tags = []
```
