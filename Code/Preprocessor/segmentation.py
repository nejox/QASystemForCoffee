import numpy as np
import time
import fitz
import pandas as pd
from langdetect import detect
from loguru import logger

class Segmenter:
    def __init__(self, file, model):
        self._file = file
        self._model = model

    def get_segments_df(self, mode):
        if mode == 0:
            return self._attribute_headline_detection()
        
        if mode == 1:
            return self._visual_headline_detection()

    def _attribute_headline_detection(self):
        """
        Method to extract the headers and paragraphs out of a given document through Character Attributes.

        Parameters
        ----------
        
        Returns
        -------
        final_dic : pandas.DataFrame
            DataFrame containing information about every passage in the given document.
            With columns [file, language, label, text].
        """
        pass

    def _visual_headline_detection(self):
        """
        Method to extract the headers and paragraphs out of a given document through Object Detection.
        
        Returns
        -------
        final_dic : pandas.DataFrame
            DataFrame containing information about every passage in the given document.
            With columns [file, language, label, text].
        """
        import layoutparser as lp
        import pdf2image
        
        # Load PDF with Fitz
        doc = fitz.open(self._file)

        # Load Images of PDF
        logger.info(f"Converting PDF pages to images.")
        doc_images = np.asarray(pdf2image.convert_from_path(self._file, dpi=72))
        logger.info(f"Finished Converting PDF pages to images.")

        word_dic_list = []

        for idx_pages, page in enumerate(doc.pages()):
          if (idx_pages + 1) % 5 == 0 or idx_pages == 0:
              logger.info(f"Processing Page {idx_pages+1}/{doc.page_count}")
          page_language = self._get_page_language(page)
          
          start = time.time()

          layout = self._model.detect(doc_images[page.number])
          annotated = lp.draw_box(doc_images[page.number], layout, box_width=2, box_alpha=0.2, show_element_type=False)
          # annotated.save(f"annotated_images/delonghi/{idx_pages}.png", "PNG")
          headers = lp.Layout([b for b in layout if b.type=='Header'])
          subheaders = lp.Layout([b for b in layout if b.type=='Subheader'])

          toc = lp.Layout([b for b in layout if b.type=='ToC'])

          if toc:
            continue

          words = page.get_text("words")

          for word in words:
            word_dic = {}
            word_dic['word'] = word[4]
            word_dic['label'] = "Paragraph"
            word_dic['page_nbr'] = idx_pages+1
            word_dic['file'] = doc.name
            word_dic['language'] = page_language

            # check for header intersection
            for idx, header in enumerate(headers):
              if fitz.Rect(word[:4]).intersects(fitz.Rect(header.coordinates)):
                word_dic['label'] = f"Header_{idx}"

            # check for subheader intersection
            for idx, subheader in enumerate(subheaders):
              if fitz.Rect(word[:4]).intersects(fitz.Rect(subheader.coordinates)):
                word_dic['label'] = f"Subheader_{idx}"
            
            word_dic_list.append(word_dic)

        df_words = pd.DataFrame(word_dic_list)
        df_words['key'] = (df_words['label'] != df_words['label'].shift(1)).astype(int).cumsum()
        merged_df = df_words.groupby(['key', 'label', 'file', 'language'])['word'].apply(' '.join).reset_index(name="text")

        return pd.DataFrame(merged_df)

    def _get_page_language(self, page):
        """
        Method for detecting the language on a given page.

        Parameters
        ----------
        page : fitz.Page
            Pdf page read in through the fitz library.
        
        Returns
        -------
        str
            Language code for the detected language.
        """
        page_text = page.get_text('text')
        
        try:
            lang = detect(page_text)
        except:
            lang = 'No language detected!'
        
        return lang