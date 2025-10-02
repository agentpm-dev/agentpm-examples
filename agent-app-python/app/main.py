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
print("Loading tools from AgentPM…")
scrape_tool = load("@zack/wikipedia-scrape@0.1.1", with_meta=True)
summarize_tool = load("@zack/summarize-text@0.1.3", with_meta=True, env={ "OPENAI_API_KEY": OPENAI_API_KEY })
translate_tool = load("@zack/translate-text@0.1.0", with_meta=True, env={ "OPENAI_API_KEY": OPENAI_API_KEY })
sentiment_tool = load("@zack/sentiment-analysis@0.1.1", with_meta=True)
resize_tool = load("@zack/resize-image@0.1.2", with_meta=True)

# Map AgentPM callables to LangChain Tools
def make_tool(name: str, fn, description: str):
    return Tool(
        name=name,
        description=description,
        func=lambda s: fn(json.loads(s)),
    )

def _fmt(x):
    return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)

tool_objs = [scrape_tool, summarize_tool, translate_tool, sentiment_tool, resize_tool]

tools = [
    make_tool(
        t["meta"]["name"],
        t["func"],
        f"{t['meta']['description']} - Inputs: {_fmt(t['meta']['inputs'])}. Outputs: {_fmt(t['meta']['outputs'])}."
    )
    for t in tool_objs
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
        "translate the summary to Spanish, run sentiment on the English summary,"
        "and resize the first image to 320x180.\n"
        "URL: https://en.wikipedia.org/wiki/Alan_Turing\n"
        "Return a compact JSON with keys: title, summary_en, summary_es, sentiment resized_image_base64_prefix"
    )
    result = executor.invoke({"input": task})
    print("\n=== FINAL ANSWER ===\n", result["output"])
