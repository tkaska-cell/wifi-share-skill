---
name: wifi-share
description: WiFi認証情報から「カメラでスキャン→ワンタップ接続」できる接続QRポスターを生成し、Vercelで公開URL(*.vercel.app)にして会場の人に共有する。「WiFi共有」「会場のWiFiをQRで」「ゲストWiFiのページ作って」「WiFiの接続ページ公開して」等の文脈で使用。
argument-hint: [SSID password / WIFI:S:...;P:...;; / 省略で直近メッセージから抽出]
disable-model-invocation: true
allowed-tools: Read Write Edit Bash Glob
---

# wifi-share — WiFi接続QRポスターをVercel公開

会場の人に「カメラでQRを読むだけでワンタップ接続」できるページを作り、
公開URL（`*.vercel.app`）にして共有する。iPhone/Android両対応の標準WiFi QR形式。

## 引数

`$ARGUMENTS` から接続情報を取る。以下のいずれの形式でも受け付ける:
- **WIFI QR文字列**: `WIFI:S:TS-GUEST-A;T:WPA;P:77k3mzsbjp;;`（`S:`=SSID, `T:`=認証方式, `P:`=パスワード）
- **SSID＋パスワード**: `TS-GUEST-A 77k3mzsbjp` や「SSID: xxx / PW: yyy」など自由文
- **省略時**: 会話の直近メッセージから WiFi 情報（`WIFI:S:...` 文字列や SSID/PW の記載）を抽出する

抽出できない・曖昧な場合のみ、SSID・パスワード・認証方式(WPA既定)を1回だけ確認する。

## Step 1: 接続情報を確定

- WIFI文字列なら `S:` `T:` `P:` を分解（バックスラッシュエスケープを解除）。`T:` 既定は `WPA`（パスワード無しは `nopass`）
- SSID/PWだけなら認証方式は `WPA` とみなす
- 確定した SSID / パスワード / 認証方式 をユーザーに1行で提示（誤り検知のため）

## Step 2: 配置先ディレクトリを決める

グローバルCLAUDE.mdの配置ルールに従う。**判断つかなければ「仕事(AIVEST)/副業(FERMENT U)/ライフワーク どれの会場ですか？」と確認**:
- 仕事(AIVEST/CC/PABLOS) → `~/Desktop/ClaudeCode/work/venue-wifi/`（複数会場を扱うなら `work/venue-wifi/<会場名>/`）
- 副業 → `~/Desktop/ClaudeCode/ferment-u/venue-wifi/`
- ライフワーク → `~/Desktop/ClaudeCode/lifework/venue-wifi/`

`<project>/public/` を作業ディレクトリにする。

## Step 3: ポスターHTML＋QRを生成（QR健全性を自己検証）

```bash
python3 ~/.claude/skills/wifi-share/scripts/build_poster.py \
  --ssid "<SSID>" --password "<PW>" --auth "<WPA|WEP|nopass>" \
  --venue "<会場名/空文字>" \
  --lang "<ja|en|zh|ko|es>" --langs "ja,en,zh,ko,es" \
  --outdir "<project>/public" \
  --qr-png "<project>/public/wifi_qr.png" \
  --project-dir "<project>"
```

- **言語スイッチャ内蔵**: ポスター上部に 日本語/English/中文/한국어/Español のボタン。ゲストがタップで即切替（リロード無し・印刷は選択中の言語で出力）
- `--langs` 並べる言語（既定 `ja,en,zh,ko,es`）／`--lang` 初期表示（既定 `ja`）。国内向けでも海外ゲスト対応で全部入れておいてよい
- QR下に**カメラアプリ案内**（iPhone=標準カメラ／Android=カメラ/フォトアプリ）を各言語で表示
- `?lang=en` のようにURLで初期言語を指定した共有リンクも作れる

- スクリプトは QR PNG を base64 roundtrip ＋ PIL load で自己検証してから埋め込む
  （🚨 **過去にQRが途中破損して真っ黒表示になった事故あり**＝この検証は外さない）
- ポスターHTMLには `noindex,nofollow` メタを自動付与、`--project-dir` 指定で
  セキュリティヘッダー付き `vercel.json`（X-Robots-Tag / nosniff / no-referrer / X-Frame-Options DENY）を自動生成
- `OK payload=... / WROTE ... VERCEL_JSON=...` が出れば成功

## Step 4: デプロイ前にローカル描画で目視確認（必須）

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
  --screenshot=/tmp/wifi_local.png --window-size=500,900 --hide-scrollbars \
  "file://<project>/public/index.html"
