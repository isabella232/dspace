import os
import logging
from kopf.engines import loggers

logger = logging.getLogger(__name__)
__handler = logging.StreamHandler()
__handler.setFormatter(loggers.make_formatter())
logger.addHandler(__handler)
logger.setLevel(int(os.environ.get("LOGLEVEL", logging.INFO)))


def set_default_gvr():
    if "GROUP" not in os.environ:
        os.environ["GROUP"] = "nil.digi.dev"
    if "VERSION" not in os.environ:
        os.environ["VERSION"] = "v0"
    if "PLURAL" not in os.environ:
        os.environ["PLURAL"] = "nil"
    if "NAME" not in os.environ:
        os.environ["NAME"] = "nil"
    if "NAMESPACE" not in os.environ:
        os.environ["NAMESPACE"] = "default"


set_default_gvr()

from digi import (
    on,
    util,
    view,
    filter,
)

from digi.main import run

__all__ = [
    "on", "util", "view", "filter",
    "run", "logger",
]
