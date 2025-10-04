## Python Agent

### What it does
A **LangChain (Python)** agent that loads tools from AgentPM and orchestrates a “research assistant” flow:
1) Scrape Wikipedia
2) Summarize (OpenAI)
3) Translate (OpenAI)
4) Sentiment
5) Resize first image

### AgentPM & tools
- `"kind": "agent"`
- Tools are **installed via AgentPM** and loaded dynamically in code (see `agent.json` and `app/main.py`).
- Tools are loaded and run via the Python SDK `"agentpm>=0.1.1"`

Example install:
```bash
agentpm install @zack/wikipedia-scrape@0.1.1
agentpm install @zack/summarize-text@0.1.3
agentpm install @zack/translate-text@0.1.0
agentpm install @zack/sentiment-analysis@0.1.1
agentpm install @zack/resize-image@0.1.4
```
or
```bash
# tools already defined in agent.json
agentpm install
```

### Quirks
- Uses the standard ReAct agent. LLM may shorten very long intermediate text; acceptable for demo purposes.
- The SDK runner streams child output, detects first JSON, and applies a **graceful TERM→KILL** if the child doesn’t exit quickly.
- Python tool subprocesses are run with `-u` (unbuffered) to reduce lag.

### Setup & run
```bash
uv sync --directory agent-app-python
# Put OPENAI_API_KEY into agent-app-python/.env.local
uv run --directory agent-app-python \
python -m dotenv -f .env.local run -- \
python -m app.main
```

### Example output
```text
Loading tools from AgentPM…

▶️  Chain start: chain
   Inputs: {'input': 'Given this Wikipedia URL, scrape it, summarize in <= 150 words, translate the summary to Spanish, run sentiment on the English summary,and resize the first image to 32x32.\nURL: https://en.wikipedia.org/wiki/Alan_Turing\nReturn a compact JSON with keys: title, summary_en, summary_es, sentiment resized_image_base64_prefix'}

> Entering new AgentExecutor chain...
I will start by scraping the provided Wikipedia URL to gather the necessary information about Alan Turing.

Action: wikipedia-scrape  
Action Input: {"url":"https://en.wikipedia.org/wiki/Alan_Turing"}  
{
    'ok': True, 
    'title': 'Alan Turing', 
    'text': 'Alan Mathison Turing ...',
    'images': ['https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Alan_turing_header.jpg/250px-Alan_turing_header.jpg', ...]
} 

I have successfully scraped the Wikipedia page for Alan Turing. Now, I will summarize the text to create a concise abstract of 150 words or less.

Action: summarize-text  
Action Input: {"text":"Alan Mathison Turing ...'}
{
    'ok': True, 
    'summary': "Alan Turing (1912–1954) was a pivotal English mathematician ... of theoretical computer science.'
}

Now that I have the summary of Alan Turing's life and contributions, I will translate this summary into Spanish. After that, I will perform sentiment analysis on the English summary and resize the first image from the scraped content to 32x32 pixels.

Action: translate-text  
Action Input: {"text":"Alan Turing (1912–1954) was a pivotal English mathematician ... of theoretical computer science."}
{
    'ok': True, 
    'translated': 'Alan Turing (1912–1954) fue un matemático y científico de la computación ... de la ciencia de la computación teórica.'
}

Now that I have the Spanish translation of the summary, I will proceed to perform sentiment analysis on the English summary. After that, I will resize the first image found in the article to 32x32 pixels.

Action: sentiment-analysis  
Action Input: {"text":"Alan Turing (1912–1954) was a pivotal English mathematician ... of theoretical computer science."}
{
    'ok': True, 
    'label': 'negative', 
    'scores': {
        'neg': 0.15, 
        'neu': 0.797, 
        'pos': 0.054, 
        'compound': -0.9217
    }
}

I have completed the sentiment analysis, which indicates a negative sentiment overall. Now, I will resize the first image from the scraped content to 32x32 pixels.

Action: resize-image  
Action Input: {"url":"https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Alan_turing_header.jpg/250px-Alan_turing_header.jpg","width":32,"height":32}  
{
    'ok': True, 
    'image_base64_jpeg': '/9j/4AAQSkZJRgABAQAAAQA.../2Q=='
}

I now know the final answer.

Final Answer: {
  "title": "Alan Turing",
  "summary_en": "Alan Turing (23 June 1912 – 7 June 1954) was a pivotal English mathematician and computer scientist, renowned as the father of theoretical computer science. He formalized algorithms and computation through the Turing machine, a foundational model for general-purpose computers. During World War II, Turing played a crucial role at Bletchley Park, leading efforts to decrypt German ciphers, which significantly aided the Allied victory. Post-war, he designed one of the earliest stored-program computers and delved into mathematical biology. Tragically, Turing was prosecuted for homosexuality in 1952, leading to his untimely death in 1954. His enduring legacy encompasses groundbreaking contributions to mathematics, computing, and artificial intelligence.",
  "summary_es": "Alan Turing (23 de junio de 1912 - 7 de junio de 1954) fue un matemático y científico de la computación inglés fundamental, conocido como el padre de la ciencia de la computación teórica. Formalizó algoritmos y computación a través de la máquina de Turing, un modelo fundamental para computadoras de propósito general. Durante la Segunda Guerra Mundial, Turing desempeñó un papel crucial en Bletchley Park, liderando esfuerzos para descifrar los códigos alemanes, lo que ayudó significativamente a la victoria aliada. Después de la guerra, diseñó una de las primeras computadoras de programa almacenado y se adentró en la biología matemática. Trágicamente, Turing fue procesado por homosexualidad en 1952, lo que llevó a su prematura muerte en 1954. Su legado perdurable abarca contribuciones pioneras a las matemáticas, la computación y la inteligencia artificial.",
  "sentiment": {
    "label": "negative",
    "scores": {
      'neg': 0.15, 
        'neu': 0.797, 
        'pos': 0.054, 
        'compound': -0.9217
    }
  },
  "resized_image_base64_prefix": "/9j/4AAQSkZJRgABAQAAAQA.../2Q=="
}
```