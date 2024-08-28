import numpy as np
import pandas as pd
import re
import os
from bs4 import BeautifulSoup

import functions.figureFunctions as figureFunctions

GLOBAL_COLUMNS = ['Description', 'Collection', 'Height', 'Photo Credits'] # Photo Source Individual olabilir Article 6
# helper function cleantextden parantezleri cikar article 6 ya bak

def figureInfo2MultiIndex(figure_info: dict[str, list], figure_id: int) -> list[tuple]:
    '''
    Returns list of tuples of figure_id and keys in the figure_info dictionary
    Used as indexes in excel sheets
    '''
    return [(figure_id, key) for key in figure_info.keys()]


def text2Index(text: str) -> int:
    '''
    Returns the predicted type of given data based on:
    0: Description - predicted to start and end with space and consist of letters
    2: Height - always int|float mm|cm
    1: Collection - as there are many different ways, if data does not fit above
    criteria, it is collection
    '''
    description_match = re.match('^\s[^0-9]*\s$', text) # ARTICLE 6
    if not description_match:
        description_match = re.match('(\s)?Herbarium specimen .*', text)
    if description_match:
        return 0 # Index of Description
    
    height_match = re.match('[0-9]+(\.)?[0-9]* [cm]m', text)
    if height_match:
        return 2 # Index of Height
    
    return 1 # Index of Collection

# TODO: Do not forget to make sure article_6 are passed correctly
def figureInfo2NumpyArray(figure_info: dict[str, list], photo_source: list, general_data: list, do_special_processing: bool = False):
    '''
    Returns general_data, figure_info, photo_source as a single numpy inorder array of shape
    (len(figure_info), 8) to be used as data in upcoming dataFrames 
    '''
    length = 4 # Specific Data Column Count
    result_array = np.zeros((len(figure_info), length), dtype='<U511')
    
    if do_special_processing:
        figure_info = fixArticle6(figure_info, photo_source)
    
    # Both for non-standart article format that causes overwrites
    overwritten_text = ''
    lengths_for_error = []
    
    # Simplify the addition of photo_source: list[str]|[]
    photo_source = photo_source[0] if photo_source else ''
    
    general_datas = []
    
    for i, key in enumerate(sorted(figure_info)):
        attributes = figure_info[key]
        
        # Static through the for loop, matches the shape of result array
        general_datas.append(general_data)    
        
        # Only for Atricle 6 where photo_source is independent
        if do_special_processing and not photo_source:
            result_array[i] = [attributes[0], # Description
                               attributes[1], # Collection
                               '',            # Article 6 does not have height data
                               attributes[2]  # Photo Source
                               ]
            continue
        # attributes is empty
        if len(attributes) == 0:
            result_array[i] == [''] * length
            
            lengths_for_error.append(0)
        # attributes has 1 element --> either collection or description
        elif len(attributes) == 1:
            text = attributes[0]
            j = text2Index(text)
            result_array[i] = [text if j == idx else '' for idx in range(length)]
            
            lengths_for_error.append(1)
            
        elif len(attributes) == 2:
            # none_idx can be 0,1 or 2, as length is 4
            # none_idx is initially 3
            none_idx = length - 1 
            for text in attributes:
                
                j = text2Index(text)
                result_array[i, j] = text
                
                # if j was 0,1 -> 3-1-0=2
                # (0,2) -> 3-0-2=1
                # (1,2) -> 3-1-2=0
                none_idx -= j
            
            # As there are only indexes [0,1,2], none_idx will be the one
            # that wasnt <<j>> at the loop
            result_array[i, none_idx] = ''

            lengths_for_error.append(2)
            
        elif len(attributes) == 3:
            for text in attributes:
                j = text2Index(text)
                
                if result_array[i, j] == '':
                    result_array[i, j] = text
                else:
                    overwritten_text = text
            
            lengths_for_error.append(3)
        
        result_array[i, -1] = photo_source
    

    # Fixing length errors: due to typos, sometimes an data column is missing
    # from one label and excessive in another label. This can only happen
    # when normal data points read are length 2, and the label that misses the data 
    # is length 1 and the excessive if length 3.
    if 3 in lengths_for_error and 1 in lengths_for_error:
        idx_1 = lengths_for_error.index(1)
        
        # Move overwritten_text to label with current length 1
        result_array[idx_1, 1] = overwritten_text
    
    return np.concatenate((general_datas, result_array), axis=1)

def multipleRegex2Span(patterns: list, text: str) -> (int, int):
    '''
    Regex for multiple regex patterns in a text.
    Returns the first one based on the order of patterns.
    If no match is found, return (0, 0) for result to fail
    any(result) bool check.
    '''
    for pattern in patterns:
        if search := re.search(pattern, text):
            return search.span()
    
    return (0, 0)

