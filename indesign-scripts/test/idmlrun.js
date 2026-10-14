// Gerçek A belgesinin IDML modelinde Kitapçık B scriptini çalıştırır ve sonucu scriptten BAĞIMSIZ
// denetimlerle doğrular (çakışma, taşma, çizgi, hiza, test sınırı, numara, ortak metin, cevap anahtarı, A→B).
// Kullanım: python3 -I indesign-scripts/test/idml2json.py <açılmış_idml_klasörü> belge.json
//           node indesign-scripts/test/idmlrun.js indesign-scripts/kitapcik-b-olusturucu.jsx belge.json [--layout] [--page 4,5]
//           Ortam: MODE=cross|col|rnd  SEED=n  OPT_OFF=Boşluk,Sayfalar,Tam  CSVOUT=rapor.csv (script CSV çıktısı)
var fs = require("fs"), vm = require("vm");
var scriptPath = process.argv[2], jsonPath = process.argv[3], QUIET = process.argv.indexOf("--quiet") > 0;
var M = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
var W = M.pageW, H = M.pageH;
var grepPrefs = { findWhat: "" };
var ALLTOP = [];         // üst düzey öğeler
var BYID = {};

// ---------- hikâyeler ----------
var STORIES = {};
function mkStory(sid) {
    var src = M.stories[sid] || { paras: [["", ""]], anchored: [] };
    var paras = src.paras.map(function (p) { return { _t: p[0], appliedParagraphStyle: { name: p[1] || "" } }; });
    var st = { id: sid, _p: paras, textContainers: [], _anch: [] };
    Object.defineProperty(st, "pageItems", { get: function () { return idColl(st._anch); } });
    paras.forEach(function (p) {
        Object.defineProperty(p, "contents", { get: function () { return p._t; }, set: function (v) { p._t = v; } });
        p.findGrep = function () {
            // NUMFAIL=grep|all: InDesign'da paragraf aramasının boş döndüğü durumu taklit eder (numara yazma yedek yolları için)
            if (process.env.NUMFAIL && /\(\?=\\\.\)/.test(grepPrefs.findWhat)) { return []; }
            var re = new RegExp(grepPrefs.findWhat), m = re.exec(p._t);
            if (!m) { return []; }
            var idx = m.index, len = m[0].length;
            return [{ get contents() { return p._t.substr(idx, len); }, set contents(v) { p._t = p._t.substr(0, idx) + v + p._t.substr(idx + len); } }];
        };
    });
    st.paragraphs = paras;
    function whole() { return paras.map(function (p) { return p._t; }).join("\r"); }
    // InDesign Story.characters.itemByRange(a, b): a..b (b dahil) aralığındaki metin
    st.characters = { itemByRange: function (a, b) {
        return { get contents() { return whole().substring(a, b + 1); },
                 set contents(v) {
                     if (process.env.NUMFAIL === "all") { throw new Error("metin kilitli (taklit)"); }
                     var t = whole(); t = t.substr(0, a) + v + t.substr(b + 1);
                     var parts = t.split("\r"); for (var i = 0; i < paras.length; i++) { paras[i]._t = (i < parts.length) ? parts[i] : ""; }
                 } };
    } };
    Object.defineProperty(st, "texts", { get: function () {
        return [{ get contents() { return whole(); },
                  set contents(v) { var parts = String(v).split("\r"); for (var i = 0; i < paras.length; i++) { paras[i]._t = (i < parts.length) ? parts[i] : ""; } } }];
    } });
    st.findGrep = function () {
        var res = [], re = new RegExp(grepPrefs.findWhat, "g"), txt = whole(), m;
        while ((m = re.exec(txt)) !== null) {
            (function (idx, len) {
                res.push({ index: idx, insertionPoints: [{ index: idx }], get contents() { return whole().substr(idx, len); },
                           set contents(v) { var t = whole(); t = t.substr(0, idx) + v + t.substr(idx + len);
                                             var parts = t.split("\r"); for (var i = 0; i < paras.length; i++) { paras[i]._t = parts[i]; } } });
            })(m.index, m[0].length);
        }
        return res;
    };
    return st;
}
function story(sid) { if (!STORIES[sid]) { STORIES[sid] = mkStory(sid); } return STORIES[sid]; }

// ---------- öğeler ----------
var LOCKERR = 0;
function mkItem(src, pg, spread, parent) {
    var it = { constructor: { name: src.kind }, id: src.id, pg: pg, spread: spread, _src: src, _locked: !!src.locked,
               _gb: src.gb ? src.gb.slice(0) : [0, 0, 0, 0], _parentItem: parent || null, _kids: [] };
    BYID[src.id] = it;
    it.parent = (src.kind && M.anchoredOwner[src.id]) ? { constructor: { name: "Character" } } : (parent || pg || spread);
    function translate(dy, dx) {
        it._gb = [it._gb[0] + dy, it._gb[1] + dx, it._gb[2] + dy, it._gb[3] + dx];
        it._kids.forEach(function (k) { k._tr(dy, dx); });
    }
    it._tr = translate;
    function checkLock() { if (it._locked) { LOCKERR++; throw new Error("Nesne kilitli: " + it.id); } }
    Object.defineProperty(it, "geometricBounds", {
        get: function () {
            if (it._kids.length) {
                var bs = it._kids.map(function (k) { return k.geometricBounds; });
                return [Math.min.apply(null, bs.map(function (b) { return b[0]; })), Math.min.apply(null, bs.map(function (b) { return b[1]; })),
                        Math.max.apply(null, bs.map(function (b) { return b[2]; })), Math.max.apply(null, bs.map(function (b) { return b[3]; }))];
            }
            return it._gb.slice(0);
        },
        set: function (v) {
            checkLock();
            var cur = it.geometricBounds;
            var dy = v[0] - cur[0], dx = v[1] - cur[1];
            if (it._kids.length) { translate(dy, dx); }
            else { it._gb = [v[0], v[1], v[2], v[3]]; }
        }
    });
    it.move = function (to, by) {
        checkLock();
        if (to && to._isPage) { setPage(it, to); return; }
        if (by) { translate(by[1], by[0]); }
    };
    if (src.kind === "TextFrame") {
        it.parentStory = story(src.story);
        it.parentStory.textContainers.push(it);
    }
    if (src.kind === "Group") {
        it._kids = (src.kids || []).map(function (k) { return mkItem(k, pg, spread, it); });
    }
    if (src.graphic) { it.allGraphics = [{}]; } else { it.allGraphics = []; }
    Object.defineProperty(it, "allPageItems", { get: function () { var out = []; (function rec(x) { x._kids.forEach(function (k) { out.push(k); rec(k); }); })(it); return out; } });
    Object.defineProperty(it, "pageItems", { get: function () { return idColl(it._kids); } });
    return it;
}
// InDesign'da pageItems koleksiyonu öğeleri GENEL "PageItem" türünde döndürür; gerçek tür (TextFrame,
// Group, Rectangle...) yalnız everyItem().getElements() ya da öğenin getElements() ile alınır.
function idColl(list) {
    var arr = list.map(function (k) {
        var g = { constructor: { name: "PageItem" }, id: k.id, getElements: function () { return [k]; },
                  move: function (a, b) { return k.move(a, b); } };
        Object.defineProperty(g, "geometricBounds", { get: function () { return k.geometricBounds; }, set: function (v) { k.geometricBounds = v; } });
        Object.defineProperty(g, "parent", { get: function () { return k.parent; } });
        Object.defineProperty(g, "allPageItems", { get: function () { return k.allPageItems || []; } });
        return g;
    });
    arr.everyItem = function () { return { getElements: function () { return list.slice(0); },
                                           get geometricBounds() { return list.length === 1 ? list[0].geometricBounds : list.map(function (k) { return k.geometricBounds; }); } }; };
    return arr;
}
function setPage(it, pg) { it.pg = pg; it._kids.forEach(function (k) { setPage(k, pg); }); }

