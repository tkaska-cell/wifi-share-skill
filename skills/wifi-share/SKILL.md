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
  --outdir "<project>/public" \
  --qr-png "<project>/public/wifi_qr.png"
```

スクリプトは QR PNG を base64 roundtrip ＋ PIL load で自己検証してから埋め込む
（🚨 **過去にQRが途中破損して真っ黒表示になった事故あり**＝この検証は外さない）。
`OK payload=... / WROTE ...` が出れば成功。

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
3. 本番デプロイ:
   ```bash
   cd <project> && vercel deploy --prod --yes --name venue-wifi
   ```
   出力の `Aliased https://venue-wifi.vercel.app` などの本番URLを控える。
   （🚨 デフォルトでProductionは認証ゲート無し＝誰でも閲覧可。Preview保護は関係ない）

## Step 6: ライブURLを描画確認 → 報告

```bash
sleep 3
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
  --screenshot=/tmp/wifi_live.png --window-size=500,900 --hide-scrollbars \
  "https://<本番URL>?v=1"
```
スクショを Read で目視し、QR＋SSID＋PWが正しく出ていれば完了。
`curl -sI <URL>` で `HTTP/2 200` と SSO Cookie（`_vercel_sso`）が無いことも確認（認証ゲート無し＝公開OK）。

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

## 注意事項

- 🚨 **仕事(AIVEST/CC/PABLOS)の公開物に ferment-u ドメインを使わない**（`unlisted-html-publish`のCloudflareはFERMENT U専用）。仕事の会場は Vercel の中立ドメイン一択
- 🚨 QRの健全性検証（Step 3）とデプロイ前後の描画目視（Step 4/6）は省略しない
- パスワードは会場掲示前提の共有情報。個人宅の常用WiFi等、外部公開が不適切なら公開せずローカルHTML/PNGのみで渡す
- Vercelアカウントは公開物の帰属に合わせる（AIVEST=tkaska@h-bb.jp）
