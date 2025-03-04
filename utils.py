import json
import os


# ディレクトリ構造の確認と作成
def check_directories():
    if not os.path.exists("assets"):
        os.makedirs("assets")
        print(
            "assets フォルダを作成しました。必要な画像や音声ファイルを配置してください。"
        )

    if not os.path.exists("saves"):
        os.makedirs("saves")


# ハイスコアの読み込み
def load_high_scores():
    try:
        with open("saves/high_scores.json", "r") as f:
            return json.load(f)
    except:
        # 空のハイスコアデータ
        return {"marathon": [], "sprint": [], "ultra": []}


# ハイスコアの保存
def save_high_scores(high_scores):
    with open("saves/high_scores.json", "w") as f:
        json.dump(high_scores, f)
