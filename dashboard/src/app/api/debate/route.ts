// src/app/api/scenario-gen/route.ts
import { NextResponse } from "next/server";
import { spawn } from "child_process";
import { readFile, readdir } from "fs/promises";
import { Dirent } from "fs";
import path from "path";

const SCENARIO_OUT_PATH = "/tmp/mad_scenarios.json";

type DebateRunParams = {
  backendDir: string;
  configPath: string;
  debateRounds?: number;
  portfolioName?: string;
  yaml?: string;
  debaterAPrompt?: string;
  debaterBPrompt?: string;
  judgePrompt?: string;
};

type LoggerChannel = "stdout" | "stderr";

type MadLoggerEntry = {
  channel: LoggerChannel;
  message: string;
};

type RunOptions = {
  logger?: (entry: MadLoggerEntry) => void;
};

type DebateMessage = {
  role: string;
  text: string;
  round: number;
  run?: number;
  scenarios?: any[];
};

type DebatePayload = {
  debate: DebateMessage[];
  scenarios: any[];
  metadata?: any;
  runDirectory?: string | null;
};

type StagePhase = "start" | "debater" | "judge" | "finish" | "error";

type StageEvent = {
  run: number;
  totalRuns?: number;
  round?: number;
  speakerLabel?: string;
  phase: StagePhase;
  text: string;
};

type StageEventWithProgress = StageEvent & {
  progress?: number;
};

const SPEAKER_LABEL: Record<string, string> = {
  A: "Proponent",
  B: "Devil's advocate",
  JUDGE: "Judge",
};

function extractTrailingText(line: string): string {
  const idx = line.lastIndexOf("]");
  return idx !== -1 ? line.slice(idx + 1).trim() : line.trim();
}

