import unittest
import json
import manual_scraper
import os
import utils

class TestScraper(unittest.TestCase):

    def setUp(self):
        utils.init_global_config("C:/Users/Jochen/MAI_NLP_PROJECT/Code/config/config.json")

    def test_scraper(self):
        sut = manual_scraper.ManualScraper()

        with open("C:/Users/Jochen/MAI_NLP_PROJECT/Code/ManualScraper/manual_sources/delonghi.json", "r") as file:
            source = json.load(file)
        source["paths"] = ["de-de/manuals/produkte/kaffee/moka/c/moka"]
        
        sut.scrape(source)

        self.assertTrue(os.path.isdir("./Delonghi/emkm6b_alicia_plus_moka_kaffeemaschine"))

        fileCount = 0
        for _, dirnames, filenames in os.walk('./Delonghi/emkm6b_alicia_plus_moka_kaffeemaschine'):
            fileCount += len(filenames)
            for file in filenames:
                os.remove('./Delonghi/emkm6b_alicia_plus_moka_kaffeemaschine/'+file)

        os.rmdir('./Delonghi/emkm6b_alicia_plus_moka_kaffeemaschine')
        os.rmdir('./Delonghi')

        self.assertEqual(22, fileCount) # counted from https://www.delonghi.com/de-de/manuals/emkm6-b-alicia-plus-moka-kaffeemaschine/p/EMKM6.B
        self.assertFalse(os.path.isdir("./Delonghi/emkm6b_alicia_plus_moka_kaffeemaschine"))

if __name__ == '__main__':
    unittest.main()
