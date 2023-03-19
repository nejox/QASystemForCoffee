import layoutparser as lp
import Code.Clients.client_factory as clientfactory
import time
import pandas as pd
import os
import sys
import glob
from loguru import logger
from segmentation import Segmenter


class Preprocessor:
    def __init__(self, mode=0, output_path=None, model_path=None, verbose="ERROR"):
        """
        Preprocessor for the coffee manufacturer manuals.

        Parameters
        ----------
        output_path : Path | str
            Path for where the outputted csv-file should be saved. If not provided a pandas DataFrame will be returned.
        model_path : Path | str
            Path for where the trained model lies.
        verbose : str
            Based on value more logging details will get outputted.
        """
        self._mode = mode
        self._output_path = output_path
        # self._model = self._load_model(model_path)
        self._model = None
        self._setup_logger(verbose)
        logger.info(f"Instantiated Preprocessor with specified model in path {'/' + model_path}")


    def _setup_logger(self, verbose):
        logger.remove()
        logger.add("logs/logfile.log", level=verbose, rotation="100 MB")
        # logger.add(sys.stdout, level=verbose)


    def _load_model(self, model_path, manufacturer):
        # model = lp.Detectron2LayoutModel(
        #     config_path = "/content/drive/MyDrive/vdu/model/config.yaml",
        #     model_path = "/content/drive/MyDrive/vdu/model/model_5_manufacturers.pth",
        #     label_map = {0: "Figure", 1: "Header", 2: "Subheader", 3: "Table", 4: "Text", 5: "ToC"},
        #     extra_config = ["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.6] # <-- Only output high accuracy preds
        # )
        if manufacturer == ".ipynb_checkpoints":
            return None

        logger.info(f"Loaded /content/drive/MyDrive/vdu/single_labeling/{manufacturer}/model/config.yaml")

        model = lp.Detectron2LayoutModel(
            config_path=f"/content/drive/MyDrive/vdu/single_labeling/{manufacturer}/model/config.yaml",
            model_path=f"/content/drive/MyDrive/vdu/single_labeling/{manufacturer}/model/model_final.pth",
            label_map={0: "Header", 1: "Subheader", 2: "Table", 3: "ToC"},
            extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5]  # <-- Only output high accuracy preds
        )

        return model


    def process(self, manuals_path):
        """
        Main method for preprocessing the incoming pdf files.

        Parameters
        ----------
        paths : List[Path | str] | Path | str
            Can be either a list of file paths or simply a single path either to a file or a folder.
            
        Returns
        -------
        None | DataFrame
            Depending on if a output file path was given, if 
                - yes: the corresponding csv file will be safed at the given location
                - no: a pandas DataFrame will be outputted        
        """
        time_start_all = time.time()

        corpus = []

        error_files = []

        # load all manufacturers names
        manufacturers = clientfactory.get_meta_client().get_manufacturers()

        # loop through all manufacturers
        for manufacturer in manufacturers:
            time_start_manufacturer = time.time()
            self._model = self._load_model("", manufacturer)

            manufacturer_dic = {}
            manufacturer_products = []

            products = clientfactory.get_meta_client().get_products_of_manufacturer(manufacturer)
            filepath = os.path.join(self._output_path, manufacturer)

            # Second Loop through all Products of Manufacturer
            for product in products:
                product_dic = {}

                df_list = []

                # get all pdfs of product
                metadatas = clientfactory.get_meta_client().get_metadata_of_product(manufacturer, product)

                if not len(metadatas):
                    logger.error(f"No metadata found for product" + str(product))
                    continue

                # Third Loop through all Manuals of Products
                for metadata in metadatas:
                    try:
                        time_start_single = time.time()
                        manual_name = metadata["manual_name"]
                        logger.info(f"Processing {manual_name}.")

                        # load pdf
                        pdf_location = metadata["filepath"] + metadata["filename"]
                        pdf = clientfactory.get_file_client().read_file(pdf_location)

                        # segment
                        segmenter = Segmenter(pdf, self._model)
                        pdf_df = segmenter.get_segments_df(self._mode)

                        pdf_df = self._filter(pdf_df)
                        pdf_df = self._correct_points(pdf_df)

                        df_list.append(pdf_df)
                        time_finish_single = time.time()
                        logger.info(
                            f"Finished processing {manual_name}. - Took {time_finish_single - time_start_single} seconds.")
                    except:
                        error_files.append(pdf)
                        logger.error(f"Error occured while processing {manual_name} - Skipping this file.")

                if len(df_list) == 0:
                    continue

                df = pd.concat(df_list, ignore_index=True)
                df = df[['file', 'language', 'label', 'text']]


                # TODO if necessary more metadata can be added here
                product_object = self._objectify_segments(df)
                product_dic['product_id'] = product
                product_dic['languages'] = product_object
                manufacturer_products.append(product_dic)


                # TODO save to ES right here if necessary

                filename = product + "_preprocessed.csv"
                clientfactory.get_file_client().save_as_file(file_path=filepath, filename=product, content=df.to_csv())
                logger.info(f"Saving the output dataframe to {filename}")

            manufacturer_dic['manufacturer'] = manufacturer
            manufacturer_dic['products'] = manufacturer_products
            corpus.append(manufacturer_dic)
            time_finish_manufacturer = time.time()
            logger.info(
                f"Finished processing {manufacturer}. - Took {time_finish_manufacturer - time_start_manufacturer} seconds.")

        time_finish_all = time.time()
        logger.info(f"Finished processing {len(df_list)} documents. - Took {time_finish_all - time_start_all} seconds.")

        with open('your_file.txt', 'w') as f:
            for line in error_files:
                f.write(f"{line}\n")

        return corpus


    def _objectify_segments(self, df):
        language_dic = {}

        for language in df['language'].unique():
            language_df = df[df['language'] == language]

            language_list = []

            header_id_count = 1
            subheader_id_count = 1
            last_label = None

            for row in language_df.itertuples():
                language = row.language
                label = row.label
                text = row.text

                if "Header" in label:
                    header_dic = {
                        "headerId": header_id_count,
                        "headerText": text,
                        "paragraphText": "",
                        "headerChildren": []
                    }

                    language_list.append(header_dic)
                    header_id_count += 1
                    subheader_id_count = 1
                    last_label = "Header"

                # Only Evaluate the other Options if a Header is set
                if header_id_count == 1:
                    continue

                if "Subheader" in label:
                    subheader_dic = {
                        "subHeaderId": subheader_id_count,
                        "subHeaderText": text,
                        "paragraphText": ""
                    }

                    language_list[-1]["headerChildren"].append(subheader_dic)

                    subheader_id_count += 1
                    last_label = "Subheader"

                if "Paragraph" in label:
                    if last_label == "Header":
                        language_list[-1]['paragraphText'] = text

                    if last_label == "Subheader":
                        language_list[-1]['headerChildren'][-1]["paragraphText"] = text

                    if last_label == "Paragraph":
                        continue

                    last_label = "Paragraph"

            language_dic[language] = language_list

        return language_dic


    def _filter(self, df):
        """
        Method for filtering certain unnecessary Paragraphs.

        Parameters
        ----------
        df : pandas.DataFrame
            Preprocessed Pandas DataFrame.
        
        Returns
        -------
        pandas.DataFrame
            Filtered Pandas DataFrame.
        """
        df = df.drop(df[df.text.str.len() <= 4].index)

        return df


    def _correct_points(self, df):
        df['text'] = df['text'].str.replace('�', '.')

        return df


    def _save_corpus_metadata(self):
        pass  # TODO
