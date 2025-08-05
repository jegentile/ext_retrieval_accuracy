
# MDBRA Vector Search Performance Evaluation

This Python script evaluates the performance of vector search on a MongoDB Atlas database using the `FeedbackQARetrieval` dataset from the Massive Text Embedding Benchmark (MTEB). It uses the Voyage AI API to generate text embeddings and a custom library (`mdbra`) to orchestrate the evaluation and calculate retrieval metrics.

The script is designed to test multiple embedding dimensionalities, creating a separate MongoDB collection and vector search index for each dimension to compare their performance.

-----

## Prerequisites

Before you begin, ensure you have the following:

  * **Python 3.8+**
  * **MongoDB Atlas Cluster**: A running MongoDB Atlas cluster. You will need the connection URI. The cluster must be M10 or larger to use MongoDB Atlas Vector Search.
  * **Voyage AI API Key**: An active API key from [Voyage AI](https://www.voyageai.com/).

-----

## Installation & Setup

1.  **Clone the Repository**:
    If this script is part of a larger project, clone that project.

    ```bash
    git clone https://github.com/jegentile/ext_retrieval_accuracy 
    cd ext_retrieval_accuracy
    ```

2.  **Install Dependencies**:
    Install the necessary Python libraries.

    ```bash
    pip install mteb voyageai pymongo tqdm 
    ```
    or
    ```bash
    uv pip install mteb voyageai pymongo tqdm
    ```

3.  **Set Environment Variables**:
    The script requires two environment variables to connect to the necessary services.

      * **For Voyage AI API Key**:

        ```bash
        export VOYAGEAPI="your-voyage-ai-api-key"
        ```

      * **For MongoDB Atlas Connection**:

        ```bash
        export MDBURI="mongodb+srv://<user>:<password>@<cluster-uri>/..."
        ```

    Replace the placeholders with your actual credentials and cluster information.

-----

## Configuration

You can customize the script's behavior by modifying the global constants at the top of the file:

  * `VOYAGE_MODEL`: The name of the Voyage AI model to use for generating embeddings (e.g., `'voyage-3.5'`).
  * `DATABASE_NAME`: The name of the MongoDB database where collections will be created (e.g., `'MRL_Assessment'`).
  * `MRL_DIMENSIONS`: **This is the most important setting.** It is a list of integers representing the different embedding dimensions you want to test. The script will loop through this list.
        ```python
        MRL_DIMENSIONS = [256, 512, 1024]
        ```
  * `MTEB_DATA_NAME`: The name of the MTEB task to use (e.g., `'FeedbackQARetrieval'`).

-----

## How to Run

Once the prerequisites are met and the configuration is set, you can execute the script from your terminal:

```bash
python FeedbackQARetrieval.py
```

The script will print progress updates as it loads data, creates indexes, and finally, it will print a dictionary of performance metrics for each dimension tested.

-----

## Workflow Explained

The script follows a systematic process to evaluate retrieval performance for each specified dimension.

### 1\. Initialization

  - The script initializes a connection to your MongoDB Atlas cluster.
  - It downloads and loads the `FeedbackQARetrieval` dataset from MTEB, which includes a corpus of documents, a set of queries, and the ground-truth "relevant documents" for each query.
  - It initializes the `MDBRA` evaluation framework.

### 2\. Data Processing Loop

For each embedding dimension defined in the `MRL_DIMENSIONS` list, the script performs the following steps:

  - **📄 Create Collection**: A new, unique MongoDB collection is created for the current dimension (e.g., `FeedbackQARetrieval_256`).

  - **✨ Generate & Store Embeddings**: The `load_data_into_collection` function iterates through the corpus documents, generates vector embeddings of the specified dimension using the Voyage AI API, and inserts the documents along with their new vectors into the collection.

  - **🔎 Create Vector Index**: The `create_vector_index` function programmatically creates a MongoDB Atlas Vector Search index on the vector field of the newly populated collection. The script then pauses for 120 seconds to allow the index to finish building.

  - **🏷️ Load Labels and Queries**: The `load_mteb_labels` function prepares the ground-truth data for evaluation. It generates embeddings for each query and stores the queries, their vectors, and the list of known relevant document IDs in the database using the `mdbra` framework.

### 3\. Calculate and Report Metrics

  - After processing all specified dimensions, the script queries the `mdbra` framework.
  - It calls `CalculateMetrics` for each configured index. This function runs the test queries against the corresponding vector index, retrieves the results, and compares them to the ground-truth labels.
  - Finally, it prints a metrics dictionary (e.g., containing recall) for each dimension, allowing you to compare their retrieval performance.
