"""HTML-Report erzeugen und per Apple Mail verschicken."""
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from .common import CheckResult

TEMPLATE = Template(
    """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Abschlusslink-Check {{ datum }}</title>
<style>
  body { font-family: -apple-system, Helvetica, Arial, sans-serif; margin: 24px; color: #1a2b3c; }
  h1 { font-size: 22px; } h2 { font-size: 17px; margin-top: 28px; }
  .zusammenfassung { padding: 12px 16px; border-radius: 8px; margin: 12px 0;
    background: {{ '#e6f4ea' if fehler == 0 and pruefbedarf == 0 else '#fff8e1' if fehler == 0 else '#fdecea' }};
    border: 1px solid {{ '#34a853' if fehler == 0 and pruefbedarf == 0 else '#f9ab00' if fehler == 0 else '#ea4335' }}; }
  table { border-collapse: collapse; width: 100%; margin-top: 8px; }
  th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #ddd;
           font-size: 13px; vertical-align: top; }
  .ok { color: #188038; font-weight: 600; }
  .warnung { color: #b06000; font-weight: 600; }
  .fehler { color: #c5221f; font-weight: 600; }
  .url { color: #666; font-size: 11px; word-break: break-all; }
  details ul { margin: 4px 0; padding-left: 18px; }
  li { font-size: 12px; }
  .neu { background: #fff8e1; }
</style>
</head>
<body>
<h1>{{ titel }} &ndash; {{ datum }}</h1>
<div class="zusammenfassung">
  <strong>{{ 'Alles in Ordnung.' if fehler == 0 and pruefbedarf == 0 else ((pruefbedarf ~ ' Ergebnis(se) manuell prüfen.') if fehler == 0 else (fehler ~ ' Defekt(e) gefunden!')) }}</strong><br>
  {{ funnel_ok }}/{{ funnel_gesamt }} Abschlussstrecken erfolgreich bis zum Abschluss-Button durchgeklickt,
  {{ http_ok }}/{{ http_gesamt }} Links erreichbar,
  {{ dl_ok }}/{{ dl_gesamt }} Downloads in Ordnung.
</div>

{% if neue or verschwundene %}
<h2>Veränderungen seit dem letzten Lauf</h2>
<ul>
  {% for url in neue %}<li class="neu">NEU: {{ url }}</li>{% endfor %}
  {% for url in verschwundene %}<li>NICHT MEHR GEFUNDEN: {{ url }}</li>{% endfor %}
</ul>
{% endif %}

<h2>Abschlussstrecken (Klick-Test)</h2>
<table>
<tr><th>Status</th><th>Tarif / Strecke</th><th>Schritte</th><th>Details</th></tr>
{% for r in funnels %}
<tr>
  <td class="{{ 'ok' if r.status in ('OK', 'WEITERLEITUNG_OK') else ('fehler' if r.status == 'DEFEKT' else 'warnung') }}">{{ r.status }}</td>
  <td><strong>{{ r.link.gesellschaft or '-' }}</strong><br>{{ r.link.tarif or '-' }} ({{ r.link.typ }})
    <div class="url">{{ r.link.url }}</div>
    {% if r.link.tarife %}<details><summary>{{ r.link.tarife | length }} zugeordnete Tarife</summary><ul>
      {% for t in r.link.tarife %}<li>{{ t.name }} – {{ t.tarifseite }}</li>{% endfor %}
    </ul></details>{% endif %}
  </td>
  <td>{{ r.steps_done }}</td>
  <td>
    {% if r.stop_button %}Abschluss-Button erreicht: &bdquo;{{ r.stop_button }}&ldquo;<br>{% endif %}
    <details><summary>Protokoll ({{ r.details | length }} Einträge)</summary>
      <ul>{% for d in r.details %}<li>{{ d }}</li>{% endfor %}</ul>
      {% if r.screenshots %}Screenshots: {% for s in r.screenshots %}<a href="screenshots/{{ s }}">{{ s }}</a> {% endfor %}{% endif %}
    </details>
  </td>
</tr>
{% endfor %}
</table>

<h2>Erreichbarkeit aller Links</h2>
<table>
<tr><th>Status</th><th>Link</th><th>Details</th></tr>
{% for r in https %}
<tr>
  <td class="{{ 'ok' if r.status in ('OK', 'WEITERLEITUNG_OK') else ('fehler' if r.status == 'DEFEKT' else 'warnung') }}">{{ r.status }}</td>
  <td><strong>{{ r.link.gesellschaft or '-' }}</strong><br>{{ r.link.tarif or r.link.kategorie }}<div class="url">{{ r.link.url }}</div></td>
  <td>{{ r.details | join(' | ') }}</td>
</tr>
{% endfor %}
</table>

<h2>Downloads</h2>
{% if downloads %}
<table>
<tr><th>Status</th><th>Datei</th><th>Details</th></tr>
{% for r in downloads %}
<tr>
  <td class="{{ 'ok' if r.status in ('OK', 'WEITERLEITUNG_OK') else ('fehler' if r.status == 'DEFEKT' else 'warnung') }}">{{ r.status }}</td>
  <td class="url">{{ r.link.url }}<br>gefunden auf: {{ r.link.quelle }}</td>
  <td>{{ r.details | join(' | ') }}</td>
</tr>
{% endfor %}
</table>
{% else %}<p>Keine Downloads gefunden.</p>{% endif %}

<p style="color:#999; font-size:11px; margin-top:32px;">
Erzeugt am {{ erzeugt }} vom OVV-LinkChecker. Es wurde kein Antrag abgesendet;
Abschluss-Buttons werden erreicht, aber nie geklickt.
</p>
</body>
</html>"""
)


