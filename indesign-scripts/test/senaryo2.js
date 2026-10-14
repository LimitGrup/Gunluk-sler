// AYT tipi: tek sayfalı yayılım, ders bölgeleri (giriş metninde aralıklar), iki sütun.
// YONERGE=1 ise s.4'te Tarih bölgesi (7-12) içinde "9 ve 10. soruları ... metne göre" yönergesi var.
module.exports = function (a) {
    var L = [40, 290], R = [305, 555];
    function col(pg, x, y1, y2, n, txt, ans, id) { var t = a.q(pg, [y1, x[0], y2, x[1]], n, txt, ans); t._qid = id; return t; }
    a.page("1");
    var p2 = a.page("2"), p3 = a.page("3"), p4 = a.page("4");
    a.t(p2, [60, 40, 110, 555], "Bu testte sırasıyla, Türk Dili ve Edebiyatı (1-6), Tarih-1 (7-12) alanlarına ait toplam 12 soru vardır.");
    col(p2, L, 120, 400, 1, "Bu dizelerde hangi söz sanatı vardır?", "A", "A1");
    col(p2, L, 420, 760, 2, "Hangisi Tanzimat döneminin özelliğidir?", "B", "A2");
    col(p2, R, 120, 330, 3, "Hangi eser halk edebiyatına aittir?", "C", "A3");
    col(p2, R, 350, 760, 4, "Hangisinde ünsüz benzeşmesi vardır?", "D", "A4");
    col(p3, L, 60, 380, 5, "Divan şiirinde hangi nazım biçimi kullanılır?", "A", "A5");
    col(p3, L, 400, 780, 6, "Hangisi Servetifünun sanatçısıdır?", "B", "A6");
    col(p3, R, 60, 400, 7, "Osmanlı Devleti'nin kuruluş dönemi ile ilgili hangisi doğrudur?", "C", "A7");
    col(p3, R, 420, 780, 8, "Hangisi Malazgirt Savaşı'nın sonuçlarındandır?", "D", "A8");
    if (process.env.YONERGE === "1") { a.t(p4, [60, 40, 90, 290], "9 ve 10. soruları aşağıdaki metne göre cevaplayınız."); }
    a.t(p4, [95, 40, 330, 290], "Selçuklu Devleti'nde ikta sistemi, toprakların askerî ve idari amaçlarla dağıtılmasıdır.");
    col(p4, L, 340, 560, 9, "Bu metne göre ikta sisteminin amacı hangisidir?", "A", "A9");
    col(p4, L, 580, 790, 10, "Metinde sözü edilen sistemin sonuçlarından biri hangisidir?", "B", "A10");
    col(p4, R, 60, 400, 11, "Hangisi Türkiye Selçuklularına aittir?", "C", "A11");
    col(p4, R, 420, 780, 12, "Hangisi Haçlı Seferleri'nin sonucudur?", "D", "A12");
    return {
        name: "AYT-DENEME-1-A.indd", facing: false,
        key: "1-A 2-B 3-C 4-D 5-A 6-B 7-C 8-D 9-A 10-B 11-C 12-D 13-A 14-B 15-C 16-D 17-A 18-B 19-C 20-D",
        check: function (ALL) {
            if (process.env.YONERGE !== "1") { return; }
            function where(id) { var t = ALL.filter(function (x) { return x._qid === id; })[0];
                                 return { page: t.pg.name, num: +/^(\d+)\./.exec(t.parentStory.paragraphs[0]._t)[1] }; }
            var w9 = where("A9"), w10 = where("A10");
            var ok = w9.page === "4" && w10.page === "4" && [9, 10].indexOf(w9.num) >= 0 && [9, 10].indexOf(w10.num) >= 0;
            console.log("\n--- Denetim ---\n  " + (ok ? "✔" : "✘") + " Tarih bölgesi içindeki 9-10 ortak metin grubu yerinde (A9→" + w9.num + ", A10→" + w10.num + ")");
        }
    };
};
