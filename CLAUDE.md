# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dactylo Supreme

Webapp om blind te leren typen met tien vingers ("dactylo"), voor één volwassen gebruiker:
Nederlandstalig, MacBook met een **Belgisch AZERTY**-toetsenbord, gebruikt via Safari
(als app in het Dock). De site staat op GitHub Pages vanuit deze repository (branch `main`,
map `/`). **Elke push naar `main` staat binnen een paar minuten live bij de gebruiker.**
Alles wat op `main` staat, wordt mee gepubliceerd, ook dit bestand en `tests/`.

Stijl: sober en volwassen, zoals een klassieke dactylocursus. Geen kinderachtige spelletjes,
geen geluid.

## Werkwijze met Paolo

- Werk per module. Na elke module: stoppen, kort rapporteren, wachten op akkoord.
- Commit lokaal; **push pas na expliciet akkoord** van Paolo (een push is meteen live).
- Wees eerlijk over wat getest is en wat niet. Noem iets pas klaar als de tests slagen en
  duidelijk is wat nog manueel op de Mac getest moet worden.
- Geef plannen volledig in één bericht, stap voor stap.
- Antwoord in het Nederlands.

## Architectuur

Alles zit in één bestand: `index.html` (HTML, CSS en vanilla JavaScript). Geen build, geen
frameworks, geen extra libraries. De enige externe bron is Google Fonts (Atkinson Hyperlegible
en IBM Plex Mono); de app moet ook zonder die lettertypes werken.

Het script is één IIFE met `'use strict'`, in ES5-stijl: `var`, `function` en
stringconcatenatie; geen `let`/`const`, arrow functions, template literals of classes.
Ingebouwde objecten zoals `Map`, `Set`, `Object.assign` en `padStart` worden wel gebruikt.
Commentaar is in het Nederlands.

Routes via de hash: `#/lessen`, `#/les/<id>`, `#/voortgang`, `#/oefenen`, `#/instellingen`.
`route()` stopt bij elke hashwijziging de lopende oefening en wist `FLOW`. Binnen een les blijft
de hash `#/les/<id>`: intro, oefeningen en resultaten zijn gewone `render…()`-aanroepen.

Elke pagina bouwt een HTML-string en zet die in `app.innerHTML`; elke dynamische waarde gaat
door `esc()`. Knoppen krijgen `data-act="…"` en worden afgehandeld in de ene klik-handler
onderaan het script. Buiten een oefening klikt Enter op het element met `data-primary`.
Globale toestand: `S` (opgeslagen gegevens), `RUN` (lopende oefening), `FLOW` (lopende les of
vrije oefening) en `NOTICE` (melding die de volgende pagina één keer toont).

Belangrijkste onderdelen, in de volgorde van het script:

- `buildLayout(variant)` en `buildCharMap()`: het toetsenbord op het scherm, Belgisch AZERTY
  in een Mac- en een Windows-variant. Alleen visueel: `LAYOUT` en `CHARMAP` sturen het
  toetsenbord, de hint voor de volgende toets en vinger, en de fouten per vinger. Vingers:
  `lp lr lm li ri rm rr rp th`. Na een wijziging van `S.settings.layout`: `refreshLayout()`.
- `WORDS` (kleine letters) en `SENTENCES` (volledige vorm: hoofdletter, leestekens): eigen
  Nederlandse lijsten. `sentenceForm()` laat de hoofdletter vooraan en de punt achteraan weg
  zolang die nog niet gekend zijn; een zin met andere ongekende tekens wordt pas bruikbaar als
  die aangeleerd zijn. Generatoren nemen alleen woorden en zinnen met gekende tekens, dus inhoud
  voor latere modules mag er al in staan. `BASELINE_TEXT` (beginmeting) heeft wel hoofdletters
  en leestekens.
- `MODULES`, met lessen via `L(id, title, type, opts)` (opts: `add`, `focus`, `help`, `intro`).
  `derive()` zet alle lessen in één rij `ALL_LESSONS` (een les gaat open als de vorige of de
  les zelf geslaagd is),
  geeft ze een `nr` volgens hun positie (bv. "2.4", alleen weergave) en vult `KNOWN[lesId]` =
  alle tekens die gekend zijn tot en met die les (afgeleid uit `add`: letters, hoofdletters,
  accenten, leestekens, cijfers, symbolen, `\n`, `\t`). `__dactylo.allowed(id)` = `KNOWN` plus
  de spatie; de test gebruikt die functie.
