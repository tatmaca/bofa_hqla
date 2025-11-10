// src/app/api/scenario-gen/route.ts
import { NextResponse } from "next/server";
import { exec } from "child_process"; // kept for later when we re‑enable live runs
import { readFile } from "fs/promises";
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

/**
 * Parse the offline MAD log (temp.txt) and pull out the most recent
 * Proponent / Devil's Advocate round as a lightweight "chat" transcript.
 *
 * We look for lines like:
 *   [RUN#1 R2-A] Output preview:
 *   [RUN#1 R2-B] Output preview:
 * and grab everything after each marker up to the next marker (or EOF).
 */
function extractLatestRoundFromLog(logText: string) {
  type Side = "A" | "B";
  const segments: { round: number; side: Side; start: number; end: number }[] = [];

  const re = /R(\d+)-(A|B)] Output preview:/g;
  let m: RegExpExecArray | null;

  while ((m = re.exec(logText)) !== null) {
    const round = parseInt(m[1], 10);
    const side = m[2] as Side;
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

  // Find the highest round number we saw in the log
  const latestRound = segments.reduce(
    (max, s) => (s.round > max ? s.round : max),
    segments[0].round
  );

  const latestSegs = segments.filter((s) => s.round === latestRound);

  // Map into the UI "debate" shape the page.tsx expects:
  //   { role: "Proponent" | "Devil's Advocate", text: string, round: number }
  const debate = latestSegs.map((s) => {
    const raw = logText.slice(s.start, s.end).trim();

    // Trim very long blobs so the preview doesn't explode
    const maxLen = 2000;
    const text =
      raw.length > maxLen ? raw.slice(0, maxLen) + "\n…[truncated]" : raw;

    const role =
      s.side === "A" ? ("Proponent" as const) : ("Devil's Advocate" as const);

    return {
      role,
      text,
      round: s.round,
    };
  });

  // Sort so Proponent then Devil's Advocate (if both present)
  debate.sort((a, b) => a.round - b.round || a.role.localeCompare(b.role));

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

    // 1) Load the last scenarios JSON (written by a previous run of debate_scenarios.py)
    const outPath = "/tmp/mad_scenarios.json";
    let scenarios: any[] = [];
    try {
      const rawJson = await readFile(outPath, "utf-8");
      const parsed = JSON.parse(rawJson);
      // script writes a JSON array in --format json mode
      scenarios = Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.error(
        "[scenario-gen] Could not read /tmp/mad_scenarios.json; returning empty scenarios.",
        e
      );
      scenarios = [];
    }

    // 2) Load the offline debate log and extract the latest round as a chat
    const tempLogPath = path.join(backendDir, "temp.txt");
    let debate: { role: string; text: string; round: number }[] = [];
    try {
      const logText = await readFile(tempLogPath, "utf-8");
      debate = extractLatestRoundFromLog(logText);
    } catch (e) {
      console.error(
        "[scenario-gen] Could not read temp.txt for offline debate; returning empty debate.",
        e
      );
      debate = [];
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