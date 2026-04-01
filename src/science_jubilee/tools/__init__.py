import os

_CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "configs")


def _find_config(filename: str, path: str = None) -> str:
    """Return the full path to a tool config file.

    If *path* is given explicitly, look there.  Otherwise check ``configs/user/``
    first (user-specific calibration), then fall back to ``configs/examples/``
    (shipped example files).
    """
    if path is not None:
        return os.path.join(path, filename)
    user = os.path.join(_CONFIGS_DIR, "user", filename)
    if os.path.isfile(user):
        return user
    return os.path.join(_CONFIGS_DIR, "examples", filename)
