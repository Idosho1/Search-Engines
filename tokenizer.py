# import libraries
import re
import matplotlib.pyplot as plt

# regex to filter out punctuation other than . and ' that will be handeled separately 
punctuationRegex = '[^a-zA-Z0-9.\']'
vowels = ['a','e','i','o','u']

# list that will contain all the stopwords
stopwords = []

# parse stopwords.txt to extract the stopwords
with open ('stopwords.txt') as file:
    lines = file.readlines()
    for word in lines:
        stopwords.append(word.replace("\n",""))    

# close the file after parsing through it
file.close()

# take a word and if it has an abbreviation, separate it
def findAbbreviation(word):
    if word.find('.') != 1:
        return -1
    
    i = 0
    wordToAdd = ""
    nextDot = False
    while i < len(word):
        nextChar = word[i]
        i += 1
        if nextChar != '.':
            if nextDot:
                return i-2
            else:
                nextDot = True
                wordToAdd += nextChar
        else:
            nextDot = False

    return len(word)

# determine if a word is short
def shortWord(word):
    # remove leading cosonants
    i = 0
    while i < len(word) and word[i] not in vowels:
        i += 1
    word = word[i:]

    # remove trailing vowels
    i = len(word)-1
    while i >= 0 and word[i] in vowels:
        i -= 1
    word = word[:i+1]

    # count number of vowel cosonant parts (m)
    m = 0
    vowel = True
    for ch in word:
        if ch not in vowels:
            if vowel:
                vowel = False
        else:
            if not vowel:
                vowel = True
                m += 1

    if not vowel:
        m += 1

    return m == 1

# tokenize a single word
def tokenizeWord(word):
    result = []
    word = word.lower()
    word = word.replace("'","")

    # if it contains a period, find abbreviation or split accordingly
    if '.' in word:
        index = findAbbreviation(word)
        abbreviation = ""

        if index >= 0:
            abbreviation = word[0:index]
            word = word[index:]

        result.append(abbreviation.replace(".",""))

        dotSplit = word.split(".")

        for w in dotSplit:
            result.append(w)
    else:
        result.append(word)

    # return after splitting
    return list(filter(lambda x: len(x) != 0,result))


# tokenize a single line
def tokenizeLine(line):
    words = re.split(punctuationRegex,line) # split on punctuation
    result = []
    skip = 0

    for i in range(0,len(words)):
        word = words[i].lower()
        word = word.replace("'","")

        if skip > 0:
            skip -= 1
        else:
            # handles connecting mr. or ms. with name
            if word == "mr." or word == "ms." or word == "mrs.":
                if i+1 < len(words):
                    wordToAdd = tokenizeWord(words[i+1])
                    if len(wordToAdd) > 0:
                        result.append(word[0:-1] + wordToAdd[0])

                        for j in range(1,len(wordToAdd)):
                            result.append(wordToAdd[j])

                    skip += 1
                else:
                    result.append(word[0:-1])
            else:
                ws = tokenizeWord(word)
                for w in ws:
                    result.append(w)

    # returns the tokenized words after removing empty strings created by splitting
    return list(filter(lambda x: x != '',result))

# removes stopwords from a list of words
def removeStopwords(lst):
    return list(filter(lambda x: x not in stopwords,lst))

