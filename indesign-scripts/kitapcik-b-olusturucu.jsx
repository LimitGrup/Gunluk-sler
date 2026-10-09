// =============================================================
//  KİTAPÇIK B OLUŞTURUCU  v4.26
//  (v4.15: özel havuzlar + ikinci şans + kendini teşhis eden bekçi
//   + bağlı-görsel sertleştirme + ortaokul kapısına belge-içi yedek.
//   v4.16: sade panel. v4.17: kompakt seçenekler geri + doğal havuz yazımı
//   (\u201Csayfa 7-8 soru 25,31\u201D, \u201Cve\u201D bağlacı desteklenir).
//   Lise/AYT yolu davranışsal olarak birebir korunur.
//   v4.18: hata düzeltmeleri — bölüm işaretinde "KİMYA"→"KİMYB" hatası,
//   boş sayfanın komşu sayfa sorularını sahiplenmesi, kaçak/yinelenen
//   sorulu testte blok takası numarası, karşılıklı sayfada blok takası
//   yatay kayması, harfi okunamayan soruda B anahtarında A harfi kalması.
//   v4.19: ORTAK METİN — "8 ve 9.", "1, 2 ve 3.", "6. ve 7.", "5 ile 8.",
//   "13. soruyu ... göre" yönergeleri tanınır (önceden yalnız "8-9.");
//   metni taşıyan soru ve yönergesiz dış göndermeli soru yerinde kilitlenir;
//   soruya ait serbest görsel/şekil/etiket çerçeveleri soruyla birlikte taşınır.
//   v4.20: 10 gerçek A belgesiyle (5-11, TYT, AYT) doğrulandı — HİZA: sorular A'daki
//   yerlerinde kalır, yalnız üstteki içerik uzarsa itilir (önce boşluk daralır);
//   sıkıştırma başlık/giriş ile ilk soru arasını daraltmaz; sütun ayırıcı çizgi blokla
//   (ve blok takasında karşı sayfaya) taşınır; dekor şekiller/başlık şeritleri ve
//   çizgiler bekçide engel sayılır; kendi metnini çapalı taşıyan soru kilitlenmez;
//   kapaktaki "A KİTAPÇIĞI" harfi B olur; "..._1A" dosyası "..._1B" adını alır.
//   v4.21: HIZ — v4.19-v4.20'deki yönerge regex'i sayı listeli metinlerde üstel sürede
//   çalışıp InDesign'da scripti kilitliyordu; regex'siz, doğrusal ayrıştırıcıyla
//   değiştirildi. Grafikler toplu okunur (everyItem), bekçi sabit engelleri yeniden
//   okumaz, aynı yerleşim iki kez hesaplanmaz; ilerleme penceresi eklendi.
//   v4.22: test başlangıcı okuma sırasından bağımsız ("1." olan sayfa yeni testi başlatır);
//   çerçeveyle örtüşmeyen çapalı nesne bir sayfa kaydırılarak düzeltilir ya da yok sayılır;
//   rapor sadeleşti: yerinde kalan her sorunun nedeni, DİKKAT / BİLGİ bölümleri, ayrıntı CSV'de.
//   v4.23: ALT SINIR — sorular kenar boşluğunun (ya da A'da sorunun indiği en alt noktanın)
//   altına inmez; altbilgi bandındaki "TESTİ BİTTİ" çerçevesi sınırı aşağı çekmez (önceden
//   bazı sorular master altbilgi çizgisine/sayfa numarasına iniyordu). SATIR HİZASI — A'da
//   aynı satırdan başlayan sol/sağ sorular B'de de aynı satırdan başlar; bozan sıra yalnız
//   başka çare yoksa seçilir ve DİKKAT'te bildirilir. ALTA SIĞDIRMA — sığmayan soru, hizası
//   olmayan yerde yalnız gerektiği kadar yukarı alınır; yerinde kalan soru için son deneme.
//   v4.24: 5 yeni ortaokul denemesiyle (MOBESE) doğrulandı — A'da tek grupta duran birden çok
//   soru ya da ortak metinle gruplanmış soru ayrı ayrı ele alınır (yalnız kendi sayfasında karışır;
//   önceden sabit kalıyor, "numara dizisinde eksik" uyarısı çıkıyordu). İngilizce ortak metin
//   yönergesi ("Answer the questions 8-10 according to the text below.") ve "According to the text
//   above" göndermesi tanınır (önceden İngilizce gruptan soru başka sayfaya gidiyordu). Tam sayfa
//   takası: soru sayısı farklı sayfalar arasında, aradaki sayfada ortak metin/ders bölgesi varsa
//   yapılmaz ("8 ve 9. soruları" grubu 7-8'e kayıyordu); karşı sayfaya sığmazsa sorular başka
//   sırayla denenir; ayırıcı çizgi sütunlarla hizalı taşınır; kısalan blokta "TESTİ BİTTİ" yukarı
//   çekilmez; numarası aynı kalacak takas yapılmaz. SAYFA İÇİ BLOK SIRASI: eşi olmayan tam
//   genişlik soru, sayfadaki iki sütunlu blokla yer değiştirir. HİZA: 1-3 pt kaçık satırlar da
//   satırdır; itilen satırın karşı sütunu da aynı hizaya iner; taşan sütun yalnız kendi aralığını
//   daraltır (diğer sütun A'daki yerinde kalır); sorunun altındaki sabit yazıya en az 12 pt.
//   "Yerinde kalan" artık numarası değişmeyen sorudur (sayfası değişse bile).
//   v4.25: GENELLEME — belgeye özel ayar yok; görülmemiş belgeler için kurallar ve güvenlik ağı:
//   BRANŞ SINIRI: numaralar branşlar arasında sıfırlanmadan sürse bile her "Bu testte N soru
//   vardır." girişi yeni branş bölgesi açar; üst bant yazısı ("SÖZEL BÖLÜM - TÜRKÇE", "MATEMATİK
//   TESTİ") farklı sayfalar arasında takas yapılmaz. SÜTUN TAKASI: sol ve sağ sütun soruları dikey
//   konumlarını koruyarak yer değiştirebilir. ORTAK METİN GÜVENLİK AĞI: yönergesi tanınmayan soru
//   dışı metin varsa o sayfanın soruları sayfa dışına çıkmaz; metnin altındaki "Bu metne göre /
//   Tabloda / According to" gönderme yapan ardışık sorular örtük grup olarak kendi aralarında
//   karışır; gönderme yoksa yerinde kalır ve DİKKAT'te bildirilir. Takasta "TEST BİTTİ" yazısı
//   görsele binmez, ayırıcı çizgi alt kenar boşluğunu aşmaz. 90 değiştirilmiş belge varyasyonuyla
//   (soru boyları, silinmiş yönergeler, kesintisiz numaralar) doğrulandı.
//   v4.26: INDESIGN'IN KENDİ DAVRANIŞLARINA GÖRE DÜZELTMELER (v4.25 ekran görüntülerinden):
//   SAĞ SAYFA — karşılıklı sayfalı belgede InDesign Page.bounds'u yayılım koordinatında veriyor
//   (sağ sayfa [0,W,H,2W]); öğeler sayfa koordinatında. Bu yüzden sağ sayfaların tüm soruları "sol
//   sütun" sayılıyor, satır hizası bozuluyor, yanlış branş bölgesi ("Test 2: 3-12") ve numara
//   boşluğu/tekrarı oluşuyordu. Sayfa sınırı öğelerin koordinatına göre düzeltilir. GRUP ÇÖZME —
//   pageItems[i] InDesign'da genel "PageItem" döndüğünden gruptaki sorular kayboluyordu (getElements).
//   SIRALAMA — ExtendScript'in sort'u kararsız; tüm karşılaştırıcılar eşitliği kendisi çözer.
//   NUMARALAMA — sayaç "son okunan" değil "en büyük" numaradır; numaralar yazılmadan önce her testte
//   A'daki numara kümesiyle karşılaştırılır, tutmazsa test okuma sırasıyla 1..N numaralanır.
//   GÖNDERME — "bu …den / yukarıdaki …" kelime kelime aranır (ExtendScript düzenli ifadesi yarım
//   kelimede yanlış eşleşip gönderme yapmayan soruları kilitliyordu). İngilizce "(2-3)" parantezli
//   yönerge tanınır. ORTAK METİN BANDI TAKASI — ortak metin grubu (yönerge + metin + soruları) ile
//   diğer sorular sayfa içinde bant olarak yer değiştirebilir; yönergedeki numaralar güncellenir.)
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
    var dlg = new Window("dialog", "Kitapçık B Oluşturucu v4.26 — Limit Yayınları");
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
    // v4.22: uyarı penceresinin BİLGİ bölümüne çıkan satırlar (hepsi CSV'ye de yazılır).
    // "KRİTİK"/"UYARI" ile başlayanlar DİKKAT bölümüne; "Ayrıntı:" ile başlayanlar yalnız CSV'ye.
    var INFO = [];
    function info(s) { LOG.push(s); INFO.push(s); }

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
        var _nmB = /[-_\s\d]B(?=[.\-_\s]|$)/.test(_nm);
        if ((_hasB && !_hasA) || _nmB) {
            if (!confirm("DİKKAT: Bu belge daha önce B'ye çevrilmiş görünüyor" +
                         (_nmB ? " (dosya adında B var)" : " (üst bant B)") +
                         ".\nB üzerinden tekrar üretmek soruları bozar.\n\nYine de devam edilsin mi?")) { return; }
        }
    } catch (eBG) {}

    function makeBName(base) {
        // v4.19: "...DENEME_1A" -> "...DENEME_1B" (4. desen)
        var pats = [/-A(?![0-9A-Za-zÇĞİÖŞÜçğıöşü])/, /_A(?![0-9A-Za-zÇĞİÖŞÜçğıöşü])/, /(^|\s)A(?![0-9A-Za-zÇĞİÖŞÜçğıöşü])/,
                    /(\d)A(?![0-9A-Za-zÇĞİÖŞÜçğıöşü])/];
        for (var i = 0; i < pats.length; i++) {
            if (pats[i].test(base)) {
                if (i >= 2) { return base.replace(pats[i], "$1B"); }
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
    info("B kopyası: " + bBase + ".indd");
    if (isMiddleSchool) {
        info("Ortaokul (" + middleSchoolGrade + ". sınıf) güvenli yerleşim modu kullanıldı.");
        log("Ayrıntı: ortaokul hiza koruması — test giriş bandı sert sınır; sütun içi elastik boşluk üst sınırı " + MIDDLE_SCHOOL_GAP_CAP + " pt.");
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

    // v4.20: ilerleme penceresi (uzun belgelerde scriptin çalıştığı görülsün)
    var prog = null, progLast = 0;
    function progress(msg, force) {
        try {
            var now = new Date().getTime();
            if (!force && now - progLast < 400) { return; }
            progLast = now;
            if (prog === null) {
                prog = new Window("palette", "Kitapçık B Oluşturucu");
                prog.alignChildren = "fill";
                prog.msg = prog.add("statictext", undefined, msg);
                prog.msg.characters = 46;
                prog.show();
            }
            prog.msg.text = msg;
            prog.update();
        } catch (ePr) {}
    }
    function progressClose() { try { if (prog !== null) { prog.close(); } } catch (ePr2) {} prog = null; }

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
        var TAIL_GAP = 12;   // v4.24: sorunun ALTINDAKİ sabit yazıya ("TESTİ BİTTİ" vb.) en az boşluk (A'da daha darsa o kadar)
        var GAP_FLOOR = 8;
        var SCALES = chkCompress.value ? [1.0, 0.9, 0.8, 0.7, 0.6, 0.5] : [1.0];
        // v4.19 YERLEŞİM MERDİVENİ: önce her soru A'daki yerinde kalır, yalnız üstündeki
        // içerik uzarsa aşağı itilir ("sabitli"); sığmazsa eski akışlı yerleşim denenir.
        // Böylece sütun başlangıçları, satır hizaları ve sütun ayırıcıları A'daki gibi kalır.
        // Sabitli yerleşimde üstteki soru uzarsa önce aradaki boş alan daralır (en az
        // ANCHOR_MIN_GAP; A'daki boşluk bundan darsa A'daki kadar); yetmezse soru itilir.
        // (Ölçüm: 10 A belgesinde soru arası boşluk medyanı 117 pt, %5'lik dilim 42 pt.)
        var ANCHOR_MIN_GAP = chkCompress.value ? 28 : 100000;
        var LEVELS = [{ s: 1.0, a: true }];
        (function () {
            for (var qs = 0; qs < SCALES.length; qs++) { LEVELS.push({ s: SCALES[qs], a: false }); }
        })();
        var FW_RATIO = 0.55;

        function isIntroText(s) {
            var head = String(s).substr(0, 60);
            return /Bu\s+(testte|denemede|s[ıi]navda)/i.test(head);
        }

        // v4.19 ORTAK METİN YÖNERGESİ: "8 ve 9. soruları", "1, 2 ve 3. soruları",
        // "6. ve 7. sorular", "10-12. soruları", "5 ile 8. sorular", "13. soruyu ... göre".
        // v4.20: REGEX YOK — ExtendScript'te sayı listeli metinlerde (anahtar, tablo, dizi)
        // iç içe tekrarlı regex üstel geri izlemeye düşüp scripti kilitliyordu. Paragrafta
        // "soru" yoksa hiç iş yapılmaz; varsa kelimenin önündeki en çok 80 karakter geriye
        // doğru karakter karakter okunur (süre metin uzunluğuyla doğru orantılı).
        // "cevaplayınız" (yönerge) bağlamdır; "cevaplayacaktır" (Din Kültürü seçmeli blok açıklaması) değildir
        var LINKCTX_RE = /g[öo]re|cevaplay[ıi]n[ıi]z|yararlan|ilgili|ba[ğg]l[ıi]/i;
        // v4.24: İngilizce yönerge bağlamı ("Answer the questions 8-10 according to the text below.")
        var LINKCTX_EN_RE = /according\s+to|based\s+on|\banswer|\bread\b|\brefer|\buse\s+the/i;
        var LETTERS = "abcçdefgğhıijklmnoöprsştuüvyzqwxâîûABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZQWXÂÎÛ";
        function isLetterCh(c) { return c !== "" && LETTERS.indexOf(c) >= 0; }
        function isDigitCh(c) { return c >= "0" && c <= "9" && c.length === 1; }
        function isSpaceCh(c) {
            if (c === "") { return false; }
            var cc = c.charCodeAt(0);
            return cc === 32 || cc === 9 || cc === 160 || (cc >= 0x2000 && cc <= 0x200B) || cc === 0x202F || cc === 0x3000;
        }
        // p konumundaki "soru"nun önündeki sayı listesini geriye doğru oku: [sayılar, başlangıç] ya da null
        function numsBefore(par, low, p) {
            var i = p - 1, lim = p - 80, nums = [], start = -1;
            if (lim < 0) { lim = 0; }
            function skipSp() { while (i >= lim && isSpaceCh(par.charAt(i))) { i--; } }
            function skipSuffix() {          // "4\u2019üncü", "3'üncü"
                var k = i;
                while (k >= lim && isLetterCh(par.charAt(k))) { k--; }
                if (k < i && k >= lim && (par.charAt(k) === "'" || par.charAt(k) === "\u2019")) { i = k - 1; }
            }
            function readNum() {
                var e = i;
                while (i >= lim && isDigitCh(par.charAt(i))) { i--; }
                var len = e - i;
                if (len < 1 || len > 3) { return false; }
                if (i >= lim && isDigitCh(par.charAt(i))) { return false; }
                nums.push(parseInt(par.substring(i + 1, e + 1), 10));
                start = i + 1;
                return true;
            }
            skipSp();
            if (i >= lim && par.charAt(i) === ".") { i--; }
            skipSp(); skipSuffix(); skipSp();
            if (!readNum()) { return null; }
            for (var guard = 0; guard < 40; guard++) {
                var save = i;
                skipSp();
                if (i >= lim && par.charAt(i) === ".") { i--; skipSp(); }
                var c = par.charAt(i), ok = false;
                if (i >= lim && (c === "," || c === "-" || c === "\u2013" || c === "—")) { i--; ok = true; }
                else {
                    var words = ["ve", "ile", "ila"];
                    for (var w = 0; w < words.length && !ok; w++) {
                        var wl = words[w].length, b = i - wl + 1;
                        if (b >= lim && low.substr(b, wl) === words[w] && !isLetterCh(par.charAt(b - 1))) { i = b - 1; ok = true; }
                    }
                }
                if (!ok) { i = save; break; }
                skipSp();
                if (i >= lim && par.charAt(i) === ".") { i--; skipSp(); }
                skipSuffix(); skipSp();
                if (!readNum()) { i = save; break; }
            }
            return { nums: nums, at: start };
        }
        // v4.24: İngilizce — "question(s)" kelimesinden SONRAKİ sayı listesini ileri doğru oku
        //        ("questions 8-10", "8 and 9", "8, 9 and 10", "8 to 10"): {nums, at} ya da null
        function numsAfter(par, low, p) {
            var i = p, lim = p + 80, nums = [], start = -1;
            if (lim > par.length) { lim = par.length; }
            function skipSpF() { while (i < lim && isSpaceCh(par.charAt(i))) { i++; } }
            function readNumF() {
                var b = i;
                while (i < lim && isDigitCh(par.charAt(i))) { i++; }
                if (i - b < 1 || i - b > 3) { return false; }
                if (i < lim && isLetterCh(par.charAt(i))) { return false; }
                nums.push(parseInt(par.substring(b, i), 10));
                if (start < 0) { start = b; }
                return true;
            }
            skipSpF();
            // v4.26: "Answer the questions (2-3) according to ..." — parantezli/köşeli liste
            if (i < lim && (par.charAt(i) === "(" || par.charAt(i) === "[")) { i++; skipSpF(); }
            if (!readNumF()) { return null; }
            for (var g2 = 0; g2 < 40; g2++) {
                var save = i;
                skipSpF();
                if (i < lim && par.charAt(i) === ".") { i++; skipSpF(); }
                var c = par.charAt(i), ok = false;
                if (i < lim && (c === "," || c === "-" || c === "\u2013" || c === "\u2014" || c === "&")) { i++; ok = true; }
                else {
                    var wordsE = ["and", "to"];
                    for (var w2 = 0; w2 < wordsE.length && !ok; w2++) {
                        var wl2 = wordsE[w2].length;
                        if (low.substr(i, wl2) === wordsE[w2] && !isLetterCh(par.charAt(i + wl2))) { i += wl2; ok = true; }
                    }
                }
                if (!ok) { i = save; break; }
                skipSpF();
                if (!readNumF()) { i = save; break; }
            }
            // "8 - 10" aralığı: uçlar arası dolu kabul edilir (lo/hi ile)
            return { nums: nums, at: start, end: i };
        }
        function linkDirectives(text) {
            var out = [];
            var pars = String(text).split(/[\r\n\u2029]+/);
            for (var pq = 0; pq < pars.length; pq++) {
                var par = pars[pq];
                if (par.length > 300) { continue; }
                var low = par.toLowerCase();
                if (isIntroText(par)) { continue; }
                // v4.24: İngilizce yönerge
                var fromE = 0, pE, ctxE = null;
                while ((pE = low.indexOf("question", fromE)) >= 0) {
                    fromE = pE + 8;
                    if (pE > 0 && isLetterCh(par.charAt(pE - 1))) { continue; }
                    var afterE = pE + 8;
                    if (low.charAt(afterE) === "s") { afterE++; }
                    if (isLetterCh(par.charAt(afterE))) { continue; }
                    var na = numsAfter(par, low, afterE);
                    if (na === null) { continue; }
                    if (ctxE === null) { ctxE = LINKCTX_EN_RE.test(par); }
                    if (!ctxE) { continue; }
                    var loE = 999, hiE = 0;
                    for (var nqE = 0; nqE < na.nums.length; nqE++) {
                        if (na.nums[nqE] < loE) { loE = na.nums[nqE]; }
                        if (na.nums[nqE] > hiE) { hiE = na.nums[nqE]; }
                    }
                    if (loE < 1 || hiE - loE > 40) { continue; }
                    out.push({ lo: loE, hi: hiE, link: true, at: na.at, end: na.end });
                }
                if (low.indexOf("soru") < 0) { continue; }
                var ctx = null, from = 0, p;
                while ((p = low.indexOf("soru", from)) >= 0) {
                    from = p + 4;
                    if (p > 0 && isLetterCh(par.charAt(p - 1))) { continue; }
                    if (low.substr(p, 6) === "sorulu") { continue; }   // "20 soruluk sınav"
                    var nb = numsBefore(par, low, p);
                    if (nb === null) { continue; }
                    if (ctx === null) { ctx = LINKCTX_RE.test(par); }
                    if (nb.nums.length === 1 && !ctx) { continue; }   // "Toplam 40 soru" vb.
                    var lo = 999, hi = 0;
                    for (var nq = 0; nq < nb.nums.length; nq++) {
                        if (nb.nums[nq] < lo) { lo = nb.nums[nq]; }
                        if (nb.nums[nq] > hi) { hi = nb.nums[nq]; }
                    }
                    if (lo < 1 || hi - lo > 40) { continue; }
                    out.push({ lo: lo, hi: hi, link: ctx, at: nb.at, end: p });
                }
            }
            return out;
        }
        // Çerçeve metni bir yönergeyle başlıyor mu? ("6. ve 7. soruları ..." soru 6 sanılmasın)
        function isDirectiveStart(text) {
            var first = String(text).split(/[\r\n\u2029]/)[0].replace(/^[\s\u200B\uFEFF\uFFFC\u009E]+/, "");
            var ds = linkDirectives(first);
            return ds.length > 0 && ds[0].at === 0;
        }

        // v4.20 HIZ: InDesign koleksiyonunu tek çağrıda diziye çevir; öğe öğe erişim
        // (coll[i], coll.length her turda) InDesign'da en pahalı işlemdir.
        function itemsOf(coll) {
            var n = 0;
            try { n = coll.length; } catch (eIo0) { return []; }
            if (n === 0) { return []; }
            try { var el = coll.everyItem().getElements(); if (el && el.length === n) { return el; } } catch (eIo1) {}
            var out = [];
            for (var q = 0; q < n; q++) { try { out.push(coll[q]); } catch (eIo2) {} }
            return out;
        }
        // aynı koleksiyonun sınırlarını tek çağrıda al (tek öğede InDesign düz dizi döndürür)
        function boundsOf(coll, els) {
            var n = els.length, out = [];
            if (n === 0) { return out; }
            if (n > 1) {
                try {
                    var bAll = coll.everyItem().geometricBounds;
                    if (bAll && bAll.length === n && bAll[0] && bAll[0].length === 4) { return bAll; }
                } catch (eBo1) {}
            }
            for (var q = 0; q < n; q++) { try { out.push(els[q].geometricBounds); } catch (eBo2) { out.push(null); } }
            return out;
        }

        // v4.8: grup içindeki metin çerçevelerini güvenle listele.
        // allPageItems bazı sürümlerde boş dönebildiğinden öz-yinelemeli yedek içerir.
        // v4.25: üst bant yazısından branş etiketi: "SÖZEL BÖLÜM - TÜRKÇE" → TÜRKÇE,
        //        "MATEMATİK TESTİ" → MATEMATİK ("TESTİ BİTTİ", "TESTİNE GEÇİNİZ" sayılmaz)
        function branchLabelOf(t) {
            var tl = trimS(String(t));
            if (tl.length < 3 || tl.length > 70 || /[\r\n\u2029]/.test(tl)) { return ""; }
            var mB = /B[ÖO]L[ÜU]M[Ü]?\s*[-\u2013\u2014:]\s*(.+)$/i.exec(tl);
            var nm = mB ? mB[1] : null;
            if (nm === null) {
                var mT = /^(.{3,60}?)\s+TEST[İI]\s*$/.exec(tl);
                if (mT) { nm = mT[1]; }
            }
            if (nm === null || /B[İI]TT[İI]|GE[ÇC][İI]N[İI]Z/i.test(tl)) { return ""; }
            return nm.toUpperCase().replace(/[\s\u00A0.,:;\-\u2013\u2014]+/g, "").replace(/İ/g, "I");
        }

        // v4.24: grubun doğrudan/iç içe (çapalı olmayan) metin çerçevelerinde kaç tam soru var
        function groupQCount(g) {
            var tfsQ = innerTextFrames(g), nQ = 0;
            for (var iQ = 0; iQ < tfsQ.length; iQ++) {
                try { if (tfsQ[iQ].parent.constructor.name === "Character") { continue; } } catch (eQ0) {}
                var tQ = "";
                try { tQ = String(tfsQ[iQ].parentStory.texts[0].contents); } catch (eQ1) { continue; }
                var mQ = QNUM_RE.exec(tQ);
                if (!mQ || SINIF_RE.test(tQ) || isDirectiveStart(tQ)) { continue; }
                var bQ = tQ.substr(mQ[0].length).replace(/[\s\u00A0\u200B\uFEFF\uFFFC\u009E\u00BB\u00AB»«¶]+/g, "");
                if (bQ.length >= 8) { nQ++; }
            }
            return nQ;
        }

        // v4.24: grupta soru olmayan, ortak metin yönergesi taşıyan (çapalı olmayan) çerçeve var mı
        function groupLinkText(g) {
            var tfsL = innerTextFrames(g);
            for (var iL = 0; iL < tfsL.length; iL++) {
                try { if (tfsL[iL].parent.constructor.name === "Character") { continue; } } catch (eL0) {}
                var tL = "";
                try { tL = String(tfsL[iL].parentStory.texts[0].contents); } catch (eL1) { continue; }
                var mL = QNUM_RE.exec(tL);
                if (mL && !SINIF_RE.test(tL) && !isDirectiveStart(tL)) { continue; }
                if (linkDirectives(tL).length > 0) { return tL; }
            }
            return null;
        }

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
                // v4.26: koleksiyonun [i] öğesi InDesign'da genel "PageItem" döner; gerçek tür getElements ile
                try { kids = itemsOf(cur.pageItems); } catch (eIT2) { kids = null; }
                if (kids === null) { continue; }
                for (var q8 = 0; q8 < kids.length; q8++) {
                    var cn8 = kids[q8].constructor.name;
                    if (cn8 === "TextFrame") { out.push(kids[q8]); }
                    else if (cn8 === "Group") { stack.push(kids[q8]); }
                }
            }
            return out;
        }

        // v4.26: sayfa sınırının öğelerle aynı koordinat uzayına getirilmesi için gereken yatay kayma
        // (0, ±W). Öğe merkezlerinin en çoğunun sayfa içine düştüğü kayma seçilir; eşitlikte 0.
        function pageBoundsShift(list, pbS) {
            var wS = pbS[3] - pbS[1], cand = [0, -wS, wS], best = 0, bestN = -1, cxs = [], iS;
            if (!(wS > 0) || list.length === 0) { return 0; }
            for (iS = 0; iS < list.length; iS++) {   // her öğenin sınırı bir kez okunur (InDesign'da her okuma bir DOM çağrısı)
                try { var gS = list[iS].geometricBounds; cxs.push((gS[1] + gS[3]) / 2); } catch (eS) {}
            }
            for (var cS = 0; cS < cand.length; cS++) {
                var nS = 0;
                for (iS = 0; iS < cxs.length; iS++) {
                    if (cxs[iS] >= pbS[1] + cand[cS] - 2 && cxs[iS] <= pbS[3] + cand[cS] + 2) { nS++; }
                }
                if (nS > bestN) { bestN = nS; best = cand[cS]; }
            }
            return best;
        }
        var pbShiftPages = [];

        // -----------------------------------------------------
        // 5) ENVANTER
        // -----------------------------------------------------
        var pages = doc.pages;
        var pageData = [];
        var compTotal = 0;
        var revertWhy = {};   // v4.22: sayfa A düzeninde bırakıldıysa nedeni
        var allSlots = [];
        var msSignal = false;
        var pi, ci, k, i, j;

        progress("Sayfalar okunuyor…", true);
        for (pi = 0; pi < pages.length; pi++) {
            progress("Sayfalar okunuyor: " + (pi + 1) + " / " + pages.length);
            var pg = pages[pi];
            var pb = pg.bounds;
            var pW = pb[3] - pb[1];
            var midX = (pb[1] + pb[3]) / 2;
            var botMargin = 0;
            try { botMargin = pg.marginPreferences.bottom; } catch (eM) {}
            var usableBottom = pb[2] - botMargin;

            var introRanges = [];
            var linkRanges = [];   // v4.19: bu sayfadaki ortak metin yönergeleri
            var compCands = [];    // v4.19: soruya ait olabilecek serbest görsel/şekil/etiket
            var textBlocks = [];   // v4.25: soru dışı uzun metin içeren dekor gruplar (olası ortak metin)

            var items = [];
            var ignoredIds = {};
            // v4.8: pg.pageItems bazı InDesign sürümlerinde sayfa için BOŞ döner
            // (v4.5-4.7'de hiç soru bulunamamasının nedeni). Kanıtlı yöntem:
            // textFrames + groups; ikisi de boşsa spread öğelerinden bu sayfaya düşenler.
            var tlItems = [];
            var pageLabel = "";   // v4.25: "SÖZEL BÖLÜM - TÜRKÇE" / "MATEMATİK TESTİ" → branş etiketi
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
                    var spIt = itemsOf(pg.parent.pageItems);   // v4.26: gerçek türler (genel PageItem değil)
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
            // v4.26 SAYFA KOORDİNATI: karşılıklı sayfalı belgede InDesign Page.bounds'u yayılımın sol
            // kenarına göre bildirebiliyor (sağ sayfa [0, W, H, 2W]); öğelerin geometricBounds'u ise
            // PAGE_ORIGIN'de sayfanın kendi koordinatında. Bu fark yüzünden sağ sayfanın tüm soruları
            // "sol sütun" sayılıyor, hiza/numara/ortak metin hataları doğuyordu. Sayfa sınırı, sayfadaki
            // öğelerin çoğunun bulunduğu koordinat uzayına kaydırılır.
            var pbSh = pageBoundsShift(tlItems, pb);
            if (pbSh !== 0) {
                pb = [pb[0], pb[1] + pbSh, pb[2], pb[3] + pbSh];
                midX = (pb[1] + pb[3]) / 2;
                pbShiftPages.push(pg.name);
            }
            for (k2 = 0; k2 < tlItems.length; k2++) {
                var scanTfs;
                if (tlItems[k2].constructor.name === "TextFrame") { scanTfs = [tlItems[k2]]; }
                else { scanTfs = innerTextFrames(tlItems[k2]); }
                for (var q7 = 0; q7 < scanTfs.length; q7++) {
                    var c0 = "";
                    try { c0 = String(scanTfs[q7].parentStory.texts[0].contents); } catch (eIsc) { continue; }
                    if (!msSignal && /Bu\s+testte\s+\d+\s+soru/i.test(c0)) { msSignal = true; }
                    if (pageLabel === "") { pageLabel = branchLabelOf(c0); }
                    if (isIntroText(c0)) {
                        RANGE_RE.lastIndex = 0;
                        var mR;
                        while ((mR = RANGE_RE.exec(c0)) !== null) {
                            introRanges.push({ lo: parseInt(mR[1], 10), hi: parseInt(mR[2], 10) });
                        }
                    }
                    // v4.19: soru metni olmayan her çerçevede (gruplar dahil) yönerge ara
                    var qm7 = QNUM_RE.exec(c0);
                    if (!qm7 || SINIF_RE.test(c0) || isDirectiveStart(c0)) {
                        var dl7 = linkDirectives(c0);
                        for (var dq7 = 0; dq7 < dl7.length; dq7++) {
                            // v4.26: yönergenin çerçevesi (ortak metin bandı takasında numarası güncellenir)
                            linkRanges.push({ lo: dl7[dq7].lo, hi: dl7[dq7].hi, link: dl7[dq7].link, tf: scanTfs[q7] });
                        }
                    }
                }
            }

            // v4.24: A'da birden çok soru tek grupta duruyorsa (ör. 5 ve 6. sorular birlikte
            // gruplanmış) grup çözülmüş gibi her soru ayrı ele alınır. Grup üyesi başka sayfaya
            // taşınamadığından bu sorular yalnız KENDİ SAYFASINDA yer değiştirir (noXPage).
            // Aynı şekilde ortak metni (yönerge + metin) ve sorusunu tek grupta tutan "taşıyıcı" grup
            // da çözülür: metin bloğu yerinde sabit kalır, soru gruptaki diğer sorularla karışır.
            var noXP = {}, multiQ = 0, fixedBlk = {};
            for (k2 = 0; k2 < tlItems.length; k2++) {
                if (tlItems[k2].constructor.name !== "Group") { continue; }
                var gqc = groupQCount(tlItems[k2]);
                if (gqc < 1 || (gqc === 1 && groupLinkText(tlItems[k2]) === null)) { continue; }
                var kidsM = null;
                // v4.26: InDesign'da pageItems[i] genel "PageItem" döner (constructor.name TextFrame/Group
                // değil); grup çözülürken sorular kayboluyor, numara dizisinde eksik oluşuyordu.
                try { kidsM = itemsOf(tlItems[k2].pageItems); } catch (eMG) { kidsM = null; }
                if (kidsM === null || kidsM.length === 0) { continue; }
                var replM = [];
                for (var mk = 0; mk < kidsM.length; mk++) {
                    var kcn = kidsM[mk].constructor.name;
                    try { noXP[kidsM[mk].id] = true; } catch (eMG1) {}
                    if (kcn === "TextFrame" || kcn === "Group") {
                        replM.push(kidsM[mk]);
                        if (kcn === "Group" && groupQCount(kidsM[mk]) === 0) { try { fixedBlk[kidsM[mk].id] = true; } catch (eMG4) {} }
                    }
                    else { try { compCands.push({ it: kidsM[mk], b: kidsM[mk].geometricBounds }); } catch (eMG2) {} }
                }
                tlItems.splice(k2, 1);
                for (mk = 0; mk < replM.length; mk++) { tlItems.splice(k2 + mk, 0, replM[mk]); }
                k2--;
                multiQ++;
            }
            if (multiQ > 0) {
                log("Ayrıntı: s." + pg.name + " — A'da tek grup içinde duran sorular (ya da ortak metinle gruplanmış soru) ayrı ayrı ele alındı; grup bozulmadığı için yalnız bu sayfada yer değiştirirler.");
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
                    if (innerTFs.length === 0) {
                        // v4.19: metinsiz grup (görsel/şekil) — bir sorunun içindeyse onunla taşınır
                        compCands.push({ it: pit, b: gb });
                        continue;
                    }
                    var numCount = 0, introTxt = null, grpCarrier = false, grpVisual = false, grpTxtLen = 0, grpNonQLen = 0;
                    content = "";
                    for (i = 0; i < innerTFs.length; i++) {
                        var itxt = "";
                        try { itxt = String(innerTFs[i].parentStory.texts[0].contents); } catch (eG3) { continue; }
                        grpTxtLen += itxt.length;
                        var gm = QNUM_RE.exec(itxt);
                        var gIsQ = false;
                        if (gm && !SINIF_RE.test(itxt) && !isDirectiveStart(itxt)) {
                            var gbody = itxt.substr(gm[0].length)
                                            .replace(/[\s\u00A0\u200B\uFEFF\uFFFC\u009E\u00BB\u00AB»«¶]+/g, "");
                            if (gbody.length >= 8) {
                                gIsQ = true;
                                numCount++;
                                if (numCount === 1) { content = itxt; numTf = innerTFs[i]; }
                            }
                        }
                        if (!gIsQ && linkDirectives(itxt).length > 0) { grpCarrier = true; }
                        if (!gIsQ) {
                            var anchG = false;
                            try { anchG = (innerTFs[i].parent.constructor.name === "Character"); } catch (eAG) {}
                            if (!anchG) { grpNonQLen += itxt.length; }
                        }
                        if (introTxt === null && isIntroText(itxt)) { introTxt = itxt; }
                    }
                    if (numCount === 1) {
                        // grup = soru
                        try { grpVisual = (pit.allPageItems.length > innerTFs.length); } catch (eGV) { grpVisual = false; }
                    } else if (numCount > 1) {
                        log("UYARI: s." + pg.name + " — birden çok numaralı soru içeren grup sabit bırakıldı; elle karıştırın.");
                        content = "";
                        numTf = null;
                    } else if (introTxt !== null) {
                        content = introTxt;
                        numTf = null;
                    } else if (fixedBlk[pit.id] === true) {
                        // v4.24: çözülen gruptan gelen soru dışı metin bloğu (ör. yönerge + tablo): sabit öğe
                        var lnkT = groupLinkText(pit);
                        if (lnkT !== null) { content = lnkT; }
                        else { try { content = String(innerTFs[0].parentStory.texts[0].contents); } catch (eFB) { content = "metin"; } }
                        numTf = null;
                    } else {
                        for (i = 0; i < innerTFs.length; i++) {
                            try { ignoredIds[innerTFs[i].id] = true; } catch (eIG1) {}
                        }
                        // v4.19: etiketli şekil grubu bir sorunun içindeyse onunla taşınır
                        compCands.push({ it: pit, b: gb });
                        if (grpTxtLen >= 120) { textBlocks.push({ y1: gb[0], x1: gb[1], y2: gb[2], x2: gb[3], etiket: "grup" }); }
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
                    linkedHeader: false, grup: 0, ans: "?", noXPage: false,
                    emptyText: (trimS(content) === "" && cn === "TextFrame"),
                    txtLen: trimS(content).length, bigText: (cn === "Group" && grpNonQLen >= 120)
                };
                try { if (noXP[pit.id] === true) { rec.noXPage = true; } } catch (eNX) {}

                if (isIntroText(content)) {
                    rec.kind = "intro";
                    var mIn = /Bu\s+(testte|denemede)\s+(\d{1,3})\s+soru/i.exec(content);
                    rec.introN = mIn ? parseInt(mIn[2], 10) : 0;
                } else {
                    var m = QNUM_RE.exec(content);
                    if (m && !SINIF_RE.test(content) && !isDirectiveStart(content)) {
                        // taslak artığı: numara var ama gövde yok ("1. »" gibi)
                        var body = content.substr(m[0].length)
                                          .replace(/[\s\u00A0\u200B\uFEFF\uFFFC\u009E\u00BB\u00AB»«¶]+/g, "");
                        if (body.length >= 8) {
                            rec.kind = "soru";
                            rec.num = parseInt(m[1], 10);
                            // v4.19: gövde başı (ortak metne gönderme denetimi için)
                            rec.head = content.substr(m[0].length).substr(0, 200);
                            // v4.19: yönergeyi/ortak metni kendi içinde taşıyan soru (taşıyıcı)
                            rec.carrier = (cn === "Group") ? grpCarrier : (linkDirectives(content).length > 0);
                            rec.hasVisual = (cn === "Group") ? grpVisual : false;
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
                    if (anc.length > 0) { rU.hasVisual = true; }   // v4.19
                    var pgH = pb[2] - pb[0];
                    for (i = 0; i < anc.length; i++) {
                        var agb;
                        try { agb = anc[i].geometricBounds; } catch (eA1) { continue; }
                        // v4.15 akıl süzgeci: yanlış koordinat uzayından gelen
                        // bağlı nesneler zarfı bozmasın
                        if (agb[0] < rU.fy1 - 1.2 * pgH || agb[2] > rU.fy2 + 1.2 * pgH) { continue; }
                        if (agb[3] < pb[1] - pW || agb[1] > pb[3] + pW) { continue; }
                        // v4.22: çerçeveyle HİÇ örtüşmeyen çapalı nesne yanlış koordinat uzayındadır
                        // (karşılıklı sayfada InDesign bazen yayılımın öbür sayfasına göre bildirir):
                        // bir sayfa genişliği kaydırılmış hâli örtüşüyorsa o kullanılır, yoksa yok sayılır.
                        var frA = [rU.fy1, rU.fx1, rU.fy2, rU.fx2];
                        var touchesA = function (b) {
                            return Math.min(b[2], frA[2]) > Math.max(b[0], frA[0]) && Math.min(b[3], frA[3]) > Math.max(b[1], frA[1]);
                        };
                        if (!touchesA(agb)) {
                            var agbS = null, shA = [-pW, pW];
                            for (var sa = 0; sa < shA.length && agbS === null; sa++) {
                                var cand = [agb[0], agb[1] + shA[sa], agb[2], agb[3] + shA[sa]];
                                if (touchesA(cand)) { agbS = cand; }
                            }
                            log("Ayrıntı: s." + pg.name + " — " + trimS(String(rU.etiket)).substr(0, 6) +
                                " sorusunun çapalı nesnesi çerçevenin dışında bildirildi [" + Math.round(agb[0]) + "," +
                                Math.round(agb[1]) + "," + Math.round(agb[2]) + "," + Math.round(agb[3]) + "] — " +
                                (agbS ? "bir sayfa genişliği kaydırılarak düzeltildi." : "yok sayıldı."));
                            if (agbS === null) { continue; }
                            agb = agbS;
                        }
                        var tasma = Math.max(rU.fy1 - agb[0], agb[2] - rU.fy2, rU.fx1 - agb[1], agb[3] - rU.fx2);
                        if (tasma > 10) {
                            log("Ayrıntı: s." + pg.name + " — " + trimS(String(rU.etiket)).substr(0, 6) +
                                " sorusunun çapalı nesnesi çerçeveden " + Math.round(tasma) + " pt taşıyor (çerçeve [" +
                                Math.round(rU.fy1) + "," + Math.round(rU.fx1) + "," + Math.round(rU.fy2) + "," + Math.round(rU.fx2) +
                                "], nesne [" + Math.round(agb[0]) + "," + Math.round(agb[1]) + "," + Math.round(agb[2]) + "," + Math.round(agb[3]) + "]).");
                        }
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
                    if (ghost) {
                        droppedGhost++;
                        try { ignoredIds[itF.tf.id] = true; } catch (eIG4) {}
                        // v4.19: soru üzerindeki boş olmayan etiket/açıklama çerçevesi
                        // sabit kalmaz; içinde bulunduğu soruyla taşınır (aşağıda)
                        compCands.push({ it: itF.tf, b: [itF.fy1, itF.fx1, itF.fy2, itF.fx2] });
                        continue;
                    }
                }
                kept.push(itF);
            }

            // v4.19 SORUYA AİT SERBEST ÇERÇEVELER: soruyla gruplanmamış/çapalanmamış
            // görsel, şekil, tablo, etiket çerçeveleri v4.18'e kadar yerinde kalıyor,
            // soru taşınınca başka sorunun üstünde kalıyordu. Alanının en az %80'i bir
            // sorunun zarfı içinde olan çerçeve o sorunun parçası sayılır ve soruyla
            // birlikte taşınır; zarf bu çerçeveleri de kapsar.
            try {
                // sayfanın üst düzey grafikleri (metne çapalı olanlar bu koleksiyonlarda yer almaz)
                var fgCols = [pg.rectangles, pg.polygons, pg.ovals, pg.graphicLines];
                for (var fc = 0; fc < fgCols.length; fc++) {
                    var fgEl = itemsOf(fgCols[fc]);
                    var fgB = boundsOf(fgCols[fc], fgEl);
                    for (var fi = 0; fi < fgEl.length; fi++) {
                        if (!fgB[fi]) { continue; }
                        compCands.push({ it: fgEl[fi], b: fgB[fi], line: (fc === 3) });
                    }
                }
            } catch (eFG2) {}
            var compN = 0, compQs = [];
            for (k = 0; k < compCands.length; k++) {
                var cb = compCands[k].b;
                var cr = { y1: cb[0], x1: cb[1], y2: cb[2], x2: cb[3] };
                if (cr.y2 - cr.y1 < 1) { cr.y1 -= 0.5; cr.y2 += 0.5; }   // yatay çizgi
                if (cr.x2 - cr.x1 < 1) { cr.x1 -= 0.5; cr.x2 += 0.5; }   // dikey çizgi
                var cArea = (cr.x2 - cr.x1) * (cr.y2 - cr.y1);
                var bestQ = null, bestOv = 0;
                for (i = 0; i < kept.length; i++) {
                    if (kept[i].kind !== "soru") { continue; }
                    var ovC = ovArea(cr, kept[i]);
                    if (ovC > bestOv) { bestOv = ovC; bestQ = kept[i]; }
                }
                if (bestQ === null || bestOv < 0.8 * cArea) { continue; }
                compCands[k].assigned = true;
                if (!bestQ.comps) { bestQ.comps = []; }
                bestQ.comps.push({ it: compCands[k].it, b: [cb[0], cb[1], cb[2], cb[3]], cur: pi });
                compN++;
                if (bestQ.compLogged !== true) { bestQ.compLogged = true; compQs.push("S" + bestQ.num); }
            }
            for (k = 0; k < kept.length; k++) {
                var rC = kept[k];
                if (!rC.comps) { continue; }
                for (i = 0; i < rC.comps.length; i++) {
                    var bC = rC.comps[i].b;
                    if (bC[0] < rC.y1) { rC.y1 = bC[0]; }
                    if (bC[2] > rC.y2) { rC.y2 = bC[2]; }
                    if (bC[1] < rC.x1) { rC.x1 = bC[1]; }
                    if (bC[3] > rC.x2) { rC.x2 = bC[3]; }
                }
                rC.h = rC.y2 - rC.y1;
                rC.shape = ((rC.x2 - rC.x1) > pW * FW_RATIO) ? "FW" : "COL";
                rC.col = ((rC.x1 + rC.x2) / 2 < midX) ? 0 : 1;
            }
            // v4.19 GRAFİK ENGELLER: hiçbir soruya ait olmayan dikdörtgen/görsel/şekil
            // (başlık şeridi, yan panel, dekor) taşınan soruların girmemesi gereken
            // engellerdir. A'da zaten bir sorunun içinden geçen arka plan şekilleri hariç.
            var obstacles = [], dividers = [];
            for (k = 0; k < compCands.length; k++) {
                // v4.19: dikey sütun ayırıcı çizgi (blok kayarsa üst ucu blokla birlikte kayar)
                var cbD = compCands[k].b;
                if (!compCands[k].assigned && compCands[k].line === true && (cbD[3] - cbD[1]) < 3 && (cbD[2] - cbD[0]) > 30) {
                    dividers.push({ it: compCands[k].it, b: [cbD[0], cbD[1], cbD[2], cbD[3]] });
                }
            }
            for (k = 0; k < compCands.length; k++) {
                if (compCands[k].assigned) { continue; }
                var ob = compCands[k].b;
                if (ob[2] - ob[0] < 3 || ob[3] - ob[1] < 3) { continue; }   // çizgiler
                var bgOb = false;
                for (i = 0; i < kept.length; i++) {
                    if (kept[i].kind !== "soru") { continue; }
                    var dvO = Math.min(ob[2], kept[i].y2) - Math.max(ob[0], kept[i].y1);
                    var dhO = Math.min(ob[3], kept[i].x2) - Math.max(ob[1], kept[i].x1);
                    if (dvO > 3 && dhO > 3) { bgOb = true; break; }
                }
                if (!bgOb) { obstacles.push({ it: compCands[k].it, b: [ob[0], ob[1], ob[2], ob[3]] }); }
            }
            if (compN > 0) {
                compTotal += compN;
                log("Ayrıntı: s." + pg.name + " — soruyla gruplanmamış " + compN + " görsel/şekil/etiket çerçevesi ait olduğu soruyla (" +
                    compQs.join(", ") + ") birlikte taşınacak.");
            }
            if (droppedStub > 0) {
                log("UYARI: s." + pg.name + " — numarası olan ama içi boş " + droppedStub + " çerçeve (taslak artığı) yok sayıldı; A dosyasından silmeniz önerilir.");
            }
            if (droppedGhost > 0) {
                log("Ayrıntı: s." + pg.name + " — içi boş ya da süs amaçlı " + droppedGhost + " metin çerçevesi yok sayıldı (sorulara dokunulmadı).");
            }
            items = kept;
            // v4.26: ExtendScript'in sort'u kararlı değil; her karşılaştırıcı eşitliği kendisi çözer
            items.sort(function (a, b) { return (a.y1 - b.y1) || (a.x1 - b.x1) || (a.y2 - b.y2) || (a.num - b.num); });

            // bloklar
            var blocks = [];
            var rowPairs = [];   // v4.23: A'da aynı satırda başlayan sol/sağ soru çiftleri
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
                c0a.sort(function (a, b) { return (a.y1 - b.y1) || (a.x1 - b.x1) || (a.y2 - b.y2) || (a.num - b.num); });
                c1a.sort(function (a, b) { return (a.y1 - b.y1) || (a.x1 - b.x1) || (a.y2 - b.y2) || (a.num - b.num); });
                blocks[k].cols = [c0a, c1a];
                // v4.23 SATIR HİZASI: karşı sütunda aynı yükseklikten başlayan öğesi olan soru
                // "hizalı"dır; yerleşimde yukarı çekilmez, Faz 1 bu hizayı bozmayan sırayı seçer.
                for (var al0 = 0; al0 < c0a.length; al0++) {
                    for (var al1 = 0; al1 < c1a.length; al1++) {
                        if (c0a[al0] === c1a[al1]) { continue; }
                        var dAl = c0a[al0].y1 - c1a[al1].y1;
                        if (dAl > 3 || dAl < -3) { continue; }   // v4.24: tasarımdaki 1-3 pt'lik kaçıklık da satırdır
                        c0a[al0].aligned = true; c1a[al1].aligned = true;
                        if (c0a[al0].kind === "soru" && c1a[al1].kind === "soru") { rowPairs.push([c0a[al0], c1a[al1]]); }
                    }
                }
            }

            // v4.23: HB sabit çerçevelerin de sığdığı sayfa sınırıdır; altbilgi bandına konmuş
            // "... TESTİ BİTTİ." gibi bir çerçeve onu aşağı çekebilir. Sorular için ayrı sınır QB:
            // kenar boşluğu ya da A'da bu sayfada bir sorunun indiği en alt nokta (hangisi aşağıdaysa).
            // Böylece B'de hiçbir soru master altbilgisine (çizgi, sayfa no) inmez.
            var maxB = usableBottom, maxQB = usableBottom;
            for (k = 0; k < items.length; k++) {
                if (items[k].y2 > maxB) { maxB = items[k].y2; }
                if (items[k].kind === "soru" && items[k].y2 > maxQB) { maxQB = items[k].y2; }
            }

            pageData.push({ blocks: blocks, items: items, HB: maxB + 0.5, QB: maxQB + 0.5, rowPairs: rowPairs, label: pageLabel, textBlocks: textBlocks, introRanges: introRanges,
                            linkRanges: linkRanges, obstacles: obstacles, dividers: dividers,
                            bundleWith: -1, name: String(pg.name), ignoredIds: ignoredIds });
        }

        if (pbShiftPages.length > 0) {
            log("Ayrıntı: " + pbShiftPages.length + " sayfada (s." + pbShiftPages.slice(0, 12).join(", s.") + (pbShiftPages.length > 12 ? ", …" : "") +
                ") InDesign sayfa sınırını yayılım koordinatında bildirdi; öğelerin koordinatına göre düzeltildi (sütunlar doğru ayrıldı).");
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
                info("Ortaokul güvenli yerleşim modu kullanıldı (belge içeriğinden algılandı).");
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
        function addZone(sec, lo, hi, isLink) {
            if (!secZones[sec]) { secZones[sec] = []; }
            for (var z = 0; z < secZones[sec].length; z++) {
                if (secZones[sec][z].lo === lo && secZones[sec][z].hi === hi) {
                    if (isLink) { secZones[sec][z].link = true; }
                    return;
                }
            }
            secZones[sec].push({ lo: lo, hi: hi, link: (isLink === true) });
        }

        var spillN = 0, spillLog = [];
        var pendingLinks = [];   // v4.19: sorusu sonraki sayfada olan yönergeler
        for (pi = 0; pi < pageData.length; pi++) {
            (function (pd) {
                // v4.22: sayfada TEK bir "1." varsa yeni test SAYFA BAŞINDA başlamış sayılır; böylece
                // okuma sırası (çapalı görsellerin InDesign'ın bildirdiği konumuna göre değişebiliyor)
                // test ayrımını bozmaz. Önceki testin devamı olan numaralar (son sayıdan itibaren
                // ardışık) önceki teste yazılır; yeni testin 1. sorusundan SONRA okunanlar v4.3'teki
                // gibi yerinde kilitlenir. Sayfada iki "1." varsa eski (sıraya bağlı) yol kullanılır.
                var pqA = [], onesA = 0, oneIdxA = -1, qa2;
                pageQuestionWalk(pd, function (r) { if (r.kind === "soru") { pqA.push(r); } });
                for (qa2 = 0; qa2 < pqA.length; qa2++) {
                    if (pqA[qa2].num === 1) { onesA++; if (oneIdxA < 0) { oneIdxA = qa2; } }
                }
                if (onesA === 1 && seenAny) {
                    var prevSecA = secCount, prevCntA = secQCount[secCount] || 0;
                    secCount++;
                    var haveA = {}, contTo = prevCntA, usedA = {};
                    for (qa2 = 0; qa2 < pqA.length; qa2++) { haveA[pqA[qa2].num] = true; }
                    while (haveA[contTo + 1] && contTo + 1 !== 1) { contTo++; }
                    for (qa2 = 0; qa2 < pqA.length; qa2++) {
                        var rA = pqA[qa2];
                        if (rA.num !== 1 && rA.num > prevCntA && rA.num <= contTo && !usedA[rA.num]) {
                            usedA[rA.num] = true;
                            rA.sec = prevSecA;
                            secQCount[prevSecA] = (secQCount[prevSecA] || 0) + 1;
                            if (qa2 > oneIdxA) {
                                spillN++;
                                rA.grup = 900000 + spillN;   // kilit: hiçbir takasa girmez
                                spillLog.push("Test " + (prevSecA + 1) + " S" + rA.num + " (s." + pd.name + ")");
                            }
                            continue;
                        }
                        seenAny = true;
                        rA.sec = secCount;
                        secQCount[secCount] = (secQCount[secCount] || 0) + 1;
                    }
                } else {
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
                }
                for (var q = 0; q < pd.items.length; q++) {
                    if (pd.items[q].kind === "yonerge" && seenAny) {
                        addZone(secCount, pd.items[q].lo, pd.items[q].hi);
                    }
                }
                // v4.19: ortak metin yönergeleri, numarası aralıkta olan sorunun testine
                // yazılır (metin sayfası sorulardan önceyse sonraki sayfada eşlenir).
                var lnk = pendingLinks.concat(pd.linkRanges);
                pendingLinks = [];
                for (var lq = 0; lq < lnk.length; lq++) {
                    var lr = lnk[lq], secL = -1;
                    pageQuestionWalk(pd, function (r) {
                        if (secL < 0 && r.kind === "soru" && r.sec >= 0 && r.num >= lr.lo && r.num <= lr.hi) { secL = r.sec; }
                    });
                    if (secL >= 0) { addZone(secL, lr.lo, lr.hi, lr.link); }
                    else if ((lr.age || 0) < 1) {
                        pendingLinks.push({ lo: lr.lo, hi: lr.hi, link: lr.link, age: (lr.age || 0) + 1 });
                    }
                }
            })(pageData[pi]);
        }
        var totalSections = secCount + 1;
        if (spillLog.length > 0) {
            info("Önceki testin son sorusu yeni testin sayfasında; numarası korunarak yerinde bırakıldı: " + spillLog.join(", "));
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

        // v4.25: BRANŞ SINIRI — numaralar branşlar arasında sıfırlanmadan sürüyorsa (Türkçe 1-20,
        // Sosyal 21-30) test ortasında yeni bir "Bu testte N soru vardır." girişi görülür; girişten
        // sonraki ilk sorudan başlayan N soruluk aralık ayrı branş bölgesidir (takas sınırı).
        var branchZoneLog = [];
        for (pi = 0; pi < pageData.length; pi++) {
            var pdI = pageData[pi];
            if (pdI.introRanges.length > 0) { continue; }
            for (k = 0; k < pdI.items.length; k++) {
                var inI = pdI.items[k];
                if (inI.kind !== "intro" || !(inI.introN > 0)) { continue; }
                // v4.26: girişin altındaki EN KÜÇÜK numaralı soru (gezinme sırasından bağımsız; aynı hizadaki
                // sol/sağ sorularda sağdakinin seçilip "Test 2: 3-12" gibi yanlış bölge oluşması önlenir)
                var q0I = null;
                for (var pq0 = pi; pq0 < pageData.length && q0I === null && pq0 <= pi + 1; pq0++) {
                    pageQuestionWalk(pageData[pq0], function (r) {
                        if (r.kind === "soru" && r.sec >= 0 && (pq0 > pi || r.y1 >= inI.y1 - 2) &&
                            (q0I === null || r.num < q0I.num)) { q0I = r; }
                    });
                }
                if (q0I === null || q0I.num <= 1) { continue; }
                // bölge ancak test girişte yazandan fazla soru içeriyorsa (numaralar branşlar arasında sürüyorsa) anlamlıdır
                if (!((secQCount[q0I.sec] || 0) > inI.introN) || q0I.num + inI.introN - 1 > (secQCount[q0I.sec] || 0)) { continue; }
                addZone(q0I.sec, q0I.num, q0I.num + inI.introN - 1);
                branchZoneLog.push("Test " + (q0I.sec + 1) + ": " + q0I.num + "-" + (q0I.num + inI.introN - 1) + " (s." + pdI.name + ")");
            }
        }
        if (branchZoneLog.length > 0) {
            info("Numaraları kesintisiz süren branşlar ayrıldı (takaslar branş içinde kalır): " + branchZoneLog.join(", "));
        }

        // v4.19: iç içe bölgelerde EN DAR olan seçilir (ör. ders bölgesi 25-34 içindeki
        // 27-28 ortak metin grubu); eşit genişlikte ilk eklenen geçerli kalır.
        function zoneOf(sec, num) {
            var zl = secZones[sec];
            if (!zl) { return 0; }
            var bestZ = 0, bestW = 100000;
            for (var z = 0; z < zl.length; z++) {
                if (num >= zl[z].lo && num <= zl[z].hi && (zl[z].hi - zl[z].lo) < bestW) {
                    bestZ = z + 1; bestW = zl[z].hi - zl[z].lo;
                }
            }
            return bestZ;
        }
        function isLinkZone(sec, z) {
            return z > 0 && secZones[sec] && secZones[sec][z - 1] && secZones[sec][z - 1].link === true;
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
            log("UYARI: Bir testin sorusu önceki testin soruları arasında okundu: " + strayFix.join(", ") +
                " — kendi testine sayıldı, numarası korunarak yerinde bırakıldı. A dosyasında yerini kontrol edin.");
        }
        if (dupList.length > 0) {
            log("KRİTİK: Aynı testte aynı numaralı iki soru var: " + dupList.join(", ") +
                " — ikisi de yerinde bırakıldı ve cevap anahtarına yazılmadı; A dosyasını düzeltin.");
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
                info("Özel havuz " + poolIdx + " (\u201C" + ent + "\u201D): " + cnt + " soru" +
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

        // -----------------------------------------------------
        // v4.19 ORTAK METİN GÜVENLİĞİ
        //  a) Yönergeyi/ortak metni kendi içinde taşıyan soru yerinde kilitlenir
        //     (taşınsa metin, ona bağlı soruların altına düşerdi).
        //  b) Hiçbir ortak metin grubunda olmayıp gövdesi "Buna göre", "Bu metne göre",
        //     "Yukarıdaki ..." gibi DIŞARIDAKİ bir metne/görsele gönderme ile başlayan
        //     soru yerinde kilitlenir (yönergesi yazılmamış bağlı soru için güvenlik ağı).
        //     Özel havuzdaki sorulara (b) uygulanmaz; havuz kullanıcı kararıdır.
        // -----------------------------------------------------
        // Güçlü gönderme: dışarıdaki METNE (her zaman kilit nedeni).
        var REF_START_RE = /^(bu\s+(metn|metin|par[çc]a|[öo]yk[üu]|hik[âa]ye|[şs]iir|diyalo|konu[şs]ma)|yukar[ıi]daki\s+(metn|metin|par[çc]a|[öo]yk[üu]|hik[âa]ye|[şs]iir|diyalo)|metne\s+g[öo]re|metinde|metnin|par[çc]aya\s+g[öo]re|par[çc]ada|[şs]iirde|according\s+to\s+the\s+(texts?|passage|dialogue|conversation|story|e-?mail|letter|paragraphs?|poem|article)|based\s+on\s+the\s+(texts?|passage|dialogue|conversation|story))/i;
        // Zayıf gönderme: "Buna göre", tablo/grafik/görsel — soru kendi görselini taşıyorsa ona aittir.
        var REF_WEAK_RE = /^(buna\s+g[öo]re|bu\s+(tablo|grafi|g[öo]rsel|harita|bilgi|veri|[şs]ekil)|yukar[ıi]daki|tabloya\s+g[öo]re|grafi[ğg]e\s+g[öo]re|[şs]ekle\s+g[öo]re|verilen\s+bilgilere\s+g[öo]re|tablo(da|daki)\s|grafi(kte|kteki|ğe)\s|[şs]ekil(de|deki)\s|harita(da|daki)\s|g[öo]rsel(de|deki)\s|according\s+to\s+the\s+(chart|table|graph|picture|information|map|poster|advertisement|schedule|menu|survey|results))/i;
        // v4.26: "bu …den/…dan" ve "yukarıdaki …" göndermeleri metnin herhangi bir yerinde, KELİME KELİME
        // aranır. Eski tek parça düzenli ifade InDesign'ın (ExtendScript) motorunda, pencere bir kelimenin
        // ortasında bittiğinde ("… ve bu devletle") yanlış eşleşiyor, gönderme yapmayan soruları kilitliyordu.
        var CUE_LET_RE = /[A-Za-z\u00C7\u011E\u0130\u00D6\u015E\u00DC\u00E7\u011F\u0131\u00F6\u015F\u00FC\u00C2\u00CE\u00DB\u00E2\u00EE\u00FB]/;
        var CUE_BU_STEMS = ["\u00F6yk\u00FC", "oyk\u00FC", "\u00F6yku", "oyku", "hik\u00E2ye", "hikaye", "\u015Fiir", "siir", "metin", "metn", "par\u00E7a", "parca"];
        var CUE_YUK_STEMS = CUE_BU_STEMS.concat(["tablo", "grafi", "g\u00F6rsel", "gorsel", "harita"]);
        // metnin ilk n karakteri; n'inci karakter bir kelimenin ortasına düşüyorsa yarım kelime atılır,
        // sonuna boşluk eklenir (düzenli ifade hiçbir zaman metnin sonuna yarım kelimeyle dayanmaz)
        function cueWin(t, n) {
            var ts = String(t), w = ts.substr(0, n);
            if (ts.length > n && CUE_LET_RE.test(ts.charAt(n))) {
                var e = w.length;
                while (e > 0 && CUE_LET_RE.test(w.charAt(e - 1))) { e--; }
                w = w.substr(0, e);
            }
            return w + " ";
        }
        function startsAnyCue(w, arr) {
            for (var a = 0; a < arr.length; a++) { if (w.substr(0, arr[a].length) === arr[a]) { return true; } }
            return false;
        }
        function onlySpace(g) { return g.length > 0 && g.replace(/\s+/g, "") === ""; }
        // gönderme kelimesinin konumu (yoksa -1)
        function refAnyIndex(t) {
            var ts = String(t);
            var lowT = ts.replace(/\u0130/g, "i").replace(/I/g, "\u0131").toLowerCase();
            var lowE = ts.replace(/\u0130/g, "i").toLowerCase();
            if (lowT.length !== ts.length || lowE.length !== ts.length) { return -1; }
            var words = [], st = -1, i;
            for (i = 0; i <= lowT.length; i++) {
                var isL = (i < lowT.length) && CUE_LET_RE.test(lowT.charAt(i));
                if (isL && st < 0) { st = i; }
                if (!isL && st >= 0) { words.push({ s: st, e: i }); st = -1; }
            }
            for (i = 0; i + 1 < words.length; i++) {
                if (!onlySpace(lowT.substring(words[i].e, words[i + 1].s))) { continue; }
                var a = lowT.substring(words[i].s, words[i].e), b = lowT.substring(words[i + 1].s, words[i + 1].e);
                if ((a === "yukar\u0131daki" || a === "yukaridaki") && startsAnyCue(b, CUE_YUK_STEMS)) { return words[i].s; }
                if (a === "bu" && b.length > 4 && startsAnyCue(b, CUE_BU_STEMS)) {
                    var suf = b.substr(b.length - 3);
                    if (suf === "den" || suf === "dan" || suf === "ten" || suf === "tan") { return words[i].s; }
                }
                var aE = lowE.substring(words[i].s, words[i].e), bE = lowE.substring(words[i + 1].s, words[i + 1].e);
                if (aE === "the" && (bE === "text" || bE === "texts" || bE === "passage" || bE === "dialogue" || bE === "conversation") &&
                    i + 2 < words.length && onlySpace(lowE.substring(words[i + 1].e, words[i + 2].s)) &&
                    lowE.substring(words[i + 2].s, words[i + 2].e) === "above") { return words[i].s; }
            }
            return -1;
        }
        var carrierLock = [], cueLock = [];
        for (k = 0; k < allSlots.length; k++) {
            var rL = allSlots[k];
            if (rL.grup >= 600000) { continue; }   // zaten kilitli
            var tagL = "Test " + (rL.sec + 1) + " S" + rL.num + " (s." + pageData[rL.pdIdx].name + ")";
            if (rL.carrier) {
                rL.grup = 600000 + k;
                carrierLock.push(tagL);
                continue;
            }
            if (rL.grup !== 0 || rL.pool > 0 || isLinkZone(rL.sec, rL.zone)) { continue; }
            var hdRaw = String(rL.head || "");
            var ownVisual = rL.hasVisual === true || (rL.comps && rL.comps.length > 0) || hdRaw.indexOf("\uFFFC") >= 0;
            // Gövde, sorunun KENDİ çapalı içeriğiyle (metin kutusu/görsel) başlıyorsa gönderme
            // o içeriğedir ("1.⏎[metin]⏎Bu metne göre ...") — soru metniyle birlikte taşınır.
            var hd0 = hdRaw.replace(/^[\s\u200B\uFEFF\u009E]+/, "");
            if (hd0.charAt(0) === "\uFFFC") { continue; }
            var hd = cueWin(trimS(hd0), 160);
            var iAny = refAnyIndex(cueWin(hd0, 100)), fpos = hd0.indexOf("\uFFFC");
            var anyHit = (iAny >= 0) && (fpos < 0 || fpos > iAny);
            if (REF_START_RE.test(hd) || anyHit || (!ownVisual && REF_WEAK_RE.test(hd))) {
                rL.grup = 650000 + k;
                cueLock.push(tagL);
                // v4.25: gönderilen metni kendi grubunda taşıyan bir önceki soru (aynı sayfa) da yerinde kalır
                var prevQ = null;
                pageQuestionWalk(pageData[rL.pdIdx], function (r) {
                    if (r.kind === "soru" && r.sec === rL.sec && r.num === rL.num - 1) { prevQ = r; }
                });
                if (prevQ !== null && prevQ.bigText && prevQ.grup === 0 && !prevQ.carrier) {
                    prevQ.carrier = true; prevQ.grup = 600000 + k;
                    carrierLock.push("Test " + (prevQ.sec + 1) + " S" + prevQ.num + " (s." + pageData[prevQ.pdIdx].name + ")");
                }
            }
        }
        // v4.25 GÜVENLİK AĞI: sayfada soru dışı uzun bir metin (olası ortak metin) var ama yönergesi
        // tanınmadıysa ("8 ve 9. soruları..." / "Answer the questions..." dışında bir yazım), o sayfanın
        // soruları başka sayfaya taşınmaz (yalnız kendi sayfasında karışır) ve DİKKAT'te bildirilir.
        var orphanPg = [];
        for (pi = 0; pi < pageData.length; pi++) {
            var pdOr = pageData[pi], qOr = [], linkedOr = false;
            pageQuestionWalk(pdOr, function (r) {
                if (r.kind !== "soru") { return; }
                qOr.push(r);
                if (isLinkZone(r.sec, r.zone)) { linkedOr = true; }
            });
            if (qOr.length === 0 || linkedOr || pdOr.linkRanges.length > 0) { continue; }
            var bigOr = null;
            for (k = 0; k < pdOr.items.length; k++) {
                var itOr = pdOr.items[k];
                if (itOr.kind === "soru" || itOr.kind === "intro" || itOr.emptyText) { continue; }
                if (itOr.y2 - itOr.y1 >= 40 && itOr.x2 - itOr.x1 >= 150 && (itOr.txtLen || 0) >= 60) { bigOr = itOr; break; }
            }
            if (bigOr === null) {
                var tbs = pdOr.textBlocks || [];
                for (k = 0; k < tbs.length; k++) {
                    if (tbs[k].y2 - tbs[k].y1 >= 40 && tbs[k].x2 - tbs[k].x1 >= 150) {
                        // bir sorunun zarfı içindeyse (soruya ait görsel/etiket) ortak metin değildir
                        var inQ = false;
                        for (var qz = 0; qz < qOr.length; qz++) {
                            if (tbs[k].y1 >= qOr[qz].y1 - 2 && tbs[k].y2 <= qOr[qz].y2 + 2 && tbs[k].x1 >= qOr[qz].x1 - 2 && tbs[k].x2 <= qOr[qz].x2 + 2) { inQ = true; break; }
                        }
                        if (!inQ) { bigOr = tbs[k]; break; }
                    }
                }
            }
            if (bigOr === null) { continue; }
            for (k = 0; k < qOr.length; k++) { qOr[k].noXPage = true; qOr[k].orphanPg = true; }
            // metnin altındaki sorular okuma sırasıyla; ilki gönderme yapıyorsa (kilitliyse) ardışık
            // gönderme yapan sorular örtük ortak metin grubu olur (kendi aralarında karışır). Hiçbiri
            // gönderme yapmıyorsa grubun nereye kadar sürdüğü bilinemez: metnin altındakiler yerinde kalır.
            var belowOr = [];
            for (k = 0; k < qOr.length; k++) {
                if (qOr[k].y1 >= bigOr.y2 - 6 && qOr[k].pool === 0) { belowOr.push(qOr[k]); }
            }
            belowOr.sort(function (a, b) { return (a.num - b.num) || (a.y1 - b.y1) || (a.x1 - b.x1); });
            var runOr = [];
            for (k = 0; k < belowOr.length; k++) {
                var isCue = belowOr[k].grup >= 650000 && belowOr[k].grup < 700000;
                if (!isCue || (runOr.length > 0 && (belowOr[k].num !== runOr[runOr.length - 1].num + 1 || belowOr[k].sec !== runOr[0].sec))) { break; }
                runOr.push(belowOr[k]);
            }
            var grpTxt = "";
            if (runOr.length >= 2) {
                var loO = runOr[0].num, hiO = runOr[runOr.length - 1].num, secO = runOr[0].sec;
                addZone(secO, loO, hiO, true);
                var znO = zoneOf(secO, loO);
                for (k = 0; k < runOr.length; k++) {
                    var tagO = "Test " + (secO + 1) + " S" + runOr[k].num + " (s." + pdOr.name + ")";
                    for (var cq9 = cueLock.length - 1; cq9 >= 0; cq9--) { if (cueLock[cq9] === tagO) { cueLock.splice(cq9, 1); } }
                    runOr[k].grup = 0; runOr[k].zone = znO;
                }
                grpTxt = ", " + loO + "-" + hiO + " kendi içinde karıştı";
            } else if (runOr.length === 0 && belowOr.length > 0 && !(belowOr[0].grup >= 600000)) {
                // işaret yok: metnin altındaki sorular yerinde kalır (kilit)
                for (k = 0; k < belowOr.length; k++) {
                    if (belowOr[k].grup === 0) { belowOr[k].grup = 660000 + orphanPg.length * 100 + k; belowOr[k].orphanLock = true; }
                }
                grpTxt = ", altındaki sorular yerinde bırakıldı";
            }
            orphanPg.push("s." + pdOr.name + " (" + (bigOr.etiket === "grup" ? "metin grubu" : "\u2018" + bigOr.etiket + "\u2019") + grpTxt + ")");
        }
        if (orphanPg.length > 0) {
            log("UYARI: " + orphanPg.join(", ") + " — soru dışı uzun metin var ama hangi sorulara ait olduğunu söyleyen yönerge " +
                "tanınmadı; bu sayfaların soruları başka sayfaya taşınmadı (yalnız kendi sayfasında karıştı). Metne bağlı soru varsa kontrol edin.");
        }

        var linkLog = [];
        for (k = 0; k < totalSections; k++) {
            var lzs = [];
            if (secZones[k]) {
                for (j = 0; j < secZones[k].length; j++) {
                    if (secZones[k][j].link) { lzs.push(secZones[k][j].lo + "-" + secZones[k][j].hi); }
                }
            }
            if (lzs.length > 0) { linkLog.push("Test " + (k + 1) + ": " + lzs.join(", ")); }
        }
        if (linkLog.length > 0) {
            info("Ortak metinli soru grupları korundu (yalnız kendi içinde karıştı): " + linkLog.join("  |  "));
        } else {
            log("Ayrıntı: ortak metin yönergesi (\u201C8 ve 9. soruları ... göre\u201D vb.) bulunamadı.");
        }
        if (carrierLock.length > 0) {
            log("Ayrıntı: ortak metni/yönergeyi kendi içinde taşıyan soru yerinde bırakıldı: " + carrierLock.join(", "));
        }
        if (cueLock.length > 0) {
            log("Ayrıntı: yönergesi bulunamayan ama dışarıdaki bir metne/görsele gönderme yapan soru yerinde bırakıldı: " + cueLock.join(", "));
        }

        if (compTotal > 0) {
            info("Soruyla gruplanmamış " + compTotal + " görsel/şekil/etiket, ait olduğu soruyla birlikte taşınacak.");
        }
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
        log("Ayrıntı: envanter — " + pages.length + " sayfa (" + skippedPages + " sorusuz sayfa), " +
            totalSections + " test, " + totalQ + " soru (" + fwQ + " tam genişlik, " + colQ + " sütun).");
        log("Ayrıntı: ders bölgeleri — " + zi2.join("  |  "));
        var testLine = [];
        for (k = 0; k < totalSections; k++) { testLine.push("Test " + (k + 1) + ": " + (secQCount[k] || 0) + " soru"); }
        info("Bulunan testler — " + testLine.join(", ") + " (toplam " + totalQ + " soru).");


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

        function layoutAt(pd, assign, lv) { return tryLayoutScale(pd, assign, LEVELS[lv].s, LEVELS[lv].a); }
        function tryLayoutScale(pd, assign, scale, anchored) {
            var plc = [];
            var cursor = null, prevBotOld = null;
            // v4.19 ÜST HİZA: sıkıştırma yalnız SORULAR arasındaki boşluklara uygulanır;
            // sabit bir bloktan (başlık, test girişi, yönerge, ortak metin) sonraki ilk
            // soru A'daki uzaklığını korur (aksi hâlde sayfanın soru başlangıç hizası
            // yukarı kayıyor, sorular üstteki başlık şeridine giriyordu).
            var prevFixed = false;
            var regs = [];
            function ag(x) { return (x <= 0) ? x : ((x < ANCHOR_MIN_GAP) ? x : ANCHOR_MIN_GAP); }
            // v4.24: alta sığdırmada izin verilen en dar aralık: A'daki aralığın yarısı (en az GAP_FLOOR),
            // ama hiçbir zaman ag()'den geniş değil
            function gp(x) {
                if (x <= 0) { return x; }
                var hv = x * 0.5, fl = (x < GAP_FLOOR) ? x : GAP_FLOOR;
                var v = (hv > fl) ? hv : fl, a = ag(x);
                return (v < a) ? v : a;
            }
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
                        var gReq = prevFixed ? MIN_GAP : TAIL_GAP;
                        var minG = (gap < gReq) ? gap : gReq;
                        if (ntF < cursor + minG - 0.01) { return null; }
                    }
                    cursor = blk.bot; prevBotOld = blk.bot;
                    prevFixed = true;
                } else if (blk.type === "FWQ") {
                    var contQ = assign[blk.it.slotKey];
                    var ntQ = (cursor === null) ? blk.top : (cursor + (prevFixed ? gap : (anchored ? ag(gap) : gg(gap))));
                    if (anchored && ntQ < blk.top) { ntQ = blk.top; }
                    if (isMiddleSchool) {
                        var msFwBarrier = middleSchoolIntroBarrier(pd, blk.it);
                        if (msFwBarrier !== null && ntQ < msFwBarrier) { ntQ = msFwBarrier; }
                    }
                    plc.push({ slot: blk.it, cont: contQ, ny1: ntQ });
                    if (ntQ + contQ.h > pd.QB) { return null; }
                    cursor = ntQ + contQ.h; prevBotOld = blk.bot;
                    prevFixed = false;
                } else {
                    var shift = (cursor === null) ? 0 : ((cursor + (prevFixed ? gap : (anchored ? ag(gap) : gg(gap)))) - blk.top);
                    if (anchored && shift < 0) { shift = 0; }
                    regs.push({ top: blk.top, bot: blk.bot, shift: shift });
                    var regBot = null, regHasQ = false, plcStart = plc.length;
                    for (var c2 = 0; c2 < 2; c2++) {
                        var pB = null, pBold = null, cPrevFixed = false;
                        // v4.23/v4.24 ALTA SIĞDIRMA: sayfanın son bloğunda, altında sabit öğe olmayan
                        // sütun sorusu A konumunda sayfaya sığmıyorsa, karşı sütunla satır hizası
                        // yoksa yalnız gerektiği kadar yukarı alınır; diğer sütun A'daki yerinde kalır
                        // (önceden 1 pt'lik taşma bile tüm sayfayı sıkıştırmalı düzene geçiriyordu).
                        // sufH[t]: t'den sütun sonuna kadar en sıkı (gp aralıklı) yükseklik.
                        var sufH = null;
                        if (anchored && b === pd.blocks.length - 1) {
                            sufH = [];
                            var colS = blk.cols[c2], accS = -1;
                            for (var t3 = colS.length - 1; t3 >= 0; t3--) {
                                if (colS[t3].kind !== "soru" || (t3 < colS.length - 1 && accS < 0)) { accS = -1; sufH[t3] = -1; continue; }
                                var hS = assign[colS[t3].slotKey].h;
                                accS = (accS < 0) ? hS : (hS + gp(colS[t3 + 1].y1 - colS[t3].y2) + accS);
                                sufH[t3] = accS;
                            }
                        }
                        for (var t2 = 0; t2 < blk.cols[c2].length; t2++) {
                            var it2 = blk.cols[c2][t2];
                            var g2 = (pBold === null) ? null : (it2.y1 - pBold);
                            if (it2.kind !== "soru") {
                                var ntX = it2.y1 + shift;
                                if (isMiddleSchool) { ntX = it2.y1; }
                                if (pB !== null && g2 !== null) {
                                    var gReq2 = cPrevFixed ? MIN_GAP : TAIL_GAP;
                                    var mg2 = (g2 < gReq2) ? g2 : gReq2;
                                    if (ntX < pB + mg2 - 0.01) { return null; }
                                }
                                pB = it2.y2 + shift; pBold = it2.y2;
                                if (isMiddleSchool) { pB = it2.y2; }
                                cPrevFixed = true;
                            } else {
                                var cont2 = assign[it2.slotKey];
                                var nt2 = (pB === null) ? (it2.y1 + shift) : (pB + (cPrevFixed ? g2 : (anchored ? ag(g2) : gg(g2))));
                                var cPrevFixedB = cPrevFixed;
                                cPrevFixed = false;
                                regHasQ = true;
                                if (isMiddleSchool) {
                                    if (pB === null) {
                                        var msBarrier = middleSchoolIntroBarrier(pd, it2);
                                        if (msBarrier !== null && nt2 < msBarrier) { nt2 = msBarrier; }
                                    } else if (!anchored && g2 !== null && g2 > MIDDLE_SCHOOL_GAP_CAP) {
                                        nt2 = pB + gg(MIDDLE_SCHOOL_GAP_CAP);
                                    }
                                }
                                var prevWasFixed = cPrevFixedB;
                                if (anchored && nt2 < it2.y1 + shift) { nt2 = it2.y1 + shift; }
                                // v4.24 ALTA SIĞDIRMA: sütun sayfaya sığmıyorsa yalnız bu soru gerektiği kadar
                                // yukarı alınır (üstündekine en az gp(boşluk); sabit öğeden sonra A'daki boşluk).
                                if (anchored && sufH !== null && sufH[t2] >= 0 && !it2.aligned && pB !== null) {
                                    var latY = pd.QB - 0.5 - sufH[t2];
                                    if (latY < nt2) {
                                        var minY = pB + (prevWasFixed ? g2 : gp(g2));
                                        nt2 = (latY > minY) ? latY : minY;
                                    }
                                }
                                plc.push({ slot: it2, cont: cont2, ny1: nt2 });
                                if (nt2 + cont2.h > pd.QB) { return null; }
                                pB = nt2 + cont2.h; pBold = it2.y2;
                            }
                            if (pB !== null && (regBot === null || pB > regBot)) { regBot = pB; }
                        }
                    }
                    // v4.24 SATIR EŞİTLEME: A'da aynı satırdan başlayan sol/sağ sorulardan biri
                    // (üstündeki içerik uzadığı için) aşağı itildiyse karşı sütundaki de aynı hizaya
                    // indirilir; altında sabit öğe olan ya da sayfaya sığmayan sütunda yapılmaz.
                    if (pd.rowPairs && pd.rowPairs.length > 0 && plc.length > plcStart) {
                        var byK = {};
                        for (var e6 = plcStart; e6 < plc.length; e6++) { byK[plc[e6].slot.slotKey] = plc[e6]; }
                        for (var rp6 = 0; rp6 < pd.rowPairs.length; rp6++) {
                            var pL = pd.rowPairs[rp6][0], pR = pd.rowPairs[rp6][1];
                            var eL = byK[pL.slotKey], eR = byK[pR.slotKey];
                            if (!eL || !eR) { continue; }
                            var dA6 = pL.y1 - pR.y1, cur6 = eL.ny1 - eR.ny1;
                            if (cur6 - dA6 <= 1 && dA6 - cur6 <= 1) { continue; }
                            var ci6 = (cur6 < dA6) ? 0 : 1, del6 = (cur6 < dA6) ? (dA6 - cur6) : (cur6 - dA6);
                            var col6 = blk.cols[ci6], tg6 = (ci6 === 0) ? pL : pR, k6 = -1, t6, fixB = false;
                            for (t6 = 0; t6 < col6.length; t6++) { if (col6[t6] === tg6) { k6 = t6; } else if (k6 >= 0 && col6[t6].kind !== "soru") { fixB = true; } }
                            if (k6 < 0 || fixB) { continue; }
                            var okS = true;
                            for (t6 = k6; t6 < col6.length; t6++) {
                                var en6 = byK[col6[t6].slotKey];
                                if (en6 && en6.ny1 + del6 + en6.cont.h > pd.QB) { okS = false; }
                            }
                            if (!okS) { continue; }
                            for (t6 = k6; t6 < col6.length; t6++) {
                                var en7 = byK[col6[t6].slotKey];
                                if (en7) {
                                    en7.ny1 += del6;
                                    if (regBot === null || en7.ny1 + en7.cont.h > regBot) { regBot = en7.ny1 + en7.cont.h; }
                                }
                            }
                        }
                    }
                    cursor = (regBot !== null) ? regBot : (blk.bot + shift);
                    prevBotOld = blk.bot;
                    prevFixed = !regHasQ;
                }
                if (cursor !== null && cursor > pd.HB) { return null; }
            }
            plc.regs = regs;
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
                if (rects[qx][2] > pd.QB + 2) { return false; }
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

        // v4.19: yerleşim, sayfadaki grafik engellerin (başlık şeridi, dekor) içine girmemeli.
        function obstacleSafe(pd, plc) {
            if (!pd.obstacles || pd.obstacles.length === 0 || plc === null) { return true; }
            for (var qo2 = 0; qo2 < plc.length; qo2++) {
                var pq = plc[qo2];
                var r0 = pq.ny1, r1 = pq.slot.x1, r2 = pq.ny1 + (pq.cont.y2 - pq.cont.y1), r3 = pq.slot.x1 + (pq.cont.x2 - pq.cont.x1);
                for (var ob2 = 0; ob2 < pd.obstacles.length; ob2++) {
                    var obb = pd.obstacles[ob2].b;
                    var dvq = Math.min(r2, obb[2]) - Math.max(r0, obb[0]);
                    var dhq = Math.min(r3, obb[3]) - Math.max(r1, obb[1]);
                    if (dvq > 1 && dhq > 1) { return false; }
                }
            }
            return true;
        }

        // v4.20: başarılı düzeyin yerleşimi saklanır (aynı hesabı tekrar yapmamak için)
        var lastFitPlc = null;
        function fitLevel(pd, assign) {
            lastFitPlc = null;
            for (var si = 0; si < LEVELS.length; si++) {
                if (isMiddleSchool) {
                    var middleSchoolPlc = layoutAt(pd, assign, si);
                    if (middleSchoolPlc !== null && middleSchoolLayoutSafe(pd, middleSchoolPlc) &&
                        obstacleSafe(pd, middleSchoolPlc)) { lastFitPlc = middleSchoolPlc; return si; }
                    continue;
                }
                var plcF = layoutAt(pd, assign, si);
                if (plcF !== null && obstacleSafe(pd, plcF)) { lastFitPlc = plcF; return si; }
            }
            return -1;
        }

        // v4.15/v4.19: sıkıştırmasız güvenli yerleşim (ikinci şans ve sütun içi ikili mod)
        function strictPlc(pdX, assignX) {
            for (var sv = 0; sv < 2; sv++) {
                var pX = tryLayoutScale(pdX, assignX, 1.0, sv === 0);
                if (pX === null || !obstacleSafe(pdX, pX)) { continue; }
                if (isMiddleSchool && !middleSchoolLayoutSafe(pdX, pX)) { continue; }
                return pX;
            }
            return null;
        }

        // v4.25: iki sayfanın üst bant branş etiketi (ikisinde de varsa) aynı mı
        function sameBranchPages(p1, p2) {
            var l1 = pageData[p1].label, l2 = pageData[p2].label;
            return !(l1 && l2 && l1 !== l2);
        }
        // v4.23: A'da aynı satırda başlayan sol/sağ soru çiftlerinden B yerleşiminde
        // aynı satırda başlamayanların sayısı (satır hizası bozulması).
        function rowBreaks(pdR, plcR) {
            if (plcR === null || !pdR.rowPairs || pdR.rowPairs.length === 0) { return 0; }
            var nyR = {};
            for (var qR = 0; qR < plcR.length; qR++) { nyR[plcR[qR].slot.slotKey] = plcR[qR].ny1; }
            var nBr = 0;
            for (var rR = 0; rR < pdR.rowPairs.length; rR++) {
                var yA = nyR[pdR.rowPairs[rR][0].slotKey], yB = nyR[pdR.rowPairs[rR][1].slotKey];
                if (yA === undefined || yB === undefined) { continue; }
                var dRA = pdR.rowPairs[rR][0].y1 - pdR.rowPairs[rR][1].y1;
                if (Math.abs(yA - yB) > Math.abs(dRA) + 1) { nBr++; }
            }
            return nBr;
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

        progress("Sayfa içi karışım…", true);
        for (pi = 0; pi < pageData.length; pi++) {
            progress("Sayfa içi karışım: " + (pi + 1) + " / " + pageData.length);
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
                    if (strictPlc(pd, trialC) !== null) {
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

                var best = null, bestD = -1, bestL = 99, bestS = -1, bestP = 100000, bestK = 100000;
                var feasStrict = [], feasComp = [];
                for (var pp = 0; pp < perms.length; pp++) {
                    var pr2 = perms[pp];
                    var trial = copyAssign(assign);
                    for (k = 0; k < mQ; k++) { trial[grp[k].slotKey] = contents[pr2[k]]; }
                    var lvl = fitLevel(pd, trial);
                    if (lvl < 0) { continue; }
                    var plcP = lastFitPlc;
                    var disp = 0, sumd = 0;
                    for (k = 0; k < mQ; k++) {
                        if (pr2[k] !== k) { disp++; }
                        sumd += (pr2[k] > k) ? (pr2[k] - k) : (k - pr2[k]);
                    }
                    if (mode === "rnd") {
                        // v4.23: hizayı bozmayan karışımlar arasından seçilir; hepsi bozuyorsa
                        // soru Faz 2/2c'ye bırakılır (çapraz moddaki kural).
                        if (disp > 0 && rowBreaks(pd, plcP) === 0) { if (lvl === 0) { feasStrict.push(pr2); } else { feasComp.push(pr2); } }
                        continue;
                    }
                    // v4.19: eşit karışım ve düzeyde, soruları A'daki yerinden en az kaydıran
                    // permütasyon seçilir (satır hizası korunur).
                    // v4.23: A'daki satır hizasını bozan sıra en sona kalır; bu yüzden yerinde
                    // kalan soru, Faz 2'de başka sayfayla, olmazsa Faz 2c'de yeniden denenir.
                    var pen = 0;
                    var brk = rowBreaks(pd, plcP);
                    if (plcP !== null && (brk < bestK || (brk === bestK && (disp > bestD || (disp === bestD && lvl <= bestL))))) {
                        for (k = 0; k < plcP.length; k++) {
                            var dyP = plcP[k].ny1 - plcP[k].slot.y1;
                            if (dyP > 0.5 || dyP < -0.5) { pen++; }
                        }
                    }
                    var better = (brk < bestK) || (brk === bestK && (
                                 (disp > bestD) ||
                                 (disp === bestD && lvl < bestL) ||
                                 (disp === bestD && lvl === bestL && pen < bestP) ||
                                 (disp === bestD && lvl === bestL && pen === bestP && sumd > bestS)));
                    if (better) {
                        best = pr2; bestD = disp; bestL = lvl; bestS = sumd; bestP = pen; bestK = brk;
                        if (disp === mQ && lvl === 0 && pen === 0) {
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
        progress("Sayfalar arası takas…", true);
        if (chkXPage.value && mode !== "col") {
            for (var pass2 = 0; pass2 < 2; pass2++) {
                var stuck = [];
                for (k = 0; k < allSlots.length; k++) {
                    var S0 = allSlots[k];
                    if (S0.grup === 0 && !S0.noXPage && assigns[S0.pdIdx][S0.slotKey] === S0) { stuck.push(S0); }
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
                        if (contT0.noXPage) { continue; }   // v4.24: grup üyesi sayfasından çıkamaz
                        if (!sameBranchPages(S.pdIdx, T.pdIdx)) { continue; }   // v4.25: üst bant branşı
                        var dh = contS.h - contT0.h; if (dh < 0) { dh = -dh; }
                        var dp = T.pdIdx - S.pdIdx; if (dp < 0) { dp = -dp; }
                        cands.push({ pri: (contT0 === T ? 0 : 1), dh: dh, dp: dp, num: T.num, T: T });
                    }
                    cands.sort(function (a, b) {
                        return (a.pri - b.pri) || (a.dh - b.dh) || (a.dp - b.dp) || (a.num - b.num) || (a.T.pdIdx - b.T.pdIdx) || (a.T.x1 - b.T.x1);
                    });
                    var done = false;
                    // v4.23: geçiş 0: sıkıştırmasız ve satır hizasını bozmadan; 1: hizayı bozmadan;
                    // 2: (yalnız hiza yüzünden reddedilen aday varsa) hizayı bozarak.
                    for (var sPass = 0; sPass < 3 && !done; sPass++) {
                        var rejBrk = false;
                        for (j = 0; j < cands.length; j++) {
                            var T2 = cands[j].T;
                            var contT = assigns[T2.pdIdx][T2.slotKey];
                            var tA = copyAssign(assigns[S.pdIdx]); tA[S.slotKey] = contT;
                            var tB = copyAssign(assigns[T2.pdIdx]); tB[T2.slotKey] = contS;
                            var la = fitLevel(pageData[S.pdIdx], tA);
                            if (la < 0) { continue; }
                            var brA2 = rowBreaks(pageData[S.pdIdx], lastFitPlc);
                            var lb = fitLevel(pageData[T2.pdIdx], tB);
                            if (lb < 0) { continue; }
                            var brB2 = rowBreaks(pageData[T2.pdIdx], lastFitPlc);
                            if (sPass === 0 && (la > 0 || lb > 0)) { continue; }
                            if (sPass < 2 && (brA2 > 0 || brB2 > 0)) {
                                var b0A = (fitLevel(pageData[S.pdIdx], assigns[S.pdIdx]) >= 0) ? rowBreaks(pageData[S.pdIdx], lastFitPlc) : 0;
                                var b0B = (fitLevel(pageData[T2.pdIdx], assigns[T2.pdIdx]) >= 0) ? rowBreaks(pageData[T2.pdIdx], lastFitPlc) : 0;
                                if (brA2 > b0A || brB2 > b0B) { rejBrk = true; continue; }
                            }
                            assigns[S.pdIdx][S.slotKey] = contT;
                            assigns[T2.pdIdx][T2.slotKey] = contS;
                            exchLog.push("Test " + (S.sec + 1) + ": A" + contS.num + " (s." + pageData[S.pdIdx].name +
                                         ") \u2194 A" + contT.num + " (s." + pageData[T2.pdIdx].name + ")");
                            done = true; break;
                        }
                        if (sPass === 1 && !rejBrk) { break; }
                    }
                }
            }
            if (exchLog.length > 0) {
                info("Sayfalar arası takas: " + exchLog.length + " kez iki farklı sayfadaki soru yer değiştirdi (ayrıntı CSV'de).");
                log("Ayrıntı: sayfalar arası takas — " + exchLog.join("  |  "));
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
        // v4.24: asgOpt verilirse sayfanın o atamasıyla ölçülür (alternatif diziliş denemesi).
        //        Sayfadaki tüm sorular AYNI branşta (bölüm + ders bölgesi) olmalı; ortak metin bölgesi olamaz.
        function pageBundleInfo(pdi, asgOpt) {
            var asg = asgOpt || assigns[pdi];
            var qs = pageSlots(pdi);
            if (qs.length === 0) { return null; }
            var sec = qs[0].sec, zn = qs[0].zone, top = qs[0].y1, bot = qs[0].y2;
            if (zn !== 0 && isLinkZone(sec, zn)) { return null; }
            for (var q = 0; q < qs.length; q++) {
                if (qs[q].sec !== sec || qs[q].zone !== zn || qs[q].grup !== 0 || qs[q].pool !== 0) { return null; }
                if (asg[qs[q].slotKey].noXPage) { return null; }
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
            var lvl = fitLevel(pageData[pdi], asg);
            if (lvl < 0) { return null; }
            var plcB = layoutAt(pageData[pdi], asg, lvl);
            var aBot = top;
            for (var q2 = 0; q2 < plcB.length; q2++) {
                var b3 = plcB[q2].ny1 + plcB[q2].cont.h;
                if (b3 > aBot) { aBot = b3; }
            }
            return { sec: sec, zone: zn, top: top, bot: bot, aBot: aBot, aH: aBot - top,
                     qs: qs, tail: tail, pdi: pdi, plc: plcB };
        }
        function tailFits(info, newBot) {
            var pdT = pageData[info.pdi];
            for (var t4 = 0; t4 < info.tail.length; t4++) {
                var tl4 = info.tail[t4];
                var nt5 = newBot + (tl4.y1 - info.bot);
                if (nt5 < tl4.y1) { nt5 = tl4.y1; }   // v4.24: kuyruk yukarı çekilmez
                if (nt5 + (tl4.y2 - tl4.y1) > pdT.HB + 0.5) { return false; }
                if (nt5 === tl4.y1) { continue; }
                // v4.25: aşağı inen kuyruk ("TEST BİTTİ") sayfadaki başka sabit öğeye ya da görsele binmemeli
                var r4 = [nt5, tl4.x1, nt5 + (tl4.y2 - tl4.y1), tl4.x2];
                for (var o4 = 0; o4 < pdT.items.length; o4++) {
                    var it4 = pdT.items[o4];
                    if (it4 === tl4 || it4.kind === "soru") { continue; }
                    var inTail = false;
                    for (var u4 = 0; u4 < info.tail.length; u4++) { if (info.tail[u4] === it4) { inTail = true; } }
                    if (!inTail && middleSchoolRectsOverlap(r4, [it4.y1, it4.x1, it4.y2, it4.x2])) { return false; }
                }
                var obs4 = pdT.obstacles || [];
                for (o4 = 0; o4 < obs4.length; o4++) { if (middleSchoolRectsOverlap(r4, obs4[o4].b)) { return false; } }
            }
            return true;
        }
        // v4.24: iki sayfanın soru sayısı farklıysa bölüm baştan numaralanırken ARADAKİ
        // sayfaların numaraları kayar; oradaki "8 ve 9. soruları ... göre" yönergesi ya da
        // ders aralığı yanlış soruları gösterir. Bu yüzden ya sayılar eşit olmalı ya da
        // aradaki sayfalarda bölümün hiçbir sorusu bölgede/grupta olmamalı ve yönerge bulunmamalı.
        function bundleRenumberSafe(i1, i2) {
            if (i1.qs.length === i2.qs.length) { return true; }
            var lo = (i1.pdi < i2.pdi) ? i1.pdi : i2.pdi, hi = (i1.pdi < i2.pdi) ? i2.pdi : i1.pdi;
            for (var pq = lo; pq <= hi; pq++) {
                if (pageData[pq].linkRanges && pageData[pq].linkRanges.length > 0) { return false; }
                var safe = true;
                pageQuestionWalk(pageData[pq], function (r) {
                    if (r.kind === "soru" && r.sec === i1.sec && (r.zone !== i1.zone || r.grup !== 0)) { safe = false; }
                });
                if (!safe) { return false; }
            }
            return true;
        }
        // v4.24: iki sayfa takas edilince (bölüm baştan sıralı numaralanır) numarası AYNI kalan soru
        // sayısı: S'nin içeriği T'de, T'ninki S'de; aradaki sayfalar ayrıca Faz 2c/2d'de ele alınır.
        function bundleKeeps(iS, iT) {
            var secK = iS.sec, keeps = 0;
            function cntOn(pK) {
                var srcK = (pK === iS.pdi) ? iT.pdi : ((pK === iT.pdi) ? iS.pdi : ((pageData[pK].bundleWith >= 0) ? pageData[pK].bundleWith : pK));
                var cK = 0;
                pageQuestionWalk(pageData[srcK], function (r) { if (r.kind === "soru" && r.sec === secK) { cK++; } });
                return cK;
            }
            function startOf(pT) { var st0 = 0; for (var pK = 0; pK < pT; pK++) { st0 += cntOn(pK); } return st0; }
            var pairs = [[iS, iT.pdi], [iT, iS.pdi]];
            for (var pp = 0; pp < 2; pp++) {
                var infK = pairs[pp][0], st1 = startOf(pairs[pp][1]);
                for (var qK = 0; qK < infK.plc.length; qK++) { if (infK.plc[qK].cont.num === st1 + qK + 1) { keeps++; } }
            }
            return keeps;
        }
        // v4.24: inf bloğu (kendi iç düzeniyle) onto sayfasının soru bandına sığar mı
        function bundleFitsOnto(inf, onto) {
            if (onto.top + inf.aH > pageData[onto.pdi].QB + 0.5) { return false; }
            if (!tailFits(onto, onto.top + inf.aH)) { return false; }
            if (isMiddleSchool) {
                // v4.15: blok nakli hedef sayfada 2D zarf denetiminden geçmeli
                var psB = [];
                for (var pqF = 0; pqF < inf.plc.length; pqF++) {
                    psB.push({ slot: { x1: inf.plc[pqF].slot.x1 }, cont: inf.plc[pqF].cont,
                               ny1: inf.plc[pqF].ny1 + (onto.top - inf.top) });
                }
                if (!middleSchoolLayoutSafe(pageData[onto.pdi], psB)) { return false; }
            }
            return true;
        }
        // v4.24: blok mevcut sırasıyla sığmıyorsa (ör. uzun soru karşı sayfanın "TESTİ BİTTİ"
        // yazısına denk geliyorsa) aynı sorular kaynak sayfada başka sırayla dizilerek denenir.
        function bundleAlt(inf, onto) {
            var slA = pageSlots(inf.pdi), baseA = assigns[inf.pdi], grsA = {}, gksA = [], tries = 0, a5;
            for (a5 = 0; a5 < slA.length; a5++) {
                var gkA = slA[a5].shape + "|" + slA[a5].grup + "|" + slA[a5].pool;
                if (!grsA[gkA]) { grsA[gkA] = []; gksA.push(gkA); }
                grsA[gkA].push(slA[a5]);
            }
            for (var gA = 0; gA < gksA.length; gA++) {
                var grpA = grsA[gksA[gA]], mA = grpA.length;
                if (mA < 2 || mA > 5) { continue; }
                var contA = [];
                for (a5 = 0; a5 < mA; a5++) { contA.push(baseA[grpA[a5].slotKey]); }
                var permsA = allPerms(mA);
                for (var pA = 0; pA < permsA.length && tries < 150; pA++) {
                    var prA = permsA[pA], idA = true;
                    for (a5 = 0; a5 < mA; a5++) { if (prA[a5] !== a5) { idA = false; break; } }
                    if (idA) { continue; }
                    tries++;
                    var trA = copyAssign(baseA);
                    for (a5 = 0; a5 < mA; a5++) { trA[grpA[a5].slotKey] = contA[prA[a5]]; }
                    var infA2 = pageBundleInfo(inf.pdi, trA);
                    if (infA2 !== null && bundleFitsOnto(infA2, onto)) { return { inf: infA2, assign: trA }; }
                }
            }
            return null;
        }
        // v4.18: sayfadaki soru çerçevelerinin en soldaki kenarı (sütun düzeninin x başlangıcı)
        function bundleLeftEdge(info) {
            var mx = null;
            for (var q5 = 0; q5 < info.qs.length; q5++) {
                if (mx === null || info.qs[q5].fx1 < mx) { mx = info.qs[q5].fx1; }
            }
            return mx;
        }
        progress("Tam sayfa takası…", true);
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
                    // yalnız aynı branş: aynı test ve aynı ders bölgesi
                    if (infT === null || infT.sec !== infS.sec || infT.zone !== infS.zone) { continue; }
                    if (!sameBranchPages(Sb2.pdIdx, j)) { continue; }   // v4.25: üst bant branşı
                    if (!bundleRenumberSafe(infS, infT)) { continue; }
                    if (isMiddleSchool) {
                        // v4.18: blok, KAYNAK sayfanın x konumlarıyla yerleştirilir. İç/dış kenar
                        // boşluğu farklı karşılıklı sayfalarda sol ve sağ sayfanın sütunları farklı
                        // x'te durur; blok yatayda kayar ve bekçi bunu bindirme saymaz.
                        // Sütun başlangıcı iki sayfada farklıysa blok takası yapılmaz.
                        var dxB = bundleLeftEdge(infS) - bundleLeftEdge(infT);
                        if (dxB > 3 || dxB < -3) { continue; }
                    }
                    // karşılıklı sığma: gerçek yerleşim yüksekliğiyle; olmazsa başka dizilişle
                    var useS = infS, useT = infT, altSA = null, altTA = null;
                    if (!bundleFitsOnto(useS, useT)) {
                        var alS = bundleAlt(useS, useT);
                        if (alS === null) { continue; }
                        useS = alS.inf; altSA = alS.assign;
                    }
                    if (!bundleFitsOnto(useT, useS)) {
                        var alT = bundleAlt(useT, useS);
                        if (alT === null) { continue; }
                        useT = alT.inf; altTA = alT.assign;
                    }
                    if (bundleKeeps(useS, useT) > 0) { continue; }
                    var dhB = useS.aH - useT.aH; if (dhB < 0) { dhB = -dhB; }
                    var dpB = j - Sb2.pdIdx; if (dpB < 0) { dpB = -dpB; }
                    if (bestB === null || dhB < bestB.dh || (dhB === bestB.dh && dpB < bestB.dp)) {
                        bestB = { dh: dhB, dp: dpB, inf: useT, infS: useS, aS: altSA, aT: altTA };
                    }
                }
                if (bestB !== null) {
                    var infT2 = bestB.inf;
                    pageData[Sb2.pdIdx].bundleWith = infT2.pdi;
                    pageData[infT2.pdi].bundleWith = Sb2.pdIdx;
                    pageData[Sb2.pdIdx].bundleInfo = bestB.infS;
                    pageData[infT2.pdi].bundleInfo = infT2;
                    if (bestB.aS !== null) { assigns[Sb2.pdIdx] = bestB.aS; }
                    if (bestB.aT !== null) { assigns[infT2.pdi] = bestB.aT; }
                    bundleSecs[infS.sec] = true;
                    bundleLog.push("Test " + (infS.sec + 1) + ": s." + pageData[Sb2.pdIdx].name +
                                   " \u2194 s." + pageData[infT2.pdi].name);
                }
            }
            if (bundleLog.length > 0) { info("Tam sayfa takası (iki sayfanın soruları blok hâlinde yer değiştirdi): " + bundleLog.join("  |  ")); }
        }

        // -----------------------------------------------------
        // 10b) FAZ 2c — YERİNDE KALANA SON DENEME  (v4.23)
        //      Faz 1 satır hizasını koruyan sırayı seçer; bu yüzden yerinde kalan ve
        //      Faz 2'de başka sayfayla da değişemeyen soru için sayfa içi sıra burada,
        //      yerinde kalan sayısını azaltmak koşuluyla yeniden denenir.
        // -----------------------------------------------------
        // v4.24: blok takaslı bölümde numaralar baştan sıralı yazılır; takas, soru sayısı farklı
        // sayfalar arasındaysa aradaki sayfaların numaraları kayar. "Yerinde kalma" B'deki gerçek
        // numarayla ölçülür (A numarasıyla değil).
        function finalNumsOf(piF) {
            var slF = [], outF = [], k7;
            pageQuestionWalk(pageData[piF], function (r) { if (r.kind === "soru") { slF.push(r); } });
            var prevCnt = {}, seenSec = {};
            for (k7 = 0; k7 < slF.length; k7++) {
                var sF = slF[k7].sec;
                if (!bundleSecs[sF]) { outF.push(slF[k7].num); continue; }
                if (!seenSec[sF]) {
                    seenSec[sF] = true;
                    var cF = 0;
                    for (var pF = 0; pF < piF; pF++) {
                        var srcF = (pageData[pF].bundleWith >= 0) ? pageData[pF].bundleWith : pF;
                        pageQuestionWalk(pageData[srcF], function (r) { if (r.kind === "soru" && r.sec === sF) { cF++; } });
                    }
                    prevCnt[sF] = cF;
                }
                prevCnt[sF]++;
                outF.push(prevCnt[sF]);
            }
            return outF;
        }
        var repairN = 0, repairPg = [];
        progress("Yerinde kalan sorular yeniden deneniyor…", true);
        if (mode !== "col") {
            for (pi = 0; pi < pageData.length; pi++) {
                var pdR2 = pageData[pi];
                if (pdR2.bundleWith >= 0) { continue; }
                var slR = [];
                pageQuestionWalk(pdR2, function (r) { if (r.kind === "soru") { slR.push(r); } });
                var asR = assigns[pi], anyStuck = false, fnR = finalNumsOf(pi), fnOf = {};
                for (k = 0; k < slR.length; k++) {
                    fnOf[slR[k].slotKey] = fnR[k];
                    var cR0 = asR[slR[k].slotKey];
                    if (cR0.num === fnR[k]) { anyStuck = true; }
                }
                if (!anyStuck) { continue; }
                var grR = {}, gkR = [];
                for (k = 0; k < slR.length; k++) {
                    var gkr = slR[k].sec + "|" + slR[k].zone + "|" + slR[k].shape + "|" + slR[k].grup + "|" + slR[k].pool;
                    if (!grR[gkr]) { grR[gkr] = []; gkR.push(gkr); }
                    grR[gkr].push(slR[k]);
                }
                for (var gR = 0; gR < gkR.length; gR++) {
                    var grpR = grR[gkR[gR]], mR = grpR.length;
                    if (mR < 2 || mR > 7) { continue; }
                    if (grpR[0].grup > 0 && !chkLinked.value) { continue; }
                    var contR = [], curSt = 0;
                    for (k = 0; k < mR; k++) {
                        contR.push(asR[grpR[k].slotKey]);
                        if (contR[k].num === fnOf[grpR[k].slotKey]) { curSt++; }
                    }
                    if (curSt === 0) { continue; }
                    var permsR2 = allPerms(mR), bestR = null, bestSt = curSt, bestLR = 99, bestKR = 100000, bestPR = 100000;
                    for (var ppR = 0; ppR < permsR2.length; ppR++) {
                        var prR = permsR2[ppR], st = 0;
                        for (k = 0; k < mR; k++) { if (contR[prR[k]].num === fnOf[grpR[k].slotKey]) { st++; } }
                        if (st >= curSt || st > bestSt) { continue; }
                        var trR = copyAssign(asR);
                        for (k = 0; k < mR; k++) { trR[grpR[k].slotKey] = contR[prR[k]]; }
                        var lvR = fitLevel(pdR2, trR);
                        if (lvR < 0) { continue; }
                        var plR = lastFitPlc, brR = rowBreaks(pdR2, plR), peR = 0;
                        for (k = 0; k < plR.length; k++) {
                            var dyR = plR[k].ny1 - plR[k].slot.y1;
                            if (dyR > 0.5 || dyR < -0.5) { peR++; }
                        }
                        if (st < bestSt || (st === bestSt && (brR < bestKR || (brR === bestKR && (lvR < bestLR || (lvR === bestLR && peR < bestPR)))))) {
                            bestR = prR; bestSt = st; bestLR = lvR; bestKR = brR; bestPR = peR;
                        }
                    }
                    if (bestR !== null) {
                        for (k = 0; k < mR; k++) { asR[grpR[k].slotKey] = contR[bestR[k]]; }
                        repairN += curSt - bestSt;
                        if (bestKR > 0) { repairPg.push(pdR2.name); }
                    }
                }
            }
            if (repairN > 0) {
                log("Ayrıntı: yerinde kalan " + repairN + " soru sayfa içinde yeniden sıralanarak yer değiştirdi" +
                    (repairPg.length ? " (s." + repairPg.join(", s.") + ": sol/sağ sütunun satır başları A'daki gibi aynı hizada değil)." : "."));
            }
        }

        // -----------------------------------------------------
        // 10c) FAZ 2d — SAYFA İÇİ BLOK SIRASI  (v4.24)
        //      Tam genişlik soru, sayfasında aynı türden eşi olmadığı için yerinde kalıyorsa
        //      sayfadaki iki sütunlu soru bloğuyla yer değiştirir: sütunlar yukarı, tam genişlik
        //      soru alta (ya da tersi). Okuma sırası değiştiği için sayfadaki tüm numaralar
        //      kayar; yalnız sayfanın tüm soruları aynı test ve aynı bölgedeyse yapılır
        //      (ortak metin grubu da olabilir: numaralar grubun aralığında kalır).
        // -----------------------------------------------------
        var reorderLog = [], colSwapLog = [];
        // pdO sayfasında, asO atamasıyla blok sırası değiştirilmiş yerleşim (olmazsa null)
        function reorderLayout(pdO, asO, fwO, regO, fwFirst, colFix) {
            if (fitLevel(pdO, asO) < 0) { return null; }
            var plO = lastFitPlc, fwE = null, regE = [], rTopN = null, rBotN = null, k5;
            for (k5 = 0; k5 < plO.length; k5++) {
                if (plO[k5].slot === fwO.it) { fwE = plO[k5]; continue; }
                regE.push(plO[k5]);
                if (rTopN === null || plO[k5].ny1 < rTopN) { rTopN = plO[k5].ny1; }
                if (rBotN === null || plO[k5].ny1 + plO[k5].cont.h > rBotN) { rBotN = plO[k5].ny1 + plO[k5].cont.h; }
            }
            if (fwE === null || regE.length === 0) { return null; }
            var gapA = fwFirst ? (regO.top - fwO.bot) : (fwO.top - regO.bot);
            if (gapA < 8) { gapA = 8; }
            var gMin = (gapA < ANCHOR_MIN_GAP) ? gapA : ANCHOR_MIN_GAP;
            var fwY, dR, lim = pdO.QB - 0.5;
            if (fwFirst) {
                dR = fwE.ny1 - rTopN;                     // sütunlar bandın üstüne
                // tam genişlik sorunun altına inebileceği sınır: sütunlarda kalan sabit öğeler
                for (k5 = 0; k5 < colFix.length; k5++) {
                    if (colFix[k5].y1 - 12 < lim && colFix[k5].y1 > rBotN + dR) { lim = colFix[k5].y1 - 12; }
                }
                fwY = rBotN + dR + gapA;                  // tam genişlik soru altlarına
                if (fwY + fwE.cont.h > lim) {
                    fwY = lim - fwE.cont.h;
                    if (fwY < rBotN + dR + gMin) { return null; }
                }
            } else {
                fwY = rTopN;                              // tam genişlik soru üste
                dR = (fwY + fwE.cont.h + gapA) - rTopN;
                if (rBotN + dR > lim) {
                    dR = lim - rBotN;
                    if (rTopN + dR < fwY + fwE.cont.h + gMin) { return null; }
                }
            }
            var newR = [];
            for (k5 = 0; k5 < regE.length; k5++) { newR.push({ slot: regE[k5].slot, cont: regE[k5].cont, ny1: regE[k5].ny1 + dR }); }
            var fwN = { slot: fwE.slot, cont: fwE.cont, ny1: fwY };
            var allN = newR.concat([fwN]);
            // güvenlik: kendi aralarında, sabit öğelerle ve grafik engellerle çakışma yok
            var rcN = [];
            for (k5 = 0; k5 < allN.length; k5++) {
                rcN.push([allN[k5].ny1, allN[k5].slot.x1, allN[k5].ny1 + (allN[k5].cont.y2 - allN[k5].cont.y1),
                          allN[k5].slot.x1 + (allN[k5].cont.x2 - allN[k5].cont.x1)]);
                if (rcN[k5][2] > pdO.QB + 0.5) { return null; }
            }
            for (k5 = 0; k5 < rcN.length; k5++) {
                for (var j5 = k5 + 1; j5 < rcN.length; j5++) { if (middleSchoolRectsOverlap(rcN[k5], rcN[j5])) { return null; } }
            }
            for (k5 = 0; k5 < pdO.items.length; k5++) {
                var fxO = pdO.items[k5];
                if (fxO.kind === "soru") { continue; }
                var fr = [fxO.y1, fxO.x1, fxO.y2, fxO.x2], touchA = false;
                for (var q5 = 0; q5 < pdO.items.length; q5++) {
                    var sq = pdO.items[q5];
                    if (sq.kind === "soru" && middleSchoolDeepOverlap(fr, [sq.y1, sq.x1, sq.y2, sq.x2])) { touchA = true; break; }
                }
                if (touchA) { continue; }
                for (j5 = 0; j5 < rcN.length; j5++) { if (middleSchoolRectsOverlap(rcN[j5], fr)) { return null; } }
            }
            if (!obstacleSafe(pdO, allN)) { return null; }
            // yeni okuma sırası: (sütun 0, sütun 1) + tam genişlik ya da tersi
            var ordR = [];
            for (var c5 = 0; c5 < 2; c5++) {
                var colN = [];
                for (k5 = 0; k5 < newR.length; k5++) { if (newR[k5].slot.col === c5) { colN.push(newR[k5]); } }
                colN.sort(function (a, b) { return (a.ny1 - b.ny1) || (a.slot.x1 - b.slot.x1) || (a.cont.num - b.cont.num); });
                for (k5 = 0; k5 < colN.length; k5++) { ordR.push(colN[k5]); }
            }
            return { ord: fwFirst ? ordR.concat([fwN]) : [fwN].concat(ordR),
                     regTop: rTopN + dR, regBot: rBotN + dR, regTopNow: rTopN };
        }
        // v4.25 SÜTUN TAKASI: sayfadaki iki sütunlu bloğun sol ve sağ sütun soruları dikey
        // konumlarını koruyarak yer değiştirir (satır hizası korunur, ayırıcı yerinde kalır).
        // Sütunlarda soru dışı öğe yalnız sütunun en altında olabilir ve takastan sonra çakışmamalı.
        function columnSwapLayout(pdC, asC) {
            var regC = null, nReg = 0, b8, c8, k8;
            for (b8 = 0; b8 < pdC.blocks.length; b8++) {
                if (pdC.blocks[b8].type !== "REG") { continue; }
                var hasQ8 = false;
                for (c8 = 0; c8 < 2; c8++) { for (k8 = 0; k8 < pdC.blocks[b8].cols[c8].length; k8++) { if (pdC.blocks[b8].cols[c8][k8].kind === "soru") { hasQ8 = true; } } }
                if (hasQ8) { regC = pdC.blocks[b8]; nReg++; }
            }
            if (nReg !== 1) { return null; }
            var bx = [[null, null], [null, null]], fix8 = [];
            for (c8 = 0; c8 < 2; c8++) {
                var qBot8 = null;
                for (k8 = 0; k8 < regC.cols[c8].length; k8++) {
                    var it8 = regC.cols[c8][k8];
                    if (it8.kind !== "soru") { continue; }
                    if (it8.grup !== 0 || it8.pool !== 0) { return null; }
                    if (bx[c8][0] === null || it8.x1 < bx[c8][0]) { bx[c8][0] = it8.x1; }
                    if (bx[c8][1] === null || it8.x2 > bx[c8][1]) { bx[c8][1] = it8.x2; }
                    if (qBot8 === null || it8.y2 > qBot8) { qBot8 = it8.y2; }
                }
                if (bx[c8][0] === null) { return null; }
                for (k8 = 0; k8 < regC.cols[c8].length; k8++) {
                    var fx8 = regC.cols[c8][k8];
                    if (fx8.kind === "soru") { continue; }
                    if (fx8.y1 < qBot8 - 2) { return null; }   // sütun içinde soruların arasında/üstünde sabit öğe
                }
            }
            var w0 = bx[0][1] - bx[0][0], w1 = bx[1][1] - bx[1][0], dx8 = bx[1][0] - bx[0][0];
            if (w0 - w1 > 3 || w1 - w0 > 3) { return null; }
            if (fitLevel(pdC, asC) < 0) { return null; }
            var pl8 = lastFitPlc, ent = [], newCols = [[], []], fwOrd = [];
            for (k8 = 0; k8 < pl8.length; k8++) {
                var e8 = pl8[k8];
                if (e8.slot.shape === "COL" && e8.ny1 >= regC.top - 400 && (e8.slot.col === 0 || e8.slot.col === 1) && inBlock(regC, e8.slot)) {
                    var toC = 1 - e8.slot.col;
                    var ne = { slot: { x1: e8.slot.x1 + (toC === 1 ? dx8 : -dx8), col: toC }, cont: e8.cont, ny1: e8.ny1 };
                    newCols[toC].push(ne); ent.push(ne);
                } else {
                    ent.push(e8);
                }
            }
            // güvenlik: kendi aralarında, sabit öğelerle, engellerle çakışma yok
            var rc8 = [];
            for (k8 = 0; k8 < ent.length; k8++) {
                rc8.push([ent[k8].ny1, ent[k8].slot.x1, ent[k8].ny1 + (ent[k8].cont.y2 - ent[k8].cont.y1),
                          ent[k8].slot.x1 + (ent[k8].cont.x2 - ent[k8].cont.x1)]);
            }
            for (k8 = 0; k8 < rc8.length; k8++) {
                for (var j8 = k8 + 1; j8 < rc8.length; j8++) { if (middleSchoolRectsOverlap(rc8[k8], rc8[j8])) { return null; } }
            }
            for (k8 = 0; k8 < pdC.items.length; k8++) {
                var fz = pdC.items[k8];
                if (fz.kind === "soru") { continue; }
                var frz = [fz.y1, fz.x1, fz.y2, fz.x2], tz = false;
                for (var q8 = 0; q8 < pdC.items.length; q8++) {
                    var sz = pdC.items[q8];
                    if (sz.kind === "soru" && middleSchoolDeepOverlap(frz, [sz.y1, sz.x1, sz.y2, sz.x2])) { tz = true; break; }
                }
                if (tz) { continue; }
                for (j8 = 0; j8 < rc8.length; j8++) { if (middleSchoolRectsOverlap(rc8[j8], frz)) { return null; } }
            }
            if (!obstacleSafe(pdC, ent)) { return null; }
            // okuma sırası: bloklar sırayla; sütun bloğunda yeni sol sütun, sonra yeni sağ sütun
            var ord8 = [];
            for (b8 = 0; b8 < pdC.blocks.length; b8++) {
                var bk = pdC.blocks[b8];
                if (bk === regC) {
                    for (c8 = 0; c8 < 2; c8++) {
                        newCols[c8].sort(function (a, b) { return (a.ny1 - b.ny1) || (a.slot.x1 - b.slot.x1) || (a.cont.num - b.cont.num); });
                        for (k8 = 0; k8 < newCols[c8].length; k8++) { ord8.push(newCols[c8][k8]); }
                    }
                } else if (bk.type === "FWQ") {
                    for (k8 = 0; k8 < pl8.length; k8++) { if (pl8[k8].slot === bk.it) { ord8.push(pl8[k8]); } }
                } else if (bk.type === "REG") {
                    for (c8 = 0; c8 < 2; c8++) { for (k8 = 0; k8 < bk.cols[c8].length; k8++) {
                        for (j8 = 0; j8 < pl8.length; j8++) { if (pl8[j8].slot === bk.cols[c8][k8]) { ord8.push(pl8[j8]); } }
                    } }
                }
            }
            if (ord8.length !== pl8.length) { return null; }
            return { ord: ord8 };
        }
        function inBlock(blk9, slot9) {
            for (var c9 = 0; c9 < 2; c9++) { for (var k9 = 0; k9 < blk9.cols[c9].length; k9++) { if (blk9.cols[c9][k9] === slot9) { return true; } } }
            return false;
        }
        progress("Sayfa içi blok sırası deneniyor…", true);
        if (mode !== "col") {
            for (pi = 0; pi < pageData.length; pi++) {
                var pdO = pageData[pi];
                if (pdO.bundleWith >= 0) { continue; }
                var slO = [];
                pageQuestionWalk(pdO, function (r) { if (r.kind === "soru") { slO.push(r); } });
                if (slO.length < 2) { continue; }
                var asO = assigns[pi], stO = 0, okO = true, fnO = finalNumsOf(pi);
                for (k = 0; k < slO.length; k++) {
                    if (asO[slO[k].slotKey].num === fnO[k]) { stO++; }
                    if (slO[k].sec !== slO[0].sec || slO[k].zone !== slO[0].zone || slO[k].grup !== 0 || slO[k].pool !== 0) { okO = false; }
                }
                if (stO === 0 || !okO) { continue; }
                var numsC = fnO.slice(0);
                numsC.sort(function (a, b) { return a - b; });
                // v4.25: önce sütun takası (dikey düzen aynen kalır); sütun soruları her dizilişte denenir
                var colBest = null, colStBest = stO, colAs = null;
                (function () {
                    var regSlC = [];
                    for (var bC = 0; bC < pdO.blocks.length; bC++) {
                        if (pdO.blocks[bC].type !== "REG") { continue; }
                        for (var cC = 0; cC < 2; cC++) { for (var kC = 0; kC < pdO.blocks[bC].cols[cC].length; kC++) {
                            if (pdO.blocks[bC].cols[cC][kC].kind === "soru") { regSlC.push(pdO.blocks[bC].cols[cC][kC]); }
                        } }
                    }
                    if (regSlC.length < 2 || regSlC.length > 6) { return; }
                    var contC = [];
                    for (var kC2 = 0; kC2 < regSlC.length; kC2++) { contC.push(asO[regSlC[kC2].slotKey]); }
                    var permsC = allPerms(regSlC.length);
                    for (var pC = 0; pC < permsC.length; pC++) {
                        var trC = copyAssign(asO);
                        for (kC2 = 0; kC2 < regSlC.length; kC2++) { trC[regSlC[kC2].slotKey] = contC[permsC[pC][kC2]]; }
                        var lyC = columnSwapLayout(pdO, trC);
                        if (lyC === null) { continue; }
                        var stC = 0;
                        for (kC2 = 0; kC2 < lyC.ord.length; kC2++) { if (lyC.ord[kC2].cont.num === numsC[kC2]) { stC++; } }
                        if (stC < colStBest) { colStBest = stC; colBest = lyC; colAs = trC; if (stC === 0) { break; } }
                    }
                })();
                if (colBest !== null && colStBest === 0) {
                    assigns[pi] = colAs;
                    var planC = { list: [], isBundle: true, tailMoves: [], divIn: [], nums: numsC.slice(0) };
                    for (k = 0; k < colBest.ord.length; k++) {
                        planC.list.push({ cont: colBest.ord[k].cont, ny1: colBest.ord[k].ny1, nx1: colBest.ord[k].slot.x1, ord: k });
                    }
                    pdO.reorder = planC;
                    colSwapLog.push("s." + pdO.name);
                    continue;
                }
                // soru blokları tam olarak ardışık [tam genişlik soru, sütun bloğu] ya da tersi
                var qbO = [];
                for (var bO = 0; bO < pdO.blocks.length; bO++) {
                    var blO = pdO.blocks[bO], hasQO = (blO.type === "FWQ");
                    if (blO.type === "REG") {
                        for (ci = 0; ci < 2; ci++) { for (k = 0; k < blO.cols[ci].length; k++) { if (blO.cols[ci][k].kind === "soru") { hasQO = true; } } }
                    }
                    if (hasQO) { qbO.push(bO); }
                }
                if (qbO.length !== 2 || qbO[1] !== qbO[0] + 1) { continue; }
                var b1O = pdO.blocks[qbO[0]], b2O = pdO.blocks[qbO[1]];
                var fwFirst = (b1O.type === "FWQ" && b2O.type === "REG");
                if (!fwFirst && !(b1O.type === "REG" && b2O.type === "FWQ")) { continue; }
                var regO = fwFirst ? b2O : b1O, fwO = fwFirst ? b1O : b2O;
                // sütundaki sabit öğe yalnız o sütunun sorularının ALTINDA olabilir (ör. "TESTİ BİTTİ")
                var rqTop = null, colFix = [], regSl = [];
                for (ci = 0; ci < 2; ci++) {
                    var cqBot = null;
                    for (k = 0; k < regO.cols[ci].length; k++) {
                        var itO = regO.cols[ci][k];
                        if (itO.kind !== "soru") { continue; }
                        regSl.push(itO);
                        if (rqTop === null || itO.y1 < rqTop) { rqTop = itO.y1; }
                        if (cqBot === null || itO.y2 > cqBot) { cqBot = itO.y2; }
                    }
                    for (k = 0; k < regO.cols[ci].length; k++) {
                        var fxC = regO.cols[ci][k];
                        if (fxC.kind === "soru") { continue; }
                        if (cqBot !== null && fxC.y1 < cqBot - 2) { okO = false; }
                        colFix.push(fxC);
                    }
                }
                if (!okO || regSl.length < 1 || regSl.length > 6) { continue; }
                // sütun sorularının her dizilişi denenir; yerinde kalan en aza iner
                var numsO = fnO.slice(0);
                numsO.sort(function (a, b) { return a - b; });
                var contO = [];
                for (k = 0; k < regSl.length; k++) { contO.push(asO[regSl[k].slotKey]); }
                var permsO = allPerms(regSl.length), bestO = null, bestStO = stO, bestAs = null;
                for (var ppO = 0; ppO < permsO.length; ppO++) {
                    var trO = copyAssign(asO);
                    for (k = 0; k < regSl.length; k++) { trO[regSl[k].slotKey] = contO[permsO[ppO][k]]; }
                    var lyO = reorderLayout(pdO, trO, fwO, regO, fwFirst, colFix);
                    if (lyO === null) { continue; }
                    var stN = 0;
                    for (k = 0; k < lyO.ord.length; k++) { if (lyO.ord[k].cont.num === numsO[k]) { stN++; } }
                    if (stN < bestStO) { bestStO = stN; bestO = lyO; bestAs = trO; if (stN === 0) { break; } }
                }
                if (bestO === null) { continue; }
                // plan: Faz 3'te blok takası gibi uygulanır (sıralı numara, ayırıcı taşınır)
                assigns[pi] = bestAs;
                var planO = { list: [], isBundle: true, tailMoves: [], divIn: [], nums: numsO.slice(0) };
                for (k = 0; k < bestO.ord.length; k++) {
                    planO.list.push({ cont: bestO.ord[k].cont, ny1: bestO.ord[k].ny1, nx1: bestO.ord[k].slot.x1, ord: k });
                }
                var dvO = pdO.dividers || [];
                for (k = 0; k < dvO.length; k++) {
                    if (Math.abs(dvO[k].b[0] - rqTop) > 8 && Math.abs(dvO[k].b[0] - regO.top) > 8) { continue; }
                    var dTop = dvO[k].b[0] + (bestO.regTop - rqTop);
                    var dBot = fwFirst ? bestO.regBot : ((dvO[k].b[2] > bestO.regBot) ? dvO[k].b[2] : bestO.regBot);
                    planO.divIn.push({ d: dvO[k], from: pi, top: dTop, bot: dBot });
                }
                pdO.reorder = planO;
                reorderLog.push("s." + pdO.name);
            }
            if (reorderLog.length > 0) {
                info("Sayfa içi blok sırası: " + reorderLog.join(", ") + " — tam genişlik soru ile iki sütunlu sorular yer değiştirdi (aynı sayfa, aynı test).");
            }
            if (colSwapLog.length > 0) {
                info("Sütun takası: " + colSwapLog.join(", ") + " — sol ve sağ sütunun soruları yer değiştirdi (aynı sayfa, aynı test).");
            }
        }

        // -----------------------------------------------------
        // 10c) FAZ 2e — ORTAK METİN BANDI TAKASI (v4.26)
        //      Sayfada bir ortak metin grubu (yönerge + metin + soruları) ile serbest soru(lar) üst üste
        //      iki bant oluşturuyor ve sayfada hâlâ numarası aynı kalan soru varsa iki bant, iç düzenleri
        //      hiç bozulmadan yer değiştirir. Okuma sırası değiştiği için yönergedeki numaralar
        //      ("9 ve 10. soruları" → "8 ve 9. soruları") yeni numaralara göre güncellenir.
        //      Yalnız aynı sayfa, aynı test ve aynı ders bölgesi; grup eksiksiz bu sayfada olmalı.
        // -----------------------------------------------------
        var bandLog = [];
        function nonLinkZoneOf(sec, num) {
            var zl = secZones[sec];
            if (!zl) { return 0; }
            var bestZ = 0, bestW = 100000;
            for (var z = 0; z < zl.length; z++) {
                if (zl[z].link) { continue; }
                if (num >= zl[z].lo && num <= zl[z].hi && (zl[z].hi - zl[z].lo) < bestW) { bestZ = z + 1; bestW = zl[z].hi - zl[z].lo; }
            }
            return bestZ;
        }
        function idOf(o) { try { return o.id; } catch (eIo) { return -1; } }
        // sayfa kaydı (çerçeve ya da grup) verilen çerçeveyi içeriyor mu
        function recHasTf(rec, tfId) {
            if (tfId === -1) { return false; }
            if (idOf(rec.tf) === tfId) { return true; }
            try {
                var apR = rec.tf.allPageItems;
                for (var a9 = 0; a9 < apR.length; a9++) { if (idOf(apR[a9]) === tfId) { return true; } }
            } catch (eRh) {}
            return false;
        }
        // hikâye metninde [lo, hi] aralığını yazan yönergenin sayı dizisi konumu {s, e} (yoksa null)
        function directiveSpan(txt, lo, hi) {
            var t = String(txt), off = 0, n = t.length;
            while (off <= n) {
                var e = off;
                while (e < n) { var ch = t.charAt(e); if (ch === "\r" || ch === "\n" || ch === "\u2029") { break; } e++; }
                var ds = linkDirectives(t.substring(off, e));
                for (var d9 = 0; d9 < ds.length; d9++) {
                    if (ds[d9].lo === lo && ds[d9].hi === hi && ds[d9].at >= 0 && ds[d9].end > ds[d9].at) { return { s: off + ds[d9].at, e: off + ds[d9].end }; }
                }
                off = e + 1;
            }
            return null;
        }
        // aralıktaki tüm sayılar [lo, hi] içinde mi (başka bir sayı yanlışlıkla değişmesin)
        function spanNumsOk(seg, lo, hi) {
            var cnt = 0, i9 = 0;
            while (i9 < seg.length) {
                if (!isDigitCh(seg.charAt(i9))) { i9++; continue; }
                var b9 = i9;
                while (i9 < seg.length && isDigitCh(seg.charAt(i9))) { i9++; }
                var v9 = parseInt(seg.substring(b9, i9), 10);
                if (i9 - b9 > 3 || v9 < lo || v9 > hi) { return false; }
                cnt++;
            }
            return cnt > 0;
        }
        function bandSwapPlan(piB, slE, asE, fnE, stE) {
            var pdB = pageData[piB], secB = slE[0].sec, k9, j9;
            // numaralar aynı ders bölgesinde kalmalı (ders sınırı bu sayfadan geçiyorsa yapılmaz)
            var nlz = nonLinkZoneOf(secB, fnE[0]);
            for (k9 = 1; k9 < fnE.length; k9++) { if (nonLinkZoneOf(secB, fnE[k9]) !== nlz) { return null; } }
            // ortak metin grupları: eksiksiz bu sayfada, yönergesi bu sayfada ve güncellenebilir
            var zinfo = {}, zl = [];
            for (k9 = 0; k9 < slE.length; k9++) {
                var zq = slE[k9].zone;
                if (!isLinkZone(secB, zq)) { continue; }
                if (!zinfo[zq]) {
                    var zz = secZones[secB][zq - 1];
                    zinfo[zq] = { z: zq, lo: zz.lo, hi: zz.hi, n: 0, dir: null, dirRec: null, span: null };
                    zl.push(zinfo[zq]);
                }
                zinfo[zq].n++;
            }
            if (zl.length === 0) { return null; }
            for (k9 = 0; k9 < zl.length; k9++) {
                var zi = zl[k9];
                if (zi.n !== zi.hi - zi.lo + 1) { return null; }
                var lrs = pdB.linkRanges || [];
                for (j9 = 0; j9 < lrs.length; j9++) { if (lrs[j9].lo === zi.lo && lrs[j9].hi === zi.hi && lrs[j9].tf) { zi.dir = lrs[j9]; break; } }
                if (zi.dir === null) { return null; }
                var dId = idOf(zi.dir.tf);
                for (j9 = 0; j9 < pdB.items.length; j9++) {
                    if (pdB.items[j9].kind !== "soru" && recHasTf(pdB.items[j9], dId)) { zi.dirRec = pdB.items[j9]; zi.dirY = pdB.items[j9].y1; break; }
                }
                // yönerge + metin tek grupta (dekor grup): sayfanın sabit şekilleri arasında durur
                var obsD = pdB.obstacles || [];
                for (j9 = 0; j9 < obsD.length && zi.dirRec === null; j9++) {
                    if (recHasTf({ tf: obsD[j9].it }, dId)) { zi.dirOb = obsD[j9]; zi.dirRec = obsD[j9]; zi.dirY = obsD[j9].b[0]; }
                }
                if (zi.dirRec === null) { return null; }
                var dTxt = "";
                try { dTxt = String(zi.dir.tf.parentStory.texts[0].contents); } catch (eDt) { return null; }
                zi.span = directiveSpan(dTxt, zi.lo, zi.hi);
                if (zi.span === null || !spanNumsOk(dTxt.substring(zi.span.s, zi.span.e), zi.lo, zi.hi)) { return null; }
            }
            // sayfanın güncel yerleşimi (Faz 1-2c atamalarıyla)
            if (fitLevel(pdB, asE) < 0) { return null; }
            var plB = lastFitPlc;
            if (plB.length !== slE.length) { return null; }
            var els = [], qTop = null, qBot = null;
            for (k9 = 0; k9 < plB.length; k9++) {
                var e9 = { t: "q", y1: plB[k9].ny1, y2: plB[k9].ny1 + plB[k9].cont.h, p: plB[k9] };
                els.push(e9);
                if (qTop === null || e9.y1 < qTop) { qTop = e9.y1; }
                if (qBot === null || e9.y2 > qBot) { qBot = e9.y2; }
            }
            var rTop = qTop;
            for (k9 = 0; k9 < zl.length; k9++) { if (zl[k9].dirY < rTop) { rTop = zl[k9].dirY; } }
            // 0: bölgenin dışında (başlık, "TEST BİTTİ"), 1: içinde, -1: sınırı kesiyor
            var cls = function (y1, y2) {
                if (y2 <= rTop + 0.5 || y1 >= qBot - 0.5) { return 0; }
                if (y1 >= rTop - 0.5 && y2 <= qBot + 0.5) { return 1; }
                return -1;
            };
            for (k9 = 0; k9 < pdB.items.length; k9++) {
                var it9 = pdB.items[k9];
                if (it9.kind === "soru") { continue; }
                var c9 = cls(it9.y1, it9.y2);
                if (c9 < 0 || (c9 === 1 && it9.kind === "intro")) { return null; }
                if (c9 === 1) { els.push({ t: "f", y1: it9.y1, y2: it9.y2, rec: it9 }); }
            }
            var obs9 = pdB.obstacles || [];
            for (k9 = 0; k9 < obs9.length; k9++) {
                var co9 = cls(obs9[k9].b[0], obs9[k9].b[2]);
                if (co9 < 0) { return null; }
                if (co9 === 1) { els.push({ t: "o", y1: obs9[k9].b[0], y2: obs9[k9].b[2], ob: obs9[k9] }); }
            }
            var dvs9 = pdB.dividers || [];
            for (k9 = 0; k9 < dvs9.length; k9++) {
                var db9 = dvs9[k9].b;
                if (db9[2] <= rTop + 0.5 || db9[0] >= qBot - 0.5) { continue; }
                if (db9[0] < rTop - 0.5) { return null; }   // iki bandı birden kesen ayırıcı
                els.push({ t: "d", y1: db9[0], y2: (db9[2] < qBot) ? db9[2] : qBot, dv: dvs9[k9] });
            }
            // dikeyde örtüşmeyen bantlar
            els.sort(function (a, b) { return (a.y1 - b.y1) || (a.y2 - b.y2); });
            var bands = [];
            for (k9 = 0; k9 < els.length; k9++) {
                var lastB = bands.length ? bands[bands.length - 1] : null;
                if (lastB !== null && els[k9].y1 < lastB.y2 + 0.5) {
                    lastB.els.push(els[k9]);
                    if (els[k9].y2 > lastB.y2) { lastB.y2 = els[k9].y2; }
                } else {
                    bands.push({ y1: els[k9].y1, y2: els[k9].y2, els: [els[k9]] });
                }
            }
            // her ortak metin grubu (yönergesinden son sorusuna) tek birim; aradaki bantlar da gruba ait
            var unitOf = [];
            for (k9 = 0; k9 < bands.length; k9++) { unitOf.push(-1); }
            for (k9 = 0; k9 < zl.length; k9++) {
                var fb = -1, lb = -1;
                for (j9 = 0; j9 < bands.length; j9++) {
                    for (var e8 = 0; e8 < bands[j9].els.length; e8++) {
                        var el8 = bands[j9].els[e8];
                        var mine = (el8.t === "f" && el8.rec === zl[k9].dirRec) || (el8.t === "o" && el8.ob === zl[k9].dirRec) ||
                                   (el8.t === "q" && el8.p.slot.zone === zl[k9].z);
                        if (mine) { if (fb < 0) { fb = j9; } lb = j9; }
                    }
                }
                if (fb < 0) { return null; }
                for (j9 = fb; j9 <= lb; j9++) {
                    if (unitOf[j9] >= 0 && unitOf[j9] !== 1000 + fb) { return null; }   // iç içe/kesişen gruplar
                    unitOf[j9] = 1000 + fb;
                }
            }
            var units = [];
            for (k9 = 0; k9 < bands.length; k9++) {
                var key9 = (unitOf[k9] >= 0) ? unitOf[k9] : -2;
                var lastU = units.length ? units[units.length - 1] : null;
                if (lastU !== null && lastU.key === key9) {
                    lastU.bands.push(bands[k9]); lastU.y2 = bands[k9].y2;
                } else {
                    units.push({ key: key9, link: key9 >= 0, bands: [bands[k9]], y1: bands[k9].y1, y2: bands[k9].y2 });
                }
            }
            if (units.length !== 2) { return null; }
            // serbest birimde yalnız serbest soru ve ayırıcı; grup biriminde başka bölgenin sorusu yok
            for (k9 = 0; k9 < 2; k9++) {
                for (j9 = 0; j9 < units[k9].bands.length; j9++) {
                    var bl9 = units[k9].bands[j9].els;
                    for (var e7 = 0; e7 < bl9.length; e7++) {
                        var el7 = bl9[e7];
                        if (el7.t === "q") {
                            var lk7 = isLinkZone(secB, el7.p.slot.zone);
                            if (units[k9].link !== lk7) { return null; }
                        } else if (!units[k9].link && el7.t !== "d") { return null; }
                        el7.u = k9;
                    }
                }
            }
            var U1 = units[0], U2 = units[1], gapU = U2.y1 - U1.y2;
            if (gapU < 0) { return null; }
            var dyU = [U2.y2 - U1.y2, U1.y1 - U2.y1];   // üst birim aşağı, alt birim yukarı
            // yeni okuma sırası: alttaki birimin soruları önce (kendi okuma sırasıyla), sonra üstteki
            var ord = [], plOf = {};
            for (k9 = 0; k9 < els.length; k9++) { if (els[k9].t === "q") { plOf[els[k9].p.slot.slotKey] = els[k9]; } }
            var uo = [1, 0];
            for (var uu = 0; uu < 2; uu++) {
                for (k9 = 0; k9 < slE.length; k9++) {
                    var eq9 = plOf[slE[k9].slotKey];
                    if (!eq9) { return null; }
                    if (eq9.u === uo[uu]) { ord.push(eq9); }
                }
            }
            if (ord.length !== slE.length) { return null; }
            var nums = fnE.slice(0);
            nums.sort(function (a, b) { return a - b; });
            var stN = 0;
            for (k9 = 0; k9 < ord.length; k9++) { if (ord[k9].p.cont.num === nums[k9]) { stN++; } }
            if (stN >= stE) { return null; }
            // grupların yeni aralığı (ardışık ve aynı genişlikte olmalı)
            var edits = [], logE = [];
            for (k9 = 0; k9 < zl.length; k9++) {
                var nLo = null, nHi = null, nC = 0;
                for (j9 = 0; j9 < ord.length; j9++) {
                    if (ord[j9].p.slot.zone !== zl[k9].z) { continue; }
                    nC++;
                    if (nLo === null || nums[j9] < nLo) { nLo = nums[j9]; }
                    if (nHi === null || nums[j9] > nHi) { nHi = nums[j9]; }
                }
                if (nC !== zl[k9].n || nHi - nLo !== zl[k9].hi - zl[k9].lo) { return null; }
                if (nLo !== zl[k9].lo) {
                    edits.push({ tf: zl[k9].dir.tf, lo: zl[k9].lo, hi: zl[k9].hi, delta: nLo - zl[k9].lo });
                    logE.push(zl[k9].lo + "-" + zl[k9].hi + " → " + nLo + "-" + nHi);
                }
            }
            var planE = { list: [], isBundle: true, tailMoves: [], divIn: [], nums: nums, fixMoves: [], dirEdits: edits };
            for (k9 = 0; k9 < ord.length; k9++) {
                planE.list.push({ cont: ord[k9].p.cont, ny1: ord[k9].p.ny1 + dyU[ord[k9].u], nx1: ord[k9].p.slot.x1, ord: k9 });
            }
            for (k9 = 0; k9 < els.length; k9++) {
                var ex = els[k9], dyx = dyU[ex.u];
                if (ex.t === "f") { planE.fixMoves.push({ it: ex.rec.tf, y0: ex.rec.y1, dy: dyx }); }
                else if (ex.t === "o") { planE.fixMoves.push({ it: ex.ob.it, y0: ex.ob.b[0], dy: dyx, ob: ex.ob }); }
                else if (ex.t === "d") {
                    var dB = ex.dv.b, nTopD = dB[0] + dyx;
                    // aşağı inen birimin ayırıcısı A'da bölgenin altına kadar iniyorsa yine oraya kadar iner
                    var nBotD = (dyx > 0 && dB[2] >= qBot - 3) ? dB[2] : ex.y2 + dyx;
                    if (nBotD > pdB.QB + 0.5) { nBotD = pdB.QB + 0.5; }
                    planE.fixMoves.push({ it: ex.dv.it, y0: dB[0], dy: dyx, dv: ex.dv, top: nTopD, bot: nBotD });
                }
            }
            return { plan: planE, st: stN, log: "s." + pdB.name + (logE.length ? " (yönerge " + logE.join(", ") + ")" : "") };
        }
        progress("Ortak metinli sayfalarda bant sırası deneniyor…", true);
        if (chkBundle.value && mode !== "col") {
            for (pi = 0; pi < pageData.length; pi++) {
                var pdE = pageData[pi];
                if (pdE.bundleWith >= 0 || pdE.reorder) { continue; }
                var slE = pageSlots(pi);
                if (slE.length < 2) { continue; }
                var asE = assigns[pi], fnE = finalNumsOf(pi), stE = 0, okE = true, hasLinkE = false;
                for (k = 0; k < slE.length; k++) {
                    if (asE[slE[k].slotKey].num === fnE[k]) { stE++; }
                    if (slE[k].sec !== slE[0].sec || slE[k].sec < 0 || slE[k].pool !== 0 || slE[k].grup >= 600000) { okE = false; }
                    if (isLinkZone(slE[k].sec, slE[k].zone)) { hasLinkE = true; }
                }
                if (stE === 0 || !okE || !hasLinkE) { continue; }
                // bant takasından sonra da numarası aynı kalan olmasın diye her grubun (bölge + şekil)
                // içerikleri kendi slotları arasında farklı dizilişlerle denenir
                var grE = {}, gkE = [], g9;
                for (k = 0; k < slE.length; k++) {
                    var gk9 = slE[k].zone + "|" + slE[k].shape + "|" + slE[k].grup;
                    if (!grE[gk9]) { grE[gk9] = []; gkE.push(gk9); }
                    grE[gk9].push(slE[k]);
                }
                var trialsE = [asE];
                for (g9 = 0; g9 < gkE.length; g9++) {
                    var grp9 = grE[gkE[g9]];
                    if (grp9.length < 2 || grp9.length > 4) { continue; }
                    var perm9 = allPerms(grp9.length), nxt9 = [];
                    for (var t9 = 0; t9 < trialsE.length; t9++) {
                        var base9 = trialsE[t9], cont9 = [];
                        for (k = 0; k < grp9.length; k++) { cont9.push(base9[grp9[k].slotKey]); }
                        for (var p9 = 0; p9 < perm9.length && nxt9.length < 96; p9++) {
                            var tr9 = copyAssign(base9);
                            for (k = 0; k < grp9.length; k++) { tr9[grp9[k].slotKey] = cont9[perm9[p9][k]]; }
                            nxt9.push(tr9);
                        }
                    }
                    if (nxt9.length > 0) { trialsE = nxt9; }
                }
                var bpE = null, bpAs = null;
                for (t9 = 0; t9 < trialsE.length; t9++) {
                    var bp9 = bandSwapPlan(pi, slE, trialsE[t9], fnE, stE);
                    if (bp9 !== null && (bpE === null || bp9.st < bpE.st)) { bpE = bp9; bpAs = trialsE[t9]; if (bp9.st === 0) { break; } }
                }
                if (bpE === null) { continue; }
                assigns[pi] = bpAs;
                pdE.reorder = bpE.plan;
                bandLog.push(bpE.log);
            }
            if (bandLog.length > 0) {
                info("Ortak metinli sayfada bant sırası: " + bandLog.join(", ") + " — ortak metin grubu ile diğer sorular sayfa içinde yer değiştirdi; yönerge numaraları güncellendi.");
            }
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
                    // v4.24: blok kısaldıysa kuyruk ("TESTİ BİTTİ" vb.) yukarı çekilmez, A'daki yerinde kalır
                    var tyA = newBotA + (A1.tail[k].y1 - A1.bot); if (tyA < A1.tail[k].y1) { tyA = A1.tail[k].y1; }
                    planA.tailMoves.push({ it: A1.tail[k], ny1: tyA });
                }
                var newBotB = B1.top + A1.aH;
                for (k = 0; k < B1.tail.length; k++) {
                    var tyB = newBotB + (B1.tail[k].y1 - B1.bot); if (tyB < B1.tail[k].y1) { tyB = B1.tail[k].y1; }
                    planB.tailMoves.push({ it: B1.tail[k], ny1: tyB });
                }
                // v4.19: soru bandındaki dikey sütun ayırıcıları kendi içerikleriyle birlikte
                // karşı sayfaya geçer (aksi hâlde ayırıcı, gelen tam genişlik sorunun ortasından geçer).
                var bandDividers = function (inf) {
                    var out = [], dl2 = pageData[inf.pdi].dividers || [];
                    for (var dd = 0; dd < dl2.length; dd++) {
                        if (dl2[dd].b[0] >= inf.top - 8 && dl2[dd].b[0] < inf.bot) { out.push(dl2[dd]); }
                    }
                    return out;
                };
                // v4.24: kaynak sayfanın güncel yerleşiminde sütun bloğu kaydıysa ayırıcının üst ucu da o kadar kayar
                var regShiftOf = function (inf, dv) {
                    var rgs = inf.plc ? inf.plc.regs : null;
                    if (!rgs) { return 0; }
                    for (var rq2 = 0; rq2 < rgs.length; rq2++) {
                        if (Math.abs(dv.b[0] - rgs[rq2].top) <= 8 && dv.b[0] < rgs[rq2].bot) { return rgs[rq2].shift; }
                    }
                    return 0;
                };
                planA.divIn = []; planB.divIn = [];
                var dvB = bandDividers(B1), dvA = bandDividers(A1);
                for (k = 0; k < dvB.length; k++) {
                    // v4.25: alt uç soru sınırına (QB) göre; hedef sayfanın sınırını aşmaz
                    var botB = (dvB[k].b[2] >= pageData[B1.pdi].QB - 3) ? pageData[A1.pdi].QB - 0.5 : dvB[k].b[2] + dyToA;
                    if (botB > pageData[A1.pdi].QB - 0.5) { botB = pageData[A1.pdi].QB - 0.5; }
                    planA.divIn.push({ d: dvB[k], from: B1.pdi, top: dvB[k].b[0] + regShiftOf(B1, dvB[k]) + dyToA, bot: botB });
                }
                for (k = 0; k < dvA.length; k++) {
                    var botA = (dvA[k].b[2] >= pageData[A1.pdi].QB - 3) ? pageData[B1.pdi].QB - 0.5 : dvA[k].b[2] + dyToB;
                    if (botA > pageData[B1.pdi].QB - 0.5) { botA = pageData[B1.pdi].QB - 0.5; }
                    planB.divIn.push({ d: dvA[k], from: A1.pdi, top: dvA[k].b[0] + regShiftOf(A1, dvA[k]) + dyToB, bot: botA });
                }
                pagePlans[A1.pdi] = planA;
                pagePlans[B1.pdi] = planB;
            } else if (pdP.reorder) {
                pagePlans[pi] = pdP.reorder;   // v4.24: sayfa içi blok sırası (Faz 2d)
            } else {
                var lvlP = fitLevel(pdP, assigns[pi]);
                if (lvlP < 0) {
                    log("Ayrıntı: s." + pdP.name + " — sayfanın A düzeni doğrulanamadı; güvenlik için dokunulmadı.");
                    if (!revertWhy[pi]) { revertWhy[pi] = "sayfanın A düzeni ölçülerek doğrulanamadı, güvenlik için dokunulmadı"; }
                    continue;
                }
                var placements = layoutAt(pdP, assigns[pi], lvlP);
                var planN = { list: [], isBundle: false, scale: LEVELS[lvlP].s, slotOf: [], regs: placements.regs };
                for (k = 0; k < placements.length; k++) {
                    planN.list.push({ cont: placements[k].cont, ny1: placements[k].ny1,
                                      nx1: placements[k].slot.x1, slot: placements[k].slot });
                }
                pagePlans[pi] = planN;
                if (LEVELS[lvlP].s < 1.0) {
                    log("Ayrıntı: s." + pdP.name + " — sorular arası boşluklar %" + Math.round(LEVELS[lvlP].s * 100) + " ölçeğinde sıkıştırıldı.");
                }
            }
        }

        // v4.19: soruya ait serbest çerçeveleri sorunun zarf ötelemesi kadar taşı.
        // move() içerikle birlikte taşır (geometricBounds görseli kırpabilirdi).
        // Taşınamayan olursa false döner; bekçi o sayfayı geri alır.
        function moveComps(cont, targetPi, dy, dx) {
            if (!cont.comps) { return true; }
            var okC = true;
            for (var cq = 0; cq < cont.comps.length; cq++) {
                var cp = cont.comps[cq];
                try {
                    if (cp.cur !== targetPi) { cp.it.move(pages[targetPi]); cp.cur = targetPi; }
                    var gNow = cp.it.geometricBounds;
                    var ddx = (cp.b[1] + dx) - gNow[1], ddy = (cp.b[0] + dy) - gNow[0];
                    if (ddx > 0.01 || ddx < -0.01 || ddy > 0.01 || ddy < -0.01) {
                        cp.it.move(undefined, [ddx, ddy]);
                    }
                } catch (eCp) { okC = false; }
            }
            return okC;
        }

        // v4.19: iki sütunlu blok kaydıysa, bloğun üstünden başlayan dikey ayırıcının
        // üst ucunu da aynı miktarda kaydır (alt ucu yerinde kalır).
        function adjustDividers(pi4, plan4, regs4) {
            plan4.divMoves = [];
            var dvs = pageData[pi4].dividers || [];
            if (!regs4 || dvs.length === 0) { return; }
            for (var rq = 0; rq < regs4.length; rq++) {
                var rg = regs4[rq];
                if (rg.shift < 0.01 && rg.shift > -0.01) { continue; }
                for (var dq = 0; dq < dvs.length; dq++) {
                    var dv = dvs[dq];
                    if (Math.abs(dv.b[0] - rg.top) > 8 || dv.b[0] >= rg.bot) { continue; }
                    var nTop = dv.b[0] + rg.shift;
                    if (nTop > dv.b[2] - 10) { continue; }
                    try { dv.it.geometricBounds = [nTop, dv.b[1], dv.b[2], dv.b[3]]; plan4.divMoves.push(dv); } catch (eDv2) {}
                }
            }
        }
        function restoreDividers(plan5) {
            if (!plan5 || !plan5.divMoves) { return; }
            for (var dr = 0; dr < plan5.divMoves.length; dr++) {
                try { plan5.divMoves[dr].it.geometricBounds = plan5.divMoves[dr].b.slice(0); } catch (eDv3) {}
            }
            plan5.divMoves = [];
        }

        // v4.26: ortak metin bandı takasında sabit öğeler (yönerge, metin, şekil, ayırıcı) bandıyla
        // birlikte dikeyde kayar; back=true A konumuna geri götürür.
        function applyFixMoves(planF, back) {
            for (var fq = 0; fq < planF.fixMoves.length; fq++) {
                var fm = planF.fixMoves[fq];
                if (back && !fm.moved) { continue; }
                try {
                    if (fm.dv) {
                        fm.it.geometricBounds = back ? fm.dv.b.slice(0) : [fm.top, fm.dv.b[1], fm.bot, fm.dv.b[3]];
                    } else {
                        var gF = fm.it.geometricBounds;
                        var ddyF = (back ? fm.y0 : fm.y0 + fm.dy) - gF[0];
                        if (ddyF > 0.01 || ddyF < -0.01) { fm.it.move(undefined, [0, ddyF]); }
                    }
                    if (fm.ob) {
                        if (!back) { fm.ob.b0 = fm.ob.b.slice(0); fm.ob.b = [fm.ob.b0[0] + fm.dy, fm.ob.b0[1], fm.ob.b0[2] + fm.dy, fm.ob.b0[3]]; }
                        else if (fm.ob.b0) { fm.ob.b = fm.ob.b0; }
                    }
                    fm.moved = !back;
                    if (!back) { fm.err = false; }
                } catch (eFm) { if (!back) { fm.err = true; } }
            }
        }

        // Yerleştir (mutlak konum; sayfa değişimi move ile)
        progress("Sorular yerleştiriliyor…", true);
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
                pe.cont.compErr = !moveComps(pe.cont, pi, pe.ny1 - pe.cont.y1, pe.nx1 - pe.cont.x1);
                movedCount++;
            }
            if (!plan.isBundle) { adjustDividers(pi, plan, plan.regs); }
            if (plan.isBundle && plan.divIn) {
                for (k = 0; k < plan.divIn.length; k++) {
                    var di = plan.divIn[k];
                    try {
                        di.d.it.move(pages[pi]);
                        di.d.it.geometricBounds = [di.top, di.d.b[1], di.bot, di.d.b[3]];
                        di.moved = true;
                    } catch (eDi) { di.err = true; }
                }
            }
            if (plan.isBundle) {
                for (k = 0; k < plan.tailMoves.length; k++) {
                    var tm = plan.tailMoves[k];
                    var hT2 = tm.it.y2 - tm.it.y1;
                    try { tm.it.tf.geometricBounds = [tm.ny1, tm.it.x1, tm.ny1 + hT2, tm.it.x2]; } catch (eT) {}
                }
            }
            if (plan.fixMoves) { applyFixMoves(plan, false); }
        }
        log("Ayrıntı: yerleştirme — " + movedCount + " çerçeve taşındı (" + xPageMoves + " tanesi sayfa değiştirdi).");

        // -----------------------------------------------------
        // 12) BİNDİRME DENETİMİ + GERİ ALMA (numaralamadan ÖNCE)
        // -----------------------------------------------------
        function auditLog(pi5, msg) {
            var why = trimS(String(msg).replace(/\s*\u2014\s*sayfa (A düzenine )?geri alındı\.?\s*$/, "").replace(/^\s*\u2014\s*/, ""));
            why = why.replace("bindirme saptandı", "karışık düzende üst üste binme olacaktı")
                     .replace("taşma saptandı", "karışık düzende sayfadan taşma olacaktı");
            if (!revertWhy[pi5]) { revertWhy[pi5] = why; }
            log("Ayrıntı: s." + pageData[pi5].name + " — " + why + " — bu sayfa A düzeninde bırakıldı.");
        }
        function rectsOverlap(a, b) {
            return !(a[2] <= b[0] + 1 || b[2] <= a[0] + 1 || a[3] <= b[1] + 1 || b[3] <= a[1] + 1);
        }
        function auditPage(pi2) {
            var plan2 = pagePlans[pi2];
            if (plan2 === null) { return true; }
            if (plan2.fixMoves) {
                for (var fe = 0; fe < plan2.fixMoves.length; fe++) {
                    if (plan2.fixMoves[fe].err) {
                        auditLog(pi2, " — ortak metin bandındaki bir sabit öğe taşınamadı (kilitli nesne/katman?) — sayfa A düzenine geri alındı.");
                        return false;
                    }
                }
            }
            for (var qc = 0; qc < plan2.list.length; qc++) {
                if (plan2.list[qc].cont.compErr) {
                    auditLog(pi2, " — S" + plan2.list[qc].cont.num +
                        " sorusuna ait görsel/şekil çerçevesi taşınamadı (kilitli nesne/katman?) — sayfa A düzenine geri alındı.");
                    return false;
                }
            }
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
                var touch = false, touchD = 0;
                var fr0 = [itA.y1, itA.x1, itA.y2, itA.x2];
                for (var o5 = 0; o5 < origQ0.length; o5++) {
                    if (dOv0(fr0, origQ0[o5])) {
                        touch = true;
                        // v4.24: A'daki temasın dikey derinliği (B'de bundan derin değilse tasarım gereğidir)
                        var dT = ((fr0[2] < origQ0[o5][2]) ? fr0[2] : origQ0[o5][2]) - ((fr0[0] > origQ0[o5][0]) ? fr0[0] : origQ0[o5][0]);
                        if (dT > touchD) { touchD = dT; }
                    }
                }
                fixRects.push([gb4[0], gb4[1], gb4[2], gb4[3],
                               "[" + itA.kind + " \u2018" + itA.etiket + "\u2019 y" +
                               Math.round(itA.y1) + ".." + Math.round(itA.y2) + "]", touch, touchD]);
            }
            // içerik × içerik → geri al (kanıtlı felaket)
            for (var a2 = 0; a2 < contRects.length; a2++) {
                for (var b2i = a2 + 1; b2i < contRects.length; b2i++) {
                    if (rectsOverlap(contRects[a2], contRects[b2i])) {
                        auditLog(pi2, " bindirme saptandı (" +
                            contRects[a2][4] + " × " + contRects[b2i][4] + ") — sayfa A düzenine geri alındı.");
                        return false;
                    }
                }
                if (contRects[a2][2] > pageData[pi2].QB + 2) {
                    auditLog(pi2, " taşma saptandı (" + contRects[a2][4] + ") — sayfa geri alındı.");
                    return false;
                }
                // içerik × sabit: sabit A'da zaten bir soruya değiyorsa tasarım gereğidir → UYARI
                for (var f2 = 0; f2 < fixRects.length; f2++) {
                    if (rectsOverlap(contRects[a2], fixRects[f2])) {
                        if (fixRects[f2][5]) {
                            var dNow = ((contRects[a2][2] < fixRects[f2][2]) ? contRects[a2][2] : fixRects[f2][2]) -
                                       ((contRects[a2][0] > fixRects[f2][0]) ? contRects[a2][0] : fixRects[f2][0]);
                            if (dNow > fixRects[f2][6] + 1) {
                                log("UYARI: s." + pageData[pi2].name + " — " + contRects[a2][4] + " ile " +
                                    fixRects[f2][4] + " A'dakinden " + Math.round(dNow - fixRects[f2][6]) +
                                    " pt daha fazla kesişiyor (A'da da bu çerçeve bir soruya değiyordu); baskı öncesi göz atın.");
                            }
                        } else {
                            auditLog(pi2, " bindirme saptandı (" +
                                contRects[a2][4] + " × " + fixRects[f2][4] + ") — sayfa A düzenine geri alındı.");
                            return false;
                        }
                    }
                }
            }
            // v4.19: içerik × çizgi — A'da bu sayfadaki hiçbir soruyu kesmeyen bir çizgi
            // (sütun ayırıcı, bölüm çizgisi) taşınan bir sorunun içinden geçmemeli.
            var compLineIds = {}, hasCompLines = false;
            for (q2 = 0; q2 < plan2.list.length; q2++) {
                var cpl = plan2.list[q2].cont.comps || [];
                for (var cl = 0; cl < cpl.length; cl++) { try { compLineIds[cpl[cl].it.id] = true; hasCompLines = true; } catch (eCl) {} }
            }
            var lnColl = null, linesP = [], linesB = [];
            try { lnColl = pages[pi2].graphicLines; linesP = itemsOf(lnColl); linesB = boundsOf(lnColl, linesP); } catch (eLn) { linesP = []; }
            for (var ln = 0; ln < linesP.length; ln++) {
                var lgb = linesB[ln];
                if (!lgb) { continue; }
                if (hasCompLines) {
                    var lid = -1;
                    try { lid = linesP[ln].id; } catch (eLn2) {}
                    if (compLineIds[lid]) { continue; }
                }
                var vert = (lgb[3] - lgb[1]) < 3, horz = (lgb[2] - lgb[0]) < 3;
                if (!vert && !horz) { continue; }
                var crosses = function (e) {
                    if (vert) { var lx = (lgb[1] + lgb[3]) / 2; return lx > e[1] + 3 && lx < e[3] - 3 && (Math.min(lgb[2], e[2]) - Math.max(lgb[0], e[0])) > 3; }
                    var ly = (lgb[0] + lgb[2]) / 2; return ly > e[0] + 3 && ly < e[2] - 3 && (Math.min(lgb[3], e[3]) - Math.max(lgb[1], e[1])) > 3;
                };
                var crossedInA = false;
                for (var oq = 0; oq < origQ0.length; oq++) { if (crosses(origQ0[oq])) { crossedInA = true; break; } }
                if (crossedInA) { continue; }
                for (var cq2 = 0; cq2 < contRects.length; cq2++) {
                    if (crosses(contRects[cq2])) {
                        auditLog(pi2, " — " + contRects[cq2][4] +
                            " sayfadaki bir çizginin (sütun ayırıcı vb.) üstüne düşüyor — sayfa A düzenine geri alındı.");
                        return false;
                    }
                }
            }
            // v4.19: içerik × grafik engel (soruya ait olmayan dikdörtgen/görsel/şekil)
            var obsP = pageData[pi2].obstacles || [];
            for (var ca = 0; ca < contRects.length; ca++) {
                for (var oo = 0; oo < obsP.length; oo++) {
                    var ogb2 = obsP[oo].b;   // engeller taşınmaz: envanterdeki sınır yeterli
                    if (dOv0(contRects[ca], ogb2)) {
                        auditLog(pi2, " — " + contRects[ca][4] +
                            " sayfadaki görsel/şekil çerçevesine biniyor — sayfa A düzenine geri alındı.");
                        return false;
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
                moveComps(c4, c4.page, 0, 0);   // v4.19: bağlı serbest çerçeveler de A yerine
                c4.compErr = false;
            }
            restoreDividers(plan3);
            if (plan3.isBundle && plan3.divIn) {
                for (var t8 = 0; t8 < plan3.divIn.length; t8++) {
                    var di3 = plan3.divIn[t8];
                    if (!di3.moved) { continue; }
                    try { di3.d.it.move(pages[di3.from]); di3.d.it.geometricBounds = di3.d.b.slice(0); } catch (eDi3) {}
                    di3.moved = false;
                }
            }
            if (plan3.isBundle) {
                for (var t6 = 0; t6 < plan3.tailMoves.length; t6++) {
                    var it6 = plan3.tailMoves[t6].it;
                    try { it6.tf.geometricBounds = [it6.fy1, it6.fx1, it6.fy2, it6.fx2]; } catch (eGb2) {}
                }
            }
            if (plan3.fixMoves) { applyFixMoves(plan3, true); }
            pagePlans[pi3] = null;
        }
        // v4.11: TAKAS-ATOMİK GERİ ALMA — bir sayfa iptal ediliyorsa, onunla
        // içerik alışverişi yapan tüm sayfalar KAPANIŞ KÜMESİ olarak birlikte
        // geri alınır. (Tek kanatlı iptal, karşı sayfada çift soru bırakıyordu.)
        var failed = {};
        progress("Bindirme denetimi…", true);
        for (pi = 0; pi < pageData.length; pi++) {
            if (pagePlans[pi] === null) { continue; }
            progress("Bindirme denetimi: " + (pi + 1) + " / " + pageData.length);
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
            log("Ayrıntı: takas bütünlüğü için birlikte geri alınanlar: " + closureExtra.join(", "));
        }

        // v4.15 İKİNCİ ŞANS: geri alınan sayfalar A'da kalmasın — yalnız
        // sayfa-içi, sıkıştırmasız güvenli karışım denenir ve bekçiden
        // geçerse kabul edilir.
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
                var bestR = null, bD = -1, bS = -1, bK = 100000;
                for (var pR = 0; pR < permsR.length; pR++) {
                    var prR = permsR[pR];
                    var tR = copyAssign(aR);
                    for (k = 0; k < mR2; k++) { tR[grpR[k].slotKey] = contsR[prR[k]]; }
                    var spR = strictPlc(pdR, tR);
                    if (spR === null) { continue; }
                    var dR = 0, sR = 0, kR = rowBreaks(pdR, spR);
                    for (k = 0; k < mR2; k++) {
                        if (prR[k] !== k) { dR++; }
                        sR += (prR[k] > k) ? (prR[k] - k) : (k - prR[k]);
                    }
                    if (dR > bD || (dR === bD && (kR < bK || (kR === bK && sR > bS)))) { bestR = prR; bD = dR; bS = sR; bK = kR; }
                }
                if (bestR !== null && bD > 0) {
                    for (k = 0; k < mR2; k++) { aR[grpR[k].slotKey] = contsR[bestR[k]]; }
                    anyPerm = true;
                }
            }
            if (!anyPerm) { continue; }
            var plcR = strictPlc(pdR, aR);
            if (plcR === null) { continue; }
            var planR = { list: [], isBundle: false, regs: plcR.regs };
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
                peR.cont.compErr = !moveComps(peR.cont, pi, peR.ny1 - peR.cont.y1, peR.nx1 - peR.cont.x1);
            }
            pagePlans[pi] = planR;
            adjustDividers(pi, planR, planR.regs);
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
            log("Ayrıntı: ikinci deneme — sayfa-içi güvenli karışımla kurtarıldı: " + rescued.join(", "));
        }
        // v4.22: son durumda A düzeninde kalan sayfalar (kurtarılamayanlar)
        var keptA = [];
        for (pi = 0; pi < pageData.length; pi++) {
            if (failed[pi] && pagePlans[pi] === null) { keptA.push("s." + pageData[pi].name); }
        }
        if (keptA.length > 0) {
            info("Güvenlik denetimi: " + keptA.length + " sayfa A düzeninde bırakıldı (" + keptA.join(", ") +
                 ") — karışık düzende bir çakışma olacaktı; B dosyasında sorun yok, nedeni aşağıdaki listede.");
        }
        // v4.23: A'da aynı satırdan başlayan sol/sağ sorular B'de farklı hizada kaldıysa bildir
        // (yalnız o sayfadaki bir sorunun yerinde kalmaması için başka yol yoksa olur).
        var brkPg = [];
        for (pi = 0; pi < pageData.length; pi++) {
            var plBk = pagePlans[pi];
            if (plBk === null || plBk.isBundle) { continue; }
            if (rowBreaks(pageData[pi], plBk.list) > 0) { brkPg.push("s." + pageData[pi].name); }
        }
        if (brkPg.length > 0) {
            log("UYARI: " + brkPg.join(", ") + " — A'da aynı hizadan başlayan sol/sağ sütun soruları B'de farklı hizadan başlıyor " +
                "(sorunun yerinde kalmaması için başka yerleşim yoktu). Baskı öncesi göz atın.");
        }

        // -----------------------------------------------------
        // 13) NUMARALANDIRMA ve EŞLEME
        //     Normal sayfalar: slot numarası içeriğe yazılır.
        //     Blok takaslı bölümler: bölüm baştan sıralı numaralanır.
        // -----------------------------------------------------
        // bundle iptal olduysa bölümü yeniden numaralamaya gerek kalmayabilir;
        // yine de bundleSecs'te kalan bölümler için güvenli tam numaralama yapılır.
        progress("Numaralar ve cevap anahtarı yazılıyor…", true);
        var mapping = [];
        // v4.26: yönerge metnindeki numara dizisini delta kadar kaydır (biçim korunur: yalnız rakamlar değişir)
        function applyDirEdit(ed) {
            try {
                var stD = ed.tf.parentStory;
                var spD = directiveSpan(String(stD.texts[0].contents), ed.lo, ed.hi);
                if (spD === null) { return false; }
                clearGrep();
                app.findGrepPreferences.findWhat = "\\d{1,3}";
                var fD = stD.findGrep();
                clearGrep();
                var toks = [];
                for (var fq = 0; fq < fD.length; fq++) {
                    var ixD = -1;
                    try { ixD = fD[fq].insertionPoints[0].index; } catch (eIx) { try { ixD = fD[fq].index; } catch (eIx2) { ixD = -1; } }
                    if (ixD >= spD.s && ixD < spD.e) { toks.push(fD[fq]); }
                }
                if (toks.length === 0) { return false; }
                for (var tq = toks.length - 1; tq >= 0; tq--) {
                    var vD = parseInt(String(toks[tq].contents), 10);
                    if (isNaN(vD)) { return false; }
                    toks[tq].contents = String(vD + ed.delta);
                }
                return directiveSpan(String(stD.texts[0].contents), ed.lo + ed.delta, ed.hi + ed.delta) !== null;
            } catch (eDe) { return false; }
        }
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
        // v4.26: önce TÜM numaralar hesaplanır (yazılmadan), her test A'daki numara kümesiyle
        // karşılaştırılır; tutmazsa (eksik/tekrar) o test okuma sırasına göre 1..N numaralanır.
        // Sayaç artık "son okunan" değil "o ana kadarki en büyük" numaradır: sayfanın soruları
        // hangi sırayla gezilirse gezilsin sonraki blok sayfası doğru numaradan başlar.
        var counters = [];
        for (k = 0; k < totalSections; k++) { counters.push(0); }
        var numJobs = [];
        for (pi = 0; pi < pageData.length; pi++) {
            var planM = pagePlans[pi];
            if (planM === null) {
                // değişmemiş sayfa: eşleme kimlik olarak yazılır
                pageQuestionWalk(pageData[pi], function (r) {
                    if (r.kind !== "soru") { return; }
                    var nn0;
                    if (bundleSecs[r.sec]) { counters[r.sec]++; nn0 = counters[r.sec]; }
                    else { nn0 = r.num; if (nn0 > counters[r.sec]) { counters[r.sec] = nn0; } }
                    numJobs.push({ r: r, nn: nn0, pi: pi });
                });
                continue;
            }
            // planlı sayfa: içerikler plan.list sırasıyla (bundle: kaynak düzen sırası;
            // normal: slot okuma sırası zaten; sayfa içi blok sırası: Faz 2d'nin numara listesi)
            for (k = 0; k < planM.list.length; k++) {
                var peM = planM.list[k];
                var cM = peM.cont;
                var nn;
                if (planM.nums && planM.nums.length === planM.list.length) {
                    nn = planM.nums[k];
                    if (nn > counters[cM.sec]) { counters[cM.sec] = nn; }
                } else if (planM.isBundle || bundleSecs[cM.sec]) {
                    counters[cM.sec]++;
                    nn = counters[cM.sec];
                } else {
                    nn = peM.slot.num;
                    if (nn > counters[cM.sec]) { counters[cM.sec] = nn; }
                }
                numJobs.push({ r: cM, nn: nn, pi: pi });
            }
        }
        // kuru doğrulama: her testte B numaraları A numaralarının aynısı (aynı küme, aynı tekrar sayısı)
        var cntA = [], cntB = [], badSec = [];
        for (k = 0; k < totalSections; k++) { cntA.push({}); cntB.push({}); }
        for (k = 0; k < numJobs.length; k++) {
            var sJ = numJobs[k].r.sec;
            if (sJ < 0 || sJ >= totalSections) { continue; }
            cntA[sJ][numJobs[k].r.num] = (cntA[sJ][numJobs[k].r.num] || 0) + 1;
            cntB[sJ][numJobs[k].nn] = (cntB[sJ][numJobs[k].nn] || 0) + 1;
        }
        for (k = 0; k < totalSections; k++) {
            var okJ = true, nk;
            for (nk in cntA[k]) { if (cntA[k].hasOwnProperty(nk) && cntA[k][nk] !== (cntB[k][nk] || 0)) { okJ = false; } }
            for (nk in cntB[k]) { if (cntB[k].hasOwnProperty(nk) && cntB[k][nk] !== (cntA[k][nk] || 0)) { okJ = false; } }
            if (!okJ) { badSec.push(k); }
        }
        for (var bs = 0; bs < badSec.length; bs++) {
            var rk = 0;
            for (k = 0; k < numJobs.length; k++) {
                if (numJobs[k].r.sec === badSec[bs]) { rk++; numJobs[k].nn = rk; }
            }
            log("UYARI: Test " + (badSec[bs] + 1) + " numaraları planla tutmadı (eksik/tekrar); test okuma sırasına göre 1-" + rk +
                " numaralandı. Bu testin ortak metin yönergelerini kontrol edin.");
        }
        // v4.26: ortak metin bandı yer değiştiren sayfalarda yönerge numaraları güncellenir
        for (pi = 0; pi < pageData.length; pi++) {
            var planD = pagePlans[pi];
            if (planD === null || !planD.dirEdits) { continue; }
            for (k = 0; k < planD.dirEdits.length; k++) {
                var edD = planD.dirEdits[k];
                if (!applyDirEdit(edD)) {
                    log("KRİTİK: s." + pageData[pi].name + " — ortak metin yönergesindeki \u201C" + edD.lo + "-" + edD.hi + "\u201D numaraları \u201C" +
                        (edD.lo + edD.delta) + "-" + (edD.hi + edD.delta) + "\u201D olarak güncellenemedi; yönergeyi elle düzeltin.");
                }
            }
        }
        for (k = 0; k < numJobs.length; k++) {
            var jb = numJobs[k], rJ = jb.r;
            if (!writeNum(rJ, jb.nn)) { log("UYARI: S" + rJ.num + " numarası bulunamadı (s." + pageData[jb.pi].name + ")."); }
            mapping.push({ sec: rJ.sec, oldNum: rJ.num, oldPage: pageData[rJ.page].name,
                           newNum: jb.nn, newPage: pageData[jb.pi].name, ans: rJ.ans, shape: rJ.shape,
                           keySkip: (rJ.keySkip === true), rec: rJ });
        }

        // bütünlük denetimi + yerinde kalan raporu
        var chkArr = [];
        for (k = 0; k < totalSections; k++) { chkArr.push({}); }
        // v4.22: yerinde kalan her soru için anlaşılır neden
        function stayReason(r) {
            var tip = (r.shape === "FW") ? "tam genişlik" : "sütun";
            if (r.grup >= 900000) { return "önceki testin son sorusu, yeni testin sayfasında duruyor"; }
            if (r.grup >= 800000) {
                return r.keySkip ? "testte aynı numaralı başka bir soru var (A dosyasını kontrol edin)"
                                 : "önceki testin soruları arasında okundu; numarası korunarak bırakıldı";
            }
            if (r.orphanLock) { return "yönergesi tanınmayan bir metnin altında; hangi sorulara ait olduğu bilinemediği için yerinde bırakıldı"; }
            if (r.grup >= 650000) { return "\u201CBuna göre / Bu metne göre\u201D gibi dışarıdaki bir metne gönderme yapıyor, yönergesi yok"; }
            if (r.grup >= 600000) { return "ortak metni ya da yönergesini kendi içinde taşıyor"; }
            if (revertWhy[r.pdIdx] && pagePlans[r.pdIdx] === null) { return "sayfa A düzeninde bırakıldı: " + revertWhy[r.pdIdx]; }
            if (r.noXPage && r.orphanPg) { return "sayfada yönergesi tanınmayan uzun bir metin var; yalnız kendi sayfasında yer değiştirebiliyor, sayfada sığan eşi yok"; }
            if (r.noXPage) { return "A'da başka soruyla tek grup içinde; yalnız kendi sayfasında yer değiştirebiliyor, sayfada sığan eşi yok"; }
            if (mode === "col") { return "\u201CSütun içi ikili\u201D modunda sütununda eşi yok"; }
            var peers = 0;
            for (var pq3 = 0; pq3 < allSlots.length; pq3++) {
                var T3 = allSlots[pq3];
                if (T3 === r || T3.sec !== r.sec || T3.zone !== r.zone || T3.shape !== r.shape || T3.pool !== r.pool) { continue; }
                if (T3.grup !== r.grup && !(T3.grup === 0 && r.grup === 0)) { continue; }
                peers++;
            }
            if (peers === 0) {
                if (r.pool > 0) { return "özel havuzunda tek soru"; }
                if (isLinkZone(r.sec, r.zone)) { return "ortak metin grubunun tek sorusu"; }
                return "testte başka " + tip + " soru yok (sorular yalnız aynı türden soruyla yer değiştirir)";
            }
            return "yerine sığan " + tip + " soru bulunamadı (boyu uyan eş yok)";
        }
        var stillList = [], stayLines = [];
        var dupB = [];
        for (k = 0; k < totalSections; k++) { dupB.push({}); }
        for (k = 0; k < mapping.length; k++) {
            if (chkArr[mapping[k].sec][mapping[k].newNum] === true && !mapping[k].keySkip) { dupB[mapping[k].sec][mapping[k].newNum] = true; }
            chkArr[mapping[k].sec][mapping[k].newNum] = true;
            // v4.24: numarası aynı kalan soru, sayfası değişse bile cevap anahtarında aynı sıradadır
            if (mapping[k].oldNum === mapping[k].newNum) {
                var stTag = "Test " + (mapping[k].sec + 1) + " S" + mapping[k].newNum + " (s." + mapping[k].newPage + ")";
                stillList.push(stTag);
                stayLines.push(stTag + ": " + (mapping[k].oldPage !== mapping[k].newPage
                    ? "s." + mapping[k].oldPage + "'den bu sayfaya geçti ama numarası aynı kaldı"
                    : (mapping[k].rec ? stayReason(mapping[k].rec) : "nedeni belirlenemedi")));
            }
        }
        for (k = 0; k < totalSections; k++) {
            var eks = [];
            for (i = 1; i <= (secQCount[k] || 0); i++) { if (!chkArr[k][i]) { eks.push(i); } }
            if (eks.length > 0) { log("KRİTİK: Test " + (k + 1) + " numara dizisinde eksik: " + eks.join(",")); }
            var tkr = [];
            for (var dn in dupB[k]) { if (dupB[k].hasOwnProperty(dn)) { tkr.push(dn); } }
            if (tkr.length > 0) { log("KRİTİK: Test " + (k + 1) + " numara dizisinde tekrar: " + tkr.join(",")); }
        }
        for (k = 0; k < stayLines.length; k++) { log("Yerinde kalan: " + stayLines[k]); }

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
                    if (nmk !== mk) { sec.marker = nmk; chg++; log("Ayrıntı: bölüm işareti \u201C" + mk + "\u201D → \u201C" + nmk + "\u201D"); }
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
            if (bandChg > 0) { log("Ayrıntı: master üst bant " + bandChg + " çerçevede A→B yapıldı."); }
            // v4.19: kapak, arka kapak, anahtar sayfası gibi SORUSUZ sayfalardaki kitapçık harfi
            // ("A", "A KİTAPÇIĞI"). Soru sayfalarına dokunulmaz (şekillerdeki "A" etiketleri).
            // Değişim yerinde yapılır; harfin biçimi korunur.
            var coverChg = [];
            var BOOK_RE = /K[İI]TAP[ÇC][IİĞ]|kitap[çc][ıiğ]/;
            var LONE_A = /(^|[^0-9A-Za-zÇĞİÖŞÜçğıöşü])A([^0-9A-Za-zÇĞİÖŞÜçğıöşü]|$)/;
            for (pi = 0; pi < pageData.length; pi++) {
                var hasQp = false;
                pageQuestionWalk(pageData[pi], function (r) { if (r.kind === "soru") { hasQp = true; } });
                if (hasQp) { continue; }
                var apC = [];
                try { apC = pages[pi].allPageItems; } catch (eCv) { apC = []; }
                for (i = 0; i < apC.length; i++) {
                    if (apC[i].constructor.name !== "TextFrame") { continue; }
                    var stC = null, cC = "";
                    try { stC = apC[i].parentStory; cC = trimS(String(stC.texts[0].contents)); } catch (eCv2) { continue; }
                    if (cC.length === 0 || cC.length > 40) { continue; }
                    var bandA = /^A([\s\u00A0\u2000-\u200B\u202F\u205F\u3000]+A)*$/.test(cC);
                    if (!bandA && !(BOOK_RE.test(cC) && LONE_A.test(cC))) { continue; }
                    clearGrep();
                    app.findGrepPreferences.findWhat = "(?<![\\w])A(?![\\w])";
                    var fA = stC.findGrep();
                    clearGrep();
                    for (var fa = fA.length - 1; fa >= 0; fa--) { fA[fa].contents = "B"; }
                    if (fA.length > 0) { coverChg.push("s." + pageData[pi].name + " \u201C" + cC + "\u201D"); }
                }
            }
            if (coverChg.length > 0) { log("Ayrıntı: sorusuz sayfada kitapçık harfi A→B: " + coverChg.join(", ")); }
            var harfYer = [];
            if (chg > 0) { harfYer.push("bölüm işareti"); }
            if (bandChg > 0) { harfYer.push("master üst bant (" + bandChg + " çerçeve)"); }
            if (coverChg.length > 0) { harfYer.push("kapak/sorusuz sayfa (" + coverChg.length + " yer)"); }
            if (harfYer.length > 0) { info("Kitapçık harfi A → B yapıldı: " + harfYer.join(", ") + "."); }
            else { log("UYARI: Belgede A kitapçık harfi (bölüm işareti, master bant ya da kapakta) bulunamadı — B harfini elle kontrol edin."); }
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
                var mapAt = [];
                for (k = 0; k < totalSections; k++) { mapAt.push([]); }
                for (k = 0; k < mapping.length; k++) {
                    if (mapping[k].keySkip) { continue; }
                    oldNumOf[mapping[k].sec][mapping[k].newNum] = mapping[k].oldNum;
                    mapAt[mapping[k].sec][mapping[k].newNum] = mapping[k];
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
                        log("KRİTİK: A dosyasında Test " + (secIdx + 1) + " S" + num2 + " — cevap soru içinde \u201C" + expOld +
                            "\u201D, cevap anahtarında \u201C" + oldL + "\u201D. Hangisi doğruysa A'yı düzeltin (B anahtarına soru içindeki harf yazıldı).");
                    }
                    var newL = newLetters[secIdx][num2];
                    if (!newL || newL === "?") {
                        var oN = oldNumOf[secIdx][num2];
                        if (oN !== undefined && aKey[secIdx][oN]) {
                            newL = aKey[secIdx][oN]; fromKey++;
                            // v4.23: soru içinde cevap kodu yoksa CSV'deki harf de anahtardan gelir
                            if (mapAt[secIdx][num2] && mapAt[secIdx][num2].ans === "?") { mapAt[secIdx][num2].ans = newL; }
                        }
                    }
                    if (newL && newL !== "?" && newL !== oldL) {
                        toks[k].contents = num2 + "-" + newL;
                        updated++;
                    } else if (!newL || newL === "?") {
                        log("UYARI: Anahtar Test " + (secIdx + 1) + " S" + num2 + " için harf üretilemedi.");
                    }
                }
                info("Cevap anahtarı güncellendi: " + toks.length + " numaradan " + updated + " numarada harf değişti" +
                     (toks.length - updated > 0 ? ", " + (toks.length - updated) + " numarada aynı kaldı." : "."));
                if (fromKey > 0) {
                    log("Ayrıntı: " + fromKey + " sorunun harfi soru içinden okunamadı; A anahtar bloğundan eşlemeyle alındı.");
                }
            } else { log("UYARI: Cevap anahtarı bloğu bulunamadı — B kitapçığının cevap anahtarını elle hazırlayın."); }
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
                mapping.sort(function (a, b) { return (a.sec - b.sec) || (a.newNum - b.newNum) || (a.oldNum - b.oldNum); });
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
                info("Ayrıntılı rapor: " + decodeURI(csv.name));
            } else { log("UYARI: CSV yazılamadı."); }
        }

        var movedQ = 0;
        for (k = 0; k < mapping.length; k++) {
            if (mapping[k].oldNum !== mapping[k].newNum) { movedQ++; }
        }
        // v4.22: sade uyarı penceresi — özet, yerinde kalanlar (nedenleriyle), dikkat, bilgi
        var R = [];
        R.push(movedQ + " / " + mapping.length + " soru yer değiştirdi.");
        if (stayLines.length > 0) {
            R.push("");
            R.push("YERİNDE KALAN " + stayLines.length + " SORU");
            for (k = 0; k < stayLines.length; k++) { R.push("  \u2022 " + stayLines[k]); }
        }
        var dik = [], dikSeen = {};
        for (k = 0; k < LOG.length; k++) {
            if (/^(KRİTİK|UYARI)/.test(LOG[k]) && !dikSeen[LOG[k]]) { dikSeen[LOG[k]] = true; dik.push(LOG[k]); }
        }
        R.push("");
        if (dik.length === 0) {
            R.push("DİKKAT: yok — elle kontrol gerektiren bir durum bulunmadı.");
        } else {
            R.push("DİKKAT (" + dik.length + ")");
            for (k = 0; k < dik.length && k < 12; k++) { R.push("  \u2022 " + dik[k]); }
            if (dik.length > 12) { R.push("  \u2022 \u2026 ve " + (dik.length - 12) + " satır daha (CSV raporunda)."); }
        }
        R.push("");
        R.push("BİLGİ");
        for (k = 0; k < INFO.length; k++) { R.push("  \u2022 " + INFO[k]); }
        summaryHead = R.join("\n");

        doc.save();

    } catch (eMain) { hadError = eMain; }
    progressClose();

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
    alert("Kitapçık B v4.26 — Tamamlandı ✔\n\n" + summaryHead);

})();