- Opslag: `defaultState()`, `migrate()`, `load()`, `save()`; zie "Opgeslagen gegevens".
- Oefenteksten: `planFor(lesson, known)` bepaalt de oefeningen per lestype (`intro`,
  `baseline`, `new`, `practice`, `words`, `sentences`, `review`, `weak`, `moduletest`, `free`);
  een les met `src` (bv. `'names'`) krijgt `itemsPlan()` met een bron uit `SOURCES`. Teksten
  worden gemaakt met een seeded RNG (`mulberry32`) via `makeCtx()`. Kleine letters (ook met
  accent) oefen je met `drillPieces`/`comboPiece` en woorden; andere tekens komen in korte
  stukjes uit `drillPiece()` (los) of `pieceWith()` (natuurlijk: een naam, `woord,`, een zin).
  `drillText()` zet via `coverFill()` elke nieuwe toets zeker in de oefening "Nieuwe toetsen"
  (de test controleert dat). `poolsFor(known)` cachet per gekende set de bruikbare woorden,
  namen (`NAMES`) en zinnen.
- Typen: tekens komen binnen via het verborgen tekstveld `#catch`: een gewone aanslag als
  input-event (`insertText`), een teken met een dode toets (ê, ë, ...) via `compositionend`.
  `feed()` geeft ze aan `typeChar()`. Input-events die bij een compositie horen tellen niet, en
  `COMPOSED` onderdrukt het input-event dat Safari na `compositionend` nog stuurt. Keydown op
  `document` blijft voor Esc, Enter, Tab, Backspace en `Dead`. De app vergelijkt het
  binnenkomende teken met het verwachte teken, dus het werkt op elke toetsenbordindeling. Een
  pauze tussen twee aanslagen telt maximaal `MAX_GAP` (5 s) mee.
- Statistieken per teken in `S.keys` (`h` = juist, `e` = fout), geteld op het verwachte teken,
  zonder spatie en zonder beginmeting. Zwakke toetsen komen vaker terug via `keyWeights()` en
  `weakestKeys()`.
- Testtoegang: `window.__dactylo` (ook `allowed(id)` en `names`). `state()`, `run()`, `flow()` en `layout()` zijn functies
  omdat die variabelen opnieuw toegewezen worden; `importJSON(tekst, true)` slaat de
  bevestiging over.

### Opgeslagen gegevens

`S` bevat `settings` (`name`, `layout`, `errorMode`, `help`, `theme`), `lessons[lesId]`
(`passed`, `bestAcc`, `bestApm`, `attempts`, `lastAt`, `passedAt`), `sessions` (één per
afgewerkte oefening: `t`, `l` = les-id, `x` = oefening, `k` = `ex`/`test`/`base`/`free`,
`apm`, `acc`, `n` = tekens, `e` = fouten, `ms`; alleen de laatste 3000), `keys`,
`days['JJJJ-MM-DD']` (actieve ms per dag, voor de dagen op rij), `totalMs` en `baseline`.

`save()` schrijft altijd heel `S` weg; lukt dat niet, dan vraagt een banner om back-ups.
Importeren en "Alle voortgang wissen" vervangen `S` door een nieuw object: houd geen
verwijzingen naar `S` of delen ervan bij. Een back-up is `JSON.stringify(S)`. `migrate()`
draait bij elke start en bij elke import en vult ontbrekende velden op het hoogste niveau en
in `settings` al aan uit `defaultState()`; andere omzettingen (regel 3 hieronder) schrijf je
erbij. `importJSON()` weigert een back-up met een hoger `schema`. Een les die halverwege
verlaten wordt, begint opnieuw bij de intro.

### Valkuilen

- Elk plan in `planFor()` eindigt met precies één oefening met `test: true` (de slottoets).
  `finishRun()` geeft een testresultaat aan `finishLesson()`; na een gewone oefening toont
  `renderExerciseResult()` een knop voor de volgende oefening, en die geeft een JavaScript-fout
  als er geen is.
- `threshold()` geeft 95 (procent nauwkeurigheid op de slottoets), of `null` voor `intro`,
  `baseline` en `free`: die slagen altijd. Het wordt gebruikt in `renderIntro()` en
  `finishLesson()`; `renderProgress()` rekent voor "beste geslaagde slottoets" met een eigen
  vaste 95. Een nieuw lestype heeft een `case` in `planFor()` nodig.
