#target illustrator
// ============================================================
//  İKLİM GRAFİĞİ  –  Adobe Illustrator (ExtendScript)
//  Yağış: sütun  ·  Sıcaklık: çizgi  ·  Çift eksen
//  * 12 ay, 4 mevsim ya da serbest etiketler
//  * Birden çok grafik (A, B, C...) tek seferde, ızgara düzeninde
//  * Veri: "İklim Grafiği Okuyucu" sayfasından, Excel'den ya da elle
//  * Her şey düzenlenebilir vektör olarak çizilir ve gruplanır
//  Kullanım: Dosya > Komut Dosyaları > Diğer Komut Dosyası...
//
//  Veri biçimi (her satır):   Etiket ; Sıcaklık ; Yağış
//      O;24,7;10
//      Ş;26;18
//  Birden çok grafik:          [A]  ...satırlar...  [B]  ...satırlar...
//  Eksen (isteğe bağlı):       @sicaklik;sol;0;40;10
//                              @yagis;sag;0;400;100
//  Ayırıcı: noktalı virgül ya da sekme (Excel). Ondalık: virgül ya da nokta.
// ============================================================

var MM = 2.834645669;
var SETTINGS_FILE = "IklimGrafigi_ayarlar.txt";

var SAMPLE_12 = [
    "# Etiket ; Sıcaklık (°C) ; Yağış (mm)",
    "O;24,7;10",
    "Ş;26;18",
    "M;27,3;48",
    "N;28;100",
    "M;29;170",
    "H;29,5;197",
    "T;29,3;133",
    "A;28,4;78",
    "E;27,1;30",
    "E;25,9;12",
    "K;24,9;12",
    "A;24,1;10"
].join("\n");

var SAMPLE_4 = [
    "[A]",
    "@sicaklik;sol;0;25;5",
    "@yagis;sag;0;500;100",
    "kış;6,5;255",
    "ilkb.;10;160",
    "yaz;24,5;65",
    "sonb.;15;200",
    "[B]",
    "@sicaklik;sol;0;25;5",
    "@yagis;sag;0;500;100",
    "kış;5;270",
    "ilkb.;8;200",
    "yaz;25;300",
    "sonb.;15;230"
].join("\n");

var BAR_PRESETS = [
    ["Mavi", "75,25,0,0"],
    ["Açık mavi", "60,10,0,0"],
    ["Turuncu", "0,55,95,0"],
    ["Yeşil", "75,5,100,0"],
    ["Gri", "0,0,0,45"],
    ["Siyah", "0,0,0,100"]
];
var LINE_PRESETS = [
    ["Kırmızı", "0,90,85,0"],
    ["Mavi", "85,40,0,0"],
    ["Turuncu", "0,60,95,0"],
    ["Siyah", "0,0,0,100"]
];
var LETTER_FORMATS = ["A)", "A.", "(A)", "A"];
var LINE_WIDTHS = [0.5, 0.75, 1, 1.25, 1.5, 2];
var DOT_SIZES = [2, 2.5, 3, 4];
var FONT_SIZES = [6, 6.5, 7, 7.5, 8, 9, 10, 11, 12];

var DEFAULTS = {
    data: SAMPLE_12,
    side: 0,          // 0: sıcaklık solda, 1: yağış solda
    scaleMode: 0,     // 0: veriden/otomatik, 1: otomatik, 2: elle
    tMin: "0", tMax: "40", tStep: "10",
    pMin: "0", pMax: "400", pStep: "100",
    sameScale: false,
    tTitle: "Sıcaklık (°C)",
    pTitle: "Yağış (mm)",
    titleMode: 0,     // 0: yatay, 1: dikey, 2: yok
    xTitle: "",
    grid: 0,          // 0: yok, 1: düz, 2: kesikli
    tickMode: 0,      // 0: dışa, 1: içe, 2: kesişen, 3: yok
    frame: false,
    xTicks: false,
    wMm: "90", hMm: "60",
    cols: "2", gapMm: "10",
    letters: true, letterFmt: 0, centerLast: true,
    barCmyk: "75,25,0,0", barW: "60", barStroke: false, barGrad: false,
    lineCmyk: "0,90,85,0", lineW: 2, dots: true, dotSize: 1, smooth: false,
    legend: 0,        // 0: yok, 1: her grafikte, 2: tek (üstte), 3: köşelerde
    legBar: "Yağış", legLine: "Sıcaklık",
    fontSize: 2, fontName: ""
};

main();

// ============================================================
function main() {
    var S = loadSettings();
    var result = null;

    var ui = buildDialog(S, function (opts) { result = opts; });
    if (ui.show() !== 1 || !result) return;

    try {
        drawAll(result.opts, result.panels);
    } catch (e) {
        alert("Grafik çizilirken hata oluştu:\n" + e.message + (e.line ? "  (satır " + e.line + ")" : ""));
    }
}

