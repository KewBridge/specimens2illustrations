import pandas as pd
from bs4 import BeautifulSoup
import numpy as np

import argparse

import sys
sys.path.append('./functions/pandasFunctions')
from functions.pandasFunctions import segmentOnRow

def main(inputfile, outputfile, do_special_processing = False):
    df = pd.read_csv(inputfile, delimiter = '\t', header = 0, encoding = 'utf-8')

    multi_indexes = []
    all_data = []
    
    for i in range(df.shape[0]):
        row = df.iloc[i]
        
        data, multi_index = segmentOnRow(row, i, do_special_processing)
        print(data)
        all_data.append(data)
        multi_indexes.append(multi_index)
    
    all_data = np.concatenate((all_data), axis=0)
    
    multi_indexes = np.concatenate(multi_indexes, axis=0)

    index = pd.MultiIndex.from_arrays(multi_indexes.T, names=['Figure ID', 'Segment'])
    
    columns = ['Label', 'Taxon Name', 'General Description', 'Caption Text','Url',\
               'Specific Description', 'Collection', 'Height', 'Photo Credit']

    new_df = pd.DataFrame(data=all_data, index=index, columns=columns)
        
    count_per_row = new_df.groupby(level=0, sort=False).size().values
    
    new_df.to_csv(outputfile, header=True, encoding='utf-8')
    
    print('Parsing captions in {} saving parsed caption data to {}'.format(inputfile, outputfile))

if __name__ == "__main__":
    
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Process captions.")

    # Add the command-line arguments
    parser.add_argument("input_file", help="Path to the input txt file")
    parser.add_argument("output_file", help="Path to the output captions file")
    parser.add_argument("--do_special_processing", default=False, action='store_true')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Call the main function with the provided arguments
    main(args.input_file, args.output_file, args.do_special_processing)
