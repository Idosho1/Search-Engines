import sys
import math

if __name__ == '__main__':
    # Read arguments from command line, or use sane defaults for IDE.
    argv_len = len(sys.argv)
    runFile = sys.argv[1] if argv_len >= 2 else 'sdm.trecrun'
    qrelsFile = sys.argv[2] if argv_len >= 3 else 'qrels'
    outputFile = sys.argv[3] if argv_len >= 4 else 'sdm.eval'
     
# mapping from queryNum to a dict of the form {rank: docID}
queries = {}

# mapping from queryNum to a dict of the form {docID: relevancy}
queryRelevancy = {}

# mapping from queryNum to the total relevant documents
totalRelevant = {}

# initializes queries dictionary
with open(runFile,"rt",encoding='utf-8') as input:
    for line in input:
        parts = line.split()
        
        queryNum = parts[0]
        docID = parts[2]
        rank = parts[3]
        score = parts[4]
        
        #print(queryNum,docID,rank,score)
        
        if queryNum not in queries:
            queries[queryNum] = {}
            queries[queryNum][rank] = docID
        else:
            queries[queryNum][rank] = docID
            
# initializes the relevancy dictionary
with open(qrelsFile,"rt",encoding='utf-8') as input:
    for line in input:
        parts = line.split()
        
        queryNum = parts[0]
        docID = parts[2]
        relevancy = float(parts[3])
        
        if relevancy > 0:
            if queryNum not in totalRelevant:
                totalRelevant[queryNum] = 1
            else:
                totalRelevant[queryNum] += 1
        
        if queryNum not in queryRelevancy:
            queryRelevancy[queryNum] = {}
            queryRelevancy[queryNum][docID] = relevancy
        else:
            queryRelevancy[queryNum][docID] = relevancy


      
# ideal ordering of relevancy for each query
ideal = {}

for query in queryRelevancy:
    ideal[query] = []
    for docID,relevancy in queryRelevancy[query].items():
        ideal[query].append(relevancy)
    
    ideal[query].sort(reverse=True)

# clear the file
f = open(outputFile,"w")  
f.close()

total_results = [0,0,0,0,0,0]

# calculate statistics for each query
for query in queries:
    
    # array to return with results
    result = [-1,-1,-1,-1,-1,-1]
    # 0 => NDCG@75
    # 1 => RR
    # 2 => P@15
    # 3 => R@20
    # 4 => F1@25
    # 5 => AP
    
    # array of ideal retrieved documents
    ideal_results = ideal[query]
    
    # initialize accumulators to DCG and ideal DCG
    DCG = 0
    DCG_ideal = 0
    
    # total relevant documents for the query
    relevant_total = totalRelevant[query]
    #print(relevant_total)
    
    # relevant documents so far
    relevant_count = 0
    
    # sum of all the precision values when recall increases
    total_precision = 0
    
    # RR = 1/rank of first relevant document
    reciprocal_rank = None
    
    # ranked list mapping (rank => docID)
    rankedList = queries[query]
    
    # relevancy list mapping (docID => relevancy)
    relevancyList = queryRelevancy[query]
    
    # iterate through the ranked list of documents
    for rank in range(1,len(rankedList)+1):
        
        docID = rankedList[str(rank)]
        
        relevancy = 0
        
        if docID in relevancyList:
            relevancy = relevancyList[docID]
        
        # if the document is relevant to the query
        if relevancy > 0:
            
            # increment relevant count
            relevant_count += 1
            
            total_precision += relevant_count / rank
            
            # set RR if not set already at first relevant document
            if result[1] == -1:
                result[1] = 1 / rank
        
        if rank == 1:
            DCG += relevancy
            DCG_ideal += ideal_results[rank-1]
        else:
            DCG += relevancy / math.log2(rank)   
            if rank-1 < len(ideal_results):
                DCG_ideal += ideal_results[rank-1] / math.log2(rank) 
        
        # set precision if at rank 15
        if rank == 15:
            # how many relevant out of the first 15 documents
            result[2] = relevant_count / 15
        
        # set recall if at rank 20
        if rank == 20:
            # how many out of the total relevant we retrieved
            result[3] = relevant_count / relevant_total
            
        # set F1 if at rank 25
        if rank == 25:
            # find precision and recall
            P = relevant_count / 25
            R = relevant_count / relevant_total
            
            # F1 formula
            if P+R == 0:
                result[4] = 0.0
            else:
                result[4] = (2*P*R)/(P+R)
        
        if rank == 75:
            result[0] = DCG / DCG_ideal
            
    for rank in range(len(rankedList)+1,76):
        if rank-1 < len(ideal_results):
                DCG_ideal += ideal_results[rank-1] / math.log2(rank) 
            
    # NDCG@75 = DCG / ideal DCG even if never reach 75
    if result[0] == -1:
        result[0] = DCG / DCG_ideal
    
    # RR = 0 if no relevant documents
    if result[1] == -1:
        result[1] = 0.0
    
    # P@15 = rel retrieved / 15 even if never reach 15
    if result[2] == -1:
        result[2] = relevant_count / 15
        
    # R@20 = rel retrieved / total rel even if never reach 20
    if result[3] == -1:
        result[3] = relevant_count / relevant_total
        
    # F1@25 is defined even if never reach 25
    if result[4] == -1:
        # find precision and recall
        P = relevant_count / 25
        R = relevant_count / relevant_total
        
        # F1 formula
        if P+R == 0:
            result[4] = 0.0
        else:
            result[4] = (2*P*R)/(P+R)
    
    if relevant_count == 0:
        result[5] = 0.0
    else:
        result[5] = total_precision / relevant_total
        
    for i in range(len(result)):
        total_results[i] += result[i]
    
    result = list(map(lambda x: round(x,4),result))
                
    f = open(outputFile,"a")
    
    f.write("NDCG@75 " + query + " " + str(format(result[0], '.4f')) + "\n")
    f.write("RR " + query + " " + str(format(result[1], '.4f')) + "\n")
    f.write("P@15 " + query + " " + str(format(result[2], '.4f')) + "\n")
    f.write("R@20 " + query + " " + str(format(result[3], '.4f')) + "\n")
    f.write("F1@25 " + query + " " + str(format(result[4], '.4f')) + "\n")
    f.write("AP " + query + " " + str(format(result[5], '.4f')) + "\n")

f.write("NDCG@75 " + " all " + str(format(total_results[0]/len(queries), '.4f')) + "\n")
f.write("MRR " + " all " + str(format(total_results[1]/len(queries), '.4f')) + "\n")
f.write("P@15 " + " all " + str(format(total_results[2]/len(queries), '.4f')) + "\n")
f.write("R@20 " + " all " + str(format(total_results[3]/len(queries), '.4f')) + "\n")
f.write("F1@25 " + " all " + str(format(total_results[4]/len(queries), '.4f')) + "\n")
f.write("MAP " + " all " + str(format(total_results[5]/len(queries), '.4f')) + "\n")
  
f.close()
