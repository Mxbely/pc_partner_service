import os
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

from playwright.sync_api import TimeoutError

from search_service.parsers import DEFAULT_DIR
from search_service.parsers.base import BaseParser
from search_service.parsers.laptop.allnotebookparts import AllnotebookpartsParser
from search_service.parsers.laptop.dfi import DFIParser
from search_service.parsers.laptop.forlaptop import ForLaptopKievParser
from search_service.parsers.laptop.fornb import ForNBParser
from search_service.parsers.laptop.gsmforsage import GSMForsageParser
from search_service.parsers.laptop.laptopparts import LaptoppartsParser
from search_service.parsers.laptop.radiodetal import RadiodetalParser
from search_service.parsers.laptop.room_parts import RoomPartsParser
from search_service.parsers.laptop.smartparts import SmartpartsParser
from search_service.parsers.laptop.suncomp import SuncompParser
from search_service.parsers.phone.all_spares import AllSparesParser
from search_service.parsers.phone.artmobile import ArtmobileParser
from search_service.parsers.phone.gsm_complect import GsmComplectParser
from search_service.parsers.phone.icd import IcdParser
from search_service.parsers.phone.mobile_parts import MobilePartsParser
from search_service.parsers.phone.motorolka import MotorolkaParser
from search_service.parsers.phone.part_store import PartStoreParser
from search_service.parsers.phone.partstore import PartStore1Parser
from search_service.parsers.phone.stylecom import StylecomParser
from search_service.parsers.phone.tplus import TplusParser
from search_service.parsers.phone.vseplus import VseplusParser
from search_service.parsers.phone.welcom_mobi import WelcomMobiParser

laptops = {
    "ForLaptop": ForLaptopKievParser,
    "ForNB": ForNBParser,
    "SunComp": SuncompParser,
    "GSMForsage": GSMForsageParser,
    "SmartParts": SmartpartsParser,  # CPU intensive
    "AllNotebookParts": AllnotebookpartsParser,
    "LaptopParts": LaptoppartsParser,
    "RadioDetal": RadiodetalParser,
    "DFI": DFIParser,
    "RoomParts": RoomPartsParser,
}

phones = {
    "Motorolka": MotorolkaParser,  # CPU intensive
    "AllSpares": AllSparesParser,
    "Stylecom": StylecomParser,
    "TPlus": TplusParser,
    "GSMForsage": GSMForsageParser,
    "WelcomMobi": WelcomMobiParser,
    "Vseplus": VseplusParser,
    "Artmobile": ArtmobileParser,
    "Part-Store": PartStoreParser,
    "PartStore": PartStore1Parser,  # CPU intensive
    "GSMComplect": GsmComplectParser,
    "MobileParts": MobilePartsParser,
    "ICD": IcdParser,
}


def delete_old_files():
    current_time = datetime.now()
    for filename in os.listdir(os.path.join(DEFAULT_DIR)):
        if filename.endswith(".csv"):
            filepath = os.path.join(DEFAULT_DIR, filename)
            file_time = os.path.getmtime(filepath)
            file_datetime = datetime.fromtimestamp(file_time)
            if (current_time - file_datetime).seconds > 60 * 2:  # 16 hours
                os.remove(filepath)


def make_filename(query: str, parsers: list[BaseParser]) -> str:
    query = query.replace(" ", "_")
    pars_names = "_".join([parser.__class__.__name__[:4] for parser in parsers])
    return f"{query}_{pars_names}.csv"


def run_parser(parser):
    try:
        parser.parse()
    except TimeoutError:
        print(f"Timeout for {parser.filename}")


def start_pipline(query: str, parsers: list[BaseParser]) -> str:
    st = datetime.now()
    finalname = make_filename(query, parsers)
    filepath = os.path.join(DEFAULT_DIR, finalname)
    os.makedirs(DEFAULT_DIR, exist_ok=True)
    delete_old_files()

    max_workers = int(os.cpu_count() * 0.75) or 1
    print(f"Using {max_workers} workers for parsing")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_parser, parser) for parser in parsers]
        for future in futures:
            future.result()

    with open(filepath, "a") as f:
        for parser in parsers:
            if os.path.exists(parser.filename):
                with open(parser.filename, "r") as file:
                    lines = file.readlines()
                    f.writelines(lines[1:])

    end = datetime.now()
    print(f"Pipeline finished in {end - st}")
    return filepath
