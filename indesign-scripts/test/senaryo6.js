// v4.23: (1) ALT SINIR — s.2'de altbilgi bandına (kenar boşluğu y=802'nin altına) konmuş
//        "TEST BİTTİ." çerçevesi soruların inebileceği sınırı aşağı çekmemeli.
//        (2) SATIR HİZASI — s.1'de A'da aynı satırdan başlayan sol/sağ sorular B'de de
//        aynı satırdan başlamalı. (3) Ortak metinli 1-2 grubu s.1'de, kendi slotlarında.
module.exports = function (a) {
    var L = [40, 290], R = [305, 555];
    function col(pg, x, y1, y2, n, txt, ans, id) { var t = a.q(pg, [y1, x[0], y2, x[1]], n, txt, ans); t._qid = id; return t; }
    var p1 = a.page("1"), p2 = a.page("2");
    a.t(p1, [60, 40, 100, 555], "Bu testte 7 soru vardır.");
    a.t(p1, [110, 40, 135, 290], "1 ve 2. soruları aşağıdaki metne göre cevaplayınız.");
    a.t(p1, [140, 40, 190, 290], "Metin: Bir kasabada yaşayan çocuklar her yaz kütüphanede buluşurdu.");
    col(p1, L, 200, 330, 1, "Bu metne göre çocuklar nerede buluşurdu?", "A", "A1");
    col(p1, L, 400, 560, 2, "Metinde sözü edilen mevsim hangisidir?", "B", "A2");
    col(p1, R, 200, 330, 3, "Hangisi bir doğal sayıdır?", "C", "A3");
    col(p1, R, 400, 700, 4, "Hangisi asal sayıdır?", "D", "A4");
    col(p2, L, 60, 200, 5, "Hangisi tek sayıdır?", "A", "A5");
    col(p2, L, 310, 500, 6, "Hangisi çift sayıdır?", "B", "A6");
    col(p2, R, 60, 560, 7, "Hangisi 3'ün katıdır?", "C", "A7");
    a.t(p2, [810, 305, 830, 555], "TEST BİTTİ.");
    return {
        name: "TYT-DENEME-6-A.indd", facing: false,
        key: "1-A 2-B 3-C 4-D 5-A 6-B 7-C 8-D 9-A 10-B 11-C 12-D 13-A 14-B 15-C 16-D 17-A 18-B 19-C 20-D",
        check: function (ALL) {
            var ok = true;
            function expect(c, m) { console.log((c ? "  ✔ " : "  ✘ ") + m); if (!c) { ok = false; } }
            var qs = ALL.filter(function (x) { return x._qid; }).map(function (t) {
                return { id: t._qid, page: t.pg.name, gb: t.geometricBounds, num: +/^(\d+)\./.exec(t.parentStory.paragraphs[0]._t)[1] };
            });
            console.log("\n--- Denetim ---");
            var low = qs.filter(function (q) { return q.gb[2] > 802.5; });
            expect(low.length === 0, "Hiçbir soru kenar boşluğunun (y=802) altına, altbilgi bandına inmedi" +
                   (low.length ? " — inen: " + low.map(function (q) { return q.id + " alt=" + Math.round(q.gb[2]); }).join(", ") : ""));
            function colQs(pg, c) { return qs.filter(function (q) { return q.page === pg && ((q.gb[1] + q.gb[3]) / 2 > 297) === (c === 1); })
                                            .sort(function (x, y) { return x.gb[0] - y.gb[0]; }); }
            var l1 = colQs("1", 0), r1 = colQs("1", 1);
            var aligned = l1.length === 2 && r1.length === 2 && Math.abs(l1[0].gb[0] - r1[0].gb[0]) <= 1 && Math.abs(l1[1].gb[0] - r1[1].gb[0]) <= 1;
            expect(aligned, "s.1'de A'daki iki satır hizası korundu (sol " + l1.map(function (q) { return Math.round(q.gb[0]); }).join("/") +
                   ", sağ " + r1.map(function (q) { return Math.round(q.gb[0]); }).join("/") + ")");
            var g = qs.filter(function (q) { return q.id === "A1" || q.id === "A2"; });
            expect(g.every(function (q) { return q.page === "1" && (q.num === 1 || q.num === 2) && q.gb[1] < 297 && (Math.abs(q.gb[0] - 200) < 1 || Math.abs(q.gb[0] - 400) < 1); }),
                   "Ortak metinli 1-2 grubu s.1'de kendi slotlarında (" + g.map(function (q) { return q.id + "→" + q.num; }).join(", ") + ")");
            var nums = qs.map(function (q) { return q.num; }).sort(function (x, y) { return x - y; });
            expect(nums.join(",") === "1,2,3,4,5,6,7", "Numara dizisi eksiksiz ve tekrarsız: " + nums.join(","));
            var stay = qs.filter(function (q) { return "A" + q.num === q.id && q.page === (q.num <= 4 ? "1" : "2"); });
            expect(stay.length === 0, "Yerinde kalan soru yok" + (stay.length ? " — kalan: " + stay.map(function (q) { return q.id; }).join(", ") : ""));
            console.log(ok ? "SONUÇ: TÜM DENETİMLER GEÇTİ" : "SONUÇ: HATA VAR");
        }
    };
};
