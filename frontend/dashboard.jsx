// dashboard.jsx - recruiter-facing screen with URL generation + suite picker.

const { useState, useEffect } = React;
const API = "";

function Stat({ label, value, accent }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] px-6 py-5">
      <div className="text-4xl font-bold tabular-nums" style={{ color: accent }}>
        {value}
      </div>
      <div className="mt-1 text-xs uppercase tracking-widest text-zinc-500">
        {label}
      </div>
    </div>
  );
}

function App() {
  const [report, setReport] = useState(null);
  const [suites, setSuites] = useState([]);
  const [selected, setSelected] = useState("");
  const [url, setUrl] = useState("");
  const [running, setRunning] = useState(false);
  const [generating, setGenerating] = useState(false);

  const loadReport = () =>
    fetch(`${API}/api/report`).then((r) => r.json()).then(setReport);

  const loadSuites = () =>
    fetch(`${API}/api/suites`).then((r) => r.json()).then((s) => {
      setSuites(s);
      if (s.length && !selected) setSelected(s[0].path);
    });

  useEffect(() => { loadReport(); loadSuites(); }, []);

  const generate = async () => {
    if (!url) return alert("Enter a website URL first.");
    setGenerating(true);
    try {
      const r = await fetch(`${API}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await r.json();
      await loadSuites();
      setSelected(data.path);
      alert(`Generated ${data.steps} steps for ${data.name}`);
    } catch (e) {
      alert("Generate failed: " + e.message);
    } finally {
      setGenerating(false);
    }
  };

  const run = async () => {
    if (!selected) return alert("Pick a suite to run.");
    setRunning(true);
    try {
      const r = await fetch(`${API}/api/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ suite: selected, heal: true }),
      });
      setReport(await r.json());
    } catch (e) {
      alert("Run failed: " + e.message);
    } finally {
      setRunning(false);
    }
  };

  const healed = (report?.results || []).filter((r) => r.status === "healed");
  const failed = (report?.results || []).filter((r) => r.status === "failed");

  return (
    <div className="min-h-screen bg-[#0b0b0f] text-zinc-200 px-6 py-10 md:px-16">
      <header className="border-b border-white/10 pb-6">
        <h1 className="text-2xl font-semibold text-white tracking-tight">
          Aura<span className="text-amber-400">QA</span>
        </h1>
        <p className="text-sm text-zinc-500">Self-healing E2E test agent</p>
      </header>

      {/* Generate a suite from any URL */}
      <section className="mt-6 flex flex-wrap items-center gap-3">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://your-website.com"
          className="flex-1 min-w-[260px] rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-amber-400/50"
        />
        <button
          onClick={generate}
          disabled={generating}
          className="rounded-lg border border-amber-400/40 px-5 py-2.5 text-sm font-medium text-amber-300 hover:bg-amber-400/10 disabled:opacity-50"
        >
          {generating ? "Generating\u2026" : "Generate tests"}
        </button>
      </section>

      {/* Pick a suite + run it */}
      <section className="mt-3 flex flex-wrap items-center gap-3">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="flex-1 min-w-[260px] rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-zinc-200 outline-none"
        >
          {suites.length === 0 && <option value="">No suites yet</option>}
          {suites.map((s) => (
            <option key={s.path} value={s.path}>{s.name}</option>
          ))}
        </select>
        <button
          onClick={run}
          disabled={running}
          className="rounded-lg bg-amber-400 px-5 py-2.5 text-sm font-medium text-black hover:bg-amber-300 disabled:opacity-50"
        >
          {running ? "Running\u2026" : "Run tests"}
        </button>
      </section>

      <section className="mt-8 grid grid-cols-3 gap-4">
        <Stat label="Passed" value={report?.passed ?? 0} accent="#4ade80" />
        <Stat label="Healed" value={report?.healed ?? 0} accent="#fbbf24" />
        <Stat label="Failed" value={report?.failed ?? 0} accent="#f87171" />
      </section>

      <section className="mt-10">
        <h2 className="text-sm uppercase tracking-widest text-zinc-500 mb-3">
          Selectors the AI healed
        </h2>
        <div className="rounded-xl border border-white/10 overflow-hidden">
          {healed.length === 0 && (
            <p className="px-5 py-4 text-sm text-zinc-600">Nothing healed yet.</p>
          )}
          {healed.map((r, i) => (
            <div key={i} className="px-5 py-4 border-b border-white/5 last:border-0">
              <div className="text-sm text-zinc-300">{r.intent}</div>
              <div className="mt-1 flex items-center gap-2 text-xs font-mono">
                <span className="rounded bg-red-500/10 px-2 py-1 text-red-300">
                  {r.old_selector || "(none)"}
                </span>
                <span className="text-green-400">&rarr;</span>
                <span className="rounded bg-green-500/10 px-2 py-1 text-green-300">
                  {r.new_selector}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-sm uppercase tracking-widest text-zinc-500 mb-3">
          Genuine failures
        </h2>
        <div className="rounded-xl border border-white/10 overflow-hidden">
          {failed.length === 0 && (
            <p className="px-5 py-4 text-sm text-zinc-600">No failures.</p>
          )}
          {failed.map((r, i) => (
            <div key={i} className="px-5 py-4 border-b border-white/5 last:border-0">
              <div className="text-sm text-zinc-300">{r.intent}</div>
              <div className="mt-1 text-xs text-red-400 font-mono">{r.error}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
