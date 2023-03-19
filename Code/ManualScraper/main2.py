#####################################################################
#                                                                   #
#                     Lennard Rose 5122737                          #
#                     Jochen Schmidt 5122xxx                        #
#                     Esther Ademola 5122xxx                        #
#                     Marius Benkert 5122xxx                        #
#       University of Applied Sciences Wuerzburg Schweinfurt        #
#                           SS2022                                  #
#                                                                   #
#####################################################################
import json
from argument_parser_wrapper import ArgumentParserWrapper
from manual_scraper import ManualScraper
import logging
from Code.config import config

if __name__ == '__main__':

    logging.basicConfig(filename=config.STANDARD_LOG_FILENAME,
                        format=config.STANDARD_LOG_FORMAT,
                        datefmt=config.STANDARD_LOG_DATE_FORMAT,
                        level=logging.DEBUG)

    logging.info("Start ManualScraper")

    scraper = ManualScraper()
    parser = ArgumentParserWrapper()

    with open("./manual_sources/aeg.json", "r", encoding='utf-8') as file:
        source = json.load(file)
        scraper.scrape(source)

    logging.info("Close ManualScraper")
