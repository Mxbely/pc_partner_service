import os
from datetime import datetime

from search_service.parsers.laptop.forlaptop import ForLaptopKievParser
from search_service.parsers.laptop.fornb import ForNBParser
from search_service.parsers.laptop.suncomp import SuncompParser
from search_service.parsers.phone.all_spares import AllSparesParser
from search_service.parsers.phone.motorolka import MotorolkaParser
from search_service.parsers.phone.stylecom import StylecomParser
from search_service.parsers.phone.tplus import TplusParser


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


def start_pipline(query: str):
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
    ]

    for parser in parsers:
        print(f"Start parser: {parser.filename}")
        parser.parse()
        print(f"Finished parser: {parser.filename}")

    if os.path.exists(finalname):
        os.remove(finalname)

    with open(finalname, "a") as f:
        for parser in parsers:
            if os.path.exists(parser.filename):
                with open(parser.filename, "r") as file:
                    lines = file.readlines()
                    f.writelines(lines[1:])

    return finalname