// ---------------- ARAYÜZ ----------------
function buildDialog(S, onOk) {
    var w = new Window("dialog", "İklim Grafiği (Sıcaklık + Yağış)");
    w.orientation = "column";
    w.alignChildren = "fill";
    w.margins = 14;
    w.spacing = 10;

    var tabs = w.add("tabbedpanel");
    tabs.alignChildren = "fill";
    var tD = tabs.add("tab", undefined, "Veri");
    var tA = tabs.add("tab", undefined, "Eksenler ve yazılar");
    var tG = tabs.add("tab", undefined, "Görünüm");
    var allTabs = [tD, tA, tG];
    for (var ti = 0; ti < allTabs.length; ti++) {
        allTabs[ti].orientation = "column";
        allTabs[ti].alignChildren = "fill";
        allTabs[ti].margins = [12, 14, 12, 12];
        allTabs[ti].spacing = 8;
    }

    // ---- Veri sekmesi ----
    var info = tD.add("statictext", undefined,
        "Her satır bir ay ya da mevsim:   Etiket ; Sıcaklık ; Yağış\n" +
        "Excel'den üç sütunu kopyalayıp buraya yapıştırabilirsin.", { multiline: true });
    info.preferredSize = [580, 32];
    var dataInp = tD.add("edittext", undefined, S.data,
        { multiline: true, scrolling: true, wantReturn: true });
    dataInp.preferredSize = [580, 290];

    var dg = tD.add("group");
    dg.orientation = "row";
    var bLoad = dg.add("button", undefined, "Dosyadan yükle…");
    var bS12 = dg.add("button", undefined, "Örnek: 12 ay");
    var bS4 = dg.add("button", undefined, "Örnek: 4 mevsim, 2 grafik");
    var bClr = dg.add("button", undefined, "Temizle");

    var info2 = tD.add("statictext", undefined,
        "Birden çok grafik için her grafiğin başına [A], [B]… satırı koy.\n" +
        "@sicaklik;sol;0;40;10 gibi satırlar o grafiğin eksenini belirler " +
        "(Okuyucu sayfası bunları kendisi yazar).", { multiline: true });
    info2.preferredSize = [580, 46];

    bLoad.onClick = function () {
        var f = File.openDialog("Veri dosyasını seç (.txt, .csv)");
        if (!f) return;
        var txt = readTextFile(f);
        if (txt === null) { alert("Dosya okunamadı."); return; }
        dataInp.text = txt;
    };
    bS12.onClick = function () { dataInp.text = SAMPLE_12; };
    bS4.onClick = function () { dataInp.text = SAMPLE_4; };
    bClr.onClick = function () { dataInp.text = ""; };

    // ---- Eksenler sekmesi ----
    var pSide = tA.add("panel", undefined, "Eksen yerleşimi");
    pSide.alignChildren = "left"; pSide.margins = [12, 16, 12, 10];
    var sideDD = pSide.add("dropdownlist", undefined,
        ["Sıcaklık solda, yağış sağda", "Yağış solda, sıcaklık sağda"]);
    setSel(sideDD, S.side);
    pSide.add("statictext", undefined, "Veride @ satırı olan grafiklerde verideki yerleşim kullanılır.");

    var pScale = tA.add("panel", undefined, "Eksen ölçeği");
    pScale.alignChildren = "left"; pScale.margins = [12, 16, 12, 10]; pScale.spacing = 6;
    var gs = pScale.add("group");
    gs.add("statictext", [0, 0, 60, 20], "Ölçek:");
    var scaleDD = gs.add("dropdownlist", undefined,
        ["Veriden al (yoksa otomatik)", "Otomatik hesapla", "Elle gir"]);
    setSel(scaleDD, S.scaleMode);

    var gT = pScale.add("group");
    gT.add("statictext", [0, 0, 60, 20], "Sıcaklık:");
    gT.add("statictext", undefined, "en az");
    var tMinInp = gT.add("edittext", [0, 0, 52, 22], S.tMin);
    gT.add("statictext", undefined, "en çok");
    var tMaxInp = gT.add("edittext", [0, 0, 52, 22], S.tMax);
    gT.add("statictext", undefined, "aralık");
    var tStepInp = gT.add("edittext", [0, 0, 52, 22], S.tStep);

    var gP = pScale.add("group");
    gP.add("statictext", [0, 0, 60, 20], "Yağış:");
    gP.add("statictext", undefined, "en az");
    var pMinInp = gP.add("edittext", [0, 0, 52, 22], S.pMin);
    gP.add("statictext", undefined, "en çok");
    var pMaxInp = gP.add("edittext", [0, 0, 52, 22], S.pMax);
    gP.add("statictext", undefined, "aralık");
    var pStepInp = gP.add("edittext", [0, 0, 52, 22], S.pStep);

    var sameCb = pScale.add("checkbox", undefined, "Otomatik ölçek tüm grafiklerde aynı olsun");
    sameCb.value = S.sameScale;

    function updScale() {
        var man = scaleDD.selection && scaleDD.selection.index === 2;
        gT.enabled = man; gP.enabled = man; sameCb.enabled = !man;
    }
    scaleDD.onChange = updScale;
    updScale();

    var pTit = tA.add("panel", undefined, "Başlıklar");
    pTit.alignChildren = "left"; pTit.margins = [12, 16, 12, 10]; pTit.spacing = 6;
    var r1 = pTit.add("group");
    r1.add("statictext", [0, 0, 130, 20], "Sıcaklık başlığı:");
    var tTitleInp = r1.add("edittext", [0, 0, 170, 22], S.tTitle);
    var r2 = pTit.add("group");
    r2.add("statictext", [0, 0, 130, 20], "Yağış başlığı:");
    var pTitleInp = r2.add("edittext", [0, 0, 170, 22], S.pTitle);
    var r3 = pTit.add("group");
    r3.add("statictext", [0, 0, 130, 20], "Başlık yeri:");
    var titleDD = r3.add("dropdownlist", undefined,
        ["Eksenin üstünde (yatay)", "Eksen boyunca (dikey)", "Başlık yok"]);
    setSel(titleDD, S.titleMode);
    var r4 = pTit.add("group");
    r4.add("statictext", [0, 0, 130, 20], "Yatay eksen başlığı:");
    var xTitleInp = r4.add("edittext", [0, 0, 170, 22], S.xTitle);
    r4.add("statictext", undefined, "(ör. Aylar; boş = yok)");

    var pLn = tA.add("panel", undefined, "Eksen çizgileri");
    pLn.alignChildren = "left"; pLn.margins = [12, 16, 12, 10]; pLn.spacing = 6;
    var r5 = pLn.add("group");
    var gridDD = r5.add("dropdownlist", undefined,
        ["Kılavuz çizgisi yok", "Düz kılavuz çizgileri", "Kesikli kılavuz çizgileri"]);
    setSel(gridDD, S.grid);
    var tickDD = r5.add("dropdownlist", undefined,
        ["Çentikler dışa", "Çentikler içe", "Çentikler kesişen (+)", "Çentik yok"]);
    setSel(tickDD, S.tickMode);
    var r6 = pLn.add("group");
    var frameCb = r6.add("checkbox", undefined, "Kutu çerçeve");
    frameCb.value = S.frame;
    var xTickCb = r6.add("checkbox", undefined, "Yatay eksende çentik");
    xTickCb.value = S.xTicks;

    // ---- Görünüm sekmesi ----
    var pSz = tG.add("panel", undefined, "Ölçü ve yerleşim");
    pSz.alignChildren = "left"; pSz.margins = [12, 16, 12, 10]; pSz.spacing = 6;
    var s1 = pSz.add("group");
    s1.add("statictext", [0, 0, 150, 20], "Her grafik, genişlik (mm):");
    var wInp = s1.add("edittext", [0, 0, 52, 22], S.wMm);
    s1.add("statictext", undefined, "yükseklik (mm):");
    var hInp = s1.add("edittext", [0, 0, 52, 22], S.hMm);
    var s2 = pSz.add("group");
    s2.add("statictext", [0, 0, 150, 20], "Yan yana grafik sayısı:");
    var colsInp = s2.add("edittext", [0, 0, 52, 22], S.cols);
    s2.add("statictext", undefined, "aradaki boşluk (mm):");
    var gapInp = s2.add("edittext", [0, 0, 52, 22], S.gapMm);
    var s3 = pSz.add("group");
    var lettersCb = s3.add("checkbox", undefined, "Grafik harflerini yaz");
    lettersCb.value = S.letters;
    var letterDD = s3.add("dropdownlist", undefined, LETTER_FORMATS);
    setSel(letterDD, S.letterFmt);
    var centerCb = s3.add("checkbox", undefined, "Son satırı ortala");
    centerCb.value = S.centerLast;

    var pBar = tG.add("panel", undefined, "Sütunlar (yağış)");
    pBar.alignChildren = "left"; pBar.margins = [12, 16, 12, 10]; pBar.spacing = 6;
    var b1 = pBar.add("group");
    b1.add("statictext", [0, 0, 50, 20], "Renk:");
    var barPresetDD = b1.add("dropdownlist", undefined, presetNames(BAR_PRESETS));
    b1.add("statictext", undefined, "CMYK:");
    var barCmykInp = b1.add("edittext", [0, 0, 110, 22], S.barCmyk);
    selectPreset(barPresetDD, BAR_PRESETS, S.barCmyk);
    barPresetDD.onChange = function () {
        if (barPresetDD.selection) barCmykInp.text = BAR_PRESETS[barPresetDD.selection.index][1];
    };
    var b2 = pBar.add("group");
    b2.add("statictext", [0, 0, 120, 20], "Sütun genişliği (%):");
    var barWInp = b2.add("edittext", [0, 0, 52, 22], S.barW);
    var barStrokeCb = b2.add("checkbox", undefined, "Siyah kontur");
    barStrokeCb.value = S.barStroke;
    var barGradCb = b2.add("checkbox", undefined, "Degrade dolgu");
    barGradCb.value = S.barGrad;

    var pLine = tG.add("panel", undefined, "Çizgi (sıcaklık)");
    pLine.alignChildren = "left"; pLine.margins = [12, 16, 12, 10]; pLine.spacing = 6;
    var l1 = pLine.add("group");
    l1.add("statictext", [0, 0, 50, 20], "Renk:");
    var linePresetDD = l1.add("dropdownlist", undefined, presetNames(LINE_PRESETS));
    l1.add("statictext", undefined, "CMYK:");
    var lineCmykInp = l1.add("edittext", [0, 0, 110, 22], S.lineCmyk);
    selectPreset(linePresetDD, LINE_PRESETS, S.lineCmyk);
    linePresetDD.onChange = function () {
        if (linePresetDD.selection) lineCmykInp.text = LINE_PRESETS[linePresetDD.selection.index][1];
    };
    var l2 = pLine.add("group");
    l2.add("statictext", undefined, "Kalınlık:");
    var lwDD = l2.add("dropdownlist", undefined, numLabels(LINE_WIDTHS, " pt"));
    setSel(lwDD, S.lineW);
    var dotsCb = l2.add("checkbox", undefined, "Noktalar, çap:");
    dotsCb.value = S.dots;
    var dotDD = l2.add("dropdownlist", undefined, numLabels(DOT_SIZES, " pt"));
    setSel(dotDD, S.dotSize);
    var smoothCb = l2.add("checkbox", undefined, "Yumuşak eğri");
    smoothCb.value = S.smooth;

    var pTx = tG.add("panel", undefined, "Lejant ve yazı");
    pTx.alignChildren = "left"; pTx.margins = [12, 16, 12, 10]; pTx.spacing = 6;
    var x1 = pTx.add("group");
    x1.add("statictext", [0, 0, 50, 20], "Lejant:");
    var legendDD = x1.add("dropdownlist", undefined,
        ["Yok", "Her grafiğin üstünde", "Tüm grafiklerin üstünde (tek)", "Grafiğin sol ve sağ köşesinde"]);
    setSel(legendDD, S.legend);
    var x2 = pTx.add("group");
    x2.add("statictext", [0, 0, 50, 20], "Adlar:");
    var legBarInp = x2.add("edittext", [0, 0, 110, 22], S.legBar);
    var legLineInp = x2.add("edittext", [0, 0, 110, 22], S.legLine);
    var x3 = pTx.add("group");
    x3.add("statictext", [0, 0, 80, 20], "Yazı boyutu:");
    var fsDD = x3.add("dropdownlist", undefined, numLabels(FONT_SIZES, " pt"));
    setSel(fsDD, S.fontSize);
    x3.add("statictext", undefined, "Yazı tipi:");
    var fontInp = x3.add("edittext", [0, 0, 150, 22], S.fontName);
    pTx.add("statictext", undefined,
        "Yazı tipi boşsa Helvetica Neue / Arial kullanılır. Ad, PostScript adıdır (ör. MyriadPro-Regular).");

    tabs.selection = tD;

    // ---- Düğmeler ----
    var bg = w.add("group");
    bg.alignment = "right";
    bg.add("button", undefined, "İptal", { name: "cancel" });
    var okBtn = bg.add("button", undefined, "Grafiği çiz", { name: "ok" });

    okBtn.onClick = function () {
        var S2 = {
            data: dataInp.text,
            side: sideDD.selection ? sideDD.selection.index : 0,
            scaleMode: scaleDD.selection ? scaleDD.selection.index : 0,
            tMin: tMinInp.text, tMax: tMaxInp.text, tStep: tStepInp.text,
            pMin: pMinInp.text, pMax: pMaxInp.text, pStep: pStepInp.text,
            sameScale: sameCb.value,
            tTitle: tTitleInp.text, pTitle: pTitleInp.text,
            titleMode: titleDD.selection ? titleDD.selection.index : 0,
            xTitle: xTitleInp.text,
            grid: gridDD.selection ? gridDD.selection.index : 0,
            tickMode: tickDD.selection ? tickDD.selection.index : 0,
            frame: frameCb.value, xTicks: xTickCb.value,
            wMm: wInp.text, hMm: hInp.text, cols: colsInp.text, gapMm: gapInp.text,
            letters: lettersCb.value,
            letterFmt: letterDD.selection ? letterDD.selection.index : 0,
            centerLast: centerCb.value,
            barCmyk: barCmykInp.text, barW: barWInp.text,
            barStroke: barStrokeCb.value, barGrad: barGradCb.value,
            lineCmyk: lineCmykInp.text,
            lineW: lwDD.selection ? lwDD.selection.index : 2,
            dots: dotsCb.value,
            dotSize: dotDD.selection ? dotDD.selection.index : 1,
            smooth: smoothCb.value,
            legend: legendDD.selection ? legendDD.selection.index : 0,
            legBar: legBarInp.text, legLine: legLineInp.text,
            fontSize: fsDD.selection ? fsDD.selection.index : 2,
            fontName: fontInp.text
        };
        var res = collectOptions(S2);
        if (!res) return;
        saveSettings(S2);
        onOk(res);
        w.close(1);
    };
    return w;
}

