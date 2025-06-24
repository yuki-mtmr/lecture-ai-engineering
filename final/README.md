# 講義スライド作成をサポートするCopilot

プロジェクトの詳細は、所定のドキュメントを確認すること。

## 開発方針

1. 段階的な機能実装
2. 実際の講義資料を用いた検証
3. 講師からのフィードバックに基づく改善
4. Google Gemini APIを活用した高精度な解析

## 実装内容

### 主要機能

1. PowerPointファイル読み込み: .pptxファイルの解析とテキスト抽出
2. Google Gemini API統合: 質問・補足情報の自動生成
3. スライド解析エンジン: 各スライドの内容分析と提案生成
4. CLIインターフェース: コマンドライン操作での実行

### ファイル構成

- src/core/analyzer.py: メイン解析エンジン
- src/services/gemini_client.py: Google Gemini API クライアント
- src/services/powerpoint_reader.py: PowerPoint読み込み機能
- src/cli.py: コマンドラインインターフェース
- src/types/models.py: データモデル定義
- tests/: テストコード

### 使用方法

#### 依存関係のインストール
pip install -r requirements.txt

#### 設定ファイルの作成
cp .env.example .env
#### .envファイルにGoogle Gemini API Keyを設定

#### プレゼンテーション解析
python main.py analyze LLM2023/Matsuo_Lab_LLM_Day1_20231227.pptx

#### 特定スライドの解析
python main.py analyze-slide LLM2023/Matsuo_Lab_LLM_Day1_20231227.pptx 1

#### 一括解析
python main.py batch-analyze LLM2023/

#### API接続テスト
python main.py test-connection