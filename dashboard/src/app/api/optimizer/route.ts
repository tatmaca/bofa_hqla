import { NextResponse } from "next/server";

type OptimizerRequest = {
  scenarios?: unknown[];
  method?: string;
  combine_mode?: string;
  worst_by?: string;
  top_k?: number;
  custom_weights?: Record<string, number>;
  net_cash_outflow?: number;
  min_lcr?: number;
  max_lcr?: number;
  target_duration?: number;
  duration_tolerance?: number;
  allocation_buffer?: number;
};

export async function POST(req: Request) {
  try {
    const body = (await req.json().catch(() => ({}))) as OptimizerRequest;
    const scenarios = Array.isArray(body.scenarios) ? body.scenarios : [];
    if (!scenarios.length) {
      return NextResponse.json(
        { error: "No scenarios provided to optimizer." },
        { status: 400 },
      );
    }

    const resp = await fetch("http://localhost:8000/scenario-rebalance/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...body,
        scenarios,
      }),
    });

    if (!resp.ok) {
      const detail = await resp.json().catch(() => ({}));
      return NextResponse.json(
        { error: "Optimizer backend failed", detail },
        { status: 500 },
      );
    }

    const data = await resp.json();
    return NextResponse.json(data);
  } catch (err: unknown) {
    return NextResponse.json(
      {
        error: "Failed to run optimizer",
        detail: err instanceof Error ? err.message : String(err),
      },
      { status: 500 },
    );
  }
}
