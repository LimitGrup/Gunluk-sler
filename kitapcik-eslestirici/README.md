# Kitapçık Eşleştirici (v2.41)

macOS uygulaması (`Kitapcik Eslestirici.app`). İki iş yapar:

| Düğme | Ne yapar | Çıktı |
|---|---|---|
| **EŞLEŞTİR** | A kitapçığındaki her sorunun B'de kaçıncı soru olduğunu bulur, kazanım tablosunu doldurur. | `kazanim_tablosu.xlsx` |
| **A–B KONTROL** *(yeni)* | B kitapçığını A'ya göre denetler: A'daki her soru B'de var mı, aynı mı, numaralar ve metne bağlı gruplar düzgün mü? KDS seçilince B'siz tek kitapçığı kendi içinde denetler. | `kitapcik_kontrol_raporu.pdf` (tek PDF: özet + sorunlu soruların A/B görüntüleri) |

## KDS: B kitapçığı olmayan denemenin kontrolü; rapor ilk sayfası taşmaz (v2.41)

- **KDS (tek kitapçık):** Sınav türünde yeni seçenek **"KDS (tek kitapçık)"**. Lise ve ortaokul
  için aynıdır.
  - Seçilince yalnız kitapçık PDF'i istenir ("Kitapçık PDF"). B kutusu "KDS'de yok" olur,
    düğmenin adı **KDS KONTROL** olur.
  - Dosyayı pencereye sürüklemek de yeter.
  - KONTROL kitapçığı kendi içinde denetler:
    - soru numaraları (mükerrer, atlanmış, sırasız, yanlış numara);
    - bantta yazan soru sayısı ile basılı soru sayısı;
    - açık kalmış cevap ve soru kodu (renkli, siyaha çevrilmiş, eğri);
    - şık takımı;
    - metne bağlı grup başlığı numaraları;
    - iki kez basılmış soru.
  - Yapı bantlardan okunur ("Bu testte sırasıyla, Matematik (1-15), Fizik (16-21) … toplam
    30 soru vardır"). Bant birkaç satıra bölünmüş olsa da dersler doğru çıkar; raporda soru
    dersiyle gösterilir ("Fizik · 18").
  - Numara hatası iki testi birleştirmiş görünüyorsa (Sosyal 1 yerine "21.") yapı yine
    bantlardan kurulur. Bilerek bozulmuş 7. sınıf B tek başına verildiğinde, A–B kontrolündeki
    6 HATA'nın aynısı çıktı.
  - Karşılaştırılacak ikinci kitapçık olmadığı için metin, şekil ve cevap farkı aranmaz; rapor
    bunu ilk sayfasında yazar.
  - Rapor `<deneme adı>_kontrol_raporu.pdf` olarak yazılır. Aynı klasördeki sayısal ve sözel
    raporları birbirinin üzerine yazılmaz.
  - EŞLEŞTİR, KDS'de çalışmaz; bilgi verir.
  - A–B KONTROL ve diğer sınav türleri değişmedi.
- **Rapor ilk sayfası taşmaz:** Listede her sorunun açıklaması tek satıra sıkıştırılıp "…" ile
  kesiliyor, sağ kenara dayanıyordu. Artık kenar boşlukları içinde alt satırlara bölünür ve tam
  okunur. Özet ve dosya adı satırları da bölünür. Kartlardaki açıklama kutusu da uzun metni
  kesmez, gerektiği kadar uzar.
- `testler/kds_sina.py`: Kitapçığın kopyalarını bilerek bozar, KDS kipinde denetler. Sekiz
  senaryo var: mükerrer, ileri numara, yer değiştirmiş, numara silinmiş, soru silinmiş, bant
  yanlış, açık cevap, açık kod. 4 lise KDS denemesinde ve 2 ortaokul kitapçığında hepsi doğru
  bulundu. 24 temiz gerçek kitapçıkta KDS kipi 0 HATA verdi.

## Windows sürümü (v2.40)

Uygulama Windows'ta da çalışır. Mac ve Windows aynı Python dosyasını kullanır
(`Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py`): EŞLEŞTİR ve
KONTROL ikisinde de aynıdır. Yalnız şu küçük kısımlar sisteme göre seçilir:

| | Mac | Windows |
|---|---|---|
| Başlatma | `Kitapcik Eslestirici.app` | `Kitapcik Eslestirici.exe` |
| Biten raporu açma | `open` | sistemin varsayılan programı |
| Günlük dosyası | `~/Library/Logs/KitapcikEslestirici.log` | `%LOCALAPPDATA%\KitapcikEslestirici\KitapcikEslestirici.log` |
| Başlatma hatası penceresi | macOS iletişim kutusu | Windows ileti kutusu |
| Rapor alanı yazı tipi | Menlo | Consolas |

Mac'te davranış değişmedi.

- **Kurulum:** Windows paketi bir klasördür. İçinde `Kitapcik Eslestirici.exe`, `_internal` ve
  `Okubeni.txt` vardır. Python ya da kütüphane kurmak gerekmez, hepsi paketin içindedir.
  - Klasör kalıcı bir yere konur ve `.exe`'ye çift tıklanır.
  - İlk açılışta Windows "bilgisayarınızı korudu" diyebilir; uygulama imzalı değildir.
    "Ek bilgi" → "Yine de çalıştır" denir.
- **Derleme:** `.github/workflows/windows-exe.yml`. `kitapcik-eslestirici/` altında bir
  değişiklik gönderildiğinde GitHub'ın Windows makinesi sırayla şunları yapar:
  1. Motor testlerini Windows'ta çalıştırır (`windows/windows_sina.py`: KONTROL, EŞLEŞTİR,
     cevap, tire, kesir, düzen).
  2. Uygulamayı betik olarak açıp sınar.
  3. `.exe`'yi PyInstaller ile derler.
  4. `.exe`'yi açıp KONTROL, EŞLEŞTİR ve pencereyi sınar. Bu, `KITAPCIK_PAKET_SINA` ortam
     değişkeniyle çalışan deneme kipidir; normal kullanımda devreye girmez.

  Paket, çalışmanın "Artifacts" bölümünden indirilir.
  Kütüphane sürümleri Mac/Linux'ta sınananlarla aynıdır.

## KONTROL tek PDF verir; sayfa süsü şekil sayılmaz (v2.39)

