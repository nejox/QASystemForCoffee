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
from Code.Clients.lfs_client import LFSClient
from Code.Clients.hdfs_client import HDFSClient
from Code.Clients.abstract_client import *
from Code.Clients.elastic_search_client import ElasticSearchClient, MockElasticSearchClient
from Code.config import config

_file_client = None
_manual_client = None
_meta_client = None
_context_client = None


def get_meta_client() -> MetaClient:
    """
    returns a client for metadata
    """
    global _meta_client
    if _meta_client is None:
        _meta_client = _read_client_from_config("META_CLIENT")
    return _meta_client


def get_manual_client() -> ManualClient:
    """
    returns a client for manual_configs
    """
    global _manual_client
    if _manual_client is None:
        _manual_client = _read_client_from_config("MANUAL_CLIENT")
    return _manual_client


def get_file_client() -> FileClient:
    """
    returns a client for files
    """
    global _file_client
    if _file_client is None:
        _file_client = _read_client_from_config("FILE_CLIENT")
    return _file_client


def get_context_client() -> ContextClient:
    """
    returns a client for context paragraphs
    """
    global _context_client
    if _context_client is None:
        _context_client = _read_client_from_config("CONTEXT_CLIENT")
    return _context_client


def _read_client_from_config(client_type):
    """
    returns a client based on its type and the class as set in the config file
    """
    client_name = config.CLIENTS[client_type]

    if client_name == "elastic":
        return ElasticSearchClient()
    elif client_name == "mock_elastic":
        return MockElasticSearchClient()
    elif client_name == "hdfs":
        return HDFSClient()
    elif client_name == "lfs":
        return LFSClient()
    else:
        logging.error("Unable to find client: " + client_name)
