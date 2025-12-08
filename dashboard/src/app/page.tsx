"use client";

import React, { useEffect, useMemo, useState } from "react";
import Image from "next/image"; // (Optional) Next Image for real logos
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { fs } from "fs";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  CheckCircle2,
  PlayCircle,
  Activity,
  Newspaper,
  Settings,
  ChevronRight,
  Download,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { motion } from "framer-motion";

// --- Replace these with real API calls / events wired to your Python backend --- //
function fakeWait(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

function cleanStageLine(line?: string | null) {
  if (!line) return "";
  let txt = line.replace(/^\d{2}:\d{2}:\d{2}\s*/, "");
  txt = txt.replace(/^\[[A-Z]+\]\s*/, "");
  txt = txt.replace(/^\[[^\]]+\]\s*/, "");
  txt = txt.replace(/\[INFO]\s*/i, "");
  txt = txt.replace(/Output preview:\s*/i, "");
  return txt.trim();
}

const API_BASE = "http://127.0.0.1:8000";

async function runScenarioGen(
  setter: (s: any) => void,
  params: {
    portfolioName: string;
    yaml: string;
    debateRounds: number;
    debateRuns?: number;
    debaterAPrompt: string;
    debaterBPrompt: string;
    judgePrompt: string;
    offlineSample?: boolean;
    newsContext?: string;
  },
) {
  const {
    portfolioName,
    yaml,
    debateRounds,
    debaterAPrompt,
    debateRuns,
    debaterBPrompt,
    judgePrompt,
    offlineSample,
    newsContext,
  } = params;
  const totalMessages = Math.max(
    1,
    (debateRuns || 1) * ((debateRounds || 1) * 2 + 1),
  );

  // Reset state, clear old debate + scenarios
  setter((s: any) => ({
    ...s,
    status: "running",
    pct: 10,
    liveStage: null,
    totalRuns: debateRuns || null,
    logs: [
      ...s.logs,
      `Calling MAD backend for "${portfolioName}" (${debateRounds} rounds${offlineSample ? ", offline sample" : ""}${
        newsContext ? ", news context applied" : ""
      })…`,
    ],
    liveDebate: {},
    liveRunOrder: [],
    activeLiveRun: null,
    expectedMessages: totalMessages,
    seenMessages: 0,
    output: {
      ...(s.output || {}),
      debate: [],
      scenarios: [],
      scenarioMatrix: [],
    },
  }));

  const appendLog = (incoming: string, channel?: string) => {
    const raw = (incoming ?? "").toString().trimEnd();
    if (!raw) return;
    const prefix = channel && channel !== "stdout" ? `[${channel}] ` : "";
    setter((s: any) => ({
      ...s,
      logs: [...(s.logs || []), `${prefix}${raw}`].slice(-120),
      pct: s.status === "running" ? Math.min(s.pct + 3, 96) : s.pct,
    }));
  };

  const applyStage = (stage: any) => {
    if (!stage || typeof stage !== "object") return;
    setter((s: any) => {
      const rawStageText = typeof stage.text === "string" ? stage.text : "";
      const stageMessage =
        typeof stage.message === "string" ? stage.message : "";
      const parsedStage = extractScenariosAndStripJson(
        stageMessage || rawStageText,
      );
      const stageText = parsedStage.cleanText || cleanStageLine(rawStageText);
      const rawSegments = collectJsonSegments(stageMessage || rawStageText);
      const rawMatrixText = rawSegments.length
        ? rawSegments.join("\n\n")
        : undefined;
      let entryScenarios =
        (Array.isArray(stage.scenarios) && stage.scenarios.length
          ? stage.scenarios
          : parsedStage.scenarios) || [];
      if (!entryScenarios.length && rawSegments.length) {
        const fallback = rawSegments.flatMap((segment) =>
          tryParseScenarioPayload(segment),
        );
        if (fallback.length) {
          entryScenarios = fallback;
        }
      }
      const totalRuns =
        typeof stage.totalRuns === "number" ? stage.totalRuns : undefined;
      const expected = s.expectedMessages || 0;
      const increment =
        stage.phase === "debater" || stage.phase === "judge" ? 1 : 0;
      const newSeen = Math.min(
        (s.seenMessages || 0) + increment,
        expected || Number.MAX_SAFE_INTEGER,
      );
      const progressFromMessages =
        expected > 0
          ? Math.min(98, Math.round((newSeen / expected) * 90) + 5)
          : s.pct;
      const runKey =
        typeof stage.run === "number" && Number.isFinite(stage.run)
          ? stage.run
          : 1;
      const baseLiveDebate = Array.isArray(s.liveDebate)
        ? { 1: s.liveDebate }
        : s.liveDebate && typeof s.liveDebate === "object"
          ? { ...s.liveDebate }
          : {};
      const existingRunDebate = Array.isArray(baseLiveDebate[runKey])
        ? baseLiveDebate[runKey]
        : [];
      const entryText = stageMessage || cleanStageLine(rawStageText);
      if (entryText && (stage.speakerLabel || stage.phase)) {
        const entry = {
          role:
            stage.speakerLabel ||
            (stage.phase ? stage.phase.toUpperCase() : "Update"),
          text: entryText,
          round: stage.round ?? null,
          run: stage.run ?? null,
          scenarios: entryScenarios,
          rawMatrixText,
          matrixId: entryScenarios.length
            ? `${runKey}-${stage.round ?? 0}-${Date.now()}`
            : undefined,
        };
        baseLiveDebate[runKey] = [...existingRunDebate, entry].slice(-40);
      }
      let liveRunOrder = Array.isArray(s.liveRunOrder)
        ? [...s.liveRunOrder]
        : [];
      if (!liveRunOrder.includes(runKey)) {
        liveRunOrder = [...liveRunOrder, runKey];
      }
      return {
        ...s,
        liveStage: stageText || s.liveStage,
        totalRuns: totalRuns ?? s.totalRuns,
        pct: Math.max(s.pct, progressFromMessages),
        liveDebate: baseLiveDebate,
        liveRunOrder,
        activeLiveRun: runKey,
        expectedMessages: expected,
        seenMessages: newSeen,
      };
    });
  };

  const applyResult = (data: any) => {
    const rawDebate = Array.isArray(data?.debate) ? data.debate : [];
    const debate = rawDebate.map((m: any) => ({
      role: m.role || "Proponent",
      text: m.text || "",
      round: typeof m.round === "number" ? m.round : null,
      run: typeof m.run === "number" ? m.run : null,
      scenarios: Array.isArray(m.scenarios) ? m.scenarios : [],
    }));

    const sortedDebate = [...debate].sort((a, b) => {
      const arun = a.run ?? 0;
      const brun = b.run ?? 0;
      if (arun !== brun) return arun - brun;

      const ar = a.round ?? 0;
      const br = b.round ?? 0;
      if (ar !== br) return ar - br;

      const orderForRole = (role: string) => {
        const rl = (role || "").toLowerCase();
        if (rl.includes("proponent")) return 0;
        if (rl.includes("devil")) return 1;
        if (rl.includes("judge")) return 2;
        return 3;
      };
      return orderForRole(a.role) - orderForRole(b.role);
    });

    const rawScenarios = Array.isArray(data?.scenarios) ? data.scenarios : [];
    const scenarioMatrix = rawScenarios
      .map((sc: any) => (sc && typeof sc === "object" ? sc : null))
      .filter(Boolean);
    const scenarios = scenarioMatrix.map((sc: any, idx: number) => {
      const name = sc.Scenario || sc.name || `Scenario ${idx + 1}`;
      const p =
        typeof sc.Probability === "number"
          ? sc.Probability
          : typeof sc.p === "number"
            ? sc.p
            : 0;
      const channels = sc.ImpactChannels || sc.channels || [];
      const rationale = sc.Rationale || sc.rationale || "";
      const probability = typeof p === "number" && p > 1 ? p / 100 : p;
      return {
        name,
        p: probability,
        channels: Array.isArray(channels) ? channels : [],
        rationale,
      };
    });

    const metadata = data?.metadata || null;
    setter((s: any) => ({
      ...s,
      status: "done",
      pct: 100,
      logs: [...s.logs, "Loaded live MAD debate + scenarios."],
      liveStage: "MAD judge consolidated scenarios.",
      liveDebate: {},
      liveRunOrder: [],
      activeLiveRun: null,
      expectedMessages: 0,
      seenMessages: 0,
      output: {
        ...(s.output || {}),
        debate: sortedDebate,
        scenarios,
        scenarioMatrix,
        metadata,
      },
    }));
    return { scenarios, scenarioMatrix, debate: sortedDebate, metadata };
  };

  try {
    const res = await fetch("/api/debate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify({
        portfolioName,
        yaml,
        debateRounds,
        debateRuns,
        debaterAPrompt,
        debaterBPrompt,
        judgePrompt,
        offlineSample: offlineSample ? true : undefined,
        newsContext,
      }),
    });

    if (!res.ok || !res.body) {
      throw new Error(`HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finalResult: {
      scenarios: any[];
      scenarioMatrix: any[];
      debate: any[];
    } | null = null;

    while (true) {
      const { value, done } = await reader.read();
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        let idx = buffer.indexOf("\n");
        while (idx !== -1) {
          const rawLine = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 1);
          const line = rawLine.trim();
          if (line) {
            let evt: any;
            try {
              evt = JSON.parse(line);
            } catch {
              evt = null;
            }
            if (evt) {
              if (evt.type === "log") {
                appendLog(String(evt.message ?? ""), evt.channel);
              } else if (evt.type === "stage") {
                applyStage(evt.data);
              } else if (evt.type === "error") {
                await reader.cancel();
                throw new Error(evt.message || "MAD run failed");
              } else if (evt.type === "result") {
                finalResult = applyResult(evt.data);
              }
            }
          }
          idx = buffer.indexOf("\n");
        }
      }
      if (done) break;
    }

    if (!finalResult) {
      throw new Error("MAD run completed without a result payload.");
    }

    return finalResult;
  } catch (err: any) {
    console.error("runScenarioGen error", err);
    setter((s: any) => ({
      ...s,
      status: "idle",
      pct: 0,
      liveStage: `MAD run failed.`,
      liveDebate: {},
      liveRunOrder: [],
      activeLiveRun: null,
      expectedMessages: 0,
      seenMessages: 0,
      logs: [
        ...s.logs,
        `Scenario generation failed: ${String(err?.message || err)}`,
      ],
      output: {
        ...(s.output || {}),
        debate: s.output?.debate || [],
        scenarios: s.output?.scenarios || [],
        scenarioMatrix: s.output?.scenarioMatrix || [],
      },
    }));
    return null;
  }
}

async function runImpact(setter: (s: any) => void, scenarioMatrix: any[] = []) {
  setter((s: any) => ({
    ...s,
    status: "running",
    pct: 15,
    logs: [...s.logs, "Shock buckets → duration ladder…"],
  }));
  await fakeWait(600);
  setter((s: any) => ({
    ...s,
    pct: 56,
    logs: [...s.logs, "ΔLCR/ΔNSFR computed (Basel caps)"],
  }));
  await fakeWait(600);

  const matrix = Array.isArray(scenarioMatrix) ? scenarioMatrix : [];
  const sliceCount = matrix.length > 12 ? 12 : matrix.length;
  const metrics = matrix.length
    ? matrix.slice(0, sliceCount).map((sc: any, idx: number) => {
        const name = sc.Scenario || sc.name || `Scenario ${idx + 1}`;
        const probRaw =
          typeof sc.Probability === "number"
            ? sc.Probability
            : typeof sc.p === "number"
              ? sc.p
              : 0;
        const prob = probRaw > 1 ? probRaw / 100 : probRaw;
        const signal = (prob - 0.35) * 20;
        const dLCR = Number((signal * -1.2).toFixed(1));
        const dNSFR = Number((signal * -0.6).toFixed(1));
        const dNII = Number(((prob - 0.25) * 6).toFixed(2));
        const note =
          sc.Description ||
          sc.Rationale ||
          sc.Assumptions ||
          "See scenario matrix for details.";
        return {
          scenario: name,
          dLCR,
          dNSFR,
          dNII,
          note,
          riskScore: Math.round(Math.abs(signal) + prob * 10),
        };
      })
    : [
        {
          scenario: "Hawkish Fed Surprise",
          dLCR: -6,
          dNSFR: -1,
          dNII: +3.1,
          note: "Reprice short-end; sell 30y MBS",
          riskScore: 6,
        },
        {
          scenario: "Deposit Outflow Scare",
          dLCR: -14,
          dNSFR: -3,
          dNII: -1.0,
          note: "Raise Level 1; runoff factors ↑",
          riskScore: 14,
        },
        {
          scenario: "Soft-Landing Grind",
          dLCR: +2,
          dNSFR: +1,
          dNII: +1.4,
          note: "Carry OK; watch issuance",
          riskScore: -2,
        },
        {
          scenario: "MBS Basis Blowout",
          dLCR: -4,
          dNSFR: 0,
          dNII: -2.2,
          note: "Trim 2A/2B; convexity risk",
          riskScore: 4,
        },
        {
          scenario: "Treasury Supply Shock",
          dLCR: -7,
          dNSFR: -2,
          dNII: -0.9,
          note: "Bills up; term premium ↑",
          riskScore: 7,
        },
        {
          scenario: "Credit Risk Off",
          dLCR: -9,
          dNSFR: -2,
          dNII: -1.6,
          note: "HY/IG OAS widen; rotate to L1",
          riskScore: 9,
        },
      ];

  setter((s: any) => ({
    ...s,
    status: "done",
    pct: 100,
    logs: [...s.logs, "Attribution + NII done"],
    output: { metrics, source: "matrix" },
  }));
}

async function runOptimize(setter: (s: any) => void) {
  setter((s: any) => ({
    ...s,
    status: "running",
    pct: 12,
    logs: [...s.logs, "Building guardrails (L2 caps, LCR≥110%)…"],
  }));
  await fakeWait(700);
  setter((s: any) => ({
    ...s,
    pct: 64,
    logs: [...s.logs, "Solving QP for risk-adjusted NII…"],
  }));
  await fakeWait(700);
  setter((s: any) => ({
    ...s,
    status: "done",
    pct: 100,
    logs: [...s.logs, "Trade list v1 posted."],
    output: {
      trades: [
        {
          action: "BUY",
          instr: "UST 2y",
          size: "+$500mm",
          reason: "LCR support; bear-steepener hedge",
        },
        {
          action: "SELL",
          instr: "MBS 30y 2.0%",
          size: "-$300mm",
          reason: "Neg. convexity under stress",
        },
        {
          action: "HOLD",
          instr: "UST Bills",
          size: "–",
          reason: "Cash buffer for outflows",
        },
      ],
    },
  }));
}

async function runMonitor(setter: (s: any) => void) {
  setter((s: any) => ({
    ...s,
    status: "running",
    pct: 18,
    logs: [...s.logs, "Scraping FOMC/Fed-speak, UST auction, geopolitics…"],
  }));
  await fakeWait(600);
  setter((s: any) => ({
    ...s,
    pct: 70,
    logs: [...s.logs, "Classified: ‘hawkish tilt’ → scenario score +0.1"],
  }));
  await fakeWait(600);
  setter((s: any) => ({
    ...s,
    status: "done",
    pct: 100,
    logs: [...s.logs, "Briefing drafted + alerts queued"],
    output: {
      brief:
        "Hawkish Fed language nudged bear-steepener risk; suggest +$200mm 2y add, monitor MBS basis.",
    },
  }));
}

const Step = ({
  index,
  title,
  desc,
  status,
}: {
  index: number;
  title: string;
  desc: string;
  status: "idle" | "running" | "done";
}) => {
  const color =
    status === "done"
      ? "bg-emerald-500"
      : status === "running"
        ? "bg-blue-500"
        : "bg-muted";
  const Icon = status === "done" ? CheckCircle2 : PlayCircle;
  return (
    <div className="flex items-start gap-3">
      <div
        className={`mt-1 h-6 w-6 rounded-full flex items-center justify-center text-white ${color}`}
      >
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <div className="flex items-center gap-2">
          <p className="font-semibold">
            {index}. {title}
          </p>
          {status === "done" && <Badge variant="secondary">complete</Badge>}
          {status === "running" && <Badge>running</Badge>}
        </div>
        <p className="text-sm text-muted-foreground">{desc}</p>
      </div>
    </div>
  );
};

export default function HqlaE2EDashboard() {
  const [portfolioName, setPortfolioName] = useState("Example HQLA Portfolio");
  const [yaml, setYaml] = useState(
    "# shocks.yaml\nmove_index: 110\nyield_curve: bear_steepener\ncredit_spreads: { ig_oas: +15, hy_oas: +45 }\n",
  );
  const [yieldCurve, setYieldCurve] = useState([]); // Prepare table data safely before rendering

  const scenarioCurves = useMemo(() => {
    if (!yieldCurve || yieldCurve.length === 0) return {};

    const n = yieldCurve.length;
    const midIndex = Math.floor(n / 2);

    // Compute mean rate
    const meanRate = yieldCurve.reduce((sum, p) => sum + p.rate, 0) / n;

    return {
      "level-up": yieldCurve.map((p) => ({ ...p, rate: p.rate + 0.01 })),
      "level-down": yieldCurve.map((p) => ({ ...p, rate: p.rate - 0.01 })),

      steepening: yieldCurve.map((p, i) => {
        const factor = (i - midIndex) / (n - 1);
        return { ...p, rate: p.rate + factor * 0.01 };
      }),

      flattening: yieldCurve.map((p) => {
        // nudge each rate toward the mean by a fixed fraction
        const adjustment = (meanRate - p.rate) * 0.5; // 0.5 = 50% of difference
        return { ...p, rate: p.rate + adjustment };
      }),
    };
  }, [yieldCurve]);

  const [scenario, setScenario] = useState({
    status: "idle",
    pct: 0,
    logs: [],
    output: null,
  } as any);
  const [impact, setImpact] = useState({
    status: "idle",
    pct: 0,
    logs: [],
    output: null,
  } as any);
  const [opt, setOpt] = useState({
    status: "idle",
    pct: 0,
    logs: [],
    output: null,
  } as any);
  const [mon, setMon] = useState({
    status: "idle",
    pct: 0,
    logs: [],
    output: null,
  } as any);
  const [yieldScenario, setYieldScenario] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [selectedDebateRun, setSelectedDebateRun] = useState<number | null>(
    null,
  );
  const [offlineMode, setOfflineMode] = useState(false);
  const [activeNewsArticle, setActiveNewsArticle] = useState<any | null>(null);
  const [attributionDate, setAttributionDate] = useState("2025-11-27");
  const [attributionMode, setAttributionMode] = useState("all");

  // Debate configuration (mirrors Python MAD config high-level knobs)
  const [debateRounds, setDebateRounds] = useState(3);
  const [debateRuns, setDebateRuns] = useState(5);
  const [debaterAPrompt, setDebaterAPrompt] = useState(
    `You are a **Senior Treasury Strategist at Bank of America (BoA)**.  BoA is a US G-SIB with ~$2.5T assets, $1T+ deposits, diversified consumer/commercial franchises, and global markets desks across USD/EUR/GBP/LatAm/Asia.  The HQLA stack spans USTs, Agencies/MBS, munis, GBP/EUR sovereigns, and cash, funded via retail/wealth deposits, wholesale term debt, FHLB, repo, and CP.  Protect BoA’s LCR ≥ internal targets, NSFR stability, OCI, and earnings-at-risk.

  1. **Objective:**  
    Propose 3–5 distinct 6-month scenarios that materially affect BoA’s HQLA valuations, capital ratios, liquidity metrics, or NII.

  2. **Shocks (ALL quantitative):**  
    - Interest-rate level and curve moves (USD focus; cite cross-currency spillovers when relevant).  
    - Credit spreads (IG/HY/financials), MBS basis, sovereign spreads.  
    - Deposits/funding: retail beta, wealth runoff, wholesale spread moves, secured funding costs.  
    - Regulatory/policy actions: Basel Endgame, GSIB surcharge, TLAC, liquidity add-ons.

  3. **Rationale & Channels:**  
    Tie each scenario to BoA-relevant drivers (consumer balance sheets, CRE, commodities, geopolitics, Treasury issuance).  Cite at least one channel from Rates/Curve/Credit/MBS/Deposits/Regulation/Commodity Prices.

  4. **Probabilities:**  
    Assign probabilities summing to ~1 across the set with justification.

  5. **Portfolio Awareness:**  
    Reference BoA’s Level 1/2 mix, duration/convexity, Level 2 caps, OCI sensitivity, and funding stack.

  6. **Formatting:**  
    Output a strict JSON array. Every element must include: ["Scenario","Description","Probability","Rationale","ImpactChannels","Shocks","MetricsDelta","TradeList","Assumptions"].  Shocks/Metrics must be numeric; TradeList must list concrete BoA actions (e.g., "Add $1bn bills via repo").`,
  );
  const [debaterBPrompt, setDebaterBPrompt] = useState(
    `You are the **Devil’s Advocate / soft-landing strategist for Bank of America**.  Respond to the Proponent by emphasizing benign outcomes while still referencing BoA’s HQLA exposures and funding stack.

  1. **Counter-Framing:** Challenge risk-off cases by highlighting controlled inflation, gradual easing, resilient consumers/SMEs, and diversification of BoA’s deposits/trading flows.

  2. **Constructive Scenarios:** Provide your own quantified scenarios (same schema) that favor curve bull-steepeners/flatteners, tighter spreads, stable deposit betas, or regulatory relief that benefits BoA’s Level 1/2 mix.

  3. **Portfolio Impact:** Show how BoA can redeploy liquidity (e.g., add Agency MBS, rotate into munis/sovereigns, term out wholesale funding) while protecting OCI/NII.

  4. **Formatting:** Return a JSON array identical to the Proponent’s structure with concrete BoA trades/funding actions in TradeList.`,
  );
  const [judgePrompt, setJudgePrompt] = useState(
    `You are the **Chief Risk Officer for Bank of America’s HQLA Committee**.  
  Review the Proponent and Devil’s Advocate submissions and publish the final scenario set BoA will use for capital, liquidity, and NII modeling.

  - Enforce realism (6-month horizon, quantitative shocks, probabilities ≈ 1).  
  - Keep 3–6 scenarios spanning stress/base/benign outcomes and touching BoA-relevant channels (Rates, Curve, Credit, MBS, Deposits, Regulation, Commodity Prices).  
  - Ensure TradeList items are feasible for BoA (balance sheet, funding mix, regulatory constraints).  
  - Output ONLY the strict JSON array matching the schema (no commentary, no markdown).`,
  );

  // Popups
  const [openScenario, setOpenScenario] = useState(false);
  const [openDebate, setOpenDebate] = useState(false);
  const [openImpact, setOpenImpact] = useState(false);
  const [openOpt, setOpenOpt] = useState(false);
  const [openMon, setOpenMon] = useState(false);
  const [openDebateParams, setOpenDebateParams] = useState(false);
  const [matrixModal, setMatrixModal] = useState<{
    title: string;
    scenarios: any[];
    prevScenarios?: any[];
    rawMatrixText?: string;
  } | null>(null);

  const pipelinePct = useMemo(() => {
    const pcs = [
      scenario.pct || 0,
      impact.pct || 0,
      opt.pct || 0,
      mon.pct || 0,
    ];
    return Math.round(pcs.reduce((a, b) => a + b, 0) / pcs.length);
  }, [scenario, impact, opt, mon]);

  const worst = useMemo(() => {
    const rows = impact.output?.metrics || [];
    if (!rows.length) return null;
    const sorted = [...rows].sort(
      (a: any, b: any) => (b.riskScore || 0) - (a.riskScore || 0),
    );
    return sorted[0]; // highest riskScore == worst ΔLCR
  }, [impact]);

  const [portfolioFile, setPortfolioFile] = useState<File | null>(null);
  const [yieldCurveFile, setYieldCurveFile] = useState<File | null>(null);
  const [portfolioSummary, setPortfolioSummary] = useState<any>(null);
  const [scenarioSummary, setScenarioSummary] = useState<any>(null);
  const [loadingPortfolio, setLoadingPortfolio] = useState(false);
  const [loadingCurve, setLoadingCurve] = useState(false);
  const allDone = [scenario, impact, opt, mon].every(
    (s) => s.status === "done",
  );
  const tableData = scenarioSummary
    ? scenarioSummary.scenario // scenario selected
    : portfolioSummary?.assets; // realized onlyieldCurve] = useState([]);

  async function handleUploadPortfolio() {
    if (!portfolioFile) return;
    setLoadingPortfolio(true);
    const formData = new FormData();
    formData.append("file", portfolioFile);
    try {
      await fetch("http://localhost:8000/upload-portfolio", {
        method: "POST",
        body: formData,
      });
      //await handlePricePortfolio(); // auto-price after upload
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingPortfolio(false);
    }
  }

  async function handleUploadYieldCurve() {
    if (!yieldCurveFile) return;
    setLoadingCurve(true);
    const formData = new FormData();
    formData.append("file", yieldCurveFile);
    try {
      await fetch("http://localhost:8000/upload-yield-curve", {
        method: "POST",
        body: formData,
      });
      const c = await fetch("http://localhost:8000/yield-curve/current");
      const curveData = await c.json();
      setYieldCurve(curveData.curve);
      await handlePricePortfolio(); // auto-price after curve upload
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCurve(false);
    }
  }

  async function handlePricePortfolio() {
    const res = await fetch("http://localhost:8000/price-portfolio");
    if (!res.ok) return console.error(await res.json());
    const data = await res.json();
    setPortfolioSummary(data);
  }

  const openAttributionPage = () => {
    const fallbackDate = new Date().toISOString().slice(0, 10);
    const dateParam = attributionDate || fallbackDate;
    const url = `${API_BASE}/attribution/html?date=${dateParam}&image_mode=${attributionMode}&embed_images=false`;
    if (typeof window !== "undefined") {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  // Function to handle scenario pricing
  async function handleScenarioPricing(selectedScenarioKey: string | null) {
    if (selectedScenarioKey === null) {
      // Realized selected: reset scenario summary
      setScenarioSummary(null);
      console.log("Realized curve selected — using original pricing");
      return;
    }

    // 1. Get the shocked yield curve
    const shockedCurve = scenarioCurves[selectedScenarioKey];
    if (!shockedCurve || shockedCurve.length === 0) return;

    try {
      // 2. Upload scenario curve to backend
      const uploadRes = await fetch(
        "http://localhost:8000/upload-yield-curve/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(shockedCurve),
        },
      );
      const uploadData = await uploadRes.json();
      console.log("Scenario curve upload:", uploadData);

      // 3. Price portfolio using scenario curve
      const priceRes = await fetch(
        "http://localhost:8000/price-portfolio?is_scenario=true",
      );
      if (!priceRes.ok) {
        console.error(await priceRes.json());
        return;
      }
      const priceData = await priceRes.json();
      console.log("Scenario portfolio pricing:", priceData);

      // 4. Store scenario portfolio summary separately
      setScenarioSummary(priceData);
    } catch (err) {
      console.error("Scenario pricing error:", err);
    }
  }

  // Debate run selection logic
  const debateMessages = (scenario.output?.debate || []) as any[];
  const historicalRuns = Array.from(
    new Set(debateMessages.map((m) => (typeof m.run === "number" ? m.run : 1))),
  ).sort((a, b) => a - b);
  const liveRunOrder = Array.isArray(scenario.liveRunOrder)
    ? scenario.liveRunOrder.filter((r: any) => typeof r === "number")
    : [];
  const runSet = new Set<number>();
  historicalRuns.forEach((r) => runSet.add(r));
  liveRunOrder.forEach((r: number) => {
    if (typeof r === "number") runSet.add(r);
  });
  if (typeof scenario.activeLiveRun === "number") {
    runSet.add(scenario.activeLiveRun);
  }
  const availableRuns = Array.from(runSet).sort((a, b) => a - b);
  const defaultRun =
    scenario.status === "running" && typeof scenario.activeLiveRun === "number"
      ? scenario.activeLiveRun
      : availableRuns.length
        ? availableRuns[availableRuns.length - 1]
        : null;
  const activeRun = selectedDebateRun ?? defaultRun;
  const liveDebateByRun = Array.isArray(scenario.liveDebate)
    ? { 1: scenario.liveDebate }
    : scenario.liveDebate && typeof scenario.liveDebate === "object"
      ? scenario.liveDebate
      : {};
  const liveDebateForRun =
    activeRun != null && Array.isArray(liveDebateByRun[activeRun])
      ? liveDebateByRun[activeRun]
      : [];
  const activeDebate =
    activeRun == null
      ? debateMessages
      : debateMessages.filter(
          (m) => (typeof m.run === "number" ? m.run : 1) === activeRun,
        );
  const previewDebate =
    scenario.status === "running" && liveDebateForRun.length
      ? liveDebateForRun
      : activeDebate;
  const newsOutput = mon.output;
  const newsSummary = newsOutput?.summary;
  const newsBuckets = Array.isArray(newsOutput?.buckets)
    ? newsOutput.buckets
    : [];
  const newsArticles = Array.isArray(newsOutput?.articles)
    ? newsOutput.articles.slice(0, 6)
    : [];
  const scenarioCsvSnapshot = newsOutput?.scenarioCsv;
  const scenarioMetadata = scenario.output?.metadata;
  const scenarioRunLabel =
    scenarioMetadata?.run_timestamp ||
    scenarioMetadata?.run_directory ||
    scenarioMetadata?.runDirectory ||
    null;
  useEffect(() => {
    if (newsArticles.length) {
      setActiveNewsArticle(newsArticles[0]);
    } else {
      setActiveNewsArticle(null);
    }
  }, [newsOutput]);
  const [predictedCurves, setPredictedCurves] = useState({});
  useEffect(() => {
    const matrix = scenario.output?.scenarioMatrix;
    if (!matrix || matrix.length === 0) return;

    // convert rows → JSONL → request curve predictions
    const jsonl = matrix.map((row) => JSON.stringify(row)).join("\n");
    console.log(scenarioRunLabel.slice(0, 8));

    async function fetchPredictions() {
      console.log("Entering fetch predictions");
      try {
        const yyyymmdd = scenarioRunLabel.slice(0, 8);
        const formatted = `${yyyymmdd.slice(0, 4)}-${yyyymmdd.slice(4, 6)}-${yyyymmdd.slice(6, 8)}`;
        const resp = await fetch(
          "http://localhost:8000/generate-scenario-curves",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              jsonl_input: jsonl, // match the key in your FastAPI endpoint
              combine_with_news: true, // or false depending on UI
              date: formatted,
            }),
          },
        );

        const out = await resp.json();
        console.log("API response:", out);
        setPredictedCurves(out);
        console.log("Stored predictedCurves:", out.curves);
      } catch (err) {
        console.error("Prediction error:", err);
      }
    }

    fetchPredictions();
  }, [scenario.output?.scenarioMatrix]);

  const launchScenarioGen = async (options: any) => {
    setSelectedScenario(null);
    setSelectedDebateRun(null);
    return runScenarioGen(setScenario, options);
  };

  const buildNewsContext = (news: any) => {
    if (!news) return "";
    const lines: string[] = [];
    if (news.summary?.headline)
      lines.push(`Headline: ${news.summary.headline}`);
    if (news.summary?.detail) lines.push(`Detail: ${news.summary.detail}`);
    if (news.summary?.reason)
      lines.push(`Recommendation: ${news.summary.reason}`);
    const uncovered = Array.isArray(news.buckets)
      ? news.buckets
          .filter((bucket: any) => bucket.uncovered)
          .map((bucket: any) => `${bucket.label} (${bucket.count} stories)`)
      : [];
    if (uncovered.length) {
      lines.push("Buckets lacking coverage: " + uncovered.join("; "));
    }
    if (Array.isArray(news.articles) && news.articles.length) {
      lines.push("Representative headlines:");
      news.articles.slice(0, 3).forEach((article: any) => {
        lines.push(`- ${article.bucketLabel}: ${article.title}`);
      });
    }
    return lines.join("\n");
  };

  const handleNewsUpdate = async () => {
    if (!newsOutput) return;
    const context = buildNewsContext(newsOutput);
    const scenarioResult = await launchScenarioGen({
      portfolioName,
      yaml,
      debateRounds,
      debateRuns,
      debaterAPrompt,
      debaterBPrompt,
      judgePrompt,
      offlineSample: offlineMode,
      newsContext: context,
    });
    const scenarioMatrix =
      scenarioResult?.scenarioMatrix || scenario.output?.scenarioMatrix || [];
    await runImpact(setImpact, scenarioMatrix);
    await runOptimize(setOpt, scenarioMatrix);
  };
  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-white to-slate-50">
      <header className="sticky top-0 z-10 backdrop-blur bg-white/70 border-b">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
          {/* Top-left logos + title */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-[28px] h-[28px] rounded bg-white border shadow-sm overflow-hidden flex items-center justify-center">
                <img
                  src="/logos/bofa.png"
                  alt="Bank of America"
                  className="w-full h-full object-contain"
                />
              </div>
              <div className="w-[28px] h-[28px] rounded bg-white border shadow-sm overflow-hidden flex items-center justify-center">
                <img
                  src="/logos/uchicago_finm.png"
                  alt="UChicago FINM"
                  className="w-full h-full object-contain"
                />
              </div>
            </div>
            <h1 className="font-semibold text-lg">
              AI-Enabled HQLA Risk Platform
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Brief
            </Button>
            <Button
              onClick={async () => {
                const scenarioResult = await launchScenarioGen({
                  portfolioName,
                  yaml,
                  debateRounds,
                  debateRuns,
                  debaterAPrompt,
                  debaterBPrompt,
                  judgePrompt,
                  offlineSample: offlineMode,
                });
                const scenarioMatrix =
                  scenarioResult?.scenarioMatrix ||
                  scenario.output?.scenarioMatrix ||
                  [];
                await runImpact(setImpact, scenarioMatrix);
                await runOptimize(setOpt, scenarioMatrix);
                await runMonitor(setMon, scenarioMatrix);
              }}
            >
              <PlayCircle className="h-4 w-4 mr-2" />
              Run E2E
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-none px-4 py-6 grid gap-6">
        {/* Inputs — compact */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05 }}
        >
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle>Inputs</CardTitle>
              <CardDescription>
                Upload portfolio + yield curve + define shock priors
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-2">
                <div className="col-span-1 space-y-2">
                  <label className="text-sm font-medium leading-none">
                    Portfolio name
                  </label>
                  <Input
                    className="h-8"
                    value={portfolioName}
                    onChange={(e) => setPortfolioName(e.target.value)}
                    placeholder="HQLA v2025Q4"
                  />

                  {/* Portfolio file upload */}
                  <Input
                    type="file"
                    accept=".csv"
                    onChange={(e) =>
                      setPortfolioFile(e.target.files?.[0] || null)
                    }
                    className="h-8 mt-2"
                  />
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleUploadPortfolio}
                    disabled={!portfolioFile || loadingPortfolio}
                  >
                    {loadingPortfolio ? "Uploading..." : "Upload Portfolio"}
                  </Button>

                  {/* Yield curve file upload */}
                  <Input
                    type="file"
                    accept=".csv"
                    onChange={(e) =>
                      setYieldCurveFile(e.target.files?.[0] || null)
                    }
                    className="h-8 mt-2"
                  />
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleUploadYieldCurve}
                    disabled={!yieldCurveFile || loadingCurve}
                  >
                    {loadingCurve ? "Uploading..." : "Upload Yield Curve"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.08 }}
        >
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle>Attribution Viewer</CardTitle>
              <CardDescription>
                One-click open of the attribution HTML with chart links.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-4 gap-3 items-end">
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none">
                    Report date
                  </label>
                  <Input
                    type="date"
                    className="h-9"
                    value={attributionDate}
                    onChange={(e) => setAttributionDate(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium leading-none">
                    Image type
                  </label>
                  <select
                    className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                    value={attributionMode}
                    onChange={(e) => setAttributionMode(e.target.value)}
                  >
                    <option value="all">All</option>
                    <option value="report">Report</option>
                    <option value="heatmap">Heatmap</option>
                    <option value="none">None</option>
                  </select>
                </div>
                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-medium leading-none">
                    Open
                  </label>
                  <Button className="w-full" onClick={openAttributionPage}>
                    Open attribution HTML
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Portfolio summary table */}
        {portfolioSummary && (
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Portfolio Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="max-h-64 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Instrument</TableHead>
                      <TableHead>ISIN</TableHead>
                      <TableHead>Rating</TableHead>
                      <TableHead>Coupon</TableHead>
                      <TableHead>Clean Price</TableHead>
                      <TableHead>YTM</TableHead>
                      <TableHead>Quantity</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>DV01</TableHead>
                      <TableHead>CS01</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Convexity</TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {tableData.map((row: any, i: number) => {
                      const realizedRow = portfolioSummary.assets[i];
                      const scenarioRow =
                        scenarioSummary?.scenario[i] ?? realizedRow;

                      // Compute deltas
                      const deltaCleanPrice =
                        scenarioRow.clean_price - realizedRow.clean_price;
                      const deltaYtm = scenarioRow.ytm - realizedRow.ytm;
                      const deltaDv01 = scenarioRow.dv01 - realizedRow.dv01;
                      const deltaCs01 =
                        scenarioRow.cs01 === "-" || realizedRow.cs01 === "-"
                          ? 0
                          : scenarioRow.cs01 - realizedRow.cs01;
                      const deltaDuration =
                        scenarioRow.duration - realizedRow.duration;
                      const deltaConvexity =
                        scenarioRow.convexity - realizedRow.convexity;

                      // Helper to render delta with arrow
                      const renderDelta = (
                        delta: number,
                        isPercent: boolean = false,
                      ) => {
                        if (delta === 0) return null;
                        const formattedDelta = isPercent
                          ? (delta * 100).toFixed(2)
                          : delta.toFixed(4);
                        return (
                          <span
                            className={`ml-1 ${delta > 0 ? "text-green-600" : "text-red-600"}`}
                          >
                            {delta > 0 ? "▲" : "▼"} {formattedDelta}
                          </span>
                        );
                      };

                      return (
                        <TableRow key={i}>
                          <TableCell>{row.name}</TableCell>
                          <TableCell>{row.isin}</TableCell>
                          <TableCell>{row.rating}</TableCell>
                          <TableCell>
                            {row.coupon !== "Floating"
                              ? `${(row.coupon * 100).toFixed(2)}%`
                              : "Floating"}
                          </TableCell>

                          {/* Clean Price */}
                          <TableCell>
                            {scenarioRow.clean_price.toFixed(2)}
                            {scenarioSummary && renderDelta(deltaCleanPrice)}
                          </TableCell>

                          {/* YTM */}
                          <TableCell>
                            {scenarioRow.ytm.toFixed(2)}%
                            {scenarioSummary &&
                              renderDelta(deltaYtm / 100, true)}
                          </TableCell>

                          {/* Quantity */}
                          <TableCell>{row.quantity}</TableCell>

                          {/* Category */}
                          <TableCell>{row.category}</TableCell>

                          {/* DV01 */}
                          <TableCell>
                            {scenarioRow.dv01?.toFixed(4)}
                            {scenarioSummary && renderDelta(deltaDv01)}
                          </TableCell>

                          {/* CS01 */}
                          <TableCell>
                            {scenarioRow.cs01 !== "-"
                              ? scenarioRow.cs01?.toFixed(4)
                              : "-"}
                            {scenarioSummary &&
                              scenarioRow.cs01 !== "-" &&
                              realizedRow.cs01 !== "-" &&
                              renderDelta(deltaCs01)}
                          </TableCell>

                          {/* Duration */}
                          <TableCell>
                            {scenarioRow.duration?.toFixed(4)}
                            {scenarioSummary && renderDelta(deltaDuration)}
                          </TableCell>

                          {/* Convexity */}
                          <TableCell>
                            {scenarioRow.convexity?.toFixed(4)}
                            {scenarioSummary && renderDelta(deltaConvexity)}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* === INSERT YIELD CURVE PLOT HERE === */}
        {yieldCurve?.length > 0 && (
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Yield Curve</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-2">
                <button
                  className={`px-2 py-1 border rounded ${yieldScenario === null ? "bg-blue-500 text-white" : ""}`}
                  onClick={() => {
                    setYieldScenario(null);
                    handleScenarioPricing(null);
                  }}
                >
                  Realized Only
                </button>
                {Object.keys(scenarioCurves).map((sc) => (
                  <button
                    key={sc}
                    className={`px-2 py-1 border rounded ${yieldScenario === sc ? "bg-blue-500 text-white" : ""}`}
                    onClick={() => {
                      setYieldScenario(sc);
                      handleScenarioPricing(sc);
                    }}
                  >
                    {sc.replace("-", " ")}
                  </button>
                ))}
              </div>

              {/* Wrap chart in ResponsiveContainer */}
              <ResponsiveContainer width="50%" height={300}>
                <LineChart data={yieldCurve}>
                  <XAxis dataKey="tenor" />
                  <YAxis
                    dataKey="rate"
                    domain={[0, 0.1]}
                    tickFormatter={(rate) => `${(rate * 100).toFixed(2)}%`}
                  />
                  <CartesianGrid strokeDasharray="3 3" />
                  <Tooltip
                    formatter={(value) => `${(value * 100).toFixed(2)}%`}
                  />
                  <Line
                    type="monotone"
                    dataKey="rate"
                    stroke="#007bff"
                    name="Realized"
                  />
                  {yieldScenario && scenarioCurves[yieldScenario] && (
                    <Line
                      type="monotone"
                      data={scenarioCurves[yieldScenario]}
                      dataKey="rate"
                      stroke="#ff4136"
                      name={`Scenario: ${yieldScenario}`}
                    />
                  )}
                  <Legend />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
        {/* Pipeline */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle>Pipeline (Horizontal Flow)</CardTitle>
              <CardDescription>
                Debate → Scenario Matrix → Impact/Optimization → News Feedback →
                (loops back)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FlowCanvas
                portfolioReady={Boolean(portfolioName)}
                sStatus={scenario.status as any}
                iStatus={impact.status as any}
                oStatus={opt.status as any}
                mStatus={mon.status as any}
              />
              <div className="flex items-stretch gap-3 overflow-x-auto pb-2">
                {/* Debate */}
                <div
                  className="mt-2 rounded-lg border p-2 
                                max-h-300 overflow-y-auto 
                                max-w-[800px]"
                >
                  <div className="min-w-[280px] flex-1">
                    <Step
                      index={1}
                      title="Debate Preview"
                      desc="MAD: Proponent vs Devil's advocate + Judge"
                      status={scenario.status as any}
                    />
                    <div className="mt-2 rounded-lg border p-2">
                      <div className="flex items-center justify-between mb-1">
                        <div className="text-[11px] text-slate-500">
                          ← Portfolio input feeds MAD debate and scenario
                          generation
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="text-[11px] text-slate-500 flex items-center gap-2">
                            <span>
                              Runs ×{" "}
                              <span className="font-medium">{debateRuns}</span>
                            </span>
                            <span>•</span>
                            <span>
                              Rounds ×{" "}
                              <span className="font-medium">
                                {debateRounds}
                              </span>
                            </span>
                          </div>
                          {availableRuns.length > 0 && (
                            <div className="flex items-center gap-1">
                              <span className="text-[11px] text-slate-500">
                                Run:
                              </span>
                              <select
                                className="text-[11px] bg-slate-50 border border-slate-300 rounded-full px-2 py-0.5 focus:outline-none focus:ring-1 focus:ring-slate-400"
                                value={activeRun ?? ""}
                                onChange={(e) => {
                                  const v = e.target.value;
                                  setSelectedDebateRun(v ? Number(v) : null);
                                }}
                              >
                                {availableRuns.map((r) => (
                                  <option key={r} value={r}>
                                    {r}
                                  </option>
                                ))}
                              </select>
                            </div>
                          )}
                          <label className="flex items-center gap-1 text-[11px] text-slate-600">
                            <input
                              type="checkbox"
                              className="h-3.5 w-3.5"
                              checked={offlineMode}
                              onChange={(e) => setOfflineMode(e.target.checked)}
                            />
                            Offline sample
                          </label>
                        </div>
                      </div>
                      <DebatePreview
                        debate={previewDebate}
                        maxChars={1200}
                        runOptions={availableRuns}
                        activeRun={activeRun}
                        onSelectRun={(run) => setSelectedDebateRun(run)}
                        onShowMatrix={(payload) => setMatrixModal(payload)}
                      />
                      <div className="mt-2 text-[11px] text-slate-600">
                        {scenario.liveStage
                          ? scenario.liveStage
                          : scenario.status === "running"
                            ? "MAD debate is running…"
                            : "Idle. Click Run to launch MAD debate."}
                      </div>
                      <div className="mt-2">
                        <LogView
                          logs={(scenario.logs || []).slice(-8)}
                          title="MAD"
                        />
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setOpenDebate(true)}
                          >
                            Details
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setOpenDebateParams(true)}
                          >
                            Parameters
                          </Button>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            launchScenarioGen({
                              portfolioName,
                              yaml,
                              debateRounds,
                              debateRuns,
                              debaterAPrompt,
                              debaterBPrompt,
                              judgePrompt,
                              offlineSample: offlineMode,
                            })
                          }
                        >
                          <PlayCircle className="h-4 w-4 mr-1" />
                          Run
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                <FlowArrow />

                {/* Scenario Matrix */}
                <div className="min-w-[380px] flex-1">
                  <Step
                    index={2}
                    title="Scenario Matrix"
                    desc="Judge matrix (probabilities + channels)"
                    status={scenario.status as any}
                  />
                  <div className="mt-2 rounded-lg border p-2">
                    <div className="text-[11px] text-slate-500 mb-1">
                      {scenarioRunLabel
                        ? `Run timestamp: ${scenarioRunLabel}`
                        : "Run MAD to populate this matrix."}
                    </div>
                    {scenarioMetadata?.news_context && (
                      <div className="text-[11px] text-slate-400 mb-1">
                        News context applied.
                      </div>
                    )}
                    <ScenarioMiniTable
                      data={scenario.output?.scenarios || []}
                      onSelect={(name) => setSelectedScenario(name)}
                      selected={selectedScenario}
                      open={() => setOpenScenario(true)}
                    />
                  </div>
                  <div className="flex justify-end mt-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setOpenScenario(true)}
                    >
                      Details
                    </Button>
                  </div>
                </div>

                <FlowArrow />

                {/* Impact + Optimization */}
                <div className="min-w-[420px] flex-1">
                  <Step
                    index={3}
                    title="Impact & Optimization"
                    desc="Compute ΔLCR/ΔNSFR/NII; click a row to optimize"
                    status={impact.status as any}
                  />
                  <div className="mt-2 rounded-lg border p-2">
                    <ImpactMiniTable
                      data={impact.output?.metrics || []}
                      worst={worst?.scenario}
                      onOptimize={(name) => {
                        setSelectedScenario(name);
                        runOptimize(
                          setOpt,
                          scenario.output?.scenarioMatrix || [],
                          name,
                        );
                      }}
                      open={() => setOpenImpact(true)}
                    />
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            runImpact(
                              setImpact,
                              scenario.output?.scenarioMatrix || [],
                            )
                          }
                        >
                          <PlayCircle className="h-4 w-4 mr-1" />
                          Run Impact
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setOpenImpact(true)}
                        >
                          Details
                        </Button>
                      </div>
                    </div>
                    <div className="flex justify-end mt-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setOpenOpt(true)}
                      >
                        Optimization Details
                      </Button>
                    </div>
                  </div>
                </div>

                <FlowArrow />

                {/* News */}
                <div className="min-w-[320px] flex-1">
                  <Step
                    index={4}
                    title="News Feedback"
                    desc="Find news relevant to scenarios; closes the loop"
                    status={mon.status as any}
                  />
                  <div className="mt-2 rounded-lg border p-2">
                    <div className="rounded-lg border p-3 bg-white/70 space-y-3">
                      {newsOutput ? (
                        <>
                          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                            <div>
                              <p className="font-semibold text-sm">
                                {newsSummary?.headline ||
                                  "News cycle refreshed."}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {newsSummary?.detail ||
                                  "Latest headlines bucketed by macro driver."}
                              </p>
                              {newsSummary?.reason && (
                                <p className="text-[11px] text-slate-500 mt-1">
                                  {newsSummary.reason}
                                </p>
                              )}
                              {newsSummary?.date && (
                                <p className="text-[11px] text-slate-400 mt-0.5">
                                  Snapshot: {newsSummary.date}
                                </p>
                              )}
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <Badge
                                variant={
                                  newsSummary?.shouldUpdate
                                    ? "destructive"
                                    : "secondary"
                                }
                              >
                                {newsSummary?.shouldUpdate
                                  ? "Update scenarios"
                                  : "In sync"}
                              </Badge>
                              {newsOutput?.metadata?.date_range && (
                                <Badge
                                  variant="outline"
                                  className="text-[11px]"
                                >
                                  {newsOutput.metadata.date_range.start} →{" "}
                                  {newsOutput.metadata.date_range.end}
                                </Badge>
                              )}
                            </div>
                          </div>
                          <div className="grid gap-2 sm:grid-cols-2">
                            {newsBuckets.map((bucket: any) => (
                              <div
                                key={bucket.name}
                                className="border rounded-md p-2 space-y-1"
                              >
                                <div className="flex items-start justify-between gap-2">
                                  <div>
                                    <p className="text-[11px] uppercase text-slate-500 tracking-wide">
                                      {bucket.label}
                                    </p>
                                    <p className="text-xl font-semibold">
                                      {bucket.count}
                                    </p>
                                  </div>
                                  <Badge
                                    variant={
                                      bucket.uncovered
                                        ? "destructive"
                                        : "outline"
                                    }
                                  >
                                    {bucket.uncovered
                                      ? "Needs coverage"
                                      : "Covered"}
                                  </Badge>
                                </div>
                                <p className="text-[11px] text-muted-foreground">
                                  {bucket.description}
                                </p>
                                {bucket.coverage?.length ? (
                                  <p className="text-[11px] text-emerald-600">
                                    Scenarios: {bucket.coverage.join(", ")}
                                  </p>
                                ) : (
                                  <p className="text-[11px] text-rose-600">
                                    No judge scenarios mapped
                                  </p>
                                )}
                                {bucket.topHeadlines?.[0]?.title && (
                                  <p className="text-[11px] text-slate-600 truncate">
                                    Top: {bucket.topHeadlines[0].title}
                                  </p>
                                )}
                              </div>
                            ))}
                            {!newsBuckets.length && (
                              <div className="text-sm text-muted-foreground">
                                No categorized news found in the selected
                                window.
                              </div>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-500">
                            Covered = at least one judge scenario references
                            this bucket (based on channels & keywords).
                            Uncovered buckets lack explicit scenario coverage
                            and may require a MAD refresh.
                          </p>
                          {newsArticles.length > 0 && (
                            <div className="grid gap-2 sm:grid-cols-5">
                              <div className="sm:col-span-2">
                                <p className="text-xs font-medium text-slate-600">
                                  Headlines
                                </p>
                                <ul className="mt-1 space-y-1 text-xs">
                                  {newsArticles.map(
                                    (article: any, idx: number) => (
                                      <li key={`${article.bucket}-${idx}`}>
                                        <button
                                          className={`text-left w-full rounded px-2 py-1 ${activeNewsArticle === article ? "bg-slate-200" : "text-muted-foreground hover:text-slate-800"}`}
                                          onClick={() =>
                                            setActiveNewsArticle(article)
                                          }
                                        >
                                          <span className="font-semibold text-slate-600">
                                            {article.bucketLabel}:
                                          </span>{" "}
                                          {article.title}
                                        </button>
                                      </li>
                                    ),
                                  )}
                                </ul>
                              </div>
                              <div className="sm:col-span-3 border rounded-md p-3 bg-slate-50 space-y-2 text-xs text-slate-700 min-h-[120px]">
                                {activeNewsArticle ? (
                                  <>
                                    <div className="flex items-center justify-between gap-2">
                                      <p className="text-sm font-semibold text-slate-800">
                                        {activeNewsArticle.title}
                                      </p>
                                      {activeNewsArticle.source && (
                                        <span className="text-[11px] text-slate-500">
                                          {activeNewsArticle.source}
                                        </span>
                                      )}
                                    </div>
                                    <p>
                                      {activeNewsArticle.summary ||
                                        "No summary available."}
                                    </p>
                                    {activeNewsArticle.url && (
                                      <a
                                        href={activeNewsArticle.url}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-sky-600 underline text-[11px]"
                                      >
                                        Open article
                                      </a>
                                    )}
                                  </>
                                ) : (
                                  <p className="text-muted-foreground">
                                    Select a headline to view its summary.
                                  </p>
                                )}
                              </div>
                            </div>
                          )}
                        </>
                      ) : (
                        <div className="text-sm text-muted-foreground min-h-[90px] flex items-center justify-center">
                          No news brief yet. Click Run Monitor.
                        </div>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          runMonitor(
                            setMon,
                            scenario.output?.scenarioMatrix || [],
                          )
                        }
                      >
                        <PlayCircle className="h-4 w-4 mr-1" />
                        Run Monitor
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        title="Use news to refresh MAD scenarios"
                        onClick={handleNewsUpdate}
                      >
                        <RefreshCw className="h-4 w-4 mr-1" />
                        Update Scenarios
                      </Button>
                      {scenarioCsvSnapshot && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            downloadTextFile(
                              "scenario_snapshot.csv",
                              scenarioCsvSnapshot,
                            )
                          }
                        >
                          <Download className="h-4 w-4 mr-1" />
                          Scenario CSV
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setOpenMon(true)}
                      >
                        Details
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-3">
                <Progress value={pipelinePct} />
                <p className="mt-2 text-xs text-muted-foreground">
                  Overall progress: {pipelinePct}%
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Hidden sections kept for future use */}
        <div className="hidden" />
        <div className="hidden" />
        <div className="hidden" />

        {/* Popups */}
        <Dialog open={openDebateParams} onOpenChange={setOpenDebateParams}>
          <DialogContent className="max-w-none w-[95vw] sm:max-w-[95vw] md:max-w-[95vw] h-[88vh] overflow-auto text-[15px] px-8 py-6">
            <DialogHeader>
              <DialogTitle>Debate Parameters (MAD)</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 max-h-[78vh] overflow-auto">
              <div className="grid md:grid-cols-3 gap-4">
                <div className="col-span-1 space-y-2">
                  <label className="text-sm font-medium leading-none">
                    Rounds
                  </label>
                  <Input
                    type="number"
                    min={1}
                    max={10}
                    className="w-28"
                    value={debateRounds}
                    onChange={(e) => {
                      const n = Number(e.target.value);
                      setDebateRounds(Number.isFinite(n) && n > 0 ? n : 1);
                    }}
                  />
                  <p className="text-xs text-muted-foreground">
                    Mirrors{" "}
                    <code className="font-mono text-[10px]">
                      cfg[&quot;debate&quot;][&quot;rounds&quot;]
                    </code>{" "}
                    in the Python MAD script.
                  </p>
                  <label className="flex items-center gap-2 text-sm mt-2">
                    <input
                      type="checkbox"
                      className="h-4 w-4"
                      checked={offlineMode}
                      onChange={(e) => setOfflineMode(e.target.checked)}
                    />
                    Offline sample (no OpenAI calls)
                  </label>
                </div>
                <div className="col-span-1 space-y-2">
                  <label className="text-sm font-medium leading-none">
                    Runs
                  </label>
                  <Input
                    type="number"
                    min={1}
                    max={8}
                    className="w-28"
                    value={debateRuns}
                    onChange={(e) => {
                      const n = Number(e.target.value);
                      setDebateRuns(Number.isFinite(n) && n > 0 ? n : 1);
                    }}
                  />
                  <p className="text-xs text-muted-foreground">
                    Controls how many complete debates execute per request.
                  </p>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                <strong>Rounds</strong> = number of Proponent/Devil exchanges
                per run (each round has A, B, and a Judge decision).{" "}
                <strong>Runs</strong> = how many full debates execute per
                request (the judge aggregates across them).
              </p>

              <div className="space-y-4">
                <div className="space-y-2 rounded-lg border bg-slate-50/40 p-3">
                  <label className="text-sm font-medium leading-none">
                    Proponent system prompt
                  </label>
                  <Textarea
                    className="min-h-[220px] md:min-h-[260px] text-sm"
                    value={debaterAPrompt}
                    onChange={(e) => setDebaterAPrompt(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Maps to Proponent (A){" "}
                    <code className="font-mono text-[10px]">
                      system_debater
                    </code>{" "}
                    prompt.
                  </p>
                </div>

                <div className="space-y-2 rounded-lg border bg-slate-50/40 p-3">
                  <label className="text-sm font-medium leading-none">
                    Devil's advocate system prompt
                  </label>
                  <Textarea
                    className="min-h-[220px] md:min-h-[260px] text-sm"
                    value={debaterBPrompt}
                    onChange={(e) => setDebaterBPrompt(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Maps to Devil's advocate (B){" "}
                    <code className="font-mono text-[10px]">
                      system_debater
                    </code>{" "}
                    prompt.
                  </p>
                </div>

                <div className="space-y-2 rounded-lg border bg-slate-50/40 p-3">
                  <label className="text-sm font-medium leading-none">
                    Judge system prompt
                  </label>
                  <Textarea
                    className="min-h-[220px] md:min-h-[260px] text-sm"
                    value={judgePrompt}
                    onChange={(e) => setJudgePrompt(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Maps to{" "}
                    <code className="font-mono text-[10px]">system_judge</code>{" "}
                    in your MAD config.
                  </p>
                </div>
              </div>

              <div className="text-xs text-muted-foreground">
                {/* These controls are front-end only for now. When you wire the UI to your Python runner, */}
                pass <code className="font-mono text-[10px]">debateRounds</code>
                , <code className="font-mono text-[10px]">debaterAPrompt</code>,
                <code className="font-mono text-[10px]">debaterBPrompt</code>,
                and <code className="font-mono text-[10px]">judgePrompt</code>{" "}
                into your YAML / run config.
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={openDebate} onOpenChange={setOpenDebate}>
          <DialogContent className="max-w-none w-[95vw] sm:max-w-[95vw] md:max-w-[95vw] h-[88vh] overflow-auto text-[15px] px-8 py-6">
            <DialogHeader>
              <DialogTitle>Debate (MAD)</DialogTitle>
            </DialogHeader>
            <div className="space-y-3 max-h-[74vh] overflow-auto">
              <div className="flex items-center justify-between">
                <div className="text-[12px] text-muted-foreground">
                  Two debaters + a judge; click Run in the pipeline to refresh.
                </div>
                {availableRuns.length > 0 && (
                  <div className="flex items-center gap-2 text-[11px] text-slate-500">
                    <span>Run:</span>
                    <select
                      className="text-[11px] bg-slate-50 border border-slate-300 rounded-full px-2 py-0.5 focus:outline-none focus:ring-1 focus:ring-slate-400"
                      value={activeRun ?? ""}
                      onChange={(e) => {
                        const v = e.target.value;
                        setSelectedDebateRun(v ? Number(v) : null);
                      }}
                    >
                      {availableRuns.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              <div className="rounded-lg border p-3">
                <DebatePreview
                  debate={previewDebate}
                  maxChars={20000}
                  runOptions={availableRuns}
                  activeRun={activeRun}
                  onSelectRun={(run) => setSelectedDebateRun(run)}
                  onShowMatrix={(payload) => setMatrixModal(payload)}
                />
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={openScenario} onOpenChange={setOpenScenario}>
          <DialogContent className="sm:max-w-none max-w-none w-[100vw] md:w-[95vw] h-[90vh] overflow-auto text-[16px] p-6">
            <DialogHeader>
              <DialogTitle>Scenario Generation</DialogTitle>
            </DialogHeader>
            <div className="space-y-3 max-h-[86vh] overflow-auto">
              {scenario.output?.scenarioMatrix?.length ||
              scenario.output?.scenarios?.length ? (
                <ScenarioBubbleTable
                  data={
                    scenario.output?.scenarioMatrix?.length
                      ? scenario.output.scenarioMatrix
                      : scenario.output.scenarios
                  }
                />
              ) : (
                <div className="rounded-lg border border-dashed p-6 text-center text-muted-foreground text-sm">
                  No scenarios yet. Run the step.
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={openImpact} onOpenChange={setOpenImpact}>
          <DialogContent className="sm:max-w-none max-w-none w-[100vw] md:w-[95vw] h-[90vh] overflow-auto text-[16px] p-6">
            <DialogHeader>
              <DialogTitle>Impact Analysis</DialogTitle>
            </DialogHeader>
            <div className="rounded-lg border overflow-auto max-w-full max-h-[86vh]">
              <Table className="w-full table-auto">
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-[15px] md:text-[16px]">
                      Scenario
                    </TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">
                      ΔLCR (pp)
                    </TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">
                      ΔNSFR (pp)
                    </TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">
                      ΔNII (bps)
                    </TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">
                      Note
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(impact.output?.metrics || []).map((m: any, i: number) => {
                    const isWorst = worst && m.scenario === worst.scenario;
                    return (
                      <TableRow
                        key={i}
                        className={isWorst ? "bg-red-50" : ""}
                        onClick={() => setSelectedScenario(m.scenario)}
                      >
                        <TableCell className="font-medium">
                          {m.scenario}
                        </TableCell>
                        <TableCell className={m.dLCR < 0 ? "text-red-600" : ""}>
                          {m.dLCR}
                        </TableCell>
                        <TableCell
                          className={m.dNSFR < 0 ? "text-red-600" : ""}
                        >
                          {m.dNSFR}
                        </TableCell>
                        <TableCell className={m.dNII < 0 ? "text-red-600" : ""}>
                          {m.dNII}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {m.note}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                  {!impact.output?.metrics?.length && (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        className="text-center text-muted-foreground"
                      >
                        No metrics yet. Run the step.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={openOpt} onOpenChange={setOpenOpt}>
          <DialogContent className="sm:max-w-none max-w-none w-[100vw] md:w-[95vw] h-[90vh] overflow-auto text-[16px] p-6">
            <DialogHeader>
              <DialogTitle>
                Optimization{" "}
                {selectedScenario ? `(focused on: ${selectedScenario})` : ""}
              </DialogTitle>
            </DialogHeader>
            <div className="rounded-lg border overflow-auto max-w-full max-h-[86vh]">
              <Table className="w-full table-auto">
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-[15px] md:text-[16px]">
                      Action
                    </TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">
                      Instrument
                    </TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">
                      Size
                    </TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">
                      Reason
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(opt.output?.trades || []).map((t: any, i: number) => (
                    <TableRow key={i}>
                      <TableCell>
                        <Badge
                          variant={
                            t.action === "BUY"
                              ? "default"
                              : t.action === "SELL"
                                ? "destructive"
                                : "secondary"
                          }
                        >
                          {t.action}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-medium">{t.instr}</TableCell>
                      <TableCell>{t.size}</TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {t.reason}
                      </TableCell>
                    </TableRow>
                  ))}
                  {!opt.output?.trades?.length && (
                    <TableRow>
                      <TableCell
                        colSpan={4}
                        className="text-center text-muted-foreground"
                      >
                        No trades yet. Run the step.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={openMon} onOpenChange={setOpenMon}>
          <DialogContent className="max-w-[1200px] w-[85vw] md:w-[72vw] h-[78vh] overflow-auto text-[15px] p-6">
            <DialogHeader>
              <DialogTitle>News Feedback</DialogTitle>
            </DialogHeader>
            <div className="rounded-lg border p-4 text-sm text-muted-foreground min-h-[120px] max-w-full max-h-[68vh] overflow-auto">
              {newsOutput ? (
                <pre className="text-xs whitespace-pre-wrap">
                  {JSON.stringify(newsOutput, null, 2)}
                </pre>
              ) : (
                "No briefing yet. Run the step."
              )}
            </div>
          </DialogContent>
        </Dialog>

        <Dialog
          open={Boolean(matrixModal)}
          onOpenChange={(open) => {
            if (!open) setMatrixModal(null);
          }}
        >
          <DialogContent className="max-w-none w-[98vw] sm:w-[96vw] md:w-[94vw] lg:w-[92vw] xl:w-[88vw] sm:max-w-[96vw] md:max-w-[94vw] lg:max-w-[92vw] xl:max-w-[88vw] 2xl:max-w-[1700px] max-h-[85vh] overflow-auto text-[15px] p-6">
            <DialogHeader>
              <DialogTitle>
                {matrixModal?.title || "Scenario matrix"}
              </DialogTitle>
            </DialogHeader>
            <div className="max-h-[74vh] overflow-auto space-y-4">
              {matrixModal?.prevScenarios?.length &&
              matrixModal?.scenarios?.length ? (
                <>
                  <ScenarioDiffMatrix
                    current={matrixModal.scenarios}
                    previous={matrixModal.prevScenarios}
                  />
                  <ScenarioDiffSummary
                    current={matrixModal.scenarios}
                    previous={matrixModal.prevScenarios}
                  />
                </>
              ) : matrixModal?.scenarios?.length ? (
                <ScenarioBubbleTable data={matrixModal.scenarios} />
              ) : matrixModal?.rawMatrixText ? (
                <pre className="rounded-md border bg-slate-50 p-3 text-xs whitespace-pre-wrap">
                  {matrixModal.rawMatrixText}
                </pre>
              ) : (
                <div className="text-muted-foreground text-sm">
                  No structured JSON detected in this message.
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>

        <footer className="pb-10 pt-2 text-center text-xs text-muted-foreground">
          Built for the HQLA Project Lab
        </footer>
      </main>
    </div>
  );
}

function FlowCanvas({
  portfolioReady,
  sStatus,
  iStatus,
  oStatus,
  mStatus,
}: {
  portfolioReady: boolean;
  sStatus: "idle" | "running" | "done";
  iStatus: "idle" | "running" | "done";
  oStatus: "idle" | "running" | "done";
  mStatus: "idle" | "running" | "done";
}) {
  // Map statuses to colors
  const col = (st: "idle" | "running" | "done") =>
    st === "done" ? "#10b981" : st === "running" ? "#3b82f6" : "#cbd5e1";

  // Nodes: 0: Portfolio, 1: Debate, 2: Scenario, 3: Impact, 4: Optimization, 5: News
  const nodes = [
    {
      x: 100,
      y: 100,
      label: "Portfolio\nInput",
      color: portfolioReady ? "#0ea5e9" : "#cbd5e1",
    },
    { x: 520, y: 100, label: "Debate\n(MAD)", color: col(sStatus) },
    { x: 940, y: 100, label: "Scenario\nMatrix", color: col(sStatus) },
    { x: 1360, y: 100, label: "Impact\n(LCR/NSFR/NII)", color: col(iStatus) },
    { x: 1780, y: 100, label: "Optimization\n(Trades)", color: col(oStatus) },
    { x: 2200, y: 100, label: "News\nFeedback", color: col(mStatus) },
  ];

  return (
    <div className="relative w-full mb-4">
      <svg
        viewBox="-120 -200 2400 520"
        className="w-full h-[320px] md:h-[360px]"
        style={{ overflow: "visible" }}
      >
        <defs>
          <marker
            id="arrow"
            markerWidth="14"
            markerHeight="10"
            refX="12"
            refY="4"
            orient="auto"
          >
            <path d="M0,0 L12,4 L0,8 z" fill="#94a3b8"></path>
          </marker>
          <marker
            id="arrow-strong"
            markerWidth="14"
            markerHeight="10"
            refX="12"
            refY="4"
            orient="auto"
          >
            <path d="M0,0 L12,4 L0,8 z" fill="#64748b"></path>
          </marker>
        </defs>

        {/* Edges between each node with aligned arrowheads */}
        {nodes.slice(0, -1).map((n, i) => {
          const a = n;
          const b = nodes[i + 1];
          return (
            <path
              key={i}
              d={`M ${a.x + 36} ${a.y} L ${b.x - 36} ${b.y}`}
              stroke="#94a3b8"
              strokeWidth="3.4"
              markerEnd="url(#arrow)"
            />
          );
        })}

        {/* Staple-style loop: up from top of News → left across → down into top-center of Debate */}
        {(() => {
          // Node circle radius must match the circle r used below
          const Rnode = 32;

          // News node (index 5) top point
          const newsX = nodes[5].x;
          const newsYTop = nodes[5].y - Rnode;

          // Debate node (index 1) top center point
          const debX = nodes[1].x;
          const debYTop = nodes[1].y - Rnode;

          // Top rail height (a bit above the nodes row)
          const topY = Math.min(nodes[1].y, nodes[5].y) - 140;

          // Corner radius for soft right-angle turns
          const r = 18;

          const d = [
            // Start at top of News, go straight up to the top rail (with rounded corner onto the rail)
            `M ${newsX} ${newsYTop}`,
            `V ${topY + r}`,
            `Q ${newsX} ${topY} ${newsX - r} ${topY}`,
            // Go left across the top rail toward Debate (round corner to point downward)
            `H ${debX + r}`,
            `Q ${debX} ${topY} ${debX} ${topY + r}`,
            // Go straight down into the top-center of Debate, so arrowhead points down
            `V ${debYTop + 2}`,
          ].join(" ");

          return (
            <path
              d={d}
              fill="none"
              stroke="#64748b"
              strokeWidth="3.8"
              strokeOpacity="0.45"
              strokeLinejoin="round"
              strokeLinecap="round"
              markerEnd="url(#arrow-strong)"
            />
          );
        })()}

        {/* Nodes */}
        {nodes.map((n, idx) => (
          <g key={idx} transform={`translate(${n.x}, ${n.y})`}>
            <circle
              cx="0"
              cy="0"
              r="32"
              fill={n.color}
              stroke="#334155"
              strokeWidth="0.5"
            />
            <text
              x="0"
              y="54"
              fontSize="14"
              textAnchor="middle"
              fill="#334155"
              fontFamily="ui-sans-serif, system-ui"
            >
              {n.label.split("\n").map((line, i) => (
                <tspan key={i} x="0" dy={i === 0 ? 0 : 16}>
                  {line}
                </tspan>
              ))}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function LogView({ logs, title }: { logs: string[]; title?: string }) {
  return (
    <div className="rounded-lg border p-3 bg-white/60">
      {title && (
        <p className="font-medium text-sm mb-2 flex items-center gap-1">
          <ChevronRight className="h-4 w-4" />
          {title} logs
        </p>
      )}
      <div className="space-y-1 text-xs max-h-40 overflow-auto">
        {logs?.length ? (
          logs.map((l, i) => (
            <div key={i} className="text-muted-foreground">
              • {l}
            </div>
          ))
        ) : (
          <div className="text-muted-foreground">No logs yet.</div>
        )}
      </div>
    </div>
  );
}

// Very basic markdown renderer for bold (**bold**), paragraphs, and ```json code fences
function renderMarkdown(text: string): React.ReactNode {
  // Split into paragraphs on blank lines
  const paragraphs = text.split(/\n{2,}/);

  return paragraphs.map((para, idx) => {
    const trimmed = para.trim();

    // Handle fenced code blocks like ```json ... ```
    if (trimmed.startsWith("```") && trimmed.includes("\n")) {
      const lines = trimmed.split("\n");
      const first = lines[0]; // ```json or ``` or ```lang
      const last = lines[lines.length - 1];
      if (last.trim().startsWith("```")) {
        const lang = first.replace(/```/, "").trim() || "";
        const codeBody = lines.slice(1, -1).join("\n");

        return (
          <pre
            key={idx}
            className="mt-1 rounded-md bg-slate-900/90 text-slate-50 text-xs p-3 overflow-auto"
          >
            <code className={lang ? `language-${lang}` : undefined}>
              {codeBody}
            </code>
          </pre>
        );
      }
    }

    // Very lightweight **bold** support for non-code paragraphs
    const parts = trimmed.split("**");
    const children = parts.map((part, i) =>
      i % 2 === 1 ? <strong key={i}>{part}</strong> : part,
    );
    return (
      <p key={idx} className={idx > 0 ? "mt-1" : ""}>
        {children}
      </p>
    );
  });
}

function downloadTextFile(filename: string, content: string) {
  if (!content) return;
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

// --- Helpers for extracting judge JSON and showing it as a mini matrix ---

function cleanJsonish(input: string): string {
  if (!input) return input;
  // Remove trailing commas before closing braces/brackets, which makes it more JSON5-like
  return input.replace(/,\s*([}\]])/g, "$1");
}

// Helper to extract scenario JSON from a message, robustly, and strip it from the visible text.
function extractScenariosAndStripJson(text: string): {
  cleanText: string;
  scenarios: any[];
} {
  if (!text) return { cleanText: "", scenarios: [] };

  const original = text;

  // Remove explicit JSON labels so they don't show up in the rendered prose.
  const labelStripped = original
    .split("\n")
    .filter((line) => !/^JSON\s*:?\s*$/i.test(line.trim()))
    .join("\n");

  // Capture fenced code blocks first so we can parse multiple JSON payloads if they exist.
  const fenceRegex = /```[a-zA-Z0-9]*([\s\S]*?)```/g;
  const fencedPayloads: string[] = [];
  let fenceMatch: RegExpExecArray | null;
  while ((fenceMatch = fenceRegex.exec(labelStripped)) !== null) {
    const body = fenceMatch[1]?.trim();
    if (body) fencedPayloads.push(body);
  }

  // Remove fences from the visible prose so the rendered text stays lightweight.
  let cleaned = labelStripped.replace(fenceRegex, "");
  cleaned = cleaned.replace(/(\u2026|\.\.\.)\[trunc(ated)?\]/gi, "");

  const scenariosFromFences = fencedPayloads.flatMap((payload) =>
    tryParseScenarioPayload(payload),
  );

  if (scenariosFromFences.length) {
    return { cleanText: cleaned.trim(), scenarios: scenariosFromFences };
  }

  const locateJsonStart = (body: string): number => {
    const labelRegex = /(revised\s+json|strict\s+json|json)\s*:?\s*/i;
    const match = body.match(labelRegex);
    if (match && typeof match.index === "number") {
      const afterLabel = match.index + match[0].length;
      const afterBody = body.slice(afterLabel);
      const braceIdx = afterBody.search(/[{[]/);
      if (braceIdx !== -1) {
        return afterLabel + braceIdx;
      }
      return afterLabel;
    }
    const firstCurly = body.indexOf("{");
    const firstBracket = body.indexOf("[");
    if (firstCurly === -1) return firstBracket;
    if (firstBracket === -1) return firstCurly;
    return Math.min(firstCurly, firstBracket);
  };
  const firstIdx = locateJsonStart(cleaned);

  if (firstIdx === -1) {
    return { cleanText: cleaned.trim(), scenarios: [] };
  }

  const prefixText = cleaned.slice(0, firstIdx);
  let jsonPart = cleaned.slice(firstIdx);
  const lastSq = jsonPart.lastIndexOf("]");
  const lastCurly = jsonPart.lastIndexOf("}");
  if (lastSq !== -1) jsonPart = jsonPart.slice(0, lastSq + 1);
  else if (lastCurly !== -1) jsonPart = jsonPart.slice(0, lastCurly + 1);

  const scenarios = tryParseScenarioPayload(jsonPart);
  if (scenarios.length) {
    return { cleanText: prefixText.trim(), scenarios };
  }

  const segments = collectJsonSegments(cleaned);
  if (segments.length) {
    const rows: any[] = [];
    for (const segment of segments) {
      const parsed = tryParseScenarioPayload(segment);
      if (parsed.length) rows.push(...parsed);
    }
    if (rows.length) {
      return { cleanText: prefixText.trim(), scenarios: rows };
    }
  }

  // Parsing failed—keep the original text intact so the user can still read the raw matrix.
  return { cleanText: original.trim(), scenarios: [] };
}

function unwrapScenarioArray(payload: any, allowObjectFallback = true): any[] {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if (typeof payload === "object") {
    const candidateKeys = [
      "scenarios",
      "Scenarios",
      "scenario_matrix",
      "ScenarioMatrix",
      "matrix",
      "entries",
      "rows",
      "candidates",
      "results",
      "final_scenarios",
    ];

    for (const key of candidateKeys) {
      const val = (payload as any)[key];
      if (Array.isArray(val)) return val;
      // Some responses wrap scenarios under results.scenarios, etc.
      if (val && typeof val === "object") {
        const nested = unwrapScenarioArray(val, false);
        if (nested.length) return nested;
      }
    }

    return allowObjectFallback ? [payload] : [];
  }
  return [];
}

function tryParseScenarioPayload(payload: string): any[] {
  if (!payload) return [];
  const normalized = cleanJsonish(payload.trim());
  if (!normalized) return [];

  const attempts: string[] = [normalized];

  // If multiple JSON objects are stacked without commas, wrap them into an array.
  if (!normalized.trim().startsWith("[") && /\}\s*\n\s*\{/.test(normalized)) {
    attempts.push("[" + normalized.replace(/}\s*\n\s*{/g, "},{") + "]");
  }

  for (const attempt of attempts) {
    try {
      const parsed = JSON.parse(attempt);
      const rows = unwrapScenarioArray(parsed);
      if (rows.length) return rows;
    } catch {
      continue;
    }
  }

  // Final fallback: wrap the payload in brackets and try once more.
  try {
    const parsed = JSON.parse(`[${normalized}]`);
    return unwrapScenarioArray(parsed);
  } catch {
    // Final attempt: scan for standalone JSON objects even if the payload is truncated.
    const loose = extractLooseJsonObjects(normalized);
    return loose;
  }
}

function extractLooseJsonObjects(text: string): any[] {
  const results: any[] = [];
  if (!text) return results;

  let depth = 0;
  let start = -1;
  let inString = false;
  let escape = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];

    if (inString) {
      if (escape) {
        escape = false;
      } else if (ch === "\\") {
        escape = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }

    if (ch === '"') {
      inString = true;
      continue;
    }

    if (ch === "{") {
      if (depth === 0) start = i;
      depth++;
    } else if (ch === "}") {
      depth = Math.max(depth - 1, 0);
      if (depth === 0 && start !== -1) {
        const candidate = text.slice(start, i + 1);
        try {
          const parsed = JSON.parse(cleanJsonish(candidate));
          const rows = unwrapScenarioArray(parsed);
          if (rows.length) results.push(...rows);
          else results.push(parsed);
        } catch {
          // ignore malformed fragments
        }
        start = -1;
      }
    }
  }

  return results;
}

function collectJsonSegments(text: string): string[] {
  const segments: string[] = [];
  if (!text) return segments;

  let depth = 0;
  let start = -1;
  let inString = false;
  let escape = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];

    if (inString) {
      if (escape) {
        escape = false;
      } else if (ch === "\\") {
        escape = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }

    if (ch === '"') {
      inString = true;
      continue;
    }

    if (ch === "{" || ch === "[") {
      if (depth === 0) start = i;
      depth++;
    } else if (ch === "}" || ch === "]") {
      depth = Math.max(depth - 1, 0);
      if (depth === 0 && start !== -1) {
        segments.push(text.slice(start, i + 1));
        start = -1;
      }
    }
  }

  return segments;
}

function formatScenarioField(key: string, value: any): string {
  if (value == null) return "";
  if (key === "Probability" && typeof value === "number") {
    if (value <= 1) return `${(value * 100).toFixed(0)}%`;
    return value.toFixed(2);
  }
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function buildScenarioTableColumns(data: any[]) {
  const baseColumns = [
    "Scenario",
    "Description",
    "Probability",
    "Rationale",
    "ImpactChannels",
    "Shocks",
    "MetricsDelta",
    "TradeList",
    "Assumptions",
  ];

  const keysSet = new Set<string>(baseColumns);
  data.forEach((s: any) => {
    Object.keys(s || {}).forEach((k) => keysSet.add(k));
  });

  const preferredOrder = [...baseColumns, "name", "p", "channels", "rationale"];

  const keys = Array.from(keysSet).sort((a, b) => {
    const ia = preferredOrder.indexOf(a);
    const ib = preferredOrder.indexOf(b);
    if (ia === -1 && ib === -1) return a.localeCompare(b);
    if (ia === -1) return 1;
    if (ib === -1) return -1;
    return ia - ib;
  });

  const columnWidthMap: Record<string, number> = {
    Scenario: 220,
    Description: 360,
    Probability: 120,
    Rationale: 320,
    ImpactChannels: 220,
    Shocks: 320,
    MetricsDelta: 220,
    TradeList: 260,
    Assumptions: 320,
    name: 220,
    p: 120,
    channels: 220,
  };

  const getColumnWidth = (key: string) => columnWidthMap[key] ?? 240;
  return { keys, getColumnWidth };
}

function ScenarioBubbleTable({
  data,
  bare = false,
}: {
  data: any[];
  bare?: boolean;
}) {
  if (!data?.length) return null;

  const { keys, getColumnWidth } = buildScenarioTableColumns(data);

  const containerClass = bare
    ? "overflow-auto"
    : "mt-1 rounded-md border border-slate-200 bg-white/60 overflow-auto";

  return (
    <div className={containerClass}>
      <Table className="w-full text-[12px]">
        <TableHeader>
          <TableRow>
            {keys.map((k) => (
              <TableHead
                key={k}
                className="py-2 px-3 font-semibold text-slate-800 text-[13px]"
                style={{
                  width: getColumnWidth(k),
                  maxWidth: getColumnWidth(k),
                }}
              >
                {k}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((s: any, i: number) => (
            <TableRow key={i}>
              {keys.map((k) => (
                <TableCell
                  key={k}
                  className="py-1.5 px-2 align-top whitespace-pre-wrap break-words"
                  style={{
                    width: getColumnWidth(k),
                    maxWidth: getColumnWidth(k),
                  }}
                >
                  {formatScenarioField(k, s[k])}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function renderDiffValue(key: string, previous: any, current: any) {
  const prevText =
    previous !== undefined && previous !== null
      ? formatScenarioField(key, previous)
      : "";
  const currText =
    current !== undefined && current !== null
      ? formatScenarioField(key, current)
      : "";
  if (!prevText && !currText) return "";
  if (prevText && currText) {
    if (prevText === currText) return currText;
    return (
      <div className="space-y-0.5">
        <div className="text-rose-600 line-through">{prevText}</div>
        <div className="text-emerald-700">{currText}</div>
      </div>
    );
  }
  if (currText) {
    return <span className="text-emerald-700">{currText}</span>;
  }
  return <span className="text-rose-600 line-through">{prevText}</span>;
}

function ScenarioDiffMatrix({
  current = [],
  previous = [],
}: {
  current: any[];
  previous: any[];
}) {
  const combined = [...current, ...previous];
  if (!combined.length) return null;

  type DiffRow = {
    key: string;
    displayName: string;
    current?: any;
    previous?: any;
    order: number;
  };

  const rowsMap = new Map<string, DiffRow>();

  const normalizeName = (sc: any, idx: number) => {
    const name = (sc?.Scenario || sc?.name || `Scenario ${idx + 1}`).toString();
    return { normalized: name.toLowerCase(), display: name };
  };

  current.forEach((sc, idx) => {
    const { normalized, display } = normalizeName(sc, idx);
    const existing = rowsMap.get(normalized) || {
      key: normalized,
      displayName: display,
      order: idx,
    };
    existing.current = sc;
    existing.displayName = display;
    if (typeof existing.order !== "number") existing.order = idx;
    rowsMap.set(normalized, existing);
  });

  const currentCount = current.length;
  previous.forEach((sc, idx) => {
    const { normalized, display } = normalizeName(sc, idx);
    if (rowsMap.has(normalized)) {
      const existing = rowsMap.get(normalized)!;
      existing.previous = sc;
      if (!existing.displayName) existing.displayName = display;
    } else {
      rowsMap.set(normalized, {
        key: normalized,
        displayName: display,
        previous: sc,
        order: currentCount + idx,
      });
    }
  });

  const rows = Array.from(rowsMap.values()).sort((a, b) => a.order - b.order);
  const { keys, getColumnWidth } = buildScenarioTableColumns(combined);

  return (
    <div className="rounded-md border border-slate-200 bg-white/70 overflow-auto">
      <Table className="w-full text-[12px]">
        <TableHeader>
          <TableRow>
            {keys.map((k) => (
              <TableHead
                key={k}
                className="py-2 px-3 font-semibold text-slate-800 text-[13px]"
                style={{
                  width: getColumnWidth(k),
                  maxWidth: getColumnWidth(k),
                }}
              >
                {k}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, idx) => (
            <TableRow key={row.key + idx}>
              {keys.map((k) => (
                <TableCell
                  key={k}
                  className="py-1.5 px-2 align-top whitespace-pre-wrap break-words"
                  style={{
                    width: getColumnWidth(k),
                    maxWidth: getColumnWidth(k),
                  }}
                >
                  {renderDiffValue(
                    k,
                    row.previous ? row.previous[k] : undefined,
                    row.current ? row.current[k] : undefined,
                  )}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function DebatePreview({
  debate,
  maxChars = 800,
  onShowMatrix,
  runOptions = [],
  activeRun = null,
  onSelectRun,
}: {
  debate: {
    role: string;
    text: string;
    round?: number | null;
    run?: number | null;
    scenarios?: any[];
    rawMatrixText?: string;
    matrixId?: string;
  }[];
  maxChars?: number;
  onShowMatrix?: (payload: {
    title: string;
    scenarios: any[];
    prevScenarios?: any[];
    rawMatrixText?: string;
  }) => void;
  runOptions?: number[];
  activeRun?: number | null;
  onSelectRun?: (run: number | null) => void;
}) {
  const safeDebate = Array.isArray(debate) ? debate : [];
  const runList = Array.isArray(runOptions)
    ? Array.from(new Set(runOptions.filter((r) => typeof r === "number")))
    : [];
  const resolvedActiveRun =
    typeof activeRun === "number"
      ? activeRun
      : runList.length
        ? runList[runList.length - 1]
        : null;
  const activeIdx =
    resolvedActiveRun != null ? runList.indexOf(resolvedActiveRun) : -1;
  const prevRun =
    activeIdx > 0 && activeIdx < runList.length ? runList[activeIdx - 1] : null;
  const showRunNav = runList.length > 1;
  const hasDebate = safeDebate.length > 0;

  const judgeMatrixCandidates: {
    title: string;
    scenarios: any[];
    prevScenarios?: any[];
  }[] = [];
  const prevByRun = new Map<number, any[]>();

  const normalizeSpeakerRefs = (value: string) =>
    value
      .replace(/\bA's\b/gi, "Proponent's")
      .replace(/\bB's\b/gi, "Devil's advocate's")
      .replace(/\bProponent's advocate\b/gi, "Devil's advocate")
      .replace(/\bDebater\s*A\b/gi, "Proponent")
      .replace(/\bDebater\s*B\b/gi, "Devil's advocate")
      .replace(/\bProponent\s+position\b/gi, "Proponent's position")
      .replace(
        /\bDevil'?s advocate's\s+position\b/gi,
        "Devil's advocate's position",
      );

  const renderedMessages = safeDebate.map((m, i) => {
    const roleLower = (m.role || "").toLowerCase();
    const isProponent = roleLower.includes("proponent");
    const isDevil = roleLower.includes("devil");
    const isJudge = roleLower.includes("judge");

    let justify = "justify-start";
    let bubbleClasses = "bg-slate-100 text-slate-900";

    if (isDevil) {
      justify = "justify-end";
      bubbleClasses = "bg-slate-200 text-slate-900";
    } else if (isJudge) {
      justify = "justify-center";
      bubbleClasses = "bg-white text-slate-900 border border-slate-200";
    }

    let displayText = m.text || "";
    // Strip standalone JSON label lines first, and extract scenarios
    const firstPass = extractScenariosAndStripJson(displayText);
    displayText = firstPass.cleanText;
    const providedScenarios = Array.isArray(m.scenarios) ? m.scenarios : [];
    let localScenarios = providedScenarios.length
      ? providedScenarios
      : firstPass.scenarios;
    if (
      !localScenarios.length &&
      typeof m.rawMatrixText === "string" &&
      m.rawMatrixText.trim()
    ) {
      const fallback = tryParseScenarioPayload(m.rawMatrixText);
      if (fallback.length) {
        localScenarios = fallback;
      }
    }
    const hasMatrix = localScenarios.length > 0;
    const hasRawMatrix =
      typeof m.rawMatrixText === "string" && m.rawMatrixText.trim().length > 0;
    let matrixPayload: {
      title: string;
      scenarios: any[];
      prevScenarios?: any[];
      rawMatrixText?: string;
    } | null = null;
    const runKey = typeof m.run === "number" ? m.run : 0;
    const prevForRun = prevByRun.get(runKey) || null;
    if (hasMatrix || hasRawMatrix) {
      const labels: string[] = [m.role];
      if (typeof m.round === "number") labels.push(`Round ${m.round}`);
      if (typeof m.run === "number") labels.push(`Run ${m.run}`);
      matrixPayload = {
        title: labels.join(" · "),
        scenarios: localScenarios,
        prevScenarios: prevForRun || undefined,
        rawMatrixText:
          typeof m.rawMatrixText === "string" ? m.rawMatrixText : undefined,
      };
      if (hasMatrix) {
        if (isJudge) {
          judgeMatrixCandidates.push(matrixPayload);
        }
        prevByRun.set(runKey, localScenarios);
      }
    }

    let truncated = false;
    if (displayText.length > maxChars) {
      displayText = displayText.slice(0, maxChars) + " …[truncated]";
      truncated = true;
    }

    // If there's nothing left after stripping JSON, don't render unless we have scenarios
    displayText = normalizeSpeakerRefs(displayText);

    if (!displayText && !matrixPayload) {
      return null;
    }

    return (
      <div key={i} className={`flex ${justify}`}>
        <div
          className={`max-w-[72%] rounded-2xl px-3 py-2 text-sm shadow-sm ${bubbleClasses}`}
        >
          <div className="text-[10px] font-semibold uppercase tracking-wide mb-1 opacity-70">
            {m.role}
          </div>
          {displayText && <div>{renderMarkdown(displayText)}</div>}
          {truncated && (
            <div className="mt-1 text-[10px] italic text-slate-400">
              (message truncated)
            </div>
          )}
          {matrixPayload && (
            <div className="mt-2 border-t border-slate-200 pt-2">
              <div className="flex items-center justify-between gap-2">
                <div className="text-[10px] font-semibold uppercase tracking-wide opacity-70">
                  Scenarios attached
                </div>
                {onShowMatrix && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-[11px] px-3"
                    onClick={() => {
                      onShowMatrix(matrixPayload!);
                    }}
                  >
                    View matrix
                  </Button>
                )}
              </div>
              <div className="rounded-md border border-slate-200 bg-white/80 px-1 py-1 max-h-64 overflow-auto mt-2">
                {matrixPayload.scenarios?.length ? (
                  <ScenarioBubbleTable data={matrixPayload.scenarios} bare />
                ) : matrixPayload.rawMatrixText ? (
                  <pre className="text-[11px] whitespace-pre-wrap text-slate-700">
                    {matrixPayload.rawMatrixText}
                  </pre>
                ) : (
                  <div className="text-[11px] text-slate-500">
                    Awaiting structured JSON…
                  </div>
                )}
              </div>
              {matrixPayload.prevScenarios?.length ? (
                <div className="text-[10px] text-slate-500 mt-1">
                  Diff vs previous matrix available.
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    );
  });

  return (
    <div className="space-y-3 text-[15px] leading-6">
      {showRunNav && (
        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] uppercase tracking-wide text-slate-500">
          <div className="flex flex-wrap gap-1">
            {runList.map((run) => {
              const isActive =
                resolvedActiveRun != null
                  ? resolvedActiveRun === run
                  : run === runList[runList.length - 1];
              return (
                <button
                  key={`run-${run}`}
                  type="button"
                  onClick={() => onSelectRun?.(run)}
                  className={`px-2 py-1 rounded-full border transition ${
                    isActive
                      ? "bg-slate-900 text-white border-slate-900"
                      : "bg-white text-slate-700 border-slate-300 hover:border-slate-400"
                  }`}
                >
                  Run {run}
                </button>
              );
            })}
          </div>
          {prevRun != null && (
            <button
              type="button"
              onClick={() => onSelectRun?.(prevRun)}
              className="text-[11px] text-slate-600 hover:text-slate-900 transition flex items-center gap-1"
            >
              ← Back to Run {prevRun}
            </button>
          )}
        </div>
      )}
      {hasDebate ? (
        renderedMessages.filter(Boolean)
      ) : (
        <div className="text-muted-foreground text-sm">
          No debate yet — run Scenario.
        </div>
      )}
      {judgeMatrixCandidates.length > 0 && onShowMatrix && (
        <div className="flex justify-end pt-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() =>
              onShowMatrix(
                judgeMatrixCandidates[judgeMatrixCandidates.length - 1],
              )
            }
          >
            View judge matrix
          </Button>
        </div>
      )}
    </div>
  );
}

function FlowArrow() {
  return (
    <div className="flex items-center">
      <ArrowRight className="h-5 w-5 text-slate-400" />
    </div>
  );
}

function ScenarioDiffSummary({
  current = [],
  previous = [],
}: {
  current: any[];
  previous: any[];
}) {
  if (!previous?.length) return null;
  const formatProb = (value: any) => {
    const prob =
      typeof value === "number"
        ? value
        : typeof value === "string"
          ? Number(value)
          : null;
    if (prob == null || Number.isNaN(prob)) return "";
    if (prob <= 1) return `${(prob * 100).toFixed(0)}%`;
    return `${prob.toFixed(1)}%`;
  };
  const getProb = (sc: any) =>
    typeof sc?.Probability === "number"
      ? sc.Probability
      : typeof sc?.p === "number"
        ? sc.p
        : null;
  const prevMap = new Map<string, any>();
  previous.forEach((sc: any, idx: number) => {
    const key = (sc?.Scenario || sc?.name || `prev-${idx}`)
      .toString()
      .toLowerCase();
    prevMap.set(key, sc);
  });

  const rows: {
    type: "added" | "removed" | "changed" | "unchanged";
    name: string;
    current?: any;
    previous?: any;
  }[] = [];

  current.forEach((sc: any, idx: number) => {
    const name = sc?.Scenario || sc?.name || `Scenario ${idx + 1}`;
    const key = name.toString().toLowerCase();
    if (prevMap.has(key)) {
      const prev = prevMap.get(key);
      const changed = JSON.stringify(prev) !== JSON.stringify(sc);
      rows.push({
        type: changed ? "changed" : "unchanged",
        name,
        current: sc,
        previous: prev,
      });
      prevMap.delete(key);
    } else {
      rows.push({ type: "added", name, current: sc });
    }
  });

  prevMap.forEach((prev, key) => {
    const name = prev?.Scenario || prev?.name || key;
    rows.push({ type: "removed", name, previous: prev });
  });

  const interesting = rows.filter((row) => row.type !== "unchanged");
  if (!interesting.length) return null;

  return (
    <div className="mt-4 rounded-md border border-slate-200 bg-white/70 p-3 space-y-2">
      <p className="text-sm font-semibold text-slate-700">
        TL;DR of matrix changes
      </p>
      <ul className="list-disc pl-4 text-xs text-slate-600 space-y-1 max-h-64 overflow-auto">
        {interesting.map((row, idx) => {
          let summary: React.ReactNode = null;
          if (row.type === "added" && row.current) {
            summary = (
              <>
                <span className="text-emerald-700 font-semibold">
                  {row.name}
                </span>{" "}
                added
                {getProb(row.current) != null && (
                  <> (prob {formatProb(getProb(row.current))})</>
                )}
              </>
            );
          } else if (row.type === "removed" && row.previous) {
            summary = (
              <>
                <span className="text-rose-700 font-semibold line-through">
                  {row.name}
                </span>{" "}
                removed
                {getProb(row.previous) != null && (
                  <> (prev prob {formatProb(getProb(row.previous))})</>
                )}
              </>
            );
          } else if (row.type === "changed") {
            summary = (
              <>
                <span className="font-semibold text-slate-700">{row.name}</span>{" "}
                updated
                {getProb(row.previous) != null ||
                getProb(row.current) != null ? (
                  <>
                    {" "}
                    (prob {formatProb(getProb(row.previous)) || "?"} →{" "}
                    <span className="text-emerald-700">
                      {formatProb(getProb(row.current)) || "?"}
                    </span>
                    )
                  </>
                ) : null}
              </>
            );
          }
          return <li key={`${row.name}-${idx}`}>{summary}</li>;
        })}
      </ul>
    </div>
  );
}

function ScenarioMiniTable({
  data,
  onSelect,
  selected,
  open,
}: {
  data: any[];
  onSelect: (name: string) => void;
  selected: string | null;
  open: () => void;
}) {
  return (
    <div className="rounded-lg border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Scenario</TableHead>
            <TableHead>Prob.</TableHead>
            <TableHead>Channels</TableHead>
            <TableHead>Rationale</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(data || []).map((s: any, i: number) => (
            <TableRow
              key={i}
              className={selected === s.name ? "bg-slate-50" : ""}
              onClick={() => {
                onSelect(s.name);
                open();
              }}
            >
              <TableCell className="font-medium">{s.name}</TableCell>
              <TableCell>{(s.p * 100).toFixed(0)}%</TableCell>
              <TableCell className="text-muted-foreground text-sm">
                {s.channels.join(", ")}
              </TableCell>
              <TableCell className="text-muted-foreground text-sm">
                {s.rationale || ""}
              </TableCell>
            </TableRow>
          ))}
          {!data?.length && (
            <TableRow>
              <TableCell
                colSpan={4}
                className="text-center text-muted-foreground"
              >
                No scenarios
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

function ImpactMiniTable({
  data,
  worst,
  onOptimize,
  open,
}: {
  data: any[];
  worst?: string | null;
  onOptimize: (name: string) => void;
  open: () => void;
}) {
  return (
    <div className="rounded-lg border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Scenario</TableHead>
            <TableHead>ΔLCR</TableHead>
            <TableHead>ΔNSFR</TableHead>
            <TableHead>ΔNII</TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {(data || []).map((m: any, i: number) => {
            const isWorst = worst && m.scenario === worst;
            return (
              <TableRow key={i} className={isWorst ? "bg-red-50" : ""}>
                <TableCell className="font-medium">{m.scenario}</TableCell>
                <TableCell className={m.dLCR < 0 ? "text-red-600" : ""}>
                  {m.dLCR}
                </TableCell>
                <TableCell className={m.dNSFR < 0 ? "text-red-600" : ""}>
                  {m.dNSFR}
                </TableCell>
                <TableCell className={m.dNII < 0 ? "text-red-600" : ""}>
                  {m.dNII}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      onOptimize(m.scenario);
                      open();
                    }}
                  >
                    Optimize
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
          {!data?.length && (
            <TableRow>
              <TableCell
                colSpan={5}
                className="text-center text-muted-foreground"
              >
                No metrics yet
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
