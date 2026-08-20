/**
 * Gemini Client — ProductPilot AI Multi-Model Inference Gateway.
 */

// Backend URL is defined in main.js and used globally
const BACKEND = (typeof window !== "undefined" && (window.__PRODUCTPILOT_BACKEND__ || window.__BACKEND_URL__))
  ? (window.__PRODUCTPILOT_BACKEND__ || window.__BACKEND_URL__)
  : "http://127.0.0.1:8787";
const DEFAULT_MODEL = "gemini-2.5-flash";
const GEMINI_API_KEY = (typeof window !== "undefined" && (window.__GEMINI_API_KEY__ || window.VITE_GEMINI_API_KEY)) || "";

let _backendModel = DEFAULT_MODEL;
export function setModel(m) { _backendModel = m || DEFAULT_MODEL; }

// ─── Direct REST call to Gemini API ──────────────────────────────────────────
async function geminiDirect(prompt, model) {
  if (GEMINI_API_KEY === "YOUR_GEMINI_API_KEY_HERE" || !GEMINI_API_KEY) {
    throw new Error("Gemini API key not configured. Set GEMINI_API_KEY in .env");
  }
  const apiModel = model && model.startsWith("gemini") ? model : "gemini-1.5-flash";
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${apiModel}:generateContent?key=${GEMINI_API_KEY}`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ role: "user", parts: [{ text: prompt }] }],
      generationConfig: { temperature: 0.7, maxOutputTokens: 2048 }
    })
  });
  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`Gemini API ${resp.status}: ${err}`);
  }
  const data = await resp.json();
  return data.candidates?.[0]?.content?.parts?.[0]?.text || "";
}

// ─── Core call ────────────────────────────────────────────────────────────────

export async function geminiChat(prompt, { model, onChunk } = {}) {
  const useModel = model || _backendModel;

  // 1. Electron: use IPC so the API key never leaves the main process
  if (window.taskPilotDesktop?.geminiChat) {
    const result = await window.taskPilotDesktop.geminiChat(prompt, useModel);
    if (!result.success) throw new Error(result.error);
    if (onChunk) onChunk(result.text);
    return result.text;
  }

  // 2. Try live backend server first (routes securely via OpenRouter & NVIDIA NIM)
  const activeBackend = (typeof window !== "undefined" && window.__TASKPILOT_BACKEND__)
    ? window.__TASKPILOT_BACKEND__
    : "https://taskpilotai-backend-956061149939.us-central1.run.app";

  try {
    const resp = await fetch(`${activeBackend}/api/taskpilot/gemini-chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, model: useModel })
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data.text && !data.text.startsWith("Error:") && !data.text.startsWith("No LLM")) {
        if (onChunk) onChunk(data.text);
        return data.text;
      }
    }
  } catch (backendErr) {
    console.warn("[geminiChat] Backend call failed, trying direct REST", backendErr);
  }

  // 3. Direct Google AI REST API fallback
  try {
    const text = await geminiDirect(prompt, useModel);
    if (onChunk) onChunk(text);
    return text;
  } catch (directErr) {
    throw directErr;
  }
}

// ─── Robust JSON extractor ───────────────────────────────────────────────────
// Gemini 2.5-flash uses extended thinking and often outputs reasoning text
// before/after the JSON. This extracts the first valid JSON array or object.
function extractJSON(raw) {
  if (!raw) return null;
  // Remove thinking blocks which might contain brackets and confuse extraction
  let text = raw.replace(/<thinking>[\s\S]*?<\/thinking>/gi, "");
  // Strip markdown code fences
  text = text.replace(/```json\s*/gi, "").replace(/```\s*/g, "").trim();
  // Try direct parse first
  try { return JSON.parse(text); } catch {}
  // Find the first [ or { and try to extract from there
  const arrStart = text.indexOf("[");
  const objStart = text.indexOf("{");
  // Pick whichever comes first
  const starts = [arrStart, objStart].filter(i => i !== -1);
  if (starts.length === 0) return null;
  const start = Math.min(...starts);
  const openChar = text[start];
  const closeChar = openChar === "[" ? "]" : "}";
  // Walk forward counting brackets to find the matching close
  let depth = 0;
  let end = -1;
  for (let i = start; i < text.length; i++) {
    if (text[i] === openChar) depth++;
    else if (text[i] === closeChar) { depth--; if (depth === 0) { end = i; break; } }
  }
  if (end === -1) return null;
  try { return JSON.parse(text.slice(start, end + 1)); } catch { return null; }
}