- `wordsText()` en `sentencesText()` geven `null` als er minder dan 6 woorden of 4 zinnen
  bruikbaar zijn; de plannen vallen dan met `||` terug op lettercombinaties.
- Woorden met een hoofdletter (`startingWith()`/`capWord()`): een ij vooraan wordt IJ (IJs), en
  dagen en maanden (`CALENDAR`) krijgen geen hoofdletter. Een slottoets met een focus zonder
  kleine letters (hoofdletters, leestekens, cijfers, tekens) bevat zeker een paar focusstukjes;
  de test eist gemiddeld minstens 5 focustekens per 100 tekens en minstens 3 per slottoets.
  Zwakke focustekens worden vaker gekozen (`pickFocus()`).
- Leestekens tussen stukjes: `fillTo()` en `coverFill()` zetten geen zin met hoofdletter na een
  stukje dat op , ; of : eindigt (`badAfter()`), en een tekst eindigt niet op zo'n teken. De
  test controleert ook spaties rond leestekens en haakjes en aanhalingstekens in paren.
  `sentWeight()` telt de punt achteraan niet mee; bij een focus zonder kleine letters kiest
  `sentencesText()` alleen zinnen met een focusteken. Meldingen noemen tekens bij naam
  (`KEY_NAME`, `keyName()`: komma, punt, ...).
- De seed van een oefening is `FLOW.seed + i * 7919 + FLOW.attempt * 104729`. Elke knop om
  opnieuw te beginnen verhoogt `FLOW.attempt`, zodat er een nieuwe tekst komt.
- `startExercise()` voegt alle witruimte samen tot één spatie, en `stripHTML()` maakt precies
  één `.ch`-span per teken (woorden in een `.w`-span, spaties apart): `RUN.spans[pos]` moet
  gelijk blijven lopen met `RUN.text`.
- Typen: Caps Lock blokkeert de invoer (met een melding). Cmd- en Ctrl-sneltoetsen gaan naar de
  browser, maar Ctrl+Alt (AltGr) wordt getypt. Enter, Tab en Backspace doen niets; Esc stopt de
  oefening. `errorMode` `block` laat de cursor staan bij een fout, `continue` gaat verder en
  kleurt het teken rood. De klok start bij de eerste aanslag.
- `CHARMAP` kent de basis- en de Shift-laag. Tekens met een dode toets staan in `DEAD`
  (ê = ^ dan e, ë = Shift + ^ dan e) en krijgen een hint in twee stappen. `RUN.dead` onthoudt
  welke dode toets ingedrukt werd (`^` of `¨`); alleen de juiste kort de hint in tot de letter.
  Een geannuleerde compositie (lege `compositionend`) zet de hint terug, en `^r` bij een
  verwacht teken met een dode toets telt als één fout. Bij een Shift-teken licht de Shift van
  de andere hand op (`shiftIdFor()`). Op Voortgang tellen de fouten op ê en ë bij de ^-toets.
- `PLANNED_TOTAL` is de som van alle `planned`; `planned` is ook de noemer van de
  voortgangsbalk per module en moet gelijk zijn aan het aantal lessen van een gebouwde module
  (de test controleert dat). De startpagina noemt de laatste gebouwde module zelf.
- Het typscherm past maar net op een MacBook (de test meet 1440 x 790, ook bij de langste
  oefeningen). Daarom toont de strook tijdens een oefening twee regels die meeschuiven
  (`.running .run .strip`, `markCurrent()`); zonder toetsenbord op het scherm (`no-kb`) meer.
  Elke extra regel boven het toetsenbord kan de test doen falen.
- CSS: kleuren zijn variabelen op `:root`. De donkere kleuren staan er twee keer (in
  `@media (prefers-color-scheme: dark)` en onder `:root[data-theme="dark"]`): pas beide aan.
  Vingerkleuren: `--f-*` (vol) en `--t-*` (tint), via de klassen `.f-lp` tot `.f-th`. De
  heatmap bij Voortgang gebruikt vaste rgba-kleuren in `kbHTML()`.

## Harde regels: de voortgang van de gebruiker mag nooit verloren gaan

1. `STORAGE_KEY = 'dactylo-be-azerty'` nooit veranderen.
2. Les-ids nooit veranderen, hergebruiken of verwijderen. Nieuwe lessen krijgen de ids uit het
   leerplan hieronder.