function setSel(dd, idx) {
    var i = parseInt(idx, 10);
    if (isNaN(i) || i < 0 || i >= dd.items.length) i = 0;
    dd.selection = i;
}

function presetNames(list) {
    var a = [];
    for (var i = 0; i < list.length; i++) a.push(list[i][0]);
    return a;
}

function selectPreset(dd, list, val) {
    var v = normCmyk(val);
    for (var i = 0; i < list.length; i++) {
        if (normCmyk(list[i][1]) === v) { dd.selection = i; return; }
    }
}

function normCmyk(s) {
    var a = parseCmyk(s);
    return a ? a.join(",") : "";
}

function numLabels(list, suffix) {
    var a = [];
    for (var i = 0; i < list.length; i++) a.push(String(list[i]).replace(".", ",") + suffix);
    return a;
}

// ---------------- SEÇENEKLERİ TOPLA ----------------
function collectOptions(S) {
    var panels = parseData(S.data);
    if (panels.length === 0) {
        alert("Veri bulunamadı. Her satıra  Etiket ; Sıcaklık ; Yağış  yaz.");
        return null;
    }

    var o = {};
    o.side = S.side;
    o.scaleMode = S.scaleMode;
    o.sameScale = S.sameScale;
    if (o.scaleMode === 2) {
        o.manT = axisFromText(S.tMin, S.tMax, S.tStep);
        o.manP = axisFromText(S.pMin, S.pMax, S.pStep);
        if (!o.manT || !o.manP) {
            alert("Elle girilen eksen değerleri hatalı.\nEn çok > en az ve aralık > 0 olmalı.");
            return null;
        }
    }
    o.tTitle = trim(S.tTitle);
    o.pTitle = trim(S.pTitle);
    o.titleMode = S.titleMode;
    o.xTitle = trim(S.xTitle);
    o.grid = S.grid;
    o.tickMode = S.tickMode;
    o.frame = S.frame;
    o.xTicks = S.xTicks;

    var wmm = num(S.wMm), hmm = num(S.hMm), gap = num(S.gapMm), cols = num(S.cols);
    if (wmm === null || wmm < 30) { alert("Genişlik en az 30 mm olmalı."); return null; }
    if (hmm === null || hmm < 25) { alert("Yükseklik en az 25 mm olmalı."); return null; }
    o.wPt = wmm * MM;
    o.hPt = hmm * MM;
    o.gapPt = (gap === null || gap < 0 ? 10 : gap) * MM;
    o.cols = (cols === null || cols < 1) ? 2 : Math.round(cols);

    o.letters = S.letters;
    o.letterFmt = S.letterFmt;
    o.centerLast = S.centerLast;

    o.barCmyk = parseCmyk(S.barCmyk);
    if (!o.barCmyk) { alert("Sütun rengi CMYK olarak 4 sayı olmalı (ör. 75,25,0,0)."); return null; }
    var bw = num(S.barW);
    o.barW = (bw === null) ? 0.6 : Math.max(0.1, Math.min(1, bw / 100));
    o.barStroke = S.barStroke;
    o.barGrad = S.barGrad;

    o.lineCmyk = parseCmyk(S.lineCmyk);
    if (!o.lineCmyk) { alert("Çizgi rengi CMYK olarak 4 sayı olmalı (ör. 0,90,85,0)."); return null; }
    o.lineW = LINE_WIDTHS[S.lineW] || 1;
    o.dots = S.dots;
    o.dotD = DOT_SIZES[S.dotSize] || 2.5;
    o.smooth = S.smooth;

    o.legend = S.legend;
    o.legBar = trim(S.legBar) || "Yağış";
    o.legLine = trim(S.legLine) || "Sıcaklık";
    o.fontSize = FONT_SIZES[S.fontSize] || 7;
    o.fontName = trim(S.fontName);

    return { opts: o, panels: panels };
}

