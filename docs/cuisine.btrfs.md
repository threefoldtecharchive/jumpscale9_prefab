# cuisine.btrfs

The `cuisine.btrfs` module handles **btrfs** operations.

Examples for methods in `btrfs`:

- Adding a device to a filesystem using **deviceAdd**:

```python
cuisine.btrfs.deviceAdd('\', device)
```

- Getting free data percentage using **getSpaceUsageDataFree**:

```python
cuisine.btrfs.getSpaceUsageDataFree()
```

- Checking if subvolume exists in the given path using **subvolumeExists**:

  ```python
  cuisine.btrfs.subvolumeExists('/')
  ```

```
!!!
title = "Cuisine.btrfs"
date = "2017-04-08"
tags = []
```
