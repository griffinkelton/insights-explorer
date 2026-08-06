import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { dailyRows, forecastSeries, funnelSteps, pageRows } from "@/lib/mock-ga4";
import { ChartCard } from "./ChartCard";

const axis = {
  stroke: "var(--color-muted-foreground)",
  fontSize: 11,
  tickLine: false,
  axisLine: false,
};

const tooltipStyle = {
  contentStyle: {
    background: "var(--color-popover)",
    border: "1px solid var(--color-border)",
    borderRadius: "6px",
    fontSize: "12px",
    color: "var(--color-popover-foreground)",
  },
  labelStyle: { color: "var(--color-muted-foreground)", fontSize: "11px" },
};

const shortDate = (d: string) => d.slice(5).replace("-", "/");

export function ChartsRow() {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <ChartCard title="Sessions & users" subtitle="Daily totals across the 90-day window">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={dailyRows} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={38} {...axis} />
            <YAxis {...axis} />
            <Tooltip {...tooltipStyle} />
            <Line
              type="monotone"
              dataKey="sessions"
              stroke="var(--color-chart-1)"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="users"
              stroke="var(--color-chart-2)"
              strokeWidth={1.5}
              strokeDasharray="4 3"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Top pages" subtitle="Sessions by page path">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={pageRows}
            layout="vertical"
            margin={{ top: 6, right: 12, left: 40, bottom: 0 }}
          >
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" {...axis} />
            <YAxis type="category" dataKey="page" width={110} {...axis} />
            <Tooltip {...tooltipStyle} cursor={{ fill: "var(--color-accent)" }} />
            <Bar dataKey="sessions" fill="var(--color-chart-1)" radius={[0, 3, 3, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

export function ForecastFunnelRow() {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <ChartCard title="Sessions forecast" subtitle="14-day linear projection from trailing 30 days">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={forecastSeries} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="date" tickFormatter={shortDate} minTickGap={38} {...axis} />
            <YAxis {...axis} />
            <Tooltip {...tooltipStyle} />
            <Area
              type="monotone"
              dataKey="actual"
              stroke="var(--color-chart-1)"
              fill="var(--color-chart-1)"
              fillOpacity={0.14}
              strokeWidth={2}
              connectNulls
            />
            <Area
              type="monotone"
              dataKey="forecast"
              stroke="var(--color-chart-5)"
              fill="var(--color-chart-5)"
              fillOpacity={0.08}
              strokeWidth={2}
              strokeDasharray="5 4"
              connectNulls
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Conversion funnel" subtitle="Session start through signup completion">
        <div className="flex h-full flex-col justify-center gap-2.5">
          {funnelSteps.map((s, i) => {
            const pct = (s.value / funnelSteps[0]!.value) * 100;
            const drop = i === 0 ? null : 100 - (s.value / funnelSteps[i - 1]!.value) * 100;
            return (
              <div key={s.step}>
                <div className="flex items-baseline justify-between text-xs">
                  <span className="text-foreground">{s.step}</span>
                  <span className="num text-muted-foreground">
                    {s.value.toLocaleString()}
                    {drop !== null && (
                      <span className="ml-2 text-destructive">−{drop.toFixed(1)}%</span>
                    )}
                  </span>
                </div>
                <div className="mt-1 h-2 w-full overflow-hidden rounded-xs bg-surface-2">
                  <div
                    className="h-full rounded-xs bg-primary"
                    style={{ width: `${pct}%`, opacity: 1 - i * 0.13 }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </ChartCard>
    </div>
  );
}
