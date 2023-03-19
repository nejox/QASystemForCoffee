import json
from Code.config import config
from Code.Clients.elastic_search_client import ElasticSearchClient
from os import listdir
from os.path import isfile, join

if __name__ == "__main__":
    path = config.CONFIG_PATH

    es_client = ElasticSearchClient()

    for f in listdir(path):
        if isfile(join(path, f)):
            with open(join(path, f), "r", encoding='utf-8') as file:
                source = json.load(file)
                try:
                    #if source["manufacturer_name"] == "Krups":
                    #   continue
                    es_client.index_manual_config(source["manufacturer_name"], source)
                except Exception as e:
                    print(source["manufacturer_name"])
                    print(e)
