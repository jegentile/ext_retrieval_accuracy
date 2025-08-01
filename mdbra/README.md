# **MongoDB Retrieval Analytics (MDBRA)**

MDBRA is a Python library designed to assess vector retrieval quality for index configurations.

## **Features**

* **Index Management**: Initialize and manage search indexes within your MongoDB collections.
* **Querying**: Perform vector similarity searches against your indexed data.
* **Labeling**: Define and manage sets of ground-truth labels for your retrieved documents.
* **Metrics Calculation**: Evaluate the performance of your retrieval system using metrics like MRR (Mean Reciprocal Rank), NDCG (Normalized Discounted Cumulative Gain), and Confusion Matrix.

## **Installation**

(Assumed: `uv sync --dev`)

## **Module Breakdown**

* `__init__.py`: Initializes Beanie ODM and provides convenience imports for core functions and classes.
* `index.py`:
    * IndexConfiguration: Beanie Document for storing search index configuration details.
    * Index: Beanie Document representing a MongoDB search index, linking to its configuration, database, and collection.
    * InitializeIndex: Asynchronously initializes an Index document based on an existing MongoDB search index.
* `label.py`:
    * LabelSet: Beanie Document for grouping related labels.
    * Label: Beanie Document storing the ground-truth relevant documents for a given query key within a LabelSet.
    * GetLabelSet: Asynchronously retrieves or creates a LabelSet.
* `query.py`:
    * Query: Beanie Document storing details of a performed query, including its vector, text, predictions, and associated labels.
    * QueryIndex: Asynchronously performs a vector search query against a specified index and records the results.
    * ReconcileLabelsAndQueries: Asynchronously updates the labels associated with existing queries.
* `metrics.py`:
    * CalculateMetrics: Asynchronously calculates various retrieval metrics (e.g., MRR, NDCG, Confusion Matrix) based on stored queries and labels.
    * GeneratorConfusionMatrix: Helper function to generate a confusion matrix from label and prediction sets.


## **Usage**

### **1\. Initialization**

First, initialize MDBRA with your MongoDB URI and database name.
```python
from mdbra import Initialize_MDBRA  
from motor.motor_asyncio import AsyncIOMotorClient

# Replace with your MongoDB URI and database name  
MONGO_URI = "mongodb://localhost:27017/"  
MDBRA_DB_NAME = "retrievla_quality"

async def main():  
  client = AsyncIOMotorClient(MONGO_URI)  
  await Initialize_MDBRA(MONGO_URI, MDBRA_DB_NAME)  
  print("MDBRA initialized successfully\!")

if __name__ \== "__main__":  
import asyncio  
asyncio.run(main())
```

### **2\. Indexing**

Initialize an Index object for your MongoDB collection and search index.
```python
from mdbra import InitializeIndex  
from pymongo.synchronous.collection import Collection  
from pymongo import MongoClient

async def setup_index(mongo_uri: str, db_name: str, collection_name: str, index_name: str):  
    client = MongoClient(mongo_uri)  
    my_collection: Collection = client[db_name][collection_name]  
    my_index = await InitializeIndex(my_collection, index_name)  
    print(f"Index '{my_index.configuration.name}' initialized with ID: {my_index.index_id}")  
    return my_index
```
### **3\. Querying**

Perform vector search queries, and MBDRA stores the results.

```python
from mdbra import QueryIndex, Index, InitializeIndex  
from pymongo.synchronous.collection import Collection  
from pymongo import MongoClient

async def run_query(mongo_uri: str, db_name: str, collection_name: str, index_name: str, key: str, text: str, vector: list[float]):
    client = MongoClient(mongo_uri)
    my_collection: Collection = client[db_name][collection_name]
    my_index = await InitializeIndex(my_collection, index_name) # Ensure index is initialized or retrieved

    query_result = await QueryIndex(
        collection=my_collection,
        index=my_index,
        key=key,
        text=text,
        vector=vector
    )
    print(f"Query '{query_result.text}' with key '{query_result.key}' executed.")
    return query_result
```
### **4\. Labeling**

Create and associate labels with your queries.

```python
from mdbra import GetLabelSet, Label, Query, ReconcileLabelsAndQueries
from mdbra import Index 

async def create_and_associate_labels(query_obj: Query, label_set_name: str, relevant_docs_map: dict[str, float]):
    label_set = await GetLabelSet(label_set_name)
    new_label = Label(
        key=query_obj.key,
        label_set=label_set,
        relevant_docs=relevant_docs_map,
        false_negatives_labeled=True, # Set to True if all false negatives are explicitly labeled  
        index=query_obj.index
    )
    await new_label.insert()  
```

### **5\. Calculating Metrics**

Evaluate the performance of your retrieval system.

```python

from mdbra import CalculateMetrics, Index  
from pymongo.synchronous.collection import Collection  
from pymongo import MongoClient
from mdbra import Initialize_MDBRA

async def get_metrics(  
mongo_uri: str, db_name: str, collection_name: str, index_name: str,  
metrics_list: list[str] = ['mrr@10', 'ndcg@10'], query_filters: dict = {}, label_sets=None  
):  
    # Ensure MDBRA is initialized and the index is known or initialized  
    await Initialize_MDBRA(mongo_uri, db_name) # Re-initialize if not done already

    client = MongoClient(mongo_uri)  
    my_collection: Collection = client[db_name][collection_name]  
    # This might implicitly create the Index document if it doesn't exist based on a live search index  
    my_index = await Index.find_one({'configuration.name': index_name})  
    if not my_index:  
        my_index = await InitializeIndex(my_collection, index_name)

    # Add the current index to the query filters if not already present  
    if 'index' not in query_filters:  
        query_filters['index'] = my_index

    results = await CalculateMetrics(metrics=metrics_list, query_filters=query_filters, label_sets=label_sets)  
    for key, metric_values in results.items():  
        print(f"Metrics for Key/Label Set: {key}")  
        for metric, value in metric_values.items():  
            print(f"  {metric}: {value}")  
    return results

```

