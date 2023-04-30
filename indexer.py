import sys
import os
import json
import gzip

if __name__ == '__main__':
    # Read arguments from command line, or use sane defaults for IDE.
    argv_len = len(sys.argv)
    inputFile = sys.argv[1] if argv_len >= 2 else 'shakespeare-scenes.json.gz'
    queriesFile = sys.argv[2] if argv_len >= 3 else 'trainQueries.tsv'
    outputFolder = sys.argv[3] if argv_len >= 4 else 'results/'
    if not os.path.isdir(outputFolder):
        os.mkdir(outputFolder)
        


with gzip.open(inputFile,'rt',encoding='utf-8') as input:
        
    # index will be a map of the form Map<Term,List<Posting>>
    inverted_index = {}
    
    # dictionary read from the json file
    playDict = json.load(input)["corpus"]
    
    # iterate through every play to create the index
    for play in playDict:
        playId = play["playId"]
        sceneId = play["sceneId"]
        sceneNum = play["sceneNum"]
        text = play["text"]
        
        # split the text by spaces to get the terms
        terms = text.split()

        for i,term in enumerate(terms):
            
            # if first time term is seen create a list 
            if term not in inverted_index:
                inverted_index[term] = []
              
            # get the posting list
            posting_list = inverted_index.get(term)
            
            if len(posting_list) > 0 and posting_list[len(posting_list)-1][1] == sceneId:
                posting_list[len(posting_list)-1][3].append(i)
            
            else:
                posting = (playId,sceneId,sceneNum,[i])
                posting_list.append(posting)

    
with open(queriesFile,'rt',encoding='utf-8') as input:
    for line in input:
        lineParts = line.split("\t")
        
        queryName = lineParts[0]
        documentType = lineParts[1]
        queryBool = lineParts[2]
        terms = lineParts[3::]
        terms[len(terms)-1] = terms[len(terms)-1].replace("\n","")
        
        # result list of all scenes / plays that match the query
        result = []
        
        # remove any terms that do not exist in any document or end if "and" query
        terminate = False
        newTerms = []
        
        proceeding = {}
        proceedingWords = []
        
        for term in terms:
            subTerms = term.split()
            if len(subTerms) == 1:
                newTerms.append(subTerms[0])
            
            else:
                for subTerm in subTerms:
                    newTerms.append(subTerm)
                
                proceeding[subTerms[0]] = subTerms[1::]
                
                for t in subTerms[1::]: proceedingWords.append(t)
        
        terms = newTerms
        
        for term in terms:
            if term not in inverted_index:
                if queryBool.lower() == "and":
                    terminate = True
                else:
                    terms.remove(term)
                           
        if not terminate:
            # index based on the type of document 
            checkIndex = 0 if documentType == "play" else 1
            
            pointers = [0] * len(terms)
            
            # gets the index of the minimum pointer
            def minPtr():
                minI = 0
                min = 100000000000000000000
                
                for i,ptr in enumerate(pointers):
                    if inverted_index.get(terms[i])[ptr][2] < min:
                        min = inverted_index.get(terms[i])[ptr][2]
                        minI = i
                
                return minI
            
            def equal():
                documentId = inverted_index.get(terms[0])[pointers[0]][checkIndex]
                
                # return false if the document ID's do not match
                for i,term in enumerate(terms):
                    #print(term)
                    if inverted_index.get(term)[pointers[i]][checkIndex] != documentId:
                        return False
                    
                for i,term in enumerate(terms): 
                    #print(proceedingWords) 
                    if term in proceedingWords: continue
                                      
                    if term in proceeding:
                        proceedingTerms = proceeding[term]
                        termList = inverted_index.get(term)[pointers[i]][3]
                        valid = False
                        k = 0
                        
                        while not valid and k < len(termList):
                            index = termList[k]
                            j = 1
                            
                            while (j != len(proceedingTerms)+1 and j != -1):
                                proceedingList = inverted_index.get(proceedingTerms[j-1])[pointers[terms.index(proceedingTerms[j-1])]][3]
                                if index + j in proceedingList:
                                    j += 1
                                else:
                                    j = -1

                            if j == len(proceedingTerms)+1:
                                valid = True
                                
                            k += 1
                        
                        if not valid: return False    
                    
                return True
            
            def outOfBounds():
                for i,ptr in enumerate(pointers):
                    if ptr >= len(inverted_index.get(terms[i])):
                        return True
                    
                return False
            
            if queryBool.lower() == "and":
                # if a list runs out no more terms will fit the "and" boolean
                while not outOfBounds():
                    
                    # if all point to the same document then we add it
                    if equal():
                        # add the document to result
                        valueToAdd = inverted_index.get(terms[0])[pointers[0]][checkIndex]
                        
                        if len(result) == 0 or result[len(result)-1] != valueToAdd:
                            result.append(valueToAdd)
                        
                        # increment all pointers by 1
                        for i in range(len(pointers)): pointers[i] += 1
                    
                    # documents do not match
                    else:
                        # increment the minimum pointer
                        minIndex = minPtr()
                        pointers[minIndex] += 1
            
            elif queryBool.lower() == "or":
                for i,term in enumerate(terms):
                    termList = inverted_index.get(term)
                    
                    if term in proceedingWords: continue
                    
                    for posting in termList:
                        name = posting[checkIndex]
                        indices = posting[3]
                        
                        if term not in proceeding:
                            if len(result) == 0 or result[len(result)-1] != name:
                                result.append(name)
                        
                        else:
                            proceedingTerms = proceeding[term]
                            k = 0
                            
                            while k < len(indices):
                                index = indices[k]
                                j = 1
                                
                                while (j != len(proceedingTerms)+1 and j != -1):
                                    proceedingList = inverted_index.get(proceedingTerms[j-1])
                                    m = 0
                                    while proceedingList[m][checkIndex] != name: m += 1
                                    
                                    proceedingList = proceedingList[m][3]
                                    
                                    if index + j in proceedingList:
                                        j += 1
                                    else:
                                        j = -1

                                if j == len(proceedingTerms)+1:
                                    if len(result) == 0 or result[len(result)-1] != name:
                                        result.append(name)
                                        
                                k += 1
            
                result = [*set(result)]  
                result = sorted(result)
                        
            f = open(outputFolder + "/" + queryName + ".txt", "w")
            
            for document in result:
                f.write(document + "\n")
            
            f.close()

        else:
            print("empty result")