function parseMadStageLine(line: string): StageEvent | null {
  const match = line.match(
    /\[RUN#(\d+)(?:\/(\d+))?(?:\s+(R(\d+)-(A|B)|JUDGE))?]/i
  );
  if (!match) {
    return null;
  }

  const run = Number(match[1]);
  const totalRuns = match[2] ? Number(match[2]) : undefined;
  const round = match[4] ? Number(match[4]) : undefined;
  const token = match[3]?.toUpperCase();
  const runLabel = totalRuns ? `Run ${run}/${totalRuns}` : `Run ${run}`;
  const trailing = extractTrailingText(line);

  if (!token) {
    if (/starting debate/i.test(line)) {
      return {
        run,
        totalRuns,
        phase: "start",
        text: trailing ? `${runLabel} – ${trailing}` : `${runLabel} starting debate…`,
      };
    }
    if (/finished/i.test(line)) {
      return {
        run,
        totalRuns,
        phase: "finish",
        text: trailing ? `${runLabel} ${trailing}` : `${runLabel} finished`,
      };
    }
    if (/failed/i.test(line)) {
      return {
        run,
        totalRuns,
        phase: "error",
        text: `${runLabel} ${trailing}`,
      };
    }
    return null;
  }

  if (token === "JUDGE") {
    return {
      run,
      totalRuns,
      phase: "judge",
      speakerLabel: SPEAKER_LABEL.JUDGE,
      text: `${runLabel} • Judge selecting scenarios`,
    };
  }

  const speakerLetter = match[5]?.toUpperCase();
  if (speakerLetter) {
    return {
      run,
      totalRuns,
      phase: "debater",
      round,
      speakerLabel: SPEAKER_LABEL[speakerLetter] || `Debater ${speakerLetter}`,
      text: `${runLabel} • Round ${round ?? "?"} – ${
        SPEAKER_LABEL[speakerLetter] || speakerLetter
      } complete`,
    };
  }

  return null;
}

function stageFraction(stage: StageEvent): number {
  switch (stage.phase) {
    case "start":
      return 0.05;
    case "debater": {
      const r = stage.round ?? 1;
      const approx = 0.1 + r * 0.18;
      return Math.min(approx, 0.85);
    }
    case "judge":
      return 0.92;
    case "finish":
    case "error":
      return 1;
    default:
      return 0;
  }
}

function enrichStageProgress(
  stage: StageEvent,
  runProgress: Map<number, number>,
  totalRuns: number
): StageEventWithProgress {
  const prev = runProgress.get(stage.run) ?? 0;
  const target = Math.max(prev, stageFraction(stage));
  runProgress.set(stage.run, target);
  const normalizedTotal = totalRuns > 0 ? totalRuns : 1;
  const aggregate = Math.min(
    1,
    Math.max(0, ((stage.run - 1) + target) / normalizedTotal)
  );
  return { ...stage, totalRuns: normalizedTotal, progress: aggregate };
}

async function resolveLatestRunDir(runsRoot: string): Promise<string | null> {
  try {
    const markerPath = path.join(runsRoot, "latest.txt");
    const latestName = (await readFile(markerPath, "utf-8")).trim();
    if (latestName) {
      const candidate = path.join(runsRoot, latestName);
      return candidate;
    }
  } catch {
    // ignore missing marker
  }

  try {
    const entries = (await readdir(runsRoot, { withFileTypes: true })) as Dirent[];
    const folders = entries
      .filter((ent) => ent.isDirectory())
      .map((ent) => ent.name)
      .sort();
    if (folders.length) {
      return path.join(runsRoot, folders[folders.length - 1]);
    }
  } catch {
    // ignore missing runs directory
  }
  return null;
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

async function runMadDebateScript(params: DebateRunParams, options: RunOptions = {}) {
  const pythonCmd = process.env.MAD_PYTHON || "python3";
  const scriptPath = path.join(params.backendDir, "code", "debate_scenarios.py");
  const args = [
    scriptPath,
    "--config",
    params.configPath,
    "--out",
    SCENARIO_OUT_PATH,
    "--format",
    "json",
  ];
  if (typeof params.debateRounds === "number" && Number.isFinite(params.debateRounds)) {
    args.push("--rounds", String(params.debateRounds));
  }

  const env = { ...process.env, PYTHONUNBUFFERED: "1" };
  const setEnv = (key: string, value?: string) => {
    if (isNonEmptyString(value)) {
      env[key] = value;
    } else {
      delete env[key];
    }
  };

  setEnv("MAD_PROMPT_DEBATER_A", params.debaterAPrompt);
  setEnv("MAD_PROMPT_DEBATER_B", params.debaterBPrompt);
  setEnv("MAD_PROMPT_JUDGE", params.judgePrompt);
  setEnv("MAD_PORTFOLIO_NAME", params.portfolioName);
  setEnv("MAD_SHOCK_YAML", params.yaml);

  console.log("[scenario-gen] launching MAD script", {
    pythonCmd,
    args: args.join(" "),
  });

  await new Promise<void>((resolve, reject) => {
    const child = spawn(pythonCmd, args, {
      cwd: params.backendDir,
      env,
    });

    child.stdout?.on("data", (data) => {
      const text = data.toString();
      options.logger?.({ channel: "stdout", message: text });
      if (text.trim()) {
        console.log("[MAD stdout]", text.trimEnd());
      }
    });
    child.stderr?.on("data", (data) => {
      const text = data.toString();
      options.logger?.({ channel: "stderr", message: text });
      if (text.trim()) {
        console.error("[MAD stderr]", text.trimEnd());
      }
    });
    child.on("error", (err) => {
      reject(err);
    });
    child.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`MAD script exited with code ${code ?? "unknown"}`));
      }
    });
  });

  console.log("[scenario-gen] MAD script finished successfully");
}
function cleanSegmentText(raw: string, hardLimit: number): string {
  if (!raw) return "";

  let t = raw;

  // If the model/log already injected a truncation marker, keep up to that and drop the rest.
  const truncIdx = t.search(/…\[trunc\]|\[trunc\]/);
  if (truncIdx !== -1) {
    t = t.slice(0, truncIdx + "…[trunc]".length);
  }

  // Split into lines and drop anything that looks like logger noise (timestamps, [DEBUG], [INFO], etc.)
  const lines = t.split(/\r?\n/);
  const cleanLines: string[] = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Lines like "02:01:30 [DEBUG] ..." or similar logger stuff
    if (/^\d{2}:\d{2}:\d{2}\s+\[/.test(trimmed)) break;
    if (/\[(DEBUG|INFO|WARN|ERROR)]/.test(trimmed)) break;
    if (trimmed.startsWith("Request options:")) break;
    if (trimmed.startsWith("HTTP Request:")) break;
    if (trimmed.startsWith("HTTP Response:")) break;

    cleanLines.push(line);
  }

  t = cleanLines.join("\n").trim();

  // Hard cap so we never send insane blobs to the UI
  if (t.length > hardLimit) {
    t = t.slice(0, hardLimit) + "\n…[truncated]";
  }

  return t;
}