# returns the stem of a single word
def porterStemmer(word):
    # perform step 1a of the porter stemmer 
    
    # Replace sses by ss
    if word.endswith("sses"):
        word = word[0:len(word)-4:1] + "ss"

    # Replace ied or ies by i if preceded by more than one letter, otherwise by ie
    elif (word.endswith("ies") or word.endswith("ied")):
        if len(word) > 4:
            word = word[0:len(word)-2:1]
        else:
            word = word[0:len(word)-2:1] + 'e'

    # do nothing if ends with us or ss
    elif word.endswith("ss") or word.endswith("us"):
        word = word # do nothing
   
    # Delete s if the preceding word part contains a vowel not immediately before the s
    elif word.endswith("s"):
        found = False
        i = 0
        while not found and i < len(word)-2:
            if word[i] in vowels:
                word = word[0:len(word)-1:1]
                found = True
            i += 1
        
    # perform step 1b of the porter stemmer
    
    # Replace eed, eedly by ee if it is in the part of the word after the first non-vowel following a vowel
    if word.endswith("eed") or word.endswith("eedly"):
        firstVowelIndex = -1
        followingNonVowelIndex = -1
        
        for i in range(0,len(word)):
            if word[i] in vowels:
                firstVowelIndex = i
                break
        for i in range(firstVowelIndex,len(word)):
            if word[i] not in vowels:
                followingNonVowelIndex = i
                break
        
        if firstVowelIndex != -1 and followingNonVowelIndex > firstVowelIndex:
            if word.endswith("eedly") and followingNonVowelIndex < len(word)-5:
                word = word[0:len(word)-3:1]
            elif word.endswith("eed") and followingNonVowelIndex < len(word)-3:
                word = word[0:len(word)-1:1]
    
    # Delete ed, edly, ing, ingly if the preceding word part contains a vowel 
    else:
        removed = False
        
        if word.endswith("ingly") and any(word[i] in vowels for i in range(0,len(word)-5)):
            word = word[0:len(word)-5:1]
            removed = True
        elif word.endswith("edly") and any(word[i] in vowels for i in range(0,len(word)-4)):
            word = word[0:len(word)-4:1]
            removed = True
        elif word.endswith("ing") and any(word[i] in vowels for i in range(0,len(word)-3)):
            word = word[0:len(word)-3:1]
            removed = True
        elif word.endswith("ed") and any(word[i] in vowels for i in range(0,len(word)-2)):
            word = word[0:len(word)-2:1]
            removed = True
        
        # if we removed the suffix
        if removed:
            
            # if the word ends in at, bl, or iz add e
            if word.endswith("at") or word.endswith("bl") or word.endswith("iz"):
                word += 'e'
            
            # if the word ends with a double letter that is not ll, ss, or zz, remove the last letter 
            elif word[len(word)-1] == word[len(word)-2] and not (word.endswith("ll") or word.endswith("ss") or word.endswith("zz")):
                word = word[0:len(word)-1:1]
            
            # if the word is short, add e
            elif shortWord(word):
                word += 'e'
    
    return word

# tokenize, remove stop words, and stem the file
def parseFile(fileName):
    result = []
    
    with open (fileName) as file:
        lines = file.readlines()
        for line in lines:
            # Step 1) Tokenize
            tokenizedList = tokenizeLine(line)
            # Step 2) Remove Stopwords
            removedLine = removeStopwords(tokenizedList)
            # Step 3) Stem
            stemmedLine = list(map(lambda x: porterStemmer(x),removedLine))
            
            for w in stemmedLine:
                result.append(w)
                
    file.close()
    return result

# write every word in a list to a file
def writeToFile(lst,fileName):
    f = open(fileName, "w")
    for word in lst:
        f.write(word + "\n")
    f.close()


# determine the n top words in the file 
def topWords(fileName,n):
    wordMap = {}
    words = parseFile(fileName)
    for word in words:
        if wordMap.get(word) == None:
            wordMap[word] = 1
        else:
            wordMap[word] += 1
                
    lst = list(wordMap.items())
    lst.sort(key=lambda x: -x[1])
    lst = lst[0:n]
    
    return lst

# create a vocab growth plot for the file
def vocabGrowth(fileName):
    x = []
    y = []
    wordSet = set()
    data = []
    wordCount = 0
    uniqueCount = 0
    words = parseFile(fileName)
    for word in words:
        wordCount += 1
        if word not in wordSet:
            uniqueCount += 1
            wordSet.add(word)
        data.append((wordCount,uniqueCount))
        x.append(wordCount)
        y.append(uniqueCount)
            
    # plotting the points 
    plt.plot(x, y)
    plt.xlabel('Words in Collection')
    plt.ylabel('Words in Vocabulary')
    plt.title('Vocabulary Growth in Pride and Prejudice')
    plt.show()

    return data


# UNIT TESTS
assert(tokenizeWord("A.B.C.'s")[0] == "abcs")
assert(tokenizeWord("Ph.D.")[0] == "ph" and tokenizeWord("Ph.D.")[1] == "d")
assert(tokenizeWord("U.S.A.")[0] == "usa")
assert(tokenizeWord("www.google.com")[0] == "www" and tokenizeWord("www.google.com")[1] == "google" and tokenizeWord("www.google.com")[2] == "com")
assert(porterStemmer("stresses") == "stress")
assert(porterStemmer("gaps") == "gap")
assert(porterStemmer("gas") == "gas")
assert(porterStemmer("ties") == "tie")
assert(porterStemmer("cries") == "cri")
assert(porterStemmer("stress") == "stress")
assert(porterStemmer("agreed") == "agree")
assert(porterStemmer("feed") == "feed")
assert(porterStemmer("fished") == "fishe")
assert(porterStemmer("falling") == "falle")


# PART A
writeToFile(parseFile("tokenization-input-part-A.txt"),"tokenized-A.txt")

# PART B
writeToFile(list(map(lambda x: x[0] + " " + str(x[1]),topWords("tokenization-input-part-B.txt",300))),"terms-B.txt")

# VOCAB GROWTH PLOT
vocabGrowth("tokenization-input-part-B.txt")

