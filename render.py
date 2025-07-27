import io, os, time, re, base64, requests, markdown, bs4
from flask import Flask, request, jsonify, send_from_directory
from weasyprint import HTML, CSS

app = Flask(__name__)

# ---------- Helpers ----------------------------------------------------------
def scrape_listing(url: str) -> str:
    """Raccoglie titolo, prezzo, descrizione, 6 miniature, 2 foto grandi e planimetria."""
    html = requests.get(url, timeout=10,
                        headers={"User-Agent": "Mozilla/5.0"}).text
    soup = bs4.BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").get_text(strip=True)
    price = soup.select_one(".price").get_text(strip=True) if soup.select_one(".price") else ""
    desc  = soup.select_one('meta[name=description]')["content"] if soup.select_one('meta[name=description]') else ""

    # tutte le immagini jpg/png
    imgs_all = [img["src"] for img in soup.select("img")
                if re.search(r"\.(jpe?g|png)$", img.get("src",""), re.I)]
    cover, *rest = imgs_all + [""]*9          # filler stringhe vuote
    mini   = rest[:6]
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
    return md.strip()


def markdown_to_pdf(md: str) -> bytes:
    html = markdown.markdown(md, extensions=["tables"])
    css  = """
      @page { size:A4; margin:12mm 16mm; }
      body { font-family:'Times New Roman', serif; }
      img[alt=cover] { width:100%; height:9cm; object-fit:cover; margin-bottom:12pt; }
      img[alt=mini]  { width:30%; display:inline-block; margin:2pt; }
      img[alt=hero1], img[alt=hero2] { width:100%; margin:12pt 0; }
      h1 { font-size:26pt; margin:18pt 0 6pt 0; }
    """
    return HTML(string=html).write_pdf(stylesheets=[CSS(string=css)])

# ---------- API endpoints ----------------------------------------------------
@app.post("/render")
def render_pdf():
    """
    riceve  { "listing_url": "<url annuncio luxurybrick>" }
    restituisce { download_url, listing_pdf(base64) }
    """
    body = request.get_json(force=True)
    url  = body.get("listing_url")
    if not url:
        return jsonify({"error": "listing_url is required"}), 400

    md  = scrape_listing(url)
    pdf = markdown_to_pdf(md)

    fname = f"/tmp/{int(time.time())}.pdf"
    with open(fname, "wb") as f:
        f.write(pdf)

    download_url = request.url_root.rstrip("/") + f"/tmp/{os.path.basename(fname)}"
    return jsonify({
        "download_url": download_url,
        "listing_pdf": base64.b64encode(pdf).decode()
    })

# -- serve i file salvati in /tmp --------------------------------------------
@app.get("/tmp/<fname>")
def tmp_file(fname):
    return send_from_directory(
        "/tmp",
        fname,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="listing.pdf"
    )

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
