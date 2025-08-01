from mdbra.index import IndexConfiguration, Index, InitializeIndex
from mdbra.label import Label,LabelSet,GetLabelSet,GenerateExactNearestNeighborLabel
from mdbra.query import Query, QueryIndex,ReconcileLabelsAndQueries
from mdbra.metrics import CalculateMetrics, PrecisionVersusRank
from mdbra.utilities import SamplePRF
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient


async def InitializeMDBRA(uri,mdbra_database_name):
    client = AsyncIOMotorClient(uri)
    database = client[mdbra_database_name]
    await init_beanie(database=database, document_models=[Index,IndexConfiguration, Query,Label,LabelSet])

