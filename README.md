# CHECK24 Holiday Challenge Submission Martin Weber


Hi This is my submission for the CHECK24 TechUp Holiday Challenge. 

this is a fullstack holiday search engine to search through the MASSIVE 92+ million offer dataset for Mallorca
The goal was to build something fast, functional, and demonstrate a understanding of backend systems. The whole thing runs on Docker, so you can get it up and running somewhat easily.


My Tech Stack & Approach

I wanted to use a modern high performance stack thats common in the industry. Here is what I chose and why:

Backend:     Python with FastAPI. I went with fastapi because its incredibly fast and its automatic data validation with Pydantic is actually insane. It made building a reliable API way easier.

Database:     Elasticsearch. For a search problem of this MASSIVE scale, using a standard sql database felt not right, Elasticsearch is a nice solution for this kind of work its aggregation engine is the secret sauce for making the "cheapest offer per hotel" query "fast" without having to write some awkward complex queries.

Frontend:     I used the provided Next.js/React app My main focus was on the backend but I extended the frontend to support the extra search filters I built.

Infrastructure: Everything is containerized with Docker and Docker Compose, This was a no thinker. It guarantees that the app runs the same for me as it will for you guys, completely avoiding any "it works on my machine" issues.

Cool Features & "Optimizations"

Here are some of the performance hacks and extra features implemented:
"Fast" Data Ingestion: The first version of my ingestion script was way too slow (ca. 50 hours :( ). I refactored it to use vectorized pandas operations which processes entire chunks of data at once instead of looping row for row. 
I also tuned the Elasticsearch index settings during the load, which brought the total ingestion time down to a much more reasonable 2.5 hours. ( it still ended up taking like 5 hours for ingestion alone since it crashed so often)

Aggregation Query: The main search endpoint is the most important part. Instead of a easy/simple search I used  Elasticsearchs Terms Aggregation on the hotelid and a Top Hits Aggregation to grab just the cheapest offer. This is was key for receiving results from the 92-million document index in a somewhat timely fashion.

Search Filters: as suggested in the readme, I added more searchfilters the UI and the backend fully support filtering by:
mealType (Breakfast, All Inclusive, etc.)
roomType (Double, Apartment, etc.)
oceanView (boolean)

How to run this thing locally: (maybe you wont need to because I actually hosted this at definitvnichtcheck24.xyz because porkbun didnt let me buy the .de domain if this isnt mentioned at the top then it was already too late and I chose sleep instead of that "feature")

Youll need Docker and Docker Compose installed and its a good idea to give Docker at least like 8GB of RAM (if you can stomach it) in its settings. Youll also need about 80GB of free ssd space for the stuff.

# Step 1: Get the data

you probably already have it to be honest if not then email 	techup@check24.de the very cool team will send you the offers.csv 
you can find the rest of the data @ https://github.com/TechUp-Stipendium/holiday-coding-challenge/tree/main/data

# Step 2: Data ingestion 

This is the part that takes a while (and hurt me the most)


# Open your terminal in the projects root folder
1. Start the database in the background

docker-compose up -d elasticsearch

2. IMPORTANT Wait for the database to be ready
   
docker ps

3. run the ingestion script go grab a coffee or two maybe even three
   (you could probably start a family and have grandkids if youre running this on a harddrive)
   
docker-compose run --rm backend python ingest_data.py


# Step 3: run the full application
once the data is loaded, you are ready to start the servers youll need two terminals open for this
In Terminal 1 (for backend):

From the project root run:

docker-compose up

This terminal will show live logs from the api


In Terminal 2 (for frontend):

Navigate into the frontend folder (just cd into wherever it is for you)

cd default-frontend 


Install all the js stuff 

npm i


start the frontend dev server

npm run dev


This terminal will show logs from the Next.js app dont close it



# Step 4: YIPPIE youre done 

Open your browser and go to: http://localhost:3000
you should see the full application try out the search and the added filters


Thanks for checking this out, this has been a pretty interesting experience and I want to thank you guys for this opportunity.









PS: I put this on public since im probably the last one to publish my work and I sincerely doubt anyone would see that abomination of scrambled together code and think to themselves yeah ill copy that. 

Quite frankly youd be better off vibecoding.


To be honest i dont think I will actually get like accepted to this programm since there is probably 10 more people that like actually know what they are doing so I chose to have as much fun as possible doing this.
