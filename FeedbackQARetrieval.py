import mteb
from mdbra import (Index,Label,LabelSet,Query,InitializeIndex,InitializeMDBRA,QueryIndex,
                   CalculateMetrics,ReconcileLabelsAndQueries,GetLabelSet)
import os
import voyageai
from pprint import pprint
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
from tqdm import tqdm
import json
import asyncio
import time

VOYAGE_MODEL = 'voyage-3.5'
DATABASE_NAME = 'MRL_Assessment'
MRL_DIMENSIONS = [256, 512, 1024, 2048]
MTEB_DATA_NAME = 'FeedbackQARetrieval'
MTEB_CORPUS_KEY = 'test'
VECTOR_FIELD_PREFIX='vector'

def load_data_into_collection(collection,corpus,voyage_model,dimensions,batch_size=96,vector_field='vector'):
    vo = voyageai.Client(os.environ['VOYAGEAPI'])
    batched_texts = []
    batched_documents = []
    last_key = list(corpus.keys())[-1]
    print("Loading vectors into the database")
    for k in tqdm(corpus):
        doc = {
            'text':corpus[k],
            'key':k
        }
        batched_documents.append(doc)
        batched_texts.append(doc['text'])

        if len(batched_texts) == batch_size or k==last_key:
            result = vo.embed(batched_texts,voyage_model,output_dimension=dimensions,input_type='document')
            for i,v in enumerate(batched_documents):
                batched_documents[i][vector_field]=result.embeddings[i]
            collection.insert_many(batched_documents)
            batched_documents= []
            batched_texts = []

def create_vector_index(collection,index_name,field,dimensions,similarity='cosine'):
    print("Creating search index...")
    search_index_model = SearchIndexModel(
        definition={
            "fields": [
                {
                    "type": "vector",
                    "numDimensions": dimensions,
                    "path": field,
                    "similarity": similarity
                }
            ]
        },
        name=index_name,
        type="vectorSearch"
    )
    collection.create_search_index(model=search_index_model)

async def load_mteb_labels(collection,index,queries,relevant_docs,filename,voyage_model,dimensions,load_from_file=False,label_set_name='mteb_test'):
    key_to_doc_id_mapping = {}
    if not load_from_file:
        print('Generating document key mapping.. (This can take a while...)')
        for i in tqdm(relevant_docs):
            rd_set = relevant_docs[i]
            for doc_key in rd_set:
                if rd_set[doc_key] != 0:
                    if not doc_key in key_to_doc_id_mapping.keys():
                        doc = collection.find_one({'key':doc_key})
                        key_to_doc_id_mapping[doc_key] = str(doc['_id'])

        with open(filename,'w') as f:
            json.dump(key_to_doc_id_mapping,f,indent=2)
    else:
        with open(filename) as f:
            key_to_doc_id_mapping = json.load(f)

    print('Populating labels')
    label_set = await GetLabelSet(label_set_name)
    vo = voyageai.Client(os.environ['VOYAGEAPI'])

    for qk in tqdm(queries):
        query_text = queries[qk]
        rds = relevant_docs[qk]
        r_docs = {}
        for rdk in rds:
            if rds[rdk] > 0:
                r_docs[key_to_doc_id_mapping[rdk]] = rds[rdk]

        label = Label(key=qk,label_set = label_set,relevant_docs=r_docs,false_negatives_labeled=True,index=index)
        await label.insert()

        qv = vo.embed(query_text,voyage_model,output_dimension=dimensions,input_type='query').embeddings[0]
        query = await QueryIndex(collection=collection,index=index,key=qk,text=query_text,vector=qv)
        await query.insert()

async def main():
    uri = os.environ['MDBURI']
    document_client = MongoClient(uri)
    database_name = DATABASE_NAME
    collection_name = MTEB_DATA_NAME

    task = mteb.get_task(MTEB_DATA_NAME)
    task.load_data()
    await InitializeMDBRA(uri,'mrl_retrieval_accuracy')

    MRL_DIMENSIONS = []
    for d in MRL_DIMENSIONS:
        print(f'Processing {MTEB_DATA_NAME} at {d} dimensionality')
        vector_field_name = f'{VECTOR_FIELD_PREFIX}_{d}'
        collection_name = f'{MTEB_DATA_NAME}_{d}'
        document_collection = document_client[database_name][collection_name]

        index_name = vector_field_name
        # Step 1: Load the data into a collection
        load_data_into_collection(document_collection,task.corpus[MTEB_CORPUS_KEY],VOYAGE_MODEL,d,vector_field=vector_field_name)

        # Step 2: create a vector index
        create_vector_index(document_collection,index_name,vector_field_name,d)

        # wait until the vector index is built...
        time.sleep(120)

        index = await InitializeIndex(document_collection,index_name)
        # Step 3: Load mteb labels
        await load_mteb_labels(document_collection,index,task.queries[MTEB_CORPUS_KEY],task.relevant_docs[MTEB_CORPUS_KEY],
                               f'{MTEB_DATA_NAME}-{VOYAGE_MODEL}',VOYAGE_MODEL,d,)

    # Step 5: Report Metrics

    for i in await Index.find().to_list():
        m = await CalculateMetrics(query_filters={'index':i})
        print(f'{i.configuration.name}')
        pprint(m)

if __name__ == '__main__':
    asyncio.run(main())