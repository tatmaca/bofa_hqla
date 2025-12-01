"use client";

import React, { useMemo, useState } from "react";
import Image from "next/image"; // (Optional) Next Image for real logos
import {
  LineChart,
  Line,
  Legend,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
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

async function runScenarioGen(setter: (s: any) => void) {
  setter((s: any) => ({
    ...s,
    status: "running",
    pct: 10,
    logs: [...s.logs, "Booting LLM agents…"],
  }));
  await fakeWait(600);
  setter((s: any) => ({
    ...s,
    pct: 45,
    logs: [
      ...s.logs,
      "Crawling macro + regulatory feeds…",
      "Scoring priors from MOVE, 2s10s, HY/IG OAS…",
    ],
  }));
  await fakeWait(700);
  setter((s: any) => ({
    ...s,
    pct: 78,
    logs: [...s.logs, "Debate round complete (3x agents)…"],
  }));
  await fakeWait(500);
  setter((s: any) => ({
    ...s,
    status: "done",
    pct: 100,
    logs: [...s.logs, "Scenario matrix v0.3 written."],
    output: {
      debate: [
        {
          role: "Debater A",
          text: "I argue a hawkish Fed shock is likely given the latest dot plot drift and term premium rise.",
        },
        {
          role: "Debater B",
          text: "Counter: labor softness and easing core inflation suggest a benign path — bull flattening dominates.",
        },
        {
          role: "Debater A",
          text: "MOVE > 110 and supply overhang into auctions support bear-steepener probabilities.",
        },
        {
          role: "Judge",
          text: "Verdict: assign higher weight to ‘Hawkish Fed Surprise’; keep a moderate mass on ‘Soft-Landing Grind’.",
        },
      ],
      scenarios: [
        {
          name: "Hawkish Fed Surprise",
          p: 0.22,
          channels: ["Bear steepener", "Funding costs"],
          rationale: "Dot plot repricing; term premia up",
        },
        {
          name: "Deposit Outflow Scare",
          p: 0.14,
          channels: ["Runoff ↑", "Spread widening"],
          rationale: "Regional bank headline risk",
        },
        {
          name: "Soft-Landing Grind",
          p: 0.32,
          channels: ["Bull flattener", "Carry"],
          rationale: "Cooler prints; issuance steady",
        },
        {
          name: "MBS Basis Blowout",
          p: 0.1,
          channels: ["MBS OAS ↑", "Negative convexity"],
          rationale: "Convexity hedging flows",
        },
        {
          name: "Treasury Supply Shock",
          p: 0.12,
          channels: ["Term premium ↑", "Auction tails"],
          rationale: "Heavy issuance calendar",
        },
        {
          name: "Credit Risk Off",
          p: 0.1,
          channels: ["HY/IG OAS ↑", "Liquidity"],
          rationale: "Risk-off flows widen spreads",
        },
      ],
    },
  }));
}

async function runImpact(setter: (s: any) => void) {
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
  setter((s: any) => ({
    ...s,
    status: "done",
    pct: 100,
    logs: [...s.logs, "Attribution + NII done"],
    output: {
      metrics: [
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
      ],
    },
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
  const [yieldCurve, setYieldCurve] = useState([]);

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
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);

  // Popups
  const [openScenario, setOpenScenario] = useState(false);
  const [openDebate, setOpenDebate] = useState(false);
  const [openImpact, setOpenImpact] = useState(false);
  const [openOpt, setOpenOpt] = useState(false);
  const [openMon, setOpenMon] = useState(false);

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
  const [loadingPortfolio, setLoadingPortfolio] = useState(false);
  const [loadingCurve, setLoadingCurve] = useState(false);
  const allDone = [scenario, impact, opt, mon].every(
    (s) => s.status === "done",
  );

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
            <Badge variant="outline" className="ml-2">
              MVP
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Brief
            </Button>
            <Button
              onClick={async () => {
                await runScenarioGen(setScenario);
                await runImpact(setImpact);
                await runOptimize(setOpt);
                await runMonitor(setMon);
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

                <div className="col-span-2 space-y-2">
                  <label className="text-sm font-medium leading-none">
                    Shock YAML
                  </label>
                  <Textarea
                    className="min-h-[72px] font-mono"
                    value={yaml}
                    onChange={(e) => setYaml(e.target.value)}
                  />
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
                    {portfolioSummary.assets.map((row: any, i: number) => (
                      <TableRow key={i}>
                        <TableCell>{row.name}</TableCell>
                        <TableCell>{row.isin}</TableCell>
                        <TableCell>{row.rating}</TableCell>
                        <TableCell>
                          {row.coupon != "Floating"
                            ? `${(row.coupon * 100).toFixed(2)}%`
                            : "Floating"}
                        </TableCell>
                        <TableCell>{row.clean_price.toFixed(2)}</TableCell>
                        <TableCell>{row.ytm.toFixed(2)}%</TableCell>
                        <TableCell>{row.quantity}</TableCell>
                        <TableCell>{row.category}</TableCell>
                        <TableCell>{row.dv01?.toFixed(4)}</TableCell>
                        <TableCell>
                          {row.cs01 != "-" ? row.cs01?.toFixed(4) : "-"}
                        </TableCell>
                        <TableCell>{row.duration?.toFixed(4)}</TableCell>
                        <TableCell>{row.convexity?.toFixed(4)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* === INSERT YIELD CURVE PLOT HERE === */}
        {yieldCurve && (
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Yield Curve</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-2">
                <button
                  className={`px-2 py-1 border rounded ${selectedScenario === null ? "bg-blue-500 text-white" : ""}`}
                  onClick={() => setSelectedScenario(null)}
                >
                  Realized Only
                </button>
                {Object.keys(scenarioCurves).map((sc) => (
                  <button
                    key={sc}
                    className={`px-2 py-1 border rounded ${selectedScenario === sc ? "bg-blue-500 text-white" : ""}`}
                    onClick={() => setSelectedScenario(sc)}
                  >
                    {sc.replace("-", " ")}
                  </button>
                ))}
              </div>
              <LineChart data={yieldCurve} width={600} height={300}>
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
                {selectedScenario && scenarioCurves[selectedScenario] && (
                  <Line
                    type="monotone"
                    data={scenarioCurves[selectedScenario]}
                    dataKey="rate"
                    stroke="#ff4136"
                    name={`Scenario: ${selectedScenario}`}
                  />
                )}
                <Legend />
              </LineChart>
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
                <div className="min-w-[280px] flex-1">
                  <Step
                    index={1}
                    title="Debate Preview"
                    desc="MAD: A vs B + Judge"
                    status={scenario.status as any}
                  />
                  <div className="mt-2 rounded-lg border p-2">
                    <div className="text-[11px] text-slate-500 mb-1">
                      ← Portfolio input feeds MAD debate and scenario generation
                    </div>
                    <DebatePreview debate={scenario.output?.debate || []} />
                    <div className="flex justify-between mt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setOpenDebate(true)}
                      >
                        Details
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => runScenarioGen(setScenario)}
                      >
                        <PlayCircle className="h-4 w-4 mr-1" />
                        Run
                      </Button>
                    </div>
                  </div>
                </div>

                <FlowArrow />

                {/* Scenario Matrix */}
                <div className="min-w-[380px] flex-1">
                  <Step
                    index={2}
                    title="Scenario Matrix"
                    desc="6 candidates → probs + channels"
                    status={scenario.status as any}
                  />
                  <div className="mt-2 rounded-lg border p-2">
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
                        runOptimize(setOpt);
                      }}
                      open={() => setOpenImpact(true)}
                    />
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => runImpact(setImpact)}
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
                      <div className="text-xs text-muted-foreground">
                        Worst-case:{" "}
                        <span className="font-medium">
                          {worst?.scenario || "—"}
                        </span>
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
                    <div className="rounded-lg border p-3 text-sm text-muted-foreground min-h-[100px]">
                      {mon.output?.brief ||
                        "No news brief yet. Click Run Monitor."}
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => runMonitor(setMon)}
                      >
                        <PlayCircle className="h-4 w-4 mr-1" />
                        Run Monitor
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        title="Use news to update scenarios"
                      >
                        <RefreshCw className="h-4 w-4 mr-1" />
                        Update Scenarios
                      </Button>
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
        <Dialog open={openDebate} onOpenChange={setOpenDebate}>
          <DialogContent className="max-w-[1200px] w-[85vw] md:w-[72vw] h-[78vh] overflow-auto text-[16px] p-6">
            <DialogHeader>
              <DialogTitle>Debate (MAD)</DialogTitle>
            </DialogHeader>
            <div className="space-y-3 max-h-[74vh] overflow-auto">
              <div className="text-[12px] text-muted-foreground">
                Two debaters + a judge; click Run in the pipeline to refresh.
              </div>
              <div className="rounded-lg border p-3">
                <DebatePreview debate={scenario.output?.debate || []} />
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
              <div className="rounded-lg border overflow-auto max-w-full">
                <Table className="w-full table-auto">
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-[15px] md:text-[16px]">
                        Scenario
                      </TableHead>
                      <TableHead className="text-[15px] md:text-[16px]">
                        Prob.
                      </TableHead>
                      <TableHead className="text-[15px] md:text-[16px]">
                        Channels
                      </TableHead>
                      <TableHead className="text-[15px] md:text-[16px]">
                        Rationale
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(scenario.output?.scenarios || []).map(
                      (s: any, i: number) => (
                        <TableRow key={i}>
                          <TableCell className="font-medium">
                            {s.name}
                          </TableCell>
                          <TableCell>{(s.p * 100).toFixed(0)}%</TableCell>
                          <TableCell>{s.channels.join(", ")}</TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {s.rationale}
                          </TableCell>
                        </TableRow>
                      ),
                    )}
                    {!scenario.output?.scenarios?.length && (
                      <TableRow>
                        <TableCell
                          colSpan={4}
                          className="text-center text-muted-foreground"
                        >
                          No scenarios yet. Run the step.
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
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
              {mon.output?.brief || "No briefing yet. Run the step."}
            </div>
          </DialogContent>
        </Dialog>

        <footer className="pb-10 pt-2 text-center text-xs text-muted-foreground">
          Built for the HQLA Project Lab • This is a mock UI. Wire the Run
          buttons to your back-end scripts.
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

        {/* Smooth loop back from News to top of MAD */}
        <path
          d={`M ${nodes[5].x + 26} ${nodes[5].y} C ${nodes[5].x + 320} -140, ${nodes[1].x - 320} -140, ${nodes[1].x} ${nodes[1].y - 34}`}
          fill="none"
          stroke="#94a3b8"
          strokeWidth="3.6"
          markerEnd="url(#arrow-strong)"
        />

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

function DebatePreview({
  debate,
}: {
  debate: { role: string; text: string }[];
}) {
  if (!debate?.length)
    return (
      <div className="text-muted-foreground text-sm">
        No debate yet — run Scenario.
      </div>
    );
  return (
    <div className="space-y-2 text-[15px] leading-6">
      {debate.map((m, i) => (
        <div key={i} className="flex items-start gap-2">
          <div className="shrink-0 rounded-full bg-slate-200 px-2 py-0.5 text-[10px] font-medium">
            {m.role}
          </div>
          <div className="text-sm">{m.text}</div>
        </div>
      ))}
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
            </TableRow>
          ))}
          {!data?.length && (
            <TableRow>
              <TableCell
                colSpan={3}
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
