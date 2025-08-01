
from beanie import Document, Indexed
from pymongo.synchronous.collection import Collection
from mdbra import *

async def RemoveQueriesAndLabels(index):
    for l in await Label.find({'index':index}).to_list():
        await l.delete()
    for q in Query.find({'index':index}).to_list():
        await q.delete()
    await index.delete()



async def InitializeIndex(document_client: Collection,index_name: str):
    a=document_client.full_name.split('.')
    database_name = a[0]
    collection_name = a[1]

    index_id = "placeholder"
    for i in document_client.list_search_indexes():
        if i['name'] == index_name:
            path=i['latestDefinition']['fields'][0]['path']
            similarity=i['latestDefinition']['fields'][0]['similarity']
            numDimensions=i['latestDefinition']['fields'][0]['numDimensions']
            name=i['name']
            index_id = i['id']

    index = await Index.find_one({'index_id':index_id})
    if index == None:
        ic = IndexConfiguration(name=name,path=path,similarity=similarity,numDimensions=numDimensions)
        index = Index(index_id=index_id,database=database_name,collection=collection_name,configuration=ic)
        await index.insert()

    return index

class IndexConfiguration(Document):
    name: str
    path: str
    numDimensions: int
    similarity: str

class Index(Document):
    index_id : str
    database : str
    collection: str
    configuration : IndexConfiguration

