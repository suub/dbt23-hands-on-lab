from collections import namedtuple
from dataclasses import dataclass
from importlib.util import find_spec
from typing import Any, Dict, NamedTuple, Union


__author__ = "Daniel Opitz"
__copyright__ = "Copyright 2022, SuUB"
__license__ = "GPL"
__maintainer__ = "Marie-Saphira Flug"


@dataclass
class Result:
    data: Any = None
    logs: Any = None
    metrics: Any = None
    sentinel: Any = None
    skip: Any = None


class TaskParams(NamedTuple):
    data: Any = None
    params: Union[Dict, None] = None


Many = namedtuple("Many", "items")
Partial = namedtuple("Partial", "partial")


def is_module_available(module):
    spec = None
    try:
        spec = find_spec(module)
    except ModuleNotFoundError:
        pass

    return spec is not None


def resolve_module(module):
    spec = None
    try:
        spec = find_spec(module)
    except ModuleNotFoundError:
        pass

    if spec is not None:
        return module

    try:
        spec = find_spec(f"pipelines.{module}")
    except ModuleNotFoundError:
        pass

    return f"pipelines.{module}" if spec else None


def split(a, n):
    k, m = divmod(len(a), n)
    return (
        a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n)
    )