/**
 * Fallback path: parse the offline MAD log (temp.txt) and pull out the most recent
 * Proponent / Devil's Advocate / Judge round as a lightweight "chat" transcript.
 * Prefer using transcript_run_*.jsonl via extractLatestRoundFromTranscript when available.
 *
 * Picks up debater rounds (R1-A / R1-B) and the judge output (JUDGE), preserving order.
 */
function extractLatestRoundFromLog(logText: string) {
  type Side = "A" | "B" | "J";

  type Segment = {
    round: number;
    side: Side;
    start: number;
    end: number;
  };

  const segments: Segment[] = [];

  // Match both debater rounds (R1-A / R1-B) and the final JUDGE call
  // Examples:
  //   [DEBUG] [RUN#1 R1-A] Output preview:
  //   [DEBUG] [RUN#1 R1-B] Output preview:
  //   [DEBUG] [RUN#1 JUDGE] Output preview:
  const re = /\[.*?(R(\d+)-(A|B)|JUDGE)] Output preview:/g;
  let m: RegExpExecArray | null;

  while ((m = re.exec(logText)) !== null) {
    const tag = m[1]; // "R1-A" or "JUDGE"
    const roundStr = m[2]; // "1" for debaters, undefined for JUDGE
    const sideLetter = m[3] as "A" | "B" | undefined;

    let side: Side;
    let round = 0;

    if (tag === "JUDGE") {
      side = "J";
      // We'll assign the actual round after we see all debater segments.
      round = -1;
    } else {
      side = sideLetter || "A";
      round = parseInt(roundStr || "0", 10);
    }

    const start = m.index + m[0].length;
    segments.push({ round, side, start, end: logText.length });
  }

  if (!segments.length) {
    return [];
  }

  // Fill in end indices based on the next segment's start
  for (let i = 0; i < segments.length - 1; i++) {
    segments[i].end = segments[i + 1].start;
  }

  // Determine the latest debater round; judge gets attached to that
  const debaterRounds = segments
    .filter((s) => s.side === "A" || s.side === "B")
    .map((s) => s.round);
  const latestDebaterRound = debaterRounds.length
    ? debaterRounds.reduce((max, r) => (r > max ? r : max), debaterRounds[0])
    : 0;

  // Attach judge to the latest round if we saw a judge segment
  segments.forEach((s) => {
    if (s.side === "J" && s.round === -1) {
      s.round = latestDebaterRound || 0;
    }
  });

  // Now find the highest round (including judge if present)
  const latestRound = segments.reduce(
    (max, s) => (s.round > max ? s.round : max),
    segments[0].round
  );

  const latestSegs = segments.filter((s) => s.round === latestRound);

  // Map into the UI "debate" shape:
  //   { role: "Proponent" | "Devil's advocate" | "Judge", text: string, round: number }
  const roleLabel = (side: Side) =>
    side === "A" ? "Proponent" : side === "B" ? "Devil's advocate" : "Judge";

    const debate = latestSegs.map((s) => {
    const raw = logText.slice(s.start, s.end);
    // Clean out debug/log lines + apply a generous hard cap
    const text = cleanSegmentText(raw, 4000);

    return {
        role: roleLabel(s.side),
        text,
        round: s.round,
        _side: s.side,
    } as any;
    });

  // Sort strictly as: Proponent → Devil's advocate → Judge for that round
  const order: Record<Side, number> = { A: 0, B: 1, J: 2 };
  debate.sort(
    (a: any, b: any) =>
      a.round - b.round || order[a._side as Side] - order[b._side as Side]
  );

  // Strip the internal _side field before returning
  return debate.map(({ _side, ...rest }: any) => rest);
}