3. Verandert de vorm van de opgeslagen gegevens, verhoog dan `SCHEMA` en voeg in `migrate()`
   een omzetting toe (`if (s.schema < 2) { ... }`). Gegevens van alle vorige versies moeten
   blijven werken. De test zet opslag van versie 0.1.0 klaar en controleert dat.
4. Verhoog `APP_VERSION` bij elke wijziging: `0.x.0` voor een nieuwe module, `0.x.y` voor een
   fix. Het versienummer staat onderaan de pagina; zo ziet Paolo wat er live staat.
5. Alles wat de gebruiker ziet is Nederlands, in korte, duidelijke zinnen. Decimale komma
   (`fmtPct`). Dagen en maanden schrijf je in het Nederlands met een kleine letter.
6. Schrijf alle oefenteksten zelf. Neem geen bestaande teksten, liedjes of boekfragmenten over.
7. Een oefentekst bevat alleen tekens die de gebruiker op dat moment al geleerd heeft.

## Didactiek (gebaseerd op bestaande cursussen)

- Toetsvolgorde van een bestaande AZERTY-dactylocursus: thuisrij (s d f / j k l, q m, g h),
  bovenrij (a p, z o, e r u i, t y), onderrij (w x, c v, b n), dan accenten en leestekens.
- Veel korte lessen (model TypingClub), ongeveer 10 minuten per les: korte uitleg, 4 à 5
  oefeningen met een resultaat na elke oefening, en een slottoets (model TICKEN).
