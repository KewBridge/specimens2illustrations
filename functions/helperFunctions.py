import re

def splitTextFromList(text: str, lst: list[str], indexes: list[int] = None) -> str:
    '''
    Python split() but can take list as input to what to split.
    Optional indexes are a list of integer that the function
    keeps after splitting.
    By default, only the last part is kept.
    
    Keyword arguments:
    text -- string to be splitted
    lst -- list of string splitters
    indexes -- list of indexes to decide 
    what index of string to keep after 
    splitting (default None)
    '''
    if indexes is None:
        indexes = [-1 for _ in lst]
        
    for _text, idx in zip(lst, indexes):
        text = text.split(_text)[idx]
    
    return text

def returnAllOcurrances(char: chr, text: str) -> list:
    '''text.find(char) but returns all indexes where char is in text'''
    return [i for i, ch in enumerate(text) if ch == char]
    
def customLoopCount(char: str, lst: list) -> int:
    '''
    Returns the count of all occurances of char letter in list
    'B' in 'A-E' will count as an occurance.
    '''
    return sum([1 for text in lst if char in letter2CorrectList(text)])

def correctList(lst: list) -> list:
    '''
    Converts all strings accordingly:
    'A-C' to ['A', 'B', 'C']
    'A, C' to ['A', 'C']
    '''
    new_lst = []
    for text in lst:
        new_lst += letter2CorrectList(text)
    
    return new_lst
    
def customLetterCount(lst: list) -> int:
    '''
    Returns the unique letter count in an correct list
    As the project is segmentation, labels do not have gaps
    so if G is the last letter of a sorted letter array
    'G' (71) - 'A' (65) + 1 = 7 returns this value
    G is the 7th letter of the alphabet
    '''
    new_lst = correctList(lst)
    return ord(sorted(new_lst)[-1]) - ord('A') + 1


def hyphon2Comma(text: str, hyphonText: str = '–') -> str:
    '''
    Converts "A-C" to "A, B, C" 
    hyphonText differentiates between '–' and '-'
    '''
    if len(text) == 1:
        return text
    
    hyphons = returnAllOcurrances(hyphonText, text)

    for idx in hyphons:
        previousLetter = text[idx - 1]
        nextLetter = text[idx + 1]
        newText = (', '.join([chr(c) \
                                for c in range(ord(str.upper(previousLetter)), \
                                               ord(str.upper(nextLetter))+1)]))
        
        oldText = hyphonText.join((previousLetter, nextLetter))
        text = text.replace(oldText, newText)
         
    return text

def comma2List(text: str) -> list:
    return text.split(', ')

def letter2CorrectList(text: str, hyphonText: str = '–') -> list:
    '''Converts a list of strings based on above-mentioned rules'''
    return comma2List(hyphon2Comma(text, hyphonText=hyphonText))

def cleanText(text: str, text2Cleaned: list) -> str:
    '''Removes all the strings in text2cleaned from text'''
    for _text in text2Cleaned:
        text = text.replace(_text, '')
    return text

def fixNonStandartLabels(letters, texts):
    '''
    Due to non-standart article part, sometimes a label is not bold.
    This causes the text for the previous label to contain correct-itself,
    bold label(s) and incorrect label's text. This function fixes this problem.
    '''
    resultLetters = []
    resultTexts = []
    
    
    # Fixes non-standart usage of hyphons
    _texts = []
    saved_index = -1
    for i, text in enumerate(texts):
        max_letter = chr(ord(max(letters)[0]) + 1)
        misplacedTexts = re.findall("[A-Za-z]-[A-Za-z]\s", text)
        if not misplacedTexts:
            misplacedTexts = re.findall(f'[A-{max_letter}],*\s', text)
        
        
        
        # print(misplacedTexts)
        if misplacedTexts:        
            for misplacedLetter in misplacedTexts:
                saved_index = i
                _misplacedTexts = text.split(' ' + misplacedLetter)
                if _misplacedTexts[0] == '':
                    _misplacedTexts[0] = _misplacedTexts[1]
                misplacedLetter.replace(',', '')
                # print(misplacedLetter, _misplacedTexts)
                letters.insert(saved_index + 1, str.upper(misplacedLetter.replace(' ', '')
                                                          .replace(',', '')))
                
                for _misplacedText in _misplacedTexts:
                    _texts.append(_misplacedText)
    
    if saved_index != -1:
        texts = texts[:saved_index] + _texts + texts[saved_index + 1:]

    for text, letter in zip(texts, letters):
        text = cleanText(text, ['). Scale bar: ', ' = ', '; ', ')', '('])
        if ',' in letter:
            _letters = letter.split(', ')
            
            for _letter in _letters:
                resultLetters.append(_letter)
                resultTexts.append(text)
                
        else:
            resultLetters.append(letter)
            resultTexts.append(text)

    # print(resultLetters, resultTexts)
    return resultLetters, resultTexts
           
def insert2Dict(dct, key, val):
    '''
    Insert val to dct[key] but dct[key] is a list
    Example:
        {'a':[1]} -> insert2Dict(dct, 'a', 2)
        -> {'a': [1,2]}
    '''
    if valArray := dct.get(key, 0):
        valArray.append(val)
        dct[key] = valArray
        return
    
    dct[key] = [val]
    return

def standartdizeFigureInfo(letters, texts):
    '''
    letters and texts match 1-1. Preserves this ability
    through changing 'A-C' in letters to 'A', 'B', 'C'
    by copying the 'A-C' corresponding text thrice in place
    '''
    letters, texts = fixNonStandartLabels(letters, texts)
    figureInfo = {}
    
    for idx, (letter, text) in enumerate(zip(letters, texts)):
        
        text = text.replace(' drawn from ', '') \
            .replace(' (Based on:', '').replace(' (based on:', '')
        if len(letter) == 1:
            
            insert2Dict(figureInfo, letter, text)
            # figureInfo[letter] = text
        else:
            
            hyphonIdx = max(letter.find('-'), letter.find('–'))
            
            if hyphonIdx != -1:
                
                startLetter = letter[hyphonIdx - 1]
                endLetter = letter[hyphonIdx + 1]
                
                for _letter in range(ord(startLetter), ord(endLetter) + 1):
                    insert2Dict(figureInfo, chr(_letter), text)
                    # figureInfo[chr(_letter)] = text
    
    return figureInfo    
