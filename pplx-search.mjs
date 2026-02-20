// Direct Perplexity Sonar query helper for OpenClaw
// Usage: node pplx-search.mjs "your question" [model]
// Reads PERPLEXITY_API_KEY from environment.

const apiKey = process.env.PERPLEXITY_API_KEY;
if (!apiKey) {
  console.error("Missing PERPLEXITY_API_KEY");
  process.exit(2);
}

const question = process.argv.slice(2).filter(Boolean).join(" ").trim();
if (!question) {
  console.error('Usage: node pplx-search.mjs "your question" [model]');
  process.exit(2);
}

// If the last arg looks like a model id, allow override via PPLX_MODEL env instead.
const model = process.env.PPLX_MODEL || "sonar-pro";

const body = {
  model,
  messages: [
    {
      role: "system",
      content:
        "Antworte immer auf Deutsch. Antworte präzise und nenne Quellen/Citations, wenn verfügbar."
    },
    { role: "user", content: question }
  ],
  // Keep responses reasonably small; caller can ask for more.
  max_tokens: 600,
  temperature: 0.2,
};

const res = await fetch("https://api.perplexity.ai/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify(body),
});

const text = await res.text();
let json;
try { json = JSON.parse(text); } catch { json = null; }

if (!res.ok) {
  const msg = json?.error?.message || text;
  console.error(`Perplexity error (${res.status}): ${msg}`);
  process.exit(1);
}

const answer = json?.choices?.[0]?.message?.content ?? "";
const citations = json?.citations ?? json?.choices?.[0]?.citations ?? [];

const out = {
  model: json?.model ?? model,
  answer,
  citations,
};

process.stdout.write(JSON.stringify(out, null, 2));
