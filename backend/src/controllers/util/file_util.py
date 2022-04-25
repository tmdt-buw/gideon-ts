import shutil
from pathlib import Path
from uuid import UUID

from src.config.settings import get_settings


def get_temp_file(uuid: UUID) -> Path:
    folder = Path(get_temp(), str(uuid))
    # just return first child
    for child in folder.iterdir():
        return child


def gen_temp_file(uuid: UUID, filename: str) -> Path:
    folder = Path(get_temp(), str(uuid))
    folder.mkdir()
    return Path(folder, filename)


def get_temp():
    temp = Path(get_root(), get_settings().upload_folder)
    if not temp.exists():
        temp.mkdir()
    return temp


def remove_temp():
    temp = Path(get_root(), get_settings().upload_folder)
    if temp.exists():
        shutil.rmtree(temp)


def get_root():
    return Path(__file__).parent.parent.parent
