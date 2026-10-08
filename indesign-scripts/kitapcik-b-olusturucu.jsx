// =============================================================
//  KİTAPÇIK B OLUŞTURUCU  v4.18
//  (v4.15: özel havuzlar + ikinci şans + kendini teşhis eden bekçi
//   + bağlı-görsel sertleştirme + ortaokul kapısına belge-içi yedek.
//   v4.16: sade panel. v4.17: kompakt seçenekler geri + doğal havuz yazımı
//   (\u201Csayfa 7-8 soru 25,31\u201D, \u201Cve\u201D bağlacı desteklenir).
//   Lise/AYT yolu davranışsal olarak birebir korunur.
//   v4.18: hata düzeltmeleri — bölüm işaretinde "KİMYA"→"KİMYB" hatası,
//   boş sayfanın komşu sayfa sorularını sahiplenmesi, kaçak/yinelenen
//   sorulu testte blok takası numarası, karşılıklı sayfada blok takası
//   yatay kayması, harfi okunamayan soruda B anahtarında A harfi kalması.)
//  Limit Yayınları — A kitapçığından otomatik B kitapçığı üretimi
//  (Lise AYT/TYT + Ortaokul 5-8. sınıf denemeleri)
// -------------------------------------------------------------
//  v4.2 — SAHA DÖNÜŞÜ DÜZELTMELERİ
//  • HAYALET ÇERÇEVE FİLTRESİ: İçeriği boş olan ya da bir soru
//    çerçevesinin üzerine binen "dekor" metin çerçeveleri artık
//    yerleşim zincirine girmez (üst üste binme / hiza kayması
//    yaratan gizli kapları etkisizleştirir).
//  • TAM SAYFA TAKASI: Tek başına sayfa kaplayan dev soru gibi,
//    boy eşi bulunamayan sorular için iki sayfanın TÜM soru
//    içeriği blok hâlinde takas edilir (yalnız tek-bölgeli
//    branş testlerinde; iki yönde de sığma denetlenir, test
//    sonu notları yeni son sorunun altına taşınır, bölüm
//    baştan numaralanır). Dev soru artık yerinde kalmaz.
//  • BİNDİRME DENETİMİ + GERİ ALMA: Numaralar yazılmadan önce
//    her değişen sayfada çerçevelerin GERÇEK konumları okunur;
//    üst üste binme ya da taşma saptanırsa o sayfa (sayfa
//    takasıysa iki sayfa birden) A düzenine geri alınır ve
//    KRİTİK olarak raporlanır. Bozuk sayfa asla teslim edilmez.
//
//  v4 çekirdeği: bant motoru (tam genişlik + sütun), kapak
//  sayfaları tamamen atlanır, karşılıklı sayfa desteği, boşluk
//  sıkıştırma merdiveni, ders sınırları + yönergeler korunur,
//  numara konuma sabittir, Bölüm İşareti ve master düz metin
//  "A A A A A" bandı A→B, cevap anahtarı güncellenir, CSV rapor.
//
//  Kurulum: Scripts panelinde User klasörüne kopyalayın, çift tık.
//  ExtendScript ES3 uyumludur.
// =============================================================

#target "indesign"

