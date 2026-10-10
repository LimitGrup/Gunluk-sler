// HIZ testi: eski yönerge regex'i (v4.19-v4.20) bu tür sayı listelerinde üstel sürede
// çalışıp InDesign'da scripti kilitliyordu. Tüm script 1 saniyenin altında bitmeli.
var T0 = Date.now();
module.exports = function (a) {
    var FW = [40, 555];
    function list(n, sep) { var x = []; for (var i = 1; i <= n; i++) { x.push(i); } return x.join(sep); }
    var p1 = a.page("1"), p2 = a.page("2");
    a.t(p1, [60, 40, 110, 555], "Bu testte 6 soru vardır.\rCevaplarınızı, cevap kâğıdına işaretleyiniz.");
    var q = 0;
    [[p1, 120], [p1, 330], [p1, 540], [p2, 60], [p2, 270], [p2, 480]].forEach(function (s, k) {
        q++;
        var t = a.q(s[0], [s[1], FW[0], s[1] + 180, FW[1]], q,
            "Aşağıdaki sayılar verilmiştir: " + list(15 + (k % 2), " - ") + " olarak sıralanmıştır. Buna göre hangisi doğrudur?", "ABCD".charAt(k % 4));
        t._qid = "A" + q;
    });
    a.t(p2, [690, 40, 790, 555], "Tablo: " + list(16, " ,  ") + " değerleri.");
    return {
        name: "7._SINIF_HIZ-A.indd",
        key: "1-A 2-B 3-C 4-D 5-A 6-B 7-C 8-D 9-A 10-B 11-C 12-D 13-A 14-B 15-C 16-D 17-A 18-B 19-C 20-D",
        check: function () {
            var ms = Date.now() - T0;
            console.log("\n--- Denetim ---\n  " + (ms < 1000 ? "✔" : "✘") + " Toplam süre " + ms + " ms (sınır 1000 ms)");
            console.log(ms < 1000 ? "SONUÇ: TÜM DENETİMLER GEÇTİ" : "SONUÇ: HATA VAR");
        }
    };
};
