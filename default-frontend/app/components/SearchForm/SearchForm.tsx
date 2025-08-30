import React, {ChangeEvent, useEffect, useState} from 'react';
import './SearchForm.css';
import {
    Box, Button,
    Checkbox,
    Chip,
    FormControl, FormControlLabel, InputLabel,
    ListItemText,
    MenuItem,
    Select,
    SelectChangeEvent, Stack,
    TextField, Typography,
} from "@mui/material";
import {DatePicker} from "@mui/x-date-pickers";
import Counter from "@/app/components/Counter/Counter";
import { useSearchParams } from 'next/navigation';
import { GetBestOffersByHotelFromQuery } from '@/app/types/converter';
import dayjs, { Dayjs } from 'dayjs';

type Properties = {
    submitCallback: (
        departureAirports: string[],
        countAdults: number,
        countChildren: number,
        duration: number,
        earliestDeparture: string,
        latestReturn: string,
        mealType: string,
        roomType: string,
        oceanView: boolean
    ) => Promise<void>
}

interface Airport {
    code: string,
    name: string
}

const availableDepartureAirports: Airport[] = [
    {code: "MUC", name: "Munich"},
    {code: "FRA", name: "Frankfurt"},
    {code: "DUS", name: "Düsseldorf"},
    {code: "HAM", name: "Hamburg"},
    {code: "STR", name: "Stuttgart"},
    {code: "LEJ", name: "Leipzig"},
]

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
    PaperProps: {
        style: {
            maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
            width: 250,
        },
    },
};


export default function SearchForm({submitCallback}: Properties) {
    const [departureAirports, setDepartureAirports] = useState<string[]>([]);
    const [countChildren, setCountChildren] = useState<number>(0);
    const [countAdults, setCountAdults] = useState<number>(2); // Default to 2 adults
    const [duration, setDuration] = useState<number>(7); // Default to 7 days
    const [durationInput, setDurationInput] = useState<string>("7");
    const [earliestDepartureDate, setEarliestDepartureDate] = useState<Dayjs | null>(dayjs()); // Default to today
    const [latestReturnDate, setLatestReturnDate] = useState<Dayjs | null>(dayjs().add(14, 'day')); // Default to 2 weeks from today
    const [mealType, setMealType] = useState("");
    const [roomType, setRoomType] = useState("");
    const [oceanView, setOceanView] = useState(false);

    const query = useSearchParams();

    useEffect(() => {
        const params = GetBestOffersByHotelFromQuery(query)
        setDepartureAirports(params.departureAirports && params.departureAirports[0] && params.departureAirports[0].length !== 0 ? params.departureAirports : [])
        setCountChildren(isNaN(params.countChildren) ? 0 : params.countChildren);
        setCountAdults(isNaN(params.countAdults) ? 2 : params.countAdults);
        setDuration(isNaN(params.duration) ? 7 : params.duration);
        setDurationInput(params.duration ? params.duration.toString() : "7");
        setEarliestDepartureDate(params.earliestDepartureDate ? dayjs(params.earliestDepartureDate) : dayjs());
        setLatestReturnDate(params.latestReturnDate ? dayjs(params.latestReturnDate) : dayjs().add(14, 'day'));
        setMealType(params.mealType || "");
        setRoomType(params.roomType || "");
        setOceanView(params.oceanView);

    }, [query])

    const handleAirportChange = (event: SelectChangeEvent<typeof departureAirports>) => {
        const {target: {value}} = event;
        setDepartureAirports(
            typeof value === 'string' ? value.split(',') : value,
        );
    };

    const handleDurationChange = (event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
        const value = event.target.value;
        setDurationInput(value);
        const duration = parseInt(value);
        if (!isNaN(duration)) {
            setDuration(duration);
        }
    }

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        submitCallback(
            departureAirports,
            countAdults, countChildren,
            duration,
            earliestDepartureDate ? earliestDepartureDate.toISOString() : "",
            latestReturnDate ? latestReturnDate.toISOString() : "",
            mealType,
            roomType,
            oceanView
        );
    }

    return (
        <form onSubmit={handleSubmit}>
            <Stack gap={2}>
                <Stack direction="row" gap={2} sx={{alignItems: "center"}}>
                    <FormControl fullWidth>
                        <InputLabel id="departure-airport-label">Departure Airport</InputLabel>
                        <Select id="departure-airport" multiple label="Departure airport"
                                labelId="departure-airport-label"
                                value={departureAirports} onChange={handleAirportChange} MenuProps={MenuProps}
                                renderValue={(selected) => (
                                    <Box sx={{display: 'flex', height: '90%', flexWrap: 'wrap', gap: 0.5}}>
                                        {selected.map((value) => (
                                            <Chip key={value} label={value}/>
                                        ))}
                                    </Box>
                                )}>
                            {availableDepartureAirports.map((airport) => (
                                <MenuItem key={airport.code} value={airport.code}>
                                    <Checkbox checked={departureAirports.indexOf(airport.code) > -1}/>
                                    <ListItemText primary={`${airport.name} (${airport.code})`}/>
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                    <Counter label="Children" value={countChildren} setValue={setCountChildren}/>
                    <Counter label="Adults" value={countAdults} setValue={setCountAdults}/>
                </Stack>
                <Stack direction="row" gap={2} sx={{alignItems: "center"}}>
                    <TextField sx={{minWidth: 150}} label="Duration (days)" value={durationInput} onChange={handleDurationChange}
                               type="number" variant="outlined"/>
                    <DatePicker sx={{width: "100%"}} value={earliestDepartureDate} onChange={(value) => setEarliestDepartureDate(value)} label="Earliest departure"/>
                    <DatePicker sx={{width: "100%"}} value={latestReturnDate} onChange={(value) => setLatestReturnDate(value)} label="Latest return"/>
                </Stack>
                <Stack direction="row" gap={2} sx={{alignItems: "center"}}>
                    <FormControl fullWidth>
                        <InputLabel id="meal-type-label">Meal Type</InputLabel>
                        <Select
                            labelId="meal-type-label" id="mealType"
                            value={mealType} label="Meal Type"
                            onChange={(e) => setMealType(e.target.value)}
                        >
                            <MenuItem value=""><em>Any</em></MenuItem>
                            <MenuItem value="none">None</MenuItem>
                            <MenuItem value="breakfast">Breakfast</MenuItem>
                            <MenuItem value="halfboard">Half Board</MenuItem>
                            <MenuItem value="allinclusive">All Inclusive</MenuItem>
                        </Select>
                    </FormControl>
                    <FormControl fullWidth>
                        <InputLabel id="room-type-label">Room Type</InputLabel>
                        <Select
                            labelId="room-type-label" id="roomType"
                            value={roomType} label="Room Type"
                            onChange={(e) => setRoomType(e.target.value)}
                        >
                            <MenuItem value=""><em>Any</em></MenuItem>
                            <MenuItem value="double">Double</MenuItem>
                            <MenuItem value="single">Single</MenuItem>
                            <MenuItem value="apartment">Apartment</MenuItem>
                            <MenuItem value="studio">Studio</MenuItem>
                            <MenuItem value="juniorsuite">Junior Suite</MenuItem>
                            <MenuItem value="suite">Suite</MenuItem>
                            <MenuItem value="triple">Triple</MenuItem>
                        </Select>
                    </FormControl>
                    <FormControlLabel
                        control={<Checkbox checked={oceanView} onChange={(e) => setOceanView(e.target.checked)}/>}
                        label="Ocean View"
                    />
                </Stack>
                <Button variant="contained" type="submit" sx={{p: 1.5}}>
                    Search
                </Button>
            </Stack>
        </form>
    );
}