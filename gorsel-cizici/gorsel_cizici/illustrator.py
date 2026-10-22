"""Çizimi açık Illustrator belgesine gönderme (Mac: AppleScript, Windows: COM)."""
from __future__ import annotations

import os
import subprocess
import sys

_JS = (
    '(function(){{var f=new File("{path}");'
    "if(app.documents.length==0){{app.open(f);return;}}"
    "var d=app.activeDocument;var g=d.groupItems.createFromFile(f);"
    "try{{var c=d.activeView.centerPoint;g.position=[c[0]-g.width/2,c[1]+g.height/2];}}catch(e){{}}"
    "try{{d.selection=null;g.selected=true;}}catch(e){{}}"
    "}})();"
)


def send(svg_path: str) -> tuple[bool, str]:
    """SVG dosyasını Illustrator'daki açık belgeye düzenlenebilir grup olarak yerleştir."""
    path = os.path.abspath(svg_path).replace("\\", "/")
    js = _JS.format(path=path.replace('"', '\\"'))
    if sys.platform == "darwin":
        script = (
            'tell application id "com.adobe.illustrator"\n'
            "activate\n"
            f"do javascript \"{js.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}\"\n"
            "end tell"
        )
        try:
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=60)
        except Exception as e:  # noqa: BLE001
            return False, str(e)
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "").strip()
            if "-1728" in err or "Can’t get application" in err or "can't get application" in err.lower():
                return False, "Adobe Illustrator bulunamadı."
            return False, err or "Illustrator'a gönderilemedi."
        return True, ""
    if sys.platform.startswith("win"):
        ps = (
            "$ai = New-Object -ComObject Illustrator.Application;"
            f"$ai.DoJavaScript('{js.replace(chr(39), chr(39) * 2)}')"
        )
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60)
        except Exception as e:  # noqa: BLE001
            return False, str(e)
        if r.returncode != 0:
            return False, (r.stderr or "Illustrator'a gönderilemedi.").strip()
        return True, ""
    return False, "Bu işletim sisteminde doğrudan gönderme yok; SVG'yi kaydedip Illustrator'da açın."
