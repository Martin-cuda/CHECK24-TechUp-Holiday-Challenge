import os
import pandas as pd
from elasticsearch import Elasticsearch
from tqdm import tqdm
from elasticsearch.helpers import bulk, streaming_bulk

# config
ELASTIC_HOST = os.environ.get("ELASTICSEARCH_HOST", "localhost")
INDEX_NAME = "offers"
DATA_DIR = "/data"

MAPPING = {
    "properties": {
        "hotelid": {"type": "integer"},
        "hotelname": {"type": "keyword"},
        "hotelstars": {"type": "float"},
        "price": {"type": "float"},
        "countadults": {"type": "integer"},
        "countchildren": {"type": "integer"},
        "duration": {"type": "integer"},
        "mealtype": {"type": "keyword"},
        "oceanview": {"type": "boolean"},
        "roomtype": {"type": "keyword"},
        "outbounddeparturedatetime": {"type": "date"},
        "inbounddeparturedatetime": {"type": "date"},
        "outbounddepartureairport": {"type": "keyword"},
        "outboundarrivalairport": {"type": "keyword"},
        "outboundarrivaldatetime": {"type": "date"},
        "inbounddepartureairport": {"type": "keyword"},
        "inboundarrivalairport": {"type": "keyword"},
        "inboundarrivaldatetime": {"type": "date"},
    }
}


def create_es_client():
    print(f"Connecting to Elasticsearch at {ELASTIC_HOST}...")
    client = Elasticsearch(
        hosts=[f"http://{ELASTIC_HOST}:9200"],
        verify_certs=False, request_timeout=30,
        retry_on_timeout=True, max_retries=10
    )
    if not client.ping():
        raise ConnectionError("Could not connect to Elasticsearch!")
    print("Connected to Elasticsearch successfully.")
    return client


def ingest_data():
    es = create_es_client()

    print(f"Checking for index '{INDEX_NAME}'...")
    if es.indices.exists(index=INDEX_NAME):
        print(f"Index '{INDEX_NAME}' already exists. Deleting for a fresh start.")
        es.indices.delete(index=INDEX_NAME)

    print(f"Creating index '{INDEX_NAME}' with mapping.")
    es.indices.create(index=INDEX_NAME, mappings=MAPPING)

    print("Temporarily optimizing index settings for bulk ingestion.")
    es.indices.put_settings(
        index=INDEX_NAME,
        body={"index.refresh_interval": "-1", "index.number_of_replicas": 0}
    )

    print("Loading hotels data...")
    hotels_df = pd.read_csv(os.path.join(DATA_DIR, 'hotels.csv'), sep=';')
    hotels_dict = hotels_df.set_index('hotelid').to_dict('index')
    print(f"Loaded {len(hotels_dict)} hotels.")

    print("Processing and ingesting offers data...")
    chunk_size = 50000
    total_rows = 92783430

    def generate_actions(chunk_df):
        for record in chunk_df.to_dict('records'):
            doc = {
                # hotel/offers info
                "hotelid": record.get("hotelid"),
                "hotelname": record.get("hotelname"),
                "hotelstars": record.get("hotelstars") if pd.notna(record.get("hotelstars")) else 0.0,
                "price": record.get("price") if pd.notna(record.get("price")) else 0.0,
                "countadults": record.get("countadults") if pd.notna(record.get("countadults")) else 0,
                "countchildren": record.get("countchildren") if pd.notna(record.get("countchildren")) else 0,
                "duration": record.get("duration") if pd.notna(record.get("duration")) else 0,
                "mealtype": record.get("mealtype"),
                "oceanview": record.get("oceanview"),
                "roomtype": record.get("roomtype"),
                "outbounddeparturedatetime": record.get("outbounddeparturedatetime"),
                "inbounddeparturedatetime": record.get("inbounddeparturedatetime"),
                "outbounddepartureairport": record.get("outbounddepartureairport"),
                "outboundarrivalairport": record.get("outboundarrivalairport"),
                "outboundarrivaldatetime": record.get("outboundarrivaldatetime"),
                "inbounddepartureairport": record.get("inbounddepartureairport"),
                "inboundarrivalairport": record.get("inboundarrivalairport"),
                "inboundarrivaldatetime": record.get("inboundarrivaldatetime"),
            }
            if doc["outbounddeparturedatetime"]:
                yield {"_index": INDEX_NAME, "_source": doc}

    try:
        with pd.read_csv(os.path.join(DATA_DIR, 'offers.csv'), chunksize=chunk_size) as reader:
            with tqdm(total=total_rows, unit="offers") as pbar:
                for chunk in reader:
                    departure = pd.to_datetime(chunk['departuredate'], utc=True, errors='coerce')
                    arrival = pd.to_datetime(chunk['returndate'], utc=True, errors='coerce')
                    outbound_arrival_dt = pd.to_datetime(chunk['outboundarrivaldatetime'], utc=True, errors='coerce')
                    inbound_arrival_dt = pd.to_datetime(chunk['inboundarrivaldatetime'], utc=True, errors='coerce')

                    chunk['duration'] = (arrival - departure).dt.days

                    hotel_info = chunk['hotelid'].map(hotels_dict)
                    chunk['hotelname'] = hotel_info.map(lambda x: x.get('hotelname') if isinstance(x, dict) else None)
                    chunk['hotelstars'] = hotel_info.map(lambda x: x.get('hotelstars') if isinstance(x, dict) else None)

                    # datumformatting
                    chunk['outbounddeparturedatetime'] = departure.dt.strftime('%Y-%m-%dT%H:%M:%S%z')
                    chunk['inbounddeparturedatetime'] = arrival.dt.strftime('%Y-%m-%dT%H:%M:%S%z')
                    chunk['outboundarrivaldatetime'] = outbound_arrival_dt.dt.strftime('%Y-%m-%dT%H:%M:%S%z')
                    chunk['inboundarrivaldatetime'] = inbound_arrival_dt.dt.strftime('%Y-%m-%dT%H:%M:%S%z')

                    chunk_for_es = chunk[[
                        "hotelid", "hotelname", "hotelstars", "price", "countadults",
                        "countchildren", "duration", "mealtype", "oceanview", "roomtype",
                        "outbounddeparturedatetime", "inbounddeparturedatetime",
                        "outbounddepartureairport", "outboundarrivalairport", "outboundarrivaldatetime",
                        "inbounddepartureairport", "inboundarrivalairport", "inboundarrivaldatetime"
                    ]]

                    successes = 0;
                    failures = []
                    for ok, info in streaming_bulk(es, generate_actions(chunk_for_es), raise_on_error=False):
                        if not ok:
                            failures.append(info)
                        else:
                            successes += 1
                    if failures: print(f"  ...Encountered {len(failures)} errors in this chunk.")
                    pbar.update(len(chunk))
    finally:
        print("Restoring index settings...")
        es.indices.put_settings(
            index=INDEX_NAME,
            body={"index.refresh_interval": "1s", "index.number_of_replicas": 1}
        )
        print("Data ingestion complete!")


if __name__ == "__main__":
    ingest_data()

#just a small note i literally almost went insane ingesting the dataset because 5/6 attempts went for like an hour before they crashed and docker+wsl use up all my ram :(
