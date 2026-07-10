#target indesign

// Tüm işlemler boyunca QR sırasını aklında tutması için global değişkenler
var qrFiles = [];
var qrIndex = 0;
var placedCount = 0;

function main() {
    var hasBooks = app.books.length > 0;
    var hasDocs = app.documents.length > 0;

    if (!hasBooks && !hasDocs) {
        alert("Lütfen önce işlem yapmak istediğiniz bir Book (.indb) veya tekil InDesign (.indd) dökümanı açın.");
        return;
    }

    if (hasBooks && hasDocs) {
        var mode = askBookOrDoc();
        if (mode === "doc") {
            processSingleDoc(app.activeDocument);
        } else if (mode === "book") {
            processBook();
        }
        return;
    }

    if (hasBooks && !hasDocs) {
        processBook();
        return;
    }

    if (!hasBooks && hasDocs) {
        processSingleDoc(app.activeDocument);
        return;
    }
}

function getQRFolderFiles() {
    var folder = Folder.selectDialog("Lütfen yerleştirilecek QR kodlarının bulunduğu klasörü seçin:");
    if (folder === null) return null;

    var files = folder.getFiles(/\.(jpg|jpeg|png|eps|pdf|ai)$/i);
    files.sort();

    if (files.length === 0) {
        alert("Seçilen klasörde uygun bir görsel (JPG, PNG, PDF vb.) bulunamadı.");
        return null;
    }

    return files;
}

// Aynı satırda kabul edilecek dikey tolerans (puan). Çerçeveler tam
// aynı y'de değilse de "aynı sıra" sayılabilsin diye bir pay bırakır.
var ROW_TOLERANCE = 5;

// Sayfadaki (veya bir koleksiyondaki) "qr" katmanına ait çerçeveleri
// bulur ve görsel konumlarına göre (üstten alta, aynı satırda soldan
// sağa) sıraya dizer. pageItems/masterPageItems koleksiyonlarının
// dahili sırası (z-order / oluşturma sırası) görsel sırayla birebir
// örtüşmeyebilir; QR kodlarının doğru kutuya düşmesi için asıl esas
// alınması gereken geometrik konumdur.
function collectSortedQRFrames(myPage, targetLayer) {
    var pageItems = myPage.pageItems;
    var frames = [];

    for (var j = 0; j < pageItems.length; j++) {
        var item = pageItems[j];
        if (item.itemLayer == targetLayer) {
            frames.push(item);
        }
    }

    frames.sort(function (a, b) {
        var boundsA = a.geometricBounds; // [y1, x1, y2, x2]
        var boundsB = b.geometricBounds;

        if (Math.abs(boundsA[0] - boundsB[0]) > ROW_TOLERANCE) {
            return boundsA[0] - boundsB[0]; // farklı satır -> yukarıdan aşağı
        }
        return boundsA[1] - boundsB[1]; // aynı satır -> soldan sağa
    });

    return frames;
}

function placeQRsInDocument(myDoc) {
    var targetLayer = myDoc.layers.itemByName("qr");

    if (!targetLayer.isValid) {
        return true; // Bu dökümanda "qr" katmanı yoksa sessizce geç
    }

    // Güvenlik için eğer katman kilitliyse kilidini aç
    if (targetLayer.locked) {
        targetLayer.locked = false;
    }

    // 1. AŞAMA: Master Page (Kalıp Sayfa) izinlerini zorla aç
    // Belgedeki tüm Master Sayfaları gezip qr katmanındaki çerçevelerin kilidini kaldırır
    for (var m = 0; m < myDoc.masterSpreads.length; m++) {
        var ms = myDoc.masterSpreads[m];
        for (var i = 0; i < ms.pageItems.length; i++) {
            var mItem = ms.pageItems[i];
            if (mItem.itemLayer == targetLayer) {
                mItem.allowOverrides = true;
            }
        }
    }

    // 2. AŞAMA: Belgedeki sayfaları işle
    for (var p = 0; p < myDoc.pages.length; p++) {
        var myPage = myDoc.pages[p];

        // a) Bu sayfaya uygulanan ama henüz serbest kalmamış Master
        // çerçevelerini bul ve serbest bırak. Geriye doğru gezmek,
        // override edilen öğe koleksiyondan çıkarılsa bile (ki bazı
        // InDesign sürümlerinde masterPageItems anlık/yeniden
        // sorgulanan bir koleksiyon olabilir) öğe atlanmasını önler.
        var masterItems = myPage.masterPageItems;
        if (masterItems && masterItems.length > 0) {
            for (var mi = masterItems.length - 1; mi >= 0; mi--) {
                var masterItem = masterItems[mi];
                if (masterItem.itemLayer == targetLayer) {
                    try {
                        masterItem.override(myPage); // Sizin yerinize Cmd+Shift tıklaması (Override) yapar
                    } catch (e) {
                        // Çerçeve zaten serbestse veya başka bir sorun varsa atla
                    }
                }
            }
        }

        // b) Artık Master çerçeveler de normal sayfa çerçevesi oldu.
        // Şimdi bu sayfadaki qr çerçevelerini GÖRSEL KONUMLARINA göre
        // sıraya dizip QR yerleştirme işlemini yap. (Bkz: yukarıdaki
        // collectSortedQRFrames açıklaması — bu satır, "bir düzgün bir
        // kaymış" şeklindeki sıralama hatasının düzeltildiği yer.)
        var qrFramesOnPage = collectSortedQRFrames(myPage, targetLayer);

        for (var k = 0; k < qrFramesOnPage.length; k++) {
            var currentFrame = qrFramesOnPage[k];

            if (qrIndex < qrFiles.length) {
                // Eğer içinde daha önceden kalma bir görsel varsa sil
                if (currentFrame.graphics.length > 0) {
                    currentFrame.graphics[0].remove();
                }

                // Yeni QR'ı ekle
                currentFrame.place(File(qrFiles[qrIndex]));
                currentFrame.fit(FitOptions.PROPORTIONALLY);
                currentFrame.fit(FitOptions.CENTER_CONTENT);

                qrIndex++;
                placedCount++;
            } else {
                alert("Uyarı: Klasördeki QR kodları tükendi! Kalan çerçeveler boş bırakılıyor.");
                return false; // QR kalmadığı için diğer dokümanlara geçmesini engeller
            }
        }
    }

    return true;
}