def fixArticle6(_figure_info: dict[str, list], photo_source: list) -> dict[str, list]:
    '''
    In particular, Article 6 is very differently formatted than the other articles.
    The function fixes this problem and returns it to standart.
    '''
    if any([key == 'ALL' for key in _figure_info.keys()]):
        return _figure_info
    
    # The first data column, Description contains Description and collection info
    # due to non-standart article formatting
    
    # Indentifier for the split: <<Name>> <<Number>>|[Number], 'field photograph' <<Name>> et al. ,
    # ''photograph', <<Name>> <<CAPITAL>>-<<Number>> <<Name>> s.n. 
    patterns = [
                '([A-Z][a-zêô]+)+ \[?[0-9]+\]?.*', # '<<Names>> <[Number]>...'
                'field photograph.*', # 'field photograph ...'
                '([A-Z][a-zêô]+)+ et al\..*', # <<Names>> et al. ...'
                'photograph.*', # photograph ...
                '[A-Z][a-z]+ [A-Z]+-[0-9]+.*', # <<Name>> <<CAPITAL>>-<<Number>>
                '[A-Z][a-zé]+ s\.n\..*', # <<Name>> s.n.
                ]
    
    figure_info = _figure_info.copy()
    for key in figure_info:

        attribute_error = figure_info[key][0]
        span = multipleRegex2Span(patterns, attribute_error)

        # Error checking for debugging
        if not any(span):
            # TODO: disable comments and check these
            # print('errrror')
            # print(attribute_error, figure_info)
            return figure_info

        _match = attribute_error[span[0]:span[1]]

        # Update dictionary
        val = figure_info.get(key)
        val[0] = attribute_error.replace(_match, '')
        val.insert(1, _match)
        figure_info[key] = val
    
    return figure_info

def segmentOnRow(row, idx, do_special_processing: bool) -> (np.ndarray, list[tuple]):
    '''
    Gets row of general data and caption text as input
    and returns the general data and segmented caption text
    correct order. Does special processing if flagged.
    '''
    # Columns are Label, Taxon Name, Description, Url, Figure Object
    figure_text = row['Figure Object']
    figure = BeautifulSoup(figure_text, 'xml')
    
    taxon_name = row['Taxon Name']
    
    figure_dict, photo_source = figureFunctions.getSegmentedText(figure, taxon_name)
    general_data = [row.Label, \
                    taxon_name, \
                    row.Description, \
                    figureFunctions.getCaptionText(figure), \
                    row.Url]
    
    specific_arr = figureInfo2NumpyArray(figure_dict, photo_source, general_data, do_special_processing = do_special_processing)
    
    multi_index = figureInfo2MultiIndex(figure_dict, idx+1)
    
    return specific_arr, multi_index    
    
def figures2DataFrame(figures: list):
    '''
    Returns a DataFrame created from a list of figures with 8 columns
    given below and multi-index of level 2.
    '''
    multi_indexes = []
    
    # Description, Collection, Height, Photo Credit/Source
    specific_data = []
    


   
    for i, figure in enumerate(figures):
        figure_dict, photo_source = figureFunctions.getSegmentedText(figure)
        
        # Label, Taxon Name, Description, Caption Text, Link
        general_data = [figureFunctions.getLabel(figure),\
                        figureFunctions.getTaxonName(figure),\
                        figureFunctions.getDescription(figure),\
                        figureFunctions.getCaptionText(figure),\
                        figureFunctions.getUrl(figure),\
                        ]
        
        # Array of Description, Collection, Height, Photo Credit/Source
        specific_arr = figureInfo2NumpyArray(figure_dict, photo_source, general_data, article_id=i+1)
        specific_data.append(specific_arr)
        
        
        multi_index = figureInfo2MultiIndex(figure_dict, i+1)
        multi_indexes.append(multi_index)
    # TODO: Suan specific data da 1A 1B ama general data 1, 2, 3
    all_data = np.concatenate((specific_data), axis=0)
    
    multi_indexes = np.concatenate(multi_indexes, axis=0)

    index = pd.MultiIndex.from_arrays(multi_indexes.T, names=['Figure ID', 'Segment'])
    
    columns = ['Label', 'Taxon Name', 'General Description', 'Caption Text','Url',\
               'Specific Description', 'Collection', 'Height', 'Photo Credit']

    df = pd.DataFrame(data=all_data, index=index, columns=columns)
    return df

def df2Excel(figures: list, output_file: str, file_name: str) -> None:
    '''
    Writes figures into properly formatted excel file with
    file_name output_file\plant-data.xlsx
    '''
    if not figures:
        return
    df = figures2DataFrame(figures)
    path = os.path.join(output_file, file_name)
    
    df.to_excel(path, index=True)
    return