- **Tek çıktı:** A–B KONTROL artık yalnız `kitapcik_kontrol_raporu.pdf` yazar:
  - İlk sayfada özet ve tıklanır sorun listesi var.
  - Sonraki sayfalarda her sorunun A/B görüntüsü var.
  - Sorun yoksa tek sayfa yeşil "SORUN BULUNMADI" yazar.

  Excel raporu ve A ile B için ayrı ayrı işaretli PDF'ler (`…_kontrol.pdf`) yazılmaz. Kayıt yeri
  yine başlarken sorulur (Evet = PDF'lerin klasörü, Hayır = konum seç). Biten işte "Rapor (PDF)
  şimdi açılsın mı?" diye sorulur. EŞLEŞTİR'in çıktısı ve akışı değişmedi.
- **Sayfa süsü yanlış "şekil eksik/fazla" vermez:** 8. sınıf final (sözel) çiftinde 10 HATA'nın
  hepsi aynı yanlış alarmdı:
  - Her sütunun altında, son sorunun hemen altında mor noktalı bir süs çizgisi var.
  - A ile B'de sorular yer değiştirince süs başka sorunun altına düşüyordu.
  - Program bunu "A'da 1, B'de 0 şekil parçası" diye okuyordu.

  Artık şekil sayılmayanlar:
  - Kitapçığın birçok sayfasında (en az 3 sayfa ve sayfaların %30'u) aynı yerde duran çizim ve
    resimler (çerçeve, süs, logo).
  - Sorunun son satırının tamamen altında kalan ince şerit.

  Sorunun içindeki şekiller ve şıkların resimleri eskisi gibi denetlenir.
- `testler/sus_sina.py` yeni test. A ve B'ye aynı süsü çizer, süssüz kopyaya göre yeni sorun
  çıkmamalı:
  - sütun sonu süsü: her sütunun son satırının altında;
  - sabit süs: her sayfada aynı yerde.

  Eski sürüm (v2.38) süslü 8. sınıf sayısal çiftinde 16 yanlış şekil satırı verdi: 11'i sütun
  sonu süsünden, 5'i sabit süsten. v2.39, 5 gerçek çiftin hepsinde 0 yeni sorun verdi.
- Diğer testler:
  - 17 gerçek çiftte KONTROL bulguları v2.38 ile aynı.
  - 15 gerçek çiftte EŞLEŞTİR tablosu v2.30 ile aynı.
  - Numara senaryoları 5 çiftte, baskı kopyası 7 çiftte tamam. Bunun içinde gerçekten silinmiş
    şekil her çiftte yine "şekil eksik" diye yakalanıyor.

## Bilerek bozulmuş gerçek kitapçıkta net rapor (v2.38)

7. sınıf Limit denemesinin B'si bilerek bozuldu, rapor v2.36'da gerçek hataları buluyordu ama
yanında yanıltıcı satırlar da yazıyordu. Üç neden düzeltildi:

- **Testin yalnız ilk sorusu yanlış numaralı (Sosyal 1 yerine "21.").** Motor Sosyal 1'i
  sayfadaki "1. Örnek: …" satırına bağlamıştı. Bu satır soru numarası değil ve okuma sırasına da
  uymuyordu; o sayfanın düzenini bozuyordu: tam genişlik bir soru ("SOSYAL MEDYA") ikiye bölündü,
  "A-5 B'de bulunamadı / B-8'in karşılığı yok / metin farklı / fazla şekil" gibi satırlar çıktı,
  "21." Türkçe'nin fazla sorusu sayıldı ve bant denetimi de yanıldı. Artık böyle bir çapa
  atıldığında sayfanın okuma sırası yeniden kurulur, testin baştaki eksik numarası yeniden
  aranır. Rapor tek satır yazar: "Numara yanlış: bu testin 1. sorusu '21.' diye numaralanmış."
- **Aynı satırdaki şıkların taban farkı.** Şıklar aynı satırda yüzde birkaç puan farkla
  durunca satır aralığı neredeyse 0 ölçülüyordu. Bu yüzden şıkların altındaki tablo satırları
  sorudan kopuyor, "metin farklı + fazla şekil" yazılıyordu (Fen 14). 2 pt'den küçük farklar
  artık satır aralığı sayılmaz.
- **Siyah basılmış soru kodu.** Soru kodu (ör. `56LMT7D1T1S17`) rengi siyaha çevrilerek açık
  kalmışsa "Metin farklı" deniyordu. Artık şöyle yazılır: "Soru kodu açık: sayfa 5, soru 16 —
  '56LMT7D1T1S17' basılı kalmış (SİYAH basılmış — …)". Kod biçimi dardır: iki rakam, harfler,
  sonda rakam. Gerçek kitapçıklarda siyah basılmış böyle bir metin yoktu; yanlış alarm çıkmaz.

O çiftte rapor şimdi yalnız bilerek yapılan hataları gösterir:

- Türkçe 3. sorunun yerinde '7.' yazıyor.
- Sosyal 1. soru '21.' diye numaralanmış.
- 16. soruda siyah 'A' ve siyah kod açık kalmış.
- 20. soruda renkli 'B' ve kod açık kalmış.

Bunların yanında tek bir sarı not var: test yapısı B'nin numaralarından okunamadı (bu numara
hatalarından).

Testler:

- 17 gerçek çiftte KONTROL raporu ve EŞLEŞTİR tablosu değişmedi.
- `numara_sina.py`'ye "ilk soru devam" senaryosu eklendi: Sosyal 1 yerine "21.". 5 çiftte tek
  satır HATA verdi, tüm senaryolar geçti.
- `baski_kopya_sina.py`'ye "siyah kod" senaryosu eklendi. Kodlu 3 çiftte (AYT, TYT, 7. sınıf
  sayısal) yalnız "Soru kodu açık" çıktı. 7 çiftin hepsi tamam.

## Bantta yazan soru sayısı (v2.37)

Her testin başındaki bant okunur: "Bu testte 20 soru vardır." ya da "… alanlarına ait toplam 25
soru vardır." (birkaç satıra bölünmüş olabilir). Bu sayı testte basılı soru sayısıyla, A ve B'de
ayrı ayrı karşılaştırılır. Fark varsa tek satır HATA verilir:

- "Bantta bu test için 20 soru yazıyor ama testte 19 soru var: 1 soru eksik."
- "Bantta bu test için 19 soru yazıyor ama testte 20 soru var: bant yanlış ya da 1 soru fazla."

Bir soru silinip sonrakiler yeniden numaralanmışsa (1–19) testin sonundaki "20. soru bulunamadı"
satırı ayrıca yazılmaz. Hangi sorunun eksik olduğunu "A-x sorusu B kitapçığında bulunamadı"
satırı gösterir. Önceden bant yanlışsa (19 yazıp 20 soru basılmışsa) hiçbir şey çıkmıyordu.
Temiz gerçek çiftlerde bant okuması her testte basılı soru sayısıyla birebir tuttu (6 çift,
A ve B).

## Yeni deneme için TEMİZLE (v2.35)