// ─── Specialised helpers ──────────────────────────────────────────────────────

/** Prioritise a flat task list; returns tasks with score + rankReasons */
export async function geminPrioritizeTasks(tasks) {
  const prompt = `You are TaskPilot AI — an agentic task prioritisation assistant.

Given the JSON array of engineering tasks below, rank them from highest to lowest priority.
For each task add TWO fields:
  "score": integer 0–100
  "rankReasons": array of 3 short strings explaining the score

Use these factors: severity (P1>P2>P3>P4), deadline urgency, business impact, dependency risk.
Return ONLY a valid JSON array. No markdown, no explanation outside JSON.

Tasks:
${JSON.stringify(tasks, null, 2)}`;

  const raw = await geminiChat(prompt, { model: "gemini-2.5-flash" });
  const result = extractJSON(raw);
  if (Array.isArray(result)) return result;
  console.warn("[TaskPilot] Gemini prioritisation: could not extract JSON, using local scores");
  return tasks;
}

/** Extract action items from unstructured text (email / meeting note) */
export async function geminiExtractActions(text, source = "email") {
  const prompt = `You are TaskPilot AI. Extract every actionable task from this ${source}.

Return a JSON array where each item has:
  "title": concise task title (max 80 chars)
  "description": one sentence detail
  "assignee": person mentioned, or ""
  "deadline": ISO date if mentioned, or null
  "severity": "P1"|"P2"|"P3"|"P4" — infer from urgency language
  "impact": integer 1–10

Return ONLY valid JSON. No markdown.

Text:
${text}`;

  const raw = await geminiChat(prompt, { model: "gemini-2.5-flash" });
  return extractJSON(raw) || [];
}

/** Generate a full daily plan narrative */
export async function geminiDailyPlan(tasks, engineerName, calendarBlocks = []) {
  const top = tasks.slice(0, 8);
  const meetings = calendarBlocks.map(b => `${b.start}–${b.end}: ${b.title}`).join(", ");
  const prompt = `You are TaskPilot AI. Generate a structured, actionable daily plan for ${engineerName}.

Today's calendar blocks: ${meetings || "none"}

Top prioritised tasks (in order):
${top.map((t, i) => `${i + 1}. [${t.severity || "P2"}] ${t.canonicalTitle || t.title} — score ${t.score || "?"} — due ${t.due || "?"}`).join("\n")}

Write a clear markdown daily plan with:
- A one-sentence motivating opener
- ### Top 3 Priorities (with 1-line rationale each)
- ### Time-Blocked Schedule (fit around calendar blocks)
- ### Watch List (next 3 tasks)
- ### End-of-Day Goal

Be concise, direct, and actionable. Use real task names.`;

  try {
    return await geminiChat(prompt, { model: "gemini-2.5-flash" });
  } catch (err) {
    const topP1 = tasks.slice(0, 3);
    return `### Daily Execution Focus for ${engineerName || "Engineer"}\n\n` +
      `**Top Priorities:**\n` +
      topP1.map((t, i) => `${i + 1}. **[${t.severity || "P1"}] ${t.canonicalTitle || t.title}** — High urgency item requiring immediate attention.`).join("\n") +
      `\n\n### Recommended Schedule\n- **09:00 - 11:30**: Focused deep work block on ${topP1[0]?.canonicalTitle || topP1[0]?.title || "top priority tasks"}.\n- **13:00 - 15:00**: Code review & pull request verification.\n- **16:00 - 17:00**: Standup sync & blocker resolution.`;
  }
}