function processSingleDoc(myDoc) {
    if (!myDoc.isValid) return;

    qrFiles = getQRFolderFiles();
    if (qrFiles === null) return;

    placeQRsInDocument(myDoc);
    myDoc.save();

    alert("İşlem tamamlandı!\nAktif Döküman: " + myDoc.name + "\nToplam " + placedCount + " adet QR görseli başarıyla yerleştirildi.");
}

function processBook() {
    var myBook = getTargetBook();
    if (myBook === null) return;

    qrFiles = getQRFolderFiles();
    if (qrFiles === null) return;

    var oldInteractionLevel = app.scriptPreferences.userInteractionLevel;
    app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;

    for (var i = 0; i < myBook.bookContents.length; i++) {
        var docPath = myBook.bookContents[i].fullName;
        var myDoc = app.open(File(docPath));

        var continueProcessing = placeQRsInDocument(myDoc);

        myDoc.close(SaveOptions.YES);

        if (!continueProcessing) {
            break;
        }
    }

    app.scriptPreferences.userInteractionLevel = oldInteractionLevel;
    alert("İşlem tamamlandı!\nSeçilen Book: " + myBook.name + "\nToplam " + placedCount + " adet QR görseli başarıyla yerleştirildi.");
}

function askBookOrDoc() {
    var win = new Window("dialog", "İşlem Kapsamı Seçimi");
    win.orientation = "column";
    win.alignChildren = ["left", "top"];

    win.add("statictext", undefined, "Sistemde hem açık Book dosyası hem de tekil döküman tespit edildi.\nHangi kapsamda işlem yapmak istersiniz?");

    var rActiveDoc = win.add("radiobutton", undefined, "Sadece şu an ön planda olan tek dökümanda işlem yap (" + app.activeDocument.name + ")");
    var rBook = win.add("radiobutton", undefined, "Açık olan Book dosyalarından biri üzerinde işlem yap");
    rActiveDoc.value = true;

    var groupButtons = win.add("group");
    groupButtons.alignment = ["center", "top"];
    var btnOk = groupButtons.add("button", undefined, "Tamam");
    var btnCancel = groupButtons.add("button", undefined, "İptal");

    var selection = null;
    btnOk.onClick = function() {
        if (rActiveDoc.value) selection = "doc";
        else selection = "book";
        win.close(1);
    }
    btnCancel.onClick = function() {
        win.close(0);
    }

    var res = win.show();
    if (res === 1) return selection;
    return null;
}

function getTargetBook() {
    if (app.books.length === 1) {
        return app.books.item(0);
    }

    var win = new Window("dialog", "Book Seçimi");
    win.orientation = "column";
    win.alignChildren = ["left", "top"];
    win.add("statictext", undefined, "Birden fazla Book açık.\nLütfen işlem yapılacak Book dosyasını seçin:");

    var bookNames = [];
    for (var i = 0; i < app.books.length; i++) {
        bookNames.push(app.books.item(i).name);
    }

    var dropDown = win.add("dropdownlist", undefined, bookNames);
    dropDown.selection = 0;

    var groupButtons = win.add("group");
    groupButtons.alignment = ["center", "top"];
    var btnOk = groupButtons.add("button", undefined, "Tamam");
    var btnCancel = groupButtons.add("button", undefined, "İptal");

    var selectedBook = null;
    btnOk.onClick = function() {
        selectedBook = app.books.item(dropDown.selection.index);
        win.close(1);
    }
    btnCancel.onClick = function() {
        win.close(0);
    }

    var result = win.show();
    if (result === 1) return selectedBook;
    return null;
}

main();
