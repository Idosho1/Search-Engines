import sys
import json
import gzip
import math


if __name__ == '__main__':
        # Read arguments from command line, or use sane defaults for IDE.
        argv_len = len(sys.argv)
        inputFile = sys.argv[1] if argv_len >= 2 else 'shakespeare-scenes.json.gz'
        queriesFile = sys.argv[2] if argv_len >= 3 else 'trainQueries.tsv'
        outputFile = sys.argv[3] if argv_len >= 4 else 'trainQueries.results'


    # Something like...
    # index inputFile which is probably shakespeare-scenes.json.gz
    # for each query in queriesFile
    #     run it
    #     print results out to outputFile

with gzip.open(inputFile,'rt',encoding='utf-8') as input:
        
    # index will be a map of the form Map<Term,List<Posting>>
    inverted_index = {}
    play_index = {}

    # other variables we want to know
    totalTerms = 0
    terms_dict = {}
    scenes = {}
    plays = {}
    
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

        totalTerms += len(terms)

        scenes[sceneId] = len(terms)

        if playId in plays:
            plays[playId] += len(terms)
        
        else:
            plays[playId] = len(terms)

        for term in terms:
            # if first time term is seen create a list 
            if term not in inverted_index:
                inverted_index[term] = []

            if term not in play_index:
                play_index[term] = {}
                
            if term not in terms_dict:
                terms_dict[term] = 1
            else:
                terms_dict[term] += 1
            
            term_counts = play_index.get(term)

            if playId not in term_counts:
                term_counts[playId] = 1
            
            else:
                term_counts[playId] += 1
              
            # get the posting list
            posting_list = inverted_index.get(term)
            
            if len(posting_list) > 0 and posting_list[len(posting_list)-1][1] == sceneId:
                list_tuple = list(posting_list[len(posting_list)-1])
                list_tuple[3] += 1
                posting_list[len(posting_list)-1] = tuple(list_tuple)
            
            else:
                posting = (playId,sceneId,sceneNum,1)
                posting_list.append(posting)
    
    numScenes = len(scenes) # N for scenes
    numPlays = len(plays) # N for plays

    avgSceneLength = totalTerms / numScenes # avdl for scenes
    avgPlayLength = totalTerms / numPlays # avdl for plays
    
with open(queriesFile,'rt',encoding='utf-8') as input:
    
    # clear file
    f = open(outputFile, "w")
    f.close()

    for line in input:

        lineParts = line.split("\t")

        queryName = lineParts[0]
        documentType = lineParts[1]
        rankingType = lineParts[2]

        terms = lineParts[3::]
        terms[len(terms)-1] = terms[len(terms)-1].replace("\n","")

        if documentType == "scene":
            N = numScenes
            avdl = avgSceneLength

        elif documentType == "play":
            N = numPlays
            avdl = avgPlayLength
        
        # all terms and counts in query
        termsDict = {}

        # documents to be scored
        scores = {}
        
        # get set of terms and frequencies from query
        for term in terms:
            if term in termsDict:
                termsDict[term] += 1
            else:
                termsDict[term] = 1
        
        # keep track of which terms were already scored for plays
        play_rankings = {}

        # calculate score for BM25
        if rankingType == "bm25":
            
            # constants for BM25
            k_1 = 1.8
            k_2 = 5
            b = 0.75

            # iterate through each term in the query
            for i,qf_i in termsDict.items():

                # define n_i for scene or play
                if documentType == "scene":
                    n_i = len(inverted_index.get(i))
                
                elif documentType == "play":
                    n_i = len(play_index.get(i))

                # get posting list
                postings = inverted_index.get(i)

                # iterate through the postings
                for playId,sceneId,sceneNum,count in postings:
                    
                    # make sure to not double count plays
                    if documentType == "play":
                        if playId not in play_rankings:
                            play_rankings[playId] = set()
                            play_rankings[playId].add(i)
                        else:
                            if i not in play_rankings[playId]:
                                play_rankings[playId].add(i)
                            else:
                                continue

                    # id for document depending on type
                    id = (playId if documentType == "play" else sceneId)

                    # initialize variables
                    if documentType == "scene":
                        dl = scenes[sceneId]
                        f_i = count
                    
                    elif documentType == "play":
                        dl = plays[playId]
                        f_i = play_index.get(i).get(id)

                    # define K
                    K = k_1 * ((1 - b) + b * (dl/avdl))

                    # initialize document score if not defined
                    if id not in scores:
                        scores[id] = 0
                    
                    # add up score for term
                    factor1 = math.log(1/((n_i + 0.5)/(N - n_i + 0.5)))

                    factor2 = ((k_1 + 1) * f_i)/(K + f_i)

                    factor3 = ((k_2 + 1) * qf_i)/(k_2 + qf_i)

                    scores[id] += factor1 * factor2 * factor3
        
        # calculate score for QL
        elif rankingType == "ql":
            
            # keep track of documents scored to account for missing terms
            documents_updated = {}

            score_list = []
            
            # constants for ql
            mu = 250
            C = totalTerms

            # iterate through the query terms
            for ind,i in enumerate(terms):
                
                # constants
                c_qi = terms_dict[i]
                score_list.append(mu * (c_qi/C)) # score before dividing by |D| + mu
                
                # get posting list
                postings = inverted_index.get(i)

                # iterate through the postings
                for playId,sceneId,sceneNum,count in postings:
                    
                    # id for document depending on type
                    id = (playId if documentType == "play" else sceneId)

                    # make sure to not double count plays
                    # update which terms were scored in each document
                    if id not in documents_updated:
                        documents_updated[id] = [0] * len(terms)
                        documents_updated[id][ind] = 1
                    else:
                        if documents_updated[id][ind] == 1:
                            continue
                        else:
                            documents_updated[id][ind] = 1
                    
                    # set constants for QL
                    if documentType == "scene":
                        D = scenes[id]
                        f_qiD = count

                    elif documentType == "play":
                        D = plays[id]
                        f_qiD = play_index.get(i).get(id)
                    
                    # initialize document score if not defined
                    if id not in scores:
                        scores[id] = 0
                    
                    # add up partial score for term
                    scores[id] += math.log((f_qiD + mu * (c_qi/C))/(D + mu))
            
            # add scores for terms that do not appear
            for docId,arr in documents_updated.items():
                
                # add up the partial scores for missing terms
                if documentType == "scene":
                    D = scenes[docId]
                elif documentType == "play":
                    D = plays[docId]

                # to be or not to be
                for i,bit in enumerate(arr):
                    if bit == 0:
                        score = score_list[i]/(D + mu)
                        scores[docId] += math.log(score)
                
        # sort scores and keep top 100
        list_scores = list(scores.items())
        sorted_scores = sorted(list_scores, key=lambda tup: -tup[1])[0:100]
        
        # write ranked lists to file
        f = open(outputFile, "a")
        
        for i,(document,score) in enumerate(sorted_scores):
            f.write(queryName + " skip " + document + " " + str(i+1) + " " + str(format(score, '.6f')) + " ido\n")
            
        f.close()