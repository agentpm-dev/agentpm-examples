import json
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain import hub

from app.settings import OPENAI_API_KEY
from app.callbacks import VerboseHandler

# --- 1) Load tools via AgentPM SDK ---
from agentpm import load

# Tool specs: namespace/name@version
TOOL_SPECS = [
    "research/wikipedia-scrape@0.1.0",
    "research/summarize-text@0.1.0",
    "research/translate-text@0.1.0",
    "research/sentiment-analysis@0.1.0",
    "research/resize-image@0.1.0",
]

print("Loading tools from AgentPM…")
scrape_loaded = load("@zack/wikipedia-scrape@0.1.0", with_meta=True)

def make_tool(name: str, fn, description: str):
    return Tool(
        name=name,
        description=description,
        func=lambda s: fn(json.loads(s)),
    )

# Map AgentPM callables to LangChain Tools
tools = [
    make_tool("research.scrape", loaded["research.scrape"], "Scrape a Wikipedia URL. Args JSON: {\"url\": string}"),
    make_tool("research.summarize", loaded["research.summarize"], "Summarize text. Args JSON: {\"text\": string, \"max_words\"?: int}"),
    make_tool("research.translate", loaded["research.translate"], "Translate text. Args JSON: {\"text\": string, \"target_language\": string}"),
    make_tool("research.analyze", loaded["research.analyze"], "Sentiment analysis. Args JSON: {\"text\": string}"),
    make_tool("research.resize", loaded["research.resize"], "Resize image from URL. Args JSON: {\"url\": string, \"width\": int, \"height\": int, \"keep_aspect\"?: bool}"),
]

# --- 2) Build a ReAct agent with verbose callbacks ---
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2, openai_api_key=OPENAI_API_KEY)
prompt = hub.pull("hwchase17/react")  # stock ReAct prompt is fine for demo

agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True, callbacks=[VerboseHandler()])

if __name__ == "__main__":
    # Demo task: end-to-end flow on a Wikipedia URL.
    task = (
        "Given this Wikipedia URL, scrape it, summarize in <= 150 words, "
        "translate the summary to Spanish, run sentiment on the English summary, "
        "and resize the first image to 320x180.\n"
        "URL: https://en.wikipedia.org/wiki/Alan_Turing\n"
        "Return a compact JSON with keys: title, summary_en, summary_es, sentiment, resized_image_base64_prefix"
    )
    result = executor.invoke({"input": task})
    print("\n=== FINAL ANSWER ===\n", result["output"])
