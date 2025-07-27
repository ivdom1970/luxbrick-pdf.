import io, os, time, re, base64, requests, markdown, bs4
from flask import Flask, request, jsonify, send_from_directory  # ← import completo
from weasyprint import HTML, CSS

app = Flask(__name__)

# ---------- Helpers ----------------------------------------------------------
def scrape_listing(url: str) -> str:
    html = requests.get(url, timeout=10,
                        headers={"User-Agent": "Mozilla/5.0"}).text
    soup = bs4.BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").get_text(strip=True)
    price = soup.select_one(".price").get_text(strip=True) if soup.select_one(".price") else ""
    desc  = soup.select_one('meta[name=description]')["content"] if soup.select_one('meta[name=description]') else ""

    imgs = [img["src"] for img in soup.select("img")
            if re.search(r"\.(jpe?g|png)$", img.get("src", ""), re.I)][:6]

    md = f"# {title}\n\n**{price}**\n\n{desc}\n\n" + "\n".join(f"![img]({u})" for u in imgs)
    return md

def markdown_to_pdf(md: str) -> bytes:
    html = markdown.markdown(md, extensions=["tables"])
    css  = "@page{size:A4;margin:20mm}"
    return HTML(string=html).write_pdf(stylesheets=[CSS(string=css)])

# ---------- API endpoints ----------------------------------------------------
@app.post("/render")
def render_pdf():
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

# --- nuovo endpoint che serve i file /tmp -----------------------------------
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
