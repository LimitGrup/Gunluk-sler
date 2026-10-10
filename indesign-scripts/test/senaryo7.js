// v4.24: (1) İNGİLİZCE YÖNERGE — "Answer the questions 8-10 according to the text below."
//        grubu s.3'te ve 8-10 numaralarında kalmalı (boyu uyan başka sayfa sorularıyla takas olmamalı).
//        (2) BLOK SIRASI — testteki tek tam genişlik soru (S1) sütunların altına geçerek yer değiştirmeli.
module.exports = function (a) {
    var L = [40, 290], R = [305, 555], FW = [40, 555];
    function q(pg, x, y1, y2, n, txt, ans, id) { var t = a.q(pg, [y1, x[0], y2, x[1]], n, txt, ans); t._qid = id; return t; }
    var p1 = a.page("1"), p2 = a.page("2"), p3 = a.page("3");
    a.t(p1, [60, 40, 100, 555], "Bu testte 10 soru vardır.");
    q(p1, FW, 110, 250, 1, "Look at the picture. Which of the following is TRUE?", "A", "A1");
    q(p1, L, 290, 450, 2, "Which word completes the sentence?", "B", "A2");
    q(p1, R, 290, 430, 3, "Which one is a fruit?", "C", "A3");
    q(p2, L, 60, 210, 4, "Which one is a sport?", "D", "A4");
    q(p2, R, 60, 210, 5, "Which one is a city?", "A", "A5");
    q(p2, L, 260, 410, 6, "Which one is a colour?", "B", "A6");
    q(p2, R, 260, 410, 7, "Which one is an animal?", "C", "A7");
    a.t(p3, [60, 40, 85, 555], "Answer the questions 8-10 according to the text below.");
    a.t(p3, [90, 40, 300, 555], "Tom lives in a small town. Every weekend he visits his grandparents and helps them in the garden.");
    q(p3, L, 310, 460, 8, "According to the text, where does Tom live?", "D", "A8");
    q(p3, R, 310, 460, 9, "According to the text, what does Tom do at weekends?", "A", "A9");
    q(p3, L, 490, 640, 10, "Which of the following is NOT mentioned in the text?", "B", "A10");
    return {
        name: "TYT-DENEME-7-A.indd", facing: false,
        key: "1-A 2-B 3-C 4-D 5-A 6-B 7-C 8-D 9-A 10-B 11-C 12-D 13-A 14-B 15-C 16-D 17-A 18-B 19-C 20-D",
        check: function (ALL) {
            var ok = true;
            function expect(c, m) { console.log((c ? "  ✔ " : "  ✘ ") + m); if (!c) { ok = false; } }
            var qs = ALL.filter(function (x) { return x._qid; }).map(function (t) {
                return { id: t._qid, page: t.pg.name, gb: t.geometricBounds, num: +/^(\d+)\./.exec(t.parentStory.paragraphs[0]._t)[1] };
            });
            function w(id) { return qs.filter(function (x) { return x.id === id; })[0]; }
            console.log("\n--- Denetim ---");
            var g = [w("A8"), w("A9"), w("A10")];
            expect(g.every(function (x) { return x.page === "3" && x.num >= 8 && x.num <= 10 && x.gb[0] >= 300; }),
                   "İngilizce yönergeli 8-10 grubu s.3'te, metnin altında ve 8-10 numaralarında (" + g.map(function (x) { return x.id + "→s." + x.page + " no " + x.num; }).join(", ") + ")");
            var a1 = w("A1");
            expect(a1.page === "1" && a1.num !== 1, "Tek tam genişlik soru S1 yer değiştirdi (A1→s." + a1.page + " no " + a1.num + ", y" + Math.round(a1.gb[0]) + ")");
            var nums = qs.map(function (x) { return x.num; }).sort(function (x, y) { return x - y; });
            expect(nums.join(",") === "1,2,3,4,5,6,7,8,9,10", "Numara dizisi eksiksiz ve tekrarsız: " + nums.join(","));
            var stay = qs.filter(function (x) { return "A" + x.num === x.id; });
            expect(stay.length === 0, "Yerinde kalan soru yok" + (stay.length ? " — kalan: " + stay.map(function (x) { return x.id; }).join(", ") : ""));
            var low = qs.filter(function (x) { return x.gb[2] > 802.5; });
            expect(low.length === 0, "Hiçbir soru alt kenar boşluğunun altına inmedi");
            console.log(ok ? "SONUÇ: TÜM DENETİMLER GEÇTİ" : "SONUÇ: HATA VAR");
        }
    };
};