- **TEMİZLE düğmesi:** Uygulamayı kapatıp açmadan yeni deneme yapılabilir. Düğme dosya
  kutularını, çıktı yolunu ve rapor alanını boşaltır; sınav türü olduğu gibi kalır. İş sürerken
  çalışmaz.
- **Sürükle-bırak:** Birlikte bırakılan iki PDF eskilerin yerine geçer: ilki A, ikincisi B olur.
  Önceden A doluysa ikisi de B'ye yazılıyordu.
- **Çıktı yolu:** Elle seçilmemişse her yeni A kitapçığıyla o kitapçığın klasörüne güncellenir.
  Önceden rapor eski denemenin klasörüne yazılıyordu.

## Sade rapor satırları (v2.36)

- Sayfa kısaltılmaz: "s.7" yerine "sayfa 7" yazılır. Excel'de, ekranda ve sorun kartlarında
  aynıdır.
- Açık cevap tek satırdır: "Cevap açık: sayfa 7, soru 5 — 'C' harfi basılı kalmış". Rengi ya da
  stili değişmişse kısa not parantezde yazılır: "(SİYAH basılmış — rengi elle değiştirilmiş ya da
  yanlış stil verilmiş olabilir)".
- Soru kodu için: "Soru kodu açık: sayfa 7, soru 5 — '…' basılı kalmış".
- Eğri ya da resim olan iz için: "Cevap açık olabilir: sayfa 7, soru 5 — …".
- Elle bakılacaklar "Elle bakın: sayfa 7, soru 5 — …" diye başlar.
- B'de yalnız numara yanlışsa (v2.34) rapor "A'daki soru B'de yok" demez, tek satır yazar:
  "Soru numarası hatalı: 12. sorunun yerinde '14.' yazıyor".
- Soru gerçekten yoksa (yazısı ve şekliyle silinmiş) rapor yine "A-x sorusu B kitapçığında
  bulunamadı" ve "N. soru bulunamadı" der. Metne bağlı grubun içindeki soru için de aynıdır;
  grup başlığının altındaki soruların uymadığı ayrıca yazılır.
- Grubun içinde yalnız numara yanlışsa tek satır ve grup başlığı uyarısı çıkar. Örneğin 13 tam
  genişlik, altında 14 ile 15 yan yana duran sayfa düzeninde de yan hata çıkmaz.
- Otomatik yapıda B'de numara hatası varken "test yapısı farklı" kırmızı HATA olmaz. Bunun
  yerine şu sarı not çıkar: "büyük olasılıkla yukarıdaki numara hatalarından". Numaralar
  temizken gerçek bir yapı farkı yine HATA'dır.
- `testler/numara_sina.py` artık 10 senaryo içerir; ikisi metne bağlı grup içindir (grup içi
  yanlış numara, grup içi silinmiş soru). 5 gerçek çiftte 42/42 geçti; grup senaryoları
  yalnız 3+ sorulu grubu olan çiftte çalışır.

## Tek cevap motoru (v2.30)

EŞLEŞTİR'in cevap sütunu ile A–B KONTROL'ün "açık kalan cevap" denetimi artık **aynı motoru**
kullanır:

