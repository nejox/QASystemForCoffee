from Code.Preprocessor.preprocessor import Preprocessor
import json
import Code.Clients.client_factory as factory


if __name__ == '__main__':
        
    # instantiate preprocessor
    pp = Preprocessor(mode=1, output_path='output_preprocessing/', model_path='models/visual', verbose='DEBUG')
    output = pp.process('PATH TO MANUALS')
    
    # save json output to file
    factory.get_file_client().save_as_file(file_path='output_preprocessing/',
                                           filename='corpus.json',
                                           content=output)

 #   with open('output_preprocessing/corpus.json', 'w') as fp:
 #       json.dump(output, fp, indent=2)