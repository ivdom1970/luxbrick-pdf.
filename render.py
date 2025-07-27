def scrape_listing(url: str) -> str:
    """Raccoglie titolo, prezzo, testo, 6 miniature, 2 foto grandi e planimetria."""
    html = requests.get(url, timeout=10,
                        headers={"User-Agent": "Mozilla/5.0"}).text
    soup = bs4.BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").get_text(strip=True)
    price = soup.select_one(".price").get_text(strip=True) if soup.select_one(".price") else ""
    desc  = soup.select_one('meta[name=description]')["content"] if soup.select_one('meta[name=description]') else ""

    # prende tutte le immagini jpg/png
    imgs_all = [img["src"] for img in soup.select("img")
                if re.search(r"\.(jpe?g|png)$", img.get("src",""), re.I)]
    cover, *rest = imgs_all + [""]*9   # riempie con stringhe vuote se mancano
    mini   = rest[:6]                  # 6 miniature
    hero1  = rest[6]
    hero2  = rest[7]
    plan   = next((u for u in imgs_all if re.search(r"(plan|floor)", u, re.I)), "")

    md = f"""
![cover]({cover})

# {title}

**{price}**

{desc}

---

{"".join(f"![mini]({u})" for u in mini)}

![hero1]({hero1})

![hero2]({hero2})

{'![planimetria](' + plan + ')' if plan else ''}
"""
    return md
