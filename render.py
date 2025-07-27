import io, os, time, re, base64, requests, markdown, bs4
from flask import Flask, request, jsonify
from weasyprint import HTML, CSS

app = Flask(__name__)

# ---------- Helpers ----------------------------------------------------------

def scrape_listing(url: str) -> str:
    """
    Scarica la pagina LuxuryBrick, estrae titolo, prezzo, descrizione
    e le prime 6 immagini. Ritorna una stringa Markdown pronta.
    """
    html = requests.get(
        url,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0"}
    ).text
    soup = bs4.BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").get_text(strip=True)
    price = (
        soup.select_one(".price").get_text(strip=True)
        if soup.select_one(".price") else ""
    )
    desc = (
        soup.select_one('meta[name=description]')["content"]
        if soup.select_one('meta[name=description]') else ""
    )

    # prime 6 immagini jpeg / png
    imgs = [
        img["src"] for img in soup.select("img")
        if re.search(r"\.(jpe?g|png)$", img.get("src", ""), re.I)
    ][:6]

    md = (
        f"# {title}\n\n"
        f"**{price}**\n\n"
        f"{desc}\n\n"
        + "\n".join(f"![img]({u})" for u in imgs)
    )
    return md

def markdown_to_pdf(md: str) -> bytes:
    html = markdown.markdown(md, extensions=["tables"])
    return HTML(string=html).write_pdf(
        stylesheets=[CSS(string="@page{size:A4;margin:20mm}")]
    )

# ---------- API endpoints ----------------------------------------------------

@app.post("/render")
def render_pdf():
    """
    Body JSON: { "listing_url": "https://luxurybrick.com/immobile/..." }

    Ritorna:
      {
        "download_url": "https://luxbrick-pdf.onrender.com/tmp/1722086459.pdf",
        "listing_pdf": "<base64 PDF>"
      }
    """
    body = request.get_json(force=True)
    url  = body.get("listing_url")
    if not url:
        return jsonify({"error": "listing_url is required"}), 400

    md  = scrape_listing(url)
    pdf = markdown_to_pdf(md)

    # Salva in /tmp per link diretto
    fname = f"/tmp/{int(time.time())}.pdf"
    with open(fname, "wb") as f:
        f.write(pdf)

    download_url = request.url_root.rstrip("/") + f"/tmp/{os.path.basename(fname)}"

    return jsonify({
        "download_url": download_url,
        "listing_pdf": base64.b64encode(pdf).decode()
    })

# -----------------------------------------------------------------------------


if __name__ == "__main__":           # utile se testi in locale
    app.run(host="0.0.0.0", port=8080, debug=True)
