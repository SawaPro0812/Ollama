# ローカルLLM環境構築手順（Ollama + ELYZA）

学習・開発用に Mac でローカル LLM を動かすための手順書。

## 構成概要

- **Ollama**: macOS にネイティブインストール（Metal GPU で高速動作）
- **モデル**: ELYZA（日本語特化、Apache 2.0、商用利用可）
- **インターフェース**: CLI / REST API / OpenAI 互換 API
- **用途**: 学習・開発時のみ起動、使い終わったら停止

> **なぜ Docker ではなくネイティブ？**
> macOS の Docker Desktop は Apple Silicon の GPU パススルーに対応していないため、
> コンテナ内では CPU 推論にフォールバックし、ネイティブの 1/5〜1/6 の速度になる。
> Mac ではネイティブ実行が定石。将来 AWS (Linux) に移す際は Docker 化する。

## 動作確認環境

- MacBook Air 13 インチ（M4, 2025）
- メモリ 24GB
- macOS Sequoia 15.7.3
- Homebrew インストール済み

## セットアップ

### 1. Ollama インストール

```bash
brew install --cask ollama
```

### 2. 自動起動を無効化（推奨）

学習用なので常駐させない。インストール直後に設定する。

**システム設定 → 一般 → ログイン項目と機能拡張** を開き、
「ログイン時に開く」リストから **Ollama** を選択して `−` で削除。

### 3. Ollama を起動

```bash
open -a Ollama
```

メニューバーに Ollama アイコンが表示されれば OK。
内部で `http://localhost:11434` に API サーバが立ち上がる。

### 4. ELYZA モデルを取得

```bash
ollama pull hf.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:Q4_K_M
```

- ダウンロード容量: 約 5GB
- 量子化レベルの選択肢:
  - `Q4_K_M`（約5GB）← **推奨**。速度と精度のバランス良
  - `Q5_K_M`（約6GB）← 精度をもう少し上げたい時
  - `Q8_0`（約8.5GB）← ほぼフル精度。24GB Mac なら問題なし

### 5. 動作確認

```bash
ollama run hf.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:Q4_K_M
```

対話モードに入る。`/bye` で終了。

```
>>> 日本の首都はどこですか？
東京です。
>>> /bye
```

## 日常の使い方

### 起動

以下のいずれかで起動：

```bash
# GUIアプリとして起動（メニューバー常駐）
open -a Ollama

# またはターミナル前面で起動
ollama serve
```

### 停止

- メニューバー → Ollama アイコン → **Quit Ollama**
- またはターミナルで `killall ollama`

### モデル一覧

```bash
ollama list
```

### モデル削除

```bash
ollama rm hf.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:Q4_K_M
```

### モデルをメモリから降ろす（容量解放）

```bash
ollama stop hf.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:Q4_K_M
```

## API 経由で利用

Ollama は OpenAI 互換 API を提供するため、OpenAI SDK のベースURLを差し替えるだけで使える。

### curl で叩く

```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hf.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:Q4_K_M",
    "messages": [
      {"role": "user", "content": "次の文章を3行で要約してください: ..."}
    ]
  }'
```

### Python (OpenAI SDK)

```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # ダミー値でOK
)

response = client.chat.completions.create(
    model="hf.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:Q4_K_M",
    messages=[
        {"role": "system", "content": "あなたは日本語の分析アシスタントです。"},
        {"role": "user", "content": "次のテキストを要約してキーワードを抽出してください: ..."}
    ]
)
print(response.choices[0].message.content)
```

### 別マシン（LAN内）から叩く場合

デフォルトでは `localhost` のみ受け付けるので、LAN 内に公開する設定が必要：

```bash
# Ollama を全インターフェースで listen させる
launchctl setenv OLLAMA_HOST "0.0.0.0:11434"

# Ollama を再起動
killall ollama
open -a Ollama
```

別マシンからは `http://<MacのLAN内IP>:11434/v1` でアクセス。

> **⚠️ セキュリティ注意**
> Ollama は標準で認証なし。外部公開する場合は必ずリバースプロキシ + 認証を挟むこと。
> 学習用途では LAN 内のみ + ファイアウォール設定を推奨。

## （任意）Open WebUI を追加

