"""NHANES source file registry used by the cohort builder."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NhanesFile:
    cycle: str
    component: str
    url: str

    @property
    def filename(self) -> str:
        return self.url.rsplit("/", 1)[-1]


BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"
LARGE_DATA_URL = "https://ftp.cdc.gov/pub/NHANES/LargeDataFiles"

CYCLES: dict[str, dict[str, str]] = {
    "2011-2012": {"path": "2011", "suffix": "G"},
    "2013-2014": {"path": "2013", "suffix": "H"},
}

COMPONENTS = ("DEMO", "MCQ", "PAXHD", "PAXDAY", "PAXMIN")


def get_file_registry(include_minutes: bool = False) -> list[NhanesFile]:
    components = COMPONENTS if include_minutes else tuple(c for c in COMPONENTS if c != "PAXMIN")
    files: list[NhanesFile] = []
    for cycle, meta in CYCLES.items():
        for component in components:
            extension = "xpt" if component == "PAXMIN" else "XPT"
            file_name = f"{component}_{meta['suffix']}.{extension}"
            if component == "PAXMIN":
                url = f"{LARGE_DATA_URL}/{file_name}"
            else:
                url = f"{BASE_URL}/{meta['path']}/DataFiles/{file_name}"
            files.append(NhanesFile(cycle=cycle, component=component, url=url))
    return files