/** Summarise an email thread into bullet points + action items */
export async function geminiSummariseEmail(emailBody, subject = "") {
  const prompt = `You are TaskPilot AI. Summarise this email for a software engineer.

Subject: ${subject}
Body:
${emailBody}

Return markdown with:
- **TL;DR** (one sentence)
- **Key Points** (bullet list)
- **Action Items** (bullet list, each starting with ✅)
- **Urgency**: Critical / High / Medium / Low`;

  return geminiChat(prompt, { model: "gemini-2.5-flash" });
}

/** Analyse meeting notes and extract decisions + follow-ups + meetings to schedule */
export async function geminiAnalyseMeeting(notes, meetingTitle = "") {
  const prompt = `You are TaskPilot AI. Analyse these meeting notes for "${meetingTitle}".

Notes:
${notes}

Return a JSON object with:
  "summary": string (2–3 sentences)
  "decisions": string[] (key decisions made)
  "actionItems": [{ "title", "assignee", "deadline", "severity" }]
  "followUpMeetings": [{ "title", "suggestedDate", "attendees": [], "agenda": string }]
  "risks": string[]
  "shouldwork": {
    "recommendAttend": boolean (whether the engineer should attend),
    "score": integer 0-100 (importance/urgency score),
    "reasoning": string (detailed reasoning for attending or skipping)
  },
  "transcript": [
    { "speaker": string, "text": string }
  ] (simulated dialogue of the meeting discussion in dialogue format, containing 4 to 6 statements matching the topic)

Return ONLY valid JSON.`;

  const raw = await geminiChat(prompt, { model: "gemini-2.5-flash" });
  const result = extractJSON(raw);
  if (result && typeof result === "object" && result.summary) return result;
  return {
    summary: "Could not parse meeting analysis.",
    decisions: [],
    actionItems: [],
    followUpMeetings: [],
    risks: [],
    shouldwork: {
      recommendAttend: true,
      score: 80,
      reasoning: "Failed to parse AI model response. Defaulting to recommended attendance."
    },
    transcript: [
      { speaker: "Facilitator", text: "Welcome everyone, let's go over our current checklist." },
      { speaker: "Engineer", text: "I am working on the items from our sprint backlog." },
      { speaker: "Manager", text: "Great, let's sync up and make sure we balance the loads." }
    ]
  };
}

/** Answer a natural language question about the current task state */
export async function geminiAnswerQuery(question, state, sourcesContext = "") {
  const top5 = state.prioritized.slice(0, 5).map((t, i) =>
    `${i + 1}. [${t.severity}] ${t.canonicalTitle} — score ${t.score} — due ${t.due}`
  ).join("\n");

  const prompt = `You are TaskPilot AI — an intelligent, proactive engineering assistant.

Here is the context of tasks, emails, and slack messages:
${sourcesContext}

Current state:
- Total tasks: ${state.prioritized.length}
- Completed today: ${state.completedCount}
- Top 5 tasks:
${top5}
- Active alerts: ${state.alerts.length}

Engineer's question: "${question}"

Answer concisely (2–4 sentences max). Be specific, data-driven, and actionable.
Reference real task names and scores when relevant. Provide proper reasoning for blockers and summaries for emails if requested.`;

  return geminiChat(prompt, { model: "gemini-2.5-flash" });
}

/** Real-time agent reasoning — calls onChunk for each streamed step */
export async function geminiAgentRun(intent, context, onStep) {
  const prompt = `You are TaskPilot AI — an autonomous agentic assistant.

Current context:
- Active task: ${context.activeTask}
- Total queue: ${context.queueSize} tasks
- Sources connected: ${context.sources}
- Profile: ${context.profile}

The engineer just asked: "${intent}"

Act like a real AI agent: reason step-by-step, check priorities, surface hidden risks, and give a concrete recommendation.
Format your response as:

🔍 **Scanning...** (what you checked)
🧠 **Reasoning...** (your analysis)  
⚡ **Recommendation:** (specific, actionable next step)
📊 **Confidence:** X% (your confidence in this recommendation)

Be specific, reference real data, and act proactively.`;

  return geminiChat(prompt, { model: "gemini-2.5-flash", onChunk: onStep });
}

