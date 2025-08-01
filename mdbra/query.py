from bson import ObjectId

from mdbra import Index, Label

from beanie import Document
import json
from typing import Dict
from pymongo.synchronous.collection import Collection

# Function returns documents for Psuedo Relevance Filtering
async def getPRFCandidates(query_filters={},number=10,unique_docIds=True):

    queries = await Query.find({}).to_list()
    


async def QueryIndex(collection:Collection,
                index:Index,
                key:str,
                text:str,
                vector:list[float],
                search_args:dict={"numCandidates": 20*50,
                "limit": 50},
                assign_labels:bool=True):

    index_name = index.configuration.name
    path = index.configuration.path

    database_name = index.database
    collection_name = index.collection

    search_step ={
        '$vectorSearch':{
            'index':index_name,
            'path':path,
            'queryVector':vector,
        }
    }
    project_step = {
        '$project': {
            '_id':1,
            "search_score": { "$meta": "vectorSearchScore" }
        }
    }
    search_step['$vectorSearch'].update(search_args)

    query_call = [search_step,project_step]
    results = collection.aggregate([search_step,project_step])
    predictions = {}
    for r in results:
        predictions[str(r['_id'])] = r['search_score']

    labels = await Label.find( {'key':str(key),'index':index}).to_list() if assign_labels else None

    return Query(key=str(key), index=index,text=text,vector=vector,predictions=predictions,labels=labels,query_call=json.dumps(query_call))

async def ReconcileLabelsAndQueries(index:Index):
    queries = await Query.find({'index':index}).to_list()
    for q in queries:
        labels = await Label.find( {'key':q.key,'index':index}).to_list()
        q.labels = labels
        await q.save()

class Query(Document):
    key : str
    index : Index
    query_call: str
    text : str
    vector : list[float]
    predictions: Dict[str, float]
    labels : list[Label]


