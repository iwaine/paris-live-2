# 🏷️ BALISES HTML DÉTAILLÉES - SoccerStats Live Match

## RÉSUMÉ RAPIDE

| Élément | Balise HTML Exacte | Sélecteur Python |
|---------|-------------------|------------------|
| **Home Team** | `<font style="...color:blue...18px...">` | `soup.find_all('font', style=lambda s: s and 'color:blue' in s and '18px' in s)[0]` |
| **Away Team** | `<font style="...color:blue...18px...">` | `soup.find_all('font', style=lambda s: s and 'color:blue' in s and '18px' in s)[1]` |
| **Score** | `<font style="color:#87CEFA;font-size:26px;...">` | `soup.find('font', style=lambda s: s and '#87CEFA' in s and '26px' in s)` |
| **Minute** | `<font style="font-size:13px;color:#87CEFA;">` | `soup.find('font', style=lambda s: s and '#87CEFA' in s and '13px' in s)` |
| **Possession %** | `<h3>Possession</h3>` puis `<b>49%</b>` | `h3 → parent table → td[width="80"] → b` |
| **Corners** | `<h3>Corners</h3>` puis `<b>3</b>` | `h3 → parent table → td[width="80"] → b` |
| **Shots** | `<h3>Total shots</h3>` puis `<b>5</b>` | `h3 → parent table → td[width="80"] → b` |

---

## 1️⃣ ÉQUIPES (HOME et AWAY)

### ✅ Balise HTML exacte
```html
<font style="font-size:18px;color:blue;font-weight:bold;line-height:28px;">
  RUDAR PRIJEDOR
</font>
```

### Attributs clés
- **style:** `font-size:18px;color:blue;font-weight:bold;line-height:28px;`
- **couleur:** blue
- **taille:** 18px
- **poids:** bold
- **hauteur ligne:** 28px

### Sélecteur CSS
```css
font[style*="color:blue"][style*="18px"][style*="font-weight:bold"]
```

### Sélecteur XPath
```xpath
//font[@style and contains(@style,'color:blue') and contains(@style,'18px')]
```

### Code Python (recommandé)
```python
fonts_blue = soup.find_all('font', 
                           style=lambda s: s and 'color:blue' in s and '18px' in s)
home_team = fonts_blue[0].get_text(strip=True)  # "RUDAR PRIJEDOR"
away_team = fonts_blue[1].get_text(strip=True)  # "ZRINJSKI MOSTAR"
```

---

## 2️⃣ SCORE

### ✅ Balise HTML exacte
```html
<font style="color:#87CEFA;font-size:26px;font-weight:bold;">0:2</font>
```

### Attributs clés
- **style:** `color:#87CEFA;font-size:26px;font-weight:bold;`
- **couleur:** #87CEFA (cyan clair)
- **taille:** 26px (la plus grande)
- **poids:** bold
- **format:** "HOME:AWAY" (ex: "0:2")

### Sélecteur CSS
```css
font[style*="color:#87CEFA"][style*="26px"]
```

### Sélecteur XPath
```xpath
//font[@style and contains(@style,'#87CEFA') and contains(@style,'26px')]
```

### Code Python (recommandé)
```python
score_font = soup.find('font', 
                       style=lambda s: s and '#87CEFA' in s and '26px' in s)
score_text = score_font.get_text(strip=True)  # "0:2"

# Parser le score
import re
m = re.search(r'(\d+)\s*:\s*(\d+)', score_text)
score_home = int(m.group(1))
score_away = int(m.group(2))
```

---

## 3️⃣ MINUTE

### ✅ Balise HTML exacte
```html
<font style="font-size:13px;color:#87CEFA;">90'+1</font>
```

### Attributs clés
- **style:** `font-size:13px;color:#87CEFA;`
- **couleur:** #87CEFA (cyan clair)
- **taille:** 13px (petite)
- **format:** "90'" ou "45'" ou "45+2'" (avec apostrophe et +temps)

### Sélecteur CSS
```css
font[style*="color:#87CEFA"][style*="13px"]
```

### Sélecteur XPath
```xpath
//font[@style and contains(@style,'#87CEFA') and contains(@style,'13px')]
```

### Code Python (recommandé)
```python
minute_fonts = soup.find_all('font', 
                             style=lambda s: s and '#87CEFA' in s and '13px' in s)
minute_text = minute_fonts[0].get_text(strip=True)  # "90'+1"

# Parser la minute
import re
m = re.search(r"(\d{1,2})", minute_text)
minute = int(m.group(1))  # 90
```

---

## 4️⃣ POSSESSION (et autres STATS)

