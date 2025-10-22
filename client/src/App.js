import { useState } from "react";
import "./App.css";

const DEFAULT_SENTENCE = "This plant requires watering every morning";
const DEFAULT_TARGET = "plant";

function App() {
  const [sentence, setSentence] = useState(DEFAULT_SENTENCE);
  const [target, setTarget] = useState(DEFAULT_TARGET);
  const [pos, setPos] = useState("");
  const [source, setSource] = useState("wordnet");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

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
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Request failed with ${res.status}`);
      }
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
            value={sentence}
            onChange={(e) => setSentence(e.target.value)}
            rows={3}
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
                />{" "}
                WordNet
              </label>
              <label>
                <input
                  type="radio"
                  name="source"
                  value="wikipedia"
                  checked={source === "wikipedia"}
                  onChange={() => setSource("wikipedia")}
                />{" "}
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

      <footer className="footer">
        Created by Mohamed Al-Ajily & Saara Laasonen & Abu Roman.
      </footer>
    </div>
  );
}

export default App;
