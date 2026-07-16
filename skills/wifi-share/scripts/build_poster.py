#!/usr/bin/env python3
"""WiFi接続QRポスター生成スクリプト。

認証情報からWiFi QR(PNG)を生成し、健全性を検証したうえで
接続ポスター index.html（QRをdata URIで埋め込み）を出力する。

使い方:
  python3 build_poster.py --ssid TS-GUEST-A --password 77k3mzsbjp \
      --auth WPA --venue "AIVEST" --outdir /path/to/project/public

QRが壊れて表示されない事故を防ぐため、生成後に必ず
base64 roundtrip と PIL load でPNGの健全性を自己検証する（失敗時は非0終了）。
"""
import argparse, base64, io, os, sys


def wifi_escape(s: str) -> str:
    """WiFi QR仕様のエスケープ（\\ ; , " : をバックスラッシュ）。"""
    out = []
    for ch in s:
        if ch in '\\;,":':
            out.append('\\' + ch)
        else:
            out.append(ch)
    return ''.join(out)


def build_qr_datauri(payload: str) -> str:
    try:
        import qrcode
    except ImportError:
        os.system(f"{sys.executable} -m pip install --break-system-packages --quiet 'qrcode[pil]'")
        import qrcode  # noqa

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10, border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw = buf.getvalue()
    b64 = base64.b64encode(raw).decode()

    # --- 健全性の自己検証（QR破損事故の再発防止）---
    assert base64.b64decode(b64) == raw, "base64 roundtrip mismatch"
    from PIL import Image
    Image.open(io.BytesIO(base64.b64decode(b64))).load()  # 壊れていれば例外

    return "data:image/png;base64," + b64, img


