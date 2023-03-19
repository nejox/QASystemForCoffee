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
from pywebhdfs.webhdfs import PyWebHdfsClient
from Code.Clients.abstract_client import FileClient
import json
import logging
from Code.config import config


class HDFSClient(FileClient):
    """
    HDFS Helper class
    """


    def __init__(self):
        """
        init function that creates an insecure hdfs client
        """
        logging.info("Init HDFS client with url: %s : %s", config.HDFS_URL, config.HDFS_PORT)
        self.hdfs_client = PyWebHdfsClient(host=config.HDFS_URL, port=config.HDFS_PORT,
                                           user_name=config.HDFS_USER, timeout=1)


    def read_file(self, file_path):
        """
        reads a file from the given file_path, including the filename  and returns it as json
        :param file_path: the path the file, filename included
        :return: json presentation of the files content
        """
        return json.loads(self.hdfs_client.read_file(file_path))


    def save_as_file(self, file_path, filename, content):
        """
        combines the file_path and filename to the location to save the content
        raises error if save was not successfull
        careful it overwrites the file if already present
        :param file_path: the path the file will be saved to, no filename here
        :param filename: the name of the file that will be saved
        :param content: the content that will be saved in the file
        :return: nothing
        """

        target_file_path = os.path.join(file_path, filename)
        success = self.hdfs_client.create_file(target_file_path, content, overwrite=True)

        if not success:
            raise Exception("failed to save content as file to hdfs")
