import pygame
import os
import json
import uuid
from datetime import datetime

# Pygameの初期化
pygame.init()
pygame.mixer.init()

# ディレクトリ構造の確認と作成
if not os.path.exists("assets"):
    os.makedirs("assets")
    print("assets フォルダを作成しました。必要な画像や音声ファイルを配置してください。")

if not os.path.exists("saves"):
    os.makedirs("saves")

# 定数
BASE_SCREEN_WIDTH = 800
BASE_SCREEN_HEIGHT = 700
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20

# グローバル変数
screen_width = BASE_SCREEN_WIDTH
screen_height = BASE_SCREEN_HEIGHT
grid_x = (screen_width - GRID_WIDTH * BLOCK_SIZE) // 2
grid_y = (screen_height - GRID_HEIGHT * BLOCK_SIZE) // 2
scale_factor = 1.0

# フルスクリーン設定
FULLSCREEN = False

# 色とテーマ
THEMES = {
    "classic": {
        "background": (0, 0, 0),
        "grid_bg": (20, 20, 20),
        "grid_line": (40, 40, 40),
        "text": (255, 255, 255),
        "ui_bg": (30, 30, 30),
        "ui_border": (100, 100, 100),
        "button": (50, 50, 50),
        "button_hover": (70, 70, 70),
        "button_text": (255, 255, 255),
        "blocks": [
            (0, 255, 255),  # I - シアン
            (255, 255, 0),  # O - イエロー
            (128, 0, 128),  # T - パープル
            (0, 0, 255),  # J - ブルー
            (255, 165, 0),  # L - オレンジ
            (0, 255, 0),  # S - グリーン
            (255, 0, 0),  # Z - レッド
        ],
    },
    "neon": {
        "background": (10, 10, 30),
        "grid_bg": (20, 20, 40),
        "grid_line": (40, 40, 60),
        "text": (220, 220, 255),
        "ui_bg": (30, 30, 50),
        "ui_border": (100, 100, 150),
        "button": (40, 40, 80),
        "button_hover": (60, 60, 100),
        "button_text": (200, 200, 255),
        "blocks": [
            (0, 230, 230),  # I - ネオンシアン
            (230, 230, 0),  # O - ネオンイエロー
            (200, 0, 200),  # T - ネオンパープル
            (0, 0, 230),  # J - ネオンブルー
            (230, 130, 0),  # L - ネオンオレンジ
            (0, 230, 0),  # S - ネオングリーン
            (230, 0, 0),  # Z - ネオンレッド
        ],
    },
    "retro": {
        "background": (20, 40, 20),
        "grid_bg": (30, 50, 30),
        "grid_line": (50, 70, 50),
        "text": (180, 230, 180),
        "ui_bg": (40, 60, 40),
        "ui_border": (80, 120, 80),
        "button": (60, 90, 60),
        "button_hover": (80, 110, 80),
        "button_text": (200, 255, 200),
        "blocks": [
            (100, 200, 100),  # I - レトログリーン
            (180, 200, 100),  # O - レトロイエロー
            (150, 100, 150),  # T - レトロパープル
            (100, 100, 200),  # J - レトロブルー
            (200, 150, 100),  # L - レトロオレンジ
            (120, 200, 120),  # S - レトログリーン
            (200, 100, 100),  # Z - レトロレッド
        ],
    },
    "midnight": {
        "background": (5, 5, 15),
        "grid_bg": (10, 10, 30),
        "grid_line": (20, 20, 50),
        "text": (150, 150, 255),
        "ui_bg": (15, 15, 40),
        "ui_border": (30, 30, 80),
        "button": (25, 25, 60),
        "button_hover": (35, 35, 80),
        "button_text": (180, 180, 255),
        "blocks": [
            (80, 180, 255),  # I - ミッドナイトブルー
            (220, 220, 150),  # O - ミッドナイトイエロー
            (180, 100, 220),  # T - ミッドナイトパープル
            (80, 100, 255),  # J - ミッドナイトブルー
            (255, 140, 80),  # L - ミッドナイトオレンジ
            (100, 220, 100),  # S - ミッドナイトグリーン
            (255, 100, 120),  # Z - ミッドナイトレッド
        ],
    },
    "candy": {
        "background": (250, 240, 250),
        "grid_bg": (240, 230, 240),
        "grid_line": (230, 220, 230),
        "text": (80, 50, 80),
        "ui_bg": (245, 235, 245),
        "ui_border": (200, 180, 200),
        "button": (220, 200, 220),
        "button_hover": (230, 210, 230),
        "button_text": (100, 70, 100),
        "blocks": [
            (100, 200, 255),  # I - キャンディブルー
            (255, 230, 100),  # O - キャンディイエロー
            (220, 120, 220),  # T - キャンディパープル
            (130, 130, 255),  # J - キャンディブルー
            (255, 180, 120),  # L - キャンディオレンジ
            (120, 230, 120),  # S - キャンディグリーン
            (255, 120, 150),  # Z - キャンディレッド
        ],
    },
}

