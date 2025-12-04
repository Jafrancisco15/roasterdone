import React, { useMemo, useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  Legend,
  Label
} from "recharts";
import { Button } from "./ui/button.jsx";

/**
 * RoasterScope – a single, unified chart that overlays:
 *   • Bean Temp (BT)
 *   • Environment/Exhaust Temp (ET)
 *   • Rate of Rise (ΔBT, a.k.a. RoR) – right Y axis (°C/min)
 * Layout and proportions mirror the shared screenshot: top control bar, wide chart, right legend.
 *
 * The component generates RoR from BT if not provided.
 */
export default function RoasterScope({
  data: incomingData,
  chargeAt = 0.2,
  turningPointAt = 0.65,
  dropAt = 7.1,
}) {
  const [isOn, setIsOn] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [data, setData] = useState(
    incomingData ?? generateDemoProfile()
  );

  useEffect(() => {
    if (incomingData) setData(incomingData);
  }, [incomingData]);

  const withRoR = useMemo(() => {
    // Calculate RoR in °C/min from BT using a simple centered diff
    const out = data.map((d, i) => {
      if (i === 0 || i === data.length - 1) return { ...d, RoR: 0 };
      const prev = data[i - 1];
      const next = data[i + 1];
      const dBT = next.BT - prev.BT;
      const dT = (next.t - prev.t);
      const ror = dT !== 0 ? (dBT / dT) : 0;
      return { ...d, RoR: ror };
    });
    return out;
  }, [data]);

  const reset = () => {
    setIsRunning(false);
    setData(incomingData ?? generateDemoProfile());
  };

  const togglePower = () => setIsOn((v) => !v);
  const start = () => setIsRunning(true);

  // Axis domains – tuned to resemble the screenshot
  const TEMP_MIN = 0;
  const TEMP_MAX = 260; // °C
  const TEMP_STEP = 10;
  const ROR_MIN = 0;
  const ROR_MAX = 50; // °C/min
  const TIME_MIN = 0;
  const TIME_BASE_MAX = 16;
  const TIME_STEP = 2;

  const TIME_MAX = useMemo(() => {
    const latestPoint = withRoR.at(-1)?.t ?? TIME_BASE_MAX;
    const roundedMax = Math.ceil(latestPoint / TIME_STEP) * TIME_STEP;
    return Math.max(TIME_BASE_MAX, roundedMax);
  }, [TIME_STEP, TIME_BASE_MAX, withRoR]);

  const timeTicks = useMemo(() => {
    const ticks = [];
    for (let t = TIME_MIN; t <= TIME_MAX; t += TIME_STEP) {
      ticks.push(t);
    }
    return ticks;
  }, [TIME_MAX]);

  const tempTicks = useMemo(() => {
    const ticks = [];
    for (let t = TEMP_MIN; t <= TEMP_MAX; t += TEMP_STEP) {
      ticks.push(t);
    }
    return ticks;
  }, []);

  return (
    <div className="w-full h-[80vh] bg-neutral-950 text-neutral-50 p-3 select-none">
      {/* Top Bar */}
      <div className="flex items-center justify-between gap-4 mb-3">
        <div className="text-2xl font-semibold tracking-tight">#6 Roaster Scope</div>
        <div className="flex items-center gap-3">
          <Button onClick={reset} className="rounded-2xl px-6">RESET</Button>
          <Button variant={isOn ? "default" : "secondary"} onClick={togglePower} className={`rounded-2xl px-6 ${isOn ? "" : ""}`}>
            {isOn ? "ON" : "OFF"}
          </Button>
          <Button onClick={start} className="rounded-2xl px-6">START</Button>
          <div className="ml-2 text-3xl tabular-nums">12:23</div>
        </div>
      </div>

      {/* Main Area: Chart + Right Legend */}
      <div className="grid grid-cols-12 gap-4 h-[calc(80vh-4.5rem)]">
        {/* Chart */}
        <div className="col-span-9 bg-neutral-900 rounded-2xl p-2 shadow-xl border border-neutral-800">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={withRoR} margin={{ top: 12, right: 24, bottom: 12, left: 0 }}>
              <defs>
                <linearGradient id="gridFade" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="currentColor" stopOpacity={0.18} />
                  <stop offset="100%" stopColor="currentColor" stopOpacity={0.05} />
                </linearGradient>
              </defs>

              <CartesianGrid stroke="url(#gridFade)" />

              {/* Grey band around ~220–240 °C like in the screenshot */}
              <ReferenceArea y1={220} y2={240} strokeOpacity={0} fill="#ffffff" fillOpacity={0.06} />

              <XAxis
                dataKey="t"
                type="number"
                domain={[TIME_MIN, TIME_MAX]}
                ticks={timeTicks}
                tick={{ fill: "#bfbfbf" }}
                axisLine={{ stroke: "#777" }}
                tickLine={{ stroke: "#777" }}
                minTickGap={12}
              >
                <Label value="time (min)" position="insideBottomRight" offset={-4} fill="#bfbfbf" />
              </XAxis>

              <YAxis
                yAxisId="temp"
                orientation="left"
                domain={[TEMP_MIN, TEMP_MAX]}
                ticks={tempTicks}
                tick={{ fill: "#bfbfbf" }}
                axisLine={{ stroke: "#777" }}
                tickLine={{ stroke: "#777" }}
                width={36}
              />

              <YAxis
                yAxisId="ror"
                orientation="right"
                domain={[ROR_MIN, ROR_MAX]}
                tick={{ fill: "#bfbfbf" }}
                axisLine={{ stroke: "#777" }}
                tickLine={{ stroke: "#777" }}
                width={36}
              >
                <Label value="°C/min" position="insideTopRight" offset={10} fill="#bfbfbf" />
              </YAxis>

              <Tooltip
                contentStyle={{ background: "#0a0a0a", border: "1px solid #333" }}
                labelStyle={{ color: "#e5e5e5" }}
                itemStyle={{ color: "#e5e5e5" }}
                formatter={(val, name) => [
                  typeof val === "number" ? val.toFixed(1) : val,
                  name,
                ]}
                labelFormatter={(v) => `${v.toFixed?.(2) ?? v} min`}
              />

              {/* Events: CHARGE, TP, DROP */}
              <ReferenceLine x={chargeAt} stroke="#b3b3b3" strokeDasharray="4 4">
                <Label value="CHARGE" position="insideTopLeft" fill="#bfbfbf" />
              </ReferenceLine>
              <ReferenceLine x={turningPointAt} stroke="#b3b3b3" strokeDasharray="4 4">
                <Label value={`TP ${turningPointAt.toFixed(2)}`} position="insideTopLeft" fill="#bfbfbf" />
              </ReferenceLine>
              <ReferenceLine x={dropAt} stroke="#b3b3b3" strokeDasharray="4 4">
                <Label value={`DROP ${dropAt.toFixed(2)}`} position="insideTopLeft" fill="#bfbfbf" />
              </ReferenceLine>

              {/* Lines – leave colors to theme defaults */}
              <Line yAxisId="temp" type="monotone" dataKey="ET" strokeWidth={3} dot={false} name="ET" />
              <Line yAxisId="temp" type="monotone" dataKey="BT" strokeWidth={3} dot={false} name="BT" />
              <Line yAxisId="ror" type="monotone" dataKey="RoR" strokeWidth={2} strokeDasharray="6 4" dot={false} name="ΔBT" />

              <Legend verticalAlign="bottom" height={32} wrapperStyle={{ color: "#dcdcdc" }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Right rail – compact legend + quick stats to echo screenshot composition */}
        <div className="col-span-3 flex flex-col gap-3">
          <div className="bg-neutral-900 rounded-2xl p-4 border border-neutral-800 shadow">
            <div className="text-sm uppercase tracking-wide text-neutral-300 mb-2">Channels</div>
            <ul className="space-y-1 text-sm text-neutral-200">
              <li className="flex items-center justify-between"><span>ET</span><span>{Math.round(withRoR.at(-1)?.ET ?? 0)}</span></li>
              <li className="flex items-center justify-between"><span>BT</span><span>{Math.round(withRoR.at(-1)?.BT ?? 0)}</span></li>
              <li className="flex items-center justify-between"><span>ΔBT</span><span>{(withRoR.at(-1)?.RoR ?? 0).toFixed(1)}</span></li>
            </ul>
          </div>

          <div className="bg-neutral-900 rounded-2xl p-4 border border-neutral-800 shadow flex-1">
            <div className="text-sm uppercase tracking-wide text-neutral-300 mb-2">Notes</div>
            <div className="text-neutral-400 text-sm leading-relaxed">
              Alarms, eventos, o curvas adicionales aquí.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---- Demo profile for visual parity with the screenshot ----
function generateDemoProfile() {
  const pts = [];
  const dt = 0.1; // 6 s
  let BT = 178; // precharge
  let ET = 176;

  for (let t = 0; t <= 10; t = +(t + dt).toFixed(3)) {
    if (t < 0.9) {
      // charge dip to TP
      BT -= 4.5 * dt;
      ET -= 3 * dt;
    } else if (t < 6) {
      // steady climb
      BT += 9.2 * dt;
      ET += 5.2 * dt;
    } else {
      // flattening around 230–238°C
      BT += (t % 0.6 < 0.3 ? 0.8 : -0.8) * dt;
      ET += (t % 0.8 < 0.4 ? 0.6 : -0.6) * dt;
    }

    pts.push({ t: +t.toFixed(3), BT: clamp(BT, 20, 240), ET: clamp(ET, 20, 236) });
  }
  return pts;
}

function clamp(n, a, b) {
  return Math.max(a, Math.min(b, n));
}
