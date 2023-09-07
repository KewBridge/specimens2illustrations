def returnAllOcurrances(char: chr, text: str) -> list:
    return [i for i, ch in enumerate(text) if ch == char]
    
def customCount(char: str, lst: list) -> int:
    return sum([1 for text in lst if char in letter2CorrectList(text)])

def hyphon2Comma(text: str, hyphonText: str = '–') -> str:
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
    return comma2List(hyphon2Comma(text, hyphonText=hyphonText))

def copyTexts(letters: list, texts: list):
    resultLetters = []
    resultTexts = []
    
    for letter, text in zip(letters, texts):
        correctFormattedLetter = letter2CorrectList(letter)
        
        for _letter in correctFormattedLetter:
            resultLetters.append(_letter)
            resultTexts.append(text)
    
    return resultLetters, resultTexts
