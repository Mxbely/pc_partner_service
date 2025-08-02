import os
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from playwright.sync_api import TimeoutError

from search_service.parsers.laptop.allnotebookparts import AllnotebookpartsParser
from search_service.parsers.laptop.forlaptop import ForLaptopKievParser
from search_service.parsers.laptop.fornb import ForNBParser
from search_service.parsers.laptop.gsmforsage import GSMForsageParser
from search_service.parsers.laptop.laptopparts import LaptoppartsParser
from search_service.parsers.laptop.smartparts import SmartpartsParser
from search_service.parsers.laptop.suncomp import SuncompParser
from search_service.parsers.phone.all_spares import AllSparesParser
from search_service.parsers.phone.artmobile import ArtmobileParser
from search_service.parsers.phone.motorolka import MotorolkaParser
from search_service.parsers.phone.stylecom import StylecomParser
from search_service.parsers.phone.tplus import TplusParser
from search_service.parsers.phone.vseplus import VseplusParser
from search_service.parsers.phone.welcom_mobi import WelcomMobiParser


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


def make_filename(query: str) -> str:
    query = query.replace(" ", "_")
    return f"{query}.csv"


def run_parser(parser):
    try:
        parser.parse()
    except TimeoutError:
        print(f"Timeout for {parser.filename}")


def start_pipline(query: str):
    st = datetime.now()
    finalname = make_filename(query)
    if check_file_exists(finalname):
        print(f"File {finalname} already exists. Returning existing file.")
        return finalname

    parsers = [
        ForLaptopKievParser(query),
        MotorolkaParser(query),
        AllSparesParser(query),
        ForNBParser(query),
        StylecomParser(query),
        SuncompParser(query),
        TplusParser(query),
        GSMForsageParser(query),
        WelcomMobiParser(query),
        SmartpartsParser(query), # CPU intensive
        VseplusParser(query),
        ArtmobileParser(query),
        AllnotebookpartsParser(query),
        LaptoppartsParser(query),
    ]

    max_workers = int(os.cpu_count() * 0.75) or 1
    print(f"Using {max_workers} workers for parsing")
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_parser, parser) for parser in parsers]
        for future in futures:
            future.result()

    if os.path.exists(finalname):
        os.remove(finalname)

    with open(finalname, "a") as f:
        for parser in parsers:
            if os.path.exists(parser.filename):
                with open(parser.filename, "r") as file:
                    lines = file.readlines()
                    f.writelines(lines[1:])
    end = datetime.now()
    print(f"Pipeline finished in {end - st}")
    return finalname
