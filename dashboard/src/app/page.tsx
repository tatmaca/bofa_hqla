"use client";

import React, { useMemo, useState } from "react";
import Image from "next/image"; // (Optional) Next Image for real logos
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CheckCircle2, PlayCircle, Activity, Newspaper, Settings, ChevronRight, Download, ArrowRight, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";

// --- Replace these with real API calls / events wired to your Python backend --- //
function fakeWait(ms:number) { return new Promise(r => setTimeout(r, ms)); }

async function runScenarioGen(
  setter:(s:any)=>void,
  params: {
    portfolioName: string;
    yaml: string;
    debateRounds: number;
    debaterAPrompt: string;
    debaterBPrompt: string;
    judgePrompt: string;
  }
){
  const {
    portfolioName,
    yaml,
    debateRounds,
    debaterAPrompt,
    debaterBPrompt,
    judgePrompt,
  } = params;

  // Reset state, clear old debate + scenarios
  setter((s:any)=>({
    ...s,
    status:"running",
    pct:10,
    logs:[
      ...s.logs,
      `Calling MAD backend for "${portfolioName}" (${debateRounds} rounds, offline mode)…`,
    ],
    output:{
      ...(s.output || {}),
      debate: [],
      scenarios: [],
    },
  }));

  try {
    const res = await fetch("/api/debate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify({
        portfolioName,
        yaml,
        debateRounds,
        debaterAPrompt,
        debaterBPrompt,
        judgePrompt,
      }),
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();

    const rawDebate = Array.isArray(data.debate) ? data.debate : [];
    const debate = rawDebate.map((m: any) => ({
      role: m.role || "Proponent",
      text: m.text || "",
      round: typeof m.round === "number" ? m.round : null,
      run: typeof m.run === "number" ? m.run : null,
    }));

    // Ensure chronological order with Judge at the end of each run, sort by run, round, role
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

    const rawScenarios = Array.isArray(data.scenarios) ? data.scenarios : [];
    const scenarios = rawScenarios.map((sc:any, idx:number) => {
      const name =
        sc.Scenario ||
        sc.name ||
        `Scenario ${idx + 1}`;
      const p =
        typeof sc.Probability === "number"
          ? sc.Probability
          : typeof sc.p === "number"
          ? sc.p
          : 0;
      const channels =
        sc.ImpactChannels ||
        sc.channels ||
        [];
      const rationale =
        sc.Rationale ||
        sc.rationale ||
        "";

      return { name, p, channels, rationale };
    });

    setter((s:any)=>({
      ...s,
      status:"done",
      pct:100,
      logs:[
        ...s.logs,
        "Loaded offline MAD debate from temp.txt and scenarios from /tmp/mad_scenarios.json.",
      ],
      output:{
        ...(s.output || {}),
        debate: sortedDebate,
        scenarios,
      },
    }));
  } catch (err:any) {
    console.error("runScenarioGen error", err);
    setter((s:any)=>({
      ...s,
      status:"idle",
      pct:0,
      logs:[
        ...s.logs,
        `Scenario generation failed: ${String(err?.message || err)}`,
      ],
      output:{
        ...(s.output || {}),
        debate: s.output?.debate || [],
        scenarios: s.output?.scenarios || [],
      },
    }));
  }
}

async function runImpact(setter:(s:any)=>void){
  setter((s:any)=>({...s,status:"running", pct:15, logs:[...s.logs,"Shock buckets → duration ladder…"] }));
  await fakeWait(600);
  setter((s:any)=>({...s, pct:56, logs:[...s.logs,"ΔLCR/ΔNSFR computed (Basel caps)"] }));
  await fakeWait(600);
  setter((s:any)=>({...s,status:"done", pct:100, logs:[...s.logs,"Attribution + NII done"], output:{
    metrics:[
      {scenario:"Hawkish Fed Surprise", dLCR:-6,  dNSFR:-1, dNII:+3.1, note:"Reprice short-end; sell 30y MBS",  riskScore: 6},
      {scenario:"Deposit Outflow Scare", dLCR:-14, dNSFR:-3, dNII:-1.0, note:"Raise Level 1; runoff factors ↑",  riskScore: 14},
      {scenario:"Soft-Landing Grind",    dLCR:+2,  dNSFR:+1, dNII:+1.4, note:"Carry OK; watch issuance",        riskScore: -2},
      {scenario:"MBS Basis Blowout",     dLCR:-4,  dNSFR: 0, dNII:-2.2, note:"Trim 2A/2B; convexity risk",       riskScore: 4},
      {scenario:"Treasury Supply Shock",  dLCR:-7,  dNSFR:-2, dNII:-0.9, note:"Bills up; term premium ↑",        riskScore: 7},
      {scenario:"Credit Risk Off",        dLCR:-9,  dNSFR:-2, dNII:-1.6, note:"HY/IG OAS widen; rotate to L1",   riskScore: 9}
    ]
  }}));
}

