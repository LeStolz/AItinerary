from mcp.server.fastmcp import FastMCP
from typing import List, Dict

mcp = FastMCP("booking_server")

@mcp.tool()
def search_accommodations(city: str, max_price: float, checkin: str, checkout: str) -> dict:
    """Mock search for accommodations. Returns mock prices and direct Booking.com deep links."""
    # Deterministic mock data
    mock_hotels = [
        {"name": f"Le Grand {city} Boutique", "price_per_night": max_price * 0.8, "rating": 4.5},
        {"name": f"{city} Central Hostel", "price_per_night": max_price * 0.4, "rating": 4.1},
        {"name": f"Luxury {city} Suites", "price_per_night": max_price * 1.2, "rating": 4.9}
    ]
    results = [h for h in mock_hotels if h["price_per_night"] <= max_price]
    
    # Generate booking links
    for h in results:
        h["booking_link"] = f"https://www.booking.com/searchresults.html?ss={city.replace(' ', '+')}&checkin={checkin}&checkout={checkout}"
        
    return {"results": results}

@mcp.tool()
def search_flights(origin: str, destination: str, date: str, max_price: float = 1000.0) -> dict:
    """Mock search for flights. Returns mock flights and Skyscanner links."""
    mock_flights = [
        {"airline": "Air Mock", "departure": "08:00", "arrival": "10:30", "price": 150.0},
        {"airline": "BudgetJet", "departure": "14:00", "arrival": "16:45", "price": 85.0}
    ]
    results = [f for f in mock_flights if f["price"] <= max_price]
    
    for f in results:
        # Simple mock URL logic using first 3 letters as airport code
        f["booking_link"] = f"https://www.skyscanner.net/transport/flights/{origin[:3].lower()}/{destination[:3].lower()}/{date}"
        
    return {"results": results}

@mcp.tool()
def check_sight_tickets(sight_name: str, date: str) -> dict:
    """Mock check for ticket availability at popular sights."""
    return {
        "sight": sight_name,
        "date": date,
        "status": "Available",
        "price": 25.0,
        "booking_link": f"https://www.getyourguide.com/s?q={sight_name.replace(' ', '+')}"
    }

if __name__ == "__main__":
    mcp.run()
