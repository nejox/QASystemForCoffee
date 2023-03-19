import json
import pandas as pd
import numpy as np
import os
import copy

from datasets import Dataset
from datasets import DatasetDict

basePath = "generated_training_data/"


def get_data_as_dataset():
    df_data = pd.DataFrame(read_data())
    df_data["id"] = df_data['id'].apply(str)
    dataset = Dataset.from_pandas(df_data)
    return dataset


def get_data_as_dataset_for_pipe():
    data = read_data()

    dataset = Dataset.from_pandas(pd.DataFrame(data)[["question", "context"]])
    return dataset


def read_data_autotrain():
    data = read_data(popAnswerEnd=True)

    # filter multiple answers
    for dic in data:
        answers = len(dic["answers"]["text"])
        if answers > 1:
            for i in range(1, answers):
                newDic = copy.deepcopy(dic)
                newDic["answers"]["text"] =  [dic["answers"]["text"][i]]
                newDic["answers"]["answer_start"] = [dic["answers"]["answer_start"][i]]
                #newDic["answers"]["answer_end"] = dic["answers"]["answer_end"][i]
                data.append(newDic)

            dic["answers"]["text"] = [dic["answers"]["text"][0]]
            dic["answers"]["answer_start"] = [dic["answers"]["answer_start"][0]]

            print(dic["id"])
        
        dic["answers"]["answer_start"] = dic["answers"]["answer_start"][0]
            
    
    # convert answer_start to int
    for dic in data:
        answers = len(dic["answers"]["text"])
        if answers > 1:
            print("alarm")

    return data

def read_data(popAnswerEnd=True):
    json_files = [pos_json for pos_json in os.listdir(basePath) if pos_json.endswith('.json')]

    data = []

    for json_file in json_files:
        data.extend(json.load(open(basePath + "/" + json_file, encoding="utf8")))

    formattedData = format_data(data)

    if popAnswerEnd:
        for d in formattedData:
            d["answers"].pop("answer_end", None)

    return formattedData


def format_data(data):
    formattedData = []

    for idx, dic in enumerate(data):
        # make all keys lowercase for easier working
        dic = {k.lower(): v for k, v in dic.items()}

        if not "answer" in dic:
            continue

        if "answer" in dic:
            newDic = {}

            newDic["id"] = idx
            newDic["title"] = f"Test_{idx}"

            if not "text" in dic:
                dic["text"] = dic["context"]

            newDic["context"] = dic["text"]
            newDic["question"] = dic["question"]

            answers = []
            answersStart = []
            answersEnd = []

            # special case handling
            if type(dic["answer"]) == dict:

                text = dic["answer"]["text"]
                answer_start = dic["answer"]["answer_start"]
                if "end" in dic["answer"]:
                    answer_end = dic["answer"]["answer_end"]
                else:
                    # print(dic["answer"])
                    answer_end = [start + len(text) for start, text in
                                  zip(dic["answer"]["answer_start"], dic["answer"]["text"])]

                newDic["answers"] = {
                    "text": text,
                    "answer_start": answer_start,
                    "answer_end": answer_end
                }
                # print(newDic["answers"])

            else:

                for answer in dic["answer"]:
                    answers.append(answer["text"])
                    answersStart.append(int(answer["start"]))
                    answersEnd.append(int(answer["end"]))

                newDic["answers"] = {
                    "text": answers,
                    "answer_start": answersStart,
                    "answer_end": answersEnd
                }

            formattedData.append(newDic)

    return formattedData


def convertToAutotrain():

    df_data = pd.DataFrame(read_data_autotrain())

    return df_data
