import os

BASE = "/home/ben/movies"
RAW = f"{BASE}/raw"
UNCOMPRESSED = f"{BASE}/uncompressed"
COMPRESSED = f"{BASE}/compressed"
READY = f"{BASE}/ready"


def init_dirs():
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(UNCOMPRESSED, exist_ok=True)
    os.makedirs(COMPRESSED, exist_ok=True)
    os.makedirs(READY, exist_ok=True)


def raw_dir(dvdName):
    return f"{RAW}/{dvdName}"


def uncompressed_dir(dvdName):
    return f"{UNCOMPRESSED}/{dvdName}"


def compressed_dir(dvdName):
    return f"{COMPRESSED}/{dvdName}"


def ready_dir(dvdName):
    return f"{READY}/{dvdName}"
