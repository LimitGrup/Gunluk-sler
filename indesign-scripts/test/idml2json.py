#!/usr/bin/env python3
"""IDML -> JSON belge modeli (Kitapçık B test düzeneği için).
Kullanım: python3 -I idml2json.py <açılmış_idml_klasörü> <çıktı.json>
Koordinatlar: sayfa orijinli punto, [üst, sol, alt, sağ] (InDesign geometricBounds)."""
import sys, os, json, re, urllib.parse
import xml.etree.ElementTree as ET

D, OUT = sys.argv[1], sys.argv[2]
ITEM_TAGS = {"TextFrame", "Group", "Rectangle", "Polygon", "Oval", "GraphicLine"}

def mat(s):
    a = [float(x) for x in s.split()] if s else [1, 0, 0, 1, 0, 0]
    return a
def mul(m1, m2):  # m1 ∘ m2 (önce m2, sonra m1)
    a1, b1, c1, d1, e1, f1 = m1; a2, b2, c2, d2, e2, f2 = m2
    return [a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1]
def app(m, x, y):
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f

def path_bounds(el, m):
    pts = []
    for pp in el.iter("PathPointType"):
        x, y = [float(v) for v in pp.get("Anchor").split()]
        pts.append(app(m, x, y))
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return [min(ys), min(xs), max(ys), max(xs)]   # yayılım koordinatı

def style_name(ref):
    if not ref:
        return ""
    n = ref.split("/", 1)[-1]
    n = urllib.parse.unquote(n)
    return n.split(":")[-1]

# ---- belge düzeyi ----
dm = ET.parse(os.path.join(D, "designmap.xml")).getroot()
prefs = ET.parse(os.path.join(D, "Resources", "Preferences.xml")).getroot()
dp = prefs.find(".//DocumentPreference")
facing = dp.get("FacingPages") == "true"
layers = {}
for ly in dm.iter("Layer"):
    layers[ly.get("Self")] = {"name": ly.get("Name"), "locked": ly.get("Locked") == "true", "visible": ly.get("Visible") == "true"}
sections = [{"marker": s.get("Marker", ""), "pageStart": s.get("PageStart")} for s in dm.iter("Section")]

# ---- metinler ----
stories = {}
anchored_owner = {}   # çapalı öğe id -> story id
def walk_story(node, out, anchors, sid):
    # node altındaki metni sırayla topla
    for ch in list(node):
        tag = ch.tag
        if tag == "Content":
            out.append(ch.text or "")
        elif tag == "Br":
            out.append("\r")
        elif tag in ITEM_TAGS:
            out.append("￼")
            anchors.append(ch)
        elif tag == "Table":
            out.append("\u0016")
            # tablo hücre metinleri ayrı hikâye değil; içeriği arama dışı tut
        elif tag in ("Properties", "Footnote", "Note"):
            pass
        else:
            walk_story(ch, out, anchors, sid)
        if ch.tail and tag not in ("Properties",):
            pass
    return out

def story_paras(st_el, sid):
    paras = []      # [metin, stil]
    anchors = []
    for psr in st_el.iter("ParagraphStyleRange"):
        sty = style_name(psr.get("AppliedParagraphStyle"))
        buf = []
        # işleme talimatlarını (ACE) ElementTree görmez; Content metinlerine güveniyoruz
        walk_story(psr, buf, anchors, sid)
        text = "".join(buf)
        parts = text.split("\r")
        for i, p in enumerate(parts):
            if i == len(parts) - 1 and p == "" and len(parts) > 1:
                continue
            paras.append([p, sty])
    # ardışık ParagraphStyleRange'ler aynı paragrafı bölebilir: Br yoksa birleştir
    return paras, anchors

def story_paras_exact(st_el):
    """Paragraf sınırlarını yalnız Br'den al; stil = paragrafın ilk karakterinin stili."""
    seq = []   # (metin, stil) parçaları
    anchors = []
    for psr in st_el.iter("ParagraphStyleRange"):
        sty = style_name(psr.get("AppliedParagraphStyle"))
        buf = []
        walk_story(psr, buf, anchors, None)
        seq.append(("".join(buf), sty))
    paras = []; cur = ""; cur_sty = None
    for txt, sty in seq:
        segs = txt.split("\r")
        for i, sg in enumerate(segs):
            # parçanın sonundaki Br'den sonra kalan boş kuyruk yeni paragrafın stilini belirlemez
            if cur_sty is None and not (sg == "" and i == len(segs) - 1):
                cur_sty = sty
            cur += sg
            if i < len(segs) - 1:
                paras.append([cur, cur_sty]); cur = ""; cur_sty = None
    if cur != "" or not paras:
        paras.append([cur, cur_sty or ""])
    return paras, anchors

for fn in os.listdir(os.path.join(D, "Stories")):
    root = ET.parse(os.path.join(D, "Stories", fn)).getroot()
    st = root.find("Story")
    sid = st.get("Self")
    paras, anchors = story_paras_exact(st)
    stories[sid] = {"paras": paras, "anchored": [a.get("Self") for a in anchors],
                    "anchoredKinds": [a.tag for a in anchors]}
    for a in anchors:
        anchored_owner[a.get("Self")] = sid
        # çapalı öğenin içindeki öğeler (grup içi vb.)
        for sub in a.iter():
            if sub.tag in ITEM_TAGS and sub is not a:
                anchored_owner[sub.get("Self")] = sid