// ---------- sayfalar ----------
var pages = [], spreads = [];
M.pages.forEach(function (p, i) {
    var pg = { _isPage: true, name: p.name, id: "PG" + i, idx: i, bounds: [0, 0, H, W],
               marginPreferences: { bottom: p.margin ? p.margin.Bottom : 0, top: p.margin ? p.margin.Top : 0,
                                    left: p.margin ? p.margin.Left : 0, right: p.margin ? p.margin.Right : 0 } };
    // ORDER=rev: InDesign'ın koleksiyon sırası (z-sırası) IDML sırasından farklı olabilir; sonuç sıradan bağımsız olmalı
    function top(kind) { var r = ALLTOP.filter(function (x) { return x.pg === pg && x.constructor.name === kind; }); return process.env.ORDER === "rev" ? r.reverse() : r; }
    ["TextFrame", "Group", "Rectangle", "Polygon", "Oval", "GraphicLine"].forEach(function (k) {
        var prop = { TextFrame: "textFrames", Group: "groups", Rectangle: "rectangles", Polygon: "polygons", Oval: "ovals", GraphicLine: "graphicLines" }[k];
        Object.defineProperty(pg, prop, { get: function () { return top(k); } });
    });
    Object.defineProperty(pg, "allPageItems", { get: function () {
        var out = [];
        ALLTOP.forEach(function (x) { if (x.pg === pg) { out.push(x); out = out.concat(x.allPageItems); } });
        // çapalı nesneler (metin çerçevelerinin hikâyelerinden)
        out.slice(0).forEach(function (x) { if (x.parentStory) { x.parentStory.pageItems.forEach(function (a) { out.push(a); }); } });
        return out;
    } });
    pages.push(pg);
});
M.spreads.forEach(function (s, si) {
    var sp = { idx: si };
    Object.defineProperty(sp, "pageItems", { get: function () { return idColl(ALLTOP.filter(function (x) { return x.spread === sp; })); } });
    spreads.push(sp);
    s.items.forEach(function (src) {
        var pg = (src.pageIdx === null) ? null : pages[src.pageIdx];
        var it = mkItem(src, pg, sp, null);
        ALLTOP.push(it);
    });
    s.pages.forEach(function (pi, k) {
        pages[pi].parent = sp;
        // InDesign (PAGE_ORIGIN, karşılıklı sayfa): öğelerin geometricBounds'u sayfa koordinatında
        // gelir ama Page.bounds yayılımın sol kenarına göre bildirilir; yayılımın 2. (sağ) sayfası
        // [0, W, H, 2W] döner. v4.25'e kadar betik bu yüzden sağ sayfaları tek sütun sanıyordu.
        // PAGE_BOUNDS=page: eski (ideal) davranış.
        if (process.env.PAGE_BOUNDS !== "page" && k > 0) { pages[pi].bounds = [0, k * W, H, (k + 1) * W]; }
    });
});
// çapalı nesneler: hikâyenin pageItems'ı; konumu taşıyıcı çerçevenin içinde varsayılır
Object.keys(STORIES).forEach(function (sid) {
    var st = STORIES[sid], src = M.stories[sid];
    (src && src.anchored || []).forEach(function (aid, k) {
        var a = { id: aid, constructor: { name: src.anchoredKinds[k] }, allPageItems: [], parent: { constructor: { name: "Character" } } };
        // ANCHOR_SHIFT=1: InDesign'ın karşılıklı sayfada sağ sayfadaki çapalı nesneyi sol sayfa
        // orijinine göre (x + sayfa genişliği) bildirmesini taklit eder.
        Object.defineProperty(a, "geometricBounds", { get: function () {
            var c = st.textContainers[0]; if (!c) { return [0, 0, 0, 0]; }
            // ANCHOR_BOUNDS='{"u6370":[30,330,315,530]}': belirli çapalı nesnenin InDesign'ın
            // bildirdiği konumu (sayfa koordinatı) — gerçek InDesign davranışını yeniden üretmek için
            if (process.env.ANCHOR_BOUNDS) { var ab = JSON.parse(process.env.ANCHOR_BOUNDS); if (ab[aid]) { return ab[aid].slice(0); } }
            var g = c.geometricBounds;
            if (process.env.ANCHOR_SHIFT && c.pg && M.pages[c.pg.idx].sb[1] > -1 && M.facing) { return [g[0], g[1] + W, g[2], g[3] + W]; }
            return g;
        } });
        st._anch.push(a);
    });
});

// ---------- belge ----------
var masterItems = M.masters.map(function (m) { var t = { constructor: { name: "TextFrame" }, id: m.id, parentStory: story(m.story) }; return t; });
var docFile = M.name + ".indd";
var doc = {
    modified: false, saved: true, pages: pages, sections: M.sections.map(function (s) { return { marker: s.marker }; }),
    masterSpreads: [{ allPageItems: masterItems }],
    fullName: { name: encodeURI(docFile), fsName: "/tmp/" + docFile, parent: { fsName: "/tmp" } },
    viewPreferences: {}, documentPreferences: { facingPages: M.facing }, save: function () {}
};
// InDesign Page.appliedSection: sayfanın bölümü (bölüm işareti = üst banttaki branş adı olabilir)
(function () {
    var starts = M.sections.map(function (s, si) {
        var ix = -1; M.pages.forEach(function (p, pi) { if (p.self === s.pageStart) { ix = pi; } });
        return { ix: ix, obj: doc.sections[si] };
    }).filter(function (x) { return x.ix >= 0; }).sort(function (a, b) { return a.ix - b.ix; });
    pages.forEach(function (pg, pi) {
        var cur = null; starts.forEach(function (st) { if (st.ix <= pi) { cur = st.obj; } });
        if (cur) { pg.appliedSection = cur; }
    });
})();
Object.defineProperty(doc, "stories", { get: function () { return Object.keys(STORIES).map(function (k) { return STORIES[k]; }); } });
Object.keys(M.stories).forEach(function (sid) { story(sid); });

