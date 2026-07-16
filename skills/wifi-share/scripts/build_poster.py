#!/usr/bin/env python3
"""WiFi接続QRポスター生成スクリプト（多言語スイッチャ対応）。

認証情報からWiFi QR(PNG)を生成し、健全性を検証したうえで
接続ポスター index.html（QRをdata URIで埋め込み・言語切替つき）を出力する。

使い方:
  python3 build_poster.py --ssid TS-GUEST-A --password 77k3mzsbjp \
      --auth WPA --venue "AIVEST" --lang ja --langs ja,en,zh,ko,es \
      --outdir /path/to/project/public --project-dir /path/to/project

- 画面上の言語ボタンで 日本語/English/中文/한국어/Español を即切替（リロード無し）
- QRが壊れて表示されない事故を防ぐため、生成後に必ず base64 roundtrip と PIL load で自己検証する
- ?lang=en のようにURLで初期言語を指定して共有することも可能
"""
import argparse, base64, io, json, os, sys


def wifi_escape(s: str) -> str:
    """WiFi QR仕様のエスケープ（\\ ; , " : をバックスラッシュ）。"""
    out = []
    for ch in s:
        if ch in '\\;,":':
            out.append('\\' + ch)
        else:
            out.append(ch)
    return ''.join(out)


def build_qr_datauri(payload: str):
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


# UI文言（言語別）。海外ゲストのいる会場で使えるよう代表的な言語を用意。
STRINGS = {
    "ja": {
        "autonym": "日本語",
        "headline": "Wi‑Fiにつなぐ",
        "sub": "スマホのカメラでQRを読み取るだけ",
        "qr_alt": "Wi‑Fi接続用QRコード",
        "scan_hint": "カメラを向けて、表示される通知をタップ",
        "app_hint": "📷 iPhoneは標準カメラ／Androidはカメラまたはフォトアプリで読み取り",
        "label_network": "ネットワーク名",
        "label_password": "パスワード",
        "copy": "コピー",
        "copy_done": "コピー済み",
        "manual_title": "手動で接続する場合",
        "manual_body": "設定 → Wi‑Fi → <b>{ssid}</b> を選び、上のパスワードを入力してください。",
        "eyebrow": "ゲスト Wi‑Fi",
        "title_venue": "{venue} Wi‑Fi",
        "title_default": "ゲストWi‑Fi ご案内",
    },
    "en": {
        "autonym": "English",
        "headline": "Connect to Wi‑Fi",
        "sub": "Just point your phone camera at the QR code",
        "qr_alt": "Wi‑Fi connection QR code",
        "scan_hint": "Point your camera at the code and tap the notification",
        "app_hint": "📷 iPhone: Camera app · Android: Camera or Google Lens",
        "label_network": "Network",
        "label_password": "Password",
        "copy": "Copy",
        "copy_done": "Copied",
        "manual_title": "Connect manually",
        "manual_body": "Settings → Wi‑Fi → <b>{ssid}</b>, then enter the password above.",
        "eyebrow": "Guest Wi‑Fi",
        "title_venue": "{venue} Wi‑Fi",
        "title_default": "Guest Wi‑Fi",
    },
    "zh": {
        "autonym": "中文",
        "headline": "连接 Wi‑Fi",
        "sub": "用手机相机扫描二维码即可",
        "qr_alt": "Wi‑Fi 连接二维码",
        "scan_hint": "将相机对准二维码，点击弹出的通知",
        "app_hint": "📷 iPhone：相机 App／Android：相机或扫一扫",
        "label_network": "网络名称",
        "label_password": "密码",
        "copy": "复制",
        "copy_done": "已复制",
        "manual_title": "手动连接",
        "manual_body": "设置 → Wi‑Fi → <b>{ssid}</b>，然后输入上面的密码。",
        "eyebrow": "访客 Wi‑Fi",
        "title_venue": "{venue} Wi‑Fi",
        "title_default": "访客 Wi‑Fi",
    },
    "ko": {
        "autonym": "한국어",
        "headline": "Wi‑Fi 연결하기",
        "sub": "스마트폰 카메라로 QR을 비추기만 하면 돼요",
        "qr_alt": "Wi‑Fi 연결용 QR 코드",
        "scan_hint": "카메라를 대고 표시되는 알림을 탭하세요",
        "app_hint": "📷 iPhone: 기본 카메라 / Android: 카메라 또는 QR 앱",
        "label_network": "네트워크 이름",
        "label_password": "비밀번호",
        "copy": "복사",
        "copy_done": "복사됨",
        "manual_title": "수동으로 연결하기",
        "manual_body": "설정 → Wi‑Fi → <b>{ssid}</b> 선택 후 위 비밀번호를 입력하세요.",
        "eyebrow": "게스트 Wi‑Fi",
        "title_venue": "{venue} Wi‑Fi",
        "title_default": "게스트 Wi‑Fi",
    },
    "es": {
        "autonym": "Español",
        "headline": "Conéctate al Wi‑Fi",
        "sub": "Solo apunta la cámara del móvil al código QR",
        "qr_alt": "Código QR para conectarse al Wi‑Fi",
        "scan_hint": "Apunta la cámara al código y toca la notificación",
        "app_hint": "📷 iPhone: app Cámara · Android: Cámara o Google Lens",
        "label_network": "Red",
        "label_password": "Contraseña",
        "copy": "Copiar",
        "copy_done": "Copiado",
        "manual_title": "Conexión manual",
        "manual_body": "Ajustes → Wi‑Fi → <b>{ssid}</b>, luego introduce la contraseña de arriba.",
        "eyebrow": "Wi‑Fi para invitados",
        "title_venue": "{venue} Wi‑Fi",
        "title_default": "Wi‑Fi para invitados",
    },
}


