"""Minimal browser UI for the SilentLine prototype."""

from fastapi.responses import HTMLResponse


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SilentLine</title>
  <style>
    :root { color-scheme: light; font-family: system-ui, sans-serif; }
    body { margin: 0; background: #f3f5f7; color: #17212b; }
    main { max-width: 860px; margin: auto; padding: 2rem 1rem 4rem; }
    header, section { background: white; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 2px 12px #17212b12; }
    h1 { margin-top: 0; } h2 { margin-top: 0; font-size: 1.2rem; }
    .warning { background: #fff3cd; border-left: 4px solid #d39e00; padding: .8rem; }
    label { display: block; font-weight: 600; margin: .8rem 0 .35rem; }
    textarea, input, select { box-sizing: border-box; width: 100%; padding: .7rem; border: 1px solid #b8c2cc; border-radius: 7px; font: inherit; }
    textarea { min-height: 150px; resize: vertical; }
    button { border: 0; border-radius: 7px; padding: .7rem 1rem; background: #155eef; color: white; cursor: pointer; margin: .7rem .4rem .1rem 0; }
    button.secondary { background: #52606d; } button:disabled { opacity: .6; cursor: wait; }
    .result { white-space: pre-wrap; background: #eef6ff; padding: .8rem; border-radius: 7px; }
    .error { color: #a61b1b; } .muted { color: #52606d; }
    table { border-collapse: collapse; width: 100%; } th, td { text-align: left; border-bottom: 1px solid #d9e0e6; padding: .6rem; vertical-align: top; }
    .hidden { display: none; }
  </style>
</head>
<body>
<main>
  <header>
    <h1>SilentLine</h1>
    <p>Privacy-first occupational reporting prototype.</p>
    <p class="warning"><strong>Not for real reports.</strong> PII removal is not anonymity. Story details may still identify you.</p>
  </header>

  <section>
    <h2>Submit a report</h2>
    <p class="muted">Use typed text or record a short fictional demo report. Original audio is processed transiently.</p>
    <label for="category">Category</label>
    <select id="category">
      <option value="other">Other</option><option value="harassment">Harassment</option>
      <option value="academic_dishonesty">Academic dishonesty</option><option value="misuse_of_funds">Misuse of funds</option>
      <option value="favoritism">Favoritism</option><option value="safety">Safety</option>
    </select>
    <label for="report-text">Typed report</label>
    <textarea id="report-text" placeholder="Describe a fictional concern..."></textarea>
    <button id="submit-text">Submit typed report</button>
    <button id="record" class="secondary">Start recording</button>
    <span id="recording-status" class="muted"></span>
    <div id="submit-result" class="result hidden"></div>
  </section>

  <section>
    <h2>Return to a case</h2>
    <label for="case-id">Case ID</label><input id="case-id" autocomplete="off">
    <label for="case-passphrase">Passphrase</label><input id="case-passphrase" type="password" autocomplete="off">
    <button id="lookup">Look up case</button>
    <div id="lookup-result" class="result hidden"></div>
  </section>

  <section>
    <h2>Investigator access</h2>
    <label for="investigator-password">Investigator password</label>
    <input id="investigator-password" type="password" autocomplete="off">
    <button id="login">Sign in</button>
    <button id="reports" class="secondary hidden">Load reports</button>
    <div id="investigator-result" class="result hidden"></div>
  </section>
</main>
<script>
const $ = id => document.getElementById(id);
const show = (element, text, error = false) => {
  element.textContent = text; element.classList.remove("hidden");
  element.classList.toggle("error", error);
};
const jsonRequest = async (url, options) => {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail?.message || body.detail || "Request failed");
  return body;
};

$("submit-text").onclick = async () => {
  const button = $("submit-text");
  button.disabled = true;
  try {
    const body = await jsonRequest("/reports/text", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: $("report-text").value, category: $("category").value})
    });
    show($("submit-result"), `Case ID: ${body.case_id}\nPassphrase: ${body.passphrase}\n\nScrubbed report:\n${body.transcript_scrubbed}\n\nSave the case ID and passphrase. The passphrase is shown only once.`);
    $("report-text").value = "";
  } catch (error) { show($("submit-result"), error.message, true); }
  finally { button.disabled = false; }
};

let recorder, chunks = [];
$("record").onclick = async () => {
  if (recorder?.state === "recording") { recorder.stop(); return; }
  if (!navigator.mediaDevices?.getUserMedia) { show($("submit-result"), "Recording is unavailable; use typed text.", true); return; }
  const stream = await navigator.mediaDevices.getUserMedia({audio: true});
  recorder = new MediaRecorder(stream); chunks = [];
  recorder.ondataavailable = event => chunks.push(event.data);
  recorder.onstop = async () => {
    stream.getTracks().forEach(track => track.stop());
    $("recording-status").textContent = "Processing recording...";
    try {
      const body = await jsonRequest(`/reports/audio?category=${encodeURIComponent($("category").value)}`, {
        method: "POST", headers: {"Content-Type": recorder.mimeType || "audio/webm"},
        body: new Blob(chunks, {type: recorder.mimeType || "audio/webm"})
      });
      show($("submit-result"), `Case ID: ${body.case_id}\nPassphrase: ${body.passphrase}\n\nScrubbed report:\n${body.transcript_scrubbed}`);
    } catch (error) { show($("submit-result"), error.message, true); }
    $("recording-status").textContent = "";
  };
  recorder.start(); $("record").textContent = "Stop recording"; $("recording-status").textContent = "Recording...";
};

$("lookup").onclick = async () => {
  try {
    const body = await jsonRequest("/cases/lookup", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({case_id: $("case-id").value, passphrase: $("case-passphrase").value})
    });
    show($("lookup-result"), `Category: ${body.category}\nDate: ${body.created_date}\n\n${body.transcript_scrubbed}`);
  } catch (error) { show($("lookup-result"), error.message, true); }
};

let investigatorToken = "";
$("login").onclick = async () => {
  try {
    const body = await jsonRequest("/investigator/login", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({password: $("investigator-password").value})
    });
    investigatorToken = body.token; $("investigator-password").value = "";
    $("reports").classList.remove("hidden"); show($("investigator-result"), "Signed in. Token is kept only in this page.");
  } catch (error) { show($("investigator-result"), error.message, true); }
};
$("reports").onclick = async () => {
  try {
    const reports = await jsonRequest("/investigator/reports", {headers: {"Authorization": `Bearer ${investigatorToken}`}});
    show($("investigator-result"), reports.length ? reports.map(report => `${report.case_id} | ${report.category} | ${report.created_date}\n${report.transcript_scrubbed}`).join("\n\n") : "No reports found.");
  } catch (error) { show($("investigator-result"), error.message, true); }
};
</script>
</body>
</html>"""


def render_home() -> HTMLResponse:
    return HTMLResponse(PAGE)
