import io, base64, requests, bs4, re, markdown
from flask import Flask, request, jsonify
from weasyprint import HTML, CSS

app = Flask(__name__)

def scrape_listing(url: str) -> str:
    html = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = bs4.BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").get_text(strip=True)
    price = soup.select_one(".price").get_text(strip=True) if soup.select_one(".price") else ""
    desc  = soup.select_one("meta[name=description]")["content"] if soup.select_one("meta[name=description]") else ""

    imgs = [img["src"] for img in soup.select("img") if re.search(r"\.(jpe?g|png)$", img.get("src",""), re.I)]
    imgs = imgs[:6]                 # prime 6 immagini

    md  = f"# {title}\n\n**{price}**\n\n{desc}\n\n" + "\n".join(f"![img]({u})" for u in imgs)
    return md

@app.post("/render")
def render_pdf():
    body = request.get_json()
    url  = body.get("listing_url")
    md   = scrape_listing(url)

    html = markdown.markdown(md, extensions=["tables"])
    pdf  = HTML(string=html).write_pdf(stylesheets=[CSS(string="@page{size:A4;margin:20mm}")])
    return jsonify({"listing_pdf": base64.b64encode(pdf).decode()})