1. **Sorular sayfa düzeninden ayrılır** (A–B KONTROL'ün motoru): tam genişlik, iki sütun ya da
   ikisi karışık sayfa; sütun ya da sayfa değiştiren sorular.
2. **Cevap, sorunun oluğundaki renkli harftir:** numaranın altı ya da şıkların solundaki boşluk.
   Bir harfin olukta sayılması için yanındaki metin (soru kökü ya da şıklar) harfin sağından
   başlamalı, aynı sütunda harfin solundan başlayan metin olmamalıdır. Bu ölçü her harfin kendi
   yerinde alınır; bu yüzden:
   - şık dizilişi fark etmez: alt alta, yan yana, 3+2 (A B C / D E), 2+2+1 (A B / C D / E),
     4 şıklı 2+2;
   - şıklar sonraki sütuna ya da sayfaya taşsa da cevap şıkların yanında bulunur;
   - şeklin içindeki renkli etiketler (kırmızı "A", "B") cevap sayılmaz.
3. **Kitapçığın cevap rengi** (çoğunlukla magenta) kendiliğinden öğrenilir.
4. **Motor kendini denetler.** Cevaplı kitapçıkta her soru için:
   - cevap işareti yoksa,
   - birden fazla işaret varsa,
   - harf beklenen yerde değilse,
   - harf sorunun şıklarında yoksa (4 şıklı soruda "E" gibi)

   Kontrol sayfasına sayfasıyla birlikte "CEVAP KONTROL ET" yazılır. Yanlış bir harfi sessizce
   yazmak yerine görünür uyarı verir. A ile B'nin cevabı farklıysa "CEVAP UYUŞMAZLIĞI" uyarısı
   ayrıca vardır.
5. **Baskı (cevapsız) kitapçıkta cevap üretilmez.** Önceden 8. sınıf sayısal baskıda Matematik
   A-7'nin şeklindeki kırmızı etiketten "B" cevabı okunuyordu.

**Pembe Kod'dan alınan denetimler (v2.31–v2.32).** A–B KONTROL'ün açık cevap taraması Pembe
Kod (Cevap Kalesi) uygulamasının kurallarını da kapsar:

- **Renkten ve stilden bağımsız cevap harfi:** Cevap yerinde tek başına duran harf açık kalan
  cevap sayılır. Harf "C", "C." ya da "C)" biçiminde olabilir. Rengi siyaha, griye ya da başka
  bir renge çevrilmiş, yazı tipi ya da boyu değiştirilmiş olsa da yakalanır. Bunun için harf soru
  numarasıyla sol hizada olmalı (−6…+14 pt). Pembe Kod'un ölçümüne göre 175 gerçek cevap harfinin
  hepsi numarayla tam hizadadır. Raporda rengi açıkça yazılır: "magenta", "kırmızı", "SİYAH
  basılmış", "gri basılmış", "cevap rengi dışında bir renk" ya da "nokta/parantezli biçimde".
  Rengi ya da stili değişmiş harflerin yanına "elle değiştirilmiş olabilir" diye eklenir. Bu harf
  soru metninden ve şık sayımından çıkarılır. Böylece aynı sorun bir kez daha "metin farklı"
  ya da "ikinci şık takımı" diye yazılmaz. EŞLEŞTİR de cevaplı kitapçıkta böyle bir harfi
  kullanır, ama "cevap biçiminde değil" diye uyarır.
- **Beyaz (kâğıt rengi) harf** baskıda görünmez. Açık cevap sayılmaz, "metin farklı" da
  yazılmaz.
- **Cevap renginde kalan başka yazı (v2.32):** Soru içinde tam magenta (#EC008C) yazılmış her
  türlü metin raporlanır: kelime, sayı, etkinlik cevabı. Bu sarı UYARI'dır ("elle bakın").
  Pembe Kod tam kırmızıyı da arar; bu uygulama aramaz, çünkü gerçek baskı PDF'lerinde tam kırmızı
  içerik var: 6 çiftte "Ekvator", "y = g(x)", X/Y/Z etiketleri, konuşma balonu. Tam magenta ise
  baskı PDF'lerinde soru içinde hiç geçmiyor. Yalnız simge karakterleri var, onlar sayılmaz.
- **Piksel katmanı:** Her sorunun numara hizasındaki kök–şık arası şeridi görüntü olarak taranır.
  Önce metin katmanındaki glifler (numara, kök, şık) görüntüden çıkarılır. Satır kutuları yüksek
  olsa bile numaranın hemen altındaki iz kaybolmaz. Pembe Kod'un sabit "numara + 16 pt" sınırı
  bu durumda izi kaçırıyordu. Geriye kalan, harf boyutunda ve tek başına duran iz bildirilir:
  eğriye çevrilmiş ya da resme gömülü cevap harfi. Cevap rengindeyse HATA, değilse "elle bakın"
  uyarısı olur. Sağında, üstünde ya da altında mürekkep süren izler (şerit kenarına dayanmış
  şekil, tablo, çizgi) ve numara hizasından başlayan çerçeveler sayılmaz.
- **Ölçü:** Renkli cevapta oluk kuralı v2.30 ile aynıdır. Renksiz harfte ölçü daha sıkıdır:
  harfin sağ kenarından önce başlayan satır varsa harf cevap sayılmaz, çünkü bu girintiye dayalı
  bir tablo harfidir.

Bu kurallar `testler/duzen_sina.py` ile sınanır. Bu betik, gerçek denemelerde görülen bütün
durumları içeren A/B kitapçıkları üretir: yukarıdaki şık dizilişleri, iki sütunlu ve tam genişlik
testler, 5 ve 4 şıklı testler, şekilde kırmızı harf etiketleri, cevabın yanında renkli soru kodu,
şıkları sonraki sütuna ya da sayfaya taşan sorular, cevabın numaranın altında ya da A şıkkı
hizasında durması. EŞLEŞTİR'in cevap harfi ve B numarası ile A–B KONTROL'ün açık cevap
denetimi (temiz baskı, bilerek açık bırakılmış renkli, siyah ve eğri cevap) her durumda gerçek
değerle karşılaştırılır.

`testler/baski_kopya_sina.py` aynı denetimi gerçek bir cevaplı çiftte yapar. Renkli cevapları
silerek A ve B'nin baskı kopyasını üretir. Ardından B'den üç kopya daha çıkarır:

- **karışık kopya:** bir sorunun cevabı siyah metin, başka bir sorununki eğri olarak bırakılır;
- **şekilsiz kopya:** tek şekilli bir sorunun şekli ve çok şekilli bir sorunun bir şekli silinir
  (resim ya da çizim silinir, yazısı kalır);
- **stil kopyası:** 21 soruda cevap farklı biçimde bırakılır:
  - renk: magenta, kırmızı, mavi, camgöbeği, yeşil, gri, siyah, lacivert;
  - biçim: "C)", "C.";
  - yazı tipi ve boy: italik, Times, 7 pt, 13 pt;
  - konum: 8 pt sağa kaymış;
  - metin olmayan: magenta ve siyah eğri;
  - magenta sayı "12";
  - beyaz harf.

Beklenenler:

- temiz kopyada hiç açık cevap bildirilmez;
- karışık kopyada tam o iki soru HATA olur;
- şekilsiz kopyada tam o sorular "şekil/resim eksik" HATA'sı olur;
- stil kopyasında her biri beklenen önemle bildirilir: siyah eğri ve magenta sayı UYARI, beyaz
  harf hiç bildirilmez (basılmaz), geri kalanlar HATA; başka hiçbir yerde yeni sorun çıkmaz.

Elimizdeki yedi gerçek cevaplı çiftte sonuç:

| Çift | Temiz baskı | Siyah cevap | Eğri cevap | Silinen şekil |
|---|---|---|---|---|
| 7. sınıf MOBESE sayısal | 0 sorun | MATEMATİK 14 ✓ | FEN 7 ✓ | MAT 18 (1/1) ✓, MAT 10 (1/3) ✓ |
| 8. sınıf MOBESE sayısal | 0 sorun | MATEMATİK 14 ✓ | FEN 7 ✓ | MAT 17 (1/2) ✓ |
| 7. sınıf Limit 1 | 0 sorun | DİN KÜLTÜRÜ 1 ✓ | MATEMATİK 11 ✓ | MAT 7 (1/1) ✓, MAT 16 (1/3) ✓ |
| 8. sınıf Limit sayısal 1 | 0 sorun | MATEMATİK 14 ✓ | FEN 7 ✓ | MAT 18 (1/1) ✓, FEN 4 (1/3) ✓ |
| 7. sınıf Limit sözel 1 | 0 sorun | TÜRKÇE 17 ✓ | DİN KÜLTÜRÜ 4 ✓ | DİN 6 (1/1) ✓, İNG 6 (1/2) ✓ |
| AYT LEK 1 | 0 sorun | Coğrafya-2 16 ✓ | Matematik 25 ✓ | Mat 38 (1/1) ✓, Fizik 10 (1/4) ✓ |
| Finale TYT 1 | yalnız çiftteki gerçek metin farkı (Türkçe A-11/B-10) | Tarih 2 ✓ | Temel Matematik 19 ✓ | TM 32 (1/1) ✓, TM 24 (1/2) ✓ |

Stil kopyasında 7 çiftin hepsinde 21/21 doğru çıktı (147 durum).

Ayrıca her çiftte üç ayrı soruda şekil tek tek silinerek denendi. 21 durumun 21'i de doğru soruda
HATA verdi. Mürekkep farkı tek şekli silinen soruda %100, çok şekilliden biri silinende %14–66
çıktı.

## EŞLEŞTİR'deki düzeltmeler (v2.21, v2.27–v2.29)

EŞLEŞTİR'in eşleştirme mantığı aynen duruyor; üstüne iki düzeltme eklendi:

- **Ders adları:** Lise/Ortaokul (otomatik yapı) seçeneğinde test ve ders adı artık testin ilk
  sayfasındaki başlıktan okunuyor ("SÖZEL BÖLÜM - TÜRKÇE" → TÜRKÇE, "TÜRKÇE TESTİ" → TÜRKÇE).
  Önceden başlık satır sırasında geride kaldığında ya da önceki testin "… TESTİ BİTTİ" yazısı
  okunduğunda ad kayıyordu (ör. Türkçe soruları "Bölüm 1", İnkılap soruları "TÜRKÇE"). TYT/AYT'de
  sabit adlar kullanıldığı için değişiklik yok.
- **İçerik doğrulaması:** EŞLEŞTİR bittikten sonra her eşleşme A–B KONTROL'ün içerik
  karşılaştırmasıyla doğrulanır. Yalnızca kesin yanlış eşler düzeltilir: A sorusunun metni B'deki
  başka bir soruyla birebir (≥ %98) aynıyken EŞLEŞTİR'in seçtiği sorunun metni belirgin farklıysa
  (< %90). Her düzeltme Kontrol sayfasına ve günlüğe "DÜZELTİLDİ: … A-9 → B-4 (ilk eşleştirme B-3
  demişti …)" diye yazılır. Doğruluğu kanıtlanan eşlerin yersiz "DÜŞÜK BENZERLİK" uyarısı kalkar.
  Doğrulama bir nedenle yapılamazsa EŞLEŞTİR sonucu aynen kalır.
- **Cevap harfi (v2.27):** Cevap önce eskisi gibi soru bölümünde aranır; bulunduğu her durumda
  sonuç aynıdır. Bulunamazsa yedek olarak konuma bakılır: aynı sayfada, soru numarasının sol
  hizasında, numaranın altında ve bir sonraki sorudan önce duran renkli A–E harfi. Tam genişlik
  sayfalarda (ör. 8. sınıf MOBESE sayısal) numara satırı sağ yarıya düşünce numaranın altındaki
  cevap harfi okunmuyordu: A'da 36/40, B'de 39/40 → şimdi 40/40 ve 40/40, eşleşen 40 çiftin
  hepsinde A ile B'nin cevabı aynı.
- **Cevap harfi konumdan (v2.29):** Soru numarasının hizasında (sol boşlukta, numaranın altında,
  bir sonraki sorudan önce) renkli A–E harfi varsa cevap odur; eski sıra kuralı yalnızca böyle bir
  harf yoksa kullanılır. Eski kural sorunun içindeki ilk renkli harfi alıyordu: 8. sınıf Limit
  sayısal Matematik A-7'nin şeklindeki kırmızı "B" etiketi cevap sanılıyordu (doğrusu pembe "A";
  B kitapçığında aynı şekil olduğu için A–B cevap kıyası da yakalayamıyordu). Elimizdeki 5 cevaplı
  gerçek çiftte (376 soru, iki kitapçıkta 752 cevap) iki kural yalnızca 4 cevapta ayrışıyor ve 4'ünde de
  konumdan okunan harf doğru.
