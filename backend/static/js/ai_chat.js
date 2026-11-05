(function () {
  "use strict";
  var app = document.getElementById("ai-app");
  var $ = function (s) { return document.querySelector(s); };
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || "";

  function post(url, body) {
    return fetch(url, {
      method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf, "Accept": "application/json" },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (data) { return { ok: r.ok, status: r.status, data: data }; });
    });
  }
  function errText(res) {
    var d = res.data || {};
    if (d.error) return d.error;
    if (d.detail) return d.detail;
    var first = Object.keys(d)[0];
    return first ? first + ": " + [].concat(d[first]).join(" ") : "Request failed (HTTP " + res.status + ").";
  }

  // -------- AI Chat page
  if (app) {
    var chatUrl = app.dataset.chatUrl, genUrl = app.dataset.generateUrl;
    var convId = app.dataset.conversation ? parseInt(app.dataset.conversation, 10) : null;
    var log = $("#chat-log"), form = $("#chat-form"), input = $("#chat-input");

    var add = function (role, text, cls) {
      var d = document.createElement("div");
      d.className = "bubble " + role + (cls ? " " + cls : "");
      d.textContent = text;
      log.appendChild(d); log.scrollTop = log.scrollHeight;
      return d;
    };
    if (log) log.scrollTop = log.scrollHeight;

    if (form) form.addEventListener("submit", function (e) {
      e.preventDefault();
      var text = input.value.trim();
      if (!text) return;
      add("user", text); input.value = "";
      var wait = add("assistant", "Thinking…", "typing");
      var btn = form.querySelector("button"); btn.disabled = true;
      post(chatUrl, { message: text, conversation_id: convId }).then(function (res) {
        wait.remove(); btn.disabled = false;
        if (res.ok) {
          convId = res.data.conversation_id;
          var b = add("assistant", res.data.reply);
          var n = document.createElement("small"); n.textContent = "AI-generated draft - review before using."; b.appendChild(n);
        } else add("assistant", errText(res), "error");
      }).catch(function () { wait.remove(); btn.disabled = false; add("assistant", "Network error. Please try again.", "error"); });
    });
    if (input) input.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });

    var taskSel = $("#task-select"), taskInput = $("#task-input"), hint = $("#task-hint"), out = $("#task-output"), run = $("#task-run"), copy = $("#task-copy");
    if (taskSel) {
      var hints = JSON.parse(app.dataset.hints || "{}");
      var showHint = function () { hint.textContent = hints[taskSel.value] || ""; };
      taskSel.addEventListener("change", showHint); showHint();
      run.addEventListener("click", function () {
        out.textContent = "Generating…"; out.className = "output typing"; run.disabled = true;
        post(genUrl, { task: taskSel.value, input: taskInput.value, conversation_id: null }).then(function (res) {
          run.disabled = false;
          if (res.ok) { out.className = "output"; out.textContent = res.data.reply; copy.hidden = false; $("#task-notice").hidden = false; }
          else { out.className = "output"; out.textContent = errText(res); copy.hidden = true; }
        }).catch(function () { run.disabled = false; out.className = "output"; out.textContent = "Network error. Please try again."; });
      });
      copy.addEventListener("click", function () { if (navigator.clipboard) navigator.clipboard.writeText(out.textContent); });
    }
  }

  // -------- AI Insights page: "generate summary"
  var ins = $("#insight-run");
  if (ins) {
    var outEl = $("#insight-output");
    ins.addEventListener("click", function () {
      outEl.textContent = "Generating…"; ins.disabled = true;
      post(ins.dataset.url, { task: "public_insights", input: "" }).then(function (res) {
        ins.disabled = false;
        outEl.textContent = res.ok ? res.data.reply : errText(res);
      }).catch(function () { ins.disabled = false; outEl.textContent = "Network error. Please try again."; });
    });
  }
})();