/**
 * Parses a single transcript_run_*.jsonl file emitted by the
 * Python MAD script. Each line is:
 *   { speaker: "A"|"B"|"JUDGE", round: number, reasoning?: string, json?: string, raw?: string }
 *
 * Returns the full debate for that run (all rounds), sorted by round then speaker.
 * This function will be called for multiple transcript files, one per run.
 */
function extractLatestRoundFromTranscript(
  jsonlText: string,
  runNumber: number,
  judgeNarrative?: string
) {
  type Speaker = "A" | "B" | "JUDGE";

  type Ev = {
    speaker: Speaker;
    round: number;
    reasoning?: string;
    json?: string;
    raw?: string;
  };

  const events: Ev[] = [];

  for (const line of jsonlText.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      const obj = JSON.parse(trimmed);
      if (!obj || !obj.speaker || typeof obj.round !== "number") continue;
      const sp = String(obj.speaker).toUpperCase() as Speaker;
      if (sp !== "A" && sp !== "B" && sp !== "JUDGE") continue;
      events.push({
        speaker: sp,
        round: obj.round,
        reasoning: obj.reasoning,
        json: obj.json,
        raw: obj.raw,
      });
    } catch {
      // ignore bad lines
    }
  }

  if (!events.length) return [];

  const roleLabel = (sp: Speaker) =>
    sp === "A"
      ? "Proponent"
      : sp === "B"
      ? "Devil's advocate"
      : "Judge";

  const order: Record<Speaker, number> = { A: 0, B: 1, JUDGE: 2 };

  // Compute max debater round for this run
  const maxDebaterRound = events
    .filter((e) => e.speaker === "A" || e.speaker === "B")
    .reduce((max, e) => (e.round > max ? e.round : max), 0);

  const debate = events
    .slice()
    .sort((a, b) => {
      // Compute effectiveRound for sorting
      const aEffectiveRound =
        a.speaker === "JUDGE" && a.round === 0
          ? (maxDebaterRound || 0) + 1
          : a.round;
      const bEffectiveRound =
        b.speaker === "JUDGE" && b.round === 0
          ? (maxDebaterRound || 0) + 1
          : b.round;
      return aEffectiveRound - bEffectiveRound || order[a.speaker] - order[b.speaker];
    })
    .map((e) => {
      // Compute effectiveRound for returned object
      const effectiveRound =
        e.speaker === "JUDGE" && e.round === 0
          ? (maxDebaterRound || 0) + 1
          : e.round;

      // Try to get clean reasoning + JSON from the fields
      let reasoningText =
        (e.reasoning && String(e.reasoning).trim()) || "";
      let jsonText = (e.json && String(e.json).trim()) || "";

      // Some lines stuff "(1) Reasoning ... (2) Revised JSON: [...]" into `json`
      // Split that so reasoning stays prose and the bracketed part is treated as JSON.
      if (!reasoningText && jsonText) {
        const m = jsonText.match(/\(2\)\s*Revised JSON:\s*/);
        if (m && typeof m.index === "number") {
          const idx = m.index;
          const before = jsonText.slice(0, idx);
          const after = jsonText.slice(idx + m[0].length);
          if (before.trim()) reasoningText = before.trim();
          if (after.trim()) jsonText = after.trim();
        }
      }

      // If still no reasoning but we have raw, fall back to raw
      if (!reasoningText && e.raw) {
        reasoningText = String(e.raw).trim();
      }

      const parts: string[] = [];
      if (reasoningText) {
        parts.push(reasoningText);
      }

      if (jsonText) {
        // Show JSON nicely fenced so markdown renders it
        parts.push(
          "JSON\n\n```json\n" + jsonText + "\n```"
        );
      }

      const text = parts.join("\n\n").trim();

      const scenarios = safeParseScenarioJson(jsonText);

      const message = {
        role: roleLabel(e.speaker),
        text,
        round: effectiveRound,
        run: runNumber,
        scenarios,
      };

      if (judgeNarrative && message.role === "Judge") {
        message.text = judgeNarrative.trim();
      }

      return message;
    });

  return debate;
}

