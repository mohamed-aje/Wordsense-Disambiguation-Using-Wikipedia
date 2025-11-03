import { useState } from "react";
import "./App.css";

const DEFAULT_SENTENCE = "He deposited money in the bank";
const DEFAULT_TARGET = "bank";

function App() {
  const [sentence, setSentence] = useState(DEFAULT_SENTENCE);
  const [target, setTarget] = useState(DEFAULT_TARGET);
  const [pos, setPos] = useState("");
  const [source, setSource] = useState("wordnet");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [expMessage, setExpMessage] = useState("");
  const [corrResults, setCorrResults] = useState(null);
  const [convexResults, setConvexResults] = useState(null);
  const [convexDataset, setConvexDataset] = useState("WS353");
  const [convexBase, setConvexBase] = useState("fasttext");
  const [aquaintRunId, setAquaintRunId] = useState("");
  const [aquaintRunData, setAquaintRunData] = useState(null);
  const [pairsText, setPairsText] = useState("car,automobile\nking,queen");
  const [simResults, setSimResults] = useState(null);

  async function runWSD(which) {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const endpoint =
        which === "wikipedia" ? "/api/lesk/wiki" : "/api/lesk/wordnet";
      const body = { sentence, target };
      if (which === "wordnet" && pos) body.pos = pos;
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResult({ which, data });
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }

  const best = result?.data?.best_sense;
  const candidates = result?.data?.candidates || [];

  return (
    <div className="container">
      <h1>Word Sense Disambiguation</h1>
      <p className="subtitle">Compare Lesk using WordNet vs Wikipedia</p>

      <div className="card">
        <div className="form-row">
          <label>Sentence</label>
          <textarea
            rows={3}
            value={sentence}
            onChange={(e) => setSentence(e.target.value)}
          />
        </div>
        <div className="form-row cols">
          <div>
            <label>Target</label>
            <input value={target} onChange={(e) => setTarget(e.target.value)} />
          </div>
          <div>
            <label>POS (WordNet)</label>
            <select value={pos} onChange={(e) => setPos(e.target.value)}>
              <option value="">Any</option>
              <option value="n">Noun (n)</option>
              <option value="v">Verb (v)</option>
              <option value="a">Adjective (a)</option>
              <option value="r">Adverb (r)</option>
            </select>
          </div>
          <div>
            <label>Source</label>
            <div className="toggle">
              <label>
                <input
                  type="radio"
                  name="source"
                  value="wordnet"
                  checked={source === "wordnet"}
                  onChange={() => setSource("wordnet")}
                />
                WordNet
              </label>
              <label>
                <input
                  type="radio"
                  name="source"
                  value="wikipedia"
                  checked={source === "wikipedia"}
                  onChange={() => setSource("wikipedia")}
                />
                Wikipedia
              </label>
            </div>
          </div>
        </div>
        <div className="actions">
          <button disabled={loading} onClick={() => runWSD(source)}>
            {loading
              ? "Running…"
              : `Run ${source === "wordnet" ? "WordNet" : "Wikipedia"}`}
          </button>
          <button
            className="ghost"
            disabled={loading}
            onClick={() => {
              setSentence(DEFAULT_SENTENCE);
              setTarget(DEFAULT_TARGET);
              setPos("");
              setResult(null);
              setError("");
            }}
          >
            Reset
          </button>
        </div>
        {error && <div className="error">{error}</div>}
      </div>

      {best && (
        <div className="card">
          <div className="result-header">
            <span className="badge">Best ({source})</span>
          </div>
          {source === "wordnet" ? (
            <div>
              <div className="kv">
                <span className="k">Synset</span>
                <span className="v mono">{best.synset}</span>
              </div>
              <div className="kv">
                <span className="k">Definition</span>
                <span className="v">{best.definition}</span>
              </div>
              {best.examples?.length > 0 && (
                <div className="kv">
                  <span className="k">Examples</span>
                  <span className="v small">{best.examples.join(" | ")}</span>
                </div>
              )}
              <div className="kv">
                <span className="k">Overlap</span>
                <span className="v">
                  {best.overlap_count} ({(best.overlaps || []).join(", ")})
                </span>
              </div>
            </div>
          ) : (
            <div>
              <div className="kv">
                <span className="k">Title</span>
                <span className="v">{best.title}</span>
              </div>
              <div className="kv">
                <span className="k">Summary</span>
                <span className="v">{best.summary}</span>
              </div>
              {best.url && (
                <div className="kv">
                  <span className="k">URL</span>
                  <span className="v">
                    <a href={best.url} target="_blank" rel="noreferrer">
                      {best.url}
                    </a>
                  </span>
                </div>
              )}
              <div className="kv">
                <span className="k">Overlap</span>
                <span className="v">
                  {best.overlap_count} ({(best.overlaps || []).join(", ")})
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {candidates.length > 0 && (
        <div className="card">
          <div className="result-header">
            <span className="badge">Candidates ({candidates.length})</span>
          </div>
          <div className="list">
            {candidates.map((c, idx) => (
              <div className="list-item" key={idx}>
                {source === "wordnet" ? (
                  <div>
                    <div className="row">
                      <span className="mono bold">{c.synset}</span>
                    </div>
                    <div className="row small">{c.definition}</div>
                    <div className="row tiny mute">
                      overlap: {c.overlap_count}
                      {c.overlaps?.length ? ` · ${c.overlaps.join(", ")}` : ""}
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="row bold">{c.title}</div>
                    <div className="row small">{c.summary}</div>
                    <div className="row tiny mute">
                      overlap: {c.overlap_count}
                      {c.overlaps?.length ? ` · ${c.overlaps.join(", ")}` : ""}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="result-header">
          <span className="badge">Experiments</span>
        </div>

        <div className="form-row">
          <label>WikiSim similarity (ad-hoc pairs)</label>
          <textarea
            rows={4}
            value={pairsText}
            onChange={(e) => setPairsText(e.target.value)}
            placeholder={"word1,word2 one per line"}
          />
          <div className="actions">
            <button
              disabled={loading}
              onClick={async () => {
                setExpMessage("");
                setSimResults(null);
                try {
                  const lines = pairsText
                    .split("\n")
                    .map((l) => l.trim())
                    .filter(Boolean);
                  const pairs = lines
                    .map((l) => l.split(/[\s,]+/).slice(0, 2))
                    .filter((a) => a.length === 2 && a[0] && a[1]);
                  if (!pairs.length)
                    throw new Error("Provide at least one 'word1,word2' line");
                  const res = await fetch("/api/wikisim/similarity", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ pairs }),
                  });
                  if (!res.ok) throw new Error(await res.text());
                  const data = await res.json();
                  setSimResults(data.results || []);
                } catch (e) {
                  setExpMessage(String(e.message || e));
                }
              }}
            >
              Run WikiSim pairs
            </button>
          </div>
          {simResults && (
            <div className="list" style={{ marginTop: 12 }}>
              {simResults.map((r, i) => (
                <div className="list-item" key={i}>
                  <div className="row">
                    <span className="mono">{r.a}</span>
                    <span style={{ margin: "0 6px" }}>·</span>
                    <span className="mono">{r.b}</span>
                  </div>
                  <div className="row tiny mute">
                    score:{" "}
                    {r.score === null || r.score === undefined
                      ? "n/a"
                      : Number(r.score).toFixed(4)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="form-row cols">
          <div>
            <label>AQUAINT batch (first 50 files)</label>
            <div className="actions">
              <button
                disabled={loading}
                onClick={async () => {
                  setExpMessage("");
                  try {
                    const res = await fetch("/api/aquaint/run", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        target,
                        limit: 50,
                        method: source,
                      }),
                    });
                    if (!res.ok) throw new Error(await res.text());
                    const data = await res.json();
                    setExpMessage(
                      `Run ${data.run_id}: processed=${data.processed}, found_sentences=${data.found_sentences} → saved to ${data.results_file}`
                    );
                    setAquaintRunId(data.run_id || "");
                  } catch (e) {
                    setExpMessage(String(e.message || e));
                  }
                }}
              >
                Run AQUAINT batch
              </button>
            </div>
          </div>

          <div>
            <label>Correlation (MC, RG, WS353)</label>
            <div className="actions">
              <button
                disabled={loading}
                onClick={async () => {
                  setCorrResults(null);
                  setExpMessage("");
                  try {
                    const res = await fetch("/api/eval/correlation", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ datasets: ["MC", "RG", "WS353"] }),
                    });
                    if (!res.ok) throw new Error(await res.text());
                    const data = await res.json();
                    setCorrResults(data.results || data);
                  } catch (e) {
                    setExpMessage(String(e.message || e));
                  }
                }}
              >
                Run correlations
              </button>
            </div>
          </div>
        </div>

        {expMessage && <div className="small">{expMessage}</div>}

        {corrResults && (
          <div className="list" style={{ marginTop: 12 }}>
            {Object.entries(corrResults).map(([ds, methods]) => (
              <div className="list-item" key={ds}>
                <div className="row bold">{ds}</div>
                <div className="row tiny mute">
                  {Object.entries(methods).map(([m, v]) => (
                    <span key={m} style={{ marginRight: 12 }}>
                      {m}:{" "}
                      {v === null || v === undefined ? "n/a" : v.toFixed(4)}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        <hr style={{ opacity: 0.15, margin: "16px 0" }} />

        <div>
          <label>Convex combo (WikiSim + embedding)</label>
          <div className="form-row cols">
            <div>
              <label>Dataset</label>
              <select
                value={convexDataset}
                onChange={(e) => setConvexDataset(e.target.value)}
              >
                <option value="MC">MC</option>
                <option value="RG">RG</option>
                <option value="WS353">WS353</option>
              </select>
            </div>
            <div>
              <label>Base embedding</label>
              <select
                value={convexBase}
                onChange={(e) => setConvexBase(e.target.value)}
              >
                <option value="fasttext">fasttext</option>
                <option value="glove">glove</option>
                <option value="word2vec">word2vec</option>
              </select>
            </div>
          </div>
          <div className="actions">
            <button
              disabled={loading}
              onClick={async () => {
                setConvexResults(null);
                setExpMessage("");
                try {
                  const res = await fetch("/api/eval/convex", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      dataset: convexDataset,
                      base: convexBase,
                    }),
                  });
                  if (!res.ok) throw new Error(await res.text());
                  const data = await res.json();
                  setConvexResults(data.results || data);
                } catch (e) {
                  setExpMessage(String(e.message || e));
                }
              }}
            >
              Sweep alpha
            </button>
          </div>
          {convexResults && (
            <div className="list" style={{ marginTop: 12 }}>
              <div className="list-item">
                <div className="row bold">
                  Alpha → Spearman (WikiSim ⊕ {convexBase})
                </div>
                <div className="row tiny mute">
                  {Object.entries(convexResults).map(([a, v]) => (
                    <span key={a} style={{ marginRight: 10 }}>
                      {a}: {Number.isFinite(v) ? v.toFixed(4) : "n/a"}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <hr style={{ opacity: 0.15, margin: "16px 0" }} />

        <div>
          <label>View AQUAINT run results (by run_id)</label>
          <div className="form-row cols">
            <div>
              <input
                placeholder="run_id"
                value={aquaintRunId}
                onChange={(e) => setAquaintRunId(e.target.value)}
              />
            </div>
            <div className="actions">
              <button
                disabled={loading || !aquaintRunId}
                onClick={async () => {
                  setAquaintRunData(null);
                  setExpMessage("");
                  try {
                    const res = await fetch(
                      `/api/aquaint/result?run_id=${encodeURIComponent(
                        aquaintRunId
                      )}`
                    );
                    if (!res.ok) throw new Error(await res.text());
                    const data = await res.json();
                    setAquaintRunData(data);
                  } catch (e) {
                    setExpMessage(String(e.message || e));
                  }
                }}
              >
                Load run
              </button>
            </div>
          </div>
          {aquaintRunData && (
            <div className="list" style={{ marginTop: 12 }}>
              <div className="list-item">
                <div className="row bold">
                  {aquaintRunData.run_id} · processed={aquaintRunData.processed}{" "}
                  · found=
                  {aquaintRunData.found_sentences}
                </div>
                <div className="row tiny mute">
                  target: {aquaintRunData.target} · method:{" "}
                  {aquaintRunData.method}
                </div>
              </div>
              {(aquaintRunData.results || []).slice(0, 5).map((r, i) => (
                <div className="list-item" key={i}>
                  <div className="row small mono">{r.file}</div>
                  <div className="row tiny">
                    {r.sentence || "(no sentence containing target)"}
                  </div>
                  <div className="row tiny mute">
                    candidates: {r.candidates_count}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <footer className="footer">
        Created by Mohamed Al-Ajily & Saara Laasonen & Abu Roman.
      </footer>
    </div>
  );
}

export default App;