HTML_TEMPLATE = """<title>{title}</title>
<meta name="robots" content="noindex, nofollow" />
<meta name="referrer" content="no-referrer" />
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
    font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP","Noto Sans KR","Noto Sans SC","Segoe UI",sans-serif;
    display:flex; align-items:center; justify-content:center; padding:32px 20px;
    -webkit-font-smoothing:antialiased;
  }}
  .card {{
    width:100%; max-width:440px; background:var(--card); border:1px solid var(--line);
    border-radius:22px; box-shadow:var(--shadow); padding:22px 36px 34px; text-align:center;
  }}
  .langbar {{ display:flex; flex-wrap:wrap; justify-content:center; gap:6px; margin-bottom:20px; }}
  .lang {{
    border:1px solid var(--line); background:var(--card); color:var(--muted);
    font-size:12px; font-weight:700; padding:5px 11px; border-radius:20px; cursor:pointer;
    transition:background .15s,color .15s,border-color .15s;
  }}
  .lang:hover {{ border-color:var(--accent); color:var(--accent); }}
  .lang:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
  .lang.active {{ background:var(--accent); color:var(--accent-ink); border-color:var(--accent); }}
  .eyebrow {{ font-size:12px; letter-spacing:.16em; text-transform:uppercase; color:var(--accent); font-weight:800; margin:0 0 6px; }}
  h1 {{ font-size:30px; line-height:1.15; margin:0 0 4px; letter-spacing:-.01em; text-wrap:balance; }}
  .sub {{ margin:0 0 4px; color:var(--muted); font-size:14px; }}
  .qr {{ width:232px; height:232px; margin:18px auto 8px; padding:14px; background:#fff; border-radius:16px; border:1px solid var(--line); }}
  .qr img {{ width:100%; height:100%; display:block; image-rendering:pixelated; }}
  .scan-hint {{ font-size:13px; color:var(--muted); margin:0 0 6px; }}
  .app-hint {{ font-size:12px; color:var(--muted); margin:0 0 22px; opacity:.9; }}
  .fields {{ display:flex; flex-direction:column; gap:10px; text-align:left; margin-bottom:20px; }}
  .field {{ display:flex; align-items:center; justify-content:space-between; gap:12px; background:var(--field); border:1px solid var(--line); border-radius:12px; padding:12px 14px; }}
  .field .label {{ font-size:11px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); font-weight:700; margin-bottom:3px; }}
  .field .value {{ font-family:ui-monospace,"SF Mono","Menlo",monospace; font-size:18px; font-weight:600; letter-spacing:.02em; word-break:break-all; }}
  .copy {{ flex:none; border:1px solid var(--line); background:var(--card); color:var(--accent); font-weight:700; font-size:13px; padding:8px 14px; border-radius:9px; cursor:pointer; transition:background .15s,color .15s,border-color .15s; }}
  .copy:hover {{ background:var(--accent); color:var(--accent-ink); border-color:var(--accent); }}
  .copy:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
  .copy.done {{ background:var(--accent); color:var(--accent-ink); border-color:var(--accent); }}
  .steps {{ text-align:left; border-top:1px solid var(--line); padding-top:18px; color:var(--muted); font-size:13px; line-height:1.7; }}
  .steps b {{ color:var(--ink); }}
  @media print {{ body {{ background:#fff; }} .card {{ box-shadow:none; border-color:#ccc; }} .copy,.langbar {{ display:none; }} }}
</style>

<div class="card">
  <div class="langbar" id="langbar">{switcher_html}</div>
  <p class="eyebrow" data-i18n="eyebrow">{eyebrow_html}</p>
  <h1 data-i18n="headline">{h_headline}</h1>
  <p class="sub" data-i18n="sub">{h_sub}</p>

  <div class="qr">
    <img id="qrImg" alt="{qr_alt}" src="{qr_src}" />
  </div>
  <p class="scan-hint" data-i18n="scan_hint">{h_scan}</p>
  <p class="app-hint" data-i18n="app_hint">{h_app}</p>

  <div class="fields">
    <div class="field">
      <div>
        <div class="label" data-i18n="label_network">{h_net}</div>
        <div class="value" id="ssid">{ssid}</div>
      </div>
      <button class="copy" data-target="ssid" data-i18n="copy" type="button">{h_copy}</button>
    </div>
    <div class="field">
      <div>
        <div class="label" data-i18n="label_password">{h_pass}</div>
        <div class="value" id="pass">{password}</div>
      </div>
      <button class="copy" data-target="pass" data-i18n="copy" type="button">{h_copy}</button>
    </div>
  </div>

  <div class="steps">
    <b data-i18n="manual_title">{h_manual_title}</b><br>
    <span data-i18n="manual_body">{h_manual_body}</span>
  </div>
</div>

<script>
  var I18N = {i18n_json};
  var LANGS = Object.keys(I18N);
  var cur = "{default_lang}";

  function applyLang(lang) {{
    if (!I18N[lang]) return;
    cur = lang;
    var dict = I18N[lang];
    document.querySelectorAll("[data-i18n]").forEach(function (el) {{
      var k = el.getAttribute("data-i18n");
      if (dict[k] != null) el.innerHTML = dict[k];
    }});
    var qr = document.getElementById("qrImg");
    if (qr && dict.qr_alt) qr.setAttribute("alt", dict.qr_alt);
    if (dict.title) document.title = dict.title;
    document.documentElement.setAttribute("lang", lang);
    document.querySelectorAll(".lang").forEach(function (b) {{
      b.classList.toggle("active", b.getAttribute("data-lang") === lang);
    }});
  }}

  document.querySelectorAll(".lang").forEach(function (b) {{
    b.addEventListener("click", function () {{ applyLang(b.getAttribute("data-lang")); }});
  }});

  document.querySelectorAll(".copy").forEach(function (btn) {{
    btn.addEventListener("click", function () {{
      var text = document.getElementById(btn.dataset.target).textContent.trim();
      navigator.clipboard.writeText(text).then(function () {{
        var original = btn.textContent;
        btn.textContent = (I18N[cur] && I18N[cur].copy_done) || "OK";
        btn.classList.add("done");
        setTimeout(function () {{ btn.textContent = original; btn.classList.remove("done"); }}, 1500);
      }});
    }});
  }});

  // URLで初期言語を指定できる（例: ?lang=en）。無ければ既定言語。
  var q = (location.search.match(/[?&]lang=([a-z]{{2}})/) || [])[1];
  if (q && I18N[q]) applyLang(q);
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
    ap.add_argument("--project-dir", default="",
                    help="Vercelプロジェクトルート。指定するとセキュリティヘッダー付き vercel.json を出力")
    ap.add_argument("--lang", default="ja", choices=sorted(STRINGS.keys()),
                    help="初期表示言語（既定 ja）")
    ap.add_argument("--langs", default="ja,en,zh,ko,es",
                    help="言語スイッチャに並べる言語（カンマ区切り。既定 ja,en,zh,ko,es）")
    args = ap.parse_args()

    langs = [l.strip() for l in args.langs.split(",") if l.strip() in STRINGS]
    if not langs:
        langs = ["ja"]
    default_lang = args.lang if args.lang in langs else langs[0]

    payload = "WIFI:S:{s};T:{t};P:{p};;".format(
        s=wifi_escape(args.ssid), t=args.auth, p=wifi_escape(args.password)
    )
    qr_src, img = build_qr_datauri(payload)

    ssid_esc = html_escape(args.ssid)
    venue_esc = html_escape(args.venue)

    # 言語別の完成済み辞書（manual_body に ssid を差し込み、eyebrow は会場名を前置）
    i18n = {}
    for lang in langs:
        s = STRINGS[lang]
        title = s["title_venue"].format(venue=args.venue) if args.venue else s["title_default"]
        i18n[lang] = {
            "headline": s["headline"],
            "sub": s["sub"],
            "qr_alt": s["qr_alt"],
            "scan_hint": s["scan_hint"],
            "app_hint": s["app_hint"],
            "label_network": s["label_network"],
            "label_password": s["label_password"],
            "copy": s["copy"],
            "copy_done": s["copy_done"],
            "manual_title": s["manual_title"],
            "manual_body": s["manual_body"].format(ssid=ssid_esc),
            "eyebrow": (venue_esc + " · " + s["eyebrow"]) if args.venue else s["eyebrow"],
            "title": title,
        }

    d = i18n[default_lang]
    switcher_html = "".join(
        '<button class="lang{active}" data-lang="{code}" type="button">{name}</button>'.format(
            active=(" active" if lang == default_lang else ""),
            code=lang, name=STRINGS[lang]["autonym"],
        )
        for lang in langs
    )

    html = HTML_TEMPLATE.format(
        title=html_escape(d["title"]),
        default_lang=default_lang,
        switcher_html=switcher_html,
        eyebrow_html=d["eyebrow"],
        qr_src=qr_src,
        qr_alt=html_escape(d["qr_alt"]),
        ssid=ssid_esc,
        password=html_escape(args.password),
        h_headline=d["headline"],
        h_sub=d["sub"],
        h_scan=d["scan_hint"],
        h_app=d["app_hint"],
        h_net=d["label_network"],
        h_pass=d["label_password"],
        h_copy=d["copy"],
        h_manual_title=d["manual_title"],
        h_manual_body=d["manual_body"],
        i18n_json=json.dumps(i18n, ensure_ascii=False),
    )

    os.makedirs(args.outdir, exist_ok=True)
    out = os.path.join(args.outdir, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    if args.qr_png:
        os.makedirs(os.path.dirname(args.qr_png) or ".", exist_ok=True)
        img.save(args.qr_png)

    if args.project_dir:
        # セキュリティヘッダー: 検索非掲載・MIMEスニッフ防止・リファラ抑止・埋め込み(clickjacking)防止
        vjson = (
            '{\n'
            '  "headers": [\n'
            '    {\n'
            '      "source": "/(.*)",\n'
            '      "headers": [\n'
            '        { "key": "X-Robots-Tag", "value": "noindex, nofollow" },\n'
            '        { "key": "X-Content-Type-Options", "value": "nosniff" },\n'
            '        { "key": "Referrer-Policy", "value": "no-referrer" },\n'
            '        { "key": "X-Frame-Options", "value": "DENY" }\n'
            '      ]\n'
            '    }\n'
            '  ]\n'
            '}\n'
        )
        os.makedirs(args.project_dir, exist_ok=True)
        with open(os.path.join(args.project_dir, "vercel.json"), "w", encoding="utf-8") as f:
            f.write(vjson)

    print("OK payload=" + payload + " langs=" + ",".join(langs) + " default=" + default_lang)
    print("WROTE " + out + (" QR_PNG=" + args.qr_png if args.qr_png else "")
          + (" VERCEL_JSON=" + os.path.join(args.project_dir, "vercel.json") if args.project_dir else ""))


if __name__ == "__main__":
    main()
