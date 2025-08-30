"use client";

import SearchForm from "@/app/components/SearchForm/SearchForm";
import {duration, Stack, Typography} from "@mui/material";
import Hotel from "@/app/components/Hotel/Hotel";
import {OpenAPIClientAxios} from "openapi-client-axios";
import {Client, Components, Paths} from "@/app/types/openapi";
import {useEffect, useState} from "react";
import Link from "next/link";
import {useRouter, useSearchParams} from "next/navigation";
import BestHotelOffer = Components.Schemas.BestHotelOffer;
import {GetBestOffersByHotelFromQuery, GetBestOffersByHotelToQuery} from "@/app/types/converter";

export default function HomePage() {
    const [offers, setOffers] = useState<BestHotelOffer[]>([]);
    const [queryParameters, setQueryParameters] = useState<Paths.GetBestOffersByHotel.QueryParameters>();
    const router = useRouter();
    const query = useSearchParams();

    useEffect(() => {
        const parameters = GetBestOffersByHotelFromQuery(query);
        if(parameters.earliestDepartureDate == null) {
            return;
        }

        load(parameters).catch(console.error);
    }, []);


    async function onSubmitSearchForm(departureAirports: string[], countAdults: number, countChildren: number, duration: number, earliestDeparture: string, latestReturn: string, mealType:string, roomType:string, oceanview:boolean) {
        const parameters: Paths.GetBestOffersByHotel.QueryParameters = {
            mealType: "", oceanView: false, roomType: "",
            earliestDepartureDate: earliestDeparture,
            latestReturnDate: latestReturn,
            countAdults: countAdults,
            countChildren: countChildren,
            departureAirports: departureAirports,
            duration: duration
        };
                if (mealType) {
            parameters.mealType = mealType;
        }
        if (roomType) {
            parameters.roomType = roomType;
        }
        parameters.oceanView = oceanview;

        await load(parameters);
    }

    async function load(parameters: Paths.GetBestOffersByHotel.QueryParameters) {
        setQueryParameters(parameters);
        router.push("/?" + GetBestOffersByHotelToQuery(parameters));
        const api = new OpenAPIClientAxios({definition: 'http://localhost:8000/openapi', withServer: 0})
        const client = await api.init<Client>()
        const response = await client.getBestOffersByHotel(parameters);
        setOffers(response.data);
    }

    return (
        <>
            <Typography sx={{mb: "50px", mt: "40px"}} variant="h3">CHECK24 Holiday Challenge</Typography>
            <SearchForm submitCallback={onSubmitSearchForm}/>
            <Typography variant="h4" sx={{mt: "60px", mb: "30px"}}>Hotels for your Mallorca-Trip:</Typography>
            <Stack gap={3}>
                {offers.map(offer =>
                    <Link key={offer.hotel.id}
                          href={{pathname: '/offers', query: {...queryParameters, hotelId: offer.hotel.id}}}
                          style={{textDecoration: "none"}}>
                        <Hotel offer={offer}/>
                    </Link>
                )}
            </Stack>
        </>
    )
}