def build_report(
    run_dir: Path,
    funnels: list[CheckResult],
    https: list[CheckResult],
    downloads: list[CheckResult],
    neue: list[str],
    verschwundene: list[str],
    titel: str = "Wöchentlicher Abschlusslink-Check",
) -> tuple[Path, str, int]:
    """HTML-Report schreiben. Gibt (Pfad, Betreff, Fehlerzahl) zurück."""
    datum = run_dir.name
    fehler = sum(1 for r in funnels + https + downloads if r.status == "DEFEKT")
    pruefbedarf = sum(
        1 for r in funnels + https + downloads if r.status == "MANUELL_PRÜFEN"
    )
    html = TEMPLATE.render(
        datum=datum,
        titel=titel,
        erzeugt=datetime.now().strftime("%d.%m.%Y %H:%M"),
        fehler=fehler,
        pruefbedarf=pruefbedarf,
        funnels=sorted(funnels, key=lambda r: (r.status != "DEFEKT", r.status != "MANUELL_PRÜFEN")),
        https=sorted(https, key=lambda r: (r.status != "DEFEKT", r.status != "MANUELL_PRÜFEN")),
        downloads=sorted(downloads, key=lambda r: (r.status != "DEFEKT", r.status != "MANUELL_PRÜFEN")),
        funnel_ok=sum(1 for r in funnels if r.status == "OK"),
        funnel_gesamt=len(funnels),
        http_ok=sum(1 for r in https if r.status in ("OK", "WEITERLEITUNG_OK")),
        http_gesamt=len(https),
        dl_ok=sum(1 for r in downloads if r.status == "OK"),
        dl_gesamt=len(downloads),
        neue=neue,
        verschwundene=verschwundene,
    )
    report_path = run_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")

    if fehler == 0 and pruefbedarf == 0:
        subject = f"[Linkcheck] OK – {sum(1 for r in funnels if r.status == 'OK')}/{len(funnels)} Strecken in Ordnung"
    elif fehler == 0:
        subject = f"[Linkcheck] PRÜFBEDARF – {pruefbedarf} Ergebnis(se) manuell prüfen"
    else:
        subject = f"[Linkcheck] FEHLER – {fehler} Problem(e) gefunden"
    return report_path, subject, fehler


def send_via_apple_mail(
    report_path: Path, subject: str, body: str, recipient: str, sender: str = ""
) -> bool:
    """Report als Anhang über Apple Mail verschicken (AppleScript)."""
    sender_line = f'set sender of neueNachricht to "{sender}"' if sender else ""
    script = f'''
    tell application "Mail"
        set neueNachricht to make new outgoing message with properties {{subject:"{subject}", content:"{body}\n\n", visible:false}}
        {sender_line}
        tell neueNachricht
            make new to recipient at end of to recipients with properties {{address:"{recipient}"}}
            make new attachment with properties {{file name:POSIX file "{report_path}"}} at after the last paragraph
        end tell
        delay 2
        send neueNachricht
    end tell
    '''
    try:
        proc = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=120
        )
        return proc.returncode == 0
    except Exception:
        return False


def notify_macos(title: str, text: str) -> None:
    """macOS-Mitteilung als Fallback, wenn der Mailversand scheitert."""
    script = f'display notification "{text}" with title "{title}"'
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=15)
    except Exception:
        pass
