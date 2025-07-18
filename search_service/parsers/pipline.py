import os
from datetime import datetime
from functools import cache

from search_service.parsers.laptop.forlaptop import ForLaptopKievParser
from search_service.parsers.phone.all_spares import AllSparesParser
from search_service.parsers.phone.motorolka import MotorolkaParser


@cache
def start_pipline(query: str):
    time_ = datetime.today().strftime("%Y-%m-%d_%H-%M")
    parsers = [
        ForLaptopKievParser(query),
        MotorolkaParser(query),
        AllSparesParser(query),
    ]

    for parser in parsers:
        print(f"Start parser: {parser.filename}")
        parser.parse()
        print(f"Finished parser: {parser.filename}")

    query = query.replace(" ", "_")

    finalname = f"{query}_{time_}.csv"

    if os.path.exists(finalname):
        os.remove(finalname)

    with open(finalname, "a") as f:
        for parser in parsers:
            if os.path.exists(parser.filename):
                with open(parser.filename, "r") as file:
                    lines = file.readlines()
                    f.writelines(lines[1:])  # Пропускаємо заголовок

    # with open(finalname, "r") as f:
    #     print(f.read())

    return finalname
