'''
This script is collection of functions applied to the figure xml-object.
There are functions to get various elements and, with the help of 
standartizeFigureInfo from helperFunctions.py, creates a dictionary for
each figure, with its labels (Bold Letters from A to variable) as key and
the description, collection and height data as value.

Author: Eren Karabey
'''


import re
import sys
from helperFunctions import customLetterCount, customLoopCount, standartdizeFigureInfo

def figureSegmentation(figures: list) -> dict:
    '''
    Given a list of figures, categorize them based on their parent
    object`s title.'
    '''
    new_dict = {}
    
    for figure in figures:
        key = figure.parent.title.replace('.', '')
        
        get_title = new_dict.get(key, [])
        get_title.append(figure)
        
        new_dict[key] = get_title
    
    return new_dict

def getDescription(figure):
    '''Returns the description text for the figure from its parent object'''
    description = ' '.join([e.text for e in figure.parent.find('p').contents])      
    return description

def getTaxonName(figure):
    '''Returns the taxon name of the plant illustrated in the figure'''
    taxon_name = figure.parent.parent.find('tp:nomenclature')
    taxon_name_texts = taxon_name.find('tp:taxon-name').find_all('tp:taxon-name-part')
    return ' '.join([txt.text for txt in taxon_name_texts])

def getLabel(figure) -> str:
    '''
    Returns the label of the figure.
    Example: out: Figure 1
    '''
    return figure.label.text.replace('.', '')

def getCaptionText(figure) -> str:
    '''Returns the caption text of the figure'''
    return ' '.join([content.text for content in figure.caption.p.contents])

def getUrl(figure) -> str:
    '''Returns the url of the figure'''
    return figure.uri.text

def getLetterCount(figure) -> int:
    '''
    Returns the bold letter count of the figure.
    This is equavilent to how many segments an illustration os divided into.
    If there are no bold labels, the illustration has only one segment.
    '''
    bolds = figure.find_all('bold')
    
    if not bolds:
        return 1
    
    return customLetterCount([bold.text for bold in bolds])

def getLoopBoldCount(figure) -> int:
    '''Returns how many times the bold labels loop in a caption of the figure.'''
    bolds = figure.find_all('bold')
    
    if not bolds:
        return 0
    
    return customLoopCount('A', [bold.text for bold in bolds])

def getSegmentedText(figure) -> (dict, list):
    '''
    Returns a dictionary/map of [BOLD_LETTER] -> [Attributes]
    if there are no BOLD_LETTERS, returns dictionary of 
    ['ALL'] -> [Attributes]
    as well as a the Photo Source - always one for each figure
    '''
    if figure is None:
        return {}, []
    
    bolds = [bold.text for bold in figure.find_all('bold')]
    if len(bolds) < 1:
        no_bold_list = getTextFromNoBold(figure)
        if len(no_bold_list) == 1:
            end_line = getEndLineCondition(figure)
            return {'ALL': [no_bold_list[0]]}, [figure.p.text.split(end_line, 1)[-1]]
        if '©' in figure.p.text and '©' not in no_bold_list[-1]:
            return {'ALL': no_bold_list}, [figure.p.text.split('©')[-1]]
        return {'ALL': no_bold_list[:-1]}, [no_bold_list[-1]]

        
    texts = []
    current_text = ''
    add_to_text = False
    is_end_text = False
    general_to_text = False
    first_time_after_end = False
    end_line = getEndLineCondition(figure)
    
    generalTexts = []
    do_not_add = False
    # A system to go from 'A <<text1A>> B <<text1B>> A <<text2A>> B <<text2B>>' 
    # to {A: [text1A, text2A], B: [text1B, text2B]} 
    for line in figure.p.strings:
        
        # Error in xml
        if line in getTaxonName(figure):
            # print(line)
            continue
        
        # Check condition for differently labeled heaight data
        # There are two different labeling of height data
        # The first one is consistent with rest of the format
        # i.e. [BOLD LETTER] [DATA] repeat
        # The following code checks for the other format
        # i. e. [DATA] ([BOLD_LETTER])
        if line.find('Scale bars: ') > -1:
            texts.append(current_text)
            new_text = line.split('Scale bars: ', 1)[-1]
            texts.append(new_text)
            do_not_add = True
            current_text = ''
            continue
        
        # Check condition for differently labeled height data 2
        if line.find('Scale bar:') > -1:
            # Only continue if the format is similar to previous condition's format
            if not re.findall('[A-Z] = [0-9] [cm]m', figure.p.text):
                texts.append(current_text)
                new_text = line.split('Scale bar: ', 1)[-1]
                texts.append(new_text)
                do_not_add = True
                current_text = ''
                continue
        
        if line.find(end_line) > -1:
            is_end_text = True
            add_to_text = False
            if do_not_add:
                current_text = line.split(end_line, 1)[-1]
                break
            current_text += line.split(end_line, 1)[0]
            texts.append(current_text) 
            
            current_text = line.split(end_line, 1)[-1]
            first_time_after_end = True
            continue
        
        if line in bolds:
            if is_end_text:
                general_to_text = True
                if first_time_after_end:
                    first_time_after_end = False
                    current_text = ''
                else:
                    texts.append(current_text)
                    current_text = ''
                continue
            
            add_to_text = True
            if current_text == '':
                continue
            texts.append(current_text)
            current_text = ''
            
            continue
        
        if add_to_text:
            current_text += line
        
        if is_end_text:
            current_text += line
    
    if add_to_text or general_to_text:
        texts.append(current_text)
    else:
        generalTexts.append(current_text)
    return standartdizeFigureInfo(bolds, texts), generalTexts

