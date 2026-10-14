// Kitapçık B Oluşturucu için sahte InDesign DOM'u: scripti InDesign olmadan Node'da uçtan uca çalıştırır.
// Kullanım: node indesign-scripts/test/harness.js indesign-scripts/kitapcik-b-olusturucu.jsx indesign-scripts/test/senaryo1.js
var fs = require("fs"), vm = require("vm");
var scriptPath = process.argv[2], scenPath = process.argv[3];
var W = 595, H = 842;
var nextId = 1;
var ALL = [];           // tüm sayfa öğeleri (sayfa üyeliği .pg ile)
var grepPrefs = { findWhat: "" };

function mkPara(text, style) { return { _t: text, appliedParagraphStyle: { name: style || "Soru" } }; }
function Story(paras) {
    var st = { id: nextId++, _p: paras, pageItems: [], textContainers: [] };
    paras.forEach(function (p) {
        Object.defineProperty(p, "contents", { get: function () { return p._t; }, set: function (v) { p._t = v; } });
        p.findGrep = function () { return grepIn(function () { return p._t; }, function (v) { p._t = v; }); };
    });
    st.paragraphs = paras;
    Object.defineProperty(st, "texts", { get: function () {
        return [{ get contents() { return paras.map(function (p) { return p._t; }).join("\r"); },
                  set contents(v) { var parts = String(v).split("\r"); paras.length = 0;
                                    parts.forEach(function (t) { var np = mkPara(t); Object.defineProperty(np, "contents", { get: function () { return np._t; }, set: function (x) { np._t = x; } }); paras.push(np); }); } }];
    } });
    st.findGrep = function () {
        var whole = { get: function () { return paras.map(function (p) { return p._t; }).join("\r"); } };
        var res = [], re = new RegExp(grepPrefs.findWhat, "g"), txt = whole.get(), m;
        while ((m = re.exec(txt)) !== null) {
            (function (idx, len) {
                res.push({ get contents() { return whole.get().substr(idx, len); },
                           set contents(v) { // aynı uzunlukta değişim varsayımı
                               var t = whole.get(); t = t.substr(0, idx) + v + t.substr(idx + len);
                               var parts = t.split("\r"); for (var i = 0; i < paras.length; i++) { paras[i]._t = parts[i]; } } });
            })(m.index, m[0].length);
        }
        return res;
    };
    return st;
}
function grepIn(get, set) {
    var re = new RegExp(grepPrefs.findWhat), m = re.exec(get());
    if (!m) { return []; }
    var idx = m.index, len = m[0].length;
    return [{ get contents() { return get().substr(idx, len); },
              set contents(v) { var t = get(); set(t.substr(0, idx) + v + t.substr(idx + len)); } }];
}
function baseItem(kind, pg, gb) {
    var it = { constructor: { name: kind }, id: nextId++, pg: pg, geometricBounds: gb.slice(0), parent: pg };
    it.move = function (to, by) {
        if (to && to._isPage) { it.pg = to; it.parent = to; if (it._kids) { it._kids.forEach(function (c) { c.pg = to; }); } return; }
        if (by) { var g = it.geometricBounds; it.geometricBounds = [g[0] + by[1], g[1] + by[0], g[2] + by[1], g[3] + by[0]];
                  if (it._kids) { it._kids.forEach(function (c) { var q = c.geometricBounds; c.geometricBounds = [q[0] + by[1], q[1] + by[0], q[2] + by[1], q[3] + by[0]]; }); } }
    };
    ALL.push(it);
    return it;
}
function TF(pg, gb, paras) {
    var it = baseItem("TextFrame", pg, gb);
    it.parentStory = Story(paras);
    it.parentStory.textContainers = [it];
    it.allPageItems = [];
    return it;
}
function Page(name, idx) {
    var p = { _isPage: true, name: String(name), id: 1000 + idx, bounds: [0, 0, H, W], marginPreferences: { bottom: 40 } };
    function of(kind) { return ALL.filter(function (x) { return x.pg === p && x.constructor.name === kind && !x._inGroup; }); }
    Object.defineProperty(p, "textFrames", { get: function () { return of("TextFrame"); } });
    Object.defineProperty(p, "groups", { get: function () { return of("Group"); } });
    Object.defineProperty(p, "rectangles", { get: function () { return of("Rectangle"); } });
    p.polygons = []; p.ovals = []; p.graphicLines = [];
    Object.defineProperty(p, "allPageItems", { get: function () { return ALL.filter(function (x) { return x.pg === p; }); } });
    p.parent = { pageItems: [] };
    return p;
}

