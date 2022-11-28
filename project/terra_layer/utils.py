from collections.abc import Mapping


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


def get_layer_group_cache_key(scene, extras=None):
    """
    :param scene: The scene to be cached
    :return: The cache key
    :rtype: string
    """
    if extras is None:
        extras = []
    extras_joined = "-".join(extras)
    return f"terra-layer-{scene.pk}-{extras_joined}"