function axisFromText(a, b, c) {
    var mn = num(a), mx = num(b), st = num(c);
    if (mn === null || mx === null || st === null) return null;
    if (mx <= mn || st <= 0 || (mx - mn) / st > 60) return null;
    return { min: mn, max: mx, step: st };
}

// ---------------- VERİYİ ÇÖZ ----------------
function parseData(txt) {
    var lines = String(txt).replace(/^﻿/, "").split(/\r\n|\r|\n/);
    var panels = [];
    var cur = null;

    function newPanel(name) {
        cur = { name: name, rows: [], axT: null, axP: null, tSide: null };
        panels.push(cur);
    }

    for (var i = 0; i < lines.length; i++) {
        var s = trim(lines[i]);
        if (s === "" || s.charAt(0) === "#") continue;

        if (s.charAt(0) === "[") {
            newPanel(trim(s.replace(/^\[/, "").replace(/\].*$/, "")));
            continue;
        }
        if (!cur) newPanel("");

        if (s.charAt(0) === "@") {
            var ap = splitRow(s.substr(1));
            var kind = axisKind(ap[0]);
            if (!kind) continue;
            var k = 1, side = null;
            var sd = ap.length > 1 ? sideOf(ap[1]) : null;
            if (sd) { side = sd; k = 2; }
            var ax = axisFromText(ap[k], ap[k + 1], ap[k + 2]);
            if (kind === "t") {
                if (ax) cur.axT = ax;
                if (side) cur.tSide = side;
            } else {
                if (ax) cur.axP = ax;
                if (side) cur.tSide = (side === "sol") ? "sag" : "sol";
            }
            continue;
        }

        var parts = splitRow(s);
        var label = trim(parts[0] || "");
        var t = num(parts[1]);
        var p = num(parts[2]);
        // Başlık satırı (ör. "Ay;Sıcaklık;Yağış") atlanır
        if (t === null && p === null &&
            ((parts[1] && trim(parts[1]) !== "") || (parts[2] && trim(parts[2]) !== ""))) continue;
        cur.rows.push({ label: label, t: t, p: p });
    }

    var out = [];
    for (var j = 0; j < panels.length; j++) if (panels[j].rows.length > 0) out.push(panels[j]);
    return out;
}

function splitRow(s) {
    var parts;
    if (s.indexOf("\t") >= 0) parts = s.split("\t");
    else if (s.indexOf(";") >= 0) parts = s.split(";");
    else parts = s.split(/\s+/);
    for (var i = 0; i < parts.length; i++) parts[i] = trim(parts[i]);
    return parts;
}

