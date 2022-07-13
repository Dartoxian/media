import subprocess
import threading

from utils import dirs, compression
from utils.makemkv import MakeMkv

import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


def wait_for_disc():
    root.info("Waiting for disc to be ready")
    subprocess.run("while ! dd if=/dev/sr0 bs=2048 count=1 of=/dev/null 2>/dev/null; do sleep 1; done", check=True,
                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def eject():
    subprocess.run("eject", check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == "__main__":
    dirs.init_dirs()
    threading.Thread(target=compression.watch_for_compression, daemon=True).start()
    while True:
        wait_for_disc()

        MakeMkv().rip()

        eject()
