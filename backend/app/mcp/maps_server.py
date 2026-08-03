from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("maps_server")

@mcp.tool()
async def geocode_location(query: str) -> dict:
    """Resolve a place name to coordinates using OpenStreetMap Nominatim."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": "AItinerary-Agent/1.0"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        data = response.json()
        if not data:
            return {"error": f"Location '{query}' not found"}
        return {
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "display_name": data[0]["display_name"]
        }

@mcp.tool()
async def calculate_distance(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float, mode: str = "walking") -> dict:
    """Calculate routing distance (in km) and duration (in mins) using OSRM. Mode can be 'walking' or 'driving'."""
    profile = "foot" if mode == "walking" else "driving"
    url = f"http://router.project-osrm.org/route/v1/{profile}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        if data.get("code") != "Ok":
            return {"error": "Route not found"}
        
        route = data["routes"][0]
        return {
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_mins": round(route["duration"] / 60, 1)
        }

if __name__ == "__main__":
    # Start the stdio MCP server
    mcp.run()
