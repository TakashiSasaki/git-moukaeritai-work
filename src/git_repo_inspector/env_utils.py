import os
from typing import Dict

_GIT_ENV_VARS = [
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_NO_DISCOVERY",
    "GIT_TEMPLATE_DIR",
    "GIT_CONFIG",
]


def clean_git_env() -> Dict[str, str]:
    """Return a copy of :mod:`os.environ` with Git-related variables removed."""
    env = os.environ.copy()
    for var in _GIT_ENV_VARS:
        env.pop(var, None)
    return env
