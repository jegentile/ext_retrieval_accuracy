from beanie import Document

from mdbra import Index
from typing import Dict
from pymongo.synchronous.collection import Collection

class LabelSet(Document):
    name:str

class Label(Document):
    key : str
    label_set : LabelSet
    relevant_docs: Dict[str, float]
    false_negatives_labeled: bool = False
    index : Index

async def GenerateExactNearestNeighborLabel(key:str,query_vector:list[float],index:Index,collection,labelSet:LabelSet,limit:int=50):
    index_name = index.configuration.name
    path = index.configuration.path

    database_name = index.database
    collection_name = index.collection

    search_step ={
        '$vectorSearch':{
            'index':index_name,
            'exact':True,
            'path':path,
            'queryVector':query_vector,
            'limit':limit
        }
    }
    project_step = {
        '$project': {
            '_id':1,
            "search_score": { "$meta": "vectorSearchScore" }
        }
    }
    results = collection.aggregate([search_step,project_step])
    labels = {}

    for r in results:
        labels[str(r['_id'])] = r['search_score']

    label = Label(key=key,label_set = labelSet,relevant_docs=labels,false_negatives_labeled=True,index=index)
    return label

async def GetLabelSet(name:str):
    ls = await LabelSet.find_one({'name':name})
    if ls == None:
        ls = LabelSet(name = name)
        await ls.insert()
    return ls