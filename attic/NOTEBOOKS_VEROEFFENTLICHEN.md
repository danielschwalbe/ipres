# Jupyter Notebooks öffentlich zugänglich machen

## Optionen im Überblick

### 1. GitHub + nbviewer (Schnellste Lösung)
**Was tun:**
- Notebooks zu GitHub pushen
- Link teilen via: https://nbviewer.org

**Vorteile:**
- Kostenlos, keine Einrichtung
- Sofort verfügbar

**Nachteile:**
- Nur Ansicht, nicht interaktiv

---

### 2. Binder (Interaktiv - EMPFOHLEN)
**Was tun:**
1. `requirements.txt` erstellen:
   ```
   pandas
   matplotlib
   numpy
   jupyter
   ```

2. Falls ipres auf PyPI ist: einfach `ipres` hinzufügen
   Falls nicht: `setup.py` im Repo haben, Binder installiert automatisch

3. Zu https://mybinder.org gehen
   - GitHub URL eingeben
   - Binder-Badge kopieren

4. Badge zu README.md hinzufügen:
   ```markdown
   [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/DEIN-USERNAME/ipres/main?filepath=verhaeltniswahl.ipynb)
   ```

**Vorteile:**
- Benutzer können Code ausführen!
- Kostenlos

**Nachteile:**
- Erste Start kann 1-2 Minuten dauern

---

### 3. Jupyter Book (Professionelle Website)
**Was tun:**
```bash
pip install jupyter-book ghp-import
jupyter-book create mein-buch
# Notebooks kopieren
jupyter-book build mein-buch
ghp-import -n -p -f mein-buch/_build/html
```

**Vorteile:**
- Sehr professionell
- Durchsuchbar, strukturiert
- GitHub Pages kostenlos

**Nachteile:**
- Mehr Aufwand bei Einrichtung
- Nicht interaktiv

---

### 4. Google Colab
**Was tun:**
- Notebook zu Google Drive hochladen
- Mit Colab öffnen
- Link teilen

Am Anfang des Notebooks:
```python
!pip install git+https://github.com/DEIN-USERNAME/ipres.git
```

**Vorteile:**
- Schnell, ausführbar
- Keine eigene Infrastruktur

**Nachteile:**
- Google-Account nötig
- Abhängig von Google

---

## Empfohlene Reihenfolge

1. **Heute/Morgen**: GitHub + nbviewer (5 Minuten)
2. **Diese Woche**: Binder einrichten (15 Minuten)
3. **Später**: Jupyter Book für schöne Doku (1-2 Stunden)

---

## Nächste Schritte

- [ ] requirements.txt erstellen
- [ ] Notebooks committen und pushen
- [ ] Binder-Badge generieren
- [ ] README.md aktualisieren
- [ ] (Optional) Jupyter Book einrichten

## Hilfreiche Links

- nbviewer: https://nbviewer.org
- Binder: https://mybinder.org
- Jupyter Book: https://jupyterbook.org
- GitHub Pages: https://pages.github.com
