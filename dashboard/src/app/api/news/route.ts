import { NextResponse } from "next/server";
import { spawn } from "child_process";
import { readFile } from "fs/promises";
import path from "path";

const NEWS_EXPORT_PATH = "/tmp/mad_news_export.json";

const BUCKET_LABELS: Record<string, string> = {
  monetary_policy: "Monetary Policy",
  economic_data: "Economic Data",
  geopolitical_events: "Geopolitical Events",
  market_sentiment: "Market Sentiment",
  fiscal_policy: "Fiscal Policy",
  credit_events: "Credit Events",
  commodity_prices: "Commodity Prices",
  other_general: "Other / General",
};

const BUCKET_DESCRIPTIONS: Record<string, string> = {
  monetary_policy: "Fed decisions, dot plots, policy guidance",
  economic_data: "GDP, payrolls, CPI/PCE, macro surprises",
  geopolitical_events: "Wars, trade tensions, elections, sanctions",
  market_sentiment: "Risk-on/off tone, volatility, flight-to-quality",
  fiscal_policy: "Treasury issuance, deficits, debt ceiling, tax policy",
  credit_events: "Banking stress, spreads, defaults, deposit flight",
  commodity_prices: "Oil, energy, metals, supply shocks",
  other_general: "Human interest or uncategorized macro stories",
};

const BUCKET_KEYWORDS: Record<string, string[]> = {
  monetary_policy: [
    "fed",
    "fomc",
    "rate",
    "hike",
    "cut",
    "powell",
    "policy",
    "tightening",
    "easing",
    "balance sheet",
  ],
  economic_data: [
    "gdp",
    "employment",
    "jobs",
    "payroll",
    "inflation",
    "cpi",
    "ppi",
    "pce",
    "macro",
    "growth",
    "data",
    "recession",
  ],
  geopolitical_events: [
    "geopolitic",
    "war",
    "conflict",
    "taiwan",
    "ukraine",
    "middle east",
    "sanction",
    "election",
    "military",
    "tension",
  ],
  market_sentiment: [
    "sentiment",
    "risk-on",
    "risk off",
    "risk-off",
    "volatility",
    "selloff",
    "sell-off",
    "flight to quality",
    "liquidity",
    "market tone",
  ],
  fiscal_policy: [
    "fiscal",
    "deficit",
    "treasury issuance",
    "debt ceiling",
    "budget",
    "tax",
    "spending",
    "congress",
  ],
  credit_events: [
    "credit",
    "default",
    "bank",
    "deposit",
    "funding",
    "nsfr",
    "lcr",
    "loan",
    "downgrade",
    "spread",
  ],
  commodity_prices: [
    "oil",
    "energy",
    "gas",
    "commodity",
    "brent",
    "wti",
    "metals",
    "food",
    "supply shock",
  ],
  other_general: [],
};

const BUCKET_ORDER = Object.keys(BUCKET_LABELS);

async function runNewsExport(
  newsDir: string,
  startDate?: string,
  endDate?: string
) {
  const pythonCmd = process.env.MAD_PYTHON || "python3";
  const scriptPath = path.join(newsDir, "export_news_for_scenario_gen.py");
  const args = [scriptPath, "--output", NEWS_EXPORT_PATH];
  if (startDate) {
    args.push("--start-date", startDate);
  }
  if (endDate) {
    args.push("--end-date", endDate);
  }

  await new Promise<void>((resolve, reject) => {
    const child = spawn(pythonCmd, args, {
      cwd: newsDir,
    });
    child.stdout?.on("data", (data) => {
      const text = data.toString().trim();
      if (text) console.log("[news stdout]", text);
    });
    child.stderr?.on("data", (data) => {
      const text = data.toString().trim();
      if (text) console.error("[news stderr]", text);
    });
    child.on("error", (err) => reject(err));
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`news export exited with code ${code}`));
    });
  });
}

type ScenarioMatrixEntry = {
  Scenario?: string;
  name?: string;
  Description?: string;
  Rationale?: string;
  Assumptions?: string | string[];
  ImpactChannels?: string[];
};

function scenarioMatrixToCsv(matrix: ScenarioMatrixEntry[]): string {
  if (!Array.isArray(matrix) || !matrix.length) return "";
  const headers = [
    "Scenario",
    "Probability",
    "Description",
    "Rationale",
    "Channels",
    "Assumptions",
  ];
  const lines = [headers.join(",")];

  for (const sc of matrix) {
    const scenarioName = sc.Scenario || sc.name || "";
    const probability = typeof (sc as any).Probability === "number"
      ? (sc as any).Probability
      : "";
    const description = sc.Description || "";
    const rationale = sc.Rationale || "";
    const channels = Array.isArray(sc.ImpactChannels)
      ? sc.ImpactChannels.join("; ")
      : "";
    const assumptions = Array.isArray(sc.Assumptions)
      ? sc.Assumptions.join("; ")
      : typeof sc.Assumptions === "string"
      ? sc.Assumptions
      : "";

    const row = [
      scenarioName,
      probability,
      description,
      rationale,
      channels,
      assumptions,
    ].map((value) => {
      const str = value == null ? "" : String(value);
      if (str.includes(",") || str.includes('"') || str.includes("\n")) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    });
    lines.push(row.join(","));
  }

  return lines.join("\n");
}