function safeParseScenarioJson(raw: string | undefined): any[] {
  if (!raw) return [];
  let cleaned = raw.trim();
  if (!cleaned) return [];
  cleaned = cleaned.replace(/^```json\s*/i, "").replace(/```$/i, "").trim();

  const firstCurly = cleaned.indexOf("{");
  const firstBracket = cleaned.indexOf("[");
  const startIdx =
    firstCurly === -1
      ? firstBracket
      : firstBracket === -1
      ? firstCurly
      : Math.min(firstCurly, firstBracket);
  if (startIdx > 0) {
    cleaned = cleaned.slice(startIdx);
  }

  const lastSq = cleaned.lastIndexOf("]");
  const lastCurly = cleaned.lastIndexOf("}");
  const endIdx = Math.max(lastSq, lastCurly);
  if (endIdx !== -1) {
    cleaned = cleaned.slice(0, endIdx + 1);
  }

  const attempts: string[] = [cleaned];
  if (!cleaned.trim().startsWith("[") && /}\s*\n\s*{/.test(cleaned)) {
    attempts.push("[" + cleaned.replace(/}\s*\n\s*{/g, "},{") + "]");
  }

  for (const attempt of attempts) {
    try {
      const parsed = JSON.parse(attempt);
      if (Array.isArray(parsed)) return parsed;
      if (parsed && typeof parsed === "object") return [parsed];
    } catch (err) {
      continue;
    }
  }

  return [];
}

function extractNarrativeFromMarkdown(md: string): string {
  if (!md) return "";
  const lines = md.split(/\r?\n/);
  let capturing = false;
  const captured: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    const normalized = trimmed.replace(/[*_`]/g, "").replace(/^#+\s*/, "").trim();

    if (!capturing) {
      if (/^evaluation$/i.test(normalized)) {
        capturing = true;
        continue;
      }
      continue;
    }

    if (/^json\b/i.test(normalized) || /^```/i.test(trimmed)) {
      break;
    }
    captured.push(line);
  }

  const text = captured.join("\n").trim();
  if (text) return text;

  const fenceIdx = md.indexOf("```json");
  const slice = fenceIdx !== -1 ? md.slice(0, fenceIdx) : md;
  return slice.trim();
}