- **Başka sayfadan okunan cevap (v2.28):** Aynı nedenle soru bölümü bir sonraki sayfaya taşınca
  eski kural o sayfadaki başka bir sorunun cevabını alabiliyordu (7. sınıf MOBESE sayısal Fen
  A-16: C okunuyordu, doğrusu B). Cevap soru numarasından başka bir sayfadan okunduysa ve
  numaranın kendi sayfasında hizasında renkli harf varsa o kullanılır. Örnek ve gerçek
  kitapçıklardaki 536 soruda iki kural yalnızca bu soruda ayrışıyor. Cevaplar eşleştirmede de
  ipucu olduğu için düzeltme, iki yanlış eşi de kendiliğinden düzeltti.

Gerçek kitapçıklarda sonuç:

| Çift | EŞLEŞTİR v2.18 | v2.21 |
|---|---|---|
| 8. sınıf Sözel 1A ↔ 1B (50 soru) | 48/50 doğru (İngilizce 9–10 yer değiştirmiş) | 50/50 |
| 8. sınıf Sayısal 1A ↔ 1B (40 soru) | 38/40 doğru (Matematik 17–18 yer değiştirmiş) | 40/40 |
| TYT Deneme 1 A ↔ B (125 soru) | 125/125 | 125/125 |
| AYT Deneme 1 A ↔ B (166 soru) | 166/166 | 166/166 |
| 10. sınıf Deneme 2 A ↔ B (100 soru) | 100/100 | 100/100 |
| 11. sınıf Deneme 2 A ↔ B (100 soru) | 98/100 | 100/100 |
| 5. sınıf Deneme 1 A ↔ B (75 soru) | 69/75 | 75/75 |
| 7. sınıf Deneme 1 A ↔ B (90 soru) | 85/90 (ders adı "Bölüm 1") | 90/90 |
| 8. sınıf MOBESE Sayısal 1 A ↔ B (40 soru, cevaplı) | 38/40, cevap A 36/40 · B 39/40 | 40/40, cevap 40/40 · 40/40 |
| 7. sınıf MOBESE Sayısal 1 A ↔ B (40 soru, cevaplı) | 34/40, cevap A 36/40 (1 yanlış) · B 36/40 | 40/40, cevap 40/40 · 40/40 |
| AYT LEK 1. Deneme A ↔ B (166 soru, cevaplı) | 166/166, cevap 166/166 · 166/166 | 166/166, cevap 166/166 · 166/166 |
| 7. sınıf Limit Deneme 1 A ↔ B (90 soru, cevaplı) | 90/90, cevap 85/90 · 86/90; Din soruları "SOSYAL BİLGİLER", Türkçe "Bölüm 1" | 90/90, cevap 90/90 · 90/90, 6 branş doğru adla |
| 8. sınıf Limit Sayısal 1 A ↔ B (40 soru, cevaplı) | 38/40, cevap 39/40 (1 yanlış) · 38/40; Matematik "Bölüm 1" | 40/40, cevap 40/40 · 40/40 |
| 7. sınıf Limit Sözel 1 A ↔ B (50 soru, cevaplı) | 48/50, cevap 47/50 · 48/50; Din soruları "SOSYAL BİLGİLER" | 50/50, cevap 50/50 · 50/50, 4 branş doğru adla |
| Finale Doğru Kurs TYT Deneme 1 A ↔ B (125 soru, cevaplı) | 125/125, cevap 125/125 · 125/125 | 125/125, cevap 125/125 · 125/125 |

TYT ya da AYT seçili olup dosyalar o düzene uymuyorsa (ör. 10. sınıf kitapçığı varsayılan TYT
seçiliyken çalıştırılırsa) önce diğer sınav türü denenir; o da uymazsa yapı kitapçığın kendisinden
çıkarılır (Lise/Ortaokul seçeneği gibi) ve günlükte "DİKKAT" ile belirtilir.

