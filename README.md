※AI生成のREADMEです。
　Pythonは普通に用意したほうがいいです。

# Dash + uv 最小スターター（フローチャート付き）

このリポジトリは、`uv` で仮想環境と依存関係を管理する Dash サンプルです。フローチャート（なぜなぜ分析向け）の描画・編集UIを含みます。

## 前提
- Python は不要（`uv` が Python 本体も用意可能）
- macOS / Linux / WSL を想定

## セットアップ手順

1) `uv` をインストール

```sh
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# 以降のシェルで使えるようにパスを通す案内に従ってください
```

2) Python を用意（例: 3.11）

```sh
uv python install 3.11
```

3) 仮想環境を作成し、アクティベート

```sh
uv venv --python 3.11
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

4) 依存パッケージをインストール（`pyproject.toml` に記載済）

```sh
uv sync  # lockファイル作成とインストールを一括実行
```

5) アプリを起動

```sh
uv run python app.py  # または: python app.py
```

アプリは既定で `http://127.0.0.1:8050` で動作します。

WSL で動かして Windows 側ブラウザで開く場合は、そのまま `http://localhost:8050` を開けばアクセスできます。

uv.lock について: 本プロジェクトはアプリ用途のため、環境の再現性確保の観点で `uv.lock` をコミットすることを推奨します。

## よく使う `uv` コマンド
- 依存追加: `uv add dash pandas`
- 依存削除: `uv remove dash`
- 実行: `uv run python app.py`
- Python バージョン管理: `uv python install 3.12` / `uv venv --python 3.12`

## プロジェクト構成（提案）
- 小規模のうちはルート直下に `app.py` でOK。
- 中～大規模では `src/` 構成を推奨：
  - `src/app/__init__.py` に Dash インスタンス生成
  - `src/app/layout.py` / `src/app/callbacks.py` に分割

必要であれば、その構成へのリファクタもお手伝いできます。

## フローチャート機能の使い方

- タブ「フローチャート」を開くと以下のUIがあります。
  - 定義テキスト（flow-spec）: 1行1定義でフローを文字列から生成
    - エッジ: `A -> B`（`A => B` も可）
    - 単独ノード: ラベルのみの行
    - コメント/空行: `#` で開始する行、空行は無視
  - なぜなぜ入力パネル: 画面内でノード追加・削除
    - 「根本をセット」: 課題（根本事象）ノードを作成
    - 「選択に追加」: 選択中ノードの子として「なぜ？」ノードを追加
    - 「選択を削除」: 選択したノード or エッジを削除
  - レイアウト: 描画方法の切替
    - 横フロー (preset): 横方向に流れる見やすい配置（既定）
    - 階層 (breadthfirst) / 円 / グリッド / 力学 (cose)

補足:
- 画面はブラウザ幅に合わせて広く表示します（左右に24pxの余白）。
- ノードのテキストは自動改行され、CJK の長文は8文字ごとに改行を挿入してはみ出しを防止します。

### 実行サンプル（画像表示）

- `sample-image/` フォルダにある画像（`png/jpg/jpeg/gif`）のうち、先頭3枚をサンプルタブに表示します。
- リポジトリ同梱の `sample-image/image1.png`, `image2.png` などを置けば、自動で読み込まれます。

## サンプル定義（flow-spec に貼り付け）

```
Start -> Validate
Validate -> Approve
Validate -> Reject
Approve -> End
Reject -> End
```

```
# なぜなぜ例
転倒災害が発生した -> 通路が滑りやすかった
転倒災害が発生した -> 周囲の注意喚起が不足
通路が滑りやすかった -> 清掃が遅れた
清掃が遅れた -> 人手不足
周囲の注意喚起が不足 -> 標識が見づらい
標識が見づらい -> 設置位置が不適切
```

## トラブルシューティング

- ポートが使われている: `8050` を使う別アプリがある場合、`app.py` の `run()` に `port=8051` のように指定してください。
- レイアウト「横フロー」は `dagre` ではなく `preset` を使い、アプリ側で座標を計算しています。プラグイン導入は不要です。
