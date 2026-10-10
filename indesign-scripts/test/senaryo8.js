// v4.25: (1) BRANŞ SINIRI — numaralar sıfırlanmadan süren üç branş (1-3, 4-6, 7-9), her biri
//        "Bu testte 3 soru vardır." girişiyle başlar. Boyu aynı tam genişlik S1 ve S4 farklı
//        branşta olduğu için takas OLMAMALI. (2) SÜTUN TAKASI — s.3'te sol sütunda tek uzun soru,
//        sağda iki soru: başka eş yok; sol ve sağ sütun yer değiştirmeli (dikey konumlar korunur).
module.exports = function (a) {
    var L = [40, 290], R = [305, 555], FW = [40, 555];
    function q(pg, x, y1, y2, n, txt, ans, id) { var t = a.q(pg, [y1, x[0], y2, x[1]], n, txt, ans); t._qid = id; return t; }
    var p1 = a.page("1"), p2 = a.page("2"), p3 = a.page("3");
    a.t(p1, [30, 40, 50, 555], "SÖZEL BÖLÜM - TÜRKÇE");
    a.t(p1, [60, 40, 100, 555], "Bu testte 3 soru vardır.");
    q(p1, FW, 110, 260, 1, "Hangisi bir sıfattır?", "A", "A1");
    q(p1, L, 300, 560, 2, "Hangisi bir zamirdir?", "B", "A2");
    q(p1, R, 300, 560, 3, "Hangisi bir edattır?", "C", "A3");
    a.t(p2, [30, 40, 50, 555], "SÖZEL BÖLÜM - SOSYAL BİLGİLER");
    a.t(p2, [60, 40, 100, 555], "Bu testte 3 soru vardır.");
    q(p2, FW, 110, 260, 4, "Hangisi bir kıtadır?", "D", "A4");
    q(p2, L, 300, 560, 5, "Hangisi bir okyanustur?", "A", "A5");
    q(p2, R, 300, 560, 6, "Hangisi bir başkenttir?", "B", "A6");
    a.t(p3, [30, 40, 50, 555], "SAYISAL BÖLÜM - MATEMATİK");
    a.t(p3, [60, 40, 90, 555], "Bu testte 3 soru vardır.");
    q(p3, L, 100, 700, 7, "Hangisi bir asal sayıdır?", "C", "A7");
    q(p3, R, 100, 380, 8, "Hangisi bir çift sayıdır?", "D", "A8");
    q(p3, R, 400, 680, 9, "Hangisi bir tek sayıdır?", "A", "A9");
    return {
        name: "TYT-DENEME-8-A.indd", facing: false,
        key: "1-A 2-B 3-C 4-D 5-A 6-B 7-C 8-D 9-A 10-B 11-C 12-D 13-A 14-B 15-C 16-D 17-A 18-B 19-C 20-D",
        check: function (ALL) {
            var ok = true;
            function expect(c, m) { console.log((c ? "  ✔ " : "  ✘ ") + m); if (!c) { ok = false; } }
            var qs = ALL.filter(function (x) { return x._qid; }).map(function (t) {
                return { id: t._qid, a: +t._qid.substr(1), page: t.pg.name, gb: t.geometricBounds, num: +/^(\d+)\./.exec(t.parentStory.paragraphs[0]._t)[1] };
            });
            console.log("\n--- Denetim ---");
            var br = function (n) { return Math.floor((n - 1) / 3); };
            var cross = qs.filter(function (x) { return br(x.a) !== br(x.num) || String(br(x.a) + 1) !== x.page; });
            expect(cross.length === 0, "Her soru kendi branşının sayfasında ve numara aralığında" + (cross.length ? " — aşan: " + cross.map(function (x) { return x.id + "→s." + x.page + " no " + x.num; }).join(", ") : ""));
            var a7 = qs.filter(function (x) { return x.id === "A7"; })[0], a8 = qs.filter(function (x) { return x.id === "A8"; })[0], a9 = qs.filter(function (x) { return x.id === "A9"; })[0];
            expect(a7.gb[1] > 297 && a8.gb[1] < 297 && a9.gb[1] < 297 && Math.abs(a8.gb[0] - 100) < 1 && Math.abs(a9.gb[0] - 400) < 1 && Math.abs(a7.gb[0] - 100) < 1,
                   "s.3 sütun takası: A7 sağa, A8/A9 sola geçti, dikey konumlar korundu (A7 y" + Math.round(a7.gb[0]) + " x" + Math.round(a7.gb[1]) + ", A8 y" + Math.round(a8.gb[0]) + ", A9 y" + Math.round(a9.gb[0]) + ")");
            var nums = qs.map(function (x) { return x.num; }).sort(function (x, y) { return x - y; });
            expect(nums.join(",") === "1,2,3,4,5,6,7,8,9", "Numara dizisi eksiksiz ve tekrarsız: " + nums.join(","));
            var stay = qs.filter(function (x) { return x.a === x.num; });
            expect(stay.length === 0, "Numarası aynı kalan soru yok" + (stay.length ? " — kalan: " + stay.map(function (x) { return x.id; }).join(", ") : ""));
            console.log(ok ? "SONUÇ: TÜM DENETİMLER GEÇTİ" : "SONUÇ: HATA VAR");
        }
    };
};