# ---- yayılımlar ----
spread_files = [s.get("src") for s in dm.iter("{http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging}Spread")]
pages = []
spreads = []

def has_graphic(el):
    for t in ("Image", "PDF", "EPS", "ImportedPage", "WMF", "PICT"):
        if el.find(".//" + t) is not None:
            return True
    return False

def build_item(el, parent_m, inherited_layer, inherited_locked):
    m = mul(parent_m, mat(el.get("ItemTransform")))
    tag = el.tag
    layer = el.get("ItemLayer") or inherited_layer
    locked = (el.get("Locked") == "true") or inherited_locked
    it = {"id": el.get("Self"), "kind": tag, "layer": layer,
          "locked": locked or (layers.get(layer, {}).get("locked", False)),
          "visible": el.get("Visible") != "false"}
    if tag == "Group":
        kids = []
        for ch in list(el):
            if ch.tag in ITEM_TAGS:
                kids.append(build_item(ch, m, layer, locked))
        it["kids"] = kids
        bs = [k["sb"] for k in kids if k.get("sb")]
        it["sb"] = [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)] if bs else None
    else:
        it["sb"] = path_bounds(el, m)
        if tag == "TextFrame":
            it["story"] = el.get("ParentStory")
            it["prev"] = el.get("PreviousTextFrame")
            it["next"] = el.get("NextTextFrame")
        else:
            it["graphic"] = has_graphic(el)
            # grafik çerçevesi içinde metin çerçevesi olmaz; içerik dışı alt öğeleri yok say
    return it

for sf in spread_files:
    root = ET.parse(os.path.join(D, sf)).getroot()
    sp = root.find("Spread")
    sm = mat(sp.get("ItemTransform"))
    sp_pages = []
    for pg in sp.findall("Page"):
        gb = [float(v) for v in pg.get("GeometricBounds").split()]
        pm = mat(pg.get("ItemTransform"))
        x1, y1 = app(pm, gb[1], gb[0]); x2, y2 = app(pm, gb[3], gb[2])
        mp = pg.find("MarginPreference")
        p = {"name": pg.get("Name"), "self": pg.get("Self"), "sb": [min(y1, y2), min(x1, x2), max(y1, y2), max(x1, x2)],
             "margin": {k: float(mp.get(k)) for k in ("Top", "Bottom", "Left", "Right")} if mp is not None else None,
             "master": pg.get("AppliedMaster"), "spread": len(spreads)}
        sp_pages.append(p)
    items = []
    for ch in list(sp):
        if ch.tag in ITEM_TAGS:
            items.append(build_item(ch, [1, 0, 0, 1, 0, 0], None, False))
    # öğeyi en çok örtüştüğü sayfaya ata
    def ov(a, b):
        w = min(a[3], b[3]) - max(a[1], b[1]); h = min(a[2], b[2]) - max(a[0], b[0])
        return w * h if (w > 0 and h > 0) else 0
    for it in items:
        best, bo = None, 0
        if it.get("sb"):
            sb = list(it["sb"])
            if sb[2] - sb[0] < 1: sb[0] -= 0.5; sb[2] += 0.5
            if sb[3] - sb[1] < 1: sb[1] -= 0.5; sb[3] += 0.5
            for pi, p in enumerate(sp_pages):
                o = ov(sb, p["sb"])
                if o > bo: bo, best = o, pi
        it["pageIdx"] = None if best is None else len(pages) + best
    for p in sp_pages:
        pages.append(p)
    spreads.append({"pages": [len(pages) - len(sp_pages) + i for i in range(len(sp_pages))], "items": items})

# sayfa orijinli koordinat: öğe hangi sayfadaysa o sayfanın sol üstüne göre
def to_page(sb, p):
    return [sb[0] - p["sb"][0], sb[1] - p["sb"][1], sb[2] - p["sb"][0], sb[3] - p["sb"][1]]
def localize(it, p):
    if it.get("sb") and p is not None:
        it["gb"] = to_page(it["sb"], p)
    for k in it.get("kids", []):
        localize(k, p)
for sp in spreads:
    for it in sp["items"]:
        p = pages[it["pageIdx"]] if it["pageIdx"] is not None else pages[sp["pages"][0]]
        localize(it, p)

# master yayılımlardaki metin çerçeveleri (üst bant için)
masters = []
for fn in os.listdir(os.path.join(D, "MasterSpreads")):
    root = ET.parse(os.path.join(D, "MasterSpreads", fn)).getroot()
    for tf in root.iter("TextFrame"):
        masters.append({"id": tf.get("Self"), "story": tf.get("ParentStory")})

doc = {"name": os.path.basename(D.rstrip("/")), "facing": facing,
       "pageW": float(dp.get("PageWidth")), "pageH": float(dp.get("PageHeight")),
       "layers": layers, "sections": sections, "pages": pages, "spreads": spreads,
       "stories": stories, "anchoredOwner": anchored_owner, "masters": masters}
json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
print("%s: %d sayfa, %d yayılım, %d hikâye, %d öğe" % (doc["name"], len(pages), len(spreads), len(stories),
      sum(len(s["items"]) for s in spreads)))