// ---------- A anlık görüntüsü (denetim için) ----------
var QRE = /^[\s​﻿￼\u009E]*(\d{1,3})\.(?=[\s\t])/;
var aNum = {};   // hikâye id -> A numarası
Object.keys(STORIES).forEach(function (sid) {
    var all = STORIES[sid]._p.map(function (p) { return p._t; }).join("\r");
    var m = QRE.exec(all);
    if (!m || /Bu\s+(testte|denemede)/i.test(all.substr(0, 60)) || /^\s*\d+\s*\.?\s*(ve|,|-|–|ile)\s*\d+.{0,12}soru/i.test(all)) { return; }
    if (all.substr(m[0].length).replace(/[\s ​﻿￼\u009e»«¶]+/g, "").length < 8) { return; }
    aNum[sid] = +m[1];
});
// birden çok soru içeren grup: üyeleri ayrı öğe sayılır (her soru kendi konumuyla denetlenir)
function nQ(x) { return x.allPageItems.filter(function (k) { return k.parentStory && aNum[k.parentStory.id] !== undefined && !M.anchoredOwner[k.id]; }).length; }
// ortak metin yönergesi taşıyan (soru olmayan) çerçeve: "17 ve 18. soruları ... göre"
function hasDir(x) { return x.allPageItems.some(function (k) { return k.parentStory && aNum[k.parentStory.id] === undefined && !M.anchoredOwner[k.id] &&
    /\d{1,3}\s*\.?\s*(ve|,|-|–|ile)\s*\d{1,3}\s*\.?\s*sorular/i.test(k.parentStory._p.map(function (p) { return p._t; }).join(" ")); }); }
function snapshot() {
    var out = [];
    function add(x) {
        if (x.constructor.name === "Group" && (nQ(x) > 1 || (nQ(x) === 1 && hasDir(x)))) { x._kids.forEach(add); return; }
        out.push({ it: x, pg: x.pg.idx, gb: x.geometricBounds, kind: x.constructor.name });
    }
    ALLTOP.forEach(function (x) { if (x.pg) { add(x); } });
    return out;
}
var A = snapshot();