// --- senaryo ---
var pages = [];
var api = {
    W: W, H: H, mkPara: mkPara, TF: TF, pages: pages,
    page: function (name) { var p = Page(name, pages.length); pages.push(p); return p; },
    rect: function (pg, gb) { return baseItem("Rectangle", pg, gb); },
    q: function (pg, gb, num, text, ans) {
        return TF(pg, gb, [mkPara(num + ".\t" + text), mkPara("A) seçenek bir"), mkPara("B) seçenek iki"),
                           mkPara("C) seçenek üç"), mkPara(ans, "KOD VE CEVAP")]);
    },
    t: function (pg, gb, text) { return TF(pg, gb, [mkPara(text)]); }
};
var scen = require(require("path").resolve(scenPath));
var meta = scen(api);

var sections = [{ marker: "A" }];
var docName = meta.name || "6._SINIF_DENEME_1-A.indd";
var keyStory = null;
var doc = {
    modified: false, saved: true, pages: pages, sections: sections, masterSpreads: [],
    fullName: { name: encodeURI(docName), fsName: "/tmp/" + docName, parent: { fsName: "/tmp" } },
    viewPreferences: {}, documentPreferences: { facingPages: meta.facing !== false },
    save: function () {}
};
if (meta.key) { var kt = TF(pages[pages.length - 1], [700, 40, 800, 555], [mkPara(meta.key)]); kt.pg = null; keyStory = kt.parentStory; }
Object.defineProperty(doc, "stories", { get: function () {
    var s = ALL.filter(function (x) { return x.parentStory; }).map(function (x) { return x.parentStory; });
    return s;
} });
var alerts = [];
function ctl() { return { text: "", value: false, characters: 0, preferredSize: {}, graphics: { newPen: function () {}, PenType: { SOLID_COLOR: 0 } },
                          add: function (type, b, txt) { var c = ctl(); c.text = txt || ""; if (meta.ui && meta.ui[txt]) { meta.ui[txt](c); } return c; } }; }
var ctx = {
    app: { documents: { length: 1 }, activeDocument: doc, scriptPreferences: { enableRedraw: true },
           get findGrepPreferences() { return grepPrefs; }, set findGrepPreferences(v) { if (v === "NOTHING") { grepPrefs.findWhat = ""; } },
           changeGrepPreferences: {}, open: function () { return doc; }, doScript: function () { return ""; } },
    $: { os: "Macintosh OS 14" },
    Window: function () { var w = ctl(); w.show = function () { if (meta.pools) { poolsBox.text = meta.pools; } return 1; }; return w; },
    File: function (p) { return { fsName: p, name: encodeURI(String(p).split("/").pop()), exists: false, open: function () { return true; },
                                  write: function () {}, writeln: function () {}, close: function () {} }; },
    Folder: function () {}, ScriptLanguage: {}, MeasurementUnits: { POINTS: 0 }, RulerOrigin: { PAGE_ORIGIN: 0 },
    NothingEnum: { NOTHING: "NOTHING" }, alert: function (m) { alerts.push(m); }, confirm: function () { return true; },
    decodeURI: decodeURI, encodeURI: encodeURI, Math: Math, String: String, parseInt: parseInt, isNaN: isNaN, Error: Error, RegExp: RegExp
};
var poolsBox = null;
var origCtl = ctl;
// özel havuz kutusunu yakala (multiline edittext)
ctx.Window = function () { var w = origCtl(); var add0 = w.add; w.add = function (type, b, txt, opts) {
    var c = add0.apply(w, arguments); var a1 = c.add; c.add = function (t2, b2, txt2, o2) { var cc = a1.apply(c, arguments); if (o2 && o2.multiline) { poolsBox = cc; } return cc; }; return c; };
    w.show = function () { if (meta.pools && poolsBox) { poolsBox.text = meta.pools; } return 1; }; return w; };
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
vm.runInContext(src, ctx, { filename: scriptPath });

// --- sonuç: her sayfada hangi A sorusu (ilk satır metni) var ---
var out = alerts.join("\n---\n");
console.log(out.split("\n").filter(function (l) { return /HATA|Sayfalar arası|Ortak metne|kilitlendi|taşınacak|KRİTİK|YER DEĞİŞTİREN|Tam sayfa|Yerinde/.test(l); }).join("\n"));
console.log("\n--- B yerleşimi (sayfa: numara ← A'daki kimlik) ---");
pages.forEach(function (p) {
    var qs = ALL.filter(function (x) { return x.pg === p && x._qid; })
                .sort(function (a, b) { return (a.geometricBounds[0] - b.geometricBounds[0]) || (a.geometricBounds[1] - b.geometricBounds[1]); });
    if (qs.length) {
        console.log("s." + p.name + ": " + qs.map(function (x) {
            var n = /^(\d+)\./.exec(x.parentStory.paragraphs[0]._t); return (n ? n[1] : "?") + "←" + x._qid;
        }).join("  "));
    }
    ALL.filter(function (x) { return x.pg === p && x._img; }).forEach(function (r) {
        console.log("   görsel " + r._img + " @ y" + Math.round(r.geometricBounds[0]) + " x" + Math.round(r.geometricBounds[1]));
    });
});
if (meta.check) { meta.check(ALL, pages); }
