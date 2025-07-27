import base64, markdown, json
from flask import Flask, request, jsonify
from weasyprint import HTML, CSS

app = Flask(__name__)

@app.post("/render")
def render_pdf():
    body = request.get_json()
    md = body.get("content_md", "")
    html_body = markdown.markdown(md, extensions=["tables"])
    html_full = f"""
    <html><head><meta charset='utf-8'>
    <style>@page{{size:A4;margin:20mm}}body{{font-family:'Times New Roman',serif}}</style>
    </head><body>{html_body}</body></html>"""
    pdf = HTML(string=html_full).write_pdf(
        stylesheets=[CSS(string='img{max-width:100%}')])
    return jsonify({"listing_pdf": base64.b64encode(pdf).decode()})