def getTextFromNoBold(figure) -> list:
    '''Returns the data if figure is not segmented into multiple parts'''
    # No first letter to ignore capitilaziton
    if 'erbarium specimen' in figure.p.text:
        result = []
        for text in splitIgnoreCapital(figure.p.text, '. '):
            if getTaxonName(figure) in text and '–' not in text:
                continue
            
            if 'erbarium specimen' in text:
                if '–' in text:
                    text = text.split('–', 1)[-1]
                result.append(text)
            elif 'hotograph credit' in text:
                result.append(text.split(': ', 1)[-1])
                
        patterns = [re.compile('[A-ZØ][a-zñ]+ & [A-Z][a-zñ]+ [0-9]+'),
                    re.compile('[A-Z][a-zñ]+ [0-9]+'),
                    re.compile('\([A-Z].*et al.*\)'),
                    re.compile('[A-Z][a-zñ]+ et al.*\)'),
                    re.compile('[A-Z][a-zñ]+ s.n.'), 
                    ]
        collection = getSingleRegexMatch(figure.p.text, patterns)
        if collection:
            result = [txt.split(collection[0])[0] for txt in result]
            result.insert(1, collection[0])
            
        if not result:
            return re.findall('[A-Z][a-z]+ [A-Z]+-[0-9]+', figure.p.text)
        return result
    
    patterns = [\
                re.compile('[A-Z][.] [A-Z][a-z]+ [0-9]+'), \
                re.compile('[A-Z][a-z]+ & [A-Z][a-z]+ [0-9]+'), \
                re.compile('[A-Z][a-z]+ [0-9]+') \
                ]
    collection = getSingleRegexMatch(figure.p.text, patterns)
    
    if collection:
        return collection
    
    if 'drawn from ' in figure.p.text:
        for text in figure.p.text.split('.'):
            if 'drawn from ' in text:
                return [text.replace('drawn from ', '')]
            
    return []


def splitIgnoreCapital(text: str, sep: str) -> list:
    '''
    Returns text.split(sep) but does not split if last char of 
    the split is captial letter
    '''
    result = []
    current_text = ''
    
    # Standart split algorithm
    while text != '':
        index = text.find(sep)
        
        # If last letter of the text is the first occurance of sep in string, break
        if text.find(sep.strip(' ')) == len(text) - 1:
            result.append(text)
            break
        
        before_index_text = text[:index]
        # Conditions to not seperate text
        if len(before_index_text) == 1 or \
            ord(before_index_text[-1]) in range(ord('A'), ord('Z') + 1) or \
                'acc' in before_index_text:
            current_text += before_index_text + '.'
        
        # Further condition to not seperate text, as len(before_index_test) != 1
        elif before_index_text[-2] == ' ':
            current_text += before_index_text + '.'
            
        else:
            if current_text != '':
                result.append(current_text)
                current_text = ''
            else:
                result.append(before_index_text)
        
        # Update text to be itself after the first occurance of sep, without sep
        text = text[index+len(sep):]
        
    return result
            
def getEndLineCondition(figure) -> str:
    '''
    Returns the possible end line for given figure
    These are found and ordered via manual checking.
    If none exist in the figure, return <<PLACEHOLDER>>.
    '''
    possibleEndLines = ['Photograph credits: ','permission of ', 'Drawn by ', 'Drawn By ', 
                        'Adapted from ', 'Reproduced from ', 
                        'Illustration by ', 'Drawing by ',
                        'Courtesy of ', 'Photos By ', 'Photos by']
    
    # Arbitrary string as placeholder - does not occur in any figure
    end_line = 'PLACEHOLDER'
    for _end_line in possibleEndLines:
        if _end_line in figure.p.text:
            end_line = _end_line
    return end_line

def getSingleRegexMatch(text: str, regexs: list) -> list:
    '''
    Matches text to all the regex patterns in <<regexs>>
    Returns the first occurance as list
    '''
    for pattern in regexs:
        result = re.findall(pattern, text)
        if result:
            return result
    return []
    
    

    
