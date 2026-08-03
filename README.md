# AItinerary

[Link to website](https://aitinerary-frontend.vercel.app/)

## Multi-Agent System Design
An intelligent travel planner, tuned from **Google Gemini 3.5 Flash LLM Engine** using **prompt engineering**, that crafts tailored, real-time trip itineraries by combining personal user preferences, curated travel knowledge and desires, and live external services.

### Orchestrator Agent
- talks to the user through the **React** frontend and communicate with the **Python** backend through **FastAPI**.
- decides if it should delegate task to other agents using **LangChain**.

### Scrapbook Agent
- uses **RAG** to analyze the user's preferences, dream destinations, or journals **chunked** by document to preserve context, **embedded** using Google Gemini, stored in **Qdrant**, and **retrieved** using vector similarity search.
- outputs relevant user's preferences, dream destination guides (local etiquettes, neighborhood safety,...) and constraints, perhaps for the current trip request.

### Logistics Agent
- builds realistic day-by-day routes, sights and activity recommendations based on Scrapbook Agent's output by calling MCPs with **Python MCP SDK**.
- uses Mock Google Map MCP to fetch transit options and calculate distances to cluster nearby activities logically.
- uses Mock Weather MCP to check real-time multi-day local weather forecasts to adjust activities (e.g., move museum visit to a rainy day).
- outputs a draft timeline structured by locations, activities, transit time, and weather fit.

### Booking Agent
- validates live feasibility and costs.
- calls Mock Booking API and MCP to fetch real-time prices for accommodations, substituting options if draft items are sold out or over budget.
- outputs a finalized, fully priced, itinerary with booking links.