async function loadMadArtifacts(backendDir: string): Promise<DebatePayload> {
  // 1) Scenarios from /tmp (preferred) then fallback JSONL
  let scenarios: any[] = [];
  try {
    const rawJson = await readFile(SCENARIO_OUT_PATH, "utf-8");
    const parsed = JSON.parse(rawJson);
    scenarios = Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    console.error(
      "[scenario-gen] Could not read /tmp/mad_scenarios.json; trying data/scenarios/out.jsonl instead.",
      e
    );
    try {
      const outJsonlPath = path.join(backendDir, "data", "scenarios", "out.jsonl");
      const rawJsonl = await readFile(outJsonlPath, "utf-8");
      const lines = rawJsonl.split(/\r?\n/);
      const parsedLines: any[] = [];
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
          parsedLines.push(JSON.parse(trimmed));
        } catch (err) {
          console.error("[scenario-gen] Failed to parse JSONL line in out.jsonl:", err);
        }
      }
      scenarios = parsedLines;
    } catch (e2) {
      console.error(
        "[scenario-gen] Could not read data/scenarios/out.jsonl; returning empty scenarios.",
        e2
      );
      scenarios = [];
    }
  }

  const runsRoot = path.join(backendDir, "data", "scenarios", "runs");
  const latestRunDir = await resolveLatestRunDir(runsRoot);
  let metadata: any = null;
  if (latestRunDir) {
    try {
      const metaPath = path.join(latestRunDir, "metadata.json");
      const metaRaw = await readFile(metaPath, "utf-8");
      metadata = JSON.parse(metaRaw);
    } catch (err) {
      console.error("[scenario-gen] Failed to load run metadata:", err);
    }
  }

  // 2) Debate transcripts, with fallback to temp log
  let debate: DebateMessage[] = [];
  try {
    const scenariosDir = latestRunDir ?? path.join(backendDir, "data", "scenarios");
    const files = await readdir(scenariosDir);
    const transcriptFiles = files
      .filter((f) => /^transcript_run_\d+\.jsonl$/.test(f))
      .sort((a, b) => {
        const ma = a.match(/transcript_run_(\d+)\.jsonl/);
        const mb = b.match(/transcript_run_(\d+)\.jsonl/);
        const ra = ma ? parseInt(ma[1], 10) : 0;
        const rb = mb ? parseInt(mb[1], 10) : 0;
        return ra - rb;
      });

    for (const fileName of transcriptFiles) {
      const match = fileName.match(/transcript_run_(\d+)\.jsonl/);
      if (!match) continue;
      const runNumber = parseInt(match[1], 10);
      const transcriptPath = path.join(scenariosDir, fileName);
      const jsonlText = await readFile(transcriptPath, "utf-8");
      let judgeNarrative: string | undefined;
      try {
        const mdPath = transcriptPath.replace(/\.jsonl$/, ".md");
        const md = await readFile(mdPath, "utf-8");
        judgeNarrative = extractNarrativeFromMarkdown(md);
      } catch {
        // ignore missing MD
      }
      const runDebate = extractLatestRoundFromTranscript(jsonlText, runNumber, judgeNarrative);
      debate.push(...runDebate);
    }
  } catch (e) {
    console.error(
      "[scenario-gen] Error while trying to read transcript_run_*.jsonl; will fall back to temp.txt.",
      e
    );
  }

  if (!debate.length) {
    try {
      const tempLogPath = path.join(backendDir, "temp.txt");
      const logText = await readFile(tempLogPath, "utf-8");
      debate = extractLatestRoundFromLog(logText);
    } catch (e) {
      console.error(
        "[scenario-gen] Could not read temp.txt for offline debate; returning empty debate.",
        e
      );
      debate = [];
    }
  }

  // Ensure at least one Judge message (synthesized if needed)
  const hasJudge = debate.some((m) => m.role === "Judge");
  if (!hasJudge && scenarios.length) {
    const maxRound = debate.reduce((max, m) => (m.round > max ? m.round : max), 0);
    const judgeRound = maxRound ? maxRound + 1 : 1;
    const judgeText =
      "Judge-selected scenarios:\n\n```json\n" +
      JSON.stringify(scenarios, null, 2) +
      "\n```";
    debate.push({
      role: "Judge",
      text: judgeText,
      round: judgeRound,
      scenarios,
    });
  }

  const judgeWithMatrix = debate
    .filter(
      (m) => m.role === "Judge" && Array.isArray((m as any).scenarios) && (m as any).scenarios.length
    )
    .sort((a, b) => {
      const arun = typeof a.run === "number" ? a.run : 0;
      const brun = typeof b.run === "number" ? b.run : 0;
      if (arun !== brun) return arun - brun;
      return (a.round ?? 0) - (b.round ?? 0);
    });

  if (judgeWithMatrix.length) {
    const latestJudge = judgeWithMatrix[judgeWithMatrix.length - 1];
    if (latestJudge.scenarios?.length) {
      scenarios = latestJudge.scenarios;
    }
  }

  return { debate, scenarios, metadata, runDirectory: latestRunDir };
}

