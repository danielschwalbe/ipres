# Übersetzungsfluss der API-Dokumentation

Die englische API-Dokumentation wird mit Sphinx aus den Docstrings generiert. Deutsche Übersetzungen werden separat in `.po`-Dateien gepflegt — der Quellcode bleibt auf Englisch.

## Verzeichnisstruktur

```
docs/
  source/
    conf.py                      # Sphinx-Konfiguration
    api.rst                      # Struktur der API-Referenz
    locales/
      de/
        LC_MESSAGES/
          api.po                 # Deutsche Übersetzung der API-Referenz
          index.po               # Deutsche Übersetzung der Startseite
  build/
    html/                        # Englische HTML-Dokumentation
    html/de/                     # Deutsche HTML-Dokumentation
```

## Dokumentation aufrufen

Die fertig gebaute Dokumentation liegt als HTML im Verzeichnis `docs/build/html/`. Die Dateien können direkt im Browser geöffnet werden:

- **Englisch:** `docs/build/html/index.html`
- **Deutsch:** `docs/build/html/de/index.html`

Alternativ lässt sich ein lokaler Webserver starten:

```bash
python -m http.server --directory docs/build/html 8080
```

Die englische Dokumentation ist dann unter `http://localhost:8080` und die deutsche unter `http://localhost:8080/de/` erreichbar.

## Erstmalige Einrichtung

```bash
pip install -r requirements.txt
cd docs
make gettext
sphinx-intl update -p build/gettext -l de
```

## Dokumentation bauen

Englisch:
```bash
cd docs && make html
```

Deutsch:
```bash
cd docs && sphinx-build -b html -D language=de source build/html/de
```

## Übersetzungsfluss nach Docstring-Änderungen

Wenn Docstrings im Quellcode geändert werden, muss die Übersetzung nachgepflegt werden:

1. Neue `.pot`-Dateien erzeugen:
   ```bash
   cd docs && make gettext
   ```

2. `.po`-Dateien aktualisieren:
   ```bash
   sphinx-intl update -p build/gettext -l de
   ```
   Geänderte Einträge werden mit `#, fuzzy` markiert.

3. In `docs/source/locales/de/LC_MESSAGES/api.po` die markierten Einträge suchen, übersetzen und das `#, fuzzy`-Flag entfernen.

4. Deutsche Dokumentation neu bauen:
   ```bash
   cd docs && sphinx-build -b html -D language=de source build/html/de
   ```

## Das fuzzy-Flag

Sphinx ignoriert Einträge mit `#, fuzzy`. Nur vollständig übersetzte und nicht als fuzzy markierte Einträge erscheinen in der deutschen Dokumentation. Nicht übersetzte Einträge (`msgstr ""`) werden auf Englisch angezeigt.