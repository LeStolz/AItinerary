import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.runnables import RunnableConfig

from app.agents.state import AgentState
from app.agents.tools import scrapbook_tools, logistics_tools, booking_tools
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", max_retries=3)

class Router(BaseModel):
    next: Literal["Scrapbook Agent", "Logistics Agent", "Booking Agent", "FINISH"]
    response: str = Field(default="", description="ONLY provide a response if routing to FINISH. If routing to an expert, leave this completely EMPTY.")

supervisor_prompt = """You are the Orchestrator Agent for an AI travel agency.
Your team:
- Scrapbook Agent: Analyzes the user's preferences, dream destinations, or journals.
- Logistics Agent: Builds realistic day-by-day routes, sights, and activity recommendations and checks local weather conditions.
- Booking Agent: Validates live feasibility and costs, fetching real prices for accommodations and finalizing itineraries.

Analyze the conversation history.
1. Determine if an expert is needed. If the user asks to plan a trip, or check their scrapbook, you MUST ALWAYS route to the Scrapbook Agent FIRST to retrieve their profile and destinations, UNLESS the Scrapbook Agent just responded in the previous turn.
2. If you route to an expert, leave the response field completely EMPTY. Let the experts do the talking.
3. CRITICAL RULE: NEVER route to the same expert twice in a row! Look at the sender of the very last message. If the last message was from 'Scrapbook Agent', you CANNOT route to 'Scrapbook Agent' again! You must route to FINISH or Logistics Agent.
4. IMPORTANT ROUTING RULE: If the user ONLY asked to look up information (e.g., "what is my dream trip?", "what are my preferences?"), and the Scrapbook Agent just answered, you MUST route to FINISH. Do NOT route to the Logistics Agent unless the user EXPLICITLY asked you to build an itinerary or plan the trip!
5. If the user's request is fully answered, route to FINISH and provide a friendly summary.
"""

async def supervisor_node(state: AgentState):
    messages = [SystemMessage(content=supervisor_prompt)] + state["messages"]

    router_llm = llm.with_structured_output(Router)
    result = await router_llm.ainvoke(messages)

    # Python-level loop prevention fallback
    if len(state["messages"]) > 0:
        last_msg = state["messages"][-1]
        last_sender = getattr(last_msg, "name", None)
        if last_sender == result.next and result.next != "FINISH":
            print(f"[Orchestrator] Caught loop! Forcing FINISH instead of {result.next}", flush=True)
            result.next = "FINISH"
            if not result.response:
                result.response = "I have retrieved the latest information. Let me know if you want to proceed!"

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

    async def worker_node(state: AgentState, config: RunnableConfig):
        name = system_prompt.split(".")[0]
        print(f"\n[{name}] Starting task...", flush=True)
        result = await agent.ainvoke({"messages": state["messages"]}, config=config)
        last_message = result["messages"][-1]
        print(f"[{name}] Finished task.", flush=True)
        return {"messages": [HumanMessage(content=last_message.content, name=name)]}

    return worker_node

scrapbook_node = make_worker_node(
    scrapbook_tools,
    "Scrapbook Agent. You are a Scrapbook Agent. Use your tools to perform a semantic search on the user's travel board. "
    "Formulate a highly relevant search query based on the user's input (e.g. 'beach destinations', 'dietary restrictions', 'Paris trip'). "
    "Extract and output ONLY the user's preferences, dream destinations, or journals exactly as they are returned by your search tool right now. "
    "CRITICAL: The user's scrapbook changes over time. You MUST completely IGNORE any mention of the scrapbook or destinations in the past chat history. Do NOT infer, hallucinate, or make up ANY details, key wishes, activities, or places. You must strictly output ONLY what your tool returns for this specific query."
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