export async function POST(req: Request) {
  try {
    let body: any = {};
    try {
      body = await req.json();
    } catch {
      body = {};
    }

    const {
      portfolioName,
      yaml,
      debateRounds,
      debaterAPrompt,
      debaterBPrompt,
      judgePrompt,
      skipRun,
    } = body || {};

    const parsedRounds =
      typeof debateRounds === "number" && Number.isFinite(debateRounds)
        ? Math.max(1, Math.min(12, Math.floor(debateRounds)))
        : undefined;

    console.log("[scenario-gen] incoming params", {
      portfolioName,
      hasYaml: Boolean(typeof yaml === "string" && yaml.trim().length),
      debateRounds: parsedRounds,
      skipRun: Boolean(skipRun),
    });

    const projectRoot = path.join(process.cwd(), "..");
    const backendDir = path.join(projectRoot, "backend", "mad_debate");
    const configPath = path.join(backendDir, "config.yaml");
    const encoder = new TextEncoder();

    const stream = new ReadableStream({
      start(controller) {
        const perRunProgress = new Map<number, number>();
        let knownTotalRuns: number | undefined;
        const send = (payload: unknown) => {
          const chunk = JSON.stringify(payload) + "\n";
          controller.enqueue(encoder.encode(chunk));
        };
        const handleLine = (line: string, channel: LoggerChannel | "system") => {
          if (!line) return;
          send({ type: "log", channel, message: line });
          const stage = parseMadStageLine(line);
          if (stage) {
            if (typeof stage.totalRuns === "number") {
              knownTotalRuns = stage.totalRuns;
            } else if (typeof knownTotalRuns === "number") {
              stage.totalRuns = knownTotalRuns;
            }
            const totalForCalc = stage.totalRuns ?? knownTotalRuns ?? 1;
            const enriched = enrichStageProgress(stage, perRunProgress, totalForCalc);
            send({ type: "stage", data: enriched });
          }
        };
        const processMessage = (message: string, channel: LoggerChannel | "system" = "stdout") => {
          if (!message) return;
          const lines = message.split(/\r?\n/);
          for (const raw of lines) {
            const trimmed = raw.trim();
            if (trimmed) {
              handleLine(trimmed, channel);
            }
          }
        };

        (async () => {
          try {
            if (!skipRun) {
              await runMadDebateScript(
                {
                  backendDir,
                  configPath,
                  debateRounds: parsedRounds,
                  portfolioName: typeof portfolioName === "string" ? portfolioName : undefined,
                  yaml: typeof yaml === "string" ? yaml : undefined,
                  debaterAPrompt: typeof debaterAPrompt === "string" ? debaterAPrompt : undefined,
                  debaterBPrompt: typeof debaterBPrompt === "string" ? debaterBPrompt : undefined,
                  judgePrompt: typeof judgePrompt === "string" ? judgePrompt : undefined,
                },
                {
                  logger: (entry) => processMessage(entry.message, entry.channel),
                }
              );
            } else {
              processMessage("skipRun flag set — reusing existing MAD artifacts", "system");
            }

            processMessage("MAD script complete. Loading artifacts…", "system");
            const payload = await loadMadArtifacts(backendDir);
            send({ type: "result", data: payload });
          } catch (err: any) {
            const msg = `MAD scenario generation failed: ${String(err)}`;
            console.error(msg);
            send({ type: "error", message: msg });
          } finally {
            controller.close();
          }
        })();
      },
      cancel() {
        console.log("[scenario-gen] client cancelled MAD stream");
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "application/x-ndjson",
        "Cache-Control": "no-cache",
      },
    });
  } catch (err: any) {
    console.error("Error in MAD scenario generation route:", err);
    return NextResponse.json(
      {
        error: "Failed to start MAD scenario generation",
        detail: String(err),
      },
      { status: 500 }
    );
  }
}
