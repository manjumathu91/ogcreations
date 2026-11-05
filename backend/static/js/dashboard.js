(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // sidebar (mobile) + collapsible groups
  var shell = $(".shell");
  var burger = $("#burger");
  if (burger && shell) burger.addEventListener("click", function () { shell.classList.toggle("open"); });
  var overlay = $("#overlay");
  if (overlay && shell) overlay.addEventListener("click", function () { shell.classList.remove("open"); });
  $$(".group-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var g = btn.parentElement;
      g.classList.toggle("open");
      btn.setAttribute("aria-expanded", g.classList.contains("open") ? "true" : "false");
    });
  });
  var activeLink = $(".nav-link.active");
  if (activeLink && activeLink.scrollIntoView) activeLink.scrollIntoView({ block: "center" });

  // toasts auto-dismiss
  $$(".toast").forEach(function (t, i) {
    setTimeout(function () { t.style.opacity = "0"; t.style.transition = "opacity .4s"; setTimeout(function () { t.remove(); }, 450); }, 5000 + i * 600);
    t.addEventListener("click", function () { t.remove(); });
  });

  // confirmation dialog for destructive forms: <form data-confirm="..." data-confirm-title="...">
  var dialog = $("#confirm-dialog");
  var pending = null;
  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (form.dataset && form.dataset.confirm && !form.dataset.confirmed && dialog && dialog.showModal) {
      e.preventDefault();
      pending = form;
      $("#confirm-title", dialog).textContent = form.dataset.confirmTitle || "Are you sure?";
      $("#confirm-text", dialog).textContent = form.dataset.confirm;
      dialog.showModal();
      return;
    }
    var btn = e.submitter || $("button[type=submit]", form);
    if (btn && btn.classList.contains("btn")) {
      setTimeout(function () { btn.classList.add("loading"); }, 0);
    }
  });
  if (dialog) {
    $("#confirm-yes", dialog).addEventListener("click", function () {
      dialog.close();
      if (pending) { pending.dataset.confirmed = "1"; pending.requestSubmit ? pending.requestSubmit() : pending.submit(); pending = null; }
    });
    $("#confirm-no", dialog).addEventListener("click", function () { dialog.close(); pending = null; });
  }

  // auto-submit selects/filters
  $$("[data-autosubmit]").forEach(function (el) {
    el.addEventListener("change", function () { if (el.form) el.form.submit(); });
  });

  // copy to clipboard: <button data-copy="text">
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-copy]");
    if (!b) return;
    var text = b.dataset.copy;
    if (text.charAt(0) === "/") text = location.origin + text;
    var done = function () { var old = b.title; b.title = "Copied!"; b.classList.add("copied"); setTimeout(function () { b.title = old; b.classList.remove("copied"); }, 1200); };
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(done); else done();
  });

  // live preview when choosing an image file
  $$("input[type=file]").forEach(function (input) {
    input.addEventListener("change", function () {
      if (!input.files || !input.files[0] || input.files[0].type.indexOf("image/") !== 0) return;
      var box = input.parentElement.querySelector(".current-img");
      if (!box) { box = document.createElement("div"); box.className = "current-img"; input.parentElement.insertBefore(box, input); }
      var img = box.querySelector("img") || box.appendChild(document.createElement("img"));
      img.src = URL.createObjectURL(input.files[0]);
    });
  });
})();
