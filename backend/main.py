import json
from fastapi import FastAPI, Request
from elasticsearch import Elasticsearch
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

# fastapi and elasticsearch
app = FastAPI()

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

es = Elasticsearch(hosts=["http://es01:9200"])


# pydantic stuff

class Hotel(BaseModel):
    id: int
    name: Optional[str] = None
    stars: Optional[float] = None


class Offer(BaseModel):
    price: float
    countAdults: int = Field(..., alias='countadults')
    countChildren: int = Field(..., alias='countchildren')
    outbounddepartureairport: str
    mealtype: str
    oceanview: bool
    roomtype: str
    outbounddeparturedatetime: str
    inbounddeparturedatetime: str

    inboundDepartureAirport: Optional[str] = Field(None, alias='inbounddepartureairport')
    inboundArrivalAirport: Optional[str] = Field(None, alias='inboundarrivalairport')
    inboundArrivalDatetime: Optional[str] = Field(None, alias='inboundarrivaldatetime')
    outboundArrivalAirport: Optional[str] = Field(None, alias='outboundarrivalairport')
    outboundArrivalDatetime: Optional[str] = Field(None, alias='outboundarrivaldatetime')

    class Config:
        populate_by_name = True


class BestHotelOffer(BaseModel):
    hotel: Hotel
    minPrice: float
    departureDate: str
    returnDate: str
    countAdults: int
    countChildren: int
    duration: int
    countAvailableOffers: int
    roomType: Optional[str] = None
    mealType: Optional[str] = None


class GetHotelOffersResponse(BaseModel):
    hotel: Hotel
    items: List[Offer]


# api endpoints
@app.get("/openapi")
def get_openapi_spec():
    with open("openapi.json") as f:
        return json.load(f)


@app.get("/bestOffersByHotel", response_model=List[BestHotelOffer])
def search_hotels(request: Request):
    try:
        params = request.query_params
        airports = params.getlist("departureAirports[]")
        earliestDepartureDate = params.get("earliestDepartureDate")
        latestReturnDate = params.get("latestReturnDate")
        countAdults = int(params.get("countAdults"))
        countChildren = int(params.get("countChildren"))
        duration = int(params.get("duration"))
    except (TypeError, ValueError) as e:
        return {"error": f"Invalid query parameters: {e}"}

    query = {
        "size": 0, "query": {"bool": {"filter": [{"terms": {"outbounddepartureairport": airports}},
                                                 {"range": {"duration": {"gte": duration, "lte": duration + 1}}},
                                                 {"range": {"countadults": {"gte": countAdults}}},
                                                 {"range": {"countchildren": {"gte": countChildren}}}, {"range": {
                "outbounddeparturedatetime": {"gte": earliestDepartureDate}}},
                                                 {"range": {"inbounddeparturedatetime": {"lte": latestReturnDate}}}]}},
        "aggs": {"hotels": {"terms": {"field": "hotelid", "size": 100}, "aggs": {
            "cheapest_offer": {"top_hits": {"sort": [{"price": {"order": "asc"}}], "size": 1}}}}}
    }
    response = es.search(index="offers", body=query)
    results = []
    for bucket in response['aggregations']['hotels']['buckets']:
        cheapest_hit = bucket['cheapest_offer']['hits']['hits'][0]['_source']
        hotel_data = {
            "hotel": {"id": cheapest_hit.get('hotelid'), "name": cheapest_hit.get('hotelname'),
                      "stars": cheapest_hit.get('hotelstars')},
            "minPrice": cheapest_hit.get('price'),
            "departureDate": cheapest_hit.get('outbounddeparturedatetime'),
            "returnDate": cheapest_hit.get('inbounddeparturedatetime'),
            "countAdults": cheapest_hit.get('countadults'),
            "countChildren": cheapest_hit.get('countchildren'),
            "duration": cheapest_hit.get('duration'),
            "countAvailableOffers": bucket['doc_count'],
            "roomType": cheapest_hit.get('roomtype'),
            "mealType": cheapest_hit.get('mealtype')
        }
        results.append(hotel_data)
    return results


@app.get("/hotels/{hotel_id}/offers", response_model=GetHotelOffersResponse)
def get_hotel_offers(hotel_id: int, request: Request):
    try:
        params = request.query_params
        airports = params.getlist("departureAirports[]")
        earliestDepartureDate = params.get("earliestDepartureDate")
        latestReturnDate = params.get("latestReturnDate")
        countAdults = int(params.get("countAdults"))
        countChildren = int(params.get("countChildren"))
        duration = int(params.get("duration"))
    except (TypeError, ValueError) as e:
        return {"error": f"Invalid query parameters: {e}"}

    query = {
        "size": 200, "sort": [{"price": {"order": "asc"}}],
        "query": {"bool": {
            "filter": [{"term": {"hotelid": hotel_id}}, {"terms": {"outbounddepartureairport": airports}},
                       {"range": {"duration": {"gte": duration, "lte": duration + 1}}},
                       {"range": {"countadults": {"gte": countAdults}}},
                       {"range": {"countchildren": {"gte": countChildren}}},
                       {"range": {"outbounddeparturedatetime": {"gte": earliestDepartureDate}}},
                       {"range": {"inbounddeparturedatetime": {"lte": latestReturnDate}}}]}}
    }
    response = es.search(index="offers", body=query)

    offers_list = []
    for hit in response['hits']['hits']:
        offers_list.append(hit['_source'])

    hotel_details = {}
    if offers_list:
        first_offer = offers_list[0]
        hotel_details = {"id": first_offer.get('hotelid'), "name": first_offer.get('hotelname'),
                         "stars": first_offer.get('hotelstars')}

    final_response = {"hotel": hotel_details, "items": offers_list}
    return final_response