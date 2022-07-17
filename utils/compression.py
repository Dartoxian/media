import logging
import subprocess
import os
import time

from . import dirs

log = logging.getLogger(__name__)


def _compress_file(input, output, attempt=1):
    if (attempt == 4):
        raise ValueError(f"Attempted to convert {input} 3 times and failed each time")
    cmd = [
        f"ffmpeg",
        "-y",
        "-nostats",
        "-loglevel", "0",
        "-i", input,
        "-map", "0",
        "-c:s", "copy",
        "-vcodec", "libx264",
        "-crf", "18",
        output
    ]
    proc = subprocess.Popen(cmd)
    log.info(f"Running {subprocess.list2cmdline(proc.args)}")
    (results, errors) = proc.communicate()
    if proc.returncode != 0:
        log.info("ffmpeg status code: %d" % proc.returncode)
        _compress_file(input, output, attempt + 1)
        return

    if errors is not None:
        if len(errors) != 0:
            log.error("ffmpeg encountered the following error: ")
            log.error(errors)
            exit(1)
    os.remove(input)
    log.info(f"Compression {input} finished")


def watch_for_compression():
    while True:
        log.info("Starting compression cycle...")
        for dvdName in os.listdir(dirs.UNCOMPRESSED):
            if not os.path.exists(dirs.uncompressed_dir(dvdName)):
                # I probably tidied it up
                continue
            os.makedirs(dirs.compressed_dir(dvdName), exist_ok=True)
            for f in os.listdir(dirs.uncompressed_dir(dvdName)):
                inputFile = f"{dirs.uncompressed_dir(dvdName)}/{f}"
                if not os.path.exists(inputFile):
                    # I probably tidied it up
                    continue
                log.info(f"Found {f} in {dvdName} ready for compression")
                out = f"{dirs.compressed_dir(dvdName)}/{f}"
                if os.path.exists(out):
                    os.remove(out)
                _compress_file(inputFile, out)
                log.info(f"Finished compressing {f} in {dvdName}")
            log.info(f"Finished compressing {dvdName}")
            os.rename(f"{dirs.compressed_dir(dvdName)}", f"{dirs.ready_dir(dvdName)}")
            os.rmdir(dirs.compressed_dir(dvdName))
        log.info("Compression cycle sleeping...")
        time.sleep(30)
