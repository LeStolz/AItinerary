from mcp.server.fastmcp import FastMCP
import httpx
from typing import List, Dict

mcp = FastMCP("weather_server")

@mcp.tool()
async def get_weather_forecast(lat: float, lon: float, days: int = 3) -> dict:
    """Get multi-day weather forecast using Open-Meteo API."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "weather_code"],
        "timezone": "auto",
        "forecast_days": days
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            return {"error": data["reason"]}
            
        daily = data.get("daily", {})
        forecasts = []
        
        for i in range(len(daily.get("time", []))):
            forecasts.append({
                "date": daily["time"][i],
                "max_temp_c": daily["temperature_2m_max"][i],
                "min_temp_c": daily["temperature_2m_min"][i],
                "precipitation_prob_pct": daily["precipitation_probability_max"][i],
                "weather_code": daily["weather_code"][i]
            })
            
        return {"forecasts": forecasts}

@mcp.tool()
def suggest_weather_adjustments(daily_precipitation_prob: int) -> str:
    """Suggest if outdoor activities are suitable based on rain probability."""
    if daily_precipitation_prob > 60:
        return "High rain probability. Recommend scheduling indoor activities (museums, galleries, cafes)."
    elif daily_precipitation_prob > 30:
        return "Moderate rain probability. Outdoor activities possible but keep flexible indoor backups."
    else:
        return "Low rain probability. Ideal for outdoor sightseeing and walking tours."

if __name__ == "__main__":
    mcp.run()