ChatGPT 風 UI でブラウザから操作したい場合、Open WebUI を Docker で立てる。

`docker-compose.yml`:

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    volumes:
      - open_webui_data:/app/backend/data
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  open_webui_data:
```

```bash
docker compose up -d
```

ブラウザで `http://localhost:3000` にアクセス。

停止：

```bash
docker compose down
```

## アンインストール

完全に消す場合、以下を順に実行。

```bash
# 1. プロセス終了
killall ollama 2>/dev/null

# 2. アプリ削除
brew uninstall --cask ollama

# 3. モデル・設定・ログ削除
rm -rf ~/.ollama \
       ~/Library/LaunchAgents/com.ollama.* \
       ~/Library/Logs/Ollama \
       ~/Library/Application\ Support/Ollama \
       ~/Library/Saved\ Application\ State/com.electron.ollama.savedState
```

または一気にワンライナーで：

```bash
killall ollama 2>/dev/null; \
brew uninstall --cask ollama 2>/dev/null; \
rm -rf /Applications/Ollama.app \
       ~/.ollama \
       ~/Library/LaunchAgents/com.ollama.* \
       ~/Library/Logs/Ollama \
       ~/Library/Application\ Support/Ollama \
       ~/Library/Saved\ Application\ State/com.electron.ollama.savedState
```

## トラブルシューティング

### 起動しているか確認

```bash
curl http://localhost:11434/api/tags
```

JSON が返れば起動中。`Connection refused` なら未起動。

### ポート競合

```bash
lsof -i :11434
```

別プロセスが占有していたら停止する。

### モデルがメモリに残り続ける

デフォルトで 5 分間メモリに保持される。即時解放したい場合：

```bash
ollama stop <モデル名>
```

または環境変数で常に即時解放：

```bash
launchctl setenv OLLAMA_KEEP_ALIVE "0"
```

（再ロードでレスポンスが遅くなるので注意）

### 動作が遅い

- アクティビティモニタの「GPU 履歴」を確認し、GPU が動いているかチェック
- GPU が動いていない場合は Ollama を再起動
- それでも遅いならモデルサイズを下げる（Q5 → Q4 など）

## 他のモデルを試す

24GB Mac で動く日本語特化モデル例：

```bash
# 軽量モデル（3B、約 2GB）
ollama pull sarashina2.2:3b

# 中量級（8B〜9B、約 5〜6GB）
ollama pull hf.co/elyza/Llama-3-ELYZA-JP-8B-GGUF:Q4_K_M
ollama pull hf.co/mmnga/Llama-3.1-Swallow-8B-Instruct-v0.3-gguf:Q4_K_M

# 大型（32B、約 20GB）※常用は他アプリ控えめに
ollama pull hf.co/elyza/ELYZA-Thinking-1.0-Qwen-32B-GGUF:Q4_K_M
```

## AWS 移行時のメモ

学習が進んだら AWS に同等構成を載せ替え可能。

- **アプリ側コード**: OpenAI 互換 API で書いてあれば `base_url` を変えるだけ
- **モデル**: 同じ `ollama pull` コマンドで取得可能
- **Ollama 本体**: Linux + NVIDIA GPU なら Docker で完結（Mac と違って GPU パススルー可）

推奨インスタンス（参考、2026年時点）:

| モデル規模 | EC2 インスタンス | GPU メモリ | 料金（オンデマンド） |
|---|---|---|---|
| 7B/8B | g4dn.xlarge | 16GB | ~$0.526/時 |
| 13B〜14B | g5.xlarge | 24GB | ~$1.006/時 |
| 32B | g5.2xlarge | 24GB | ~$1.212/時 |

> AWS 公式の [aws-samples/sample-ollama-server](https://github.com/aws-samples/sample-ollama-server)
> に CloudFormation テンプレートあり。同等構成を 30 分程度で構築可能。
>
> ⚠️ 常時起動するとそれなりに高額になるため、使わない時は必ず停止すること。
> Spot インスタンス利用で 60〜70% 節約可能。

## 参考リンク

- [Ollama 公式](https://ollama.com/)
- [Ollama API ドキュメント](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [ELYZA on Hugging Face](https://huggingface.co/elyza)
- [Open WebUI](https://github.com/open-webui/open-webui)
