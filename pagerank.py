import math
import sys
import gzip

if __name__ == '__main__':
    # Read arguments from command line; or use sane defaults for IDE.
    argv_len = len(sys.argv)
    inputFile = sys.argv[1] if argv_len >= 2 else "links.srt.gz"
    lambda_val = float(sys.argv[2]) if argv_len >=3 else 0.2
    tau = float(sys.argv[3]) if argv_len >=4 else 0.005
    inLinksFile = sys.argv[4] if argv_len >= 5 else "inlinks.txt"
    pagerankFile = sys.argv[5] if argv_len >= 6 else "pagerank.txt"
    k = int(sys.argv[6]) if argv_len >= 7 else 100      
    
    with gzip.open(inputFile,'rt',encoding='utf-8') as input:
        #lines = input.readlines()
        P = set([]) # pages
        L = {} # outlinks
        I = {} # inlinks
        
        # go through input
        for line in input:
            line = line.split("\t")
            line[1] = line[1][0:len(line[1])-1]
            
            #if line[0] not in P:
            P.add(line[0])
            #if line[1] not in P:
            P.add(line[1])
            
            # link from line[0] to line[1]
            # line[1] has inlink from line[0]
            if line[1] in I:
                I[line[1]].append(line[0])
            else:
                I[line[1]] = [line[0]]
                    
            if line[0] in L:
                L[line[0]].append(line[1])
            else:
                L[line[0]] = [line[1]]
                        
          
# PageRank method
def PageRank(): 
    # initialize oldPR and newPR  
    oldPR = {}
    newPR = {}
    
    # ensure that convergence is not checked the first time
    first = True
    
    # each page is equally likely
    for i in P:
        oldPR[i] = 1/len(P)
        newPR[i] = 0
          
    # convergence method  
    def converged():
        sum = 0
        
        # accumulate the square difference 
        for p in P:
            sum += (newPR[p] - oldPR[p])**2
         
        # ensure sqrt(diff^2) is less than the tolerance   
        return math.sqrt(sum) < tau
    
    # as long as pagerank has not converged yet 
    while (first or not converged()):
        if not first:
            # copy over oldPR into newPR
            for page,score in newPR.items():
                oldPR[page] = score
        
        # initialize newPR
        for i in P:
            newPR[i] = lambda_val / len(P)
            
        first = False
        
        # accumulate sum instead of computing so that O(n^2) -> O(n)
        sum = 0
        
        # iterate through all the pages
        for p in P:
            pOutLinks = L[p] if L.get(p) != None else [] # outlinks of p

            # if there are out links
            if len(pOutLinks) > 0:
                # add to page rank of every outlink
                for u in pOutLinks:
                    newPR[u] += (1-lambda_val) * oldPR[p] / len(pOutLinks)
            # no outlinks
            else:
                # accumulate the sum
                sum += (1-lambda_val) * oldPR[p] / len(P)
        
        # add the sum to all the pages     
        for i in P:
            newPR[i] += sum
    
    return newPR                                
                     
 
# get the result of the pagerank algorithm  
result = sorted(list(PageRank().items()),key=lambda x: -x[1])[0:k]    

# write top k pagerank to file
f = open(pagerankFile, "w")
for count, value in enumerate(result):
    f.write(value[0] + "\t" + str(count+1) + "\t" + str(value[1]) + "\n")
f.close() 

# sorted inlink map
inlinks = sorted(list(map(lambda x: (x[0],len(x[1])),list(I.items()))),key=lambda x: -x[1])[0:k]

# write top k inlinks to file
f = open(inLinksFile, "w")
for count, value in enumerate(inlinks):
    f.write(value[0] + "\t" + str(count+1) + "\t" + str(value[1]) + "\n")
f.close() 




     

        

