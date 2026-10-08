// Ekran görüntülerindeki yapının sentetik kopyası (6. sınıf, karşılıklı sayfa).
// Test 1 (Türkçe) s.2-6: s.4'te "8 ve 9. soruları ... metne göre" + ortak metin + S8, S9.
// Test 2 (Din) s.7-9: s.7'de "1, 2 ve 3. soruları ... metne göre" + metin + S1 (FW), S2/S3 (sütun).
// s.9'da serbest (gruplanmamış) bir görsel S9'un içinde duruyor.
module.exports = function (a) {
    var FW = [40, 555], L = [40, 290], R = [305, 555];
    function fw(pg, y1, y2, n, txt, ans, id) { var t = a.q(pg, [y1, FW[0], y2, FW[1]], n, txt, ans); t._qid = id; return t; }
    function col(pg, x, y1, y2, n, txt, ans, id) { var t = a.q(pg, [y1, x[0], y2, x[1]], n, txt, ans); t._qid = id; return t; }
    a.page("1");                                   // kapak (sorusuz)
    var p2 = a.page("2"), p3 = a.page("3"), p4 = a.page("4"), p5 = a.page("5"), p6 = a.page("6");
    a.t(p2, [60, 40, 110, 555], "Bu testte 15 soru vardır.\rCevaplarınızı, cevap kâğıdına işaretleyiniz.");
    fw(p2, 120, 300, 1, "Aşağıdaki cümlelerin hangisinde yazım yanlışı yapılmıştır?", "A", "T1-A1");
    fw(p2, 320, 500, 2, "Hangi sözcük gerçek anlamıyla kullanılmıştır?", "B", "T1-A2");
    fw(p2, 520, 700, 3, "Aşağıdaki atasözlerinden hangisi farklıdır?", "C", "T1-A3");
    fw(p3, 60, 230, 4, "Hangisinde ünlü düşmesi vardır?", "D", "T1-A4");
    fw(p3, 250, 420, 5, "Noktalama işaretlerinden hangisi eksiktir?", "A", "T1-A5");
    fw(p3, 440, 610, 6, "Hangi cümle öznelden nesnele doğrudur?", "B", "T1-A6");
    fw(p3, 630, 790, 7, "Hangisinde abartma sanatı vardır?", "C", "T1-A7");
    a.t(p4, [60, 40, 90, 555], "8 ve 9. soruları aşağıdaki metne göre cevaplayınız.");
    a.t(p4, [95, 40, 330, 555], "Otların yeşil olması, denizin mavi olması, gökyüzünün bulutsuz olması, pekâlâ bir meseledir.");
    fw(p4, 340, 520, 8, "Yukarıdaki metni inceleyen bir öğrenci bu metinle ilgili defterine notlar almıştır.", "B", "T1-A8");
    fw(p4, 540, 800, 9, "Aşağıda, bu öyküden alınan iki cümle verilmiştir.", "A", "T1-A9");
    fw(p5, 60, 240, 10, "Hangisinde deyim yoktur?", "D", "T1-A10");
    fw(p5, 260, 440, 11, "Hangisi bir öneri cümlesidir?", "A", "T1-A11");
    fw(p5, 460, 640, 12, "Hangi sözcükte yapım eki vardır?", "B", "T1-A12");
    fw(p6, 60, 240, 13, "Evlerin çoğunun duvarları çatlamıştı. Bazı balkonlar zamana yenik düşerek eğilmişti.", "C", "T1-A13");
    fw(p6, 260, 440, 14, "Hangisinde koşul anlamı vardır?", "D", "T1-A14");
    fw(p6, 460, 640, 15, "Hangisinde neden-sonuç ilişkisi vardır?", "A", "T1-A15");
    var p7 = a.page("7"), p8 = a.page("8"), p9 = a.page("9");
    a.t(p7, [60, 40, 110, 555], "Bu testte 10 soru vardır.\rCevaplarınızı, cevap kâğıdına işaretleyiniz.");
    a.t(p7, [120, 40, 150, 555], "1, 2 ve 3. soruları aşağıdaki metne göre cevaplayınız.");
    a.t(p7, [155, 40, 420, 555], "Özlem, okul kütüphanesinin sessiz bir köşesinde dönem ödevi için kaynak taraması yapıyordu.");
    fw(p7, 430, 560, 1, "Buna göre aşağıdaki bilgilerden hangisi doğru değildir?", "C", "T2-A1");
    col(p7, L, 600, 780, 2, "Bu metinde peygamberlerle ilgili aşağıdaki konulardan hangisine değinilmemiştir?", "A", "T2-A2");
    col(p7, R, 600, 780, 3, "Bu metne göre peygamberlerin öncelikli görevi aşağıdakilerden hangisidir?", "B", "T2-A3");
    fw(p8, 60, 300, 4, "Hangisi ibadetlerin amaçlarından biri değildir?", "D", "T2-A4");
    fw(p8, 320, 560, 5, "Hangisi Hz. Muhammed'in özelliklerinden biridir?", "A", "T2-A5");
    fw(p8, 580, 790, 6, "Hangi davranış yardımlaşmaya örnektir?", "B", "T2-A6");
    fw(p9, 60, 190, 7, "İnsanlar, yalnızca akıl ve duyularıyla doğru ve yanlışı tam olarak ayırt edemeyebilir.", "C", "T2-A7");
    fw(p9, 210, 450, 8, "Hangisi zekâtın faydalarından biridir?", "D", "T2-A8");
    col(p9, L, 470, 700, 9, "Görseldeki durum hangi kavramla ilgilidir?", "A", "T2-A9");
    col(p9, R, 470, 640, 10, "Hangisi Kur'an'ın temel konularından biridir?", "B", "T2-A10");
    var img = a.rect(p9, [560, 60, 680, 270]); img._img = "G(S9'un görseli)";
    return {
        name: "6._SINIF_DENEME_1-A.indd",
        key: "1-A 2-B 3-C 4-D 5-A 6-B 7-C 8-B 9-A 10-D 11-A 12-B 13-C 14-D 15-A 1-C 2-A 3-B 4-D 5-A 6-B 7-C 8-D 9-A 10-B",
        check: function (ALL, pages) {
            function where(id) { var t = ALL.filter(function (x) { return x._qid === id; })[0];
                                 return { page: t.pg.name, num: +/^(\d+)\./.exec(t.parentStory.paragraphs[0]._t)[1], y: t.geometricBounds[0], x: t.geometricBounds[1] }; }
            var ok = true;
            function expect(cond, msg) { console.log((cond ? "  ✔ " : "  ✘ ") + msg); if (!cond) { ok = false; } }
            console.log("\n--- Denetim ---");
            var a8 = where("T1-A8"), a9 = where("T1-A9");
            expect(a8.page === "4" && a9.page === "4" && [8, 9].indexOf(a8.num) >= 0 && [8, 9].indexOf(a9.num) >= 0,
                   "Test 1: metne bağlı A8/A9 s.4'te ve 8-9 numaralarında kaldı (A8→s." + a8.page + " no " + a8.num + ", A9→s." + a9.page + " no " + a9.num + ")");
            var b1 = where("T2-A1"), b2 = where("T2-A2"), b3 = where("T2-A3");
            // v4.24: grup sayfasında ve 1-3 aralığında kalır; tam genişlik A1 sütunların altına geçebilir
            var g3 = [b1, b2, b3];
            expect(g3.every(function (z) { return z.page === "7" && z.num >= 1 && z.num <= 3; }) &&
                   b1.num !== b2.num && b2.num !== b3.num && b1.num !== b3.num,
                   "Test 2: metne bağlı 1-3 grubu s.7'de ve 1-3 numaralarında kaldı (A1→" + b1.num + ", A2→" + b2.num + ", A3→" + b3.num + ")");
            var t2 = ALL.filter(function (x) { return /^T2-A[123]$/.test(x._qid); });
            expect(t2.every(function (x) { return x.geometricBounds[0] >= 420; }),
                   "Test 2: grup soruları ortak metnin (y<420) altında");
            var a9q = ALL.filter(function (x) { return x._qid === "T2-A9"; })[0];
            var im = ALL.filter(function (x) { return x._img; })[0];
            var dy = im.geometricBounds[0] - a9q.geometricBounds[0], dx = im.geometricBounds[1] - a9q.geometricBounds[1];
            expect(im.pg === a9q.pg && Math.abs(dy - 90) < 0.01 && Math.abs(dx - 20) < 0.01,
                   "S9'un serbest görseli soruyla aynı sayfada ve aynı göreli konumda (dy=" + Math.round(dy) + ", dx=" + Math.round(dx) + ")");
            console.log(ok ? "SONUÇ: TÜM DENETİMLER GEÇTİ" : "SONUÇ: HATA VAR");
        }
    };
};
