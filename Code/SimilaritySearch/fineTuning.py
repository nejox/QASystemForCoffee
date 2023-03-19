from huggingface_hub import HfApi
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
from datasets import load_dataset

from lossEvaluator import LossEvaluator


def save_manually_to_hub(repo_name, path):
    # path = 'C:/Users/Jochen/MAI_NLP_PROJECT/Code/SimilaritySearch/all-MiniLM-L6-v2_fine_tuned_coffee/'
    api = HfApi()
    api.create_repo(repo_id=repo_name, exist_ok=True)

    files_to_push_to_hub = [
        'README.md',
        'config.json',
        'config_sentence_transformers.json',
        'modules.json',
        'pytorch_model.bin',
        'sentence_bert_config.json',
        'special_tokens_map.json',
        'tokenizer.json',
        'tokenizer_config.json',
        'vocab.txt'
    ]

    for filename in files_to_push_to_hub:
        api.upload_file(
            path_or_fileobj=path + filename,
            repo_id="nejox/" + repo_name,
            path_in_repo=filename,
            repo_type="model",
            commit_message="Pushing fine-tuned SimSearch model",
            commit_description="Fine-tuned sentence transformer model for coffee"
        )

    api.upload_folder(
        folder_path=path + "1_Pooling",
        path_in_repo="1_Pooling",
        repo_id="nejox/" + repo_name,
        repo_type="model",
    )


def save_model_to_hub(model, repo_name, private=False, exist_ok=True):
    model.save_to_hub(repo_name, private=private, exist_ok=exist_ok)


if __name__ == '__main__':
    embName = 'all-MiniLM-L6-v2_fine_tuned_coffee'
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    dataset = load_dataset("json", data_files="train_data.json")

    train_data = dataset['train']['set']
    n_examples = dataset['train'].num_rows

    train_examples = []
    for i in range(n_examples):
        example = train_data[i]
        train_examples.append(InputExample(texts=[example[0], example[1]]))

    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=8)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)
    num_epochs = 10
    warmup_steps = int(len(train_dataloader) * num_epochs * 0.1)

    eva = LossEvaluator(train_dataloader, loss_model=train_loss, log_dir='logs/')

    model.fit(train_objectives=[(train_dataloader, train_loss)],
              evaluator=eva,
              evaluation_steps=10,
              output_path=embName + "_eva",
              epochs=num_epochs,
              warmup_steps=warmup_steps,
              save_best_model=True)

    model.save(embName)

    try:
        save_model_to_hub(model, embName)
    except:
        save_manually_to_hub(embName, embName + '/')