- Nauwkeurigheid eerst (TypingClub). Snelheid telt pas mee vanaf fase 2.
- Zwakke toetsen vaker herhalen (TIPP10, keybr).
- Na de toetsen: aanpassing (alles door elkaar), snelheid (woorden uit de eigen taal),
  vlotheid (volledige alinea's, fouten verbeteren, gelijkmatig ritme) (model Klavaro).
- De hulp van het toetsenbord op het scherm verdwijnt stap voor stap: `help: 'full'` (volgende
  toets altijd zichtbaar), `'hint'` (pas na een fout of 2 s twijfel), `'none'` (verborgen).
- Eindnorm (TICKEN): minstens 100 aanslagen per minuut bij 99% nauwkeurigheid.

## Belgisch AZERTY: details die ertoe doen

- Thuisrij: q s d f g h j k l m (zonder klinkers). Streepjes op f en j.
- Punt = Shift + `;`, vraagteken = Shift + `,`, `/` = Shift + `:`, `+` = Shift + `=`,
  `%` = Shift + `ù`, `*` = Shift + `$`, `_` = Shift + `-`.
- Cijfers: Shift + cijferrij (`& é " ' ( § è ! ç à`). Cijfers 1 tot 5 met de rechter-Shift,
  6 tot 0 met de linker-Shift.
- é, è, ç en à liggen zonder Shift op de cijferrij; ù ligt rechts van m.
- `^` en `¨` zijn dode toetsen rechts van p: ê = `^` dan e; ë = Shift + `^` (¨) dan e. In het
  Nederlands komen vooral ë, ï en é voor (België, ideeën, ruïne, één, café).
- Hoofdletters: Shift met de andere hand dan de letter.
- Mac en Windows: letters, cijfers en leestekens liggen op dezelfde plek. Verschillen: de toets
  links van 1 (Mac: @ en #, Windows: ² en ³), € en de Option-/AltGr-combinaties.
  **Op de Mac is nog niet geverifieerd welke van @ en # Shift vraagt, en waar € zit.** Vul dat
  niet in op basis van aannames; Paolo stuurt een foto van haar toetsenbord.

## Leerplan: 126 lessen

| Module | Fase | Inhoud | Lessen | Status |
|---|---|---|---|---|
| 1 Start | 1 | Houding, thuispositie, vingerverdeling, beginmeting | 3 | klaar |
| 2 Thuisrij | 1 | s d f j k l, q m, g h | 10 | klaar |
| 3 Bovenrij | 1 | a p, z o, e r u i, t y | 15 | klaar |
| 4 Onderrij | 1 | w x, c v, b n | 11 | klaar |
| 5 Hoofdletters | 1 | Linker- en rechter-Shift | 8 | klaar |
| 6 Accenten | 1 | é è, ç à, ù en ^ (ê), ¨ (ë ï ö ü) | 10 | klaar |
| 7 Leestekens | 1 | , ; ! : " ' ( ) - . ? | 12 | klaar |
| 8 Cijfers | 1 | 1 tot 0 met Shift, datums, bedragen, nummers | 8 | te bouwen |
| 9 Tekens en bediening | 1 | @ # € % / + = * &, Enter, Backspace, Tab | 9 | te bouwen |
| 10 Alles door elkaar | 2 | Alle toetsen, lastige combinaties, zwakke toetsen | 10 | te bouwen |
| 11 Snelheid | 3 | Meest gebruikte woorden, korte zinnen, tijdtests van 1 minuut | 12 | te bouwen |
| 12 Vlotheid | 4 | Alinea's, verhalen, zakelijke teksten, e-mails, brieven, tijdtests van 3 en 5 minuten | 15 | te bouwen |
| 13 Examen | 5 | Twee proefexamens en het examen met certificaat | 3 | te bouwen |

### Lessen per module (deze ids gebruiken)

**Module 4, onderrij.** w met de linkerpink (vanaf q), x met de linkerringvinger (vanaf s),
c met de linkermiddelvinger (vanaf d), v en b met de linkerwijsvinger (vanaf f), n met de
rechterwijsvinger (vanaf j).
`m4-wx` (new, add `wx`), `m4-wx-oef` (practice), `m4-cv` (new, add `cv`), `m4-cv-oef`,
`m4-bn` (new, add `bn`), `m4-bn-oef`, `m4-woorden` (words), `m4-zinnen` (sentences),
`m4-herh` (review), `m4-zwak` (weak), `m4-toets` (moduletest).
Na module 4 zijn alle letters gekend: breid `WORDS` en `SENTENCES` uit met gewone
Nederlandse woorden en zinnetjes (nog in kleine letters, zonder leestekens).

**Module 5, hoofdletters.** De linker-Shift voor letters van de rechterhand
(Y U I O P H J K L M N), de rechter-Shift voor letters van de linkerhand
(A Z E R T Q S D F G W X C V B).
`m5-shift-links` (new), `m5-shift-links-oef` (practice), `m5-shift-rechts` (new),
`m5-shift-rechts-oef` (practice), `m5-namen` (words: steden en voornamen),
`m5-zinnen` (sentences: hoofdletter vooraan, nog zonder punt), `m5-herh` (review),
`m5-toets` (moduletest).

**Module 6, accenten.**
`m6-ee` (new: é en è), `m6-ee-oef` (practice), `m6-ca` (new: ç en à), `m6-circ` (new: ù en de
dode toets ^ voor ê, â, ô), `m6-trema` (new: Shift + ^ voor ë, ï, ö, ü), `m6-trema-oef`
(practice), `m6-woorden` (words: één, café, crème, enquête, België, ideeën, ruïne, naïef,
coördinator, reünie, ...), `m6-herh` (review), `m6-zwak` (weak), `m6-toets` (moduletest).
Zie technische taak 4: dode toetsen zijn het grootste risico van het hele project.

**Module 7, leestekens.**
`m7-komma` (new: `,` `;`), `m7-komma-oef` (practice), `m7-uitroep` (new: `!` `:`),
`m7-aanhaling` (new: `"` en `'`, zoals in zo'n, auto's, 's avonds), `m7-haakjes` (new: `(` `)`),
`m7-koppel` (new: `-`, zoals in e-mail, Oost-Vlaanderen), `m7-punt` (new: `.` en `?`, beide met
Shift), `m7-punt-oef` (practice), `m7-zinnen` (sentences: volledige zinnen met hoofdletter en
leestekens), `m7-herh` (review), `m7-zwak` (weak), `m7-toets` (moduletest).
Vanaf `m7-punt` krijgen alle zinnen een hoofdletter en een punt.

**Module 8, cijfers.**
`m8-cijfers-links` (new: 1 tot 5, met de rechter-Shift), `m8-cijfers-rechts` (new: 6 tot 0,
met de linker-Shift), `m8-cijfers-oef` (practice), `m8-datums` (datums en uren, bv. 14 maart,
9.30 uur), `m8-bedragen` (bedragen en nummers, bv. 12,50 euro, 09 123 45 67), `m8-herh`
(review), `m8-zwak` (weak), `m8-toets` (moduletest).

**Module 9, tekens en bediening.** Pas bouwen na controle van de Mac-indeling (@, #, €).
`m9-at` (new: @ en #), `m9-euro` (new: € en %), `m9-reken` (new: / en +), `m9-tekens`
(new: = * &), `m9-enter` (new: Enter, nieuwe regels), `m9-backspace` (fouten verbeteren met
Backspace), `m9-tab` (Tab), `m9-herh` (review: e-mailadressen, websites, bedragen),
`m9-toets` (moduletest).

**Module 10, alles door elkaar (fase 2).**
`m10-mix1`, `m10-mix2`, `m10-mix3` (alle toetsen door elkaar), `m10-ij` (ij, ei en ui),
`m10-ch` (ch, sch en ng), `m10-eu` (eu, oe, ou en au), `m10-dubbel` (dubbele letters),
`m10-zwak1`, `m10-zwak2` (weak), `m10-toets` (moduletest).
De lessen over combinaties vragen een generator die op lettercombinaties focust in plaats van
op losse toetsen.

**Module 11, snelheid (fase 3).**
`m11-woorden100`, `m11-woorden200`, `m11-woorden500`, `m11-woorden1000` (de meest gebruikte
woorden), `m11-zinnen1`, `m11-zinnen2`, `m11-zinnen3` (korte zinnen), `m11-tijd1`,
`m11-tijd2`, `m11-tijd3` (tijdtests van 1 minuut), `m11-zwak` (weak), `m11-toets`.

**Module 12, vlotheid (fase 4).**
`m12-alinea1` tot `m12-alinea3`, `m12-verhaal1`, `m12-verhaal2`, `m12-zakelijk1`,
`m12-zakelijk2`, `m12-email1`, `m12-email2`, `m12-brief1`, `m12-brief2` (met Enter),
`m12-tijd3-1`, `m12-tijd3-2` (tijdtests van 3 minuten), `m12-tijd5` (tijdtest van
5 minuten), `m12-toets`.

**Module 13, examen (fase 5).**
`m13-proef1`, `m13-proef2`, `m13-examen`. Het examen geeft een certificaat.

### Slaagnormen

- Fase 1 (modules 1 tot 9): slottoets minstens 95% nauwkeurig, geen snelheidseis.
- Module 10: minstens 97% en 60 aanslagen per minuut.
- Module 11: minstens 97%; de minimumsnelheid stijgt per les van 70 naar 100 aanslagen per
  minuut.
- Module 12: minstens 97% en 100 aanslagen per minuut.
- Module 13: tijdtest van 5 minuten, minstens 99% en 100 aanslagen per minuut. Certificaat:
  geslaagd bij 100, zilver bij 150, goud bij 200 aanslagen per minuut, telkens bij minstens 99%.

`threshold()` moet daarvoor naast nauwkeurigheid ook een snelheidseis kunnen teruggeven, en
het resultaatscherm moet tonen welke eis niet gehaald werd.

### Hulp van het toetsenbord op het scherm

Modules 4 tot 9: nieuwe lessen `full`, de andere `hint`. Modules 10 en 11: `hint`.
Modules 12 en 13: `none`. Via Instellingen kan de gebruiker de hulp altijd zelf aanzetten.

## Technische taken

1. **Geslaagde lessen blijven open.** Klaar in 0.1.1: `isUnlocked(l)` geeft ook `true` als `l`
   zelf al geslaagd is, zodat gedane lessen open blijven als er ooit een les tussenkomt.
2. **Toegelaten tekens per les.** Klaar in 0.3.0: `KNOWN` bevat alle tekens uit `add`, en
   `window.__dactylo.allowed(id)` geeft de toegelaten tekens van een les, inclusief de spatie.
3. **Hoofdletters en leestekens in teksten** (modules 5 en 7). Gebruik ze nooit vóór de les
   waarin ze aangeleerd worden. Eigennamen met een hoofdletter. Hoofdletters zijn klaar in 0.3.0
   (`sentenceForm()`, `NAMES`, `pieceWith()`), leestekens in 0.5.0 (`WRAP`, `APOS_WORDS`,
   `HYPHEN_WORDS`, zinnen met leestekens).
4. **Dode toetsen** (module 6). Klaar in 0.4.0 (zie "Typen" hierboven); manueel te testen met
   `tests/MANUEEL-safari.md`. Oorspronkelijke opdracht: bij ^ en ¨ sturen browsers op macOS vaak compositie-events, en
   de keydown van de afsluitende letter kan `isComposing = true` hebben. De huidige handler
   slaat zulke events over, waardoor ê en ë nooit zouden binnenkomen. Vang tekens daarom op via
   een verborgen, gefocust tekstveld met `beforeinput`, `input` en `compositionend`; keydown
   blijft voor Esc, Enter, Backspace en Tab. Zorg dat niets dubbel telt, en pas `TYPE_JS` in
   `tests/test_app.py` mee aan. Dit kan in Chromium op Linux niet volledig getest worden:
   schrijf een manuele testlijst voor Safari op de Mac.
5. **Enter en Backspace** (modules 9 en 12). `startExercise` voegt nu alle witruimte samen tot
   één spatie; laat `\n` toe, toon Enter als ⏎ en laat het typen. Voeg een modus toe waarin een
   fout zichtbaar blijft en met Backspace verbeterd moet worden, zoals bij echte tekst.
6. **Tijdtests** (modules 11 tot 13). Een oefenvorm met een vaste duur (1, 3 of 5 minuten) in
   plaats van een vaste tekst. Score: aanslagen per minuut en nauwkeurigheid over die duur. De
   test in `tests/test_app.py` verwacht nu dat een oefening eindigt als de tekst getypt is;
   pas hem aan voor tijdtests.
7. **Woordenlijst op frequentie** (module 11). Stel zelf de meest gebruikte Nederlandse woorden
   samen. Alleen bestaande, gewone woorden.
8. **Certificaat** (module 13). Een afdrukbare pagina (print-CSS) met naam
   (`S.settings.name`), datum, snelheid, nauwkeurigheid en niveau.

## Openstaande punten

- Mac-indeling van @, # en € controleren vóór module 9.
- Dode toetsen testen op haar Mac in Safari, met de lijst in `tests/MANUEEL-safari.md`.
- Google Fonts laden niet in een testomgeving zonder internet. Op de echte site controleren.

## Testen

Eenmalig, in WSL vanuit de repo (zet `.venv/` in `.gitignore`):

```
python3 -m venv .venv
source .venv/bin/activate
pip install playwright
python -m playwright install --with-deps chromium
```

`--with-deps` installeert systeempakketten en vraagt daarom het sudo-wachtwoord. In deze WSL
staan Playwright en Chromium ook al in de gebruikersinstallatie (`~/.local`,
`~/.cache/ms-playwright`); dan werkt `python3 tests/test_app.py` ook zonder venv.

Bij elke wijziging:

```
source .venv/bin/activate
python3 -m http.server 8765 >/dev/null 2>&1 &
python3 tests/test_app.py
kill %1
```

De test doorloopt alle lessen die in `index.html` staan, dus hij groeit mee met nieuwe
modules. Hij controleert onder meer:

- het lezen van opslag uit versie 0.1.0;
- het leerplan (13 modules, 126 lessen, unieke ids);
- dat oefenteksten enkel toegelaten tekens bevatten (100 seeds per oefening);
- dat een slottoets met te veel fouten niet slaagt en de volgende les op slot houdt;
- het doorlopen van elke les;
- dat de voortgang een herlaadbeurt overleeft;
- back-up exporteren en importeren;
- dat het typscherm op een MacBook-scherm (1440 x 790) past;
- dat er geen JavaScript-fouten zijn.

Screenshots komen in `/tmp/dactylo-shots`: bekijk ze na elke module. Breid de test uit voor
nieuw gedrag.

De voortgang staat in `localStorage` per adres: `localhost`, `file://` en de echte site hebben
elk hun eigen voortgang.

`TYPE_JS` in de test typt zoals een echt toetsenbord: een keydown op het document en een
input-event in `#catch`; `COMPOSE_JS` bootst een dode toets na in de volgorde van Chrome en van
Safari. Wat de test niet kan nabootsen, staat in `tests/MANUEEL-safari.md` (manuele test op de
Mac). `tests/alles-open.json` is een back-up waarin alle lessen geslaagd zijn, om elke les te
kunnen openen bij een manuele test; nooit terugzetten in de app van de gebruiker zelf.

## Na elke module

1. Tests slagen en de screenshots zijn bekeken.
2. `APP_VERSION` is verhoogd.
3. Lokaal gecommit, met een duidelijke boodschap.
4. Rapport aan Paolo: wat er veranderde, het testresultaat, wat hij nog manueel op de Mac moet
   testen, en of de gebruiker vooraf een back-up moet maken (ja bij een schemawijziging).
5. Pas pushen na zijn akkoord.
