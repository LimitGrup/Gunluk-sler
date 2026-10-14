// render.js çıktısındaki sayfaları PNG'ye çevirir: node shot.js belge.html çıktı_klasörü [sayfa,...]
var pw = require("playwright"), path = require("path"), fs = require("fs");
(async function () {
    var html = path.resolve(process.argv[2]), out = path.resolve(process.argv[3]);
    var want = process.argv[4] ? process.argv[4].split(",") : null;
    if (!fs.existsSync(out)) { fs.mkdirSync(out, { recursive: true }); }
    var b = await pw.chromium.launch(), pg = await b.newPage({ viewport: { width: 900, height: 700 } });
    await pg.goto("file://" + html);
    var ids = await pg.$$eval("div.p", function (ds) { return ds.map(function (d) { return d.id; }); });
    for (var i = 0; i < ids.length; i++) {
        if (want && want.indexOf(ids[i].substr(1)) < 0) { continue; }
        var el = await pg.$("#" + ids[i].replace(/\./g, "\\."));
        await el.screenshot({ path: out + "/" + path.basename(html, ".html") + "_s" + ids[i].substr(1) + ".png" });
    }
    await b.close();
})();