function axisKind(s) {
    var k = lowerTr(trim(s || ""));
    if (k === "") return null;
    var c = k.charAt(0);
    if (c === "s" || c === "t") return "t";      // sicaklik, sıcaklık, temp
    if (c === "y" || c === "p") return "p";      // yagis, yağış, precip
    return null;
}

function sideOf(s) {
    var k = lowerTr(trim(s || ""));
    if (k === "sol" || k === "left" || k === "l") return "sol";
    if (k === "sag" || k === "sağ" || k === "right" || k === "r") return "sag";
    return null;
}

function lowerTr(s) {
    return String(s).replace(/I/g, "ı").replace(/İ/g, "i").toLowerCase()
        .replace(/ı/g, "i").replace(/ş/g, "s").replace(/ğ/g, "g")
        .replace(/ç/g, "c").replace(/ö/g, "o").replace(/ü/g, "u");
}

// ---------------- EKSENLER ----------------
function resolveAxes(panels, o) {
    var g = null;
    if (o.sameScale) {
        g = { tLo: 0, tHi: 0, pHi: 0 };
        for (var i = 0; i < panels.length; i++) {
            var r = dataRange(panels[i]);
            if (r.tLo < g.tLo) g.tLo = r.tLo;
            if (r.tHi > g.tHi) g.tHi = r.tHi;
            if (r.pHi > g.pHi) g.pHi = r.pHi;
        }
    }
    for (var j = 0; j < panels.length; j++) {
        var P = panels[j];
        var rng = g || dataRange(P);
        var t = null, p = null;
        if (o.scaleMode === 2) {
            t = copyAx(o.manT); p = copyAx(o.manP);
        } else if (o.scaleMode === 0) {
            t = P.axT ? copyAx(P.axT) : null;
            p = P.axP ? copyAx(P.axP) : null;
        }
        if (!t && !p) {
            var both = autoAxes(rng.tLo, rng.tHi, rng.pHi);
            t = both.t; p = both.p;
        } else if (!t) {
            t = autoAxisDiv(rng.tLo, rng.tHi, divOf(p));
        } else if (!p) {
            p = autoAxisDiv(0, rng.pHi, divOf(t));
        }
        var tSide = (o.scaleMode === 0 && P.tSide) ? P.tSide : (o.side === 0 ? "sol" : "sag");
        t.kind = "t"; p.kind = "p";
        t.side = tSide; p.side = (tSide === "sol") ? "sag" : "sol";
        P.ax = { t: t, p: p };
    }
}

function copyAx(a) { return { min: a.min, max: a.max, step: a.step }; }

function divOf(a) { return Math.max(1, Math.round((a.max - a.min) / a.step)); }

function dataRange(P) {
    var tLo = 0, tHi = 0, pHi = 0;
    for (var i = 0; i < P.rows.length; i++) {
        var r = P.rows[i];
        if (r.t !== null) { if (r.t < tLo) tLo = r.t; if (r.t > tHi) tHi = r.t; }
        if (r.p !== null && r.p > pHi) pHi = r.p;
    }
    if (tHi - tLo < 1e-9) tHi = tLo + 1;
    if (pHi < 1e-9) pHi = 1;
    return { tLo: tLo, tHi: tHi, pHi: pHi };
}

function niceStep(raw) {
    if (!(raw > 0)) return 1;
    var p = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10));
    var m = raw / p;
    var c = [1, 2, 2.5, 5, 10];
    for (var i = 0; i < c.length; i++) if (m <= c[i] + 1e-9) return c[i] * p;
    return 10 * p;
}

function autoAxisDiv(lo, hi, d) {
    var st = niceStep((hi - lo) / d);
    var mn = Math.floor(lo / st + 1e-9) * st;
    var guard = 0;
    while (mn + d * st < hi - 1e-9 && guard < 20) {
        st = niceStep(st * 1.0001);
        mn = Math.floor(lo / st + 1e-9) * st;
        guard++;
    }
    return { min: mn, max: mn + d * st, step: st };
}

function autoAxes(tLo, tHi, pHi) {
    var best = null;
    for (var d = 3; d <= 8; d++) {
        var t = autoAxisDiv(tLo, tHi, d);
        var p = autoAxisDiv(0, pHi, d);
        var score = (t.max - t.min) / (tHi - tLo) + (p.max - p.min) / pHi + Math.abs(d - 5) * 0.03;
        if (!best || score < best.score) best = { score: score, t: t, p: p };
    }
    return best;
}

function tickValues(ax) {
    var n = divOf(ax);
    var a = [];
    for (var i = 0; i <= n; i++) a.push(ax.min + i * ax.step);
    return a;
}

// ---------------- ÇİZİM ----------------
function drawAll(o, panels) {
    if (app.documents.length === 0) app.documents.add(DocumentColorSpace.CMYK);
    var doc = app.activeDocument;
    var layer = doc.activeLayer;
    if (layer.locked || !layer.visible) {
        alert("Etkin katman kilitli ya da gizli. Başka bir katman seç ya da kilidi aç.");
        return;
    }

    resolveAxes(panels, o);

    var C = {
        black: makeColor([0, 0, 0, 100]),
        grid: makeColor([0, 0, 0, 35]),
        bar: makeColor(o.barCmyk),
        line: makeColor(o.lineCmyk)
    };
    if (o.barGrad) C.barFill = makeBarGradient(doc, o.barCmyk);

    var F = { r: null };
    if (o.fontName !== "") {
        F.r = pickFont([o.fontName]);
        if (!F.r) alert("\"" + o.fontName + "\" yazı tipi bulunamadı; varsayılan kullanılacak.");
    }
    if (!F.r) F.r = pickFont(["HelveticaNeue", "HelveticaNeue-Roman", "HelveticaNeueLTStd-Roman",
                              "Helvetica", "ArialMT", "MyriadPro-Regular"]);

    var ctx = { doc: doc, o: o, C: C, F: F, fs: o.fontSize };

    var n = panels.length;
    var cols = Math.max(1, Math.min(o.cols, n));
    var rows = Math.ceil(n / cols);
    var single = (n === 1);
    var topLegend = (o.legend === 2 && !single);
    var legRowH = topLegend ? (o.fontSize * 1.2 + 8) : 0;

    var totalW = cols * o.wPt + (cols - 1) * o.gapPt;
    var totalH = legRowH + rows * o.hPt + (rows - 1) * o.gapPt;

    var ab = doc.artboards[doc.artboards.getActiveArtboardIndex()].artboardRect;
    var left = (ab[0] + ab[2]) / 2 - totalW / 2;
    var top = (ab[1] + ab[3]) / 2 + totalH / 2;

    var root = layer.groupItems.add();
    root.name = single ? ("İklim Grafiği" + (panels[0].name ? " " + panels[0].name : "")) : "İklim Grafikleri";

    for (var k = 0; k < n; k++) {
        var r = Math.floor(k / cols), c = k % cols;
        var inRow = Math.min(cols, n - r * cols);
        var off = (o.centerLast && inRow < cols) ? (cols - inRow) * (o.wPt + o.gapPt) / 2 : 0;
        var L = left + off + c * (o.wPt + o.gapPt);
        var T = top - legRowH - r * (o.hPt + o.gapPt);
        var ctr = single ? root : root.groupItems.add();
        if (!single) ctr.name = "İklim Grafiği" + (panels[k].name ? " " + panels[k].name : "");
        drawPanel(ctx, ctr, panels[k], L, T, single);
    }

    if (topLegend) {
        var lg = root.groupItems.add();
        lg.name = "Lejant";
        drawLegendCentered(ctx, lg, left + totalW / 2, top - legRowH / 2 + o.fontSize * 0.1);
    }

    app.redraw();
}

