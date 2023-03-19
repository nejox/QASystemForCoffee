from transformers import AutoTokenizer, AutoModelForQuestionAnswering, pipeline
from evaluate import load
from evaluate import evaluator
import torch
import pandas as pd
from utils import read_data, get_data_as_dataset_for_pipe, get_data_as_dataset

if __name__ == "__main__":
    # Read data
    data = read_data()
    df_data = pd.DataFrame(data)

    dataset = get_data_as_dataset()


    qa_model = pipeline("question-answering", model=model_checkpoint, tokenizer=model_checkpoint)

    #task_evaluator = evaluator("question-answering")
    #results = task_evaluator.compute(
    #    model_or_pipeline=qa_model,
    #    data=dataset_full,
    #    metric="squad")
    results = qa_model(dataset.remove_columns(["id", "title", "answers"]))
    print(results)

    print(f"Question: {df_data['question'].values[0]}")
    print(f"Answer: {answer}")
    pipe_answer = qa_model(question=df_data["question"].values[0], context=df_data["context"].values[0])
    print(f"Pipeline Answer: {pipe_answer}")
    print(f"True answer: {df_data['answers'].values[0]['text'][0]}")

    object = df_data.iloc[0].to_dict()
    object["answers"].pop('answer_end', None)

    references = [{"id": str(object["id"]), "answers": object["answers"]}, {"id": str(object["id"]), "answers": object["answers"]}]
    predictions = [{"id": str(object["id"]), "prediction_text": answer}, {"id": str(object["id"]), "prediction_text": pipe_answer["answer"]}]

    squad_metric = load("squad")
    # needs format: {'predictions': {'id': Value(dtype='string', id=None), 'prediction_text': Value(dtype='string', id=None)}, 'references': {'id': Value(dtype='string', id=None), 'answers': Sequence(feature={'text': Value(dtype='string', id=None), 'answer_start': Value(dtype='int32', id=None)}, length=-1, id=None)}}

    results = squad_metric.compute(predictions=predictions, references=references)
    print(results)


