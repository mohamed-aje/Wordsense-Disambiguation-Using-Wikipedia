# WSD Client

Minimal React UI to run Lesk with WordNet or Wikipedia against a sentence and target word.

## Run locally

```bash
npm install
npm start
```

Backend should run at http://127.0.0.1:8000 (a dev proxy is configured in `package.json`).

## Build

```bash
npm run build
```

The UI renders a form (sentence, target, POS) and supports choosing WordNet or Wikipedia, then displays the best sense and candidate list with overlap details.