function drawPanel(ctx, g, P, L, T, single) {
    var o = ctx.o, C = ctx.C, F = ctx.F, fs = ctx.fs;
    var W = o.wPt, H = o.hPt;
    var capH = fs * 0.7, asc = fs * 0.75, desc = fs * 0.22;
    var tickLen = Math.max(2.5, fs * 0.45);
    var labGap = Math.max(2, fs * 0.35);

    var tAx = P.ax.t, pAx = P.ax.p;
    var leftAx = (tAx.side === "sol") ? tAx : pAx;
    var rightAx = (leftAx === tAx) ? pAx : tAx;
    var leftVals = tickValues(leftAx), rightVals = tickValues(rightAx);

    var tOut = (o.tickMode === 0 || o.tickMode === 2) ? tickLen : 0;
    var tIn = (o.tickMode === 1 || o.tickMode === 2) ? tickLen : 0;
    if (o.tickMode === 3) { tOut = 0; tIn = 0; }

    var leftStr = [], rightStr = [], wl = 0, wr = 0, i;
    for (i = 0; i < leftVals.length; i++) {
        leftStr.push(fmtNum(leftVals[i]));
        wl = Math.max(wl, measureText(ctx, leftStr[i], fs));
    }
    for (i = 0; i < rightVals.length; i++) {
        rightStr.push(fmtNum(rightVals[i]));
        wr = Math.max(wr, measureText(ctx, rightStr[i], fs));
    }

    var titleOf = function (ax) { return ax.kind === "t" ? o.tTitle : o.pTitle; };
    var lTitle = titleOf(leftAx), rTitle = titleOf(rightAx);
    var vTitle = (o.titleMode === 1), hTitle = (o.titleMode === 0);
    var vtW = fs * 1.2 + 2;

    // --- Dikey yerleşim (yukarıdan aşağı) ---
    var y = T;
    var letterBase = null, legendY = null, titleBase = null;
    if (o.letters && P.name !== "") {
        letterBase = y - (fs + 3) * 0.75;
        y -= (fs + 3) * 0.75 + desc + 4;
    }
    var perLegend = (o.legend === 1 || o.legend === 3 || (o.legend === 2 && single));
    if (perLegend) {
        legendY = y - fs * 0.55;
        y -= fs * 1.1 + 5;
    }
    if (hTitle && (lTitle !== "" || rTitle !== "")) {
        titleBase = y - asc;
        y -= asc + desc + 3;
    }
    var pT = y - capH / 2 - 0.5;

    var yb = T - H;
    var xTitleBase = null;
    if (o.xTitle !== "") {
        xTitleBase = yb + desc;
        yb += desc + asc + 3;
    }
    var xTickOut = (o.xTicks && o.tickMode !== 1) ? tickLen : 0;
    var xLabBase = yb + desc + 0.5;
    var pB = xLabBase + capH + labGap + xTickOut;

    var pL = L + wl + labGap + tOut + (vTitle && lTitle !== "" ? vtW : 0);
    var pR = L + W - wr - labGap - tOut - (vTitle && rTitle !== "" ? vtW : 0);

    if (pT - pB < 15 || pR - pL < 20) throw new Error("Grafik ölçüsü yazılar için çok küçük. Genişlik/yüksekliği artır ya da yazıyı küçült.");

    function yOf(ax, v) { return pB + (v - ax.min) / (ax.max - ax.min) * (pT - pB); }

    var n = P.rows.length;
    var slot = (pR - pL) / n;
    function cx(k) { return pL + slot * (k + 0.5); }

    var axW = 0.5;

    // --- Kılavuz çizgileri ---
    if (o.grid > 0) {
        for (i = 1; i < leftVals.length; i++) {
            if (o.frame && i === leftVals.length - 1) continue;
            var gy = yOf(leftAx, leftVals[i]);
            var gl = line(g, [[pL, gy], [pR, gy]], C.grid, 0.3);
            if (o.grid === 2) gl.strokeDashes = [2, 2];
        }
    }

    // --- Sütunlar (yağış) ---
    var baseVal = (pAx.min <= 0 && pAx.max >= 0) ? 0 : pAx.min;
    var by = yOf(pAx, baseVal);
    var bw = slot * o.barW;
    for (i = 0; i < n; i++) {
        var pv = P.rows[i].p;
        if (pv === null) continue;
        var ty = yOf(pAx, pv);
        var h = ty - by;
        if (h <= 0.05) continue;
        var rc = g.pathItems.rectangle(ty, cx(i) - bw / 2, bw, h);
        rc.filled = true;
        rc.fillColor = C.barFill ? C.barFill : C.bar;
        if (o.barStroke) {
            rc.stroked = true; rc.strokeColor = C.black; rc.strokeWidth = 0.3;
        } else {
            rc.stroked = false;
        }
        rc.name = "Yağış " + P.rows[i].label;
    }

    // --- Eksenler ---
    line(g, [[pL, pB], [pL, pT]], C.black, axW);
    line(g, [[pR, pB], [pR, pT]], C.black, axW);
    line(g, [[pL, pB], [pR, pB]], C.black, axW);
    if (o.frame) line(g, [[pL, pT], [pR, pT]], C.black, axW);

    if (tOut > 0 || tIn > 0) {
        for (i = 0; i < leftVals.length; i++) {
            var ly = yOf(leftAx, leftVals[i]);
            line(g, [[pL - tOut, ly], [pL + tIn, ly]], C.black, axW);
        }
        for (i = 0; i < rightVals.length; i++) {
            var ry = yOf(rightAx, rightVals[i]);
            line(g, [[pR - tIn, ry], [pR + tOut, ry]], C.black, axW);
        }
    }
    if (o.xTicks) {
        for (i = 0; i < n; i++) {
            line(g, [[cx(i), pB - xTickOut], [cx(i), pB + (o.tickMode === 1 || o.tickMode === 2 ? tickLen : 0)]], C.black, axW);
        }
    }

    // --- Sıcaklık çizgisi ---
    var run = [], runs = [];
    for (i = 0; i < n; i++) {
        var tv = P.rows[i].t;
        if (tv === null) { if (run.length) runs.push(run); run = []; continue; }
        run.push([cx(i), yOf(tAx, tv)]);
    }
    if (run.length) runs.push(run);
    for (var ri = 0; ri < runs.length; ri++) {
        var pts = runs[ri];
        if (pts.length > 1) {
            var pl = g.pathItems.add();
            pl.setEntirePath(pts);
            pl.filled = false; pl.stroked = true;
            pl.strokeColor = C.line; pl.strokeWidth = o.lineW;
            pl.strokeJoin = StrokeJoin.ROUNDENDJOIN;
            pl.strokeCap = StrokeCap.ROUNDENDCAP;
            pl.name = "Sıcaklık";
            if (o.smooth && pts.length > 2) smoothPath(pl, pts);
        }
        if (o.dots || pts.length === 1) {
            for (var di = 0; di < pts.length; di++) dot(g, pts[di][0], pts[di][1], o.dotD, C.line);
        }
    }

    // --- Yazılar ---
    for (i = 0; i < leftVals.length; i++) {
        putText(ctx, g, leftStr[i], pL - tOut - labGap, yOf(leftAx, leftVals[i]) - capH / 2, "R", fs);
    }
    for (i = 0; i < rightVals.length; i++) {
        putText(ctx, g, rightStr[i], pR + tOut + labGap, yOf(rightAx, rightVals[i]) - capH / 2, "L", fs);
    }
    for (i = 0; i < n; i++) {
        if (P.rows[i].label !== "") putText(ctx, g, P.rows[i].label, cx(i), xLabBase, "C", fs);
    }
    if (xTitleBase !== null) putText(ctx, g, o.xTitle, (pL + pR) / 2, xTitleBase, "C", fs);

    if (titleBase !== null) {
        if (lTitle !== "") putText(ctx, g, lTitle, L, titleBase, "L", fs);
        if (rTitle !== "") putText(ctx, g, rTitle, L + W, titleBase, "R", fs);
    }
    if (vTitle) {
        if (lTitle !== "") putRotated(ctx, g, lTitle, L + vtW / 2, (pT + pB) / 2, fs);
        if (rTitle !== "") putRotated(ctx, g, rTitle, L + W - vtW / 2, (pT + pB) / 2, fs);
    }

    if (letterBase !== null) {
        var lf = LETTER_FORMATS[o.letterFmt] || "A)";
        putText(ctx, g, lf.replace("A", P.name), L, letterBase, "L", fs + 3);
    }

    if (legendY !== null) {
        if (o.legend === 3) {
            var barLeft = (pAx.side === "sol");
            drawLegendItem(ctx, g, "bar", legendY, barLeft ? "L" : "R", barLeft ? L : L + W);
            drawLegendItem(ctx, g, "line", legendY, barLeft ? "R" : "L", barLeft ? L + W : L);
        } else {
            drawLegendCentered(ctx, g, (pL + pR) / 2, legendY);
        }
    }
}