# 現在のテーマ
current_theme = "classic"
theme = THEMES[current_theme]

# グローバル変数の初期化
title_font = None
font = None
small_font = None
big_font = None
screen = None
fullscreen = FULLSCREEN
need_redraw_menus = False

# テトロミノ形状の定義
TETROMINOS = [
    {
        "shape": [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
        "color": 0,
    },  # I - シアン（水色）- 特殊な回転パターン
    {"shape": [[1, 1], [1, 1]], "color": 1},  # O - イエロー（黄色）- 回転しない
    {
        "shape": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
        "color": 2,
    },  # T - パープル（紫色）- 中央を回転中心とする
    {
        "shape": [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
        "color": 3,
    },  # J - ブルー（青色）- 中央を回転中心とする
    {
        "shape": [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
        "color": 4,
    },  # L - オレンジ（橙色）- 中央を回転中心とする
    {
        "shape": [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
        "color": 5,
    },  # S - グリーン（緑色）- 中央を回転中心とする
    {
        "shape": [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
        "color": 6,
    },  # Z - レッド（赤色）- 中央を回転中心とする
]

# SRS (Super Rotation System) のキック定義
# 通常のミノ（JLSTZ）用キックテーブル
KICKS = {
    # 0->1 (A->B): 0度から90度（右回転）
    "01": [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    # 1->2 (B->C): 90度から180度（右回転）
    "12": [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    # 2->3 (C->D): 180度から270度（右回転）
    "23": [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    # 3->0 (D->A): 270度から0度（右回転）
    "30": [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    # 1->0 (B->A): 90度から0度（左回転）
    "10": [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    # 2->1 (C->B): 180度から90度（左回転）
    "21": [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    # 3->2 (D->C): 270度から180度（左回転）
    "32": [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    # 0->3 (A->D): 0度から270度（左回転）
    "03": [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}

# I型の特殊キックテーブル
I_KICKS = {
    # 0->1 (A->B): 0度から90度（右回転）
    "01": [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    # 1->2 (B->C): 90度から180度（右回転）
    "12": [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    # 2->3 (C->D): 180度から270度（右回転）
    "23": [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    # 3->0 (D->A): 270度から0度（右回転）
    "30": [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    # 1->0 (B->A): 90度から0度（左回転）
    "10": [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    # 2->1 (C->B): 180度から90度（左回転）
    "21": [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    # 3->2 (D->C): 270度から180度（左回転）
    "32": [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    # 0->3 (A->D): 0度から270度（左回転）
    "03": [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
}


def init_fonts():
    global title_font, font, small_font, big_font

    try:
        # デバッグ情報を追加
        print("フォント初期化を開始します...")

        # カスタムフォントのパスを設定
        font_path = "MoralerspaceNF_v1.1.0/MoralerspaceNeonNF-Bold.ttf"

        # フォントが存在するか確認
        if os.path.exists(font_path):
            title_font = pygame.font.Font(font_path, int(32 * scale_factor))
            font = pygame.font.Font(font_path, int(18 * scale_factor))
            small_font = pygame.font.Font(font_path, int(14 * scale_factor))
            big_font = pygame.font.Font(font_path, int(24 * scale_factor))
            print("カスタムフォントを読み込みました")
        else:
            # 代替パスを試す
            alt_font_path = "../MoralerspaceNF_v1.1.0/MoralerspaceNeonNF-Bold.ttf"
            if os.path.exists(alt_font_path):
                title_font = pygame.font.Font(alt_font_path, int(32 * scale_factor))
                font = pygame.font.Font(alt_font_path, int(18 * scale_factor))
                small_font = pygame.font.Font(alt_font_path, int(14 * scale_factor))
                big_font = pygame.font.Font(alt_font_path, int(24 * scale_factor))
                print("代替パスからカスタムフォントを読み込みました")
            else:
                # システムフォントにフォールバック
                print("システムフォントを使用します")
                title_font = pygame.font.SysFont("arial", int(32 * scale_factor))
                font = pygame.font.SysFont("arial", int(18 * scale_factor))
                small_font = pygame.font.SysFont("arial", int(14 * scale_factor))
                big_font = pygame.font.SysFont("arial", int(24 * scale_factor))

        # フォントが初期化されたか確認
        print(f"フォント初期化後のtitle_font: {title_font}")
    except Exception as e:
        # エラーが発生した場合のフォールバック
        print(f"フォント読み込みエラー: {e}")
        # 最後の手段としてPygameのデフォルトフォントを使用
        title_font = pygame.font.Font(None, int(32 * scale_factor))
        font = pygame.font.Font(None, int(18 * scale_factor))
        small_font = pygame.font.Font(None, int(14 * scale_factor))
        big_font = pygame.font.Font(None, int(24 * scale_factor))
        print(f"デフォルトフォントを設定しました: {title_font}")


# サウンドの初期化
def init_sounds():
    global move_sound, rotate_sound, drop_sound, clear_sound, tetris_sound, level_up_sound
    global hold_sound, game_over_sound, click_sound, has_sound, has_music

    # 効果音とBGMを別々に処理

    # 効果音の初期化
    try:
        # 効果音の読み込み
        click_sound = pygame.mixer.Sound("assets/click.wav")
        move_sound = pygame.mixer.Sound("assets/move.wav")
        rotate_sound = pygame.mixer.Sound("assets/rotate.wav")
        drop_sound = pygame.mixer.Sound("assets/drop.wav")
        clear_sound = pygame.mixer.Sound("assets/clear.wav")
        tetris_sound = pygame.mixer.Sound("assets/tetris.wav")
        level_up_sound = pygame.mixer.Sound("assets/level_up.wav")
        game_over_sound = pygame.mixer.Sound("assets/game_over.wav")
        hold_sound = pygame.mixer.Sound("assets/hold.wav")

        # 音量設定
        click_sound.set_volume(0.3)
        move_sound.set_volume(0.3)
        rotate_sound.set_volume(0.4)
        drop_sound.set_volume(0.5)
        clear_sound.set_volume(0.6)
        tetris_sound.set_volume(0.7)
        level_up_sound.set_volume(0.7)
        game_over_sound.set_volume(0.7)
        hold_sound.set_volume(0.4)

        has_sound = True
    except Exception as e:
        print(f"効果音ファイルの読み込みエラー: {e}")
        has_sound = False

        # 音声ファイルがない場合のダミーオブジェクト
        class DummySound:
            def play(self):
                pass

            def set_volume(self, vol):
                pass

        click_sound = DummySound()
        move_sound = DummySound()
        rotate_sound = DummySound()
        drop_sound = DummySound()
        clear_sound = DummySound()
        tetris_sound = DummySound()
        level_up_sound = DummySound()
        game_over_sound = DummySound()
        hold_sound = DummySound()

    # BGMの初期化（効果音とは別に処理）
    try:
        # BGMの読み込み
        pygame.mixer.music.load("assets/tetris_theme.mp3")
        pygame.mixer.music.set_volume(0.5)
        has_music = True
        print("BGMを正常に読み込みました")
    except Exception as e:
        print(f"BGM読み込みエラー: {e}")
        has_music = False


# 設定の読み込み
def load_settings():
    try:
        with open("saves/settings.json", "r") as f:
            return json.load(f)
    except:
        # デフォルト設定
        return {
            "theme": "classic",
            "music": True,
            "sound": True,
            "ghost_piece": True,
            "effects": True,  # エフェクト表示
            "effect_type": "default",  # エフェクトタイプ
            "selected_bgm": "tetris_theme.mp3",  # BGM設定を追加
            "game_mode": "marathon",  # ゲームモード
            "das": 0.17,  # Delayed Auto Shift (秒)
            "arr": 0.03,  # Auto Repeat Rate (秒)
            "lock_delay": 0.5,  # 追加：ロックディレイ設定
            "max_lock_resets": 15,  # 追加：最大ロックディレイリセット回数
            "key_bindings": {  # キー設定
                "move_left": pygame.K_LEFT,
                "move_right": pygame.K_RIGHT,
                "rotate_cw": pygame.K_UP,
                "rotate_ccw": pygame.K_z,
                "soft_drop": pygame.K_DOWN,
                "hard_drop": pygame.K_SPACE,
                "hold": pygame.K_c,
                "pause": pygame.K_p,
            },
        }


# 設定の保存
def save_settings(settings):
    with open("saves/settings.json", "w") as f:
        json.dump(settings, f)


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


# テーマの切り替え
def cycle_theme():
    global current_theme, theme, settings, need_redraw_menus

    themes = list(THEMES.keys())
    current_index = themes.index(current_theme)
    next_index = (current_index + 1) % len(themes)
    current_theme = themes[next_index]
    theme = THEMES[current_theme]

    # 設定を更新
    settings["theme"] = current_theme
    save_settings(settings)

    # 再描画フラグを設定
    need_redraw_menus = True

    print(f"テーマを変更しました: {current_theme}")
    return current_theme


def apply_theme_change():
    """テーマ変更を即座に適用する"""
    global need_redraw_menus
    need_redraw_menus = False
    print(f"テーマ適用: {current_theme}")


# フルスクリーン切り替え関数
def toggle_fullscreen():
    global screen, fullscreen, FULLSCREEN, grid_x, grid_y, scale_factor
    global screen_width, screen_height

    try:
        # 現在の状態を反転
        fullscreen = not fullscreen

        # ディスプレイ再初期化
        pygame.display.quit()
        pygame.display.init()

        if fullscreen:
            # フルスクリーンモードに切り替え
            try:
                desktop_sizes = pygame.display.get_desktop_sizes()
                if desktop_sizes:
                    screen_width, screen_height = desktop_sizes[0]
                else:
                    screen_width, screen_height = 1920, 1080
            except:
                # デスクトップサイズ取得に失敗した場合のフォールバック
                screen_width, screen_height = 1920, 1080

            try:
                screen = pygame.display.set_mode(
                    (screen_width, screen_height), pygame.FULLSCREEN
                )
            except pygame.error as e:
                print(f"フルスクリーンモード設定に失敗: {e}")
                # フルスクリーンに失敗した場合はウィンドウモードに戻す
                fullscreen = False
                screen_width = BASE_SCREEN_WIDTH
                screen_height = BASE_SCREEN_HEIGHT
                screen = pygame.display.set_mode((screen_width, screen_height))
                scale_factor = 1.0

            if fullscreen:
                # スケール係数の計算
                width_scale = screen_width / BASE_SCREEN_WIDTH
                height_scale = screen_height / BASE_SCREEN_HEIGHT
                scale_factor = min(width_scale, height_scale)
        else:
            # ウィンドウモードに切り替え
            screen_width = BASE_SCREEN_WIDTH
            screen_height = BASE_SCREEN_HEIGHT
            try:
                screen = pygame.display.set_mode((screen_width, screen_height))
                scale_factor = 1.0
            except pygame.error as e:
                print(f"ウィンドウモード設定に失敗: {e}")
                return None

        # グリッド位置を再計算
        grid_x = (screen_width - GRID_WIDTH * BLOCK_SIZE * scale_factor) // 2
        grid_y = (screen_height - GRID_HEIGHT * BLOCK_SIZE * scale_factor) // 2

        # フォントの再初期化
        try:
            init_fonts()
        except Exception as e:
            print(f"フォント再初期化エラー: {e}")

        # 設定を更新
        try:
            settings["fullscreen"] = fullscreen
            save_settings(settings)
            FULLSCREEN = fullscreen
        except Exception as e:
            print(f"設定保存エラー: {e}")

        pygame.display.set_caption("テトリス")
        return screen

    except Exception as e:
        print(f"フルスクリーン切り替えで予期しないエラー: {e}")
        # エラー時は安全なウィンドウモードに戻す
        try:
            fullscreen = False
            screen_width = BASE_SCREEN_WIDTH
            screen_height = BASE_SCREEN_HEIGHT
            screen = pygame.display.set_mode((screen_width, screen_height))
            scale_factor = 1.0
            grid_x = (screen_width - GRID_WIDTH * BLOCK_SIZE * scale_factor) // 2
            grid_y = (screen_height - GRID_HEIGHT * BLOCK_SIZE * scale_factor) // 2
            pygame.display.set_caption("テトリス")
            return screen
        except:
            print("フルスクリーン切り替えの復旧に失敗しました")
            return None


# スクリーンの初期化
def initialize_screen(fullscreen=False):
    global screen, screen_width, screen_height, grid_x, grid_y, scale_factor, FULLSCREEN

    FULLSCREEN = fullscreen

    if fullscreen:
        # フルスクリーンモード
        # デスクトップの解像度を取得
        desktop_sizes = pygame.display.get_desktop_sizes()
        if desktop_sizes:
            screen_width, screen_height = desktop_sizes[0]
        else:
            # フォールバック: 一般的な解像度
            screen_width, screen_height = 1920, 1080

        # フルスクリーンモードでの画面設定
        screen = pygame.display.set_mode(
            (screen_width, screen_height), pygame.FULLSCREEN
        )

        # スケール係数の計算
        width_scale = screen_width / BASE_SCREEN_WIDTH
        height_scale = screen_height / BASE_SCREEN_HEIGHT
        scale_factor = min(width_scale, height_scale)
    else:
        # ウィンドウモード
        screen_width = BASE_SCREEN_WIDTH
        screen_height = BASE_SCREEN_HEIGHT
        screen = pygame.display.set_mode((screen_width, screen_height))
        scale_factor = 1.0

    # グリッド位置の再計算 - 画面中央に配置
    grid_x = (screen_width - GRID_WIDTH * BLOCK_SIZE * scale_factor) // 2
    grid_y = (screen_height - GRID_HEIGHT * BLOCK_SIZE * scale_factor) // 2

    # 画面をクリア
    screen.fill((0, 0, 0))  # デフォルトの黒

    pygame.display.set_caption("テトリス")
    return screen


# 設定を読み込み
settings = load_settings()
current_theme = settings.get("theme", "classic")
theme = THEMES[current_theme]

# サウンド関連のグローバル変数を追加
move_sound = None
rotate_sound = None
drop_sound = None
clear_sound = None
tetris_sound = None
level_up_sound = None
hold_sound = None
game_over_sound = None
click_sound = None
has_sound = False
has_music = False  # ここでモジュールレベルで宣言
