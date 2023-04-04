from collections.abc import Mapping
from hashlib import md5


def dict_merge(dct, merge_dct, add_keys=True):
    dct = dct.copy()
    if not add_keys:
        merge_dct = {k: merge_dct[k] for k in set(dct).intersection(set(merge_dct))}

    for k, _ in merge_dct.items():
        if k in dct and isinstance(dct[k], dict) and isinstance(merge_dct[k], Mapping):
            dct[k] = dict_merge(dct[k], merge_dct[k], add_keys=add_keys)
        else:
            dct[k] = merge_dct[k]

    return dct


def get_scene_tree_cache_key(scene, user_groups=None):
    """Make cache ey for Scene Tree"""
    scene_key = f"{scene.pk}-{scene.updated_at}"
    user_groups_key = (
        f"{user_groups.values_list('pk', flat=True)}" if user_groups else ""
    )
    layers_key = f"{scene.layers.values('id', 'group', 'updated_at')}"
    cache_string = f"tree-{scene_key}-{user_groups_key}-{layers_key}"
    return md5(cache_string.encode("utf-8")).hexdigest()