// ---------------- LEJANT ----------------
function legendItemWidth(ctx, kind) {
    var fs = ctx.fs;
    var sw = (kind === "bar") ? fs * 1.1 : fs * 2.4;
    var txt = (kind === "bar") ? ctx.o.legBar : ctx.o.legLine;
    return sw + fs * 0.45 + measureText(ctx, txt, fs);
}

function drawLegendCentered(ctx, g, cxm, cy) {
    var gap = ctx.fs * 2;
    var wb = legendItemWidth(ctx, "bar"), wl = legendItemWidth(ctx, "line");
    var x = cxm - (wb + gap + wl) / 2;
    drawLegendItem(ctx, g, "bar", cy, "L", x);
    drawLegendItem(ctx, g, "line", cy, "L", x + wb + gap);
}

// align "L": öğe x'ten sağa; "R": öğe x'te biter
function drawLegendItem(ctx, g, kind, cy, align, x) {
    var o = ctx.o, C = ctx.C, fs = ctx.fs;
    var wTot = legendItemWidth(ctx, kind);
    var x0 = (align === "R") ? x - wTot : x;
    var capH = fs * 0.7;
    var txt;
    if (kind === "bar") {
        var s = fs * 1.1;
        var rc = g.pathItems.rectangle(cy + s / 2, x0, s, s);
        rc.filled = true; rc.fillColor = C.barFill ? C.barFill : C.bar;
        if (o.barStroke) { rc.stroked = true; rc.strokeColor = C.black; rc.strokeWidth = 0.3; }
        else rc.stroked = false;
        txt = o.legBar;
        putText(ctx, g, txt, x0 + s + fs * 0.45, cy - capH / 2, "L", fs);
    } else {
        var len = fs * 2.4;
        var ln = line(g, [[x0, cy], [x0 + len, cy]], C.line, o.lineW);
        ln.strokeCap = StrokeCap.ROUNDENDCAP;
        if (o.dots) dot(g, x0 + len / 2, cy, o.dotD, C.line);
        txt = o.legLine;
        putText(ctx, g, txt, x0 + len + fs * 0.45, cy - capH / 2, "L", fs);
    }
}

// ---------------- ÇİZİM YARDIMCILARI ----------------
function line(g, pts, color, wdt) {
    var p = g.pathItems.add();
    p.setEntirePath(pts);
    p.filled = false;
    p.stroked = true;
    p.strokeColor = color;
    p.strokeWidth = wdt;
    return p;
}

function dot(g, x, y, d, color) {
    var e = g.pathItems.ellipse(y + d / 2, x - d / 2, d, d);
    e.filled = true;
    e.fillColor = color;
    e.stroked = false;
    return e;
}

function smoothPath(path, pts) {
    var pp = path.pathPoints;
    var n = pts.length;
    for (var i = 0; i < n; i++) {
        var a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
        var dx = (b[0] - a[0]) / 6, dy = (b[1] - a[1]) / 6;
        pp[i].leftDirection = [pts[i][0] - dx, pts[i][1] - dy];
        pp[i].rightDirection = [pts[i][0] + dx, pts[i][1] + dy];
        pp[i].pointType = PointType.SMOOTH;
    }
}