/** Generate weekly standup summary */
export async function geminiWeeklyStandup(tasks, completedIds, engineerName) {
  const completed = tasks.filter(t => completedIds.includes(t.id));
  const pending = tasks.filter(t => !completedIds.includes(t.id));

  const prompt = `You are TaskPilot AI. Generate a standup-ready weekly summary for ${engineerName}.

Completed this week (${completed.length}):
${completed.map(t => `- ${t.canonicalTitle || t.title}`).join("\n") || "None"}

Still pending (${pending.slice(0, 5).length}):
${pending.slice(0, 5).map(t => `- [${t.severity}] ${t.canonicalTitle || t.title} (score: ${t.score})`).join("\n")}

Write a 3-paragraph weekly summary:
1. Accomplishments (what was done)
2. In-progress and blockers
3. Next week priorities and risks

Keep it professional and suitable for a manager standup report.`;

  return geminiChat(prompt, { model: "gemini-2.5-flash" });
}

/** Analyse meeting for scheduling — returns suggested meeting slots */
export async function geminiMeetingPrioritizer(meetings, calendarBlocks) {
  const prompt = `You are TaskPilot AI. Analyse these pending meetings and upcoming calendar blocks.

Pending meetings to schedule:
${JSON.stringify(meetings, null, 2)}

Existing calendar blocks:
${JSON.stringify(calendarBlocks, null, 2)}

Return a JSON array of recommended meeting schedules:
[{
  "meetingTitle": string,
  "priority": "Critical"|"High"|"Medium"|"Low",
  "priorityScore": integer 0-100,
  "suggestedTime": ISO datetime string,
  "duration": minutes as integer,
  "reasoning": string,
  "attendees": string[],
  "agenda": string,
  "isConflict": boolean,
  "conflictsWith": string or null
}]

Return ONLY valid JSON.`;

  const raw = await geminiChat(prompt, { model: "gemini-2.5-flash" });
  return extractJSON(raw) || [];
}


// ─── New Agent Capability Helpers (backend endpoints) ─────────────────────────

/** Ingest all source data and return summary */
export async function agentIngest() {
  const resp = await fetch(`${BACKEND}/api/agent/ingest`, { method: "POST", headers: { "Content-Type": "application/json" } });
  if (!resp.ok) throw new Error(`ingest ${resp.status}`);
  return resp.json();
}

/** Extract action items from emails and meeting notes */
export async function agentExtractActions() {
  const resp = await fetch(`${BACKEND}/api/agent/extract-actions`, { method: "POST", headers: { "Content-Type": "application/json" } });
  if (!resp.ok) throw new Error(`extract-actions ${resp.status}`);
  return resp.json();
}

/** Get deduplication log */
export async function agentDedupLog() {
  const resp = await fetch(`${BACKEND}/api/agent/dedup-log`);
  if (!resp.ok) throw new Error(`dedup-log ${resp.status}`);
  return resp.json();
}

/** Get top N prioritized tasks with explanations */
export async function agentPrioritized(limit = 10) {
  const resp = await fetch(`${BACKEND}/api/agent/prioritized?limit=${limit}`);
  if (!resp.ok) throw new Error(`prioritized ${resp.status}`);
  return resp.json();
}

/** Get all VP emails */
export async function agentGetVpEmails() {
  const resp = await fetch(`${BACKEND}/api/agent/vp-emails`);
  if (!resp.ok) throw new Error(`vp-emails ${resp.status}`);
  return resp.json();
}

/** Summarize a specific email by ID */
export async function agentSummarizeEmail(emailId) {
  const resp = await fetch(`${BACKEND}/api/agent/summarize-email`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ emailId })
  });
  if (!resp.ok) throw new Error(`summarize-email ${resp.status}`);
  return resp.json();
}

