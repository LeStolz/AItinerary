from langchain_core.tools import tool
from app.mcp.client import MCPWrapper
from langchain_core.runnables import RunnableConfig
import json

@tool
def read_travel_board(query: str, config: RunnableConfig) -> str:
    """Search the user's travel board for relevant preferences, notes, and destinations using semantic search."""
    try:
        user_id = config.get("configurable", {}).get("thread_id")
        print(f"============= READ_TRAVEL_BOARD TOOL CALLED =============", flush=True)
        print(f"query: {query}", flush=True)
        print(f"user_id extracted from config: {user_id} (type: {type(user_id)})", flush=True)
        
        if not user_id:
            return "Error: Could not determine user context."

        from app.db.qdrant_db import get_qdrant_client, get_embeddings, COLLECTION_NAME
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        import json

        qdrant = get_qdrant_client()
        embeddings = get_embeddings()

        vector = embeddings.embed_query(query)

        print("Searching Qdrant...", flush=True)
        results = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=int(user_id)))]
            ),
            limit=5
        ).points
        print(f"Search returned {len(results)} results.", flush=True)
        
        if not results:
            print("DEBUG_EMPTY: No vectors matched this user_id in Qdrant.", flush=True)
            return "DEBUG_EMPTY: No vectors matched this user_id in Qdrant."
            
        formatted_results = []
        for r in results:
            title = r.payload.get("title", "Untitled")
            content = r.payload.get("content", "")
            try:
                content_dict = json.loads(content)
                content_text = content_dict.get("markdown", content)
            except:
                content_text = content
            
            formatted_results.append(f"{title}\n{content_text}")
            
        return "\n\n---\n\n".join(formatted_results)
    except Exception as e:
        print(f"============= TOOL CRASHED: {e} =============", flush=True)
        return f"DEBUG_ERROR: {e}"

@tool
async def geocode(location: str) -> str:
    """Get latitude and longitude coordinates for a location string."""
    try:
        session = await MCPWrapper("maps_server.py").get_session()
        res = await session.call_tool("geocode_location", {"query": location})
        return res.content[0].text
    except Exception as e:
        return f"Error: {e}"

@tool
async def calculate_distance(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float, mode: str = "walking") -> str:
    """Calculate distance (km) and travel time (mins) between two lat/lon coordinates."""
    try:
        session = await MCPWrapper("maps_server.py").get_session()
        res = await session.call_tool("calculate_distance", {
            "origin_lat": origin_lat, "origin_lon": origin_lon,
            "dest_lat": dest_lat, "dest_lon": dest_lon,
            "mode": mode
        })
        return res.content[0].text
    except Exception as e:
        return f"Error: {e}"

@tool
async def get_weather(lat: float, lon: float, days: int = 3) -> str:
    """Get multi-day weather forecast for given coordinates."""
    try:
        session = await MCPWrapper("weather_server.py").get_session()
        res = await session.call_tool("get_weather_forecast", {"lat": lat, "lon": lon, "days": days})
        return res.content[0].text
    except Exception as e:
        return f"Error: {e}"

@tool
async def search_accommodations(city: str, max_price: float, checkin: str, checkout: str) -> str:
    """Search for accommodations under a maximum price constraint."""
    try:
        session = await MCPWrapper("booking_server.py").get_session()
        res = await session.call_tool("search_accommodations", {
            "city": city, "max_price": max_price,
            "checkin": checkin, "checkout": checkout
        })
        return res.content[0].text
    except Exception as e:
        return f"Error: {e}"

@tool
async def save_final_itinerary(trip_title: str, content: str, config: RunnableConfig) -> str:
    """Save the completed itinerary to the user's travel board."""
    user_id = config.get("configurable", {}).get("thread_id")
    if not user_id:
        return "Error: Could not determine user context."

    try:
        from app.db.qdrant_db import get_qdrant_client, get_embeddings, COLLECTION_NAME
        from qdrant_client.http.models import PointStruct
        import json
        import uuid

        qdrant = get_qdrant_client()
        embeddings = get_embeddings()

        card_id = uuid.uuid4().hex

        payload = {
            "user_id": int(user_id),
            "type": "itinerary",
            "title": f"Itinerary: {trip_title}",
            "content": json.dumps({"markdown": content})
        }

        text_to_embed = f"{payload['title']}\n{payload['content']}"
        vector = embeddings.embed_query(text_to_embed)

        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(id=card_id, vector=vector, payload=payload)]
        )
        return "Successfully saved itinerary to the Travel Board."
    except Exception as e:
        return f"Error: {e}"

scrapbook_tools = [read_travel_board]
logistics_tools = [geocode, calculate_distance, get_weather]
booking_tools = [search_accommodations, save_final_itinerary]
