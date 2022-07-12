import csv
import os
import subprocess
import threading

BASE = "/home/ben/movies"
RAW = f"{BASE}/raw"
COMPRESSED = f"{BASE}/compressed"
READY = f"{BASE}/ready"


def wait_for_disc():
    print("Waiting for disc to be ready")
    subprocess.run("while ! dd if=/dev/sr0 bs=2048 count=1 of=/dev/null 2>/dev/null; do sleep 1; done", check=True,
                   shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def get_disc_name():
    print("Analysing disc")
    stream = os.popen('makemkvcon info -r')

    reader = csv.reader(stream.readlines())
    rows = [r for r in list(reader) if len(r) > 0]

    dvdName = [r for r in rows if r[0] == "DRV:0"][0][5]
    if not dvdName:
        "Could not detect dvd name"
        exit(1)
    print(f"Found DVD name: {dvdName}")
    return dvdName


def complete_raw_copy(dvdName):
    rawDir = f"{RAW}/{dvdName}"
    print(f"Making raw write directory {rawDir}")
    os.makedirs(rawDir, exist_ok=True)

    print("Beginning raw copy...")
    proc = subprocess.Popen(f"makemkvcon mkv disc:0 all {rawDir}".split())
    (results, errors) = proc.communicate()
    if proc.returncode != 0:
        print(
            "MakeMKV (rip_disc) returned status code: %d" % proc.returncode)

    if errors is not None:
        if len(errors) != 0:
            print("MakeMKV encountered the following error: ")
            print(errors)
            exit(1)


def eject():
    subprocess.run("eject", check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def compress_file(input, output):
    proc = subprocess.Popen(f"ffmpeg -i {input} -map 0 -c:s copy -vcodec libx264 -crf 18 {output}".split())
    (results, errors) = proc.communicate()
    if proc.returncode != 0:
        print(
            "ffmpeg status code: %d" % proc.returncode)

    if errors is not None:
        if len(errors) != 0:
            print("ffmpeg encountered the following error: ")
            print(errors)
            exit(1)
    os.remove(input)
    print(f"Compression {input} finished")

def finish_process(dvdName):
    print("Handed over to side thread to finish conversion process")
    rawDir = f"{RAW}/{dvdName}"
    compressionDir = f"{COMPRESSED}/{dvdName}"
    readyDir = f"{READY}/{dvdName}"
    os.makedirs(compressionDir, exist_ok=True)
    threads = [threading.Thread(target=compress_file, args=(f"{rawDir}/{f}", f"{compressionDir}/{f}")) for f in os.listdir(rawDir)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    os.makedirs(READY, exist_ok=True)
    os.rename(compressionDir, readyDir)
    os.rmdir(rawDir)
    print("Done")

if __name__ == "__main__":
    while True:
        wait_for_disc()

        dvdName = get_disc_name()

        complete_raw_copy(dvdName)
        eject()

        threading.Thread(target=finish_process, args=(dvdName,)).start()