Örnek kitapçıklarda ana tablo (B numaraları) v2.18 ile aynıdır (`testler/eslestir_sina.py`).
Değişen tek yer, doğrulanan eşlerin Kontrol sayfasındaki benzerlik yüzdesidir.

## A–B KONTROL: sorunsuz baskı kontrolü

Cevap kapalı **baskı PDF'leri** için tasarlandı; cevap açık PDF'lerle de çalışır. Cevap açık
PDF'lerde ek olarak A ve B'nin cevap harfleri de kıyaslanır.

Her kitapçık önce **kendi içinde**, sonra **A ile B karşılıklı** denetlenir.

1. **Açık kalan cevap:** Baskıda görünmemesi gereken renkli cevap harfi ya da soru kodu arar.
   Harf soru numarasının altında, şıkların solundaki boşlukta ya da magenta renkte olabilir.
   Şekil içindeki renkli etiketler (haritadaki kırmızı A, B, C gibi) cevap sayılmaz. Kitapçığın
   tamamı cevaplıysa tek bir "bu kitapçıkta cevaplar açık" uyarısı verilir.
2. **Numaralar branş branş düzgün mü (A ve B ayrı ayrı):** Her testte 1'den N'e eksiksiz gidiyor
   mu? Atlanan numara, mükerrer numara ("8." iki kez) ya da sırasız numaralı şıklı soru varsa
   yerini ve büyük olasılıkla doğru numarayı yazar. Bir sorunun içinde ikinci şık takımı varsa
   (numarası düşmüş soru) onu da bildirir. v2.33'te eklenenler:
   - **Okuma sırası:** Her numara var olsa bile sayfada sıra bozuksa HATA verilir ("12. soru 11.
     sorudan önce basılmış"). Bu, yer değiştirmiş numarayı ya da yanlış yere konmuş soruyu yakalar.
   - **Kaymış numaralar:** Bir noktadan sonra numaralar bir fazla basılmışsa bu açıkça yazılır: "Bu
     test 20 soruluk ve 11. soru yok: 11. sorudan itibaren numaralar bir fazla basılmış".
   - **1'den başlamayan test:** Bir testin numaraları önceki testten devam ediyorsa (Sosyal 1–10
     yerine 21–30) tek bir HATA verilir: "bu testin 1–10. soruları '21.'–'30.' diye numaralanmış".
     Önceden motor bu durumda sonraki bütün testleri kaybediyordu ve rapora 100'e yakın yan hata
     düşüyordu. Şimdi testler kendi yerlerinde yeniden bulunur. Numaraları doğru olan testler
     sessizce yerine oturur.
   - **Yanlış numaralı soru tek satırda (v2.34):** Bir soruya yanlış numara yazılmışsa (11'den
     sonra gelen soruya "13.", ya da "10.") ve aynı numara testte iki kez geçiyorsa, motor
     sıraya uyanı gerçek soru sayar. Rapor tek satır yazar: "Soru numarası hatalı: 12.
     sorunun yerinde '13.' yazıyor (13 numarası bu testte iki kez geçiyor)". Yanlış numaralı
     sorunun başı da sayfa düzeninde soru başlangıcı sayılır. Böylece A'daki soru için "B'de
     yok", "metin farklı" ya da "fazla şekil" gibi yan hatalar çıkmaz.
   - **Grafik/tablo etiketi numara sanılmaz:** Sütun kenarında durmayan ve sıraya uymayan bir
     "numara" soru başlangıcı sayılmaz. Örneğin bir grafikteki "11. ay" etiketi 11. soru sayılmaz.
     Gerçek soru numarası yanlış yazılmışsa rapor yalnız asıl hatayı gösterir.

   `testler/numara_sina.py` B'nin numaralarını 8 biçimde bozar (v2.34'te "ileri numara" eklendi:
   11'den sonra gelen soruya "13."). Mükerrer, ileri numara ve yer değiştirmiş numarada rapora
   tek satır düşmelidir. v2.34'te aynı 5 çiftte 8 senaryonun hepsi geçti (40/40). Aşağıdaki
   ilk ölçüm v2.33'te, 7 senaryoyla yapıldı. Elimizdeki 5 gerçek çiftin baskı
   kopyasında (7. sınıf Limit 1, 7. sınıf Limit sözel 1, 8. sınıf MOBESE sayısal, AYT LEK 1,
   Finale TYT 1) 7 senaryonun hepsi doğru numarada HATA verdi (35/35). Senaryolar:
   - mükerrer numara;
   - olmayan numara;
   - yer değiştirmiş iki numara;
   - bir noktadan sonra kaymış numaralar;
   - 1'den başlamayan test;
   - silinmiş numara;
   - noktası unutulmuş numara.

   1'den başlamayan testte sonuç tek bir HATA ve "test yapısı farklı" oldu. Önceden bu durumda
   76–97 satır çıkıyordu.
3. **Metne bağlı grup başlıkları (A ve B ayrı ayrı):** "14 ve 15. soruları…", "1-4. soruları…",
   "12. ve 13. soruları…" gibi başlıklardaki numaralar altındaki sorularla aynı mı?
4. **A'daki her soru B'de var mı?** Soru metni ve şıklarıyla birlikte aranır. LGS düzeninde
   sorunun kendi metni sorunun parçası sayılır. Eşleştirme her testin içinde, dersler arasında
   yapılır; soru başka dersin aralığına kaymışsa yakalanır.
