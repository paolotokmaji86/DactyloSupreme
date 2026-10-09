# Manuele test op de Mac (Safari)

De automatische test draait in Chromium op Linux. Hoe Safari op macOS dode toetsen, Caps Lock,
het accentmenu en het Belgisch AZERTY-toetsenbord echt doorgeeft, kan hij niet nabootsen.
Overloop daarom deze lijst op de MacBook voor je een nieuwe versie pusht.

Sinds versie 0.4.0 komt elk getypt teken binnen via een verborgen tekstveld, in alle lessen.
Test dus ook een oude les (bv. 2.1 of 5.1), niet alleen module 6.

## Voorbereiding

- Test in een **gewoon Safari-venster**, niet in de app in het Dock. Een webapp in het Dock heeft
  eigen websitegegevens, los van Safari, dus haar voortgang blijft onaangeroerd.
- Open de site. Ga naar Instellingen, kies Toetsenbord: "Belgisch AZERTY, Mac".
- Om elke les te kunnen openen: Instellingen, "Back-up terugzetten", en kies
  `tests/alles-open.json` uit deze repository. Daarin staan alle lessen als geslaagd.
  Zet dit bestand **nooit** terug in de app van de gebruikster zelf.
- Ga een les binnen via Lessen en druk op Enter om te beginnen.

Noteer bij elk punt: in orde, of wat er gebeurde. Let telkens op de teller "nauwkeurig" en op de
cursor: één aanslag mag maar één teken verder gaan.

## Gewone invoer (alle lessen)

1. Les 2.1: typ een paar regels. Elke toets schuift precies één teken op en telt één aanslag, de
   spatie telt mee en laat de pagina niet scrollen, Enter, Tab en Backspace doen niets, Esc stopt
   de oefening.
2. Klik tijdens een oefening in de lege marge naast de tekst, en ook op de kopbalk. Typ meteen
   verder, in les 6.4 ook meteen ^ e. Typen moet blijven werken, zonder fout.
3. Wissel met Cmd+Tab naar een ander programma en terug. Typ meteen verder (ook ^ e).
4. Hou een letter (bv. e) een seconde ingedrukt. Verschijnt het accentmenu van macOS? Laat los en
   typ verder. Noteer wat er gebeurt en of er een aanslag te veel geteld wordt.

## Module 5: hoofdletters

5. Les 5.1 en 5.3: hoofdletters met de linker- en de rechter-Shift tellen als juist.
6. Zet Caps Lock aan tijdens een oefening. Er verschijnt een melding en typen telt niet mee.
   Zet Caps Lock uit en typ verder: dat gaat zonder fout.

## Module 6: accenten en dode toetsen

7. Les 6.1 (é en è) en 6.3 (ç en à): de tekens tellen als juist.
8. Les 6.4 (ù en het dakje): typ ù (rechts naast de m).
9. Zelfde les: typ ^ en daarna e. Verwacht: **ê als één juiste aanslag**; de nauwkeurigheid blijft
   100%; de cursor gaat één teken verder. Idem voor â en ô.
10. Zelfde les: bij een ê toont het toetsenbord eerst de ^-toets én de e. Na het aanslaan van ^
    blijft enkel de e oplichten.
11. Typ snel na elkaar drie keer ê (^ e ^ e ^ e). Verwacht: per teken één positie en één aanslag.
12. Les 6.5 (trema): Shift + ^, Shift loslaten, dan e geeft ë als één juiste aanslag. Idem voor
    ï, ö, ü.
13. Zelfde les: hou Shift bewust vast bij de e. Verwacht: Ë telt als één fout, daarna lukt ë
    gewoon.
14. Zelfde les, bij een ë: druk eerst ^ zonder Shift. Verwacht: het toetsenbord blijft Shift + ^
    tonen (niet enkel de e).
15. Typ ^ en daarna een letter die er niet mee samengaat (bv. r). Verwacht: **één** fout, de
    cursor blijft staan, geen vastloper.
16. Typ ^ en daarna Backspace. Verwacht: geen fout; het toetsenbord toont weer ^ en de letter;
    daarna telt ^ e als juist.
17. Typ ^ en daarna een spatie. Verwacht: een fout, geen vastloper.
17b. Druk ^ en meteen Esc. Start de oefening opnieuw en typ ^ e: telt als juist.
18. Caps Lock aan, ^ e: melding, het telt niet. Caps Lock uit en meteen ^ e: telt als juist.
19. Laat een oefening eindigen op een teken met een dode toets (bv. een woord als enquête of
    ideeën in les 6.7). Verwacht: het resultaat verschijnt zonder extra fout, en Enter gaat naar
    de volgende oefening.
20. Kies in Instellingen "Doortypen, de fout blijft rood staan" en herhaal punt 9 en 15.
    Zet de instelling daarna terug.

## Algemeen

21. Laad de echte site: de lettertypes (Atkinson Hyperlegible en IBM Plex Mono) worden geladen.
