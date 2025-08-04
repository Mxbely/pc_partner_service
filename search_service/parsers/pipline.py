import os
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from playwright.sync_api import TimeoutError

from search_service.parsers.base import BaseParser
from search_service.parsers.laptop.allnotebookparts import AllnotebookpartsParser
from search_service.parsers.laptop.dfi import DFIParser
from search_service.parsers.laptop.forlaptop import ForLaptopKievParser
from search_service.parsers.laptop.fornb import ForNBParser
from search_service.parsers.laptop.gsmforsage import GSMForsageParser
from search_service.parsers.laptop.laptopparts import LaptoppartsParser
from search_service.parsers.laptop.radiodetal import RadiodetalParser
from search_service.parsers.laptop.smartparts import SmartpartsParser
from search_service.parsers.laptop.suncomp import SuncompParser
from search_service.parsers.phone.all_spares import AllSparesParser
from search_service.parsers.phone.artmobile import ArtmobileParser
from search_service.parsers.phone.gsm_complect import GsmComplectParser
from search_service.parsers.phone.motorolka import MotorolkaParser
from search_service.parsers.phone.part_store import PartStoreParser
from search_service.parsers.phone.stylecom import StylecomParser
from search_service.parsers.phone.tplus import TplusParser
from search_service.parsers.phone.vseplus import VseplusParser
from search_service.parsers.phone.welcom_mobi import WelcomMobiParser


filters = {
    "ForLaptop": ForLaptopKievParser,
    "Motorolka": MotorolkaParser,  # CPU intensive
    "AllSpares": AllSparesParser,
    "ForNB": ForNBParser,
    "Stylecom": StylecomParser,
    "SunComp": SuncompParser,
    "TPlus": TplusParser,
    "GSMForsage": GSMForsageParser,
    "WelcomMobi": WelcomMobiParser,
    "SmartParts": SmartpartsParser,  # CPU intensive
    "Vseplus": VseplusParser,
    "Artmobile": ArtmobileParser,
    "AllNotebookParts": AllnotebookpartsParser,
    "LaptopParts": LaptoppartsParser,
    "RadioDetal": RadiodetalParser,
    "DFI": DFIParser,
    "PartStore": PartStoreParser,
    "GSMComplect": GsmComplectParser,
}

def delete_old_files():
    current_time = datetime.now()
    for filename in os.listdir("."):
        if filename.endswith(".csv"):
            file_time = os.path.getmtime(filename)
            file_datetime = datetime.fromtimestamp(file_time)
            if (current_time - file_datetime).seconds > 60 * 60 * 16:  # 16 hours
                os.remove(filename)


def check_file_exists(filename: str) -> bool:
    delete_old_files()
    return os.path.exists(filename)


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
    if check_file_exists(finalname):
        print(f"File {finalname} already exists. Returning existing file.")
        return finalname

    max_workers = int(os.cpu_count() * 0.75) or 1
    print(f"Using {max_workers} workers for parsing")
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_parser, parser) for parser in parsers]
        for future in futures:
            future.result()

    if os.path.exists(finalname):
        os.remove(finalname)

    with open(finalname, "w") as f:
        pass

    with open(finalname, "a") as f:
        for parser in parsers:
            if os.path.exists(parser.filename):
                with open(parser.filename, "r") as file:
                    lines = file.readlines()
                    f.writelines(lines[1:])
                os.remove(parser.filename)
    end = datetime.now()
    print(f"Pipeline finished in {end - st}")
    return finalname
