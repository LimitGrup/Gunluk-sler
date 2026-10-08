// A ve B sayfalarını yan yana SVG olarak çizer (görsel hiza denetimi için).
// idmlrun.js içinden RENDER=klasör ortam değişkeniyle çağrılır; klasöre <belge>.html yazar.
// PNG için: node indesign-scripts/test/shot.js klasör/<belge>.html çıktı_klasörü [sayfa,...]
var fs = require("fs");
module.exports = function (dir, o) {
    var QRE = /^[\s​﻿￼\u009E]*(\d{1,3})\.(?=[\s\t])/;
    function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
    function qInfo(it, useA) {
        var tfs = it.parentStory ? [it] : it.allPageItems.filter(function (k) { return k.parentStory && !o.M.anchoredOwner[k.id]; });
        for (var i = 0; i < tfs.length; i++) {
            var sid = tfs[i].parentStory.id;
            if (o.aNum[sid] !== undefined) {
                var m = QRE.exec(tfs[i].parentStory._p[0]._t);
                return useA ? "A" + o.aNum[sid] : ((m ? m[1] : "?") + "←A" + o.aNum[sid]);
            }
        }
        return null;
    }
    function shapes(snap, pgIdx, useA) {
        var out = [];
        var p = o.M.pages[pgIdx], mg = p.margin || { Top: 0, Bottom: 0, Left: 0, Right: 0 };
        out.push('<rect x="0" y="0" width="' + o.W + '" height="' + o.H + '" fill="#fff" stroke="#999"/>');
        out.push('<rect x="' + mg.Left + '" y="' + mg.Top + '" width="' + (o.W - mg.Left - mg.Right) + '" height="' + (o.H - mg.Top - mg.Bottom) +
                 '" fill="none" stroke="#e0a" stroke-dasharray="4 3" stroke-width="0.8"/>');
        snap.forEach(function (r) {
            if (r.pg !== pgIdx) { return; }
            var g = r.gb, x = g[1], y = g[0], w = g[3] - g[1], h = g[2] - g[0];
            if (r.kind === "GraphicLine") { out.push('<line x1="' + x + '" y1="' + y + '" x2="' + (x + w) + '" y2="' + (y + h) + '" stroke="#000" stroke-width="1.2"/>'); return; }
            var q = qInfo(r.it, useA);
            if (q) {
                out.push('<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" fill="rgba(60,120,255,0.18)" stroke="#2557d6" stroke-width="1.2"/>');
                out.push('<text x="' + (x + 4) + '" y="' + (y + 16) + '" font-size="15" font-weight="bold" fill="#123">' + esc(q) + '</text>');
                out.push('<text x="' + (x + 4) + '" y="' + (y + h - 4) + '" font-size="9" fill="#456">y ' + Math.round(y) + '–' + Math.round(y + h) + '</text>');
            } else {
                var isG = r.kind !== "TextFrame" && r.kind !== "Group";
                out.push('<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" fill="' + (isG ? "rgba(40,170,80,0.18)" : "rgba(120,120,120,0.18)") + '" stroke="' + (isG ? "#2a5" : "#777") + '" stroke-width="0.8"/>');
                var t = r.it.parentStory ? r.it.parentStory._p[0]._t : (r.kind === "Group" ? "grup" : r.kind);
                out.push('<text x="' + (x + 3) + '" y="' + (y + 10) + '" font-size="8" fill="#333">' + esc(String(t).replace(/[\t\u009e￼]/g, " ").trim().substr(0, 40)) + '</text>');
            }
        });
        return out.join("");
    }
    var html = ['<!doctype html><meta charset="utf-8"><style>body{font-family:sans-serif;background:#eee}div.p{display:inline-block;margin:6px;background:#fff;padding:4px}h3{margin:2px}</style>'];
    o.M.pages.forEach(function (p, i) {
        var has = o.A.some(function (r) { return r.pg === i; }) || o.B.some(function (r) { return r.pg === i; });
        if (!has) { return; }
        html.push('<div class="p" id="p' + esc(p.name) + '"><h3>s.' + esc(p.name) + ' — A (sol) / B (sağ)</h3>');
        ["A", "B"].forEach(function (k) {
            html.push('<svg width="' + (o.W * 0.62) + '" height="' + (o.H * 0.62) + '" viewBox="0 0 ' + o.W + ' ' + o.H + '">' + shapes(k === "A" ? o.A : o.B, i, k === "A") + '</svg>');
        });
        html.push("</div>");
    });
    if (!fs.existsSync(dir)) { fs.mkdirSync(dir, { recursive: true }); }
    fs.writeFileSync(dir + "/" + o.M.name + ".html", html.join("\n"));
};
