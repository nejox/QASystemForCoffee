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
import os
from Code.Clients.abstract_client import FileClient
import json
import logging


class LFSClient(FileClient):
    """
    Saves to local file system
    """

    def save_as_file(self, file_path, filename, content):
        """
        combines the file_path and filename to the location to save the content
        careful it overwrites the file if already present
        :param file_path: the path the file will be saved to, no filename here
        :param filename: the name of the file that will be saved
        :param content: the content that will be saved in the file
        :return: nothing
        """
        os.makedirs(file_path, exist_ok=True)
        target = os.path.join(file_path, filename)

        with open(target, "wb") as file:
            file.write(content)


    def read_file(self, file_path):
        """
        reads a file from the given file_path, including the filename  and returns it as json
        :param file_path: the path the file, filename included
        :return: json presentation of the files content
        """
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except:
            logging.error(file_path + " not found.")
