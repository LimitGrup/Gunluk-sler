#!/usr/bin/env python3
"""Dayanıklılık testi: gerçek A belge modellerinden (idml2json çıktısı) değiştirilmiş varyasyonlar üretir.
Kullanım: python3 -I fuzz.py <çıktı_klasörü> <model.json> [<model.json> ...]
Varyasyonlar:
  boyN      : soruların ~%40'ının yüksekliği rastgele %0-30 kısaltılır (tohum N)
  yonergesiz: ortak metin yönergeleri ("8 ve 9. soruları ... göre", "Answer the questions ...") silinir
  surekli   : (yalnız ders aralığı olmayan belgeler) numaralar branşlar arasında sıfırlanmadan sürer
Her varyasyona bağımsız denetim için A'daki branş (test) ve ortak metin grubu bilgisi yazılır:
  branchOf: {hikâye id: branş no}, origGroups: [{pg, sids}]"""
import sys, os, json, re, copy, random

QRE = re.compile(r"^[\s​﻿￼\u009e]*(\d{1,3})\.(?=[\s\t])")
DIR_TR = re.compile(r"(\d{1,3})\s*[-–]\s*(\d{1,3})\.?\s*sorular|(\d{1,3})\s*(?:,\s*\d{1,3}\s*)*(?:ve|ile)\s*(\d{1,3})\s*\.\s*sorular", re.I)
DIR_EN = re.compile(r"questions?\s+(\d{1,3})\s*(?:(?:-|–|—|to|and|,)\s*\d{1,3}\s*)*(?:-|–|—|to|and|,)\s*(\d{1,3})", re.I)

def story_text(d, sid):
    st = d["stories"].get(sid)
    return "\r".join(p[0] for p in st["paras"]) if st else ""

def is_q(d, sid):
    t = story_text(d, sid); m = QRE.match(t)
    if not m or re.match(r"\s*Bu\s+(testte|denemede)", t[:60], re.I): return None
    if len(re.sub(r"[\s ​﻿￼\u009e»«¶]+", "", t[m.end():])) < 8: return None
    if re.match(r"^\s*\d+\s*\.?\s*(ve|,|-|–|ile)\s*\d+.{0,12}soru", t, re.I): return None
    return int(m.group(1))

def walk(it):
    yield it
    for k in it.get("kids", []): yield from walk(k)

def questions(d):
    """[(sayfa, y1, x1, x2, sid, num)] okuma sırasıyla: sayfa, sütun, y"""
    W = d["pageW"]; out = []
    for sp in d["spreads"]:
        for it in sp["items"]:
            if it.get("pageIdx") is None: continue
            for k in walk(it):
                if k["kind"] == "TextFrame" and k.get("story") and k["id"] not in d["anchoredOwner"]:
                    n = is_q(d, k["story"])
                    if n is not None and k.get("gb"):
                        g = k["gb"]; col = 1 if ((g[3] - g[1]) < W * 0.55 and (g[1] + g[3]) / 2 > W / 2) else 0
                        out.append((it["pageIdx"], col, g[0], k["story"], n, k))
    out.sort(key=lambda q: (q[0], q[1], q[2]))
    return out

def tests_of(d):
    qs = questions(d); t = -1; br = {}; cnt = {}
    for q in qs:
        if q[4] == 1 or t < 0: t += 1
        br[q[3]] = t; cnt[t] = cnt.get(t, 0) + 1
    return qs, br, cnt

def groups_of(d, qs):
    """A'daki ortak metin grupları: yönerge metni + aynı sayfadaki aralıktaki soruların hikâye id'leri"""
    gs = []
    for sp in d["spreads"]:
        for it in sp["items"]:
            if it.get("pageIdx") is None: continue
            for k in walk(it):
                if k["kind"] != "TextFrame" or not k.get("story") or is_q(d, k["story"]) is not None: continue
                t = story_text(d, k["story"]); lo = hi = None
                m = DIR_TR.search(t)
                if m and re.search(r"g[öo]re", t, re.I): lo, hi = int(m.group(1) or m.group(3)), int(m.group(2) or m.group(4))
                else:
                    e = DIR_EN.search(t)
                    if e and re.search(r"according\s+to|based\s+on|answer|read", t, re.I): lo, hi = int(e.group(1)), int(e.group(2))
                if lo is None: continue
                pg = it["pageIdx"]
                sids = [q[3] for q in qs if q[0] == pg and lo <= q[4] <= hi]
                if len(sids) >= 2: gs.append({"pg": pg, "sids": sids})
    return gs

