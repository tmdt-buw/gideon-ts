from enum import Enum


class FileType(str, Enum):
    json = '.json',
    ts = '.ts'
