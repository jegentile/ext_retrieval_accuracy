import heapq
from mdbra import Query
from pprint import pprint
#Psuedo Relevance Feedback
async def SamplePRF(query_filters={},number:int=10,enable_duplicates=False):
    highest_sim = 0
    queries = await Query.find(query_filters).to_list()
    results = []
    for q in queries:
        for p in q.predictions:
            score = q.predictions[p]
            if score > highest_sim:
                highest_sim = score
            tuple = (-1*score,q,p)
            results.append(tuple)

    print(highest_sim)
    return_results = []
    return_result_docids = {}

    while len(return_results) < number:
        r = heapq.heappop(results)
        a = {'score':-1*r[0],'query':r[1],'document':r[2]}
        if enable_duplicates:
            return_results.append(a)
        else:
            if a['query'].id not in return_result_docids.keys() and a['document'] not in return_result_docids.keys():
                return_result_docids[a['query'].id] = 1
                return_result_docids[a['document']] = 1
                return_results.append(a)

    return return_results