def strip_directives(d):
    n = 0
    for st in d["stories"].values():
        for p in st["paras"]:
            t = p[0]
            if len(t) < 200 and ((DIR_TR.search(t) and re.search(r"g[öo]re", t, re.I)) or (DIR_EN.search(t) and re.search(r"according|based|answer", t, re.I))):
                p[0] = "Aşağıdaki metni dikkatlice okuyunuz." if re.search(r"soru", t, re.I) else "Read the text carefully."; n += 1
    return n

def shrink(d, seed):
    rnd = random.Random(seed); n = 0
    for q in questions(d):
        k = q[5]
        if k.get("kids") or rnd.random() > 0.4: continue
        g = k["gb"]; h = g[2] - g[0]
        if h < 60: continue
        r = rnd.uniform(0.0, 0.3); k["gb"][2] = g[0] + h * (1 - r); n += 1
    return n

def continuous(d):
    qs, br, cnt = tests_of(d)
    if any(re.search(r"\(\d{1,3}\s*[-–]\s*\d{1,3}\)", story_text(d, s)) for s in d["stories"]): return None   # ders aralıklı (lise)
    off = {}; acc = 0
    for t in sorted(cnt): off[t] = acc; acc += cnt[t]
    pg_test = {}
    for q in qs: pg_test.setdefault(q[0], br[q[3]])
    # soru numaraları
    for q in qs:
        p0 = d["stories"][q[3]]["paras"][0]
        p0[0] = QRE.sub(lambda m: m.group(0).replace(m.group(1), str(int(m.group(1)) + off[br[q[3]]]), 1), p0[0], count=1)
    # yönergeler: sayfanın testine göre kaydır
    story_pg = {}
    for sp in d["spreads"]:
        for it in sp["items"]:
            if it.get("pageIdx") is None: continue
            for k in walk(it):
                if k.get("story"): story_pg[k["story"]] = it["pageIdx"]
    for sid, st in d["stories"].items():
        if sid in br or sid not in story_pg: continue
        pg = story_pg[sid]; t0 = pg_test.get(pg, pg_test.get(pg + 1))
        if t0 is None or off[t0] == 0: continue
        for p in st["paras"]:
            t = p[0]
            if len(t) < 200 and re.search(r"soru|question", t, re.I) and not re.search(r"Bu\s+testte", t, re.I) and re.search(r"\d", t):
                p[0] = re.sub(r"(?<![\d\w])(\d{1,3})(?![\d])", lambda m: str(int(m.group(1)) + off[t0]), t)
    # cevap anahtarı: sıralı
    best = None; bc = 0
    for sid, st in d["stories"].items():
        c = len(re.findall(r"\d{1,3}-[A-E]", "\r".join(p[0] for p in st["paras"])))
        if c > bc: bc, best = c, sid
    if best and bc >= 20:
        # anahtarda testler "1-" ile başlar; her numaraya o testin kaydırması eklenir (sıra korunur)
        t = [-1]
        def rn(m):
            n = int(m.group(1))
            if n == 1: t[0] += 1
            return "%d-%s" % (n + off.get(t[0], 0), m.group(2))
        for p in d["stories"][best]["paras"]: p[0] = re.sub(r"(\d{1,3})-([A-E])", rn, p[0])
    return off

out, srcs = sys.argv[1], sys.argv[2:]
for src in srcs:
    base = os.path.basename(src)[:-5]
    d0 = json.load(open(src, encoding="utf-8"))
    qs, br, cnt = tests_of(d0)
    meta = {"branchOf": br, "origGroups": groups_of(d0, qs)}
    variants = []
    for seed in (1, 2, 3):
        d = copy.deepcopy(d0); n = shrink(d, seed); variants.append(("boy%d" % seed, d, "%d soru kısaldı" % n))
    d = copy.deepcopy(d0); n = strip_directives(d); variants.append(("yonergesiz", d, "%d yönerge silindi" % n))
    d = copy.deepcopy(d0)
    if continuous(d) is not None:
        variants.append(("surekli", d, "kesintisiz numara"))
        d2 = copy.deepcopy(d); shrink(d2, 7); variants.append(("surekli_boy7", d2, "kesintisiz + kısalmış"))
        d3 = copy.deepcopy(d); strip_directives(d3); variants.append(("surekli_yonergesiz", d3, "kesintisiz + yönergesiz"))
    for name, d, note in variants:
        d.update(meta); d["name"] = base + "__" + name
        json.dump(d, open(os.path.join(out, base + "__" + name + ".json"), "w", encoding="utf-8"), ensure_ascii=False)
        print(base + "__" + name, "—", note)