(function () {

    function trimS(s) { return String(s).replace(/^\s+|\s+$/g, ""); }

    function makeRng(seed) {
        var a = seed >>> 0;
        return function () {
            a = (a + 0x6D2B79F5) >>> 0;
            var t = a;
            t = (((t ^ (t >>> 15)) * ((t | 1) >>> 0))) >>> 0;
            t = (t + (((t ^ (t >>> 7)) * ((t | 61) >>> 0)) >>> 0)) >>> 0;
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
    }

    function allPerms(n) {
        var res = [], arr = [], i;
        for (i = 0; i < n; i++) { arr.push(i); }
        function heap(k) {
            if (k === 1) { res.push(arr.slice(0)); return; }
            for (var j = 0; j < k; j++) {
                heap(k - 1);
                var t, idx = (k % 2 === 0) ? j : 0;
                t = arr[idx]; arr[idx] = arr[k - 1]; arr[k - 1] = t;
            }
        }
        heap(n);
        return res;
    }

    // ---------------------------------------------------------
    // 1) ARAYÜZ
    // ---------------------------------------------------------
    var dlg = new Window("dialog", "Kitapçık B Oluşturucu v4.18 — Limit Yayınları");
    dlg.orientation = "column";
    dlg.alignChildren = "fill";
    dlg.margins = 16;
    dlg.spacing = 10;

    var rowFile = dlg.add("group");
    rowFile.add("statictext", undefined, "A Kitapçığı (.indd):");
    var txtFile = rowFile.add("edittext", undefined, "");
    txtFile.characters = 36;
    var btnSec = rowFile.add("button", undefined, "Seç...");
    var btnFinder = null;
    if ($.os.indexOf("Mac") !== -1) {
        btnFinder = rowFile.add("button", undefined, "Finder'daki seçimi al");
    }
    var chkActive = dlg.add("checkbox", undefined, "Dosya seçme, açık olan aktif belgeyi kullan");
    if (app.documents.length > 0) {
        chkActive.value = true;
        try { txtFile.text = app.activeDocument.fullName.fsName; } catch (e0) {}
    }
    btnSec.onClick = function () {
        var filt = ($.os.indexOf("Mac") !== -1)
            ? function (ff) { return (ff instanceof Folder) || /\.indd$/i.test(ff.name); }
            : "InDesign Belgesi:*.indd";
        var f = File.openDialog("A kitapçığı .indd dosyasını seçin", filt);
        if (f) { txtFile.text = f.fsName; chkActive.value = false; }
    };
    if (btnFinder !== null) {
        btnFinder.onClick = function () {
            var asrc = 'tell application "Finder"\n' +
                       'set sel to selection\n' +
                       'set out to ""\n' +
                       'repeat with f in sel\n' +
                       'set out to out & (POSIX path of (f as alias)) & linefeed\n' +
                       'end repeat\n' +
                       'return out\n' +
                       'end tell';
            var res = "";
            try { res = String(app.doScript(asrc, ScriptLanguage.APPLESCRIPT_LANGUAGE)); }
            catch (eAS) {
                alert("Finder'a erişilemedi. macOS izin istediyse onaylayın (Sistem Ayarları > Gizlilik > Otomasyon > InDesign → Finder) ve tekrar deneyin.");
                return;
            }
            var lines = res.split("\n");
            var picked = "";
            for (var li = 0; li < lines.length; li++) {
                var pth = trimS(lines[li]);
                if (pth !== "" && /\.indd$/i.test(pth)) { picked = pth; break; }
                if (picked === "" && pth !== "") { picked = pth; }
            }
            if (picked === "") {
                alert("Finder'da seçili dosya bulunamadı.\nÖnce Finder'da A kitapçığı .indd dosyasını tıklayın, sonra bu düğmeye basın.");
                return;
            }
            if (!/\.indd$/i.test(picked)) {
                alert("Seçili dosya .indd değil:\n" + picked + "\nLütfen InDesign belgesini seçin.");
                return;
            }
            txtFile.text = picked;
            chkActive.value = false;
        };
    }

    var rowMode = dlg.add("group");
    rowMode.add("statictext", undefined, "Mod:");
    var rbCross = rowMode.add("radiobutton", undefined, "Çapraz (önerilen)");
    var rbCol   = rowMode.add("radiobutton", undefined, "Sütun içi ikili");
    var rbRnd   = rowMode.add("radiobutton", undefined, "Rastgele, seed:");
    var txtSeed = rowMode.add("edittext", undefined, "2526");
    txtSeed.characters = 6;
    rbCross.value = true;
    rbCross.onClick = function () { rbCol.value = false; rbRnd.value = false; };
    rbCol.onClick   = function () { rbCross.value = false; rbRnd.value = false; };
    rbRnd.onClick   = function () { rbCross.value = false; rbCol.value = false; };

    var pnlOpt = dlg.add("panel", undefined, "Seçenekler");
    pnlOpt.orientation = "row";
    pnlOpt.alignChildren = "top";
    pnlOpt.margins = 10;
    var optCol1 = pnlOpt.add("group"); optCol1.orientation = "column"; optCol1.alignChildren = "left";
    var optCol2 = pnlOpt.add("group"); optCol2.orientation = "column"; optCol2.alignChildren = "left";
    var chkXPage    = optCol1.add("checkbox", undefined, "Sayfalar arası takas");
    var chkBundle   = optCol1.add("checkbox", undefined, "Tam sayfa blok takası");
    var chkCompress = optCol1.add("checkbox", undefined, "Boşluk sıkıştırma");
    var chkLinked   = optCol1.add("checkbox", undefined, "Grup içi takas (parçaya göre)");
    var chkMarker   = optCol2.add("checkbox", undefined, "Kitapçık harfi A→B");
    var chkKey      = optCol2.add("checkbox", undefined, "Cevap anahtarı güncelle");
    var chkCsv      = optCol2.add("checkbox", undefined, "CSV rapor");
    chkXPage.value = true; chkBundle.value = true; chkCompress.value = true; chkLinked.value = true;
    chkMarker.value = true; chkKey.value = true; chkCsv.value = true;

    var pnlPool = dlg.add("panel", undefined, "Özel havuzlar (boş bırak = normal karışım)");
    pnlPool.orientation = "column";
    pnlPool.alignChildren = "fill";
    pnlPool.margins = 12;
    var txtPools = pnlPool.add("edittext", undefined, "", { multiline: true, scrolling: true });
    txtPools.preferredSize.height = 46;
    var hintPool1 = pnlPool.add("statictext", undefined,
        "Örn:    sayfa 7 ve 8 soru 5-10");
    var hintPool2 = pnlPool.add("statictext", undefined,
        "           sayfa 35 ve 40 soru 14-20");
    var hintPool3 = pnlPool.add("statictext", undefined,
        "veya:  sayfa 7 ve 8 soru 5-10 ; sayfa 35 ve 40 soru 14-20");
    try {
        var hpArr = [hintPool1, hintPool2, hintPool3];
        for (var hp = 0; hp < hpArr.length; hp++) {
            hpArr[hp].graphics.foregroundColor = hpArr[hp].graphics.newPen(hpArr[hp].graphics.PenType.SOLID_COLOR, [0.45, 0.45, 0.45], 1);
        }
    } catch (eHint2) {}

    var rowBtn = dlg.add("group");
    rowBtn.alignment = "right";
    rowBtn.add("button", undefined, "Vazgeç", { name: "cancel" });
    rowBtn.add("button", undefined, "Çalıştır", { name: "ok" });

    if (dlg.show() !== 1) { return; }

    // ---------------------------------------------------------
    // 2) BELGE + B KOPYASI
    // ---------------------------------------------------------
    var LOG = [];
    function log(s) { LOG.push(s); }

    var srcDoc = null;
    try {
        if (chkActive.value && app.documents.length > 0) {
            srcDoc = app.activeDocument;
            if (srcDoc.modified) {
                if (!confirm("Aktif belgede kaydedilmemiş değişiklikler var.\nB kopyası ekrandaki hâlden üretilecek. Devam edilsin mi?")) { return; }
            }
        } else {
            var p = trimS(txtFile.text);
            if (p === "") { alert("Lütfen bir .indd dosyası seçin."); return; }
            var f = new File(p);
            if (!f.exists) { alert("Dosya bulunamadı:\n" + p); return; }
            srcDoc = app.open(f, true);
        }
    } catch (eOpen) { alert("Belge açılamadı: " + eOpen.message); return; }
    if (!srcDoc.saved) { alert("Belge daha önce hiç kaydedilmemiş. Önce A belgesini kaydedin."); return; }

    // Zaten B'ye çevrilmiş bir belgeyi yeniden işlemek zinciri bozar — uyar.
    try {
        var _hasA = false, _hasB = false;
        for (var _s = 0; _s < srcDoc.sections.length; _s++) {
            var _mk = String(srcDoc.sections[_s].marker);
            if (/(^|[^0-9A-Za-zÇĞİÖŞÜçğıöşü])A([^0-9A-Za-zÇĞİÖŞÜçğıöşü]|$)/.test(_mk)) { _hasA = true; }
            if (/(^|[^0-9A-Za-zÇĞİÖŞÜçğıöşü])B([^0-9A-Za-zÇĞİÖŞÜçğıöşü]|$)/.test(_mk)) { _hasB = true; }
        }
        var _nm = decodeURI(srcDoc.fullName.name);
        var _nmB = /[-_\s]B(?=[.\-_\s]|$)/.test(_nm);
        if ((_hasB && !_hasA) || _nmB) {
            if (!confirm("DİKKAT: Bu belge daha önce B'ye çevrilmiş görünüyor" +
                         (_nmB ? " (dosya adında B var)" : " (üst bant B)") +
                         ".\nB üzerinden tekrar üretmek soruları bozar.\n\nYine de devam edilsin mi?")) { return; }
        }
    } catch (eBG) {}

    function makeBName(base) {
        var pats = [/-A(?![0-9A-Za-zÇĞİÖŞÜçğıöşü])/, /_A(?![0-9A-Za-zÇĞİÖŞÜçğıöşü])/, /(^|\s)A(?![0-9A-Za-zÇĞİÖŞÜçğıöşü])/];
        for (var i = 0; i < pats.length; i++) {
            if (pats[i].test(base)) {
                if (i === 2) { return base.replace(pats[i], "$1B"); }
                return base.replace(pats[i], (i === 0 ? "-B" : "_B"));
            }
        }
        return base + "_B";
    }

    var srcFile = srcDoc.fullName;
    var folder = srcFile.parent;
    var baseName = decodeURI(srcFile.name).replace(/\.indd$/i, "");
    var bBase = makeBName(baseName);

    // v4.12 ORTAOKUL KORUMA KATMANI:
    // Yalnız 5-8. sınıf dosyalarında ek geometri ön-denetimi devreye girer.
    // 9-11, TYT ve AYT akışı aşağıdaki koşullar false olduğu için v4.11 ile aynıdır.
    var middleSchoolName = baseName.replace(/[_\-]+/g, " ");
    var middleSchoolMatch = /(^|[^0-9])([5-8])\s*\.?\s*SINIF\b/i.exec(middleSchoolName);
    var isMiddleSchool = (middleSchoolMatch !== null);
    var middleSchoolGrade = isMiddleSchool ? parseInt(middleSchoolMatch[2], 10) : 0;
    var MIDDLE_SCHOOL_GAP_CAP = 48; // yalnız 5-8: büyük dekoratif dikey boşlukları güvenli üst sınırda tutar
    var bFile = new File(folder.fsName + "/" + bBase + ".indd");
    if (bFile.exists && !confirm("\u201C" + bBase + ".indd\u201D zaten var. Üzerine yazılsın mı?")) { return; }

    var doc = srcDoc;
    try { doc.save(bFile); }
    catch (eSave) { alert("B kopyası kaydedilemedi: " + eSave.message); return; }
    log("B kopyası: " + bBase + ".indd");
    if (isMiddleSchool) {
        log("Ortaokul güvenli geometri modu: " + middleSchoolGrade + ". sınıf — v4.11 çekirdeği korunarak ek ön-denetim aktif.");
        log("Ortaokul hiza koruması: test giriş bandı sert sınır; sütun içi elastik boşluk üst sınırı " + MIDDLE_SCHOOL_GAP_CAP + " pt.");
    }

    // ---------------------------------------------------------
    // 3) TERCİHLER
    // ---------------------------------------------------------
    var oldH = doc.viewPreferences.horizontalMeasurementUnits;
    var oldV = doc.viewPreferences.verticalMeasurementUnits;
    var oldOrigin = doc.viewPreferences.rulerOrigin;
    var oldRedraw = app.scriptPreferences.enableRedraw;
    app.scriptPreferences.enableRedraw = false;
    doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.POINTS;
    doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.POINTS;
    doc.viewPreferences.rulerOrigin = RulerOrigin.PAGE_ORIGIN;

    function clearGrep() {
        app.findGrepPreferences = NothingEnum.NOTHING;
        app.changeGrepPreferences = NothingEnum.NOTHING;
    }

    var hadError = null;
    var summaryHead = "";
    try {

        // -----------------------------------------------------
        // 4) SABİTLER ve DESENLER
        // -----------------------------------------------------
        var QNUM_RE    = /^[\s\u200B\uFEFF\uFFFC\u009E]*(\d{1,3})\.(?=[\s\t])/;
        var SINIF_RE   = /^\s*\d{1,3}\.\s*SINIF\b/i;
        var YONERGE_RE = /(\d{1,3})\s*[-\u2013]\s*(\d{1,3})\.?\s*sorular/i;
        var LINKED_RE  = /(par[çc]aya|metne|[şs]iire|tabloya|grafi[ğg]e|g[öo]rsele|haritaya|diyalo[ğg]a)\s+g[öo]re/i;
        var RANGE_RE   = /\((\d{1,3})\s*[-\u2013]\s*(\d{1,3})\)/g;
        var MIN_GAP = 4;
        var GAP_FLOOR = 8;
        var SCALES = chkCompress.value ? [1.0, 0.9, 0.8, 0.7, 0.6, 0.5] : [1.0];
        var FW_RATIO = 0.55;

        function isIntroText(s) {
            var head = String(s).substr(0, 60);
            return /Bu\s+(testte|denemede|s[ıi]navda)/i.test(head);
        }

        // v4.8: grup içindeki metin çerçevelerini güvenle listele.
        // allPageItems bazı sürümlerde boş dönebildiğinden öz-yinelemeli yedek içerir.
        function innerTextFrames(container) {
            var out = [];
            var got = null;
            try { got = container.allPageItems; } catch (eIT1) { got = null; }
            if (got !== null && got.length > 0) {
                for (var q9 = 0; q9 < got.length; q9++) {
                    if (got[q9].constructor.name === "TextFrame") { out.push(got[q9]); }
                }
                if (out.length > 0) { return out; }
            }
            var stack = [container];
            while (stack.length > 0) {
                var cur = stack.pop();
                var kids = null;
                try { kids = cur.pageItems; } catch (eIT2) { kids = null; }
                if (kids === null) { continue; }
                for (var q8 = 0; q8 < kids.length; q8++) {
                    var cn8 = kids[q8].constructor.name;
                    if (cn8 === "TextFrame") { out.push(kids[q8]); }
                    else if (cn8 === "Group") { stack.push(kids[q8]); }
                }
            }
            return out;
        }

        // -----------------------------------------------------
        // 5) ENVANTER
        // -----------------------------------------------------
        var pages = doc.pages;
        var pageData = [];
        var allSlots = [];
        var msSignal = false;
        var pi, ci, k, i, j;

        for (pi = 0; pi < pages.length; pi++) {
            var pg = pages[pi];
            var pb = pg.bounds;
            var pW = pb[3] - pb[1];
            var midX = (pb[1] + pb[3]) / 2;
            var botMargin = 0;
            try { botMargin = pg.marginPreferences.bottom; } catch (eM) {}
            var usableBottom = pb[2] - botMargin;

            var introRanges = [];

            var items = [];
            var ignoredIds = {};
            // v4.8: pg.pageItems bazı InDesign sürümlerinde sayfa için BOŞ döner
            // (v4.5-4.7'de hiç soru bulunamamasının nedeni). Kanıtlı yöntem:
            // textFrames + groups; ikisi de boşsa spread öğelerinden bu sayfaya düşenler.
            var tlItems = [];
            var k2;
            try {
                var tfsL = pg.textFrames;
                for (k2 = 0; k2 < tfsL.length; k2++) { tlItems.push(tfsL[k2]); }
            } catch (eTL1) {}
            try {
                var grsL = pg.groups;
                for (k2 = 0; k2 < grsL.length; k2++) { tlItems.push(grsL[k2]); }
            } catch (eTL2) {}
            if (tlItems.length === 0) {
                try {
                    var spIt = pg.parent.pageItems;
                    for (k2 = 0; k2 < spIt.length; k2++) {
                        var cnS = spIt[k2].constructor.name;
                        if (cnS !== "TextFrame" && cnS !== "Group") { continue; }
                        // v4.18: PAGE_ORIGIN'de karşılıklı sayfaların ikisi de 0..W aralığında
                        // ölçüldüğünden komşu sayfanın soruları da bu sayfaya alınıyordu.
                        // Başka sayfaya ait olduğu kesin öğe atlanır (pasteboard öğesi eski kuralla).
                        var ppS = null, ppId = -1;
                        try { ppS = spIt[k2].parentPage; } catch (eTL5) { ppS = null; }
                        if (ppS) {
                            try { ppId = ppS.id; } catch (eTL6) { ppId = -1; }
                            if (ppId !== -1 && ppId !== pg.id) { continue; }
                        }
                        var gbS;
                        try { gbS = spIt[k2].geometricBounds; } catch (eTL3) { continue; }
                        var cxS = (gbS[1] + gbS[3]) / 2;
                        if (cxS >= pb[1] - 2 && cxS <= pb[3] + 2) { tlItems.push(spIt[k2]); }
                    }
                } catch (eTL4) {}
            }
            for (k2 = 0; k2 < tlItems.length; k2++) {
                var scanTfs;
                if (tlItems[k2].constructor.name === "TextFrame") { scanTfs = [tlItems[k2]]; }
                else { scanTfs = innerTextFrames(tlItems[k2]); }
                for (var q7 = 0; q7 < scanTfs.length; q7++) {
                    var c0 = "";
                    try { c0 = String(scanTfs[q7].parentStory.texts[0].contents); } catch (eIsc) { continue; }
                    if (!msSignal && /Bu\s+testte\s+\d+\s+soru/i.test(c0)) { msSignal = true; }
                    if (isIntroText(c0)) {
                        RANGE_RE.lastIndex = 0;
                        var mR;
                        while ((mR = RANGE_RE.exec(c0)) !== null) {
                            introRanges.push({ lo: parseInt(mR[1], 10), hi: parseInt(mR[2], 10) });
                        }
                    }
                }
            }

            for (k = 0; k < tlItems.length; k++) {
                var pit = tlItems[k];
                var cn = pit.constructor.name;
                var gb, content, numTf = null;
                if (cn === "TextFrame") {
                    try { gb = pit.geometricBounds; } catch (e1) { continue; }
                    try { content = String(pit.parentStory.texts[0].contents); } catch (e2) { content = ""; }
                    numTf = pit;
                } else if (cn === "Group") {
                    // GRUP DESTEĞİ: içinde TAM BİR soru barındıran grup, sorunun
                    // kendisi sayılır ve grup hâlinde taşınır; test tanıtımı
                    // barındıran grup sabit tanıtım bloğu sayılır.
                    try { gb = pit.geometricBounds; } catch (eG1) { continue; }
                    var innerTFs = innerTextFrames(pit);
                    if (innerTFs.length === 0) { continue; }
                    var numCount = 0, introTxt = null;
                    content = "";
                    for (i = 0; i < innerTFs.length; i++) {
                        var itxt = "";
                        try { itxt = String(innerTFs[i].parentStory.texts[0].contents); } catch (eG3) { continue; }
                        var gm = QNUM_RE.exec(itxt);
                        if (gm && !SINIF_RE.test(itxt)) {
                            var gbody = itxt.substr(gm[0].length)
                                            .replace(/[\s\u00A0\u200B\uFEFF\uFFFC\u009E\u00BB\u00AB»«¶]+/g, "");
                            if (gbody.length >= 8) {
                                numCount++;
                                if (numCount === 1) { content = itxt; numTf = innerTFs[i]; }
                            }
                        }
                        if (introTxt === null && isIntroText(itxt)) { introTxt = itxt; }
                    }
                    if (numCount === 1) {
                        // grup = soru
                    } else if (numCount > 1) {
                        log("UYARI: s." + pg.name + " — birden çok numaralı soru içeren grup sabit bırakıldı; elle karıştırın.");
                        content = "";
                        numTf = null;
                    } else if (introTxt !== null) {
                        content = introTxt;
                        numTf = null;
                    } else {
                        for (i = 0; i < innerTFs.length; i++) {
                            try { ignoredIds[innerTFs[i].id] = true; } catch (eIG1) {}
                        }
                        continue; // dekor grup — yok say (iç metinleri bekçi engeli DEĞİLDİR)
                    }
                } else {
                    continue;
                }

                var rec = {
                    tf: pit, numTf: numTf, page: pi,
                    pool: 0, etiket: trimS(content).substr(0, 18),
                    y1: gb[0], y2: gb[2], x1: gb[1], x2: gb[3],
                    h: gb[2] - gb[0],
                    shape: ((gb[3] - gb[1]) > pW * FW_RATIO) ? "FW" : "COL",
                    col: ((gb[1] + gb[3]) / 2 < midX) ? 0 : 1,
                    kind: "diger", num: 0, zone: 0, sec: -1,
                    linkedHeader: false, grup: 0, ans: "?",
                    emptyText: (trimS(content) === "" && cn === "TextFrame")
                };

                if (isIntroText(content)) {
                    rec.kind = "intro";
                } else {
                    var m = QNUM_RE.exec(content);
                    if (m && !SINIF_RE.test(content)) {
                        // taslak artığı: numara var ama gövde yok ("1. »" gibi)
                        var body = content.substr(m[0].length)
                                          .replace(/[\s\u00A0\u200B\uFEFF\uFFFC\u009E\u00BB\u00AB»«¶]+/g, "");
                        if (body.length >= 8) {
                            rec.kind = "soru";
                            rec.num = parseInt(m[1], 10);
                        } else {
                            rec.numStub = true;   // 'diger' kalır; hayalet filtresinde ayıklanır
                        }
                    } else if (!m) {
                        var y = YONERGE_RE.exec(content);
                        if (y) {
                            rec.kind = "yonerge";
                            rec.lo = parseInt(y[1], 10);
                            rec.hi = parseInt(y[2], 10);
                            rec.linkedHeader = LINKED_RE.test(content);
                        }
                    }
                }
                items.push(rec);
            }

            // GÖRSEL BİRLEŞİK SINIR (v4.3): soru yüksekliği/genişliği, çerçeveden
            // taşan BAĞLI görseller dahil ölçülür. Yerleşim ve bindirme denetimi
            // baskıdaki gerçek kapladığı alana göre yapılır.
            for (k = 0; k < items.length; k++) {
                var rU = items[k];
                rU.fy1 = rU.y1; rU.fx1 = rU.x1; rU.fy2 = rU.y2; rU.fx2 = rU.x2;
                if (rU.kind !== "soru") { continue; }
                try {
                    var stU = (rU.numTf || rU.tf).parentStory;
                    if (stU.textContainers.length !== 1) { continue; }
                    var anc = stU.pageItems;
                    var pgH = pb[2] - pb[0];
                    for (i = 0; i < anc.length; i++) {
                        var agb;
                        try { agb = anc[i].geometricBounds; } catch (eA1) { continue; }
                        // v4.15 akıl süzgeci: yanlış koordinat uzayından gelen
                        // bağlı nesneler zarfı bozmasın
                        if (agb[0] < rU.fy1 - 1.2 * pgH || agb[2] > rU.fy2 + 1.2 * pgH) { continue; }
                        if (agb[3] < pb[1] - pW || agb[1] > pb[3] + pW) { continue; }
                        if (agb[0] < rU.y1) { rU.y1 = agb[0]; }
                        if (agb[2] > rU.y2) { rU.y2 = agb[2]; }
                        if (agb[1] < rU.x1) { rU.x1 = agb[1]; }
                        if (agb[3] > rU.x2) { rU.x2 = agb[3]; }
                    }
                } catch (eU) {}
                rU.h = rU.y2 - rU.y1;
                rU.shape = ((rU.x2 - rU.x1) > pW * FW_RATIO) ? "FW" : "COL";
                rU.col = ((rU.x1 + rU.x2) / 2 < midX) ? 0 : 1;
            }
            // yardımcı süreç için konmuş minik numaralı çerçeveler soru değildir
            for (k = 0; k < items.length; k++) {
                if (items[k].kind === "soru" && (items[k].y2 - items[k].y1) < 28) {
                    items[k].kind = "diger";
                    items[k].emptyText = true;
                }
            }

            // HAYALET FİLTRESİ (v4.2): boş 'diger' çerçeveler ve bir soruya
            // binen 'diger' çerçeveler yerleşim zincirine alınmaz.
            function ovArea(a, b) {
                var w = Math.min(a.x2, b.x2) - Math.max(a.x1, b.x1);
                var h2 = Math.min(a.y2, b.y2) - Math.max(a.y1, b.y1);
                return (w > 0 && h2 > 0) ? (w * h2) : 0;
            }
            // İKİZ ÇERÇEVE BİRLEŞTİRME (v4.4): aynı numaralı ve büyük ölçüde
            // üst üste binen iki 'soru' çerçevesinden gövdesi kısa olan kap
            // sayılır ve yerleşim dışı bırakılır (görsel 1'deki çift "1." vakası).
            var twinDrop = 0;
            for (k = 0; k < items.length; k++) {
                if (items[k].kind !== "soru") { continue; }
                for (i = k + 1; i < items.length; i++) {
                    if (items[i].kind !== "soru") { continue; }
                    if (items[i].num !== items[k].num) { continue; }
                    var ovT = ovArea(items[k], items[i]);
                    var aK = (items[k].x2 - items[k].x1) * (items[k].y2 - items[k].y1);
                    var aI = (items[i].x2 - items[i].x1) * (items[i].y2 - items[i].y1);
                    var aMin = (aK < aI) ? aK : aI;
                    if (aMin > 0 && ovT > 0.6 * aMin) {
                        var lenK = 0, lenI = 0;
                        try { lenK = String(items[k].tf.parentStory.texts[0].contents).length; } catch (eL1) {}
                        try { lenI = String(items[i].tf.parentStory.texts[0].contents).length; } catch (eL2) {}
                        var dropIdx = (lenK < lenI) ? k : i;
                        items[dropIdx].kind = "diger";
                        items[dropIdx].emptyText = true; // hayalet filtresi ayıklasın
                        twinDrop++;
                    }
                }
            }
            if (twinDrop > 0) {
                log("UYARI: s." + pg.name + " — aynı numaralı İKİZ soru çerçevesi bulundu; kap çerçeve yerleşim dışı bırakıldı. A dosyasında birleştirmeniz önerilir.");
            }

            var kept = [], droppedGhost = 0, droppedStub = 0;
            for (k = 0; k < items.length; k++) {
                var itF = items[k];
                if (itF.kind === "diger") {
                    if (itF.numStub) { droppedStub++; try { ignoredIds[itF.tf.id] = true; } catch (eIG2) {} continue; }
                    if (itF.emptyText) { droppedGhost++; try { ignoredIds[itF.tf.id] = true; } catch (eIG3) {} continue; }
                    var ghost = false;
                    for (i = 0; i < items.length; i++) {
                        if (items[i].kind !== "soru") { continue; }
                        var ov = ovArea(itF, items[i]);
                        var aSelf = (itF.x2 - itF.x1) * (itF.y2 - itF.y1);
                        if (aSelf > 0 && ov > 0.4 * aSelf) { ghost = true; break; }
                    }
                    if (ghost) { droppedGhost++; try { ignoredIds[itF.tf.id] = true; } catch (eIG4) {} continue; }
                }
                kept.push(itF);
            }
            if (droppedStub > 0) {
                log("UYARI: s." + pg.name + " — " + droppedStub + " NUMARALI BOŞ çerçeve (taslak artığı) yerleşim dışı bırakıldı; A dosyasında temizlemeniz önerilir.");
            }
            if (droppedGhost > 0) {
                log("Bilgi: s." + pg.name + " — " + droppedGhost + " boş/dekor çerçeve yerleşim dışı bırakıldı.");
            }
            items = kept;
            items.sort(function (a, b) { return (a.y1 - b.y1) || (a.x1 - b.x1); });

            // bloklar
            var blocks = [];
            for (k = 0; k < items.length; k++) {
                var it = items[k];
                if (it.shape === "FW") {
                    blocks.push({ type: (it.kind === "soru") ? "FWQ" : "FWF", it: it, top: it.y1, bot: it.y2 });
                } else {
                    var last = blocks.length ? blocks[blocks.length - 1] : null;
                    if (last && last.type === "REG") {
                        last.items.push(it);
                        if (it.y1 < last.top) { last.top = it.y1; }
                        if (it.y2 > last.bot) { last.bot = it.y2; }
                    } else {
                        blocks.push({ type: "REG", items: [it], top: it.y1, bot: it.y2 });
                    }
                }
            }
            for (k = 0; k < blocks.length; k++) {
                if (blocks[k].type !== "REG") { continue; }
                // sütun x-bantları (bloktaki sorulardan; soru yoksa sayfa yarıları)
                var bx = [[null, null], [null, null]];
                for (i = 0; i < blocks[k].items.length; i++) {
                    var bi = blocks[k].items[i];
                    if (bi.kind !== "soru") { continue; }
                    var bc = bi.col;
                    if (bx[bc][0] === null || bi.x1 < bx[bc][0]) { bx[bc][0] = bi.x1; }
                    if (bx[bc][1] === null || bi.x2 > bx[bc][1]) { bx[bc][1] = bi.x2; }
                }
                if (bx[0][0] === null) { bx[0] = [pb[1], midX]; }
                if (bx[1][0] === null) { bx[1] = [midX, pb[3]]; }
                var c0a = [], c1a = [];
                for (i = 0; i < blocks[k].items.length; i++) {
                    var it9 = blocks[k].items[i];
                    if (it9.kind === "soru") {
                        if (it9.col === 0) { c0a.push(it9); } else { c1a.push(it9); }
                    } else {
                        // v4.10: iki sütun arasına taşan sabit, HER İKİ zincire pinlenir;
                        // böylece model ile baskı gerçeği aynı şeyi görür.
                        var in0 = (it9.x2 > bx[0][0] + 4) && (it9.x1 < bx[0][1] - 4);
                        var in1 = (it9.x2 > bx[1][0] + 4) && (it9.x1 < bx[1][1] - 4);
                        if (!in0 && !in1) { if (it9.col === 0) { in0 = true; } else { in1 = true; } }
                        if (in0) { c0a.push(it9); }
                        if (in1) { c1a.push(it9); }
                    }
                }
                c0a.sort(function (a, b) { return a.y1 - b.y1; });
                c1a.sort(function (a, b) { return a.y1 - b.y1; });
                blocks[k].cols = [c0a, c1a];
            }

            var maxB = usableBottom;
            for (k = 0; k < items.length; k++) { if (items[k].y2 > maxB) { maxB = items[k].y2; } }

            pageData.push({ blocks: blocks, items: items, HB: maxB + 0.5, introRanges: introRanges,
                            bundleWith: -1, name: String(pg.name), ignoredIds: ignoredIds });
        }

        // v4.15: dosya adı 5-8 kalıbına uymasa bile, karşılıklı sayfa +
        // "Bu testte N soru" branş girişi görülen belgede ortaokul koruması açılır.
        // (Lise/AYT girişleri "Bu testte sırasıyla, ..." kalıbındadır ve tek
        //  sayfalı yayılımdadır; bu kapıdan geçemez.)
        if (!isMiddleSchool && msSignal) {
            var fpMS = false;
            try { fpMS = (doc.documentPreferences.facingPages === true); } catch (eFPms) {}
            if (fpMS) {
                isMiddleSchool = true;
                log("Ortaokul güvenli modu belge içeriğinden algılandı (karşılıklı sayfa + branş test girişi).");
            }
        }

        // -----------------------------------------------------
        // 6) BÖLÜMLER ve DERS BÖLGELERİ
        // -----------------------------------------------------
        function pageQuestionWalk(pd, fn) {
            for (var b = 0; b < pd.blocks.length; b++) {
                var blk = pd.blocks[b];
                if (blk.type === "FWQ") { fn(blk.it); }
                else if (blk.type === "REG") {
                    for (var c2 = 0; c2 < 2; c2++) {
                        for (var t2 = 0; t2 < blk.cols[c2].length; t2++) { fn(blk.cols[c2][t2]); }
                    }
                }
            }
        }

        var secZones = [], secQCount = [];
        var secCount = 0, seenAny = false;
        function addZone(sec, lo, hi) {
            if (!secZones[sec]) { secZones[sec] = []; }
            for (var z = 0; z < secZones[sec].length; z++) {
                if (secZones[sec][z].lo === lo && secZones[sec][z].hi === hi) { return; }
            }
            secZones[sec].push({ lo: lo, hi: hi });
        }

        var spillN = 0, spillLog = [];
        for (pi = 0; pi < pageData.length; pi++) {
            (function (pd) {
                var resetOnPage = false, prevSecAtReset = -1, prevCntAtReset = 0;
                pageQuestionWalk(pd, function (r) {
                    if (r.kind !== "soru") { return; }
                    if (r.num === 1 && seenAny) {
                        resetOnPage = true;
                        prevSecAtReset = secCount;
                        prevCntAtReset = secQCount[secCount] || 0;
                        secCount++;
                    }
                    // TEST KAYMASI (v4.3): yeni test başlayan sayfada, önceki testin
                    // devamı olan soru (örn. S16) yanlış teste sayılmasın; yerine kilitlenir.
                    if (resetOnPage && r.num !== 1 && r.num === prevCntAtReset + 1) {
                        r.sec = prevSecAtReset;
                        secQCount[prevSecAtReset] = prevCntAtReset + 1;
                        prevCntAtReset++;
                        spillN++;
                        r.grup = 900000 + spillN;   // kilit: hiçbir takasa girmez
                        spillLog.push("Test " + (prevSecAtReset + 1) + " S" + r.num + " (s." + pd.name + ")");
                        return;
                    }
                    seenAny = true;
                    r.sec = secCount;
                    if (!secQCount[secCount]) { secQCount[secCount] = 0; }
                    secQCount[secCount]++;
                });
                for (var q = 0; q < pd.items.length; q++) {
                    if (pd.items[q].kind === "yonerge" && seenAny) {
                        addZone(secCount, pd.items[q].lo, pd.items[q].hi);
                    }
                }
            })(pageData[pi]);
        }
        var totalSections = secCount + 1;
        if (spillLog.length > 0) {
            log("Test kayması yakalandı ve yerine kilitlendi: " + spillLog.join(", "));
        }

        for (pi = 0; pi < pageData.length; pi++) {
            if (pageData[pi].introRanges.length === 0) { continue; }
            var firstSec = -1;
            pageQuestionWalk(pageData[pi], function (r) {
                if (r.kind === "soru" && firstSec === -1) { firstSec = r.sec; }
            });
            if (firstSec < 0) { continue; }
            for (j = 0; j < pageData[pi].introRanges.length; j++) {
                addZone(firstSec, pageData[pi].introRanges[j].lo, pageData[pi].introRanges[j].hi);
            }
        }

        function zoneOf(sec, num) {
            var zl = secZones[sec];
            if (!zl) { return 0; }
            for (var z = 0; z < zl.length; z++) {
                if (num >= zl[z].lo && num <= zl[z].hi) { return z + 1; }
            }
            return 0;
        }

        for (pi = 0; pi < pageData.length; pi++) {
            var pdG = pageData[pi];
            for (k = 0; k < pdG.blocks.length; k++) {
                if (pdG.blocks[k].type === "FWQ") {
                    var rF = pdG.blocks[k].it;
                    rF.zone = zoneOf(rF.sec, rF.num);
                } else if (pdG.blocks[k].type === "REG") {
                    for (ci = 0; ci < 2; ci++) {
                        var stk = pdG.blocks[k].cols[ci];
                        var grupSayac = 0;
                        for (i = 0; i < stk.length; i++) {
                            var r1 = stk[i];
                            if (r1.kind !== "soru") { continue; }
                            r1.zone = zoneOf(r1.sec, r1.num);
                            if (i > 0 && stk[i - 1].kind === "yonerge" && stk[i - 1].linkedHeader) {
                                grupSayac++;
                                var gid = (pi + 1) * 1000 + ci * 100 + grupSayac;
                                r1.grup = gid;
                                var kk = i + 1;
                                while (kk < stk.length && stk[kk].kind === "soru") {
                                    stk[kk].grup = gid;
                                    stk[kk].zone = zoneOf(stk[kk].sec, stk[kk].num);
                                    kk++;
                                }
                                i = kk - 1;
                            }
                        }
                    }
                }
            }
        }

        function readAnswer(rec) {
            try {
                var stq = (rec.numTf || rec.tf).parentStory;
                for (var qi = 0; qi < stq.paragraphs.length; qi++) {
                    var pr = stq.paragraphs[qi];
                    var sn = "";
                    try { sn = pr.appliedParagraphStyle.name; } catch (e3) {}
                    if (sn.toUpperCase().indexOf("KOD VE CEVAP") !== -1) {
                        var mm = /([A-E])/.exec(trimS(String(pr.contents)));
                        if (mm) { return mm[1]; }
                    }
                }
            } catch (e4) {}
            return "?";
        }

        var totalQ = 0, fwQ = 0, colQ = 0, skippedPages = 0;
        for (pi = 0; pi < pageData.length; pi++) {
            var hasQ = false;
            pageQuestionWalk(pageData[pi], function (r) {
                if (r.kind !== "soru") { return; }
                hasQ = true;
                r.ans = readAnswer(r);
                r.slotKey = "s" + allSlots.length;
                r.pdIdx = pi;
                allSlots.push(r);
                totalQ++;
                if (r.shape === "FW") { fwQ++; } else { colQ++; }
            });
            if (!hasQ) { skippedPages++; }
        }

        if (totalQ === 0) {
            throw new Error("HİÇ SORU BULUNAMADI. Bu bir dosya sorunu değil, script/InDesign uyum sorunudur. " +
                            "Oluşan B kopyasını silin ve bu pencerenin görüntüsünü iletin. Orijinal A değişmedi.");
        }

        // Aynı testte YİNELENEN numara denetimi + KOMŞU TESTE KAÇAN SORU düzeltmesi
        var haveNum = [];
        for (k = 0; k < totalSections; k++) { haveNum.push({}); }
        for (k = 0; k < allSlots.length; k++) { haveNum[allSlots[k].sec][allSlots[k].num] = true; }
        var dupSeen = [], dupList = [], strayFix = [];
        // v4.18: kaçak/yinelenen soru içeren testler blok takasına girmez; blok takası
        // testi okuma sırasıyla baştan numaraladığından bu sorular yanlış numara alıyordu.
        var noBundleSec = {};
        for (k = 0; k < totalSections; k++) { dupSeen.push({}); }
        for (k = 0; k < allSlots.length; k++) {
            var rD = allSlots[k];
            if (dupSeen[rD.sec][rD.num]) {
                // sonradan gelen kopya: bir SONRAKİ testte bu numara eksikse oraya aittir
                if (rD.sec + 1 < totalSections && !haveNum[rD.sec + 1][rD.num] &&
                    rD.num <= (secQCount[rD.sec + 1] || 0) + 1) {
                    haveNum[rD.sec + 1][rD.num] = true;
                    secQCount[rD.sec] = (secQCount[rD.sec] || 1) - 1;
                    secQCount[rD.sec + 1] = (secQCount[rD.sec + 1] || 0) + 1;
                    rD.sec = rD.sec + 1;
                    rD.zone = zoneOf(rD.sec, rD.num);
                    rD.grup = 800000 + k;   // yerinde kilitli: numarası ve yeri zaten doğru
                    noBundleSec[rD.sec] = true;
                    strayFix.push("Test " + (rD.sec + 1) + " S" + rD.num + " (s." + pageData[rD.pdIdx].name + ")");
                } else {
                    dupList.push("Test " + (rD.sec + 1) + " S" + rD.num + " (s." + pageData[rD.pdIdx].name + ")");
                    rD.grup = 800000 + k;
                    rD.keySkip = true;
                    noBundleSec[rD.sec] = true;
                    dupSeen[rD.sec][rD.num].grup = 800000 + k + 500;
                    dupSeen[rD.sec][rD.num].keySkip = true;
                }
            } else { dupSeen[rD.sec][rD.num] = rD; }
        }
        if (strayFix.length > 0) {
            log("Düzeltildi — komşu testin sayfasına konmuş soru kendi testine sayıldı ve yerinde kilitlendi: " +
                strayFix.join(", ") + ". (A dosyasında bu soruyu doğru sayfaya almanız önerilir.)");
        }
        if (dupList.length > 0) {
            log("KRİTİK: Aynı testte yinelenen soru numarası: " + dupList.join(", ") +
                " — bu sorular YERİNDE KİLİTLENDİ ve cevap anahtarı yazımından dışlandı; A dosyasını kontrol edin.");
        }

        // -----------------------------------------------------
        // v4.15 ÖZEL HAVUZLAR: kullanıcı aralıkları yalnız kendi
        // içinde karışır; boş bırakılırsa davranış birebir aynıdır.
        // -----------------------------------------------------
        (function () {
            var raw = trimS(txtPools.text || "");
            if (raw === "") { return; }
            function parseList(s) {
                var out = [], parts = s.split(",");
                for (var pL = 0; pL < parts.length; pL++) {
                    var t = trimS(parts[pL]);
                    if (t === "") { continue; }
                    var mL = /^(\d{1,3})(?:\s*-\s*(\d{1,3}))?$/.exec(t);
                    if (!mL) { return null; }
                    var lo = parseInt(mL[1], 10);
                    var hi = mL[2] ? parseInt(mL[2], 10) : lo;
                    if (hi < lo) { var tt = lo; lo = hi; hi = tt; }
                    out.push([lo, hi]);
                }
                return out.length ? out : null;
            }
            function inList(nv, lst) {
                for (var q = 0; q < lst.length; q++) {
                    if (nv >= lst[q][0] && nv <= lst[q][1]) { return true; }
                }
                return false;
            }
            var entries = raw.split(/[;\n\r]+/);
            var poolIdx = 0, overlapWarn = 0;
            for (var eI = 0; eI < entries.length; eI++) {
                var ent = trimS(entries[eI]);
                if (ent === "") { continue; }
                // v4.17: doğal yazım — "sayfa 7-8 soru 25,31", "sayfa 7 ve 8 soru 25 ve 31",
                // "7-8 25,31", "s7-8:25,31" biçimlerinin hepsi kabul edilir.
                var entN = ent.replace(/[\u2013\u2014]/g, "-");   // uzun tire → normal tire
                entN = entN.replace(/\bve\b/gi, ",");
                entN = entN.replace(/sayfalar/gi, "s").replace(/sayfa/gi, "s")
                           .replace(/sorular/gi, "#").replace(/soru/gi, "#").replace(/\bno\b/gi, "#");
                var pgsRaw = "", numRaw = "";
                var ci2 = entN.indexOf(":");
                var hi3 = entN.indexOf("#");
                if (ci2 >= 0) {
                    pgsRaw = entN.substring(0, ci2);
                    numRaw = entN.substring(ci2 + 1);
                } else if (hi3 >= 0) {
                    pgsRaw = entN.substring(0, hi3);
                    numRaw = entN.substring(hi3 + 1);
                } else {
                    var mSp = /^\s*(s\.?\s*)?([0-9][0-9,\-\s]*?)(?:\s+([0-9][0-9,\-\s]*))?\s*$/i.exec(entN);
                    if (mSp) { pgsRaw = (mSp[1] || "") + mSp[2]; numRaw = mSp[3] || ""; }
                    else { pgsRaw = entN; }
                }
                numRaw = trimS(String(numRaw)).replace(/^[.#:\s]+/, "");
                pgsRaw = trimS(pgsRaw).replace(/^s\.?\s*/i, "");
                var pgsList = parseList(pgsRaw);
                var numList = (trimS(numRaw) === "") ? null : parseList(numRaw);
                if (pgsList === null || (trimS(numRaw) !== "" && numList === null)) {
                    log("UYARI: Özel havuz girdisi anlaşılamadı: \u201C" + ent +
                        "\u201D — örnek yazım: sayfa 7 ve 8 soru 5-10  (ya da 7-8:5-10)");
                    continue;
                }
                poolIdx++;
                var cnt = 0;
                for (var sI = 0; sI < allSlots.length; sI++) {
                    var rP = allSlots[sI];
                    var pNum = parseInt(pageData[rP.pdIdx].name, 10);
                    if (isNaN(pNum) || !inList(pNum, pgsList)) { continue; }
                    if (numList !== null && !inList(rP.num, numList)) { continue; }
                    if (rP.pool > 0) { overlapWarn++; continue; }
                    rP.pool = poolIdx;
                    cnt++;
                }
                var fwC = 0, colC = 0;
                for (sI = 0; sI < allSlots.length; sI++) {
                    if (allSlots[sI].pool !== poolIdx) { continue; }
                    if (allSlots[sI].shape === "FW") { fwC++; } else { colC++; }
                }
                log("Özel havuz " + poolIdx + " (\u201C" + ent + "\u201D): " + cnt + " soru" +
                    (cnt === 0 ? " — EŞLEŞME YOK, tanımı kontrol edin." :
                     (cnt === 1 ? " — tek soru karışamaz, yerinde kalır." :
                      " kendi içinde karışacak.")));
                if (fwC > 0 && colC > 0 && (fwC === 1 || colC === 1)) {
                    log("UYARI: Havuz " + poolIdx + " karışık tipte (" + fwC + " tam genişlik + " + colC +
                        " sütun) — farklı tipler birbiriyle takas edilemez; tek kalan tip yerinde kalabilir.");
                }
            }
            if (overlapWarn > 0) {
                log("UYARI: " + overlapWarn + " soru birden çok havuz tanımına uydu — ilk tanım geçerli sayıldı.");
            }
        })();

        var zi2 = [];
        for (k = 0; k < totalSections; k++) {
            var zstr = "";
            if (secZones[k] && secZones[k].length > 0) {
                var zp = [];
                for (j = 0; j < secZones[k].length; j++) { zp.push(secZones[k][j].lo + "-" + secZones[k][j].hi); }
                zstr = " [" + zp.join(", ") + "]";
            } else { zstr = " [tek bölge]"; }
            zi2.push("Test " + (k + 1) + ": " + (secQCount[k] || 0) + " soru" + zstr);
        }
        log("Envanter: " + pages.length + " sayfa (" + skippedPages + " sorusuz sayfa atlandı), " +
            totalSections + " test, " + totalQ + " soru (" + fwQ + " tam genişlik, " + colQ + " sütun).");
        log("Ders bölgeleri — " + zi2.join("  |  "));


        // -----------------------------------------------------
        // 7) YERLEŞİM MOTORU
        // -----------------------------------------------------
        // v4.13 ORTAOKUL HİZA KORUMASI:
        // 5-8 tasarımlarında test giriş metni ile ilk soru çerçevesi A'da geometrik
        // olarak üst üste gelebiliyor. A sorusunun iç boşluğu bunu gizlerken başka
        // bir soru aynı slota geldiğinde görünür metin başlığın içine çıkabiliyor.
        // Bu yardımcı yalnız "intro" bandını sert üst sınır kabul eder.
        function middleSchoolIntroBarrier(pd, slot) {
            if (!isMiddleSchool) { return null; }
            var barrier = null;
            for (var mb = 0; mb < pd.items.length; mb++) {
                var fx = pd.items[mb];
                if (fx.kind !== "intro") { continue; }

                var xov = Math.min(slot.x2, fx.x2) - Math.max(slot.x1, fx.x1);
                if (xov <= 4) { continue; }

                // Uzak bir giriş bloğu bu slotu etkilemesin.
                if (fx.y2 < slot.y1 - 72 || fx.y1 > slot.y1 + 36) { continue; }

                var cand = fx.y2 + MIN_GAP;
                if (barrier === null || cand > barrier) { barrier = cand; }
            }
            return barrier;
        }

        function tryLayoutScale(pd, assign, scale) {
            var plc = [];
            var cursor = null, prevBotOld = null;
            function gg(x) {
                if (x <= 0) { return x; }
                var v = x * scale;
                var fl = (x < GAP_FLOOR) ? x : GAP_FLOOR;
                return (v > fl) ? v : fl;
            }
            for (var b = 0; b < pd.blocks.length; b++) {
                var blk = pd.blocks[b];
                var gap = (prevBotOld === null) ? null : (blk.top - prevBotOld);
                if (blk.type === "FWF") {
                    var ntF = blk.top;
                    if (cursor !== null && gap !== null) {
                        var minG = (gap < MIN_GAP) ? gap : MIN_GAP;
                        if (ntF < cursor + minG - 0.01) { return null; }
                    }
                    cursor = blk.bot; prevBotOld = blk.bot;
                } else if (blk.type === "FWQ") {
                    var contQ = assign[blk.it.slotKey];
                    var ntQ = (cursor === null) ? blk.top : (cursor + gg(gap));
                    if (isMiddleSchool) {
                        var msFwBarrier = middleSchoolIntroBarrier(pd, blk.it);
                        if (msFwBarrier !== null && ntQ < msFwBarrier) { ntQ = msFwBarrier; }
                    }
                    plc.push({ slot: blk.it, cont: contQ, ny1: ntQ });
                    cursor = ntQ + contQ.h; prevBotOld = blk.bot;
                } else {
                    var shift = (cursor === null) ? 0 : ((cursor + gg(gap)) - blk.top);
                    var regBot = null;
                    for (var c2 = 0; c2 < 2; c2++) {
                        var pB = null, pBold = null;
                        for (var t2 = 0; t2 < blk.cols[c2].length; t2++) {
                            var it2 = blk.cols[c2][t2];
                            var g2 = (pBold === null) ? null : (it2.y1 - pBold);
                            if (it2.kind !== "soru") {
                                var ntX = it2.y1 + shift;
                                if (isMiddleSchool) { ntX = it2.y1; }
                                if (pB !== null && g2 !== null) {
                                    var mg2 = (g2 < MIN_GAP) ? g2 : MIN_GAP;
                                    if (ntX < pB + mg2 - 0.01) { return null; }
                                }
                                pB = it2.y2 + shift; pBold = it2.y2;
                                if (isMiddleSchool) { pB = it2.y2; }
                            } else {
                                var cont2 = assign[it2.slotKey];
                                var nt2 = (pB === null) ? (it2.y1 + shift) : (pB + gg(g2));
                                if (isMiddleSchool) {
                                    if (pB === null) {
                                        var msBarrier = middleSchoolIntroBarrier(pd, it2);
                                        if (msBarrier !== null && nt2 < msBarrier) { nt2 = msBarrier; }
                                    } else if (g2 !== null && g2 > MIDDLE_SCHOOL_GAP_CAP) {
                                        nt2 = pB + gg(MIDDLE_SCHOOL_GAP_CAP);
                                    }
                                }
                                plc.push({ slot: it2, cont: cont2, ny1: nt2 });
                                pB = nt2 + cont2.h; pBold = it2.y2;
                            }
                            if (pB !== null && (regBot === null || pB > regBot)) { regBot = pB; }
                        }
                    }
                    cursor = (regBot !== null) ? regBot : (blk.bot + shift);
                    prevBotOld = blk.bot;
                }
                if (cursor !== null && cursor > pd.HB) { return null; }
            }
            return plc;
        }

        // v4.12: 5-8. sınıfta tryLayoutScale yalnız dikey zinciri doğruluyordu.
        // Görsel ağırlıklı sorular karşı sütuna taşabildiği için gerçek zarf,
        // diğer soru zarfları ve sabit çerçevelerle taşımadan ÖNCE karşılaştırılır.
        function middleSchoolRectsOverlap(a, b) {
            return !(a[2] <= b[0] + 1 || b[2] <= a[0] + 1 ||
                     a[3] <= b[1] + 1 || b[3] <= a[1] + 1);
        }

        function middleSchoolDeepOverlap(a, b) {
            var dv = ((a[2] < b[2]) ? a[2] : b[2]) - ((a[0] > b[0]) ? a[0] : b[0]);
            var dh = ((a[3] < b[3]) ? a[3] : b[3]) - ((a[1] > b[1]) ? a[1] : b[1]);
            return (dv > 3 && dh > 3);
        }

        function middleSchoolLayoutSafe(pd, plc) {
            if (!isMiddleSchool) { return true; }

            var rects = [];
            var qx;
            for (qx = 0; qx < plc.length; qx++) {
                var peQ = plc[qx];
                var envW = peQ.cont.x2 - peQ.cont.x1;
                var envH = peQ.cont.y2 - peQ.cont.y1;
                rects.push([
                    peQ.ny1,
                    peQ.slot.x1,
                    peQ.ny1 + envH,
                    peQ.slot.x1 + envW
                ]);
            }

            for (qx = 0; qx < rects.length; qx++) {
                if (rects[qx][2] > pd.HB + 2) { return false; }
                for (var qy = qx + 1; qy < rects.length; qy++) {
                    if (middleSchoolRectsOverlap(rects[qx], rects[qy])) { return false; }
                }
            }

            var originalQuestions = [];
            for (qx = 0; qx < pd.items.length; qx++) {
                if (pd.items[qx].kind === "soru") {
                    originalQuestions.push([
                        pd.items[qx].y1, pd.items[qx].x1,
                        pd.items[qx].y2, pd.items[qx].x2
                    ]);
                }
            }

            for (qx = 0; qx < pd.items.length; qx++) {
                var fixedItem = pd.items[qx];
                if (fixedItem.kind === "soru") { continue; }

                var fixedRect = [fixedItem.y1, fixedItem.x1, fixedItem.y2, fixedItem.x2];
                var touchedQuestionInA = false;
                for (var qo = 0; qo < originalQuestions.length; qo++) {
                    if (middleSchoolDeepOverlap(fixedRect, originalQuestions[qo])) {
                        touchedQuestionInA = true;
                        break;
                    }
                }
                if (touchedQuestionInA) { continue; }

                for (var qr = 0; qr < rects.length; qr++) {
                    if (middleSchoolRectsOverlap(rects[qr], fixedRect)) { return false; }
                }
            }

            return true;
        }

        function fitLevel(pd, assign) {
            for (var si = 0; si < SCALES.length; si++) {
                if (isMiddleSchool) {
                    var middleSchoolPlc = tryLayoutScale(pd, assign, SCALES[si]);
                    if (middleSchoolPlc !== null && middleSchoolLayoutSafe(pd, middleSchoolPlc)) { return si; }
                    continue;
                }
                if (tryLayoutScale(pd, assign, SCALES[si]) !== null) { return si; }
            }
            return -1;
        }

        function copyAssign(a) {
            var b2 = {};
            for (var kk4 in a) { b2[kk4] = a[kk4]; }
            return b2;
        }

        // -----------------------------------------------------
        // 8) FAZ 1 — sayfa içi karışım
        // -----------------------------------------------------
        var mode = rbCross.value ? "cross" : (rbCol.value ? "col" : "rnd");
        var seed = parseInt(trimS(txtSeed.text), 10);
        if (isNaN(seed)) { seed = 2526; }
        var rng = makeRng(seed);

        var assigns = [];

        for (pi = 0; pi < pageData.length; pi++) {
            var pd = pageData[pi];
            var slots = [];
            pageQuestionWalk(pd, function (r) { if (r.kind === "soru") { slots.push(r); } });

            var assign = {};
            for (k = 0; k < slots.length; k++) { assign[slots[k].slotKey] = slots[k]; }

            var groups = {}, gkeys = [];
            for (k = 0; k < slots.length; k++) {
                var gk = slots[k].sec + "|" + slots[k].zone + "|" + slots[k].shape + "|" + slots[k].grup + "|" + slots[k].pool;
                if (!groups[gk]) { groups[gk] = []; gkeys.push(gk); }
                groups[gk].push(slots[k]);
            }

            for (var g2i = 0; g2i < gkeys.length; g2i++) {
                var grp = groups[gkeys[g2i]];
                var mQ = grp.length;
                if (mQ < 2) { continue; }
                if (grp[0].grup > 0 && !chkLinked.value) { continue; }
                var contents = grp.slice(0);

                if (mode === "col") {
                    if (grp[0].shape !== "COL") { continue; }
                    var byCol = [[], []];
                    for (k = 0; k < mQ; k++) { byCol[grp[k].col].push(k); }
                    var permC = [];
                    for (k = 0; k < mQ; k++) { permC[k] = k; }
                    for (ci = 0; ci < 2; ci++) {
                        for (k = 0; k + 1 < byCol[ci].length; k += 2) {
                            var a1 = byCol[ci][k], b1 = byCol[ci][k + 1];
                            var tsw = permC[a1]; permC[a1] = permC[b1]; permC[b1] = tsw;
                        }
                    }
                    var trialC = copyAssign(assign);
                    for (k = 0; k < mQ; k++) { trialC[grp[k].slotKey] = contents[permC[k]]; }
                    if (isMiddleSchool) {
                        var middleSchoolColPlc = tryLayoutScale(pd, trialC, 1.0);
                        if (middleSchoolColPlc === null || !middleSchoolLayoutSafe(pd, middleSchoolColPlc)) { continue; }
                    }
                    if (tryLayoutScale(pd, trialC, 1.0) !== null) {
                        for (k = 0; k < mQ; k++) { assign[grp[k].slotKey] = contents[permC[k]]; }
                    }
                    continue;
                }

                var perms;
                if (mQ <= 7) { perms = allPerms(mQ); }
                else {
                    perms = [[]];
                    for (k = 0; k < mQ; k++) { perms[0].push(mQ - 1 - k); }
                }

                var best = null, bestD = -1, bestL = 99, bestS = -1;
                var feasStrict = [], feasComp = [];
                for (var pp = 0; pp < perms.length; pp++) {
                    var pr2 = perms[pp];
                    var trial = copyAssign(assign);
                    for (k = 0; k < mQ; k++) { trial[grp[k].slotKey] = contents[pr2[k]]; }
                    var lvl = fitLevel(pd, trial);
                    if (lvl < 0) { continue; }
                    var disp = 0, sumd = 0;
                    for (k = 0; k < mQ; k++) {
                        if (pr2[k] !== k) { disp++; }
                        sumd += (pr2[k] > k) ? (pr2[k] - k) : (k - pr2[k]);
                    }
                    if (mode === "rnd") {
                        if (disp > 0) { if (lvl === 0) { feasStrict.push(pr2); } else { feasComp.push(pr2); } }
                        continue;
                    }
                    var better = (disp > bestD) ||
                                 (disp === bestD && lvl < bestL) ||
                                 (disp === bestD && lvl === bestL && sumd > bestS);
                    if (better) {
                        best = pr2; bestD = disp; bestL = lvl; bestS = sumd;
                        if (disp === mQ && lvl === 0) {
                            var isRev = true;
                            for (k = 0; k < mQ; k++) { if (pr2[k] !== mQ - 1 - k) { isRev = false; break; } }
                            if (isRev) { break; }
                        }
                    }
                }
                if (mode === "rnd") {
                    var pool = feasStrict.length ? feasStrict : feasComp;
                    if (pool.length > 0) { best = pool[Math.floor(rng() * pool.length)]; }
                }
                if (best !== null) {
                    for (k = 0; k < mQ; k++) { assign[grp[k].slotKey] = contents[best[k]]; }
                }
            }
            assigns.push(assign);
        }

        // -----------------------------------------------------
        // 9) FAZ 2 — sayfalar arası tekil takas (aynı bölüm+bölge+şekil)
        // -----------------------------------------------------
        var exchLog = [];
        if (chkXPage.value && mode !== "col") {
            for (var pass2 = 0; pass2 < 2; pass2++) {
                var stuck = [];
                for (k = 0; k < allSlots.length; k++) {
                    var S0 = allSlots[k];
                    if (S0.grup === 0 && assigns[S0.pdIdx][S0.slotKey] === S0) { stuck.push(S0); }
                }
                for (i = 0; i < stuck.length; i++) {
                    var S = stuck[i];
                    if (assigns[S.pdIdx][S.slotKey] !== S) { continue; }
                    var contS = assigns[S.pdIdx][S.slotKey];
                    var cands = [];
                    for (j = 0; j < allSlots.length; j++) {
                        var T = allSlots[j];
                        if (T.pdIdx === S.pdIdx || T.grup !== 0) { continue; }
                        if (T.sec !== S.sec || T.zone !== S.zone || T.shape !== S.shape) { continue; }
                        if (T.pool !== S.pool) { continue; }  // özel havuzlar yalnız kendi içinde
                        var contT0 = assigns[T.pdIdx][T.slotKey];
                        var dh = contS.h - contT0.h; if (dh < 0) { dh = -dh; }
                        var dp = T.pdIdx - S.pdIdx; if (dp < 0) { dp = -dp; }
                        cands.push({ pri: (contT0 === T ? 0 : 1), dh: dh, dp: dp, num: T.num, T: T });
                    }
                    cands.sort(function (a, b) {
                        return (a.pri - b.pri) || (a.dh - b.dh) || (a.dp - b.dp) || (a.num - b.num);
                    });
                    var done = false;
                    for (var sPass = 0; sPass < 2 && !done; sPass++) {
                        for (j = 0; j < cands.length; j++) {
                            var T2 = cands[j].T;
                            var contT = assigns[T2.pdIdx][T2.slotKey];
                            var tA = copyAssign(assigns[S.pdIdx]); tA[S.slotKey] = contT;
                            var tB = copyAssign(assigns[T2.pdIdx]); tB[T2.slotKey] = contS;
                            var la = fitLevel(pageData[S.pdIdx], tA);
                            var lb = fitLevel(pageData[T2.pdIdx], tB);
                            if (la < 0 || lb < 0) { continue; }
                            if (sPass === 0 && (la > 0 || lb > 0)) { continue; }
                            assigns[S.pdIdx][S.slotKey] = contT;
                            assigns[T2.pdIdx][T2.slotKey] = contS;
                            exchLog.push("Test " + (S.sec + 1) + ": A" + contS.num + " (s." + pageData[S.pdIdx].name +
                                         ") \u2194 A" + contT.num + " (s." + pageData[T2.pdIdx].name + ")");
                            done = true; break;
                        }
                    }
                }
            }
            if (exchLog.length > 0) {
                log("Sayfalar arası takas (" + exchLog.length + "): " + exchLog.join("  |  "));
            }
        }

        // -----------------------------------------------------
        // 10) FAZ 2b — TAM SAYFA (blok) TAKASI  (v4.2)
        //     Tek-bölgeli testlerde, hâlâ yerinde kalan soru için
        //     iki sayfanın tüm soru bandı takas edilir.
        // -----------------------------------------------------
        var bundleSecs = {};   // renumaralanacak bölümler
        var bundleLog = [];
        function pageSlots(pdi) {
            var out = [];
            pageQuestionWalk(pageData[pdi], function (r) { if (r.kind === "soru") { out.push(r); } });
            return out;
        }
        // Sayfanın GÜNCEL atamalarıyla bant bilgisi: yerleşim gerçek yükseklikle ölçülür.
        function pageBundleInfo(pdi) {
            var qs = pageSlots(pdi);
            if (qs.length === 0) { return null; }
            var sec = qs[0].sec, top = qs[0].y1, bot = qs[0].y2;
            for (var q = 0; q < qs.length; q++) {
                if (qs[q].sec !== sec || qs[q].zone !== 0 || qs[q].grup !== 0 || qs[q].pool !== 0) { return null; }
                if (qs[q].y1 < top) { top = qs[q].y1; }
                if (qs[q].y2 > bot) { bot = qs[q].y2; }
            }
            var tail = [];
            for (var t3 = 0; t3 < pageData[pdi].items.length; t3++) {
                var itX = pageData[pdi].items[t3];
                if (itX.kind === "soru") { continue; }
                var mid = (itX.y1 + itX.y2) / 2;
                if (mid > top - 2 && mid < bot + 2) { return null; }
                if (itX.y1 >= bot - 2) { tail.push(itX); }
            }
            // güncel atamalarla yerleşim (kendi sayfasında)
            var lvl = fitLevel(pageData[pdi], assigns[pdi]);
            if (lvl < 0) { return null; }
            var plcB = tryLayoutScale(pageData[pdi], assigns[pdi], SCALES[lvl]);
            var aBot = top;
            for (var q2 = 0; q2 < plcB.length; q2++) {
                var b3 = plcB[q2].ny1 + plcB[q2].cont.h;
                if (b3 > aBot) { aBot = b3; }
            }
            return { sec: sec, top: top, bot: bot, aBot: aBot, aH: aBot - top,
                     qs: qs, tail: tail, pdi: pdi, plc: plcB };
        }
        function tailFits(info, newBot) {
            for (var t4 = 0; t4 < info.tail.length; t4++) {
                var nt5 = newBot + (info.tail[t4].y1 - info.bot);
                if (nt5 + (info.tail[t4].y2 - info.tail[t4].y1) > pageData[info.pdi].HB + 0.5) { return false; }
            }
            return true;
        }
        // v4.18: sayfadaki soru çerçevelerinin en soldaki kenarı (sütun düzeninin x başlangıcı)
        function bundleLeftEdge(info) {
            var mx = null;
            for (var q5 = 0; q5 < info.qs.length; q5++) {
                if (mx === null || info.qs[q5].fx1 < mx) { mx = info.qs[q5].fx1; }
            }
            return mx;
        }
        if (chkBundle.value && mode !== "col") {
            var stillB = [];
            for (k = 0; k < allSlots.length; k++) {
                var Sb = allSlots[k];
                if (Sb.grup === 0 && assigns[Sb.pdIdx][Sb.slotKey] === Sb) { stillB.push(Sb); }
            }
            for (i = 0; i < stillB.length; i++) {
                var Sb2 = stillB[i];
                if (assigns[Sb2.pdIdx][Sb2.slotKey] !== Sb2) { continue; }
                if (pageData[Sb2.pdIdx].bundleWith >= 0) { continue; }
                var infS = pageBundleInfo(Sb2.pdIdx);
                if (infS === null || noBundleSec[infS.sec]) { continue; }
                var bestB = null;
                for (j = 0; j < pageData.length; j++) {
                    if (j === Sb2.pdIdx || pageData[j].bundleWith >= 0) { continue; }
                    var infT = pageBundleInfo(j);
                    if (infT === null || infT.sec !== infS.sec) { continue; }
                    // karşılıklı sığma: gerçek yerleşim yüksekliğiyle
                    if (infT.top + infS.aH > pageData[j].HB + 0.5) { continue; }
                    if (infS.top + infT.aH > pageData[Sb2.pdIdx].HB + 0.5) { continue; }
                    if (!tailFits(infT, infT.top + infS.aH)) { continue; }
                    if (!tailFits(infS, infS.top + infT.aH)) { continue; }
                    if (isMiddleSchool) {
                        // v4.18: blok, KAYNAK sayfanın x konumlarıyla yerleştirilir. İç/dış kenar
                        // boşluğu farklı karşılıklı sayfalarda sol ve sağ sayfanın sütunları farklı
                        // x'te durur; blok yatayda kayar ve bekçi bunu bindirme saymaz.
                        // Sütun başlangıcı iki sayfada farklıysa blok takası yapılmaz.
                        var dxB = bundleLeftEdge(infS) - bundleLeftEdge(infT);
                        if (dxB > 3 || dxB < -3) { continue; }
                        // v4.15: blok nakli hedef sayfada 2D zarf denetiminden geçmeli
                        var msOK = true, pqB, pseudoB;
                        pseudoB = [];
                        for (pqB = 0; pqB < infS.plc.length; pqB++) {
                            pseudoB.push({ slot: { x1: infS.plc[pqB].slot.x1 },
                                           cont: infS.plc[pqB].cont,
                                           ny1: infS.plc[pqB].ny1 + (infT.top - infS.top) });
                        }
                        if (!middleSchoolLayoutSafe(pageData[j], pseudoB)) { msOK = false; }
                        if (msOK) {
                            pseudoB = [];
                            for (pqB = 0; pqB < infT.plc.length; pqB++) {
                                pseudoB.push({ slot: { x1: infT.plc[pqB].slot.x1 },
                                               cont: infT.plc[pqB].cont,
                                               ny1: infT.plc[pqB].ny1 + (infS.top - infT.top) });
                            }
                            if (!middleSchoolLayoutSafe(pageData[Sb2.pdIdx], pseudoB)) { msOK = false; }
                        }
                        if (!msOK) { continue; }
                    }
                    var dhB = infS.aH - infT.aH; if (dhB < 0) { dhB = -dhB; }
                    var dpB = j - Sb2.pdIdx; if (dpB < 0) { dpB = -dpB; }
                    if (bestB === null || dhB < bestB.dh || (dhB === bestB.dh && dpB < bestB.dp)) {
                        bestB = { dh: dhB, dp: dpB, inf: infT };
                    }
                }
                if (bestB !== null) {
                    var infT2 = bestB.inf;
                    pageData[Sb2.pdIdx].bundleWith = infT2.pdi;
                    pageData[infT2.pdi].bundleWith = Sb2.pdIdx;
                    pageData[Sb2.pdIdx].bundleInfo = infS;
                    pageData[infT2.pdi].bundleInfo = infT2;
                    bundleSecs[infS.sec] = true;
                    bundleLog.push("Test " + (infS.sec + 1) + ": s." + pageData[Sb2.pdIdx].name +
                                   " \u2194 s." + pageData[infT2.pdi].name + " (tüm sorular blok hâlinde)");
                }
            }
            if (bundleLog.length > 0) { log("Tam sayfa takası (" + bundleLog.length + "): " + bundleLog.join("  |  ")); }
        }

        // -----------------------------------------------------
        // 11) FAZ 3 — uygula (önce yerleştir, SONRA denetle, SONRA numarala)
        // -----------------------------------------------------
        // Her içerik için nihai hedef: {tf, cont, page, ny1, nx1, order}
        var finalPlace = [];      // sayfa bazlı gruplanmış
        var pagePlans = [];       // [pi] -> {list:[{cont, ny1, nx1}], isBundle}

        for (pi = 0; pi < pageData.length; pi++) { pagePlans.push(null); }

        for (pi = 0; pi < pageData.length; pi++) {
            var pdP = pageData[pi];
            if (pdP.bundleWith >= 0) {
                if (pdP.bundleWith < pi) { continue; } // çift, ilk görüldüğünde işlendi
                var A1 = pdP.bundleInfo, B1 = pageData[pdP.bundleWith].bundleInfo;
                // A sayfası B'nin GÜNCEL yerleşimini, B sayfası A'nınkini alır
                // (kaynak iç düzen ve atanmış içerikler korunur, üst kenar hedef banda oturur)
                var planA = { list: [], isBundle: true, tailMoves: [] };
                var planB = { list: [], isBundle: true, tailMoves: [] };
                var dyToA = A1.top - B1.top;
                var dyToB = B1.top - A1.top;
                for (k = 0; k < B1.plc.length; k++) {
                    planA.list.push({ cont: B1.plc[k].cont, ny1: B1.plc[k].ny1 + dyToA,
                                      nx1: B1.plc[k].slot.x1, ord: k });
                }
                for (k = 0; k < A1.plc.length; k++) {
                    planB.list.push({ cont: A1.plc[k].cont, ny1: A1.plc[k].ny1 + dyToB,
                                      nx1: A1.plc[k].slot.x1, ord: k });
                }
                var newBotA = A1.top + B1.aH;
                for (k = 0; k < A1.tail.length; k++) {
                    planA.tailMoves.push({ it: A1.tail[k], ny1: newBotA + (A1.tail[k].y1 - A1.bot) });
                }
                var newBotB = B1.top + A1.aH;
                for (k = 0; k < B1.tail.length; k++) {
                    planB.tailMoves.push({ it: B1.tail[k], ny1: newBotB + (B1.tail[k].y1 - B1.bot) });
                }
                pagePlans[A1.pdi] = planA;
                pagePlans[B1.pdi] = planB;
            } else {
                var lvlP = fitLevel(pdP, assigns[pi]);
                if (lvlP < 0) {
                    log("KRİTİK: Sayfa " + pdP.name + " yerleşimi doğrulanamadı; sayfa değiştirilmedi.");
                    continue;
                }
                var placements = tryLayoutScale(pdP, assigns[pi], SCALES[lvlP]);
                var planN = { list: [], isBundle: false, scale: SCALES[lvlP], slotOf: [] };
                for (k = 0; k < placements.length; k++) {
                    planN.list.push({ cont: placements[k].cont, ny1: placements[k].ny1,
                                      nx1: placements[k].slot.x1, slot: placements[k].slot });
                }
                pagePlans[pi] = planN;
                if (SCALES[lvlP] < 1.0) {
                    log("Bilgi: s." + pdP.name + " boşluklar %" + Math.round(SCALES[lvlP] * 100) + " ölçeğinde sıkıştırıldı.");
                }
            }
        }

        // Yerleştir (mutlak konum; sayfa değişimi move ile)
        var movedCount = 0, xPageMoves = 0;
        for (pi = 0; pi < pageData.length; pi++) {
            var plan = pagePlans[pi];
            if (plan === null) { continue; }
            for (k = 0; k < plan.list.length; k++) {
                var pe = plan.list[k];
                var needs = (pe.cont.page !== pi) ||
                            (pe.nx1 - pe.cont.x1 > 0.01) || (pe.nx1 - pe.cont.x1 < -0.01) ||
                            (pe.ny1 - pe.cont.y1 > 0.01) || (pe.ny1 - pe.cont.y1 < -0.01);
                if (!needs) { continue; }
                if (pe.cont.page !== pi) { pe.cont.tf.move(pages[pi]); xPageMoves++; }
                var offT = pe.cont.fy1 - pe.cont.y1;
                var offL = pe.cont.fx1 - pe.cont.x1;
                var w0 = pe.cont.fx2 - pe.cont.fx1, h0 = pe.cont.fy2 - pe.cont.fy1;
                try {
                    var gbNow = pe.cont.tf.geometricBounds;
                    w0 = gbNow[3] - gbNow[1]; h0 = gbNow[2] - gbNow[0];
                } catch (eG) {}
                pe.cont.tf.geometricBounds = [pe.ny1 + offT, pe.nx1 + offL,
                                              pe.ny1 + offT + h0, pe.nx1 + offL + w0];
                movedCount++;
            }
            if (plan.isBundle) {
                for (k = 0; k < plan.tailMoves.length; k++) {
                    var tm = plan.tailMoves[k];
                    var hT2 = tm.it.y2 - tm.it.y1;
                    try { tm.it.tf.geometricBounds = [tm.ny1, tm.it.x1, tm.ny1 + hT2, tm.it.x2]; } catch (eT) {}
                }
            }
        }
        log("Yerleştirme: " + movedCount + " çerçeve taşındı (" + xPageMoves + " tanesi sayfa değiştirdi).");

        // -----------------------------------------------------
        // 12) BİNDİRME DENETİMİ + GERİ ALMA (numaralamadan ÖNCE)
        // -----------------------------------------------------
        function rectsOverlap(a, b) {
            return !(a[2] <= b[0] + 1 || b[2] <= a[0] + 1 || a[3] <= b[1] + 1 || b[3] <= a[1] + 1);
        }
        function auditPage(pi2) {
            var plan2 = pagePlans[pi2];
            if (plan2 === null) { return true; }
            var contRects = [];
            for (var q2 = 0; q2 < plan2.list.length; q2++) {
                var c3 = plan2.list[q2].cont;
                var gb3;
                try { gb3 = c3.tf.geometricBounds; } catch (eR) { continue; }
                var oT = c3.fy1 - c3.y1, oL = c3.fx1 - c3.x1;
                contRects.push([gb3[0] - oT, gb3[1] - oL,
                                gb3[0] - oT + (c3.y2 - c3.y1), gb3[1] - oL + (c3.x2 - c3.x1),
                                "S" + c3.num]);
            }
            // orijinal soru zarfları (sabitin A'da zaten soruya değip değmediği için)
            var origQ0 = [];
            for (var t5 = 0; t5 < pageData[pi2].items.length; t5++) {
                var iq0 = pageData[pi2].items[t5];
                if (iq0.kind === "soru") { origQ0.push([iq0.y1, iq0.x1, iq0.y2, iq0.x2]); }
            }
            function dOv0(a, b) {
                var dv = ((a[2] < b[2]) ? a[2] : b[2]) - ((a[0] > b[0]) ? a[0] : b[0]);
                var dh = ((a[3] < b[3]) ? a[3] : b[3]) - ((a[1] > b[1]) ? a[1] : b[1]);
                return (dv > 3 && dh > 3);
            }
            var fixRects = [];
            for (t5 = 0; t5 < pageData[pi2].items.length; t5++) {
                var itA = pageData[pi2].items[t5];
                if (itA.kind === "soru") { continue; }
                var gb4;
                try { gb4 = itA.tf.geometricBounds; } catch (eR2) { continue; }
                var touch = false;
                var fr0 = [itA.y1, itA.x1, itA.y2, itA.x2];
                for (var o5 = 0; o5 < origQ0.length; o5++) {
                    if (dOv0(fr0, origQ0[o5])) { touch = true; break; }
                }
                fixRects.push([gb4[0], gb4[1], gb4[2], gb4[3],
                               "[" + itA.kind + " \u2018" + itA.etiket + "\u2019 y" +
                               Math.round(itA.y1) + ".." + Math.round(itA.y2) + "]", touch]);
            }
            // içerik × içerik → geri al (kanıtlı felaket)
            for (var a2 = 0; a2 < contRects.length; a2++) {
                for (var b2i = a2 + 1; b2i < contRects.length; b2i++) {
                    if (rectsOverlap(contRects[a2], contRects[b2i])) {
                        log("KRİTİK: s." + pageData[pi2].name + " bindirme saptandı (" +
                            contRects[a2][4] + " × " + contRects[b2i][4] + ") — sayfa A düzenine geri alındı.");
                        return false;
                    }
                }
                if (contRects[a2][2] > pageData[pi2].HB + 2) {
                    log("KRİTİK: s." + pageData[pi2].name + " taşma saptandı (" + contRects[a2][4] + ") — sayfa geri alındı.");
                    return false;
                }
                // içerik × sabit: sabit A'da zaten bir soruya değiyorsa tasarım gereğidir → UYARI
                for (var f2 = 0; f2 < fixRects.length; f2++) {
                    if (rectsOverlap(contRects[a2], fixRects[f2])) {
                        if (fixRects[f2][5]) {
                            log("UYARI: s." + pageData[pi2].name + " — " + contRects[a2][4] + " ile " +
                                fixRects[f2][4] + " kesişiyor (A'da da temas eden dekor); baskı öncesi göz atın.");
                        } else {
                            log("KRİTİK: s." + pageData[pi2].name + " bindirme saptandı (" +
                                contRects[a2][4] + " × " + fixRects[f2][4] + ") — sayfa A düzenine geri alındı.");
                            return false;
                        }
                    }
                }
            }
            // sabit × sabit A'nın kendi tasarımıdır; denetlenmez.
            // v4.4: GRUPLARIN İÇİNDEKİ metinler dahil tüm sayfa metin çerçeveleri
            // engel sayılır (A'da zaten bir soruya değenler hariç — soru montajı).
            var placedIds = {};
            for (q2 = 0; q2 < plan2.list.length; q2++) {
                var cP = plan2.list[q2].cont;
                try { placedIds[cP.tf.id] = true; } catch (eI1) {}
                try {
                    var kidsP = cP.tf.allPageItems;
                    for (var kP = 0; kP < kidsP.length; kP++) { placedIds[kidsP[kP].id] = true; }
                } catch (eI1b) {}
                try {
                    var ancP = (cP.numTf || cP.tf).parentStory.pageItems;
                    for (var aP = 0; aP < ancP.length; aP++) {
                        placedIds[ancP[aP].id] = true;
                        try {
                            var sub2 = ancP[aP].allPageItems;
                            for (var s2 = 0; s2 < sub2.length; s2++) { placedIds[sub2[s2].id] = true; }
                        } catch (eI2b) {}
                    }
                } catch (eI2) {}
            }
            for (var t7 = 0; t7 < pageData[pi2].items.length; t7++) {
                try { placedIds[pageData[pi2].items[t7].tf.id] = true; } catch (eI3) {}
                try {
                    var kidsN = pageData[pi2].items[t7].tf.allPageItems;
                    for (var kN = 0; kN < kidsN.length; kN++) { placedIds[kidsN[kN].id] = true; }
                } catch (eI3b) {}
                try {
                    var ancN = (pageData[pi2].items[t7].numTf || pageData[pi2].items[t7].tf).parentStory.pageItems;
                    for (var aN = 0; aN < ancN.length; aN++) {
                        placedIds[ancN[aN].id] = true;
                        try {
                            var sub3 = ancN[aN].allPageItems;
                            for (var s3 = 0; s3 < sub3.length; s3++) { placedIds[sub3[s3].id] = true; }
                        } catch (eI3d) {}
                    }
                } catch (eI3c) {}
            }
            for (var ig in pageData[pi2].ignoredIds) { placedIds[ig] = true; }
            var origQ = [];
            for (t7 = 0; t7 < pageData[pi2].items.length; t7++) {
                var iq = pageData[pi2].items[t7];
                if (iq.kind === "soru") { origQ.push([iq.y1, iq.x1, iq.y2, iq.x2]); }
            }
            function deepOv(a, b) {
                var dv = ((a[2] < b[2]) ? a[2] : b[2]) - ((a[0] > b[0]) ? a[0] : b[0]);
                var dh = ((a[3] < b[3]) ? a[3] : b[3]) - ((a[1] > b[1]) ? a[1] : b[1]);
                return (dv > 3 && dh > 3);
            }
            var obst;
            try { obst = pages[pi2].allPageItems; } catch (eO0) { obst = []; }
            for (var o1 = 0; o1 < obst.length; o1++) {
                if (obst[o1].constructor.name !== "TextFrame") { continue; }
                var oid = -1;
                try { oid = obst[o1].id; } catch (eO1) {}
                if (placedIds[oid]) { continue; }
                var ogb;
                try { ogb = obst[o1].geometricBounds; } catch (eO2) { continue; }
                var wasPart = false;
                for (var o2 = 0; o2 < origQ.length; o2++) {
                    if (deepOv(ogb, origQ[o2])) { wasPart = true; break; }
                }
                if (wasPart) { continue; }
                for (q2 = 0; q2 < plan2.list.length; q2++) {
                    var cE = plan2.list[q2].cont;
                    var gbE;
                    try { gbE = cE.tf.geometricBounds; } catch (eO3) { continue; }
                    var oTE = cE.fy1 - cE.y1, oLE = cE.fx1 - cE.x1;
                    var env = [gbE[0] - oTE, gbE[1] - oLE,
                               gbE[0] - oTE + (cE.y2 - cE.y1), gbE[1] - oLE + (cE.x2 - cE.x1)];
                    if (deepOv(ogb, env)) {
                        var oTxt = "";
                        try { oTxt = trimS(String(obst[o1].parentStory.texts[0].contents)).substr(0, 18); } catch (eO4) {}
                        log("UYARI: s." + pageData[pi2].name + " — S" + cE.num +
                            " sayfadaki \u2018" + oTxt + "\u2019 metniyle (y" + Math.round(ogb[0]) + ".." +
                            Math.round(ogb[2]) + ") kesişiyor olabilir; baskı öncesi göz atın.");
                        o1 = obst.length; break; // sayfa başına tek uyarı; İPTAL YOK
                    }
                }
            }
            return true;
        }
        function restorePage(pi3) {
            var plan3 = pagePlans[pi3];
            if (plan3 === null) { return; }
            for (var q3 = 0; q3 < plan3.list.length; q3++) {
                var c4 = plan3.list[q3].cont;
                if (c4.page !== pi3) {
                    try { c4.tf.move(pages[c4.page]); } catch (eMv) {}
                }
                try { c4.tf.geometricBounds = [c4.fy1, c4.fx1, c4.fy2, c4.fx2]; } catch (eGb) {}
            }
            if (plan3.isBundle) {
                for (var t6 = 0; t6 < plan3.tailMoves.length; t6++) {
                    var it6 = plan3.tailMoves[t6].it;
                    try { it6.tf.geometricBounds = [it6.fy1, it6.fx1, it6.fy2, it6.fx2]; } catch (eGb2) {}
                }
            }
            pagePlans[pi3] = null;
        }
        // v4.11: TAKAS-ATOMİK GERİ ALMA — bir sayfa iptal ediliyorsa, onunla
        // içerik alışverişi yapan tüm sayfalar KAPANIŞ KÜMESİ olarak birlikte
        // geri alınır. (Tek kanatlı iptal, karşı sayfada çift soru bırakıyordu.)
        var failed = {};
        for (pi = 0; pi < pageData.length; pi++) {
            if (pagePlans[pi] === null) { continue; }
            if (!auditPage(pi)) { failed[pi] = true; }
        }
        var grew = true;
        while (grew) {
            grew = false;
            for (pi = 0; pi < pageData.length; pi++) {
                if (pagePlans[pi] === null) { continue; }
                var inSet = failed[pi] === true;
                // bundle eşi her zaman birlikte
                if (inSet && pageData[pi].bundleWith >= 0 && !failed[pageData[pi].bundleWith]) {
                    failed[pageData[pi].bundleWith] = true; grew = true;
                }
                for (k = 0; k < pagePlans[pi].list.length; k++) {
                    var cc = pagePlans[pi].list[k].cont;
                    if (inSet) {
                        // (a) bu sayfanın planındaki yabancı içeriğin kaynağı da geri alınmalı
                        if (cc.page !== pi && pagePlans[cc.page] !== null && !failed[cc.page]) {
                            failed[cc.page] = true; grew = true;
                        }
                    } else if (failed[cc.page]) {
                        // (b) geri alınan bir sayfanın yerlisini barındıran sayfa da geri alınmalı
                        failed[pi] = true; grew = true; break;
                    }
                }
            }
        }
        var reverted = 0, closureExtra = [];
        for (pi = 0; pi < pageData.length; pi++) {
            if (!failed[pi] || pagePlans[pi] === null) { continue; }
            restorePage(pi);
            if (pageData[pi].bundleWith >= 0) { pageData[pi].bundleWith = -1; }
            reverted++;
            closureExtra.push("s." + pageData[pi].name);
        }
        if (reverted > 1) {
            log("Takas bütünlüğü için birlikte geri alınanlar: " + closureExtra.join(", "));
        }
        if (reverted > 0) { log("Geri alınan sayfa/çift: " + reverted + " — CSV'deki KRİTİK satırlarına bakın."); }

        // v4.15 İKİNCİ ŞANS: geri alınan sayfalar A'da kalmasın — yalnız
        // sayfa-içi, sıkıştırmasız güvenli karışım denenir ve bekçiden
        // geçerse kabul edilir.
        function strictPlc(pdX, assignX) {
            var pX = tryLayoutScale(pdX, assignX, 1.0);
            if (pX === null) { return null; }
            if (isMiddleSchool && !middleSchoolLayoutSafe(pdX, pX)) { return null; }
            return pX;
        }
        var rescued = [];
        for (pi = 0; pi < pageData.length; pi++) {
            if (!failed[pi]) { continue; }
            var pdR = pageData[pi];
            var slotsR = [];
            pageQuestionWalk(pdR, function (r) { if (r.kind === "soru") { slotsR.push(r); } });
            if (slotsR.length < 2) { continue; }
            var aR = {};
            for (k = 0; k < slotsR.length; k++) { aR[slotsR[k].slotKey] = slotsR[k]; }
            var groupsR = {}, gkR = [];
            for (k = 0; k < slotsR.length; k++) {
                var gkey = slotsR[k].sec + "|" + slotsR[k].zone + "|" + slotsR[k].shape + "|" +
                           slotsR[k].grup + "|" + slotsR[k].pool;
                if (!groupsR[gkey]) { groupsR[gkey] = []; gkR.push(gkey); }
                groupsR[gkey].push(slotsR[k]);
            }
            var anyPerm = false;
            for (var gR = 0; gR < gkR.length; gR++) {
                var grpR = groupsR[gkR[gR]];
                var mR2 = grpR.length;
                if (mR2 < 2 || grpR[0].grup > 0) { continue; }
                var contsR = grpR.slice(0);
                var permsR;
                if (mR2 <= 7) { permsR = allPerms(mR2); }
                else {
                    permsR = [[]];
                    for (k = 0; k < mR2; k++) { permsR[0].push(mR2 - 1 - k); }
                }
                var bestR = null, bD = -1, bS = -1;
                for (var pR = 0; pR < permsR.length; pR++) {
                    var prR = permsR[pR];
                    var tR = copyAssign(aR);
                    for (k = 0; k < mR2; k++) { tR[grpR[k].slotKey] = contsR[prR[k]]; }
                    if (strictPlc(pdR, tR) === null) { continue; }
                    var dR = 0, sR = 0;
                    for (k = 0; k < mR2; k++) {
                        if (prR[k] !== k) { dR++; }
                        sR += (prR[k] > k) ? (prR[k] - k) : (k - prR[k]);
                    }
                    if (dR > bD || (dR === bD && sR > bS)) { bestR = prR; bD = dR; bS = sR; }
                }
                if (bestR !== null && bD > 0) {
                    for (k = 0; k < mR2; k++) { aR[grpR[k].slotKey] = contsR[bestR[k]]; }
                    anyPerm = true;
                }
            }
            if (!anyPerm) { continue; }
            var plcR = strictPlc(pdR, aR);
            if (plcR === null) { continue; }
            var planR = { list: [], isBundle: false };
            for (k = 0; k < plcR.length; k++) {
                planR.list.push({ cont: plcR[k].cont, ny1: plcR[k].ny1,
                                  nx1: plcR[k].slot.x1, slot: plcR[k].slot });
            }
            for (k = 0; k < planR.list.length; k++) {
                var peR = planR.list[k];
                var nd = (peR.nx1 - peR.cont.x1 > 0.01) || (peR.nx1 - peR.cont.x1 < -0.01) ||
                         (peR.ny1 - peR.cont.y1 > 0.01) || (peR.ny1 - peR.cont.y1 < -0.01);
                if (!nd) { continue; }
                var oTR = peR.cont.fy1 - peR.cont.y1, oLR = peR.cont.fx1 - peR.cont.x1;
                var wR = peR.cont.fx2 - peR.cont.fx1, hR = peR.cont.fy2 - peR.cont.fy1;
                try {
                    var gbR = peR.cont.tf.geometricBounds;
                    wR = gbR[3] - gbR[1]; hR = gbR[2] - gbR[0];
                } catch (eGR) {}
                peR.cont.tf.geometricBounds = [peR.ny1 + oTR, peR.nx1 + oLR,
                                               peR.ny1 + oTR + hR, peR.nx1 + oLR + wR];
            }
            pagePlans[pi] = planR;
            if (auditPage(pi)) {
                var mvR = 0;
                for (k = 0; k < planR.list.length; k++) {
                    if (planR.list[k].cont !== planR.list[k].slot) { mvR++; }
                }
                rescued.push("s." + pdR.name + " (" + mvR + " soru)");
            } else {
                restorePage(pi);
            }
        }
        if (rescued.length > 0) {
            log("İkinci deneme — sayfa-içi güvenli karışımla kurtarıldı: " + rescued.join(", "));
        }

        // -----------------------------------------------------
        // 13) NUMARALANDIRMA ve EŞLEME
        //     Normal sayfalar: slot numarası içeriğe yazılır.
        //     Blok takaslı bölümler: bölüm baştan sıralı numaralanır.
        // -----------------------------------------------------
        // bundle iptal olduysa bölümü yeniden numaralamaya gerek kalmayabilir;
        // yine de bundleSecs'te kalan bölümler için güvenli tam numaralama yapılır.
        var mapping = [];
        function writeNum(contRec, newNum) {
            if (contRec.num === newNum) { return true; }
            clearGrep();
            app.findGrepPreferences.findWhat = "\\d{1,3}(?=\\.)";
            var found = (contRec.numTf || contRec.tf).parentStory.paragraphs[0].findGrep();
            clearGrep();
            if (found.length > 0) { found[0].contents = String(newNum); return true; }
            return false;
        }

        // bölüm bazlı: bundle'lı bölümlerde tam sıralı numaralandırma
        var counters = [];
        for (k = 0; k < totalSections; k++) { counters.push(0); }

        for (pi = 0; pi < pageData.length; pi++) {
            var planM = pagePlans[pi];
            if (planM === null) {
                // değişmemiş sayfa: eşleme kimlik olarak yazılır
                pageQuestionWalk(pageData[pi], function (r) {
                    if (r.kind !== "soru") { return; }
                    var nn0;
                    if (bundleSecs[r.sec]) { counters[r.sec]++; nn0 = counters[r.sec]; }
                    else { nn0 = r.num; counters[r.sec] = nn0; }
                    if (nn0 !== r.num) {
                        if (!writeNum(r, nn0)) { log("UYARI: S" + r.num + " numarası bulunamadı (s." + pageData[pi].name + ")."); }
                    }
                    mapping.push({ sec: r.sec, oldNum: r.num, oldPage: pageData[r.page].name,
                                   newNum: nn0, newPage: pageData[pi].name, ans: r.ans, shape: r.shape,
                                   keySkip: (r.keySkip === true) });
                });
                continue;
            }
            // planlı sayfa: içerikler plan.list sırasıyla (bundle: kaynak düzen sırası;
            // normal: slot okuma sırası zaten)
            for (k = 0; k < planM.list.length; k++) {
                var peM = planM.list[k];
                var cM = peM.cont;
                var nn;
                if (planM.isBundle || bundleSecs[cM.sec]) {
                    counters[cM.sec]++;
                    nn = counters[cM.sec];
                } else {
                    nn = peM.slot.num;
                    counters[cM.sec] = nn;
                }
                if (!writeNum(cM, nn)) { log("UYARI: S" + cM.num + " numarası bulunamadı (s." + pageData[pi].name + ")."); }
                mapping.push({ sec: cM.sec, oldNum: cM.num, oldPage: pageData[cM.page].name,
                               newNum: nn, newPage: pageData[pi].name, ans: cM.ans, shape: cM.shape,
                               keySkip: (cM.keySkip === true) });
            }
        }

        // bütünlük denetimi + yerinde kalan raporu
        var chkArr = [];
        for (k = 0; k < totalSections; k++) { chkArr.push({}); }
        var stillList = [];
        for (k = 0; k < mapping.length; k++) {
            chkArr[mapping[k].sec][mapping[k].newNum] = true;
            if (mapping[k].oldNum === mapping[k].newNum && mapping[k].oldPage === mapping[k].newPage) {
                stillList.push("Test " + (mapping[k].sec + 1) + " S" + mapping[k].newNum +
                               (mapping[k].shape === "FW" ? " (tam genişlik)" : ""));
            }
        }
        for (k = 0; k < totalSections; k++) {
            var eks = [];
            for (i = 1; i <= (secQCount[k] || 0); i++) { if (!chkArr[k][i]) { eks.push(i); } }
            if (eks.length > 0) { log("KRİTİK: Test " + (k + 1) + " numara dizisinde eksik: " + eks.join(",")); }
        }
        if (stillList.length > 0) {
            log("Yerinde kalanlar (" + stillList.length + "): " + stillList.join(", "));
        } else if (mapping.length > 0) {
            log("Tüm sorular yer değiştirdi.");
        }

        // -----------------------------------------------------
        // 14) KİTAPÇIK HARFİ A→B (Bölüm İşareti + master bant)
        // -----------------------------------------------------
        if (chkMarker.value) {
            var chg = 0;
            for (k = 0; k < doc.sections.length; k++) {
                var sec = doc.sections[k];
                var mk = String(sec.marker);
                if (/A/.test(mk)) {
                    // v4.18: yalnız tek başına duran A değişir; "KİMYA"/"COĞRAFYA" gibi
                    // A ile biten kelimeler artık "KİMYB" olmaz ("1A" → "1B" korunur).
                    var nmk = mk.replace(/(^|[^A-Za-zÇĞİÖŞÜçğıöşü])A(?![0-9A-Za-zÇĞİÖŞÜçğıöşü])/g, "$1B");
                    if (nmk !== mk) { sec.marker = nmk; chg++; log("Bölüm işareti: \u201C" + mk + "\u201D → \u201C" + nmk + "\u201D"); }
                }
            }
            var bandChg = 0;
            try {
                var BAND_RE = /^A([\s\u00A0\u2000-\u200B\u202F\u205F\u3000]+A)*$/;
                for (k = 0; k < doc.masterSpreads.length; k++) {
                    var msItems = doc.masterSpreads[k].allPageItems;
                    for (i = 0; i < msItems.length; i++) {
                        if (msItems[i].constructor.name !== "TextFrame") { continue; }
                        var stM = null;
                        try { stM = msItems[i].parentStory; } catch (eS1) { continue; }
                        var cM2 = trimS(String(stM.texts[0].contents));
                        if (BAND_RE.test(cM2)) {
                            stM.texts[0].contents = cM2.replace(/A/g, "B");
                            bandChg++;
                        }
                    }
                }
            } catch (eMS) {}
            if (bandChg > 0) { log("Master üst bant: " + bandChg + " çerçevede A→B yapıldı."); }
            if (chg === 0 && bandChg === 0) { log("Bilgi: A içeren bölüm işareti/master bant bulunamadı."); }
        }

        // -----------------------------------------------------
        // 15) CEVAP ANAHTARI BLOĞU
        // -----------------------------------------------------
        if (chkKey.value) {
            var newLetters = [], oldBySecNum = [];
            for (k = 0; k < totalSections; k++) { newLetters.push([]); oldBySecNum.push([]); }
            var keySkipN = 0;
            for (k = 0; k < mapping.length; k++) {
                var mp = mapping[k];
                if (mp.keySkip) { keySkipN++; continue; }
                newLetters[mp.sec][mp.newNum] = mp.ans;
                oldBySecNum[mp.sec][mp.oldNum] = mp.ans;
            }
            if (keySkipN > 0) {
                log("UYARI: " + keySkipN + " yinelenen-numaralı soru anahtar yazımından dışlandı — ilgili harfleri elle doğrulayın.");
            }
            clearGrep();
            app.findGrepPreferences.findWhat = "\\d{1,3}-[A-E]";
            var keyStory = null, bestC = 0;
            for (k = 0; k < doc.stories.length; k++) {
                var hits = doc.stories[k].findGrep();
                if (hits.length > bestC) { bestC = hits.length; keyStory = doc.stories[k]; }
            }
            clearGrep();
            if (keyStory !== null && bestC >= 20) {
                clearGrep();
                app.findGrepPreferences.findWhat = "(\\d{1,3})-([A-E])";
                var toks = keyStory.findGrep();
                clearGrep();
                // v4.18: soru içinden harfi okunamayan ("?") sorularda B anahtarında A'nın
                // o numaradaki harfi kalıyordu. Önce A anahtarı okunur; bu sorular için harf,
                // sorunun A numarasındaki anahtar harfinden eşlemeyle alınır.
                var aKey = [], oldNumOf = [];
                for (k = 0; k < totalSections; k++) { aKey.push([]); oldNumOf.push([]); }
                var secIdxA = -1;
                for (k = 0; k < toks.length; k++) {
                    var mmA = /^(\d{1,3})-([A-E])$/.exec(String(toks[k].contents));
                    if (!mmA) { continue; }
                    var numA = parseInt(mmA[1], 10);
                    if (numA === 1) { secIdxA++; }
                    if (secIdxA < 0 || secIdxA >= totalSections) { continue; }
                    if (!aKey[secIdxA][numA]) { aKey[secIdxA][numA] = mmA[2]; }
                }
                for (k = 0; k < mapping.length; k++) {
                    if (mapping[k].keySkip) { continue; }
                    oldNumOf[mapping[k].sec][mapping[k].newNum] = mapping[k].oldNum;
                }
                var secIdx = -1, updated = 0, mismatch = 0, fromKey = 0;
                for (k = 0; k < toks.length; k++) {
                    var mm2 = /^(\d{1,3})-([A-E])$/.exec(String(toks[k].contents));
                    if (!mm2) { continue; }
                    var num2 = parseInt(mm2[1], 10);
                    var oldL = mm2[2];
                    if (num2 === 1) { secIdx++; }
                    if (secIdx < 0 || secIdx >= totalSections) { continue; }
                    var expOld = oldBySecNum[secIdx][num2];
                    if (expOld && expOld !== "?" && expOld !== oldL) {
                        mismatch++;
                        log("KRİTİK — A uyuşmazlığı: Test " + (secIdx + 1) + " S" + num2 +
                            " soru içi \u201C" + expOld + "\u201D, blokta \u201C" + oldL + "\u201D.");
                    }
                    var newL = newLetters[secIdx][num2];
                    if (!newL || newL === "?") {
                        var oN = oldNumOf[secIdx][num2];
                        if (oN !== undefined && aKey[secIdx][oN]) { newL = aKey[secIdx][oN]; fromKey++; }
                    }
                    if (newL && newL !== "?" && newL !== oldL) {
                        toks[k].contents = num2 + "-" + newL;
                        updated++;
                    } else if (!newL || newL === "?") {
                        log("UYARI: Anahtar Test " + (secIdx + 1) + " S" + num2 + " için harf üretilemedi.");
                    }
                }
                log("Cevap anahtarı: " + toks.length + " girdi, " + updated + " güncellendi." +
                    (mismatch ? " (" + mismatch + " A-uyuşmazlığı.)" : ""));
                if (fromKey > 0) {
                    log("Bilgi: " + fromKey + " sorunun harfi soru içinden okunamadı; A anahtar bloğundan eşlemeyle alındı.");
                }
            } else { log("Bilgi: Cevap anahtarı bloğu bulunamadı."); }
        }

        // -----------------------------------------------------
        // 16) CSV
        // -----------------------------------------------------
        if (chkCsv.value) {
            var csv = new File(folder.fsName + "/" + bBase + "_AB_eslesme.csv");
            csv.encoding = "UTF-8";
            if (csv.open("w")) {
                csv.write("\uFEFF");
                csv.writeln("Test;A_SoruNo;A_Sayfa;B_SoruNo;B_Sayfa;Tip;Cevap");
                mapping.sort(function (a, b) { return (a.sec - b.sec) || (a.newNum - b.newNum); });
                for (k = 0; k < mapping.length; k++) {
                    var m3 = mapping[k];
                    csv.writeln("Test " + (m3.sec + 1) + ";" + m3.oldNum + ";" + m3.oldPage + ";" +
                                m3.newNum + ";" + m3.newPage + ";" +
                                (m3.shape === "FW" ? "TamGenislik" : "Sutun") + ";" + m3.ans);
                }
                csv.writeln("");
                csv.writeln("LOG");
                for (k = 0; k < LOG.length; k++) { csv.writeln(LOG[k].replace(/;/g, ",")); }
                csv.close();
                log("Rapor: " + decodeURI(csv.name));
            } else { log("UYARI: CSV yazılamadı."); }
        }

        var movedQ = 0;
        for (k = 0; k < mapping.length; k++) {
            if (mapping[k].oldNum !== mapping[k].newNum || mapping[k].oldPage !== mapping[k].newPage) { movedQ++; }
        }
        summaryHead = "YER DEĞİŞTİREN SORU: " + movedQ + " / " + mapping.length + "\n";
        if (reverted > 0) {
            summaryHead += "DİKKAT: " + reverted + " sayfa güvenlik nedeniyle A düzenine geri alındı — LOG'daki KRİTİK satırlarını iletin.\n";
        }
        summaryHead += "\n";

        doc.save();

    } catch (eMain) { hadError = eMain; }

    try {
        doc.viewPreferences.horizontalMeasurementUnits = oldH;
        doc.viewPreferences.verticalMeasurementUnits = oldV;
        doc.viewPreferences.rulerOrigin = oldOrigin;
    } catch (eP) {}
    app.scriptPreferences.enableRedraw = oldRedraw;
    clearGrep();

    if (hadError) {
        alert("HATA: " + hadError.message + (hadError.line ? ("  (satır " + hadError.line + ")") : "") +
              "\n\nB dosyası yarım kalmış olabilir; orijinal A dosyanız diskte değişmedi.");
        return;
    }
    alert("Kitapçık B v4.18 — Tamamlandı ✔\n" + summaryHead + LOG.join("\n"));

})();
