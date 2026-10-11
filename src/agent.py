from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from . import prompt
from .tools import *

MODEL = "gemini-2.5-flash"

# --- Tools ---
tool_manage_product = FunctionTool(func = manage_product)
tool_get_retailer_id = FunctionTool(func = get_retailer_id)
tool_process_fixed_bulk = FunctionTool(func = process_fixed_bulk)

# --- Agent Definition ---
root_agent = LlmAgent(
    model = MODEL,
    name = "tipti_shopper_agent",
    description = ("This agent is responsible of helping the Shopper with product management. "),
    instruction = prompt.SHOPPER_AGENT_PROMPT,
    tools = [
        tool_manage_product, tool_get_retailer_id, tool_process_fixed_bulk
    ]
)