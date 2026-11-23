"""Klistrar in app.js i Lagets_poangliga.html (mellan <script> och </script>)
och kopierar resultatet till index.html i reporoten (för GitHub Pages).

Kör: python src/filapp/build.py
"""
from pathlib import Path
import re

here = Path(__file__).resolve().parent
html_path = here / "Lagets_poangliga.html"
js = (here / "app.js").read_text(encoding="utf-8").strip()
html = html_path.read_text(encoding="utf-8")

new, n = re.subn(r"(<script>\n).*?(\n</script>)", lambda m: m.group(1) + js + m.group(2), html, count=1, flags=re.S)
if n != 1:
    raise SystemExit("Hittade inget <script>-block i Lagets_poangliga.html")

html_path.write_text(new, encoding="utf-8", newline="\n")
(here.parent.parent / "index.html").write_text(new, encoding="utf-8", newline="\n")
print("Byggt:", html_path.name, "+ index.html")
