import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Literal

from app.agents.state import AgentState
from app.agents.tools import scrapbook_tools, logistics_tools, booking_tools
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0, max_retries=0)

class Router(BaseModel):
    next: Literal["Scrapbook Agent", "Logistics Agent", "Booking Agent", "FINISH"]
    response: str = Field(default="", description="ONLY provide a response if routing to FINISH. If routing to an expert, leave this completely EMPTY.")

supervisor_prompt = """You are the Orchestrator Agent for an AI travel agency.
Your team:
- Scrapbook Agent: Analyzes the user's preferences, dream destinations, or journals.
- Logistics Agent: Builds realistic day-by-day routes, sights, and activity recommendations and checks local weather conditions.
- Booking Agent: Validates live feasibility and costs, fetching real prices for accommodations and finalizing itineraries.

Analyze the conversation history.
1. Determine if an expert is needed to fulfill the request. If so, route to them and leave the response field completely EMPTY. Do NOT provide transition messages. Let the experts do the talking.
2. NEVER route to the same expert twice in a row. If an expert just responded, you MUST move on to another expert in the workflow (e.g. Scrapbook -> Logistics -> Booking), or FINISH if the user's request is fully answered.
3. If the request is fully answered, or if it's a casual greeting, route to FINISH. Provide a natural, friendly response.
"""

async def supervisor_node(state: AgentState):
    messages = [SystemMessage(content=supervisor_prompt)] + state["messages"]

    router_llm = llm.with_structured_output(Router)
    result = await router_llm.ainvoke(messages)

    out_messages = []
    if result.response:
        out_messages.append(HumanMessage(content=result.response, name="Orchestrator Agent"))

    return {
        "messages": out_messages,
        "next": result.next
    }

def make_worker_node(tools, system_prompt):
    # create_react_agent returns a compiled graph
    agent = create_react_agent(llm, tools=tools, prompt=system_prompt)

    async def worker_node(state: AgentState):
        name = system_prompt.split(".")[0]
        print(f"\n[{name}] Starting task...", flush=True)
        result = await agent.ainvoke({"messages": state["messages"]})
        last_message = result["messages"][-1]
        print(f"[{name}] Finished task.", flush=True)
        return {"messages": [HumanMessage(content=last_message.content, name=name)]}

    return worker_node

scrapbook_node = make_worker_node(
    scrapbook_tools,
    "Scrapbook Agent. You are a Scrapbook Agent. Use your tools to perform a semantic search on the user's travel board. "
    "Formulate a highly relevant search query based on the user's input (e.g. 'beach destinations', 'dietary restrictions', 'Paris trip'). "
    "Extract and output ONLY the user's preferences, dream destinations, or journals exactly as they are returned by your search tool. "
    "Do NOT infer, hallucinate, or make up ANY details, key wishes, activities, or places that are not explicitly written in the search results. "
    "If the search returns no relevant information, state that the information is not saved on the board. Act STRICTLY as a literal data retriever."
)

logistics_node = make_worker_node(
    logistics_tools,
    "Logistics Agent. You are a Logistics Agent. Build realistic day-by-day routes, sights, and activity recommendations based on the Scrapbook Agent's output. "
    "Use your tools to cluster nearby activities logically and check local weather conditions. "
    "Output a draft timeline structured by locations, activities, transit time, and weather fit. "
    "Output ONLY the draft timeline and verification results. Do NOT write the finalized itinerary."
)

booking_node = make_worker_node(
    booking_tools,
    "Booking Agent. You are a Booking Agent. Validate live feasibility and costs using the draft from the Logistics agent. "
    "Use your tools to search for accommodations under budget constraints. Substitute options if draft items are over budget. "
    "You MUST save the final itinerary to the travel board using your tools. "
    "After saving, you MUST output the complete finalized, fully priced itinerary directly in your final chat message. "
    "Crucially, you MUST include real, clickable booking links for accommodations and activities using markdown format, e.g., [Book Hotel](URL). "
    "You MUST extract and use ONLY the exact booking links provided in the output of your search tools. Do NOT hallucinate or dynamically generate your own URLs. "
    "Do NOT output any markdown tables. Format all pricing and comparisons as clean bulleted lists instead."
)
