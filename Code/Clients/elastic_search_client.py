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
from Code.Clients.abstract_client import ManualClient, MetaClient, ContextClient
import logging
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import elasticsearch
from Code.Utils import utils
from Code.config import config


class ElasticSearchClient(MetaClient, ManualClient, ContextClient):
    """
    Wrapper Class for the elasticsearch client
    offers all functionality concerning communication with the elasticsearch server
    """

    def __init__(self):
        """
        constructor which crates ElasticSearchClient with the elasticsearch
        url from the config file
        """

        logging.info("Init Elasticsearch client with url: %s : %s", config.ES_URL,
                     config.ES_PORT)
        self.es_client = Elasticsearch([config.ES_URL + ":" + config.ES_PORT])
        elasticsearch.logger.setLevel(config.ES_LOG_LEVEL)
        self._initialize_indices_if_not_existing()

    def _initialize_indices_if_not_existing(self):
        """
        initializes needed indizes if not already there
        """
        if not self.es_client.indices.exists(index=config.manuals_sourceIndex):
            logging.info("Index " + config.manuals_sourceIndex + " not found, initialize index.")
            self.es_client.indices.create(index=config.manuals_sourceMapping,
                                          ignore=400)  # , body=config.sourceMapping, ignore=400)
            # ignore 400 cause by IndexAlreadyExistsException when creating an index

        if not self.es_client.indices.exists(index=config.manuals_metaIndex):
            logging.info("Index " + config.manuals_metaIndex + " not found, initialize index.")
            self.es_client.indices.create(index=config.manuals_metaIndex, body=config.manuals_metaMapping, ignore=400)

        if not self.es_client.indices.exists(index=config.context_index):
            logging.info("Index " + config.context_index + " not found, initialize index.")
            self.es_client.indices.create(index=config.context_index, body=config.context_mapping, ignore=400)

    def delete_manual_metadata(self, id):
        """
        deletes meta_data doc in manual_meta_data index
        """
        self.es_client.delete(index=config.manuals_metaIndex, id=id)

    def get_manual_config(self, id):
        """
        search elasticsearch for article configs by id
        :param id: the id you want to search for
        :return: _source element of the found _doc or nothing
        """

        query = {"query": {"match": {"_id": {"query": id}}}}
        docs = self.es_client.search(index=config.manuals_sourceIndex, body=query)
        if docs["hits"]["hits"]:
            return docs["hits"]["hits"][0]["_source"]
        else:
            logging.error("id: " + id + " not found.")

    def get_all_manual_configs(self):
        """
        search elasticsearch for all article configs
        :return: result field - list format - with all _source elements of the index - can be empty
        """

        query = {"size": 1000, "query": {"match_all": {}}}
        docs = self.es_client.search(index=config.manuals_sourceIndex, body=query)
        result = []
        for doc in docs["hits"]["hits"]:
            result.append(doc["_source"])
        return result

    def index_manual_metadata(self, metadata_json):
        """
        index meta data to elasticsearch
        :return: the id of the new indexed meta data
        """

        result = self.es_client.index(index=config.manuals_metaIndex, body=metadata_json,
                                      doc_type="_doc")

        if result["result"] == "created" and result["_id"]:
            return result["_id"]

        else:
            raise Exception("manual metadata not created")

    def index_manual_config(self, id, doc):
        """
        does index a single doc of metadata for restriction/measures

        Args:
            id (string): id of the document
            doc (object/dict): document to insert
        """
        result = self.es_client.index(index=config.manuals_sourceIndex, id=id, body=doc)
        if not (result["result"] == "created" or result["result"] == "updated"):
            raise Exception("config could not be indexed")

    def get_latest_entry_URL(self, source_URL, manufacturer_name):
        """
        searches for the latest entries url of the given website, number of returned entries defined in config
        latest means  index time 
        :param source_URL: the URL of the site we are looking for the latest entry
        :returns: the url of the latest entries in the manual_meta_data index with the matching source_URL
        """
        try:
            result = []
            query = {
                "_source":
                    {"includes": ["URL"]
                     },
                "query":
                    {"bool":
                        {"must": [
                            {"match_phrase": {"manufacturer_name": {"query": manufacturer_name}}},
                            {"match_phrase": {"source_URL": {"query": source_URL}}}
                        ]}
                    },
                "sort": [{"index_time": {"order": "desc"}}],
                "size": 10000
            }
            docs = self.es_client.search(index=config.manuals_metaIndex, body=query)

            for doc in docs["hits"]["hits"]:
                result.append(doc["_source"]["URL"])

            return result
        except:
            return None

    def count_entries_by_product_and_manual(self, manufacturer, product_name, manual_name):
        """
        searches for entries by given manufacturer, product_name and manual_name to check if given manual already exists
        :param manufacturer: the name of the manufacturer
        :param product_name: the name of the product
        :param manual_name: the name of the manual
        :returns: the count of entries given the arguments
        """
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"manufacturer_name": manufacturer}},
                            {"match": {"product_name": product_name}},
                            {"match": {"manual_name": manual_name}}
                        ]
                    }
                }
            }
            response = self.es_client.count(index=config.manuals_metaIndex, body=query)

            return response["count"]
        except:
            return None

    def get_manufacturers(self):
        try:
            query = {
                "size": 0,
                "aggs": {
                    "manufacturer": {
                        "terms": {
                            "field": "manufacturer_name.keyword",
                            "size": 500
                        }
                    }
                }
            }

            docs = self.es_client.search(index=config.context_index, body=query)
            result = []
            if docs["aggregations"]["manufacturer"]:
                for manufacturer in docs["aggregations"]["manufacturer"]["buckets"]:
                    result.append(manufacturer["key"])

                return result

            else:
                logging.error("No manufactuers in metadata found")
        except:
            return

    def get_products_of_all_manufacturers(self):
        try:
            query = {
                "size": 0,
                "aggs": {
                    "manufacturers": {
                        "terms": {
                            "field": "manufacturer_name.keyword"
                        },
                        "aggs": {
                            "products": {
                                "terms": {
                                    "field": "product_name.keyword"
                                }
                            }
                        }
                    }
                }
            }

            docs = self.es_client.search(index=config.context_index, body=query)
            result = {}
            if docs["aggregations"]["manufacturers"]:
                for manufacturer in docs["aggregations"]["manufacturers"]["buckets"]:
                    result[manufacturer['key']] = []

                    for product in manufacturer["products"]["buckets"]:
                        result[manufacturer['key']].append(product["key"])

                return result

            else:
                logging.error("No manufactuer/product in metadata found")
        except:
            return

    def get_products_of_manufacturer(self, manufacturer):
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match_phrase": {
                                    "manufacturer_name": {
                                        "query": manufacturer

                                    }
                                }

                            }]
                    }
                },

                "aggs": {
                    "products": {
                        "terms": {
                            "field": "product_name.keyword"
                        }
                    }

                },
                "size": 0}

            docs = self.es_client.search(index=config.context_index, body=query)
            result = []
            if docs["aggregations"]["products"]:
                for product in docs["aggregations"]["products"]["buckets"]:
                    result.append(product["key"])

                return result

            else:
                logging.error("No products in metadata found")
        except:
            return

    def get_metadata_of_product(self, manufacturer, product):
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match_phrase": {
                                    "manufacturer_name": {
                                        "query": manufacturer
                                    }
                                }

                            },
                            {
                                "match_phrase": {
                                    "product_name": {
                                        "query": product
                                    }
                                }
                            }]
                    }
                }
            }

            docs = self.es_client.search(index=config.manuals_metaIndex, body=query)
            result = []
            if docs["hits"]["hits"]:
                for manual in docs["hits"]["hits"]:
                    result.append(manual["_source"])

                return result

            else:
                logging.error("No products in metadata found")
        except:
            return

    def bulk_index_contexts(self, docs):
        """
        bulk index contexts to elasticsearch
        :return: if error counter > 0 return False, else True
        """
        requests = []
        for i, doc in enumerate(docs):
            request = doc
            request["_op_type"] = "index"
            request["_index"] = config.context_index
            requests.append(request)
        success, failed = bulk(self.es_client, requests, stats_only=True)
        logging.info("Indexed %d contexts successfully, %d failed" % (success, failed))
        return failed == 0

    def index_context(self, context):
        """
        index context to elasticsearch
        :return: the id of the new indexed context
        """

        result = self.es_client.index(index=config.context_index, body=context,
                                      doc_type="_doc")

        if result["result"] == "created" and result["_id"]:
            return result["_id"]

        else:
            raise Exception("context not created")

    def delete_context(self, id):
        """
        deletes corpus_metadata doc in corpus_metaIndex index
        """
        self.es_client.delete(index=config.context_index, id=id)

    def get_context(self, manufacturer, product_name, language):

        try:
            query = {
                "size": 10000,
                "query": {
                    "bool": {
                        "must": []
                    }
                }
            }

            if manufacturer:
                query["query"]["bool"]["must"].append({"match_phrase": {"manufacturer_name": {"query": manufacturer}}})
            if product_name:
                query["query"]["bool"]["must"].append({"match_phrase": {"product_name": {"query": product_name}}})
            if language:
                query["query"]["bool"]["must"].append({"match_phrase": {"language": {"query": language}}})

            if not query["query"]["bool"]["must"]:
                # return whole corpusfile or tell application to answer based on
                # all it learned
                return None

            docs = self.es_client.search(index=config.context_index, body=query)
            result = []
            if docs["hits"]["hits"]:
                for doc in docs["hits"]["hits"]:
                    result.append(doc["_source"])

                return result

            else:
                logging.error("No context for: " + str(query["query"]["bool"]["must"]) + " not found.")

        except:
            return None

    # TODO not really sure if this is sufficient - check if return is all {n_returns} most similar contexts
    def search_similar_context(self, question_embedded, manufacturer=None, product_name=None, language="en",
                               n_returns: int = 100):
        try:
            body = {
                "size": n_returns,
                "query": {
                    "bool": {
                        "must": []
                    }
                },
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'vector_embedding') + 1.0",
                    # Add 1.0 because ES doesnt support negative score
                    "params": {"query_vector": question_embedded}
                }
            }
            script_query = {
                "script_score": {
                    "query": {
                        "bool": {
                            "must": []
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'vector_embedding') + 1.0",
                        "params": {"query_vector": question_embedded}
                    }
                }
            }

            if manufacturer:
                script_query["script_score"]["query"]["bool"]["must"].append(
                    {"match_phrase": {"manufacturer_name": {"query": manufacturer}}})
            if product_name:
                script_query["script_score"]["query"]["bool"]["must"].append(
                    {"match_phrase": {"product_name": {"query": product_name}}})
            if language:
                script_query["script_score"]["query"]["bool"]["must"].append({"match_phrase": {"language": {"query": language}}})

            if not script_query["script_score"]["query"]["bool"]["must"]:
                # return whole corpusfile or tell application to answer based on
                # all it learned
                script_query["script_score"]["query"] = {"match_all": {}}

            body = {
                "size": n_returns,
                "query": script_query,

            }

            docs = self.es_client.search(index=config.context_index, body=body)
            result = []
            if docs["hits"]["hits"]:
                for doc in docs["hits"]["hits"]:
                    result.append(doc["_source"])

                return result

            else:
                logging.error("No context for: " + str(body["query"]["bool"]["must"]) + " not found.")

        except Exception as e:
            logging.error(e)
            return None


class MockElasticSearchClient(MetaClient, ManualClient):

    def get_metadata_of_product(self, manufacturer, product):
        pass

    def get_manufacturers(self):
        pass

    def get_products_of_all_manufacturers(self):
        pass

    def get_products_of_manufacturer(self, manufacturer):
        pass

    def delete_context(self, id):
        pass

    def index_manual_metadata(self, metadata_json):
        return True

    def get_latest_entry_URL(self, source_URL, region):
        return False

    def delete_manual_metadata(self, id):
        return True

    def get_manual_config(self, id):
        return True

    def get_all_manual_configs(self):
        return True

    def __init__(self):
        pass

    def get_context(self, manufacturer, product_name, language):
        return True

    def index_context(self, corpusfile_metadata):
        return True

    def search_similar_context(self, question_embedded, manufacturer, product_name, language, n_returns: int):
        pass
