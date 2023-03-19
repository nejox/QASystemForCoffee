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
from abc import ABC, abstractmethod
import logging


class MetaClient(ABC):

    @abstractmethod
    def index_manual_metadata(self, metadata_json):
        logging.error("Method not implemented")


    @abstractmethod
    def get_latest_entry_URL(self, source_URL, region):
        logging.error("Method not implemented")


    @abstractmethod
    def delete_manual_metadata(self, id):
        logging.error("Method not implemented")


    @abstractmethod
    def get_manufacturers(self):
        logging.error("Method not implemented")


    @abstractmethod
    def get_products_of_manufacturer(self, manufacturer):
        logging.error("Method not implemented")


    @abstractmethod
    def get_metadata_of_product(self, manufacturer, product):
        logging.error("Method not implemented")


class ManualClient(ABC):

    @abstractmethod
    def get_manual_config(self, id):
        logging.error("Method not implemented")


    @abstractmethod
    def get_all_manual_configs(self):
        logging.error("Method not implemented")


class FileClient(ABC):

    @abstractmethod
    def save_as_file(self, file_path, filename, content):
        logging.error("Method not implemented")


    @abstractmethod
    def read_file(self, file_path):
        logging.error("Method not implemented")


class ContextClient(ABC):
    """
    @abstractmethod
    def index_context(self, data):
        logging.error("Method not implemented")
    """
    @abstractmethod
    def search_similar_context(self, question_embedded, manufacturer, product_name, language, n_returns: int):
        logging.error("Method not implemented")

    @abstractmethod
    def bulk_index_contexts(self, docs):
        logging.error("Method not implemented")

    @abstractmethod
    def index_context(self, context):
        logging.error("Method not implemented")


    @abstractmethod
    def get_context(self, manufacturer, product_name, language):
        logging.error("Method not implemented")


    @abstractmethod
    def delete_context(self, id):
        logging.error("Method not implemented")

