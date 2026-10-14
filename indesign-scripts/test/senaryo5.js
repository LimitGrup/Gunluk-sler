// Sahada (8. sınıf Sayısal, v4.21) görülen hata: yeni testin sayfasında 2. sorunun çapalı
// görseli InDesign'da çerçevenin üstüne taşınca 2. soru 1. sorudan ÖNCE okunuyor, önceki teste
// sayılıp "komşu teste kaçan soru" diye yerinde kilitleniyordu. Test ayrımı okuma sırasından
// bağımsız olmalı: 2. soru Test 2'de kalmalı, uyarı çıkmamalı.
module.exports = function (a) {
    var L = [40, 290], R = [305, 555];
    function col(pg, x, y1, y2, n, txt, ans, id) { var t = a.q(pg, [y1, x[0], y2, x[1]], n, txt, ans); t._qid = id; return t; }
    var p1 = a.page("1"), p2 = a.page("2"), p3 = a.page("3"), p4 = a.page("4");
    a.t(p1, [60, 40, 110, 555], "Bu testte 4 soru vardır.\rCevaplarınızı, cevap kâğıdına işaretleyiniz.");
    col(p1, L, 130, 400, 1, "Hangisi bir doğal sayıdır?", "A", "T1-1"); col(p1, R, 130, 380, 2, "Hangisi asal sayıdır?", "B", "T1-2");
    col(p2, L, 60, 330, 3, "Hangisi tek sayıdır?", "C", "T1-3"); col(p2, R, 60, 340, 4, "Hangisi çift sayıdır?", "D", "T1-4");
    a.t(p3, [60, 40, 110, 555], "Bu testte 4 soru vardır.\rCevaplarınızı, cevap kâğıdına işaretleyiniz.");
    col(p3, L, 130, 400, 1, "Bu deneyde bağımsız değişken hangisidir?", "A", "T2-1");
    var s2 = col(p3, R, 130, 390, 2, "Aşağıdaki görselde gölge boyları verilmiştir. Hangisi doğrudur?", "B", "T2-2");
    s2.parentStory.pageItems = [{ id: 99901, geometricBounds: [50, 320, 200, 540] }];   // InDesign'ın bildirdiği konum
    col(p4, L, 60, 330, 3, "Hangisi bir besin zinciridir?", "C", "T2-3"); col(p4, R, 60, 340, 4, "Hangisi bir enerji türüdür?", "D", "T2-4");
    return {
        name: "8._SINIF_SIRA-A.indd",
        key: "1-A 2-B 3-C 4-D 1-A 2-B 3-C 4-D 1-A 2-B 3-C 4-D 1-A 2-B 3-C 4-D 1-A 2-B 3-C 4-D",
        check: function (ALL) {
            function where(id) { var t = ALL.filter(function (x) { return x._qid === id; })[0];
                                 return { page: t.pg.name, num: +/^(\d+)\./.exec(t.parentStory.paragraphs[0]._t)[1] }; }
            var w = where("T2-2");
            // yanlışlıkla kilitlenirse A'daki yerinde (s.3, no 2) kalır; doğru çalışmada S1 ile yer değiştirir
            var ok = (w.page === "3" || w.page === "4") && w.num >= 1 && w.num <= 4 && !(w.page === "3" && w.num === 2);
            var nums = ALL.filter(function (x) { return x._qid && /^T2/.test(x._qid); }).map(function (x) { return +/^(\d+)\./.exec(x.parentStory.paragraphs[0]._t)[1]; }).sort();
            var ok2 = nums.join(",") === "1,2,3,4";
            console.log("\n--- Denetim ---\n  " + (ok ? "✔" : "✘") + " Test 2'nin 2. sorusu Test 2'de kaldı ve kilitlenmeden karıştı (s." + w.page + " no " + w.num + ")");
            console.log("  " + (ok2 ? "✔" : "✘") + " Test 2 numaraları eksiksiz: " + nums.join(","));
            console.log(ok && ok2 ? "SONUÇ: TÜM DENETİMLER GEÇTİ" : "SONUÇ: HATA VAR");
        }
    };
};