/** Mark a task as P1 priority */
export async function agentMarkPriority(taskId, reason = "") {
  const resp = await fetch(`${BACKEND}/api/agent/mark-priority`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ taskId, reason })
  });
  if (!resp.ok) throw new Error(`mark-priority ${resp.status}`);
  return resp.json();
}

/** Get teammate blockers */
export async function agentGetBlockers() {
  const resp = await fetch(`${BACKEND}/api/agent/blockers`);
  if (!resp.ok) throw new Error(`blockers ${resp.status}`);
  return resp.json();
}

/**
 * Inject a new P1 defect mid-demo and get the re-prioritized queue.
 * @param {object} defect - optional fields: id, title, description, assignee, deadline
 */
export async function agentInjectP1(defect = {}) {
  const resp = await fetch(`${BACKEND}/api/agent/inject-p1`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(defect)
  });
  if (!resp.ok) throw new Error(`inject-p1 ${resp.status}`);
  return resp.json();
}

/** Get agent learning profile — what it has learned about this user */
export async function agentLearningProfile() {
  const resp = await fetch(`${BACKEND}/api/agent/learning-profile`);
  if (!resp.ok) throw new Error(`learning-profile ${resp.status}`);
  return resp.json();
}

// ─── GCP Enterprise Cloud Suite API Wrappers ──────────────────────────────────
export async function gcpVertexRagSearch(query, filters = {}) {
  const resp = await fetch(`${BACKEND}/api/gcp/vertex-search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, filters })
  });
  if (!resp.ok) throw new Error(`vertex-search ${resp.status}`);
  return resp.json();
}

export async function gcpAudioTranscribe(audioBase64 = "", fileName = "recording.mp3") {
  const resp = await fetch(`${BACKEND}/api/gcp/multimodal/audio-transcribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ audioBase64, fileName })
  });
  if (!resp.ok) throw new Error(`audio-transcribe ${resp.status}`);
  return resp.json();
}

export async function gcpVisionOcr(imageBase64 = "", imageType = "image/png") {
  const resp = await fetch(`${BACKEND}/api/gcp/multimodal/vision-ocr`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ imageBase64, imageType })
  });
  if (!resp.ok) throw new Error(`vision-ocr ${resp.status}`);
  return resp.json();
}

export async function gcpPubSubPublish(sourceSystem = "Jira", eventType = "webhook", data = {}) {
  const resp = await fetch(`${BACKEND}/api/gcp/pubsub/publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sourceSystem, eventType, data })
  });
  if (!resp.ok) throw new Error(`pubsub-publish ${resp.status}`);
  return resp.json();
}

export async function gcpCloudTasksSchedule(taskName = "agent_scan", delaySeconds = 5, payload = {}) {
  const resp = await fetch(`${BACKEND}/api/gcp/cloudtasks/schedule`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ taskName, delaySeconds, payload })
  });
  if (!resp.ok) throw new Error(`cloudtasks-schedule ${resp.status}`);
  return resp.json();
}

export async function gcpGetPipelineTelemetry() {
  const resp = await fetch(`${BACKEND}/api/gcp/event-pipeline/status`);
  if (!resp.ok) throw new Error(`event-pipeline-status ${resp.status}`);
  return resp.json();
}

export async function gcpTranslateText(text = "", targetLanguage = "en") {
  const resp = await fetch(`${BACKEND}/api/gcp/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, targetLanguage })
  });
  if (!resp.ok) throw new Error(`translate ${resp.status}`);
  return resp.json();
}

export async function gcpVectorSimilarity(title = "", description = "") {
  const resp = await fetch(`${BACKEND}/api/gcp/vector-search/similarity`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description })
  });
  if (!resp.ok) throw new Error(`vector-similarity ${resp.status}`);
  return resp.json();
}

export async function gcpGetVectorIndexStatus() {
  const resp = await fetch(`${BACKEND}/api/gcp/vector-search/index-status`);
  if (!resp.ok) throw new Error(`vector-index-status ${resp.status}`);
  return resp.json();
}

