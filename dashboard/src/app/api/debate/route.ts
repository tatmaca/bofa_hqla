// src/app/api/scenario-gen/route.ts
import { NextResponse } from "next/server";
import { exec } from "child_process"; // kept for later when we re‑enable live runs
import { readFile, readdir } from "fs/promises";
import path from "path";

// Helper to run a shell command and wait for it
// (not used in offline mode, but kept for future wiring to the live debate script)
function runCommand(cmd: string, cwd: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = exec(cmd, { cwd }, (err) => {
      if (err) return reject(err);
      resolve();
    });

    // optional: log stderr for debugging
    child.stderr?.on("data", (data) => {
      console.error("[MAD stderr]", data.toString());
    });
  });
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
function extractLatestRoundFromTranscript(jsonlText: string, runNumber: number) {
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

      return {
        role: roleLabel(e.speaker),
        text,
        round: effectiveRound,
        run: runNumber,
      };
    });

  return debate;
}

export async function POST(req: Request) {
  try {
    // Read UI params (still mostly informational in this offline mode)
    let body: any = {};
    try {
      body = await req.json();
    } catch {
      body = {};
    }

    const { portfolioName, yaml, debateRounds } = body;

    console.log("[scenario-gen] incoming params (OFFLINE)", {
      portfolioName,
      hasYaml: Boolean(yaml && String(yaml).trim()),
      debateRounds,
    });

    // projectRoot = bofa_hqla/
    const projectRoot = path.join(process.cwd(), "..");
    // backend / mad_debate (this folder contains config.yaml, data/, temp.txt, etc.)
    const backendDir = path.join(projectRoot, "backend", "mad_debate");

    // 1) Load the last scenarios JSON produced by the MAD script.
    //    Preferred: /tmp/mad_scenarios.json (when you run with --out /tmp/mad_scenarios.json --format json)
    //    Fallback:  backend data/scenarios/out.jsonl (JSON Lines, one scenario per line)
    let scenarios: any[] = [];
    const outPath = "/tmp/mad_scenarios.json";

    try {
      const rawJson = await readFile(outPath, "utf-8");
      const parsed = JSON.parse(rawJson);
      scenarios = Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.error(
        "[scenario-gen] Could not read /tmp/mad_scenarios.json; trying data/scenarios/out.jsonl instead.",
        e
      );
      try {
        const outJsonlPath = path.join(
          backendDir,
          "data",
          "scenarios",
          "out.jsonl"
        );
        const rawJsonl = await readFile(outJsonlPath, "utf-8");
        const lines = rawJsonl.split(/\r?\n/);
        const parsedLines: any[] = [];
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          try {
            parsedLines.push(JSON.parse(trimmed));
          } catch (err) {
            console.error(
              "[scenario-gen] Failed to parse JSONL line in out.jsonl:",
              err
            );
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

    // 2) Load the debate: prefer transcript_run_*.jsonl (full reasoning), fall back to temp.txt previews.
    let debate: { role: string; text: string; round: number; run?: number }[] = [];

    try {
      const scenariosDir = path.join(backendDir, "data", "scenarios");
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

      // Read all transcript files and aggregate debates
      for (const fileName of transcriptFiles) {
        const match = fileName.match(/transcript_run_(\d+)\.jsonl/);
        if (!match) continue;
        const runNumber = parseInt(match[1], 10);
        const transcriptPath = path.join(scenariosDir, fileName);
        const jsonlText = await readFile(transcriptPath, "utf-8");
        const runDebate = extractLatestRoundFromTranscript(jsonlText, runNumber);
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

    // If there is no explicit JUDGE speaker in the transcript, synthesize a Judge
    // message from the final scenarios so the UI always has a judge bubble.
    const hasJudge = debate.some((m) => m.role === "Judge");
    if (!hasJudge && scenarios.length) {
      const maxRound = debate.reduce(
        (max, m) => (m.round > max ? m.round : max),
        0
      );
      const judgeRound = maxRound ? maxRound + 1 : 1;

      const judgeText =
        "Judge-selected scenarios:\n\n```json\n" +
        JSON.stringify(scenarios, null, 2) +
        "\n```";

      debate.push({
        role: "Judge",
        text: judgeText,
        round: judgeRound,
      });
    }

    // Shape: { debate, scenarios } — exactly what runScenarioGen on the UI expects
    return NextResponse.json({ debate, scenarios });
  } catch (err: any) {
    console.error("Error in offline MAD scenario generation route:", err);
    return NextResponse.json(
      {
        error: "Failed to load offline MAD scenarios / debate",
        detail: String(err),
      },
      { status: 500 }
    );
  }
}