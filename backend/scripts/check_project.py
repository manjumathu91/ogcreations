"""Static consistency checks (no Django needed): template tag balance, {% url %} names,
template/static references, and Python name errors via compile. Run: python scripts/check_project.py"""
import ast, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
problems = []

# ---- collect URL names from urls.py files
names = set()
for path in ["apps/dashboard/urls.py", "apps/accounts/urls.py"]:
    app = re.search(r'app_name\s*=\s*"(\w+)"', open(path).read()).group(1)
    for n in re.findall(r'name="(\w+)"', open(path).read()):
        names.add(f"{app}:{n}")
tpl_files = []
for r, _, fs in os.walk("templates"):
    for f in fs:
        tpl_files.append(os.path.join(r, f))
tpl_rel = {os.path.relpath(p, "templates") for p in tpl_files}
static_rel = {os.path.relpath(os.path.join(r, f), "static") for r, _, fs in os.walk("static") for f in fs}

openers = {"if": "endif", "for": "endfor", "block": "endblock", "with": "endwith"}
for p in tpl_files:
    src = open(p).read()
    stack = []
    for m in re.finditer(r"{%\s*(\w+)([^%]*)%}", src):
        tag, rest = m.group(1), m.group(2)
        if tag in openers:
            stack.append(tag)
        elif tag in openers.values():
            if not stack or openers[stack[-1]] != tag:
                problems.append(f"{p}: unbalanced {tag} (stack {stack})")
            else:
                stack.pop()
        elif tag == "url":
            n = re.match(r"\s*['\"]([\w:]+)['\"]", rest)
            if n and n.group(1) not in names:
                problems.append(f"{p}: unknown url name {n.group(1)}")
        elif tag == "static":
            n = re.match(r"\s*['\"]([^'\"]+)['\"]", rest)
            if n and n.group(1) not in static_rel:
                problems.append(f"{p}: missing static file {n.group(1)}")
        elif tag in ("extends", "include"):
            n = re.match(r"\s*['\"]([^'\"]+)['\"]", rest)
            if n and n.group(1) not in tpl_rel:
                problems.append(f"{p}: missing template {n.group(1)}")
    if stack:
        problems.append(f"{p}: unclosed tags {stack}")
    for v in re.findall(r"{{[^}]*}}", src):
        if v.count("(") or v.count("["):
            problems.append(f"{p}: suspicious variable syntax {v}")

# ---- templates referenced from python
for p in [os.path.join(r, f) for r, _, fs in os.walk("apps") for f in fs if f.endswith(".py")]:
    src = open(p).read()
    for t in re.findall(r'["\']((?:dashboard|accounts|emails)/[\w/]+\.html|\d{3}\.html)["\']', src):
        if t not in tpl_rel:
            problems.append(f"{p}: missing template {t}")
    for n in re.findall(r'(?:reverse|redirect)\(\s*["\'](\w+:\w+)["\']', src):
        if n not in names and not n.startswith("api"):
            problems.append(f"{p}: unknown url name {n}")

# ---- Python: undefined names (simple) using compile + pyflakes if present
try:
    import pyflakes.api, pyflakes.reporter
    class R(pyflakes.reporter.Reporter):
        def unexpectedError(self, *a): pass
        def syntaxError(self, *a): problems.append("syntax: %s" % (a,))
        def flake(self, msg):
            s = str(msg)
            if "undefined name" in s or "unable to detect undefined names" in s:
                problems.append(s)
    for r, _, fs in os.walk("."):
        if "migrations" in r or r.startswith("./scripts"):
            continue
        for f in fs:
            if f.endswith(".py"):
                pyflakes.api.checkPath(os.path.join(r, f), R(sys.stdout, sys.stderr))
except ImportError:
    print("(pyflakes not installed - skipped undefined-name check)")

print("\n".join(problems) if problems else "No problems found")
sys.exit(1 if problems else 0)
