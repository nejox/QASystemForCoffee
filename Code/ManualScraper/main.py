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

from tqdm import tqdm

from argument_parser_wrapper import ArgumentParserWrapper
from manual_scraper import ManualScraper
import logging
import sys
from Code.config import config

if __name__ == '__main__':

    logging.basicConfig(filename=config.STANDARD_LOG_FILENAME,
                        format=config.STANDARD_LOG_FORMAT,
                        datefmt=config.STANDARD_LOG_DATE_FORMAT,
                        level=logging.DEBUG)
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setLevel(logging.INFO)
    #logging.getLogger().addHandler(streamHandler)
    # TODO needs more fine tuning

    logging.info("Start ManualScraper")

    scraper = ManualScraper()
    parser = ArgumentParserWrapper()

    for source in tqdm(parser.parse_data_from_arguments(), desc="scrape sources"):
        scraper.scrape(source)

    logging.info("Close ManualScraper")
