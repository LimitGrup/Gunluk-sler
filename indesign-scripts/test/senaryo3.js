// Kenar durumlar: "6. ve 7. soruları" (numarayla başlayan yönerge), kendi görseli olan
// "Buna göre" sorusu (kilitlenmemeli), görselsiz "Buna göre" (kilitlenmeli), özel havuz.
module.exports = function (a) {
    var FW = [40, 555];
    function fw(pg, y1, y2, n, txt, ans, id) { var t = a.q(pg, [y1, FW[0], y2, FW[1]], n, txt, ans); t._qid = id; return t; }
    var p1 = a.page("1"), p2 = a.page("2"), p3 = a.page("3"), p4 = a.page("4");
    a.t(p1, [60, 40, 110, 555], "Bu testte 12 soru vardır.\rCevaplarınızı, cevap kâğıdına işaretleyiniz.");
    var q1 = fw(p1, 120, 300, 1, "￼\rBuna göre tablodaki değerlerden hangisi en büyüktür?", "A", "A1");
    q1.parentStory.pageItems = [{ geometricBounds: [130, 60, 220, 300] }];      // çapalı tablo görseli
    fw(p1, 320, 500, 2, "Hangisi bir doğal sayıdır?", "B", "A2");
    fw(p1, 520, 700, 3, "Hangisi asal sayıdır?", "C", "A3");
    fw(p2, 60, 240, 4, "Hangisi tek sayıdır?", "D", "A4");
    fw(p2, 260, 440, 5, "Buna göre Ali kaç yaşındadır?", "A", "A5");               // dışarıdaki bilgiye bağlı
    fw(p2, 460, 640, 8, "Hangisi çift sayıdır?", "B", "A8");
    a.t(p3, [60, 40, 90, 555], "6. ve 7. soruları aşağıdaki tabloya göre cevaplayınız.");
    a.t(p3, [95, 40, 250, 555], "Tablo: Bir okuldaki öğrenci sayıları sınıflara göre verilmiştir.");
    fw(p3, 260, 440, 6, "Tabloya göre en kalabalık sınıf hangisidir?", "C", "A6");
    fw(p3, 460, 640, 7, "Tablodaki öğrencilerin toplamı kaçtır?", "D", "A7");
    fw(p4, 60, 240, 9, "Hangisi 3'ün katıdır?", "A", "A9");
    fw(p4, 260, 440, 10, "Hangisi 5'in katıdır?", "B", "A10");
    fw(p4, 460, 640, 11, "Hangisi 7'nin katıdır?", "C", "A11");
    fw(p4, 660, 790, 12, "Hangisi 4'ün katıdır?", "D", "A12");
    return {
        name: "7._SINIF_MAT-A.indd",
        pools: "sayfa 4 soru 9-11",
        key: "1-A 2-B 3-C 4-D 5-A 6-C 7-D 8-B 9-A 10-B 11-C 12-D 13-A 14-B 15-C 16-D 17-A 18-B 19-C 20-D",
        check: function (ALL) {
            function where(id) { var t = ALL.filter(function (x) { return x._qid === id; })[0];
                                 return { page: t.pg.name, num: +/^(\d+)\./.exec(t.parentStory.paragraphs[0]._t)[1] }; }
            var ok = true;
            function expect(c, m) { console.log((c ? "  ✔ " : "  ✘ ") + m); if (!c) { ok = false; } }
            console.log("\n--- Denetim ---");
            var a1 = where("A1"), a5 = where("A5"), a6 = where("A6"), a7 = where("A7");
            expect(!(a1.page === "1" && a1.num === 1), "Kendi görseli olan 'Buna göre' sorusu kilitlenmedi, karıştı (A1→s." + a1.page + " no " + a1.num + ")");
            expect(a5.page === "2" && a5.num === 5, "Görselsiz 'Buna göre' sorusu yerinde kilitlendi (A5→s." + a5.page + " no " + a5.num + ")");
            expect(a6.page === "3" && a7.page === "3" && [6, 7].indexOf(a6.num) >= 0 && [6, 7].indexOf(a7.num) >= 0,
                   "'6. ve 7. soruları' grubu s.3'te kaldı (A6→" + a6.num + ", A7→" + a7.num + ")");
            var nums = ALL.filter(function (x) { return x._qid; }).map(function (x) { return +/^(\d+)\./.exec(x.parentStory.paragraphs[0]._t)[1]; }).sort(function (p, q) { return p - q; });
            expect(nums.join(",") === "1,2,3,4,5,6,7,8,9,10,11,12", "Numara dizisi eksiksiz ve tekrarsız: " + nums.join(","));
            var a12 = where("A12");
            expect(a12.num === 12 && a12.page === "4", "Havuz dışındaki S12 havuz sorularıyla karışmadı (A12→" + a12.num + ")");
            console.log(ok ? "SONUÇ: TÜM DENETİMLER GEÇTİ" : "SONUÇ: HATA VAR");
        }
    };
};
