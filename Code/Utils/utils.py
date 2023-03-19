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
from datetime import datetime, date
import dateutil
import unicodedata
import re
from Code.config import config
import pytz
from urllib.parse import urljoin, urlparse


def parse_date(index_date):
    """
    parses a date to the STANDARD_DATETIME_FORMAT from config 
    :param index_date: the date to parse, can be str or date
    :return: the date in new format
    """
    if type(index_date) == str:
        index_date = re.sub(r"[a-zA-Z]+", " ", index_date)
        index_date = dateutil.parser.parse(index_date)

    return index_date.strftime(config.STANDARD_DATETIME_FORMAT)


def date_now():
    """
    returns current datetime in the STANDARD_DATETIME_FORMAT
    """
    return parse_date(datetime.now(pytz.timezone("Europe/Berlin")))


def date_today():
    """
    returns todays date in the STANDARD_DATE_FORMAT
    """
    return date.today().strftime(config.STANDARD_DATE_FORMAT)

def clean_url(url):
    return urljoin(url, urlparse(url).path)

def slugify(value, allow_unicode=True):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    value.replace("ä", "ae").replace("Ä", "Ae").replace("ö", "oe").replace("Ö", "Oe").replace("ü", "ue").replace("Ü",
                                                                                                                 "Ue").replace(
        "ß", "ss")
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '_', value).strip('-_')

#  titlestring.replace(" ", "_").replace(",", "_").replace(":", "_").replace("ä", "ae").replace("Ä", "Ae").replace("ö", "oe").replace("Ö", "Oe").replace("ü", "ue").replace("Ü", "Ue")