async function runOptimize(setter:(s:any)=>void){
  setter((s:any)=>({...s,status:"running", pct:12, logs:[...s.logs,"Building guardrails (L2 caps, LCR≥110%)…"] }));
  await fakeWait(700);
  setter((s:any)=>({...s, pct:64, logs:[...s.logs,"Solving QP for risk-adjusted NII…"] }));
  await fakeWait(700);
  setter((s:any)=>({...s,status:"done", pct:100, logs:[...s.logs,"Trade list v1 posted."], output:{
    trades:[
      {action:"BUY", instr:"UST 2y", size:"+$500mm", reason:"LCR support; bear-steepener hedge"},
      {action:"SELL", instr:"MBS 30y 2.0%", size:"-$300mm", reason:"Neg. convexity under stress"},
      {action:"HOLD", instr:"UST Bills", size:"–", reason:"Cash buffer for outflows"}
    ]
  }}));
}

async function runMonitor(setter:(s:any)=>void){
  setter((s:any)=>({...s,status:"running", pct:18, logs:[...s.logs,"Scraping FOMC/Fed-speak, UST auction, geopolitics…"] }));
  await fakeWait(600);
  setter((s:any)=>({...s, pct:70, logs:[...s.logs,"Classified: ‘hawkish tilt’ → scenario score +0.1"] }));
  await fakeWait(600);
  setter((s:any)=>({...s,status:"done", pct:100, logs:[...s.logs,"Briefing drafted + alerts queued"],
    output:{brief:"Hawkish Fed language nudged bear-steepener risk; suggest +$200mm 2y add, monitor MBS basis."}
  }));
}

const Step = ({index, title, desc, status}:{index:number;title:string;desc:string;status:"idle"|"running"|"done"}) => {
  const color = status === "done" ? "bg-emerald-500" : status === "running" ? "bg-blue-500" : "bg-muted";
  const Icon = status === "done" ? CheckCircle2 : PlayCircle;
  return (
    <div className="flex items-start gap-3">
      <div className={`mt-1 h-6 w-6 rounded-full flex items-center justify-center text-white ${color}`}>
        <Icon className="h-4 w-4"/>
      </div>
      <div>
        <div className="flex items-center gap-2">
          <p className="font-semibold">{index}. {title}</p>
          {status === "done" && <Badge variant="secondary">complete</Badge>}
          {status === "running" && <Badge>running</Badge>}
        </div>
        <p className="text-sm text-muted-foreground">{desc}</p>
      </div>
    </div>
  );
};