5. **Eşleşen her çift için:**
   - Metin ve şıklar birebir aynı mı? Fark kelime düzeyinde gösterilir. Baskıda görünmeyen
     farklar sayılmaz: boşluklar, satır sonunda bölünen kelimeler, tirenin kodu ("-", yumuşak
     tire, Unicode tire), "ü"nün tek harf ya da "u"+"¨" yazılması, ﬁ gibi bitişik harfler.
     Görünen noktalama farkı (ör. virgül yalnızca A'da) sarı UYARI, kelime/harf farkı kırmızı
     HATA olur.
   - Ders aynı mı?
   - Cevap harfi aynı mı? (cevap açık PDF'lerde)
   - Şekil ve resimler aynı mı? Sorudaki resim ve çizimler "şekil kutuları"na toplanır, her şekil
     kendi kutusunda görüntü olarak kıyaslanır. Satır aralığı ya da konum değişse de yalnızca
     gerçekten değişen şekil yakalanır. Değişen şekil HATA olur. Soru B'ye alınırken şekli ya da
     resmi unutulmuşsa da HATA olur (v2.32): "B'de şekil/resim eksik: A'da 1, B'de 0 şekil
     parçası". Aynı kural metne bağlı grupların ortak şekillerine ve B'ye fazladan konan şekle de
     uygulanır. Parça sayısı farklıyken şekil mürekkebi yalnızca %6–10 farklıysa sarı UYARI
     verilir, elle bakılması gerekir.
6. **Metne bağlı gruplar A ↔ B:** A'daki grubun soruları B'de yine yan yana ve aynı başlık altında
   mı? Metin aynı mı? B'de bir grubun metni başka grubun sorularının üstüne düşmüşse açıkça yazar:
   "B'de metin ile altındaki sorular uyumsuz: B 5-8. soruların üstündeki metin, A'da 15-17.
   soruların metni".
7. **Aynı soru iki kez basılmış mı?**
8. **Otomatik yapıda (Lise / Ortaokul):** A ve B'nin test yapısı (test adları, soru sayıları)
   aynı mı?

Sayfa düzeni soru numaralarına göre çözülür. Her numaradan bir bölge başlar: soru tam
genişlikse sayfa boyu, değilse kendi sütunu. Böylece aynı sayfada tam genişlik soru (yan yana
A B C D şıklarıyla) ve iki sütun bir arada olsa da her satır kendi sorusunda kalır. Numaranın
sağında ve onun hizasında duran satır, üst üste kesir (315/2) ya da büyük karakter yüzünden
numaranın biraz üstünden başlasa da o sorunun ilk satırı sayılır.

### Rapor

A–B KONTROL başlarken raporun nereye kaydedileceği sorulur. "Evet" derseniz rapor PDF'lerin
bulunduğu klasöre yazılır; soruda klasör adı gösterilir. "Hayır" derseniz kayıt penceresi
açılır, yer ve ad seçilir. Kayıt penceresinde vazgeçilirse kontrol başlamaz.

Rapor tek PDF'tir (`kitapcik_kontrol_raporu.pdf`, v2.39):

- **İlk sayfa:** Özet var: A ve B'de yerinde duran soru sayısı, eşleşen soru, metin birebir,
  metne bağlı gruplar, şekiller, açık cevap. Altında **"Bakılacak sorular"** listesi var:
  - Her satırda sıra numarası, testi, soru numarası (A-7 / B-2), **A ve B sayfası** ve ne
    bulunduğu yazar.
  - Hatalar kırmızı, uyarılar turuncu yazılır.
  - Liste önce hataları, sonra uyarıları kitapçıktaki sırayla verir.
  - Satıra tıklayınca o sorunun sayfası açılır.
  - Sorun yoksa başlık yeşil "SORUN BULUNMADI" olur.
- **Sonraki sayfalar:** Her sorun için bir sayfa. Üstte ne bulunduğu ve sayfası, altta sorunun
  **A ve B kitapçığındaki görüntüsü yan yana**:
  - farklı kelimeler sarıyla boyanır;
  - farklı şekil kırmızı çerçeveyle, en farklı küçük bölgesi ayrıca işaretlenir;
  - açık kalan cevap harfi çerçevelenir;
  - bulunamayan sorunun yerine önceki ve sonraki soru gösterilir.

  Böylece her uyarı, PDF'leri açıp aramadan birkaç saniyede doğrulanır.

Uygulamada kontrol bitince "Rapor (PDF) şimdi açılsın mı?" diye sorulur. Günlükte de her sorun
sayfasıyla yazılır. v2.38'e kadar ayrıca Excel raporu ve A ile B için işaretli PDF kopyaları
yazılıyordu; artık yazılmaz.

### Farklı şablonlar

Uygulama belirli bir kitapçığa göre ayarlanmadı; genel kurallarla çalışır:
- Soru numaraları sütun kenarına hizalı "12." biçiminde aranır, sıraları test test izlenir.
- Testler numaranın 1'e dönmesinden, adları sayfa üstündeki başlıktan ("… TESTİ",
  "… BÖLÜM - …"), ders dağılımı "Bu testte sırasıyla, Tarih (1-10), …" yönergesinden okunur.
- Sayfa düzeni (tek sütun, iki sütun, ikisinin karışımı) her sayfada soru numaralarına göre
  ayrıca çözülür.
- Sayfa üst/alt bilgileri sabit metinden değil, sayfalarda aynı yerde tekrar etmelerinden tanınır.

10. ve 11. sınıf kitapçıkları bu kurallarla ilk denemede tanındı; yalnızca iki genel kusur
düzeltildi (alt satıra kayan şık parçasının soru numarası sanılması, yakın iki tablonun şekil
kutusunda birleşmesi). 5. ve 7. sınıfta da 75/75 ve 90/90 soru ilk denemede bulundu. Düzeltilen
genel kusurlar: renkli içerik metninin ("81 ilde") soru kodu sanılması; kırpılmış vektör
resimlerin görünmeyen parçalarının şekil sayılması (artık her çizim parçası PDF'teki kırpma
alanıyla kesiliyor); ortalı sayfa numarasının ("1" ile "12") sayfa bilgisi olarak tanınmaması;
kalıp sayfadan kalıp üstü örtülmüş eski başlığın test adı sanılması.

Şekil kararı: şekil sayısı ve boyutları A ile B'de tutuyorsa her şekil görüntü olarak kıyaslanır
(fark varsa HATA). Tutmuyorsa (aynı şekiller satır aralığı yüzünden farklı birleşmiş olabilir)
sorudaki toplam şekil mürekkebi kıyaslanır; yalnızca belirgin fark varsa (%6'dan fazla) UYARI. Hiç görülmemiş bir şablonda yine de beklenmedik bir durum çıkabilir;
öyle bir çiftte rapor şüpheli bir sonuç verirse o çift gönderilip kural genelleştirilmelidir.

### Bilinen sınırlar

- PDF'te **seçilebilir metin** olmalı. Yazılar eğriye çevrilmişse (outline) ya da taranmışsa önce
  OCR gerekir.
- PDF küçültülürken ya da Distiller / "PDF olarak yazdır" ile yeniden kaydedilirken yazı
  tiplerinin harf eşlemesi kaybolabilir: görüntü doğru, metin anlamsız ("Bu testte" →
  "%X WHVWWH"). Uygulama bunu fark edip "yazılar okunamıyor" diye durur; özgün PDF
  kullanılmalıdır. Küçültmek gerekirse Acrobat'ta Dosya > Farklı Kaydet > Küçültülmüş Boyutlu
  PDF yazıları korur.
- B baskı PDF'i **sayfa sayfa** olmalı; montajlı (imposition, 2 sayfa yan yana) PDF desteklenmez.
- Şekil parçalarının sayısı A ve B'de farklıysa, örneğin parçalar arasındaki boşluk değiştiği
  için, sorudaki toplam şekil mürekkebi karşılaştırılır. Mürekkep aynıysa fark yok sayılır.
  Bu yüzden toplam şeklin %6'sından küçük bir parçanın (tek bir ok, küçük bir etiket kutusu)
  eksikliği yakalanmayabilir.

### Gerçek kitapçıklarla deneme (8. sınıf Limit denemesi, sözel + sayısal, baskı PDF'leri)

| Çift | Soru | Sonuç | Süre |
|---|---|---|---|
| Sözel 1A ↔ 1B | 50 | 50/50 birebir eşleşme, 0 hata, 0 uyarı | ~2 sn |
| Sayısal 1A ↔ 1B | 40 | 40/40 birebir eşleşme, 0 hata, 0 uyarı | ~25 sn |
| TYT Deneme 1 A ↔ B | 125 | 125/125 birebir, 3 metin grubu aynı, 0 hata, 0 uyarı | ~35 sn |
| AYT Deneme 1 A ↔ B | 166 | 166/166 birebir, 0 hata, 0 uyarı | ~5 sn |
| 10. sınıf Deneme 2 A ↔ B | 100 | 100/100 birebir, 0 hata, 0 uyarı | ~14 sn |
| 11. sınıf Deneme 2 A ↔ B | 100 | 100/100 birebir, 0 hata, 0 uyarı | ~4 sn |
| 5. sınıf Deneme 1 A ↔ B | 75 | 75/75 birebir, 0 hata, 0 uyarı | ~16 sn |
| 7. sınıf Deneme 1 A ↔ B | 90 | 90/90 birebir, 0 hata, 0 uyarı | ~50 sn |
| 7. sınıf MOBESE Sayısal 1 A ↔ B (cevaplı) | 40 | 40/40 birebir, 2 metin grubu aynı, 0 hata (yalnız "cevaplar açık" uyarısı) | ~20 sn |
| 8. sınıf MOBESE Sayısal 1 A ↔ B (cevaplı) | 40 | 40/40 birebir, 0 hata (yalnız "cevaplar açık" uyarısı) | ~20 sn |
| AYT LEK 1. Deneme A ↔ B (cevaplı) | 166 | 166/166 birebir, 0 hata (yalnız "cevaplar açık" uyarısı) | ~60 sn |
| 7. sınıf Limit Sözel 1 A ↔ B (cevaplı) | 50 | 50/50 birebir, 4 metin grubu aynı, 0 hata | ~15 sn |
| Finale Doğru Kurs TYT Deneme 1 A ↔ B (cevaplı) | 125 | 124/125 birebir, 3 metin grubu aynı, **1 gerçek fark yakalandı** (Türkçe A-11 / B-10: V. deyim A'da "kolları sıvamak", B'de "kol gezmek") | ~60 sn |

TYT'de B kitapçığı metne bağlı grubun sorularını ters sırayla diziyor (A 35-36 → B 38-37).
Bu yayınevi düzeni hata sayılmaz; soruların yan yana ve aynı metnin altında olması denetlenir.
"16-20. soruları Din Kültürü … cevaplayacaktır" gibi seçmeli ders yönergeleri metin grubu
sayılmaz.

TYT B'nin bir kopyasına iki hata eklendi (Sosyal'de bir soru numarası kaydırıldı, bir metin
grubunun parçasından bir kelime silindi); ikisi de yakalandı.

Sözel 1B'nin bir kopyasına üç hata eklendi: bir soru numarası değiştirildi, bir kelime silindi,
bir soruya magenta cevap harfi kondu. Üçü de doğru soruda yakalandı ("6. soru bulunamadı" ile
"'7.' yazıyor, beklenen numara büyük olasılıkla 6", "Metin farklı: «stratejik»", "Açık kalan
cevap harfi: 'C'").

## Testler

`testler/` klasöründeki betikler uygulamanın motorunu arayüzsüz çalıştırır:

```bash
pip install pymupdf numpy scipy openpyxl
python3 testler/ornek_pdf_uret.py /tmp/ornek          # gerçek dizgiye benzeyen A/B PDF'leri
python3 testler/eslestir_sina.py "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/ornek /tmp/sonuc.json
python3 testler/kontrol_sina.py  "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/ornek
python3 testler/duzen_sina.py    "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/duzen  # cevap motoru: şık dizilişleri, taşan şıklar, şekil etiketleri
python3 testler/cevap_sina.py    "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/ornek  # EŞLEŞTİR: cevap harfi ve B numarası gerçek değerle aynı mı
python3 testler/kesir_sina.py    "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/kesir  # ilk satır numaranın üstünden başlıyor: kaybolmamalı
python3 testler/tire_sina.py     "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" /tmp/tire   # A ve B'de farklı tire karakteri: sahte uyarı olmamalı
python3 testler/numara_sina.py "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" A_baski.pdf B_baski.pdf OTOMATİK /tmp/numara  # B'de numaraları 11 biçimde bozar: her biri doğru yerde HATA olmalı
python3 testler/baski_kopya_sina.py "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" A.pdf B.pdf OTOMATİK /tmp/kopya  # gerçek cevaplı çiftten baskı kopyası: siyah/eğri cevap, 21 stil, siyah kod yakalanmalı
python3 testler/sus_sina.py "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" A.pdf B.pdf OTOMATİK /tmp/sus  # sütun sonu / sabit sayfa süsü: yanlış şekil uyarısı çıkmamalı
python3 testler/kds_sina.py "Kitapcik Eslestirici.app/Contents/Resources/kitapcik_eslestirici_app.py" kitapcik.pdf /tmp/kds  # KDS (tek kitapçık): 8 bozma senaryosu bulunmalı
```

Üretilen örnekler: iki sütunlu ve tek sütunlu (2x2 şıklı) sayfalar, metne bağlı gruplar, şekilli
sorular, magenta cevaplı ve cevapsız (baskı) A ile B. `ortaokul_B_hatali.pdf` içine 10 tür bilinçli
hata eklenir: eksik soru, yanlış grup başlığı, mükerrer numara, kelime farkı, cevap farkı, şık farkı,
şekil farkı, parça farkı, iki kez basılmış soru, metni yer değiştirmiş iki grup. Baskı varyantında
(`ortaokul_B_hatali_baski.pdf`) ayrıca bir soruda cevap harfi açık bırakılır.

v2.19 sonuçları:

- Temiz çiftlerde 0 hata; eşleşme doğruluğu %100. Cevap açık örneklerde yalnızca "bu kitapçıkta
  cevaplar açık" bilgisi çıkar.
- Hatalı B'de 10 hatanın 10'u yakalanıyor.
- İki kitapçık da cevapsız baskıyken cevap farkı dışındaki 9 hatanın 9'u ve açık kalan cevap
  yakalanıyor (cevap baskıda görünmediği için kıyaslanamaz).
