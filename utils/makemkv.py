import csv
import logging
import os
import subprocess
import time
import datetime

from typing import List

from . import dirs


class MakeMkvMessageParser:
    def __init__(self, messages: List[str]):
        self._messages = messages

    def get_rows(self, stype: str) -> List[List[str]]:
        toReturn = []
        for row in csv.reader(self._messages):
            if len(row) == 0:
                continue
            if row[0].startswith(stype):
                toReturn.append(row)
        return toReturn

    def get(self, stype: str, sid=None, scode=None) -> List[str]:
        """
            Returns a list of messages that match the search string
            Parses message output.
            Inputs:
                stype   (Str): Type of message
                sid     (Int): ID of message
                scode   (Int): Code of message
            Outputs:
                toreturn    (List)
        """
        toreturn = []
        for row in self.get_rows(stype):
            trackId = row[0].split(":")[1]
            if sid is None:
                toreturn.append(trackId)
                continue

            if int(trackId) == sid:
                if scode is None:
                    toreturn.append(row[2])
                    continue
                if scode == int(row[1]):
                    toreturn.append(row[3])

        return toreturn


class MakeMkv:

    def __init__(self):
        self.log = logging.getLogger(__name__)

    def rip(self):
        # New disc, reload info
        self._info()
        os.makedirs(dirs.raw_dir(self._dvdName), exist_ok=True)
        for title in self._titleIndices:
            self._ripTitle(title)
            for f in os.listdir(dirs.raw_dir(self._dvdName)):
                os.makedirs(dirs.uncompressed_dir(self._dvdName), exist_ok=True)
                os.rename(f"{dirs.raw_dir(self._dvdName)}/{f}", f"{dirs.uncompressed_dir(self._dvdName)}/{f}")
        os.rmdir(dirs.raw_dir(self._dvdName))

    def _info(self):
        self.log.info("Analysing disc")
        parser = self._run("makemkvcon info -r disc:0")

        self._dvdName = parser.get_rows("DRV:0")[0][5]

        if not self._dvdName:
            "Could not detect dvd name"
            exit(1)

        self.log.info(f"Found DVD name: {self._dvdName}")

        durations = {}
        titles = list(set(parser.get("TINFO")))
        titles.sort()
        for titleNo in titles:
            d = parser.get("TINFO", int(titleNo), 9)[0]
            x = time.strptime(d, '%H:%M:%S')
            titleDur = datetime.timedelta(
                hours=x.tm_hour,
                minutes=x.tm_min,
                seconds=x.tm_sec
            ).total_seconds()
            durations[titleNo] = titleDur

        max_duration = max(durations.values())
        required_length = max_duration * 0.75
        self.log.info(
            f"Longest clip is {max_duration} seconds, required length to be extracted is {required_length} seconds")

        self._titleIndices = [t for t in durations.keys() if durations[t] >= required_length]

        self.log.info(f"Decided to extract titles: {self._titleIndices}")

    def _ripTitle(self, title: str):
        self.log.info(f"Ripping {title}")
        self._run(f"makemkvcon mkv disc:0 {title} {dirs.raw_dir(self._dvdName)} --noscan")

    def _run(self, cmd):
        self.log.info(f"Executing {cmd}")
        proc = subprocess.Popen(
            cmd.split(),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

        (results, errors) = proc.communicate()

        if proc.returncode > 0:
            self.log.error(
                "MakeMKV (cmd) returned status code: %d" % proc.returncode)

        if errors is not None:
            if len(errors) > 0:
                self.log.error("MakeMKV encountered the following error: ")
                self.log.error(errors)
                return False
        return MakeMkvMessageParser(results.decode("utf-8").split("\n"))