// A cevap anahtarı (en çok "N-X" içeren hikâye)
function keyTokens() {
    var best = null, bc = 0;
    Object.keys(STORIES).forEach(function (sid) {
        var t = STORIES[sid]._p.map(function (p) { return p._t; }).join("\r");
        var c = (t.match(/\d{1,3}-[A-E]/g) || []).length;
        if (c > bc) { bc = c; best = sid; }
    });
    if (!best || bc < 20) { return null; }
    var t2 = STORIES[best]._p.map(function (p) { return p._t; }).join("\r"), re = /(\d{1,3})-([A-E])/g, m, out = [], sec = -1;
    while ((m = re.exec(t2)) !== null) { if (+m[1] === 1) { sec++; } out.push({ sec: sec, num: +m[1], L: m[2] }); }
    return out;
}
var KEY_A = keyTokens();
// A'daki ortak metin grupları (bağımsız: yalnız sayfada duran, soru olmayan çerçevelerdeki yönergeler)
var DIR_RE = /(\d{1,3})\s*[-–]\s*(\d{1,3})\.?\s*sorular|(\d{1,3})\s*(?:,\s*\d{1,3}\s*)*(?:ve|ile)\s*(\d{1,3})\s*\.\s*sorular/i;
var DIR_EN_RE = /questions?\s+[(\[]?\s*(\d{1,3})\s*(?:(?:-|–|—|to|and|,)\s*\d{1,3}\s*)*(?:-|–|—|to|and|,)\s*(\d{1,3})/i;
var GROUPS_A = [];
// yönerge metninden aralık (yönerge değilse null)
function dirRange(t) {
    if (QRE.test(t) && !/^\s*\d+\s*\.?\s*(ve|,|-|–)/.test(t)) { return null; }
    var m = DIR_RE.exec(t);
    if (m && /g[öo]re/i.test(t)) { return { lo: +(m[1] || m[3]), hi: +(m[2] || m[4]) }; }
    // İngilizce: "Answer the questions 8-10 according to ...", "questions (2-3) ...", "Questions 4 to 6 are based on"
    var e = DIR_EN_RE.exec(t);
    if (!e || !/according\s+to|based\s+on|answer|read/i.test(t)) { return null; }
    return { lo: +e[1], hi: +e[2] };
}
ALLTOP.forEach(function (x) {
    if (!x.pg) { return; }
    var tfs = x.parentStory ? [x] : x.allPageItems.filter(function (k) { return k.parentStory; });
    tfs.forEach(function (tf) {
        var t = tf.parentStory._p.map(function (p) { return p._t; }).join(" ");
        var r = dirRange(t);
        if (r) { GROUPS_A.push({ pg: x.pg.idx, lo: r.lo, hi: r.hi, tf: tf, top: x, y1: tf.geometricBounds[0] }); }
    });
});

// ---------- çalıştır ----------
var alerts = [];
var CTLS = [];
function ctl(txt) { var c = { text: txt || "", value: false, characters: 0, preferredSize: {}, graphics: { newPen: function () {}, PenType: { SOLID_COLOR: 0 } },
                          add: function (type, bnd, t2) { var k = ctl(t2); k._type = type; k._label = t2 || ""; CTLS.push(k); return k; } }; return c; }
function applyUi() {
    var mode = process.env.MODE || "cross";
    CTLS.forEach(function (c) {
        if (c._type === "radiobutton") {
            c.value = (mode === "cross" && /Çapraz/.test(c._label)) || (mode === "col" && /Sütun içi/.test(c._label)) || (mode === "rnd" && /Rastgele/.test(c._label));
        }
        if (c._type === "edittext" && /^\d+$/.test(c.text) && process.env.SEED) { c.text = process.env.SEED; }
        // POOLS="sayfa 18 ve 19 soru 16-25; ...": özel havuz kutusu (çok satırlı metin alanı)
        if (c._type === "edittext" && c.text === "" && process.env.POOLS) { c.text = process.env.POOLS; }
        if (c._type === "checkbox" && process.env.OPT_OFF && process.env.OPT_OFF.split(",").some(function (o) { return c._label.indexOf(o) === 0; })) { c.value = false; }
    });
}
var ctx = {
    app: { documents: { length: 1 }, activeDocument: doc, scriptPreferences: { enableRedraw: true },
           get findGrepPreferences() { return grepPrefs; }, set findGrepPreferences(v) { if (v === "NOTHING") { grepPrefs.findWhat = ""; } },
           changeGrepPreferences: {}, open: function () { return doc; }, doScript: function () { return ""; } },
    $: { os: "Macintosh OS 14", writeln: function (s) { console.log(s); } },
    Window: function () { var w = ctl(); w.show = function () { applyUi(); return 1; }; return w; },
    File: function (p) { var buf = [];   // CSVOUT=dosya: script'in yazdığı CSV'yi diske al
                         return { fsName: p, name: encodeURI(String(p).split("/").pop()), exists: false, open: function () { return true; },
                                  write: function (t) { buf.push(String(t)); }, writeln: function (t) { buf.push(String(t) + "\n"); },
                                  close: function () { if (process.env.CSVOUT && /\.csv$/.test(String(p))) { fs.writeFileSync(process.env.CSVOUT, buf.join("")); } } }; },
    Folder: function () {}, ScriptLanguage: {}, MeasurementUnits: { POINTS: 0 }, RulerOrigin: { PAGE_ORIGIN: 0 },
    NothingEnum: { NOTHING: "NOTHING" }, alert: function (m) { alerts.push(m); }, confirm: function () { return true; },
    decodeURI: decodeURI, encodeURI: encodeURI
};
// "aktif belgeyi kullan" kutusu işaretli olmalı: ilk checkbox
var src = fs.readFileSync(scriptPath, "utf8").replace(/^#target.*$/m, "");
// ExtendScript (ES3) metin içindeki U+2028/U+2029'u satır sonu sayar: script InDesign'da hiç açılmaz
// (Node bunu kabul ettiği için model fark etmezdi). Böyle bir karakter varsa test hemen durur.
(function () {
    var mLT = /[\u2028\u2029]/.exec(src);
    if (mLT) {
        console.log("HATA: script'te görünmez satır ayırıcı (U+" + src.charCodeAt(mLT.index).toString(16).toUpperCase() + ") var, satır " +
                    src.substr(0, mLT.index).split("\n").length + " — ExtendScript'te sözdizimi hatası olur; \\u2029 kaçışıyla yazın.");
        process.exit(1);
    }
})();
vm.createContext(ctx);
// ExtendScript'in Array.sort'u kararlı değildir: eşit anahtarlı öğelerin sırası korunmaz.
// Varsayılan olarak eşitlikler girdinin TERSİ sırasında döner (SORT=stable: kararlı V8 sırası).
if (process.env.SORT !== "stable") {
    vm.runInContext("(function () { var os = Array.prototype.sort; Array.prototype.sort = function (c) {" +
                    " if (typeof c !== 'function') { return os.call(this); } this.reverse(); return os.call(this, c); }; })();", ctx);
}
var t0 = Date.now();
vm.runInContext(src, ctx, { filename: scriptPath, timeout: 600000 });
var dt = Date.now() - t0;
if (process.env.COUNT) { console.log("  yerleşim hesabı: " + (ctx.globalThis && ctx.globalThis.__N || vm.runInContext("typeof __N === 'undefined' ? 0 : __N", ctx))); }
var LOG = (alerts[alerts.length - 1] || "").split("\n");
// v4.22 biçimi: "x / y soru yer değiştirdi." satırını eski özet satırına çevir (araçların uyumu için)
LOG = LOG.map(function (l) { var mm = /^(\d+) \/ (\d+) soru yer değiştirdi\./.exec(l); return mm ? "YER DEĞİŞTİREN SORU: " + mm[1] + " / " + mm[2] : l.replace(/^\s*\u2022\s*/, ""); });
if (process.env.FULLALERT) { console.log(alerts.join("\n----\n")); }

// ---------- BAĞIMSIZ DENETİMLER ----------
var issues = [], KEYINFO = '', GROUPINFO = '';
function issue(s) { issues.push(s); }
function ov(a, b) { var w = Math.min(a[3], b[3]) - Math.max(a[1], b[1]), h = Math.min(a[2], b[2]) - Math.max(a[0], b[0]); return (w > 2 && h > 2) ? w * h : 0; }
var B = snapshot();
var aById = {}; A.forEach(function (r) { aById[r.it.id] = r; });
function label(x) {
    if (x.parentStory) { var t = x.parentStory._p[0]._t.replace(/[\t\u009e￼]/g, " ").trim(); return "[" + t.substr(0, 22) + "]"; }
    if (x.constructor.name === "Group") { var tf = x.allPageItems.filter(function (k) { return k.parentStory; })[0]; return "grup" + (tf ? "[" + tf.parentStory._p[0]._t.replace(/[\t\u009e]/g, " ").trim().substr(0, 18) + "]" : ""); }
    return x.constructor.name + (x.allGraphics.length ? "(görsel)" : "");
}
function aNumOf(it) { var tfs = it.parentStory ? [it] : it.allPageItems.filter(function (k) { return k.parentStory; }); return tfs.some(function (t) { return aNum[t.parentStory.id] !== undefined; }); }
// 1) YENİ ÇAKIŞMA: A'da örtüşmeyen iki öğe B'de örtüşüyor mu?
var moved = B.filter(function (r) { var a = aById[r.it.id]; return !a || a.pg !== r.pg || Math.abs(a.gb[0] - r.gb[0]) > 0.01 || Math.abs(a.gb[1] - r.gb[1]) > 0.01; });
moved.forEach(function (r) {
    B.forEach(function (o) {
        if (o.it === r.it || o.pg !== r.pg) { return; }
        if (o.kind === "GraphicLine" && r.kind === "GraphicLine") { return; }
        var nowOv = ov(r.gb, o.gb);
        if (!nowOv) { return; }
        var a1 = aById[r.it.id], a2 = aById[o.it.id];
        var was = (a1 && a2 && a1.pg === a2.pg) ? ov(a1.gb, a2.gb) : 0;
        // tasarım teması: yerinde duran öğe A'da da bu sayfada bir soruya en az bu derinlikte değiyordu
        if (!was && a2 && a2.pg === o.pg && Math.abs(a2.gb[0] - o.gb[0]) < 0.01) {
            var dB = Math.min(r.gb[2], o.gb[2]) - Math.max(r.gb[0], o.gb[0]);
            var dA = 0;
            A.forEach(function (x) { if (x.pg === o.pg && x.it !== o.it && aNumOf(x.it) && ov(x.gb, a2.gb)) { dA = Math.max(dA, Math.min(x.gb[2], a2.gb[2]) - Math.max(x.gb[0], a2.gb[0])); } });
            if (dB <= dA + 1) { return; }
        }
        if (nowOv > was + 4) {
            var key = [r.it.id, o.it.id].sort().join("|");
            if (!issue[key]) { issue[key] = 1; issue("ÇAKIŞMA s." + pages[r.pg].name + ": " + label(r.it) + " × " + label(o.it) + " (" + Math.round(nowOv) + " pt²)"); }
        }
    });
});
// 1b) ÇİZGİ: taşınan bir sorunun içinden, A'da hiçbir soruyu kesmeyen bir çizgi geçiyor mu?
function crossLine(l, e) {
    var vert = (l[3] - l[1]) < 3, horz = (l[2] - l[0]) < 3;
    if (vert) { var lx = (l[1] + l[3]) / 2; return lx > e[1] + 3 && lx < e[3] - 3 && (Math.min(l[2], e[2]) - Math.max(l[0], e[0])) > 3; }
    if (horz) { var ly = (l[0] + l[2]) / 2; return ly > e[0] + 3 && ly < e[2] - 3 && (Math.min(l[3], e[3]) - Math.max(l[1], e[1])) > 3; }
    return false;
}
B.forEach(function (ln) {
    if (ln.kind !== "GraphicLine") { return; }
    var la = aById[ln.it.id];
    var crossedA = la && A.some(function (x) { return x.pg === la.pg && x.it !== ln.it && x.kind === "TextFrame" && QRE.test(x.it.parentStory._p[0]._t) && crossLine(la.gb, x.gb); });
    if (crossedA) { return; }
    B.forEach(function (q) {
        if (q.pg !== ln.pg || q.kind === "GraphicLine" || q.it === ln.it) { return; }
        if (crossLine(ln.gb, q.gb)) {
            var a0 = aById[q.it.id];
            if (a0 && la && a0.pg === la.pg && crossLine(la.gb, a0.gb)) { return; }
            issue("ÇİZGİ s." + pages[q.pg].name + ": çizgi [" + ln.gb.map(Math.round).join(" ") + "] " + label(q.it) + " içinden geçiyor");
        }
    });
});
// 1c) KİTAPÇIK HARFİ: B'de hiçbir yerde tek başına "A" kitapçık harfi / "A A A A A" bandı kalmamalı
Object.keys(STORIES).forEach(function (sid) {
    var t = STORIES[sid]._p.map(function (p) { return p._t; }).join("\r").replace(/^\s+|\s+$/g, "");
    if (/^A([\s  -​]+A)*$/.test(t) || (/K[İI]TAP[ÇC]/.test(t) && t.length <= 40 && /(^|[^\wÇĞİÖŞÜçğıöşü])A([^\wÇĞİÖŞÜçğıöşü]|$)/.test(t))) {
        var on = ALLTOP.some(function (x) { return x.pg && ((x.parentStory && x.parentStory.id === sid) || x.allPageItems.some(function (k) { return k.parentStory && k.parentStory.id === sid; })); });
        var onMaster = M.masters.some(function (m) { return m.story === sid; });
        if (on || onMaster) { issue("KİTAPÇIK HARFİ B'de hâlâ A: " + JSON.stringify(t) + (onMaster ? " (master)" : " (sayfa)")); }
    }
});
var secA = doc.sections.filter(function (x) { return /(^|[^\w])A([^\w]|$)/.test(String(x.marker)); });
if (secA.length) { issue("BÖLÜM İŞARETİ B'de hâlâ A: " + secA.map(function (x) { return x.marker; }).join(",")); }
// 2) SAYFA DIŞINA TAŞMA
//    Soru: kenar boşluğu ya da A'da o sayfada bir sorunun indiği en alt nokta (altbilgi bandına
//    konmuş "TESTİ BİTTİ" gibi sabit çerçeveler soru sınırını aşağı çekmez). Diğer öğeler: eski kural.
var qaBot = {};
questionsAt(A, true).forEach(function (q) { if (!(qaBot[q.pg] >= q.gb[2])) { qaBot[q.pg] = q.gb[2]; } });
moved.forEach(function (r) {
    var p = M.pages[r.pg], bot = H - (p.margin ? p.margin.Bottom : 0);
    var isQ = (r.it.parentStory ? [r.it] : r.it.allPageItems.filter(function (k) { return k.parentStory; }))
              .some(function (tf) { return aNum[tf.parentStory.id] !== undefined; });
    if (isQ) { if (qaBot[r.pg] > bot) { bot = qaBot[r.pg]; } }
    else { A.forEach(function (x) { if (x.pg === r.pg && x.kind !== "GraphicLine" && x.gb[2] > bot && x.gb[2] < H) { bot = x.gb[2]; } }); }
    if (r.gb[2] > bot + 2) { issue("TAŞMA s." + pages[r.pg].name + ": " + label(r.it) + " alt=" + Math.round(r.gb[2]) + " > " + Math.round(bot)); }
    if (r.gb[1] < -1 || r.gb[3] > W + 1) { issue("YATAY TAŞMA s." + pages[r.pg].name + ": " + label(r.it)); }
});
// 3) NUMARA DİZİSİ + TEST SINIRI: B'de her testte 1..N bir kez, sorular kendi testinin sayfalarında
function questionsAt(snap, useA) {
    var qs = [];
    snap.forEach(function (r) {
        var tfs = r.it.parentStory ? [r.it] : r.it.allPageItems.filter(function (k) { return k.parentStory; });
        tfs.forEach(function (tf) { var m = QRE.exec(tf.parentStory._p[0]._t); if (aNum[tf.parentStory.id] !== undefined) { qs.push({ sid: tf.parentStory.id, num: useA ? aNum[tf.parentStory.id] : (m ? +m[1] : -1), pg: r.pg, gb: r.gb, it: r.it }); } });
    });
    return qs;
}
var qa = questionsAt(A, true), qb = questionsAt(B, false);
// A'da testleri çıkar: sayfa sırası + okuma sırası, 1'e dönüşte yeni test
function colOf(g) { return ((g[3] - g[1]) < W * 0.55 && (g[1] + g[3]) / 2 > W / 2) ? 1 : 0; }
function readingOrder(q) { return q.slice(0).sort(function (a, b) { return (a.pg - b.pg) || (colOf(a.gb) - colOf(b.gb)) || (a.gb[0] - b.gb[0]); }); }
var testOf = {}, t = -1, testPages = [];
readingOrder(qa).forEach(function (q) { if (q.num === 1) { t++; testPages[t] = {}; } if (t < 0) { t = 0; testPages[0] = {}; } testOf[q.sid] = t; testPages[t][q.pg] = 1; });
var bNums = {};
qb.forEach(function (q) {
    var tt = testOf[q.sid]; if (tt === undefined) { return; }
    if (!testPages[tt][q.pg]) { issue("TEST DIŞI: Test " + (tt + 1) + " sorusu (A" + aNum[q.sid] + ") s." + pages[q.pg].name + " sayfasına gitti"); }
    bNums[tt] = bNums[tt] || {}; bNums[tt][q.num] = (bNums[tt][q.num] || 0) + 1;
});
// 1b) OKUMA SIRASI (v4.26): B'de her testin numaraları sayfa sayfa okuma sırasıyla artmalı —
// tam genişlik soru kendi bandıdır; iki sütunlu bantta önce sol sütun yukarıdan aşağı, sonra sağ sütun.
// A'nın kendisi bu sıraya uymayan sayfa (tasarım gereği) denetim dışıdır.
function bandSeq(list) {
    var bySeq = list.slice(0).sort(function (a, b) { return (a.pg - b.pg) || (a.gb[0] - b.gb[0]) || (a.gb[1] - b.gb[1]); });
    var out = [], band = null, lastPg = -1;
    function flush() { if (!band) { return; } band.sort(function (a, b) { return (colOf(a.gb) - colOf(b.gb)) || (a.gb[0] - b.gb[0]); }); out = out.concat(band); band = null; }
    bySeq.forEach(function (q) {
        if (q.pg !== lastPg) { flush(); lastPg = q.pg; }
        if (q.gb[3] - q.gb[1] > W * 0.55) { flush(); out.push(q); return; }
        if (!band) { band = []; }
        band.push(q);
    });
    flush();
    return out;
}
function orderBreaks(list) {
    var seq = bandSeq(list), last = {}, bad = {};
    seq.forEach(function (q) {
        var tt = testOf[q.sid]; if (tt === undefined) { return; }
        if (last[tt] !== undefined && q.num <= last[tt].num) { bad[q.pg] = (bad[q.pg] || []).concat([last[tt].num + "→" + q.num]); }
        last[tt] = q;
    });
    return bad;
}
var aBreak = orderBreaks(qa), bBreak = orderBreaks(qb);
Object.keys(bBreak).forEach(function (pg) {
    if (aBreak[pg]) { return; }
    issue("OKUMA SIRASI s." + pages[pg].name + ": numaralar okuma sırasıyla artmıyor (" + bBreak[pg].join(", ") + ")");
});
Object.keys(bNums).forEach(function (tt) {
    var nums = Object.keys(bNums[tt]).map(Number).sort(function (a, b) { return a - b; });
    var n = nums.length, bad = [];
    for (var i = 1; i <= nums[nums.length - 1]; i++) { if (!bNums[tt][i]) { bad.push("eksik " + i); } else if (bNums[tt][i] > 1) { bad.push(i + "×" + bNums[tt][i]); } }
    if (bad.length) { issue("NUMARA Test " + (+tt + 1) + ": " + bad.join(", ")); }
});
// 3b) BRANŞ (fuzz.py varyasyonları): soru, A'daki branşının sayfalarında ve numara aralığında kalmalı
if (M.branchOf) {
    var brPages = {}, brLo = {}, brHi = {};
    qa.forEach(function (q) {
        var b = M.branchOf[q.sid]; if (b === undefined) { return; }
        brPages[b] = brPages[b] || {}; brPages[b][q.pg] = 1;
        if (brLo[b] === undefined || q.num < brLo[b]) { brLo[b] = q.num; }
        if (brHi[b] === undefined || q.num > brHi[b]) { brHi[b] = q.num; }
    });
    qb.forEach(function (q) {
        var b = M.branchOf[q.sid]; if (b === undefined) { return; }
        if (!brPages[b][q.pg] || q.num < brLo[b] || q.num > brHi[b]) {
            issue("BRANŞ DIŞI: A" + aNum[q.sid] + " (branş " + (b + 1) + ") → s." + pages[q.pg].name + " no " + q.num);
        }
    });
}
// 3c) ÖZGÜN ORTAK METİN GRUBU (yönergesi silinmiş olsa bile): grup sayfasında, numaraları kendi arasında
if (M.origGroups) {
    M.origGroups.forEach(function (g) {
        var an = [], bn = [], bad = false;
        g.sids.forEach(function (sid) {
            var a = qa.filter(function (x) { return x.sid === sid; })[0], b = qb.filter(function (x) { return x.sid === sid; })[0];
            if (!a || !b) { return; }
            an.push(a.num); bn.push(b.num);
            if (b.pg !== g.pg) { bad = true; }
        });
        an.sort(function (x, y) { return x - y; }); bn.sort(function (x, y) { return x - y; });
        // v4.26: grubun yönergesi B'de aynı miktarda yeniden numaralandıysa (bant takası) kayma beklenir
        if (an.length) {
            GROUPS_A.forEach(function (gd) {
                if (gd.pg !== g.pg || gd.lo !== an[0] || gd.hi !== an[an.length - 1]) { return; }
                var rD = dirRange(gd.tf.parentStory._p.map(function (p) { return p._t; }).join(" "));
                if (rD && rD.lo !== gd.lo) { var dl = rD.lo - gd.lo; an = an.map(function (v) { return v + dl; }); }
            });
        }
        if (bad || an.join(",") !== bn.join(",")) { issue("ORTAK METİN (özgün) s." + pages[g.pg].name + ": A " + an.join(",") + " → B " + bn.join(",") + (bad ? " (sayfa dışı)" : "")); }
    });
}
// 4) HİZA: taşınan soru çerçevesinin sol kenarı, o sayfada A'daki bir soru sütununun sol kenarına denk mi?
qb.forEach(function (q) {
    var a = qa.filter(function (x) { return x.sid === q.sid; })[0];
    if (!a || (a.pg === q.pg && Math.abs(a.gb[1] - q.gb[1]) < 0.5)) { return; }
    var cols = qa.map(function (x) { return x.gb[1]; });
    if (!cols.some(function (x) { return Math.abs(x - q.gb[1]) < 1.5; })) {
        issue("HİZA s." + pages[q.pg].name + ": A" + aNum[q.sid] + " sol kenarı x=" + q.gb[1].toFixed(1) + " sayfadaki sütunlara (" + cols.map(function (c) { return c.toFixed(1); }).filter(function (v, i, s) { return s.indexOf(v) === i; }).join(",") + ") denk değil");
    }
});
// 5) CEVAP ANAHTARI: B anahtarında (test t, n) harfi = B'de t testinde n numaraya gelen sorunun A anahtarındaki harfi
var KEY_B = keyTokens();
if (KEY_A && KEY_B) {
    var aL = {}; KEY_A.forEach(function (k) { aL[k.sec + ":" + k.num] = k.L; });
    var expect = {};
    qb.forEach(function (q) { var tt = testOf[q.sid]; if (tt === undefined) { return; } expect[tt + ":" + q.num] = aL[tt + ":" + aNum[q.sid]]; });
    var bad = [];
    KEY_B.forEach(function (k) { var e = expect[k.sec + ":" + k.num]; if (e && e !== k.L) { bad.push("Test " + (k.sec + 1) + " S" + k.num + ": B'de " + k.L + ", olması gereken " + e); } });
    if (bad.length) { issue("CEVAP ANAHTARI " + bad.length + " yanlış: " + bad.slice(0, 6).join("; ")); }
    KEYINFO = "anahtar " + KEY_B.length + " girdi denetlendi";
} else { KEYINFO = "anahtar bloğu yok"; }
// 6) ORTAK METİN GRUPLARI: gruptaki sorular aynı sayfada, A'daki grup slotlarında ve grup numaralarında
// v4.26: yönerge B'de yeniden numaralanmış olabilir (ortak metin bandı sayfa içinde yer değiştirdi):
// grup B'deki yönerge metnine göre denetlenir; sorular yönergenin ALTINDA, A'daki grup sütunlarında olmalı.
var dirMoved = 0;
GROUPS_A.forEach(function (g) {
    var tB = g.tf.parentStory._p.map(function (p) { return p._t; }).join(" ");
    var rB = dirRange(tB);
    if (!rB) { issue("ORTAK METİN s." + pages[g.pg].name + " grup " + g.lo + "-" + g.hi + ": B'de yönerge okunamadı"); return; }
    if (rB.lo - g.lo !== rB.hi - g.hi) { issue("ORTAK METİN s." + pages[g.pg].name + " grup " + g.lo + "-" + g.hi + ": yönerge tutarsız güncellendi → " + rB.lo + "-" + rB.hi); }
    if (rB.lo !== g.lo) { dirMoved++; }
    var bpg = g.top.pg ? g.top.pg.idx : g.pg, dirY = g.tf.geometricBounds[0];
    var aq = qa.filter(function (q) { return q.pg === g.pg && q.num >= g.lo && q.num <= g.hi; });
    aq.forEach(function (q) {
        var b = qb.filter(function (x) { return x.sid === q.sid; })[0];
        if (!b) { return; }
        var slotOk = aq.some(function (o) { return Math.abs(o.gb[1] - b.gb[1]) < 1; }) && b.gb[0] >= dirY - 1;
        if (b.pg !== bpg || b.num < rB.lo || b.num > rB.hi || !slotOk) {
            issue("ORTAK METİN s." + pages[g.pg].name + " grup " + rB.lo + "-" + rB.hi + ": A" + q.num + " → s." + pages[b.pg].name + " no " + b.num + (slotOk ? "" : " (grup slotu dışında / yönergenin üstünde)"));
        }
    });
    // gruba dışarıdan soru girmiş mi?
    qb.forEach(function (b) {
        if (b.pg !== bpg || b.num < rB.lo || b.num > rB.hi) { return; }
        var a = qa.filter(function (x) { return x.sid === b.sid; })[0];
        if (a && (a.pg !== g.pg || a.num < g.lo || a.num > g.hi)) { issue("ORTAK METİN s." + pages[g.pg].name + " grup " + rB.lo + "-" + rB.hi + ": dışarıdan A" + a.num + " (s." + pages[a.pg].name + ") girdi"); }
    });
});
GROUPINFO = GROUPS_A.length + " ortak metin grubu denetlendi" + (dirMoved ? " (" + dirMoved + " yönerge yeniden numaralandı)" : "");
// 7) HİZA: (a) sayfanın ilk sorusu A'daki yükseklikte, (b) A'da aynı satırdaki iki sütun
//    slotu B'de de aynı satırda, (c) dikey ayırıcı çizgi ilk satırla hizalı
var nAlign = 0;
pages.forEach(function (p, i) {
    var aq = qa.filter(function (q) { return q.pg === i; }), bq = qb.filter(function (q) { return q.pg === i; });
    if (!aq.length || !bq.length) { return; }
    var aMin = Math.min.apply(null, aq.map(function (q) { return q.gb[0]; })), bMin = Math.min.apply(null, bq.map(function (q) { return q.gb[0]; }));
    // v4.26: ortak metin bandı sayfanın başına geçtiyse sayfanın ilk öğesi yönergedir
    GROUPS_A.forEach(function (g) {
        if (g.pg !== i) { return; }
        var gA = g.top.geometricBounds ? g.top._src.gb[0] : g.y1, gB = g.top.geometricBounds[0];
        if (gA < aMin) { aMin = gA; }
        if (gB < bMin) { bMin = gB; }
    });
    if (Math.abs(aMin - bMin) > 0.5) { issue("SAYFA BAŞI s." + p.name + ": ilk soru A'da y=" + aMin.toFixed(1) + ", B'de y=" + bMin.toFixed(1)); }
    function colList(list, c) { return list.filter(function (q) { return (q.gb[3] - q.gb[1]) < W * 0.55 && colOf(q.gb) === c; }).sort(function (x, y) { return x.gb[0] - y.gb[0]; }); }
    var aL = colList(aq, 0), aR = colList(aq, 1), bL = colList(bq, 0), bR = colList(bq, 1);
    aL.forEach(function (x, li) { aR.forEach(function (y, ri) {
        var dAr = Math.abs(x.gb[0] - y.gb[0]);
        if (dAr > 3) { return; }   // 1-3 pt'lik tasarım kaçıklığı da satırdır
        nAlign++;
        // v4.26: iki soru da AYNI kaynak sayfadan blok hâlinde geldiyse (tam sayfa takası) kaynak sayfadaki
        // kendi kaçıklıkları korunur — izin verilen fark o kaçıklıktır
        var tol = dAr;
        if (bL[li] && bR[ri]) {
            var sL = qa.filter(function (z) { return z.sid === bL[li].sid; })[0], sR = qa.filter(function (z) { return z.sid === bR[ri].sid; })[0];
            if (sL && sR && sL.pg === sR.pg && sL.pg !== i) { var dS = Math.abs(sL.gb[0] - sR.gb[0]); if (dS <= 3 && dS > tol) { tol = dS; } }
        }
        if (bL[li] && bR[ri] && Math.abs(bL[li].gb[0] - bR[ri].gb[0]) > tol + 1) {
            issue("SATIR HİZASI s." + p.name + ": A'da aynı satırdaki sol/sağ slotlar B'de " + bL[li].gb[0].toFixed(1) + " / " + bR[ri].gb[0].toFixed(1));
        }
    }); });
    // (c) ayırıcı: A'da bir sütun sorusunun üst kenarıyla başlayan dikey çizgi, B'de bulunduğu sayfada
    //     yine bir sütun sorusunun üst kenarıyla (±8) başlamalı (blok takasıyla sayfa değiştirmiş olabilir)
    A.forEach(function (r) {
        if (r.pg !== i || r.kind !== "GraphicLine" || (r.gb[3] - r.gb[1]) > 3 || (r.gb[2] - r.gb[0]) < 30) { return; }
        var colA = aq.filter(function (q) { return (q.gb[3] - q.gb[1]) < W * 0.55; });
        if (!colA.some(function (q) { return Math.abs(q.gb[0] - r.gb[0]) <= 8; })) { return; }
        var rb = B.filter(function (x) { return x.it === r.it; })[0];
        var colB = qb.filter(function (q) { return q.pg === rb.pg && (q.gb[3] - q.gb[1]) < W * 0.55; });
        if (!colB.some(function (q) { return Math.abs(q.gb[0] - rb.gb[0]) <= 8; })) {
            issue("AYIRICI s." + pages[rb.pg].name + ": çizgi üstü y=" + rb.gb[0].toFixed(1) + ", sütun soruları: " + colB.map(function (q) { return q.gb[0].toFixed(0); }).join(","));
        }
    });
});
var summary = LOG.filter(function (l) { return /Bölüm işareti|Master üst bant|A içeren|B kopyası|Sorusuz sayfada|YER DEĞİŞTİREN|KRİTİK|UYARI|Ortak metne|kilitlendi|taşınacak|Envanter|Ders bölgeleri|Geri alınan|Tam sayfa|İkinci deneme|Yerinde kalanlar|HATA|Ortaokul/.test(l); });
console.log("################ " + M.name + "  (" + (dt / 1000).toFixed(3) + " sn)");
if (alerts.length > 1 || /HATA/.test(alerts[0] || "")) { console.log(alerts.join("\n----\n")); }
(QUIET ? summary.filter(function (l) { return /YER DEĞİŞTİREN|KRİTİK|Ortak metne|Envanter|Geri alınan|HATA/.test(l); }) : summary).forEach(function (l) { console.log("  LOG| " + l); });
var sameNum = qb.filter(function (q) { return testOf[q.sid] !== undefined && q.num === aNum[q.sid]; }).length;
console.log("  Denetim: " + (issues.length ? issues.length + " sorun" : "TEMİZ") + "  (" + KEYINFO + "; " + GROUPINFO + "; " + nAlign + " satır hizası; numarası aynı kalan " + sameNum + ")");
issues.forEach(function (s) { console.log("   ✘ " + s); });
if (process.argv.indexOf("--layout") > 0) {
    pages.forEach(function (p, i) {
        var qs = qb.filter(function (q) { return q.pg === i; }).sort(function (a, b) { return (a.gb[1] > 290) - (b.gb[1] > 290) || a.gb[0] - b.gb[0]; });
        if (qs.length) { console.log("   s." + p.name + ": " + qs.map(function (q) { return q.num + "←A" + aNum[q.sid] + (qa.filter(function (x) { return x.sid === q.sid; })[0].pg !== i ? "(s." + pages[qa.filter(function (x) { return x.sid === q.sid; })[0].pg].name + ")" : ""); }).join(" ")); }
    });
}
var pgArg = process.argv.indexOf("--page");
if (pgArg > 0 && process.argv[pgArg + 1] !== "ALL") {
    process.argv[pgArg + 1].split(",").forEach(function (name) {
        var pi = pages.filter(function (p) { return p.name === name; })[0].idx;
        var p = M.pages[pi];
        console.log("\n  === s." + name + "  (alt kenar boşluğu sınırı y=" + Math.round(H - p.margin.Bottom) + ", sayfa yüksekliği " + Math.round(H) + ")");
        var rows = [];
        B.forEach(function (r) { if (r.pg === pi) { rows.push(r); } });
        A.forEach(function (r) { if (r.pg === pi && !rows.some(function (x) { return x.it === r.it; })) { rows.push({ it: r.it, pg: -1, gb: null }); } });
        rows.sort(function (a, b) { var ga = (aById[a.it.id] && aById[a.it.id].pg === pi) ? aById[a.it.id].gb : a.gb, gb2 = (aById[b.it.id] && aById[b.it.id].pg === pi) ? aById[b.it.id].gb : b.gb; return (ga ? ga[1] > W / 2 : 1) - (gb2 ? gb2[1] > W / 2 : 1) || (ga ? ga[0] : 9999) - (gb2 ? gb2[0] : 9999); });
        rows.forEach(function (r) {
            var a = aById[r.it.id], f = function (g) { return g ? "[" + g.map(function (v) { return ("    " + Math.round(v)).slice(-4); }).join(" ") + "]" : "[       --        ]"; };
            console.log("   A" + f(a && a.pg === pi ? a.gb : null) + "  B" + f(r.gb) + "  " + label(r.it));
        });
    });
}
// GEOMOUT=dosya: B'deki tüm çerçevelerin sayfa, konum ve metin başı (sürümler arası birebir karşılaştırma için)
if (process.env.GEOMOUT) {
    var gl = [];
    (function walkG(list, depth) {
        list.forEach(function (x) {
            var g = x.geometricBounds || [0, 0, 0, 0], t = "";
            try { if (x.parentStory) { t = x.parentStory._p.map(function (pp) { return pp._t; }).join("¶").substr(0, 40); } } catch (eG) {}
            gl.push([x.pg ? x.pg.name : "-", x.id, x.constructor.name, g.map(function (v) { return v.toFixed(1); }).join(","), depth, t].join("|"));
            walkG(x._kids || [], depth + 1);
        });
    })(ALLTOP, 0);
    fs.writeFileSync(process.env.GEOMOUT, gl.sort().join("\n"));
}
// RENDER=klasör: A/B sayfa çizimleri (görsel denetim)
if (process.env.RENDER) { require("./render.js")(process.env.RENDER, { A: A, B: B, M: M, W: W, H: H, aNum: aNum }); }

// DRIFT=1: her sayfada B'deki sütun sorularının, A'da o sütunda aynı sıradaki slotun y'sinden ortalama kayması
if (process.env.DRIFT) {
    var dsum = 0, dn = 0, dbig = 0;
    pages.forEach(function (p, i) {
        [0, 1].forEach(function (c) {
            function col(list) { return list.filter(function (q) { return q.pg === i && (q.gb[3] - q.gb[1]) < W * 0.55 && colOf(q.gb) === c; }).sort(function (x, y) { return x.gb[0] - y.gb[0]; }); }
            var a = col(qa), b = col(qb);
            if (a.length !== b.length) { return; }
            for (var k = 0; k < a.length; k++) { var d = Math.abs(a[k].gb[0] - b[k].gb[0]); dsum += d; dn++; if (d > 60) { dbig++; if (process.env.DRIFT === '2') { console.log('  KAYMA s.' + p.name + ' sütun ' + c + ' sıra ' + k + ': A y=' + Math.round(a[k].gb[0]) + ' B y=' + Math.round(b[k].gb[0])); } } }
        });
    });
    console.log("DRIFT " + (dn ? (dsum / dn).toFixed(2) : 0) + " " + dn + " " + dbig);
}
