import "dotenv/config";
import { load } from "@agentpm/sdk";
import { pull } from "langchain/hub";
import { AgentExecutor, createOpenAIToolsAgent } from "langchain/agents";
import { ChatOpenAI } from "@langchain/openai";
import { DynamicStructuredTool } from "@langchain/core/tools";
import { BaseCallbackHandler } from "@langchain/core/callbacks/base";
import { JSONSchemaToZod } from '@dmitryrechkin/json-schema-to-zod';

const OPENAI_API_KEY = process.env.OPENAI_API_KEY ?? "";

// ——— Verbose callbacks (similar to your Python VerboseHandler)
class TerseHandler extends BaseCallbackHandler {
    name = "TerseHandler";
    #t0 = 0;

    // LLM
    async handleLLMStart(_llm: any, prompts: string | any[]) {
        const p = prompts?.[prompts.length - 1] ?? "";
        console.log(`🤖 LLM start: ${p.slice(0, 140)}…`);
    }
    async handleLLMEnd() {
        console.log("🤖 LLM end");
    }

    // Tools
    async handleToolStart(serialized: any, input: any, runId: any, parentRunId: any, tags: any[], metadata: {
        toolName: any;
    }, runType: any, config: { runName: any; }) {
        this.#t0 = Date.now();
        const toolName =
            config?.runName ||
            metadata?.toolName ||
            (tags?.find(t => t.startsWith("tool:"))?.split(":")[1]) ||
            "tool";

        const args = typeof input === "string" ? input : JSON.stringify(input);
        console.log(`🛠️ ${toolName} ← ${args.slice(0, 200)}`);
    }

    async handleToolEnd(output: any, _tool: any, _runId: any, _parentRunId: any, tags: any[], metadata: {
        toolName: any;
    }, _runType: any, config: { runName: any; }) {
        const ms = Date.now() - this.#t0;
        const toolName =
            config?.runName || metadata?.toolName ||
            (tags?.find(t => t.startsWith("tool:"))?.split(":")[1]) || "tool";

        const s = typeof output === "string" ? output : JSON.stringify(output);
        console.log(`✅ ${toolName} → ${s.slice(0, 240)} (${ms}ms)`);
    }

    // Chains/agents
    async handleChainStart(chain: { name: string | string[]; }, _inputs: any, runId: any, parentRunId: any, tags: string | string[]) {
        // Only log the run that has no parent AND is your top agent
        if (!parentRunId && (chain?.name?.includes?.("AgentExecutor") || tags?.includes("root"))) {
            console.log(`🔗 Agent start (${runId})`);
        }
    }

    async handleChainEnd(_outputs: any, runId: any, parentRunId: any, tags: string | string[]) {
        if (!parentRunId && tags?.includes("root")) {
            console.log(`🔗 Agent end (${runId})`);
        }
    }

    // (optional) errors
    async handleToolError(e, tool) {
        console.log(`🛑 ${tool?.name ?? "tool"} error:`, e?.message ?? e);
    }
    async handleLLMError(e) {
        console.log(`🛑 LLM error:`, e?.message ?? e);
    }
}

// ——— Helper: make LangChain tools from AgentPM callables
function makeTool(name: string, fn: (args: unknown) => Promise<unknown> | unknown, description: string, inputs: any) {
    // ReAct agents pass a **string**; we’ll accept either JSON string or plain
    return new DynamicStructuredTool({
        name,
        description,
        schema: JSONSchemaToZod.convert(inputs),
        metadata: { toolName: name },
        tags: [`tool:${name}`],
        func: async (input) => {
            try {
                const out = await fn(input);
                return typeof out === "string" ? out : JSON.stringify(out);
            } catch (e: any) {
                return JSON.stringify({ ok: false, error: String(e?.message ?? e) });
            }
        },
    });
}

// ——— Load tools from AgentPM (same set as Python)
async function loadAllTools() {
    console.log("Loading tools from AgentPM…");
    const scrape = await load("@zack/wikipedia-scrape@0.1.1", { withMeta: true });
    const summarize = await load("@zack/summarize-text@0.1.3", { withMeta: true, env: { OPENAI_API_KEY } });
    const translate = await load("@zack/translate-text@0.1.0", { withMeta: true, env: { OPENAI_API_KEY } });
    const sentiment = await load("@zack/sentiment-analysis@0.1.1", { withMeta: true });
    const resize = await load("@zack/resize-image@0.1.4", { withMeta: true });

    // const objs = [scrape, summarize];
    const objs = [scrape, summarize, translate, sentiment, resize];

    const tools = objs.map((t: any) =>
        makeTool(
            t.meta.name,
            t.func,
            `${t.meta.description} - Inputs: ${JSON.stringify(t.meta.inputs)}. Outputs: ${JSON.stringify(t.meta.outputs)}.`,
            t.meta.inputs,
        )
    );

    return { tools };
}

async function main() {
    const { tools } = await loadAllTools();

    // LLM
    const llm = new ChatOpenAI({
        model: "gpt-4o-mini",
        temperature: 0.2,
        apiKey: OPENAI_API_KEY,
    });

    // Prompt (React)
    const prompt = await pull("hwchase17/openai-tools-agent");

    // Agent + executor
    const handler = new TerseHandler();
    const agent = await createOpenAIToolsAgent({ llm, tools, prompt });
    const executor = new AgentExecutor({ agent, tools, callbacks: [handler] });

    // Demo task (same as Python)
    const task = [
        "Given this Wikipedia URL, scrape it, summarize in <= 150 words,",
        "translate the summary to Spanish, run sentiment on the English summary,",
        "and resize the first image to 32x32.",
        "URL: https://en.wikipedia.org/wiki/Alan_Turing",
        "Return a compact JSON with keys: title, summary_en, summary_es, sentiment_label, resized_image_base64_prefix"
    ].join(" ");

    const result = await executor.invoke(
        { input: task },
        { callbacks: [handler], tags: ["root"] }
    );

    console.log("\n=== FINAL ANSWER ===\n", result.output);
}

main().catch((e) => {
    console.error(e);
    process.exit(1);
});