### ✅ Structure HTML complète
```html
<table bgcolor="#cccccc" cellpadding="1" cellspacing="0" width="99%">
  <tr bgcolor="#ffffff">
    <td colspan="3">
      <h3 style="text-align: center; margin-top:3px;">
        Possession
      </h3>
    </td>
  </tr>
  <tr bgcolor="#ffffff" height="24">
    <!-- HOME VALUE -->
    <td align="right" style="padding-right:4px;" valign="middle" width="80">
      <font style="font-size:18px;color:#000000;">
        <b>49%</b>
      </font>
    </td>
    <!-- CHART/BARS -->
    <td align="center">
      <table border="0" cellpadding="1" cellspacing="0" width="220">
        <tr>
          <td align="right">
            <img alt="" height="18" src="img/icons/bar_purple.jpg" width="107.8"/>
          </td>
          <td align="left">
            <img alt="" height="18" src="img/icons/bar_cyan.jpg" width="112.2"/>
          </td>
        </tr>
      </table>
    </td>
    <!-- AWAY VALUE -->
    <td align="left" style="padding-left:4px;" valign="middle" width="80">
      <font style="font-size:18px;color:#000000;">
        <b>51%</b>
      </font>
    </td>
  </tr>
</table>
```

### Éléments clés
- **Header:** `<h3>Possession</h3>` (text exact)
- **Conteneur:** `<table>` parent avec `bgcolor="#cccccc"`
- **Valeurs:** `<font>` + `<b>` dans `<td width="80">`
- **Position:** Home à gauche (td[0]), Away à droite (td[2])

### Code Python (recommandé)
```python
import re

# Chercher le header
stat_name = "Possession"  # ou "Corners", "Total shots", "Shots on target"
h3 = soup.find('h3', string=re.compile(stat_name, re.I))

if h3:
    # Monter jusqu'à la table parent
    parent_table = h3.find_parent('table')
    
    # Extraire les valeurs HOME et AWAY
    tds = parent_table.find_all('td', width='80')
    home_value = tds[0].get_text(strip=True)  # "49%"
    away_value = tds[1].get_text(strip=True)  # "51%"
    
    # Parser la valeur
    home_num = float(home_value.replace('%', ''))  # 49.0
    away_num = float(away_value.replace('%', ''))  # 51.0
```

---

## 📊 TABLEAU COMPLET - TOUS LES SÉLECTEURS

| Section | Balise | Style | Format | Code Python |
|---------|--------|-------|--------|-------------|
| **Home Team** | `<font>` | `color:blue;18px;bold` | Texte | `fonts_blue[0].text` |
| **Away Team** | `<font>` | `color:blue;18px;bold` | Texte | `fonts_blue[1].text` |
| **Score** | `<font>` | `#87CEFA;26px;bold` | "X:Y" | `soup.find('font', style=lambda s: '#87CEFA' in s and '26px' in s)` |
| **Minute** | `<font>` | `#87CEFA;13px` | "90'" | `soup.find('font', style=lambda s: '#87CEFA' in s and '13px' in s)` |
| **Possession** | `<h3>` + `<b>` | `18px;#000;bold` | "49%" | `h3 → parent table → td[width="80"] → b` |
| **Corners** | `<h3>` + `<b>` | `18px;#000;bold` | "3" | `h3 → parent table → td[width="80"] → b` |
| **Total shots** | `<h3>` + `<b>` | `18px;#000;bold` | "5" | `h3 → parent table → td[width="80"] → b` |
| **Shots on target** | `<h3>` + `<b>` | `18px;#000;bold` | "1" | `h3 → parent table → td[width="80"] → b` |

---

## 💡 TIPS SCRAPING ROBUSTE

1. **Équipes**: Chercher les 2 premières `<font>` avec `color:blue` AND `18px`
2. **Score**: Chercher `<font>` avec `#87CEFA` AND `26px` (unique, plus grande)
3. **Minute**: Chercher `<font>` avec `#87CEFA` AND `13px`, parser avec regex `r"(\d{1,2})"`
4. **Stats**: Chercher `<h3>` avec nom stat, monter table parent, extraire `<td width="80">`
5. **Respect robots.txt**: Attendre 3+ secondes entre requêtes
6. **User-Agent**: Utiliser `paris-live-bot/1.0` ou similaire
7. **Gestion d'erreurs**: Tous les champs optionnels sauf équipes/score

---

## ✅ RÉSULTATS VALIDÉS

| Match | Équipes | Score | Minute | Possession | Corners | Shots | SOT |
|-------|---------|-------|--------|------------|---------|-------|-----|
| Bosnia 2026 | ✅ RUDAR/ZRINJSKI | ✅ 0:2 | ✅ 90'+1 | ✅ 49%/51% | ✅ 3/7 | ✅ 5/11 | ✅ 1/4 |