export default function HqlaE2EDashboard(){
  const [portfolioName, setPortfolioName] = useState("Example HQLA Portfolio");
  const [yaml, setYaml] = useState("# shocks.yaml\nmove_index: 110\nyield_curve: bear_steepener\ncredit_spreads: { ig_oas: +15, hy_oas: +45 }\n");

  const [scenario, setScenario] = useState({status:"idle", pct:0, logs:[], output:null} as any);
  const [impact, setImpact] = useState({status:"idle", pct:0, logs:[], output:null} as any);
  const [opt, setOpt] = useState({status:"idle", pct:0, logs:[], output:null} as any);
  const [mon, setMon] = useState({status:"idle", pct:0, logs:[], output:null} as any);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [selectedDebateRun, setSelectedDebateRun] = useState<number | null>(null);

  // Debate configuration (mirrors Python MAD config high-level knobs)
  const [debateRounds, setDebateRounds] = useState(3);
  const [debaterAPrompt, setDebaterAPrompt] = useState(
    "You are the Proponent (macro hawk). Propose and defend HQLA scenarios with emphasis on hawkish risks, funding stress, and term-premium shocks."
  );
  const [debaterBPrompt, setDebaterBPrompt] = useState(
    "You are the Devil's advocate (macro dove / soft-landing). Propose and defend HQLA scenarios with emphasis on benign inflation, carry, and stable funding."
  );
  const [judgePrompt, setJudgePrompt] = useState(
    "You are the Judge. You merge Proponent / Devil's advocate proposals into a final, coherent set of 3–6 HQLA scenarios with probabilities ~summed to 1 and Basel-consistent shocks."
  );

  // Popups
  const [openScenario, setOpenScenario] = useState(false);
  const [openDebate, setOpenDebate] = useState(false);
  const [openImpact, setOpenImpact] = useState(false);
  const [openOpt, setOpenOpt] = useState(false);
  const [openMon, setOpenMon] = useState(false);
  const [openDebateParams, setOpenDebateParams] = useState(false);
  const [matrixModal, setMatrixModal] = useState<{ title: string; scenarios: any[] } | null>(null);

  const pipelinePct = useMemo(()=>{
    const pcs = [scenario.pct||0, impact.pct||0, opt.pct||0, mon.pct||0];
    return Math.round(pcs.reduce((a,b)=>a+b,0)/pcs.length);
  },[scenario,impact,opt,mon]);

  const worst = useMemo(()=>{
    const rows = impact.output?.metrics || [];
    if (!rows.length) return null;
    const sorted = [...rows].sort((a:any,b:any)=> (b.riskScore||0) - (a.riskScore||0));
    return sorted[0]; // highest riskScore == worst ΔLCR
  },[impact]);

  const allDone = [scenario,impact,opt,mon].every(s=>s.status==="done");

  // Debate run selection logic
  const debateMessages = (scenario.output?.debate || []) as any[];
  const availableRuns = Array.from(
    new Set(debateMessages.map((m) => (typeof m.run === "number" ? m.run : 1)))
  ).sort((a, b) => a - b);
  const defaultRun = availableRuns.length ? availableRuns[availableRuns.length - 1] : null;
  const activeRun = selectedDebateRun ?? defaultRun;
  const activeDebate = activeRun == null
    ? debateMessages
    : debateMessages.filter((m) => (typeof m.run === "number" ? m.run : 1) === activeRun);

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-white to-slate-50">
      <header className="sticky top-0 z-10 backdrop-blur bg-white/70 border-b">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
          {/* Top-left logos + title */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-[28px] h-[28px] rounded bg-white border shadow-sm overflow-hidden flex items-center justify-center">
                <img src="/logos/bofa.png" alt="Bank of America" className="w-full h-full object-contain"/>
              </div>
              <div className="w-[28px] h-[28px] rounded bg-white border shadow-sm overflow-hidden flex items-center justify-center">
                <img src="/logos/uchicago_finm.png" alt="UChicago FINM" className="w-full h-full object-contain"/>
              </div>
            </div>
            <h1 className="font-semibold text-lg">AI-Enabled HQLA Risk Platform</h1>
            <Badge variant="outline" className="ml-2">MVP</Badge>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline"><Download className="h-4 w-4 mr-2"/>Export Brief</Button>
            <Button onClick={async()=>{
              await runScenarioGen(setScenario, {
                portfolioName,
                yaml,
                debateRounds,
                debaterAPrompt,
                debaterBPrompt,
                judgePrompt,
              });
              await runImpact(setImpact);
              await runOptimize(setOpt);
              await runMonitor(setMon);
            }}>
              <PlayCircle className="h-4 w-4 mr-2"/>Run E2E
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-none px-4 py-6 grid gap-6">
        {/* Inputs — compact */}
        <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} transition={{duration:0.4, delay:0.05}}>
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle>Inputs</CardTitle>
              <CardDescription>Upload portfolio + define shock priors</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-2">
                <div className="col-span-1 space-y-2">
                  <label className="text-sm font-medium leading-none">Portfolio name</label>
                  <Input className="h-8" value={portfolioName} onChange={(e)=>setPortfolioName(e.target.value)} placeholder="HQLA v2025Q4"/>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Button variant="outline" size="sm">Upload Holdings CSV</Button>
                    <Button variant="outline" size="sm">Upload Risk Ladder</Button>
                  </div>
                </div>
                <div className="col-span-2 space-y-2">
                  <label className="text-sm font-medium leading-none">Shock YAML</label>
                  <Textarea className="min-h-[72px] font-mono" value={yaml} onChange={(e)=>setYaml(e.target.value)} />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Pipeline */}
        <motion.div initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} transition={{duration:0.4}}>
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle>Pipeline (Horizontal Flow)</CardTitle>
              <CardDescription>Debate → Scenario Matrix → Impact/Optimization → News Feedback → (loops back)</CardDescription>
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
                  <Step index={1} title="Debate Preview" desc="MAD: Proponent vs Devil's advocate + Judge" status={scenario.status as any}/>
                  <div className="mt-2 rounded-lg border p-2">
                    <div className="flex items-center justify-between mb-1">
                      <div className="text-[11px] text-slate-500">
                        ← Portfolio input feeds MAD debate and scenario generation
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-[11px] text-slate-500">
                          Rounds: <span className="font-medium">{debateRounds}</span>
                        </div>
                        {availableRuns.length > 0 && (
                          <div className="flex items-center gap-1">
                            <span className="text-[11px] text-slate-500">Run:</span>
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
                    </div>
                    <DebatePreview
                      debate={activeDebate.slice(0, 4)}
                      maxChars={400}
                      onShowMatrix={(payload)=>setMatrixModal(payload)}
                    />
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm" onClick={()=>setOpenDebate(true)}>Details</Button>
                        <Button variant="ghost" size="sm" onClick={()=>setOpenDebateParams(true)}>Parameters</Button>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={()=>runScenarioGen(setScenario, {
                          portfolioName,
                          yaml,
                          debateRounds,
                          debaterAPrompt,
                          debaterBPrompt,
                          judgePrompt,
                        })}
                      >
                        <PlayCircle className="h-4 w-4 mr-1"/>Run
                      </Button>
                    </div>
                  </div>
                </div>

                <FlowArrow/>

                {/* Scenario Matrix */}
                <div className="min-w-[380px] flex-1">
                  <Step index={2} title="Scenario Matrix" desc="6 candidates → probs + channels" status={scenario.status as any}/>
                  <div className="mt-2 rounded-lg border p-2">
                    <ScenarioMiniTable
                      data={scenario.output?.scenarios||[]}
                      onSelect={(name)=>setSelectedScenario(name)}
                      selected={selectedScenario}
                      open={()=>setOpenScenario(true)}
                    />
                  </div>
                  <div className="flex justify-end mt-2">
                    <Button variant="ghost" size="sm" onClick={()=>setOpenScenario(true)}>Details</Button>
                  </div>
                </div>

                <FlowArrow/>

                {/* Impact + Optimization */}
                <div className="min-w-[420px] flex-1">
                  <Step index={3} title="Impact & Optimization" desc="Compute ΔLCR/ΔNSFR/NII; click a row to optimize" status={impact.status as any}/>
                  <div className="mt-2 rounded-lg border p-2">
                    <ImpactMiniTable
                      data={impact.output?.metrics||[]}
                      worst={worst?.scenario}
                      onOptimize={(name)=>{ setSelectedScenario(name); runOptimize(setOpt); }}
                      open={()=>setOpenImpact(true)}
                    />
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={()=>runImpact(setImpact)}><PlayCircle className="h-4 w-4 mr-1"/>Run Impact</Button>
                        <Button variant="ghost" size="sm" onClick={()=>setOpenImpact(true)}>Details</Button>
                      </div>
                      <div className="text-xs text-muted-foreground">Worst-case: <span className="font-medium">{worst?.scenario||"—"}</span></div>
                    </div>
                    <div className="flex justify-end mt-1">
                      <Button variant="ghost" size="sm" onClick={()=>setOpenOpt(true)}>Optimization Details</Button>
                    </div>
                  </div>
                </div>

                <FlowArrow/>

                {/* News */}
                <div className="min-w-[320px] flex-1">
                  <Step index={4} title="News Feedback" desc="Find news relevant to scenarios; closes the loop" status={mon.status as any}/>
                  <div className="mt-2 rounded-lg border p-2">
                    <div className="rounded-lg border p-3 text-sm text-muted-foreground min-h-[100px]">
                      {mon.output?.brief || "No news brief yet. Click Run Monitor."}
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <Button variant="outline" size="sm" onClick={()=>runMonitor(setMon)}><PlayCircle className="h-4 w-4 mr-1"/>Run Monitor</Button>
                      <Button variant="ghost" size="sm" title="Use news to update scenarios"><RefreshCw className="h-4 w-4 mr-1"/>Update Scenarios</Button>
                      <Button variant="ghost" size="sm" onClick={()=>setOpenMon(true)}>Details</Button>
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-3">
                <Progress value={pipelinePct} />
                <p className="mt-2 text-xs text-muted-foreground">Overall progress: {pipelinePct}%</p>
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
                  <label className="text-sm font-medium leading-none">Rounds</label>
                  <Input
                    type="number"
                    min={1}
                    max={10}
                    className="w-28"
                    value={debateRounds}
                    onChange={(e)=> {
                      const n = Number(e.target.value);
                      setDebateRounds(Number.isFinite(n) && n > 0 ? n : 1);
                    }}
                  />
                  <p className="text-xs text-muted-foreground">
                    Mirrors <code className="font-mono text-[10px]">cfg[&quot;debate&quot;][&quot;rounds&quot;]</code> in the Python MAD script.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2 rounded-lg border bg-slate-50/40 p-3">
                  <label className="text-sm font-medium leading-none">Proponent system prompt</label>
                  <Textarea
                    className="min-h-[220px] md:min-h-[260px] text-sm"
                    value={debaterAPrompt}
                    onChange={(e)=>setDebaterAPrompt(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Maps to Proponent (A) <code className="font-mono text-[10px]">system_debater</code> prompt.
                  </p>
                </div>

                <div className="space-y-2 rounded-lg border bg-slate-50/40 p-3">
                  <label className="text-sm font-medium leading-none">Devil's advocate system prompt</label>
                  <Textarea
                    className="min-h-[220px] md:min-h-[260px] text-sm"
                    value={debaterBPrompt}
                    onChange={(e)=>setDebaterBPrompt(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Maps to Devil's advocate (B) <code className="font-mono text-[10px]">system_debater</code> prompt.
                  </p>
                </div>

                <div className="space-y-2 rounded-lg border bg-slate-50/40 p-3">
                  <label className="text-sm font-medium leading-none">Judge system prompt</label>
                  <Textarea
                    className="min-h-[220px] md:min-h-[260px] text-sm"
                    value={judgePrompt}
                    onChange={(e)=>setJudgePrompt(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Maps to <code className="font-mono text-[10px]">system_judge</code> in your MAD config.
                  </p>
                </div>
              </div>

              <div className="text-xs text-muted-foreground">
                These controls are front-end only for now. When you wire the UI to your Python runner,
                pass <code className="font-mono text-[10px]">debateRounds</code>, <code className="font-mono text-[10px]">debaterAPrompt</code>,
                <code className="font-mono text-[10px]">debaterBPrompt</code>, and <code className="font-mono text-[10px]">judgePrompt</code> into your YAML / run config.
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
                  debate={activeDebate}
                  maxChars={20000}
                  onShowMatrix={(payload)=>setMatrixModal(payload)}
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
              {scenario.output?.scenarios?.length ? (
                <ScenarioBubbleTable data={scenario.output.scenarios} />
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
                    <TableHead className="text-[15px] md:text-[16px]">Scenario</TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">ΔLCR (pp)</TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">ΔNSFR (pp)</TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">ΔNII (bps)</TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">Note</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(impact.output?.metrics || []).map((m:any, i:number)=> {
                    const isWorst = worst && m.scenario===worst.scenario;
                    return (
                      <TableRow key={i} className={isWorst ? "bg-red-50" : ""} onClick={()=>setSelectedScenario(m.scenario)}>
                        <TableCell className="font-medium">{m.scenario}</TableCell>
                        <TableCell className={m.dLCR<0?"text-red-600":""}>{m.dLCR}</TableCell>
                        <TableCell className={m.dNSFR<0?"text-red-600":""}>{m.dNSFR}</TableCell>
                        <TableCell className={m.dNII<0?"text-red-600":""}>{m.dNII}</TableCell>
                        <TableCell className="text-muted-foreground text-sm">{m.note}</TableCell>
                      </TableRow>
                    );
                  })}
                  {!(impact.output?.metrics)?.length && (
                    <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">No metrics yet. Run the step.</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={openOpt} onOpenChange={setOpenOpt}>
          <DialogContent className="sm:max-w-none max-w-none w-[100vw] md:w-[95vw] h-[90vh] overflow-auto text-[16px] p-6">
            <DialogHeader>
              <DialogTitle>Optimization {selectedScenario ? `(focused on: ${selectedScenario})` : ""}</DialogTitle>
            </DialogHeader>
            <div className="rounded-lg border overflow-auto max-w-full max-h-[86vh]">
              <Table className="w-full table-auto">
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-[15px] md:text-[16px]">Action</TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">Instrument</TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">Size</TableHead>
                    <TableHead className="text-[15px] md:text-[16px]">Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(opt.output?.trades || []).map((t:any, i:number)=> (
                    <TableRow key={i}>
                      <TableCell>
                        <Badge variant={t.action==="BUY"?"default":t.action==="SELL"?"destructive":"secondary"}>{t.action}</Badge>
                      </TableCell>
                      <TableCell className="font-medium">{t.instr}</TableCell>
                      <TableCell>{t.size}</TableCell>
                      <TableCell className="text-muted-foreground text-sm">{t.reason}</TableCell>
                    </TableRow>
                  ))}
                  {!(opt.output?.trades)?.length && (
                    <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No trades yet. Run the step.</TableCell></TableRow>
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

        <Dialog open={Boolean(matrixModal)} onOpenChange={(open) => { if (!open) setMatrixModal(null); }}>
          <DialogContent className="max-w-none w-[100vw] md:w-[95vw] h-[90vh] overflow-auto text-[15px] p-6">
            <DialogHeader>
              <DialogTitle>{matrixModal?.title || "Scenario matrix"}</DialogTitle>
            </DialogHeader>
            <div className="max-h-[72vh] overflow-auto">
              {matrixModal?.scenarios?.length ? (
                <ScenarioBubbleTable data={matrixModal.scenarios} />
              ) : (
                <div className="text-muted-foreground text-sm">
                  No structured JSON detected in this message.
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>

        <footer className="pb-10 pt-2 text-center text-xs text-muted-foreground">
          Built for the HQLA Project Lab • This is a mock UI. Wire the Run buttons to your back-end scripts.
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
}:{
  portfolioReady:boolean;
  sStatus:"idle"|"running"|"done";
  iStatus:"idle"|"running"|"done";
  oStatus:"idle"|"running"|"done";
  mStatus:"idle"|"running"|"done";
}){
  // Map statuses to colors
  const col = (st:"idle"|"running"|"done") =>
    st==="done" ? "#10b981" : st==="running" ? "#3b82f6" : "#cbd5e1";

  // Nodes: 0: Portfolio, 1: Debate, 2: Scenario, 3: Impact, 4: Optimization, 5: News
  const nodes = [
    { x: 100,   y: 100,  label: "Portfolio\nInput",          color: portfolioReady ? "#0ea5e9" : "#cbd5e1" },
    { x: 520,   y: 100,  label: "Debate\n(MAD)",             color: col(sStatus) },
    { x: 940,   y: 100,  label: "Scenario\nMatrix",          color: col(sStatus) },
    { x: 1360,  y: 100,  label: "Impact\n(LCR/NSFR/NII)",    color: col(iStatus) },
    { x: 1780,  y: 100,  label: "Optimization\n(Trades)",    color: col(oStatus) },
    { x: 2200,  y: 100,  label: "News\nFeedback",            color: col(mStatus) },
  ];

  return (
    <div className="relative w-full mb-4">
      <svg viewBox="-120 -200 2400 520" className="w-full h-[320px] md:h-[360px]" style={{overflow:"visible"}}>
        <defs>
          <marker id="arrow" markerWidth="14" markerHeight="10" refX="12" refY="4" orient="auto">
            <path d="M0,0 L12,4 L0,8 z" fill="#94a3b8"></path>
          </marker>
          <marker id="arrow-strong" markerWidth="14" markerHeight="10" refX="12" refY="4" orient="auto">
            <path d="M0,0 L12,4 L0,8 z" fill="#64748b"></path>
          </marker>
        </defs>

        {/* Edges between each node with aligned arrowheads */}
        {nodes.slice(0, -1).map((n, i) => {
          const a = n; const b = nodes[i+1];
          return (
            <path key={i}
              d={`M ${a.x+36} ${a.y} L ${b.x-36} ${b.y}`}
              stroke="#94a3b8" strokeWidth="3.4" markerEnd="url(#arrow)"/>
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
            `V ${debYTop + 2}`
          ].join(' ');

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
        {nodes.map((n, idx)=> (
          <g key={idx} transform={`translate(${n.x}, ${n.y})`}>
            <circle cx="0" cy="0" r="32" fill={n.color} stroke="#334155" strokeWidth="0.5"/>
            <text x="0" y="54" fontSize="14" textAnchor="middle" fill="#334155" fontFamily="ui-sans-serif, system-ui">
              {n.label.split('\n').map((line, i)=> (
                <tspan key={i} x="0" dy={i===0 ? 0 : 16}>{line}</tspan>
              ))}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function LogView({logs, title}:{logs:string[]; title?:string}){
  return (
    <div className="rounded-lg border p-3 bg-white/60">
      {title && <p className="font-medium text-sm mb-2 flex items-center gap-1"><ChevronRight className="h-4 w-4"/>{title} logs</p>}
      <div className="space-y-1 text-xs max-h-40 overflow-auto">
        {logs?.length ? logs.map((l, i)=> <div key={i} className="text-muted-foreground">• {l}</div>) : <div className="text-muted-foreground">No logs yet.</div>}
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
      i % 2 === 1 ? <strong key={i}>{part}</strong> : part
    );
    return (
      <p key={idx} className={idx > 0 ? "mt-1" : ""}>
        {children}
      </p>
    );
  });
}


// --- Helpers for extracting judge JSON and showing it as a mini matrix ---

function cleanJsonish(input: string): string {
  if (!input) return input;
  // Remove trailing commas before closing braces/brackets, which makes it more JSON5-like
  return input.replace(/,\s*([}\]])/g, "$1");
}

// Helper to extract scenario JSON from a message, robustly, and strip it from the visible text.
function extractScenariosAndStripJson(
  text: string
): { cleanText: string; scenarios: any[] } {
  if (!text) return { cleanText: "", scenarios: [] };

  // Remove explicit JSON labels so they don't show up in the rendered prose.
  const labelStripped = text
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

  // Remove fences from the visible prose.
  let cleaned = labelStripped.replace(fenceRegex, "");
  cleaned = cleaned.replace(/(\u2026|\.\.\.)\[trunc(ated)?\]/gi, "");

  const scenariosFromFences = fencedPayloads.flatMap((payload) =>
    tryParseScenarioPayload(payload)
  );

  if (scenariosFromFences.length) {
    return { cleanText: cleaned.trim(), scenarios: scenariosFromFences };
  }

  // Fallback: look for the first JSON-looking block in the remaining text (no fences present).
  const firstCurly = cleaned.indexOf("{");
  const firstBracket = cleaned.indexOf("[");
  const firstIdx =
    firstCurly === -1
      ? firstBracket
      : firstBracket === -1
      ? firstCurly
      : Math.min(firstCurly, firstBracket);

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
  return { cleanText: prefixText.trim(), scenarios };
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

function ScenarioBubbleTable({ data, bare = false }: { data: any[]; bare?: boolean }) {
  if (!data?.length) return null;

  // Canonical scenario columns we always want to show,
  // even if the JSON objects are missing some of them.
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

  // Compute union of all keys, but seed with the canonical columns first
  const keysSet = new Set<string>(baseColumns);
  data.forEach((s: any) => {
    Object.keys(s || {}).forEach((k) => keysSet.add(k));
  });

  const preferredOrder = [
    ...baseColumns,
    "name",
    "p",
    "channels",
    "rationale",
  ];

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
                style={{ width: getColumnWidth(k), maxWidth: getColumnWidth(k) }}
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
                  style={{ width: getColumnWidth(k), maxWidth: getColumnWidth(k) }}
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

function DebatePreview({
  debate,
  maxChars = 800,
  onShowMatrix,
}: {
  debate: { role: string; text: string; round?: number | null; run?: number | null }[];
  maxChars?: number;
  onShowMatrix?: (payload: { title: string; scenarios: any[] }) => void;
}) {
  if (!debate?.length) {
    return (
      <div className="text-muted-foreground text-sm">
        No debate yet — run Scenario.
      </div>
    );
  }

  const renderedMessages = debate.map((m, i) => {
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
    const localScenarios = firstPass.scenarios;

    let truncated = false;
    if (displayText.length > maxChars) {
      displayText = displayText.slice(0, maxChars) + " …[truncated]";
      truncated = true;
    }

    // If there's nothing left after stripping JSON, don't render unless we have scenarios
    if (!displayText && !localScenarios.length) {
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
          {localScenarios.length > 0 && (
            <div className="mt-2 border-t border-slate-200 pt-2 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div className="text-[10px] font-semibold uppercase tracking-wide opacity-70">
                  Scenario Matrix
                </div>
                {onShowMatrix && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-[11px] px-3"
                    onClick={() => {
                      const labels: string[] = [m.role];
                      if (typeof m.round === "number") labels.push(`Round ${m.round}`);
                      if (typeof m.run === "number") labels.push(`Run ${m.run}`);
                      onShowMatrix({
                        title: labels.join(" · "),
                        scenarios: localScenarios,
                      });
                    }}
                  >
                    Expand
                  </Button>
                )}
              </div>
              <div className="rounded-md border border-slate-200 bg-white/80 px-1 py-1 max-h-64 overflow-auto">
                <ScenarioBubbleTable data={localScenarios} bare />
              </div>
            </div>
          )}
        </div>
      </div>
    );
  });

  return (
    <div className="space-y-3 text-[15px] leading-6">
      {renderedMessages.filter(Boolean)}
    </div>
  );
}

function FlowArrow(){
  return (
    <div className="flex items-center">
      <ArrowRight className="h-5 w-5 text-slate-400"/>
    </div>
  );
}

function ScenarioMiniTable({data, onSelect, selected, open}:{data:any[]; onSelect:(name:string)=>void; selected:string|null; open:()=>void;}){
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
          {(data||[]).map((s:any, i:number)=> (
            <TableRow key={i} className={selected===s.name ? "bg-slate-50" : ""} onClick={()=>{ onSelect(s.name); open(); }}>
              <TableCell className="font-medium">{s.name}</TableCell>
              <TableCell>{(s.p*100).toFixed(0)}%</TableCell>
              <TableCell className="text-muted-foreground text-sm">{s.channels.join(", ")}</TableCell>
              <TableCell className="text-muted-foreground text-sm">{s.rationale || ""}</TableCell>
            </TableRow>
          ))}
          {!data?.length && <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No scenarios</TableCell></TableRow>}
        </TableBody>
      </Table>
    </div>
  );
}

function ImpactMiniTable({data, worst, onOptimize, open}:{data:any[]; worst?:string|null; onOptimize:(name:string)=>void; open:()=>void;}){
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
          {(data||[]).map((m:any, i:number)=> {
            const isWorst = worst && m.scenario===worst;
            return (
              <TableRow key={i} className={isWorst ? "bg-red-50" : ""}>
                <TableCell className="font-medium">{m.scenario}</TableCell>
                <TableCell className={m.dLCR<0?"text-red-600":""}>{m.dLCR}</TableCell>
                <TableCell className={m.dNSFR<0?"text-red-600":""}>{m.dNSFR}</TableCell>
                <TableCell className={m.dNII<0?"text-red-600":""}>{m.dNII}</TableCell>
                <TableCell className="text-right">
                  <Button size="sm" variant="outline" onClick={()=>{ onOptimize(m.scenario); open(); }}>Optimize</Button>
                </TableCell>
              </TableRow>
            );
          })}
          {!data?.length && (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground">
                No metrics yet
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
