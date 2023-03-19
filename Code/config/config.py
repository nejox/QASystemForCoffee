# -------------------------------COMMON-------------------------------------------------
import logging

MAX_TRY = 3
# dont change this config without checking if it is a elasticsearch readable date-format (if you use elasticsearch)
# https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-date-format.html#strict-date-time
STANDARD_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
STANDARD_DATE_FORMAT = "%Y-%m-%d"
STANDARD_LOG_FORMAT = "[%(levelname)s][%(asctime)s]: %(message)s"
STANDARD_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
STANDARD_LOG_FILENAME = "../ManualScraper/manualscraper.log"
WEBDRIVER_DIR = "../Utils/drivers"
WEBDRIVER_FILE = "chromedriver.exe"
CLIENTS = {
    "META_CLIENT": "elastic",
    "MANUAL_CLIENT": "elastic",
    "FILE_CLIENT": "lfs",
    "CONTEXT_CLIENT": "elastic"
}
# -------------------------------HuggingFace--------------------------------------------
QA_MODEL = "nejox/roberta-base-squad2-coffee20230108"
MAX_ANSWERS = 5
EMBEDDER = "nejox/all-MiniLM-L6-v2_fine_tuned_coffee"
# -------------------------------LFS----------------------------------------------------
CORPUS_PATH = "../Preprocessor/corpus/"
CONFIG_PATH = "../ManualScraper/manual_sources/"
MANUAL_PATH = "../ManualScraper/manuals/"
# -------------------------------HDFS---------------------------------------------------
HDFS_URL = "127.0.0.1"
HDFS_PORT = "9870"
HDFS_USER = "hadoop"
# -------------------------------ElasticSearch------------------------------------------
ES_URL = '127.0.0.1'
ES_PORT = '9200'
ES_LOG_LEVEL = logging.WARNING

SIM_SEARCH_RETURNS = 50

KEY = "KEY"

manuals_sourceIndex = "manuals_config"
manuals_sourceMapping = {

}

manuals_metaIndex = "manuals_meta"
manuals_metaMapping = {
    "mappings": {
        "properties": {
            "URL": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 512
                    }
                }
            },
            "filename": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "filepath": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 512
                    }
                }
            },
            "index_time": {
                "type": "date",
                "format": "yyyy-MM-dd'T'HH:mm:ssZ"
            },
            "language": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "manual_name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "manufacturer_name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "product_name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "source_URL": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            }
        }
    }
}

context_index = "context"
EMBEDDING_DIM = 384  # depends on the embedding model, right?
context_mapping = {
    "mappings": {
        "properties": {
            "manufacturer_name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "product_name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "language": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "headerId": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "headerText": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 512
                    }
                }
            },
            "headerParagraphText": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 2048
                    }
                }
            },
            "subHeaderId": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "SubHeaderText": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "subHeaderParagraphText": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 2048
                    }
                }
            },
            "vector_embedding": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIM
            },
            "index_time": {
                "type": "date",
                "format": "yyyy-MM-dd'T'HH:mm:ssZ"
            },
        }
    }
}