```
スクショを Read で開き、**QRが正しく市松模様で表示されているか**を必ず目視する。
真っ黒・途中欠けなら Step 3 からやり直し（デプロイに進まない）。

## Step 5: Vercelで公開

1. CLIとログイン確認:
   ```bash
   vercel --version || npm install -g vercel
   vercel whoami
   ```
2. 未ログインなら、ユーザーに次を依頼（対話式のため本人が実行）:
   > プロンプトに `! vercel login` を貼って実行してください。メールは公開物の帰属に合わせて選択（AIVEST=tkaska@h-bb.jp）。
   ログイン完了を待ってから続行。
3. 本番デプロイ（🔒 **推測されにくいURL**にするためランダムsuffixを付ける）:
   ```bash
   SUFFIX=$(openssl rand -hex 3)
   cd <project> && vercel deploy --prod --yes --name "venue-wifi-$SUFFIX"
   ```
   出力の `Production https://venue-wifi-xxxxxx.vercel.app` を本番URLとして控える。
   （🚨 デフォルトでProductionは認証ゲート無し＝誰でも閲覧可。Preview保護は関係ない）
   ※ 会場ごとに使い回すなら `--name` を固定してもよいが、URLが推測されにくい方が安全

## Step 6: ライブURLを描画確認 → 報告

```bash
sleep 3
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
  --screenshot=/tmp/wifi_live.png --window-size=500,900 --hide-scrollbars \
  "https://<本番URL>?v=1"
```
スクショを Read で目視し、QR＋SSID＋PWが正しく出ていれば完了。
`curl -sI <URL>` で以下を確認:
- `HTTP/2 200` で表示される
- SSO Cookie（`_vercel_sso`）が無い（認証ゲート無し＝公開OK）
- 🔒 `x-robots-tag: noindex, nofollow` が返る（検索エンジンに拾われない＝vercel.jsonが効いている）

印刷用に QR 単体PNGを Finder表示: `open -R "<project>/public/wifi_qr.png"`

## 出力（ユーザーへの報告）

```
🔗 <本番URL>
- カメラでQRを読む → ワンタップ接続（iPhone/Android対応）
- SSID/パスワードのコピー機能・手動接続手順つき
- QR単体PNG: <project>/public/wifi_qr.png（印刷用・Finderで開いています）
```
※ 実機で一度スキャン接続テストを促す（印刷/画面サイズで読み取りやすさが変わるため）。

## 更新・停止

- **接続情報変更/別会場**: Step 3 を新しい引数で再実行 → `cd <project> && vercel deploy --prod --yes`（同じURLのまま更新）
- **公開停止**: `cd <project> && vercel remove venue-wifi --yes`

## 🔒 セキュリティ対策（既定で組み込み済み）

WiFiパスワードを公開URLに載せる性質上、以下を標準で施す:

1. **検索エンジン非掲載**: ポスターに `noindex,nofollow` メタ＋ `X-Robots-Tag` ヘッダー（vercel.json）。Google等にパスワードがインデックスされない
2. **推測されにくいURL**: プロジェクト名に `openssl rand -hex 3` のランダムsuffix。総当たりで見つけにくくする
3. **セキュリティヘッダー**: `X-Content-Type-Options: nosniff` / `Referrer-Policy: no-referrer` / `X-Frame-Options: DENY`（他サイトへの埋め込み=clickjacking防止）
4. **短命運用の推奨**: イベント終了後は `vercel remove <name> --yes` で確実に削除。長期放置しない
5. **載せてよい情報の線引き**: 会場に掲示・配布する前提の**ゲスト用**WiFiのみ。自宅・オフィスの常用WiFiや、社内ネットワークの認証情報は公開URLに載せない → その場合は**ローカルHTML/印刷用PNGのみ**で渡す
6. **QRの中身はパスワードそのもの**: QR画像を公開SNS等に貼ることは、パスワードを平文で貼るのと同じ。掲示範囲を意識する

判断に迷う認証情報（自宅・社内等）が来たら、公開せず「ローカル配布のみ」を提案してから進める。

## 注意事項

- 🚨 **仕事(AIVEST/CC/PABLOS)の公開物に ferment-u ドメインを使わない**（`unlisted-html-publish`のCloudflareはFERMENT U専用）。仕事の会場は Vercel の中立ドメイン一択
- 🚨 QRの健全性検証（Step 3）とデプロイ前後の描画目視（Step 4/6）は省略しない
- Vercelアカウントは公開物の帰属に合わせる（AIVEST=tkaska@h-bb.jp）