HTML_TEMPLATE = """<title>{title}</title>
<style>
  :root {{
    --bg:#eef1f0; --card:#fff; --ink:#14201d; --muted:#5a6b67; --line:#dbe3e0;
    --accent:#0d8074; --accent-ink:#fff; --field:#f4f7f6;
    --shadow:0 24px 60px -28px rgba(12,40,36,.38);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#0d1412; --card:#16201d; --ink:#e9efec; --muted:#9aaba6; --line:#26332f;
      --accent:#34c3b2; --accent-ink:#06211d; --field:#101917;
      --shadow:0 24px 60px -28px rgba(0,0,0,.6);
    }}
  }}
  :root[data-theme="light"] {{
    --bg:#eef1f0; --card:#fff; --ink:#14201d; --muted:#5a6b67; --line:#dbe3e0;
    --accent:#0d8074; --accent-ink:#fff; --field:#f4f7f6;
    --shadow:0 24px 60px -28px rgba(12,40,36,.38);
  }}
  :root[data-theme="dark"] {{
    --bg:#0d1412; --card:#16201d; --ink:#e9efec; --muted:#9aaba6; --line:#26332f;
    --accent:#34c3b2; --accent-ink:#06211d; --field:#101917;
    --shadow:0 24px 60px -28px rgba(0,0,0,.6);
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; min-height:100vh; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP","Segoe UI",sans-serif;
    display:flex; align-items:center; justify-content:center; padding:32px 20px;
    -webkit-font-smoothing:antialiased;
  }}
  .card {{
    width:100%; max-width:440px; background:var(--card); border:1px solid var(--line);
    border-radius:22px; box-shadow:var(--shadow); padding:40px 36px 34px; text-align:center;
  }}
  .eyebrow {{ font-size:12px; letter-spacing:.22em; text-transform:uppercase; color:var(--accent); font-weight:700; margin:0 0 6px; }}
  h1 {{ font-size:30px; line-height:1.15; margin:0 0 4px; letter-spacing:-.01em; text-wrap:balance; }}
  .sub {{ margin:0 0 26px; color:var(--muted); font-size:14px; }}
  .qr {{ width:232px; height:232px; margin:0 auto 8px; padding:14px; background:#fff; border-radius:16px; border:1px solid var(--line); }}
  .qr img {{ width:100%; height:100%; display:block; image-rendering:pixelated; }}
  .scan-hint {{ font-size:13px; color:var(--muted); margin:0 0 24px; }}
  .fields {{ display:flex; flex-direction:column; gap:10px; text-align:left; margin-bottom:20px; }}
  .field {{ display:flex; align-items:center; justify-content:space-between; gap:12px; background:var(--field); border:1px solid var(--line); border-radius:12px; padding:12px 14px; }}
  .field .label {{ font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); font-weight:700; margin-bottom:3px; }}
  .field .value {{ font-family:ui-monospace,"SF Mono","Menlo",monospace; font-size:18px; font-weight:600; letter-spacing:.02em; word-break:break-all; }}
  .copy {{ flex:none; border:1px solid var(--line); background:var(--card); color:var(--accent); font-weight:700; font-size:13px; padding:8px 14px; border-radius:9px; cursor:pointer; transition:background .15s,color .15s,border-color .15s; }}
  .copy:hover {{ background:var(--accent); color:var(--accent-ink); border-color:var(--accent); }}
  .copy:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
  .copy.done {{ background:var(--accent); color:var(--accent-ink); border-color:var(--accent); }}
  .steps {{ text-align:left; border-top:1px solid var(--line); padding-top:18px; color:var(--muted); font-size:13px; line-height:1.7; }}
  .steps b {{ color:var(--ink); }}
  @media print {{ body {{ background:#fff; }} .card {{ box-shadow:none; border-color:#ccc; }} .copy {{ display:none; }} }}
</style>

<div class="card">
  <p class="eyebrow">{eyebrow}</p>
  <h1>Wi‑Fiにつなぐ</h1>
  <p class="sub">スマホのカメラでQRを読み取るだけ</p>

  <div class="qr">
    <img alt="Wi‑Fi接続用QRコード" src="{qr_src}" />
  </div>
  <p class="scan-hint">カメラを向けて、表示される通知をタップ</p>

  <div class="fields">
    <div class="field">
      <div>
        <div class="label">ネットワーク名</div>
        <div class="value" id="ssid">{ssid}</div>
      </div>
      <button class="copy" data-target="ssid" type="button">コピー</button>
    </div>
    <div class="field">
      <div>
        <div class="label">パスワード</div>
        <div class="value" id="pass">{password}</div>
      </div>
      <button class="copy" data-target="pass" type="button">コピー</button>
    </div>
  </div>

  <div class="steps">
    <b>手動で接続する場合</b><br>
    設定 → Wi‑Fi → <b>{ssid}</b> を選び、上のパスワードを入力してください。
  </div>
</div>

<script>
  document.querySelectorAll(".copy").forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      var text = document.getElementById(btn.dataset.target).textContent.trim();
      navigator.clipboard.writeText(text).then(function () {{
        var original = btn.textContent;
        btn.textContent = "コピー済み";
        btn.classList.add("done");
        setTimeout(function () {{ btn.textContent = original; btn.classList.remove("done"); }}, 1500);
      }});
    }});
  }});
</script>
"""


def html_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssid", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--auth", default="WPA", help="WPA / WEP / nopass")
    ap.add_argument("--venue", default="", help="会場名など（省略可）")
    ap.add_argument("--outdir", required=True, help="public/ ディレクトリ（index.htmlをここに出力）")
    ap.add_argument("--qr-png", default="", help="QR単体PNGの保存先（省略可・印刷用）")
    args = ap.parse_args()

    payload = "WIFI:S:{s};T:{t};P:{p};;".format(
        s=wifi_escape(args.ssid), t=args.auth, p=wifi_escape(args.password)
    )
    qr_src, img = build_qr_datauri(payload)

    eyebrow = (html_escape(args.venue) + " · Guest Wi‑Fi") if args.venue else "Guest Wi‑Fi"
    title = (args.venue + " Wi‑Fi") if args.venue else "ゲストWi‑Fi ご案内"

    html = HTML_TEMPLATE.format(
        title=html_escape(title),
        eyebrow=eyebrow,
        qr_src=qr_src,
        ssid=html_escape(args.ssid),
        password=html_escape(args.password),
    )

    os.makedirs(args.outdir, exist_ok=True)
    out = os.path.join(args.outdir, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    if args.qr_png:
        os.makedirs(os.path.dirname(args.qr_png) or ".", exist_ok=True)
        img.save(args.qr_png)

    print("OK payload=" + payload)
    print("WROTE " + out + (" QR_PNG=" + args.qr_png if args.qr_png else ""))


if __name__ == "__main__":
    main()