function evaluateCoverage(matrix: ScenarioMatrixEntry[]) {
  const coverage: Record<string, { scenarios: string[] }> = {};
  for (const bucket of BUCKET_ORDER) {
    coverage[bucket] = { scenarios: [] };
  }

  if (!Array.isArray(matrix)) return coverage;

  matrix.forEach((sc, idx) => {
    const name = sc.Scenario || sc.name || `Scenario ${idx + 1}`;
    const channels = Array.isArray(sc.ImpactChannels) ? sc.ImpactChannels : [];
    const text = [
      sc.Scenario,
      sc.Description,
      sc.Rationale,
      Array.isArray(sc.Assumptions) ? sc.Assumptions.join(" ") : sc.Assumptions,
      channels.join(" "),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    for (const bucket of BUCKET_ORDER) {
      const keywords = BUCKET_KEYWORDS[bucket];
      const channelMatch = channels.some((ch) =>
        keywords.some((kw) => ch.toLowerCase().includes(kw))
      );
      const keywordMatch = keywords.some((kw) => text.includes(kw));
      if ((keywordMatch || channelMatch) && !coverage[bucket].scenarios.includes(name)) {
        coverage[bucket].scenarios.push(name);
      }
    }
  });

  return coverage;
}

function summarizeBuckets(
  latestDay: any,
  coverage: Record<string, { scenarios: string[] }>
) {
  const bucketCounts: Record<string, number> = latestDay?.bucket_counts || {};
  const articlesByBucket: Record<string, any[]> =
    latestDay?.articles_by_bucket || {};
  const totalArticles = Object.values(bucketCounts).reduce(
    (sum, count) => sum + (count || 0),
    0
  );

  const buckets = BUCKET_ORDER.map((bucket) => {
    const count = bucketCounts[bucket] || 0;
    const articles = Array.isArray(articlesByBucket[bucket])
      ? articlesByBucket[bucket]
      : [];
    const topHeadlines = articles.slice(0, 3).map((article) => ({
      title: article.title,
      summary: article.summary,
      source: article.source,
      url: article.url,
    }));
    const share = totalArticles ? count / totalArticles : 0;
    const coveredBy = coverage[bucket]?.scenarios || [];
    return {
      name: bucket,
      label: BUCKET_LABELS[bucket],
      description: BUCKET_DESCRIPTIONS[bucket],
      count,
      share,
      coverage: coveredBy,
      uncovered: coveredBy.length === 0,
      topHeadlines,
    };
  });

  const sortedBySignal = [...buckets].sort((a, b) => b.count - a.count);
  const topBucket = sortedBySignal[0];
  const significanceThreshold = Math.max(
    3,
    Math.round((totalArticles || 0) * 0.15)
  );
  const uncoveredHighSignal = sortedBySignal.filter(
    (bucket) => bucket.count >= significanceThreshold && bucket.uncovered
  );
  const shouldUpdate =
    (topBucket && topBucket.uncovered && topBucket.count > 0) ||
    uncoveredHighSignal.length > 0;
  const uncoveredNames = uncoveredHighSignal.map((b) => b.label);

  const headline = shouldUpdate
    ? "News drift requires scenario refresh"
    : "News cycle aligns with existing scenarios";
  const detail = topBucket
    ? `${topBucket.label} accounts for ${topBucket.count} stories (${Math.round(
        topBucket.share * 100
      )}%).`
    : "No categorized articles in the selected range.";
  const reason = shouldUpdate
    ? `Buckets lacking scenario coverage: ${uncoveredNames.join(", ") || topBucket?.label || "N/A"}`
    : "High-signal buckets already mapped to judge scenarios.";

  return {
    totalArticles,
    shouldUpdate,
    topBucket,
    headline,
    detail,
    reason,
    buckets,
  };
}

export async function POST(req: Request) {
  try {
    let body: any = {};
    try {
      body = await req.json();
    } catch {
      body = {};
    }
    const { scenarioMatrix = [], startDate, endDate } = body;

    const projectRoot = path.join(process.cwd(), "..");
    const newsDir = path.join(projectRoot, "tools", "news_ingestion");

    await runNewsExport(newsDir, startDate, endDate);
    const raw = await readFile(NEWS_EXPORT_PATH, "utf-8");
    const newsData = JSON.parse(raw);
    const latestDay = Array.isArray(newsData.daily_data)
      ? newsData.daily_data[0]
      : null;

    const coverage = evaluateCoverage(scenarioMatrix);
    const bucketSummary = summarizeBuckets(latestDay, coverage);

    const articles: any[] = [];
    bucketSummary.buckets.forEach((bucket) => {
      bucket.topHeadlines.forEach((headline) => {
        articles.push({
          bucket: bucket.name,
          bucketLabel: bucket.label,
          ...headline,
        });
      });
    });

    const scenarioCsv = scenarioMatrixToCsv(scenarioMatrix);

    return NextResponse.json({
      summary: {
        date: latestDay?.date || null,
        totalArticles: bucketSummary.totalArticles,
        shouldUpdate: bucketSummary.shouldUpdate,
        headline: bucketSummary.headline,
        detail: bucketSummary.detail,
        reason: bucketSummary.reason,
        topBucket: bucketSummary.topBucket
          ? {
              name: bucketSummary.topBucket.name,
              label: bucketSummary.topBucket.label,
              count: bucketSummary.topBucket.count,
              share: bucketSummary.topBucket.share,
            }
          : null,
      },
      buckets: bucketSummary.buckets,
      articles,
      metadata: newsData.metadata,
      llmAnalysis: latestDay?.llm_analysis || null,
      yieldCurveSnapshot: latestDay?.yield_curve_snapshot || null,
      scenarioCoverage: coverage,
      scenarioCsv,
      exportPath: NEWS_EXPORT_PATH,
    });
  } catch (err: any) {
    console.error("Error in news route:", err);
    return NextResponse.json(
      {
        error: "Failed to run news export",
        detail: String(err),
      },
      { status: 500 }
    );
  }
}