function makeBarGradient(doc, cmyk) {
    var dark = makeColor([Math.min(100, cmyk[0] + 10), Math.min(100, cmyk[1] + 10),
                          Math.min(100, cmyk[2] + 10), Math.min(100, cmyk[3] + 25)]);
    var light = makeColor([cmyk[0] * 0.12, cmyk[1] * 0.12, cmyk[2] * 0.12, cmyk[3] * 0.12]);
    var base = makeColor(cmyk);
    try {
        var gr = doc.gradients.add();
        try { gr.name = "İklim sütun degrade " + cmyk.join("-"); } catch (e1) {}
        gr.type = GradientType.LINEAR;
        var st = gr.gradientStops;
        st[0].rampPoint = 0; st[0].color = dark;
        st[1].rampPoint = 100; st[1].color = base;
        var m = st.add();
        m.rampPoint = 55; m.midPoint = 50; m.color = light;
        var gc = new GradientColor();
        gc.gradient = gr;
        return gc;
    } catch (e) {
        return null;   // degrade yapılamazsa düz renk kullanılır
    }
}

// Metni yerleştir: x yatay çapa (L/C/R), by taban çizgisi
function putText(ctx, g, str, x, by, align, size) {
    var tf = g.textFrames.add();
    tf.contents = str;
    styleText(ctx, tf, size);
    var gb = tf.geometricBounds;           // [sol, üst, sağ, alt]
    var dx = (align === "L") ? x - gb[0] : (align === "R") ? x - gb[2] : x - (gb[0] + gb[2]) / 2;
    var baseY = null;
    try { baseY = tf.anchor[1]; } catch (e) {}
    if (baseY === null || isNaN(baseY)) baseY = gb[3] + (gb[1] - gb[3]) * 0.24;
    tf.translate(dx, by - baseY);
    return tf;
}

function putRotated(ctx, g, str, cxp, cyp, size) {
    var tf = g.textFrames.add();
    tf.contents = str;
    styleText(ctx, tf, size);
    tf.rotate(90);
    var gb = tf.geometricBounds;
    tf.translate(cxp - (gb[0] + gb[2]) / 2, cyp - (gb[1] + gb[3]) / 2);
    return tf;
}

function styleText(ctx, tf, size) {
    var ca = tf.textRange.characterAttributes;
    ca.size = size;
    ca.fillColor = ctx.C.black;
    ca.strokeWeight = 0;
    if (ctx.F.r) { try { ca.textFont = ctx.F.r; } catch (e) {} }
    tf.textRange.paragraphAttributes.justification = Justification.LEFT;
}

function measureText(ctx, str, size) {
    if (str === "") return 0;
    var tf = ctx.doc.textFrames.add();
    tf.contents = str;
    styleText(ctx, tf, size);
    var gb = tf.geometricBounds;
    var w = gb[2] - gb[0];
    tf.remove();
    return w;
}

function pickFont(names) {
    for (var i = 0; i < names.length; i++) {
        try { return app.textFonts.getByName(names[i]); } catch (e) {}
    }
    return null;
}

function makeColor(a) {
    var c = new CMYKColor();
    c.cyan = a[0]; c.magenta = a[1]; c.yellow = a[2]; c.black = a[3];
    return c;
}

// ---------------- GENEL YARDIMCILAR ----------------
function parseCmyk(s) {
    var parts = trim(String(s)).split(/[,;\s\/]+/);
    if (parts.length !== 4) return null;
    var a = [];
    for (var i = 0; i < 4; i++) {
        var v = parseFloat(parts[i]);
        if (isNaN(v)) return null;
        a.push(Math.max(0, Math.min(100, v)));
    }
    return a;
}

function num(s) {
    if (s === undefined || s === null) return null;
    var t = trim(String(s)).replace(/\s/g, "").replace(/−|–/g, "-").replace(",", ".");
    if (t === "") return null;
    var v = parseFloat(t);
    return isNaN(v) ? null : v;
}

function fmtNum(v) {
    var r = Math.round(v * 100) / 100;
    var s = (Math.abs(r - Math.round(r)) < 1e-9) ? String(Math.round(r)) : String(r);
    if (s === "-0") s = "0";
    return s.replace(".", ",");
}

function trim(s) {
    return String(s).replace(/^\s+/, "").replace(/\s+$/, "");
}

function readTextFile(f) {
    try {
        f.encoding = "UTF-8";
        if (!f.open("r")) return null;
        var t = f.read();
        f.close();
        return String(t).replace(/^﻿/, "");
    } catch (e) {
        return null;
    }
}

// ---------------- AYARLARI HATIRLA ----------------
function settingsFile() {
    return new File(Folder.userData.absoluteURI + "/" + SETTINGS_FILE);
}

function escVal(s) {
    return String(s).replace(/\\/g, "\\\\").replace(/\r\n|\r|\n/g, "\\n");
}

function unescVal(s) {
    var out = "";
    for (var i = 0; i < s.length; i++) {
        var ch = s.charAt(i);
        if (ch === "\\" && i + 1 < s.length) {
            var nx = s.charAt(i + 1);
            out += (nx === "n") ? "\n" : nx;
            i++;
        } else {
            out += ch;
        }
    }
    return out;
}

function saveSettings(S) {
    try {
        var f = settingsFile();
        f.encoding = "UTF-8";
        if (!f.open("w")) return;
        for (var k in S) {
            if (S.hasOwnProperty(k)) f.writeln(k + "=" + escVal(S[k]));
        }
        f.close();
    } catch (e) {}
}

function loadSettings() {
    var S = {}, k;
    for (k in DEFAULTS) if (DEFAULTS.hasOwnProperty(k)) S[k] = DEFAULTS[k];
    try {
        var f = settingsFile();
        if (!f.exists) return S;
        f.encoding = "UTF-8";
        if (!f.open("r")) return S;
        while (!f.eof) {
            var ln = f.readln();
            var p = ln.indexOf("=");
            if (p < 1) continue;
            k = ln.substr(0, p);
            if (!DEFAULTS.hasOwnProperty(k)) continue;
            var v = unescVal(ln.substr(p + 1));
            var d = DEFAULTS[k];
            if (typeof d === "boolean") S[k] = (v === "true");
            else if (typeof d === "number") { var nv = parseInt(v, 10); if (!isNaN(nv)) S[k] = nv; }
            else S[k] = v;
        }
        f.close();
    } catch (e) {}
    return S;
}
