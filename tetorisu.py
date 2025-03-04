import pygame
import random
import math
import json
import os
import time
import uuid
from pygame import mixer
from datetime import datetime
import builtins

# Pygameの初期化
pygame.init()
mixer.init()

# フルスクリーン設定
FULLSCREEN = False

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


# フォント初期化関数
def init_fonts():
    global title_font, font, small_font, big_font

    try:
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
                title_font = pygame.font.SysFont(
                    "yugothicuibold", int(32 * scale_factor)
                )
                font = pygame.font.SysFont("yugothicuisemibold", int(18 * scale_factor))
                small_font = pygame.font.SysFont("yugothicui", int(14 * scale_factor))
                big_font = pygame.font.SysFont("yugothicuibold", int(24 * scale_factor))
                print(
                    "カスタムフォントが見つかりません。システムフォントを使用します。"
                )
    except Exception as e:
        # エラーが発生した場合のフォールバック
        print(f"フォント読み込みエラー: {e}")
        title_font = pygame.font.Font(None, int(32 * scale_factor))
        font = pygame.font.Font(None, int(18 * scale_factor))
        small_font = pygame.font.Font(None, int(14 * scale_factor))
        big_font = pygame.font.Font(None, int(24 * scale_factor))


# サウンド初期化
move_sound = None
rotate_sound = None
drop_sound = None
clear_sound = None
tetris_sound = None
level_up_sound = None
hold_sound = None
game_over_sound = None

try:
    move_sound = mixer.Sound("assets/move.wav")
    rotate_sound = mixer.Sound("assets/rotate.wav")
    drop_sound = mixer.Sound("assets/drop.wav")
    clear_sound = mixer.Sound("assets/clear.wav")
    tetris_sound = mixer.Sound("assets/tetris.wav")
    level_up_sound = mixer.Sound("assets/level_up.wav")
    hold_sound = mixer.Sound("assets/hold.wav")
    game_over_sound = mixer.Sound("assets/game_over.wav")
    click_sound = mixer.Sound("assets/click.wav")

    # 音量調整
    move_sound.set_volume(0.5)
    rotate_sound.set_volume(0.5)
    drop_sound.set_volume(0.5)
    clear_sound.set_volume(0.7)
    tetris_sound.set_volume(0.7)
    level_up_sound.set_volume(0.7)
    hold_sound.set_volume(0.5)
    game_over_sound.set_volume(0.7)
    click_sound.set_volume(0.5)

    has_sound = True
except:
    print("音声ファイルが見つかりません。サウンドは無効になります。")
    has_sound = False

# BGM初期化
has_music = False
try:
    pygame.mixer.music.load("assets/tetris_theme.mp3")
    pygame.mixer.music.set_volume(0.5)
    has_music = True
except Exception as e:
    print(f"音声ファイルの読み込みエラー: {e}")

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
            "das": 0.17,  # Delayed Auto Shift (秒)
            "arr": 0.03,  # Auto Repeat Rate (秒)
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


# 設定を読み込み
settings = load_settings()
current_theme = settings.get("theme", "classic")
theme = THEMES[current_theme]


# テーマの切り替え
def cycle_theme():
    global current_theme, theme, settings

    themes = list(THEMES.keys())
    current_index = themes.index(current_theme)
    next_index = (current_index + 1) % len(themes)
    current_theme = themes[next_index]
    theme = THEMES[current_theme]

    # 設定を更新
    settings["theme"] = current_theme
    save_settings(settings)


# フルスクリーン切り替え関数
def toggle_fullscreen():
    global screen, fullscreen, FULLSCREEN, grid_x, grid_y, scale_factor, font, small_font, big_font, title_font, screen_width, screen_height

    # fullscreenが未定義の場合は初期化
    if "fullscreen" not in globals():
        global fullscreen
        fullscreen = FULLSCREEN

    # 現在の状態を反転
    fullscreen = not fullscreen

    # 現在のテーマを保存
    current_theme_backup = current_theme

    # 画面情報を取得
    info = pygame.display.Info()

    # 完全に画面を再作成するために、Pygameディスプレイモジュールを再初期化
    pygame.display.quit()
    pygame.display.init()

    if fullscreen:
        # フルスクリーンモードに切り替え
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
        # ウィンドウモードに切り替え
        screen_width = BASE_SCREEN_WIDTH
        screen_height = BASE_SCREEN_HEIGHT
        screen = pygame.display.set_mode((screen_width, screen_height))
        scale_factor = 1.0

    # テーマを復元
    global theme
    theme = THEMES[current_theme_backup]

    # フォントの再初期化
    init_fonts()

    # グリッド位置の再計算 - 画面中央に配置
    grid_x = (screen_width - GRID_WIDTH * BLOCK_SIZE * scale_factor) // 2
    grid_y = (screen_height - GRID_HEIGHT * BLOCK_SIZE * scale_factor) // 2

    # 画面を塗りつぶし
    screen.fill(theme["background"])

    # 設定を更新
    settings["fullscreen"] = fullscreen
    save_settings(settings)

    # フルスクリーン状態をグローバル変数に保存
    FULLSCREEN = fullscreen

    # ウィンドウタイトルを設定
    pygame.display.set_caption("テトリス")

    # 現在の画面サイズを表示（デバッグ用）
    print(f"画面サイズ: {screen_width}x{screen_height}, スケール係数: {scale_factor}")

    # 各種メニューを再描画するためのフラグを設定
    global need_redraw_menus
    need_redraw_menus = True

    return fullscreen


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
    if "theme" in globals():
        screen.fill(theme["background"])
    else:
        screen.fill((0, 0, 0))  # デフォルトの黒

    pygame.display.set_caption("テトリス")
    return screen


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


# ボタンクラス
class Button:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        text,
        action=None,
        bg_color=None,
        text_color=None,
        icon=None,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        self.clicked = False
        self.icon = icon

        # デフォルトカラーをテーマから取得
        if bg_color is None:
            self.bg_color = theme["button"]
            self.hover_color = theme["button_hover"]
        else:
            self.bg_color = bg_color
            # ホバー色は背景色より少し明るく
            r = min(255, bg_color[0] + 20)
            g = min(255, bg_color[1] + 20)
            b = min(255, bg_color[2] + 20)
            self.hover_color = (r, g, b)

        self.text_color = text_color if text_color else theme["button_text"]

        # VSCode風のボタンスタイル
        self.border_radius = int(4 * scale_factor)
        self.border_color = (70, 70, 70)
        self.shadow_color = (20, 20, 20, 100)
        self.active_border_color = (0, 122, 204)  # VSCodeのアクティブ色

    def update(self, mouse_pos):
        # ホバー状態の更新
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        # 影の描画
        shadow_rect = pygame.Rect(
            self.rect.x + 2 * scale_factor,
            self.rect.y + 2 * scale_factor,
            self.rect.width,
            self.rect.height,
        )
        pygame.draw.rect(
            surface, self.shadow_color, shadow_rect, border_radius=self.border_radius
        )

        # ボタン本体の描画
        color = self.hover_color if self.hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)

        # ボーダーの描画
        border_color = self.active_border_color if self.hovered else self.border_color
        pygame.draw.rect(
            surface, border_color, self.rect, width=1, border_radius=self.border_radius
        )

        # テキストの描画
        if self.text:
            text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

        # アイコンの描画
        if self.icon:
            icon_rect = self.icon.get_rect(
                midleft=(self.rect.x + 10 * scale_factor, self.rect.centery)
            )
            surface.blit(self.icon, icon_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.clicked = True
                if has_sound and "click_sound" in globals() and click_sound:
                    click_sound.play()
                return self.action
        return None


# パーティクルクラス
class Particle:
    def __init__(self, x, y, color, size=3, speed=2, life=1.0, effect_type="default"):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.speed = speed
        self.life = life
        self.max_life = life
        self.effect_type = effect_type

        # エフェクトタイプに応じた初期化
        if effect_type == "explosion":
            self.angle = random.uniform(0, 2 * math.pi)
            self.dx = math.cos(self.angle) * self.speed
            self.dy = math.sin(self.angle) * self.speed
        elif effect_type == "rain":
            self.angle = random.uniform(
                math.pi / 2 - 0.2, math.pi / 2 + 0.2
            )  # ほぼ真下
            self.dx = math.cos(self.angle) * self.speed * 0.5
            self.dy = math.sin(self.angle) * self.speed * 2
        elif effect_type == "spiral":
            self.angle = random.uniform(0, 2 * math.pi)
            self.radius = random.uniform(2, 10)
            self.angular_speed = random.uniform(2, 5) * (
                1 if random.random() > 0.5 else -1
            )
            self.dx = math.cos(self.angle) * self.speed * 0.2
            self.dy = math.sin(self.angle) * self.speed * 0.2
        else:  # default
            self.angle = random.uniform(0, 2 * math.pi)
            self.dx = math.cos(self.angle) * self.speed
            self.dy = math.sin(self.angle) * self.speed

    def update(self, dt):
        if self.effect_type == "spiral":
            # スパイラルエフェクトの場合は角度を更新
            self.angle += self.angular_speed * dt
            self.x += self.dx * dt * 60 + math.cos(self.angle) * self.radius * dt * 2
            self.y += self.dy * dt * 60 + math.sin(self.angle) * self.radius * dt * 2
        else:
            self.x += self.dx * dt * 60
            self.y += self.dy * dt * 60

            # 重力効果（雨エフェクト）
            if self.effect_type == "rain":
                self.dy += 9.8 * dt  # 重力加速度

        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        color = (
            (*self.color[:3], alpha) if len(self.color) > 3 else (*self.color, alpha)
        )

        if self.effect_type == "rain":
            # 雨滴は縦長の楕円形
            size_x = max(1, int(self.size * 0.5 * (self.life / self.max_life)))
            size_y = max(1, int(self.size * 2 * (self.life / self.max_life)))
            pygame.draw.ellipse(
                surface,
                color,
                (int(self.x - size_x), int(self.y - size_y), size_x * 2, size_y * 2),
            )
        else:
            # 通常のパーティクルは円形
            size = max(1, int(self.size * (self.life / self.max_life)))
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)


# パーティクルシステムクラス
class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.effect_type = "default"  # デフォルトのエフェクトタイプ

    def set_effect_type(self, effect_type):
        self.effect_type = effect_type

    def create_explosion(self, x, y, color, count=10):
        for _ in range(count):
            size = random.uniform(2, 5)
            speed = random.uniform(1, 3)
            life = random.uniform(0.5, 1.5)
            self.particles.append(
                Particle(x, y, color, size, speed, life, self.effect_type)
            )

    def create_line_clear_effect(
        self, x, y, color, count=15, width=GRID_WIDTH * BLOCK_SIZE * scale_factor
    ):
        # ライン消去エフェクト
        for _ in range(count):
            size = random.uniform(3, 7)
            speed = random.uniform(2, 5)
            life = random.uniform(0.7, 1.8)
            # ライン全体にパーティクルを分散
            particle_x = x + random.uniform(0, width)
            self.particles.append(
                Particle(particle_x, y, color, size, speed, life, self.effect_type)
            )

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        for particle in self.particles:
            particle.draw(surface)


# フローティングテキストクラス
class FloatingText:
    def __init__(self, x, y, text, color, size=28, life=1.5):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = life
        self.max_life = life
        # グローバルフォントを使用して文字化けを防止
        self.font = (
            font if "font" in globals() else pygame.font.SysFont("yugothicuibold", size)
        )
        self.size = size
        self.dy = -1  # 上に移動

    def update(self, dt):
        self.y += self.dy * dt * 60
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        # フォントが存在しない場合は再作成
        if not hasattr(self, "font") or self.font is None:
            self.font = (
                font
                if "font" in globals()
                else pygame.font.SysFont("yugothicuibold", self.size)
            )
        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (self.x - text_surf.get_width() // 2, self.y))


# テトリスクラス
class Tetris:
    def __init__(self, game_mode="marathon"):
        self.game_mode = game_mode
        self.reset()

        # ゲームモードに応じた設定
        if game_mode == "sprint":
            self.lines_target = 40
            self.time_limit = None
        elif game_mode == "ultra":
            self.lines_target = None
            self.time_limit = 180  # 3分
        else:  # marathon
            self.lines_target = None
            self.time_limit = None

        # パーティクルシステムの初期化
        self.particle_system = ParticleSystem()
        # 設定からエフェクトタイプを設定
        self.particle_system.set_effect_type(settings.get("effect_type", "default"))

        # フローティングテキストのリスト
        self.floating_texts = []

        # ピース統計
        self.pieces_stats = [0] * 7
        self.tspin_count = 0

        # ゲームクリアフラグ
        self.game_clear = False

        # ハイスコアをチェック
        self.high_scores = load_high_scores().get(game_mode, [])

        # DAS/ARR設定
        self.das_delay = settings.get("das", 0.17)  # 秒
        self.arr_delay = settings.get("arr", 0.03)  # 秒
        self.das_timer = 0
        self.arr_timer = 0

    def reset(self):
        # ゲームの状態を初期化
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = None
        self.held_piece = None
        self.can_hold = True
        self.has_used_hold = False

        # 7種類のミノを1セットとしてシャッフル
        self.piece_bag = []
        self.refill_piece_bag()

        # 次のピースを5つ用意
        self.next_pieces = [self.get_next_piece() for _ in range(5)]
        self.game_over = False
        self.game_clear = False
        self.paused = False
        self.soft_drop = False

        # 次のピースを取得
        self.current_piece = self.next_pieces.pop(0)
        self.next_pieces.append(self.get_next_piece())

        # ゴーストピースの初期化
        self.ghost_piece = self.get_ghost_piece()

        # スコアと関連情報
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.combo = 0
        self.back_to_back = False

        # 落下速度と時間変数
        self.fall_time = 0
        self.fall_speed = 0.8  # 初期落下速度（秒）
        self.lock_delay = 0
        self.max_lock_delay = 0.5  # 接地からロックまでの最大時間（秒）

        # ゲーム時間
        self.time_played = 0

        # ラインクリア用
        self.clearing_lines = False
        self.lines_to_clear = []

    def refill_piece_bag(self):
        """7種類のミノを1セットとしてシャッフルし、バッグに追加する"""
        new_bag = list(range(len(TETROMINOS)))
        random.shuffle(new_bag)
        self.piece_bag.extend(new_bag)

    def get_next_piece(self):
        """バッグから次のピースを取得する。バッグが空の場合は補充する。"""
        # バッグが空の場合は補充
        if not self.piece_bag:
            self.refill_piece_bag()

        # バッグから次のピースのインデックスを取得
        piece_index = self.piece_bag.pop(0)

        piece = {
            "shape": [row[:] for row in TETROMINOS[piece_index]["shape"]],
            "color": theme["blocks"][TETROMINOS[piece_index]["color"]],
            "x": GRID_WIDTH // 2 - len(TETROMINOS[piece_index]["shape"][0]) // 2,
            "y": 0,
            "rotation": 0,
            "index": piece_index,
        }
        return piece

    def get_ghost_piece(self):
        if not self.current_piece or not settings.get("ghost_piece", True):
            return None

        # 現在のピースの深いコピー
        ghost = {
            "shape": [row[:] for row in self.current_piece["shape"]],
            "color": self.current_piece["color"],
            "x": self.current_piece["x"],
            "y": self.current_piece["y"],
            "rotation": self.current_piece["rotation"],
        }

        # 可能な限り下に移動
        while self.valid_move(ghost, y_offset=1):
            ghost["y"] += 1

        return ghost

    def valid_move(self, piece, x_offset=0, y_offset=0, new_shape=None):
        # 移動や回転が有効かチェック
        if not piece:
            return False

        shape_to_check = new_shape if new_shape else piece["shape"]

        for y, row in enumerate(shape_to_check):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece["x"] + x + x_offset
                    new_y = piece["y"] + y + y_offset

                    # 範囲チェック
                    if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                        return False

                    # 既存ブロックとの衝突チェック（グリッド内の場合のみ）
                    if new_y >= 0 and self.grid[new_y][new_x] is not None:
                        return False

        return True

    def rotate(self, clockwise=True):
        if self.game_over or self.paused or not self.current_piece:
            return

        if has_sound and settings.get("sound", True):
            rotate_sound.play()

        # 元の状態を保存
        original_rotation = self.current_piece["rotation"]
        original_shape = [row[:] for row in self.current_piece["shape"]]
        original_x = self.current_piece["x"]
        original_y = self.current_piece["y"]

        # 新しい回転状態を計算
        if clockwise:
            new_rotation = (original_rotation + 1) % 4
            # I型テトロミノの特殊な回転パターン
            if self.current_piece["index"] == 0:  # I型
                if original_rotation == 0:  # 水平から垂直へ
                    self.current_piece["shape"] = [
                        [0, 0, 1, 0],
                        [0, 0, 1, 0],
                        [0, 0, 1, 0],
                        [0, 0, 1, 0],
                    ]
                elif original_rotation == 1:  # 垂直から水平へ
                    self.current_piece["shape"] = [
                        [0, 0, 0, 0],
                        [0, 0, 0, 0],
                        [1, 1, 1, 1],
                        [0, 0, 0, 0],
                    ]
                elif original_rotation == 2:  # 水平から垂直へ
                    self.current_piece["shape"] = [
                        [0, 1, 0, 0],
                        [0, 1, 0, 0],
                        [0, 1, 0, 0],
                        [0, 1, 0, 0],
                    ]
                elif original_rotation == 3:  # 垂直から水平へ
                    self.current_piece["shape"] = [
                        [0, 0, 0, 0],
                        [1, 1, 1, 1],
                        [0, 0, 0, 0],
                        [0, 0, 0, 0],
                    ]
            else:
                # 通常のテトロミノの回転
                self.current_piece["shape"] = self.rotate_matrix(original_shape)
        else:
            new_rotation = (original_rotation - 1) % 4
            # I型テトロミノの特殊な回転パターン
            if self.current_piece["index"] == 0:  # I型
                if original_rotation == 0:  # 水平から垂直へ
                    self.current_piece["shape"] = [
                        [0, 1, 0, 0],
                        [0, 1, 0, 0],
                        [0, 1, 0, 0],
                        [0, 1, 0, 0],
                    ]
                elif original_rotation == 1:  # 垂直から水平へ
                    self.current_piece["shape"] = [
                        [0, 0, 0, 0],
                        [0, 0, 0, 0],
                        [1, 1, 1, 1],
                        [0, 0, 0, 0],
                    ]
                elif original_rotation == 2:  # 水平から垂直へ
                    self.current_piece["shape"] = [
                        [0, 0, 1, 0],
                        [0, 0, 1, 0],
                        [0, 0, 1, 0],
                        [0, 0, 1, 0],
                    ]
                elif original_rotation == 3:  # 垂直から水平へ
                    self.current_piece["shape"] = [
                        [0, 0, 0, 0],
                        [1, 1, 1, 1],
                        [0, 0, 0, 0],
                        [0, 0, 0, 0],
                    ]
            else:
                # 反時計回りの回転を実装
                self.current_piece["shape"] = self.rotate_matrix_ccw(original_shape)

        self.current_piece["rotation"] = new_rotation

        # デバッグ情報：現在のピースの位置と回転状態
        print(f"回転前: x={original_x}, y={original_y}, rotation={original_rotation}")
        print(
            f"回転後: x={self.current_piece['x']}, y={self.current_piece['y']}, rotation={new_rotation}"
        )

        # 壁や他のブロックとの衝突をチェック
        # まず基本的な位置で回転が可能かチェック
        if self.valid_move(self.current_piece):
            print("基本位置で回転可能")
            # T-Spinチェック
            if self.current_piece["index"] == 2:  # T型
                self.check_tspin()

            # ゴーストピースの更新
            self.ghost_piece = self.get_ghost_piece()
            return

        print("基本位置で回転不可能、キックテスト実行")
        # 基本位置で回転できない場合、キックテストを実行
        # キック用のパターンキー
        kick_key = f"{original_rotation}{new_rotation}"
        print(f"キックキー: {kick_key}")

        # I型ピースと他の形状で異なるキックパターンを使用
        if self.current_piece["index"] == 0:  # I型
            kicks = I_KICKS[kick_key]
            print(f"I型キックパターン: {kicks}")
        else:
            kicks = KICKS[kick_key]
            print(f"通常キックパターン: {kicks}")

        # キックテストを実行
        for i, (kick_x, kick_y) in enumerate(kicks):
            print(f"キックテスト {i+1}: ({kick_x}, {kick_y})")
            if self.valid_move(self.current_piece, x_offset=kick_x, y_offset=kick_y):
                print(f"キックテスト {i+1} 成功")
                self.current_piece["x"] += kick_x
                self.current_piece["y"] += kick_y
                print(
                    f"新しい位置: x={self.current_piece['x']}, y={self.current_piece['y']}"
                )

                # T-Spinチェック
                if self.current_piece["index"] == 2:  # T型
                    self.check_tspin()

                # ゴーストピースの更新
                self.ghost_piece = self.get_ghost_piece()
                return

        # 回転が不可能な場合は元に戻す
        self.current_piece["shape"] = original_shape
        self.current_piece["rotation"] = original_rotation
        self.current_piece["x"] = original_x
        self.current_piece["y"] = original_y

    def rotate_matrix(self, matrix):
        """行列を時計回りに90度回転

        画像に示されている回転パターンに合わせた実装です。
        時計回りの回転では、元の行列の行は新しい行列の列になり、逆順に配置されます。
        """
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        result = [[0 for _ in range(rows)] for _ in range(cols)]

        for i in range(rows):
            for j in range(cols):
                result[j][rows - 1 - i] = matrix[i][j]

        return result

    def rotate_matrix_ccw(self, matrix):
        """行列を反時計回りに90度回転

        画像に示されている回転パターンに合わせた実装です。
        反時計回りの回転では、元の行列の列は新しい行列の行になり、逆順に配置されます。
        """
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        result = [[0 for _ in range(rows)] for _ in range(cols)]

        for i in range(rows):
            for j in range(cols):
                result[cols - 1 - j][i] = matrix[i][j]

        return result

    def draw_game_clear_screen(self):
        # 半透明のオーバーレイ
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # メニューパネル
        panel_width = 400 * scale_factor
        panel_height = 400 * scale_factor
        panel_x = (screen_width - panel_width) // 2
        panel_y = (screen_height - panel_height) // 2

        pygame.draw.rect(
            screen, theme["ui_bg"], (panel_x, panel_y, panel_width, panel_height)
        )
        pygame.draw.rect(
            screen, theme["ui_border"], (panel_x, panel_y, panel_width, panel_height), 3
        )

        # タイトル
        title_text = title_font.render("ゲームクリア！", True, (100, 255, 100))
        screen.blit(
            title_text,
            (
                screen_width // 2 - title_text.get_width() // 2,
                panel_y + 30 * scale_factor,
            ),
        )

        # 結果表示
        score_text = font.render(f"スコア: {self.score}", True, theme["text"])
        level_text = font.render(f"レベル: {self.level}", True, theme["text"])
        lines_text = font.render(f"ライン: {self.lines_cleared}", True, theme["text"])

        time_minutes = int(self.time_played // 60)
        time_seconds = int(self.time_played % 60)
        time_text = font.render(
            f"クリア時間: {time_minutes}:{time_seconds:02d}", True, theme["text"]
        )

        # ハイスコア？
        is_high_score = self.check_high_score()

        if is_high_score:
            high_score_text = font.render("新記録達成！", True, (255, 255, 100))
            screen.blit(
                high_score_text,
                (
                    screen_width // 2 - high_score_text.get_width() // 2,
                    panel_y + 80 * scale_factor,
                ),
            )

        screen.blit(
            score_text,
            (
                screen_width // 2 - score_text.get_width() // 2,
                panel_y + 120 * scale_factor,
            ),
        )
        screen.blit(
            level_text,
            (
                screen_width // 2 - level_text.get_width() // 2,
                panel_y + 160 * scale_factor,
            ),
        )
        screen.blit(
            lines_text,
            (
                screen_width // 2 - lines_text.get_width() // 2,
                panel_y + 200 * scale_factor,
            ),
        )
        screen.blit(
            time_text,
            (
                screen_width // 2 - time_text.get_width() // 2,
                panel_y + 240 * scale_factor,
            ),
        )

        # リトライボタン
        retry_button = Button(
            panel_x + panel_width // 2 - 100 * scale_factor,
            panel_y + 300 * scale_factor,
            200 * scale_factor,
            40 * scale_factor,
            "リトライ",
            action=lambda: "retry",
        )

        menu_button = Button(
            panel_x + panel_width // 2 - 100 * scale_factor,
            panel_y + 350 * scale_factor,
            200 * scale_factor,
            40 * scale_factor,
            "メニューに戻る",
            action=lambda: "menu",
        )

        mouse_pos = pygame.mouse.get_pos()
        retry_button.update(mouse_pos)
        retry_button.draw(screen)

        menu_button.update(mouse_pos)
        menu_button.draw(screen)

        return [retry_button, menu_button]

    def update(self, dt):
        """ゲームの状態を更新する"""
        if self.game_over or self.paused:
            return

        # ゲーム時間の更新
        self.time_played += dt

        # 時間制限のチェック（ウルトラモード）
        if self.time_limit and self.time_played >= self.time_limit:
            self.game_over = True
            return

        # パーティクルとフローティングテキストの更新
        self.particle_system.update(dt)
        self.floating_texts = [text for text in self.floating_texts if text.update(dt)]

        # 落下処理
        self.fall_time += dt
        fall_speed = self.fall_speed / (
            1 + (self.soft_drop * 9)
        )  # ソフトドロップで10倍速く

        if self.fall_time >= fall_speed:
            self.fall_time = 0
            # 下に移動できるかチェック
            if self.valid_move(self.current_piece, y_offset=1):
                self.current_piece["y"] += 1
                # ロックディレイをリセット
                self.lock_delay = 0
            else:
                # 接地している場合、ロックディレイを増加
                self.lock_delay += dt
                if self.lock_delay >= self.max_lock_delay:
                    self.lock_piece()

        # キー長押し処理（DAS/ARR）
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
            direction = -1 if keys[pygame.K_LEFT] else 1

            # DASタイマーの更新
            if self.das_timer < self.das_delay:
                self.das_timer += dt
            else:
                # ARRタイマーの更新
                self.arr_timer += dt
                while self.arr_timer >= self.arr_delay:
                    self.move(direction)
                    self.arr_timer -= self.arr_delay
        else:
            # キーが押されていない場合はタイマーをリセット
            self.das_timer = 0
            self.arr_timer = 0

    def move(self, direction):
        """ピースを左右に移動する"""
        if self.game_over or self.paused or not self.current_piece:
            return False

        if self.valid_move(self.current_piece, x_offset=direction):
            self.current_piece["x"] += direction
            # ゴーストピースの更新
            self.ghost_piece = self.get_ghost_piece()

            # 効果音
            if move_sound and has_sound and settings.get("sound", True):
                move_sound.play()

            return True
        return False

    def lock_piece(self):
        """現在のピースをグリッドに固定する"""
        # T-Spinチェック
        tspin_type = self.check_tspin()

        # ピースが存在しない場合は何もしない
        if not self.current_piece:
            return

        # 現在のピースをグリッドに追加
        for y, row in enumerate(self.current_piece["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    block_grid_y = self.current_piece["y"] + y
                    block_grid_x = self.current_piece["x"] + x

                    # グリッド範囲内かチェック
                    if (
                        0 <= block_grid_y < GRID_HEIGHT
                        and 0 <= block_grid_x < GRID_WIDTH
                    ):
                        self.grid[block_grid_y][block_grid_x] = self.current_piece[
                            "color"
                        ]

                        # ブロック配置エフェクト（設定がONの場合）
                        if settings.get("effects", True):
                            # パーティクルエフェクト
                            # 画面上の実際の座標を計算
                            block_screen_x = (
                                grid_x + block_grid_x * BLOCK_SIZE * scale_factor
                            )
                            block_screen_y = (
                                grid_y + block_grid_y * BLOCK_SIZE * scale_factor
                            )

                            # ブロックの中心にエフェクトを配置
                    self.particle_system.create_explosion(
                        block_screen_x + (BLOCK_SIZE * scale_factor / 2),
                        block_screen_y + (BLOCK_SIZE * scale_factor / 2),
                        self.current_piece["color"],
                        5,  # パーティクル数
                    )

        # 効果音
        if drop_sound and has_sound and settings.get("sound", True):
            drop_sound.play()

        # ピース統計の更新
        self.pieces_stats[self.current_piece["index"]] += 1

        # ラインクリアチェック
        self.check_lines()

        # ホールドリセット
        self.can_hold = True

        # 次のピースを取得
        self.current_piece = self.next_pieces.pop(0)
        self.next_pieces.append(self.get_next_piece())

        # ゴーストピースの更新
        self.ghost_piece = self.get_ghost_piece()

        # ゲームオーバーチェック（新しいピースが配置できない場合）
        if not self.valid_move(self.current_piece):
            self.game_over = True
            if game_over_sound and has_sound and settings.get("sound", True):
                game_over_sound.play()

    def check_lines(self):
        """完成したラインをチェックして消去する"""
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(cell is not None for cell in self.grid[y]):
                lines_to_clear.append(y)

        lines_count = len(lines_to_clear)
        if lines_count == 0:
            return

        # 効果音を決定
        clear_sound_to_play = None
        if lines_count == 4 and "tetris_sound" in globals() and tetris_sound:
            clear_sound_to_play = tetris_sound
        elif lines_count > 0 and "clear_sound" in globals() and clear_sound:
            clear_sound_to_play = clear_sound

        # スコア計算
        # T-Spinボーナス
        tspin_type = self.check_tspin()
        tspin_bonus = 0
        if tspin_type:
            self.tspin_count += 1
            if tspin_type == "T-Spin Mini":
                tspin_bonus = 100 * self.level
            else:
                tspin_bonus = 400 * self.level

        # ライン消去ボーナス
        line_bonus = 0
        if lines_count == 1:
            line_bonus = 100 * self.level
        elif lines_count == 2:
            line_bonus = 300 * self.level
        elif lines_count == 3:
            line_bonus = 500 * self.level
        elif lines_count == 4:
            line_bonus = 800 * self.level

        # 合計スコア
        self.score += line_bonus + tspin_bonus

        # コンボボーナス
        self.combo += 1
        if self.combo > 1:
            combo_bonus = 50 * self.combo * self.level
            self.score += combo_bonus
            # コンボテキスト表示
            combo_text = f"{self.combo} Combo!"
            self.add_floating_text(
                grid_x + (GRID_WIDTH * BLOCK_SIZE * scale_factor) // 2,
                grid_y + (GRID_HEIGHT * BLOCK_SIZE * scale_factor) // 2,
                combo_text,
                (255, 255, 0),
                36,
            )

        # ライン消去テキスト表示
        if lines_count > 0:
            clear_text = ""
            if tspin_type:
                clear_text += f"{tspin_type} "
            if lines_count == 1:
                clear_text += "Single"
            elif lines_count == 2:
                clear_text += "Double"
            elif lines_count == 3:
                clear_text += "Triple"
            elif lines_count == 4:
                clear_text += "Tetris!"

            self.add_floating_text(
                grid_x + (GRID_WIDTH * BLOCK_SIZE * scale_factor) // 2,
                grid_y + (GRID_HEIGHT * BLOCK_SIZE * scale_factor) // 2 - 40,
                clear_text,
                (255, 255, 0),
                36,
            )

        # レベルアップ処理
        self.lines_cleared += lines_count
        old_level = self.level
        self.level = self.lines_cleared // 10 + 1
        if self.level > old_level:
            # レベルアップテキスト表示
            self.add_floating_text(
                grid_x + (GRID_WIDTH * BLOCK_SIZE * scale_factor) // 2,
                grid_y + (GRID_HEIGHT * BLOCK_SIZE * scale_factor) // 2 - 80,
                f"Level Up! {self.level}",
                (255, 255, 0),
                36,
            )
            # 落下速度の更新
            self.fall_speed = max(0.05, 1 - ((self.level - 1) * 0.05))

        # 効果音
        if clear_sound_to_play and has_sound and settings.get("sound", True):
            clear_sound_to_play.play()

        # パーティクルエフェクト
        for y in lines_to_clear:
            # ライン全体にエフェクトを追加
            self.particle_system.create_line_clear_effect(
                grid_x,
                grid_y + (y + 0.5) * BLOCK_SIZE * scale_factor,
                (255, 255, 255),  # 白色のパーティクル
                30,  # パーティクル数を増やす
            )

            # 各ブロックにもエフェクトを追加
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    self.particle_system.create_explosion(
                        grid_x + (x + 0.5) * BLOCK_SIZE * scale_factor,
                        grid_y + (y + 0.5) * BLOCK_SIZE * scale_factor,
                        self.grid[y][x],
                        15,
                    )

        # 改善: 一時的なグリッドを作成して、ラインクリア後の状態を正確に計算
        new_grid = []
        # 消去されないラインだけを新しいグリッドに追加
        for y in range(GRID_HEIGHT):
            if y not in lines_to_clear:
                new_grid.append(self.grid[y])

        # 消去されたライン数だけ上に空のラインを追加
        for _ in range(lines_count):
            new_grid.insert(0, [None for _ in range(GRID_WIDTH)])

        # 新しいグリッドで置き換え
        self.grid = new_grid

        # スプリントモードのクリア条件チェック
        if self.game_mode == "sprint" and self.lines_cleared >= self.lines_target:
            self.game_clear = True

    def drop(self):
        """ピースを一番下まで落とす（ハードドロップ）"""
        if self.game_over or self.paused or not self.current_piece:
            return

        # 落下距離を計算（スコア計算用）
        drop_distance = 0

        # 可能な限り下に移動
        while self.valid_move(self.current_piece, y_offset=1):
            self.current_piece["y"] += 1
            drop_distance += 1

        # ハードドロップボーナス（2点/セル）
        self.score += drop_distance * 2

        # ピースを固定
        self.lock_piece()

    def hold_piece(self):
        """現在のピースをホールドする"""
        if self.game_over or self.paused or not self.current_piece or not self.can_hold:
            return

        # 効果音
        if hold_sound and has_sound and settings.get("sound", True):
            hold_sound.play()

        # 初回ホールドの場合
        if self.held_piece is None:
            self.held_piece = {
                "shape": [
                    row[:] for row in TETROMINOS[self.current_piece["index"]]["shape"]
                ],
                "color": theme["blocks"][
                    TETROMINOS[self.current_piece["index"]]["color"]
                ],
                "index": self.current_piece["index"],
                "rotation": 0,
            }
            # 次のピースを取得
            self.current_piece = self.next_pieces.pop(0)
            self.next_pieces.append(self.get_next_piece())
        else:
            # ホールドピースと現在のピースを交換
            temp = self.held_piece
            self.held_piece = {
                "shape": [
                    row[:] for row in TETROMINOS[self.current_piece["index"]]["shape"]
                ],
                "color": theme["blocks"][
                    TETROMINOS[self.current_piece["index"]]["color"]
                ],
                "index": self.current_piece["index"],
                "rotation": 0,
            }
            self.current_piece = {
                "shape": [row[:] for row in TETROMINOS[temp["index"]]["shape"]],
                "color": theme["blocks"][TETROMINOS[temp["index"]]["color"]],
                "x": GRID_WIDTH // 2 - len(TETROMINOS[temp["index"]]["shape"][0]) // 2,
                "y": 0,
                "rotation": 0,
                "index": temp["index"],
            }

        # ホールド使用フラグを設定
        self.can_hold = False
        self.has_used_hold = True

        # ゴーストピースの更新
        self.ghost_piece = self.get_ghost_piece()

    def check_tspin(self):
        """T-Spinの条件をチェックする"""
        if self.current_piece["index"] != 2:  # T型でない場合
            self.is_tspin = False
            return

        # T-Spinの条件：T型の4隅のうち3つ以上が埋まっている
        corners_filled = 0
        t_x, t_y = self.current_piece["x"], self.current_piece["y"]

        # T型の中心座標
        center_x = t_x + 1
        center_y = t_y + 1

        # 4隅の座標
        corners = [
            (center_x - 1, center_y - 1),  # 左上
            (center_x + 1, center_y - 1),  # 右上
            (center_x - 1, center_y + 1),  # 左下
            (center_x + 1, center_y + 1),  # 右下
        ]

        # 各隅が埋まっているかチェック
        for cx, cy in corners:
            if (
                cx < 0
                or cx >= GRID_WIDTH
                or cy < 0
                or cy >= GRID_HEIGHT
                or (cy >= 0 and cx >= 0 and self.grid[cy][cx] is not None)
            ):
                corners_filled += 1

        # T-Spinの条件：3つ以上の隅が埋まっている
        self.is_tspin = corners_filled >= 3

    def toggle_pause(self):
        """ゲームの一時停止/再開を切り替える"""
        self.paused = not self.paused

        # BGMの一時停止/再開
        if has_music and settings.get("music", True):
            if self.paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    def draw(self):
        """ゲーム画面を描画する"""
        # 背景
        screen.fill(theme["background"])

        # グリッド背景
        pygame.draw.rect(
            screen,
            theme["grid_bg"],
            (
                grid_x,
                grid_y,
                GRID_WIDTH * BLOCK_SIZE * scale_factor,
                GRID_HEIGHT * BLOCK_SIZE * scale_factor,
            ),
        )

        # グリッドライン
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(
                screen,
                theme["grid_line"],
                (
                    grid_x + x * BLOCK_SIZE * scale_factor,
                    grid_y,
                ),
                (
                    grid_x + x * BLOCK_SIZE * scale_factor,
                    grid_y + GRID_HEIGHT * BLOCK_SIZE * scale_factor,
                ),
                1,
            )

        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(
                screen,
                theme["grid_line"],
                (
                    grid_x,
                    grid_y + y * BLOCK_SIZE * scale_factor,
                ),
                (
                    grid_x + GRID_WIDTH * BLOCK_SIZE * scale_factor,
                    grid_y + y * BLOCK_SIZE * scale_factor,
                ),
                1,
            )

        # グリッド内のブロックを描画
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    self.draw_block(x, y, self.grid[y][x])

        # ゴーストピースの描画
        if self.ghost_piece and settings.get("ghost_piece", True):
            for y, row in enumerate(self.ghost_piece["shape"]):
                for x, cell in enumerate(row):
                    if cell:
                        ghost_x = self.ghost_piece["x"] + x
                        ghost_y = self.ghost_piece["y"] + y

                        # 半透明のゴーストピース
                        ghost_color = self.ghost_piece["color"]
                        if len(ghost_color) == 3:
                            ghost_color = (*ghost_color, 100)  # アルファ値を追加
                        else:
                            ghost_color = (*ghost_color[:3], 100)  # アルファ値を変更

                        # 枠線のみのブロック
                        block_rect = pygame.Rect(
                            grid_x + ghost_x * BLOCK_SIZE * scale_factor,
                            grid_y + ghost_y * BLOCK_SIZE * scale_factor,
                            BLOCK_SIZE * scale_factor,
                            BLOCK_SIZE * scale_factor,
                        )
                        pygame.draw.rect(screen, ghost_color, block_rect, 2)

        # 現在のピースの描画
        if self.current_piece:
            for y, row in enumerate(self.current_piece["shape"]):
                for x, cell in enumerate(row):
                    if cell:
                        self.draw_block(
                            self.current_piece["x"] + x,
                            self.current_piece["y"] + y,
                            self.current_piece["color"],
                        )

        # 次のピースの表示
        next_text = font.render("NEXT", True, theme["text"])
        screen.blit(
            next_text,
            (
                grid_x + (GRID_WIDTH * BLOCK_SIZE + 80) * scale_factor,
                grid_y + 20 * scale_factor,
            ),
        )

        for i, next_piece in enumerate(self.next_pieces[:5]):  # 次の5つのピースを表示
            next_x = grid_x + (GRID_WIDTH * BLOCK_SIZE + 100) * scale_factor
            next_y = grid_y + (80 + i * 80) * scale_factor

            # ピースの形状に応じて位置を調整
            offset_x = 0
            if next_piece["index"] == 0:  # I型
                offset_x = -0.5 * BLOCK_SIZE * scale_factor
            elif next_piece["index"] in [2, 3, 4]:  # T, J, L型
                offset_x = 0

            # 次のピースを描画
            for y, row in enumerate(next_piece["shape"]):
                for x, cell in enumerate(row):
                    if cell:
                        block_rect = pygame.Rect(
                            next_x + (x * BLOCK_SIZE + offset_x) * scale_factor,
                            next_y + y * BLOCK_SIZE * scale_factor,
                            BLOCK_SIZE * scale_factor,
                            BLOCK_SIZE * scale_factor,
                        )
                        pygame.draw.rect(screen, next_piece["color"], block_rect)
                        pygame.draw.rect(screen, theme["ui_border"], block_rect, 1)

        # ホールドピースの表示
        hold_text = font.render("HOLD", True, theme["text"])
        screen.blit(
            hold_text,
            (
                grid_x - 150 * scale_factor,
                grid_y + 20 * scale_factor,
            ),
        )

        if self.held_piece:
            hold_x = grid_x - 130 * scale_factor
            hold_y = grid_y + 80 * scale_factor

            # ピースの形状に応じて位置を調整
            offset_x = 0
            if self.held_piece["index"] == 0:  # I型
                offset_x = -0.5 * BLOCK_SIZE * scale_factor
            elif self.held_piece["index"] in [2, 3, 4]:  # T, J, L型
                offset_x = 0

            # ホールドピースを描画（使用済みの場合は半透明）
            for y, row in enumerate(self.held_piece["shape"]):
                for x, cell in enumerate(row):
                    if cell:
                        block_rect = pygame.Rect(
                            hold_x + (x * BLOCK_SIZE + offset_x) * scale_factor,
                            hold_y + y * BLOCK_SIZE * scale_factor,
                            BLOCK_SIZE * scale_factor,
                            BLOCK_SIZE * scale_factor,
                        )

                        # 使用済みの場合は半透明
                        if not self.can_hold:
                            hold_color = (*self.held_piece["color"][:3], 128)
                            pygame.draw.rect(screen, hold_color, block_rect)
                        else:
                            pygame.draw.rect(
                                screen, self.held_piece["color"], block_rect
                            )

                        pygame.draw.rect(screen, theme["ui_border"], block_rect, 1)

        # スコア情報の表示
        score_x = grid_x - 180 * scale_factor
        score_y = grid_y + 200 * scale_factor

        score_text = font.render(f"スコア: {self.score}", True, theme["text"])
        level_text = font.render(f"レベル: {self.level}", True, theme["text"])
        lines_text = font.render(f"ライン: {self.lines_cleared}", True, theme["text"])

        # ゲームモードに応じた追加情報
        if self.game_mode == "sprint":
            # スプリントモード：残りライン数
            remaining = max(0, self.lines_target - self.lines_cleared)
            mode_text = font.render(f"残り: {remaining}ライン", True, theme["text"])
        elif self.game_mode == "ultra":
            # ウルトラモード：残り時間
            remaining = max(0, self.time_limit - self.time_played)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            mode_text = font.render(
                f"残り時間: {minutes}:{seconds:02d}", True, theme["text"]
            )
        else:
            # マラソンモード：プレイ時間
            minutes = int(self.time_played // 60)
            seconds = int(self.time_played % 60)
            mode_text = font.render(
                f"時間: {minutes}:{seconds:02d}", True, theme["text"]
            )

        screen.blit(score_text, (score_x, score_y))
        screen.blit(level_text, (score_x, score_y + 40 * scale_factor))
        screen.blit(lines_text, (score_x, score_y + 80 * scale_factor))
        screen.blit(mode_text, (score_x, score_y + 120 * scale_factor))

        # 操作説明
        controls_x = grid_x - 180 * scale_factor
        controls_y = grid_y + 350 * scale_factor

        controls = [
            "← → : 移動",
            "↓ : ソフトドロップ",
            "↑ : 回転（時計回り）",
            "Z : 回転（反時計回り）",
            "スペース : ハードドロップ",
            "C : ホールド",
            "P : 一時停止",
            "ESC : メニュー",
        ]

        for i, control in enumerate(controls):
            control_text = small_font.render(control, True, theme["text"])
            screen.blit(control_text, (controls_x, controls_y + i * 25 * scale_factor))

        # パーティクルの描画
        self.particle_system.draw(screen)

        # フローティングテキストの描画
        for text in self.floating_texts:
            text.draw(screen)

        # ゲームオーバー画面
        if self.game_over:
            return self.draw_game_over_screen()

        # ゲームクリア画面
        if self.game_clear:
            return self.draw_game_clear_screen()

        return None

    def draw_block(self, x, y, color):
        """ブロックを描画する"""
        block_rect = pygame.Rect(
            grid_x + x * BLOCK_SIZE * scale_factor,
            grid_y + y * BLOCK_SIZE * scale_factor,
            BLOCK_SIZE * scale_factor,
            BLOCK_SIZE * scale_factor,
        )
        pygame.draw.rect(screen, color, block_rect)
        pygame.draw.rect(screen, theme["ui_border"], block_rect, 1)

    def draw_game_over_screen(self):
        """ゲームオーバー画面を描画する"""
        # 半透明のオーバーレイ
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # メニューパネル
        panel_width = 400 * scale_factor
        panel_height = 400 * scale_factor
        panel_x = (screen_width - panel_width) // 2
        panel_y = (screen_height - panel_height) // 2

        pygame.draw.rect(
            screen, theme["ui_bg"], (panel_x, panel_y, panel_width, panel_height)
        )
        pygame.draw.rect(
            screen, theme["ui_border"], (panel_x, panel_y, panel_width, panel_height), 3
        )

        # タイトル
        title_text = title_font.render("ゲームオーバー", True, (255, 100, 100))
        screen.blit(
            title_text,
            (
                screen_width // 2 - title_text.get_width() // 2,
                panel_y + 30 * scale_factor,
            ),
        )

        # 結果表示
        score_text = font.render(f"スコア: {self.score}", True, theme["text"])
        level_text = font.render(f"レベル: {self.level}", True, theme["text"])
        lines_text = font.render(f"ライン: {self.lines_cleared}", True, theme["text"])

        time_minutes = int(self.time_played // 60)
        time_seconds = int(self.time_played % 60)
        time_text = font.render(
            f"プレイ時間: {time_minutes}:{time_seconds:02d}", True, theme["text"]
        )

        # ハイスコア？
        is_high_score = self.check_high_score()
        high_score_text = None  # 変数を初期化

        if is_high_score:
            # 新記録達成テキストを点滅させる
            if pygame.time.get_ticks() % 1000 < 800:  # 1秒のうち0.8秒間表示
                high_score_text = big_font.render("新記録達成！", True, (255, 255, 0))

            # high_score_textが定義されている場合のみ描画
            if high_score_text:
                screen.blit(
                    high_score_text,
                    (
                        screen_width // 2 - high_score_text.get_width() // 2,
                        panel_y + 80 * scale_factor,
                    ),
                )

        screen.blit(
            score_text,
            (
                screen_width // 2 - score_text.get_width() // 2,
                panel_y + 120 * scale_factor,
            ),
        )
        screen.blit(
            level_text,
            (
                screen_width // 2 - level_text.get_width() // 2,
                panel_y + 160 * scale_factor,
            ),
        )
        screen.blit(
            lines_text,
            (
                screen_width // 2 - lines_text.get_width() // 2,
                panel_y + 200 * scale_factor,
            ),
        )
        screen.blit(
            time_text,
            (
                screen_width // 2 - time_text.get_width() // 2,
                panel_y + 240 * scale_factor,
            ),
        )

        # リトライボタン
        retry_button = Button(
            panel_x + panel_width // 2 - 100 * scale_factor,
            panel_y + 300 * scale_factor,
            200 * scale_factor,
            40 * scale_factor,
            "リトライ",
            action=lambda: "retry",
        )

        menu_button = Button(
            panel_x + panel_width // 2 - 100 * scale_factor,
            panel_y + 350 * scale_factor,
            200 * scale_factor,
            40 * scale_factor,
            "メニューに戻る",
            action=lambda: "menu",
        )

        mouse_pos = pygame.mouse.get_pos()
        retry_button.update(mouse_pos)
        retry_button.draw(screen)

        menu_button.update(mouse_pos)
        menu_button.draw(screen)

        return [retry_button, menu_button]

    def draw_pause_menu(self):
        """ポーズメニューを描画する"""
        # 半透明のオーバーレイ
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # 半透明の黒（より暗く）
        screen.blit(overlay, (0, 0))

        # パネルの寸法と位置
        panel_width = 400 * scale_factor
        panel_height = 450 * scale_factor
        panel_x = screen_width // 2 - panel_width // 2
        panel_y = screen_height // 2 - panel_height // 2

        # VSCode風のコマンドパレット風パネル
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((45, 45, 45, 250))  # VSCodeのコマンドパレット背景色

        # パネルの角丸と枠線
        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        corner_radius = int(6 * scale_factor)  # VSCodeは角が少し丸い
        pygame.draw.rect(
            panel, (50, 50, 50, 255), panel_rect, border_radius=corner_radius
        )
        pygame.draw.rect(
            panel, (70, 70, 70), panel_rect, width=1, border_radius=corner_radius
        )

        screen.blit(panel, (panel_x, panel_y))

        # VSCode風の検索バー
        search_bar_height = 40 * scale_factor
        search_bar_rect = pygame.Rect(
            panel_x + 20 * scale_factor,
            panel_y + 20 * scale_factor,
            panel_width - 40 * scale_factor,
            search_bar_height,
        )
        pygame.draw.rect(
            screen, (60, 60, 60), search_bar_rect, border_radius=int(4 * scale_factor)
        )
        pygame.draw.rect(
            screen,
            (80, 80, 80),
            search_bar_rect,
            width=1,
            border_radius=int(4 * scale_factor),
        )

        # 検索アイコン
        icon_size = 16 * scale_factor
        pygame.draw.circle(
            screen,
            (180, 180, 180),
            (
                int(panel_x + 40 * scale_factor),
                int(panel_y + 20 * scale_factor + search_bar_height / 2),
            ),
            int(icon_size / 2),
            1,
        )

        # 検索テキスト
        search_text = font.render("ポーズメニュー", True, (180, 180, 180))
        screen.blit(
            search_text,
            (
                panel_x + 60 * scale_factor,
                panel_y
                + 20 * scale_factor
                + search_bar_height / 2
                - search_text.get_height() / 2,
            ),
        )

        # ボタンの作成（VSCode風のコマンドパレット項目）
        buttons = []
        button_y_start = panel_y + 80 * scale_factor
        button_height = 50 * scale_factor
        button_spacing = 10 * scale_factor
        button_width = panel_width - 40 * scale_factor

        # 再開ボタン
        resume_button = Button(
            panel_x + 20 * scale_factor,
            button_y_start,
            button_width,
            button_height,
            "ゲームを再開",
            action="resume",
            bg_color=(58, 58, 58),
            text_color=(212, 212, 212),
        )

        # テーマ切替ボタン
        theme_button = Button(
            panel_x + 20 * scale_factor,
            button_y_start + (button_height + button_spacing),
            button_width,
            button_height,
            f"テーマ: {current_theme.capitalize()}",
            action="theme",
            bg_color=(58, 58, 58),
            text_color=(212, 212, 212),
        )

        # フルスクリーン切替ボタン
        fullscreen_button = Button(
            panel_x + 20 * scale_factor,
            button_y_start + (button_height + button_spacing) * 2,
            button_width,
            button_height,
            "フルスクリーン切替",
            action="fullscreen",
            bg_color=(58, 58, 58),
            text_color=(212, 212, 212),
        )

        # メニューに戻るボタン
        quit_button = Button(
            panel_x + 20 * scale_factor,
            button_y_start + (button_height + button_spacing) * 3,
            button_width,
            button_height,
            "メニューに戻る",
            action="quit",
            bg_color=(58, 58, 58),
            text_color=(212, 212, 212),
        )

        buttons = [resume_button, theme_button, fullscreen_button, quit_button]

        # マウス位置の取得と更新
        mouse_pos = pygame.mouse.get_pos()
        for button in buttons:
            button.update(mouse_pos)
            button.draw(screen)

        # VSCode風のキーボードショートカット表示
        shortcut_y = panel_y + panel_height - 30 * scale_factor
        shortcut_text = small_font.render(
            "ESCキーでゲームに戻る", True, (150, 150, 150)
        )
        screen.blit(
            shortcut_text,
            (
                screen_width // 2 - shortcut_text.get_width() // 2,
                shortcut_y,
            ),
        )

        return buttons

    def check_high_score(self):
        """ハイスコアをチェックして保存する"""
        high_scores = load_high_scores()
        mode_scores = high_scores.get(self.game_mode, [])

        # スプリントモードでゲームオーバー時（クリアしていない場合）はハイスコアに登録しない
        if self.game_mode == "sprint" and not self.game_clear:
            return False

        # 新しいスコアエントリを作成
        new_score = {
            "score": self.score,
            "level": self.level,
            "lines": self.lines_cleared,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "id": str(uuid.uuid4())[:8],  # ユニークID
        }

        # スプリントモードの場合は時間を記録
        if self.game_mode == "sprint":
            new_score["time"] = self.time_played

        # 既存のスコアと重複しないようにする
        # 同じ日付・スコア・レベルの組み合わせがあれば追加しない
        is_duplicate = False
        for score in mode_scores:
            if (
                score.get("date") == new_score["date"]
                and score.get("score") == new_score["score"]
                and score.get("level") == new_score["level"]
            ):
                is_duplicate = True
                break

        # 重複していない場合のみ追加
        if not is_duplicate:
            # ハイスコアリストに追加
            mode_scores.append(new_score)

            # スコアでソート
            if self.game_mode == "sprint":
                # スプリントモードは時間が短い順
                mode_scores.sort(key=lambda x: x.get("time", float("inf")))
            else:
                # その他のモードはスコアが高い順
                mode_scores.sort(key=lambda x: x.get("score", 0), reverse=True)

            # 上位10件のみ保持
            high_scores[self.game_mode] = mode_scores[:10]

            # ハイスコアを保存
            save_high_scores(high_scores)

        # 新しいスコアがトップ5に入っているかチェック
        is_high_score = False
        for i, score in enumerate(mode_scores[:5]):
            if score["id"] == new_score["id"]:
                is_high_score = True
                break

        return is_high_score

    def add_floating_text(self, x, y, text, color, size=28, life=1.5):
        """フローティングテキストを追加する"""
        self.floating_texts.append(FloatingText(x, y, text, color, size, life))


# ウィンドウタイトル設定
pygame.display.set_caption("テトリス")

# フォントの初期化
init_fonts()

# テーマの設定
current_theme = settings.get("theme", "classic")
theme = THEMES[current_theme]

# サウンドの初期化
has_music = False

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

    # BGMの読み込み
    pygame.mixer.music.load("assets/tetris_theme.mp3")
    pygame.mixer.music.set_volume(0.5)
    has_music = True
except Exception as e:
    print(f"音声ファイルの読み込みエラー: {e}")

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


# スタートメニューの描画
def draw_start_menu():
    # 背景
    screen.fill(theme["background"])

    # 背景グラデーション効果
    gradient_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    for i in range(screen_height):
        alpha = max(0, 40 - (i // 10))
        color = (*theme["ui_border"][:3], alpha)
        pygame.draw.line(gradient_surface, color, (0, i), (screen_width, i))
    screen.blit(gradient_surface, (0, 0))

    # 装飾的な背景パターン
    for i in range(20):
        size = random.randint(5, 20) * scale_factor
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        alpha = random.randint(10, 40)
        color = (*theme["ui_border"][:3], alpha)
        pygame.draw.rect(
            screen, color, pygame.Rect(x, y, size, size), border_radius=int(size // 3)
        )

    # メインパネル
    panel_width = 500 * scale_factor
    panel_height = 550 * scale_factor
    panel_x = screen_width // 2 - panel_width // 2
    panel_y = screen_height // 2 - panel_height // 2 - 20 * scale_factor

    # 半透明のパネル背景
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((30, 30, 30, 180))  # 半透明のダークグレー

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(20 * scale_factor)
    pygame.draw.rect(panel, (50, 50, 50, 200), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel, theme["ui_border"], panel_rect, width=2, border_radius=corner_radius
    )

    # グラデーション効果（上部を少し明るく）
    gradient_height = int(panel_height // 3)
    for i in range(gradient_height):
        alpha = 40 - int(40 * i / gradient_height)
        highlight_color = (255, 255, 255, alpha)
        pygame.draw.rect(
            panel,
            highlight_color,
            pygame.Rect(0, i, panel_width, 1),
            border_radius=corner_radius if i == 0 else 0,
        )

    screen.blit(panel, (panel_x, panel_y))

    # タイトル
    title_text = title_font.render("テトリス", True, theme["text"])
    title_shadow = title_font.render("テトリス", True, (0, 0, 0, 150))

    # タイトルの影
    screen.blit(
        title_shadow,
        (
            screen_width // 2 - title_text.get_width() // 2 + 3 * scale_factor,
            panel_y + 50 * scale_factor + 3 * scale_factor,
        ),
    )

    # タイトル
    screen.blit(
        title_text,
        (screen_width // 2 - title_text.get_width() // 2, panel_y + 50 * scale_factor),
    )

    # 装飾ライン
    line_y = panel_y + 120 * scale_factor
    line_width = panel_width - 60 * scale_factor
    line_x = panel_x + 30 * scale_factor

    pygame.draw.line(
        screen,
        theme["ui_border"],
        (line_x, line_y),
        (line_x + line_width, line_y),
        width=2,
    )

    # ボタンの作成
    buttons = []

    # スタートボタン
    start_button = Button(
        screen_width // 2 - 150 * scale_factor,
        panel_y + 170 * scale_factor,
        300 * scale_factor,
        50 * scale_factor,
        "ゲームスタート",
        action="start",
    )

    # ゲームモード切替ボタン
    mode_button = Button(
        screen_width // 2 - 150 * scale_factor,
        panel_y + 240 * scale_factor,
        300 * scale_factor,
        50 * scale_factor,
        f"モード: {settings.get('game_mode', 'marathon').capitalize()}",
        action="game_mode",
    )

    # 設定ボタン
    settings_button = Button(
        screen_width // 2 - 150 * scale_factor,
        panel_y + 310 * scale_factor,
        300 * scale_factor,
        50 * scale_factor,
        "設定",
        action="settings",
    )

    # テーマ切替ボタン
    theme_button = Button(
        screen_width // 2 - 150 * scale_factor,
        panel_y + 380 * scale_factor,
        300 * scale_factor,
        50 * scale_factor,
        f"テーマ: {current_theme.capitalize()}",
        action="theme",
    )

    # ハイスコアボタン
    high_scores_button = Button(
        screen_width // 2 - 150 * scale_factor,
        panel_y + 450 * scale_factor,
        300 * scale_factor,
        50 * scale_factor,
        "ハイスコア",
        action="high_scores",
    )

    # 終了ボタン
    quit_button = Button(
        screen_width // 2 - 150 * scale_factor,
        panel_y + 520 * scale_factor,
        300 * scale_factor,
        50 * scale_factor,
        "終了",
        action="quit",
    )

    buttons.append(start_button)
    buttons.append(mode_button)
    buttons.append(settings_button)
    buttons.append(theme_button)
    buttons.append(high_scores_button)
    buttons.append(quit_button)

    # マウス位置の取得
    mouse_pos = pygame.mouse.get_pos()

    # ボタンの更新と描画
    for button in buttons:
        button.update(mouse_pos)
        button.draw(screen)

    # バージョン情報
    version_text = small_font.render("v1.0.0", True, (150, 150, 150))
    screen.blit(
        version_text,
        (
            screen_width - version_text.get_width() - 10 * scale_factor,
            screen_height - version_text.get_height() - 10 * scale_factor,
        ),
    )

    return buttons


# ハイスコア画面の描画
def draw_high_scores(game):
    # 背景
    screen.fill(theme["background"])

    # VSCode風のグリッドパターン
    grid_size = 20 * scale_factor
    for x in range(0, screen_width, int(grid_size)):
        pygame.draw.line(screen, (50, 50, 50, 30), (x, 0), (x, screen_height), 1)
    for y in range(0, screen_height, int(grid_size)):
        pygame.draw.line(screen, (50, 50, 50, 30), (0, y), (screen_width, y), 1)

    # VSCode風のアクティビティバー（左側）
    activity_bar_width = 50 * scale_factor
    pygame.draw.rect(screen, (40, 40, 40), (0, 0, activity_bar_width, screen_height))

    # アイコン（シンプルな形で表現）
    icon_size = 24 * scale_factor
    icon_margin = 20 * scale_factor

    # ファイルアイコン
    pygame.draw.rect(
        screen,
        (200, 200, 200),
        (activity_bar_width / 2 - icon_size / 2, icon_margin, icon_size, icon_size),
        2,
    )

    # 検索アイコン（円と線）
    pygame.draw.circle(
        screen,
        (200, 200, 200),
        (int(activity_bar_width / 2), int(icon_margin * 2 + icon_size * 1.5)),
        int(icon_size / 3),
        2,
    )

    # メインパネル
    panel_width = 700 * scale_factor
    panel_height = 500 * scale_factor
    panel_x = screen_width // 2 - panel_width // 2
    panel_y = screen_height // 2 - panel_height // 2

    # VSCode風のエディタパネル
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((45, 45, 45, 240))  # VSCodeのエディタ背景色

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(8 * scale_factor)  # VSCodeは角が少し丸い
    pygame.draw.rect(panel, (50, 50, 50, 255), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel, (70, 70, 70), panel_rect, width=1, border_radius=corner_radius
    )

    # VSCode風のタブバー
    tab_height = 35 * scale_factor
    pygame.draw.rect(panel, (37, 37, 38), (0, 0, panel_width, tab_height))

    # アクティブなタブ
    tab_width = 180 * scale_factor
    pygame.draw.rect(panel, (45, 45, 45), (10 * scale_factor, 0, tab_width, tab_height))

    # タブのテキスト
    tab_text = small_font.render("highscores.json", True, (212, 212, 212))
    panel.blit(
        tab_text, (20 * scale_factor, tab_height / 2 - tab_text.get_height() / 2)
    )

    screen.blit(panel, (panel_x, panel_y))

    # タイトル
    title_text = title_font.render("ハイスコア", True, (212, 212, 212))
    screen.blit(
        title_text,
        (panel_x + 20 * scale_factor, panel_y + tab_height + 20 * scale_factor),
    )

    # ゲームモード選択タブ
    modes = ["marathon", "sprint", "ultra"]
    mode_tabs = []
    mode_tab_width = panel_width / len(modes)

    for i, mode in enumerate(modes):
        mode_tab_rect = pygame.Rect(
            panel_x + i * mode_tab_width,
            panel_y + tab_height + 60 * scale_factor,
            mode_tab_width,
            30 * scale_factor,
        )

        # アクティブなモードのタブをハイライト
        if mode == game.game_mode:
            pygame.draw.rect(screen, (60, 60, 60), mode_tab_rect)
            pygame.draw.line(
                screen,
                (0, 122, 204),
                (mode_tab_rect.x, mode_tab_rect.y + mode_tab_rect.height - 2),
                (
                    mode_tab_rect.x + mode_tab_rect.width,
                    mode_tab_rect.y + mode_tab_rect.height - 2,
                ),
                2,
            )
            text_color = (255, 255, 255)
        else:
            text_color = (150, 150, 150)

        # モード名
        mode_text = font.render(mode.capitalize(), True, text_color)
        screen.blit(
            mode_text,
            (
                mode_tab_rect.x + mode_tab_rect.width / 2 - mode_text.get_width() / 2,
                mode_tab_rect.y + mode_tab_rect.height / 2 - mode_text.get_height() / 2,
            ),
        )

        mode_tabs.append((mode_tab_rect, mode))

    # VSCode風のテーブルヘッダー
    header_y = panel_y + tab_height + 100 * scale_factor
    header_height = 30 * scale_factor
    col_widths = [0.1, 0.4, 0.25, 0.25]  # 列の幅の比率

    # ヘッダー背景
    pygame.draw.rect(
        screen,
        (60, 60, 60),
        (
            panel_x + 20 * scale_factor,
            header_y,
            panel_width - 40 * scale_factor,
            header_height,
        ),
    )

    # ヘッダーテキスト
    headers = ["#", "スコア", "レベル", "日付"]
    for i, header in enumerate(headers):
        x_pos = (
            panel_x
            + 20 * scale_factor
            + sum(col_widths[:i]) * (panel_width - 40 * scale_factor)
        )
        header_text = font.render(header, True, (212, 212, 212))
        screen.blit(
            header_text,
            (
                x_pos + 10 * scale_factor,
                header_y + header_height / 2 - header_text.get_height() / 2,
            ),
        )

    # ハイスコアの表示
    high_scores = load_high_scores()
    mode_scores = high_scores.get(game.game_mode, [])

    row_height = 40 * scale_factor
    for i, score in enumerate(mode_scores[:10]):
        row_y = header_y + header_height + i * row_height

        # 交互に背景色を変える（VSCode風）
        if i % 2 == 0:
            pygame.draw.rect(
                screen,
                (50, 50, 50),
                (
                    panel_x + 20 * scale_factor,
                    row_y,
                    panel_width - 40 * scale_factor,
                    row_height,
                ),
            )

        # 順位
        rank_text = font.render(f"{i+1}", True, (212, 212, 212))
        screen.blit(
            rank_text,
            (
                panel_x + 30 * scale_factor,
                row_y + row_height / 2 - rank_text.get_height() / 2,
            ),
        )

        # スコア
        score_value = score.get("score", 0)
        if game.game_mode == "sprint":
            minutes = int(score.get("time", 0) // 60)
            seconds = int(score.get("time", 0) % 60)
            score_text = font.render(f"{minutes}:{seconds:02d}", True, (86, 156, 214))
        else:
            score_text = font.render(f"{score_value}", True, (86, 156, 214))

        x_pos = (
            panel_x
            + 20 * scale_factor
            + col_widths[0] * (panel_width - 40 * scale_factor)
        )
        screen.blit(
            score_text,
            (
                x_pos + 10 * scale_factor,
                row_y + row_height / 2 - score_text.get_height() / 2,
            ),
        )

        # レベル
        level_text = font.render(f"{score.get('level', 1)}", True, (212, 212, 212))
        x_pos = (
            panel_x
            + 20 * scale_factor
            + (col_widths[0] + col_widths[1]) * (panel_width - 40 * scale_factor)
        )
        screen.blit(
            level_text,
            (
                x_pos + 10 * scale_factor,
                row_y + row_height / 2 - level_text.get_height() / 2,
            ),
        )

        # 日付
        date_text = font.render(f"{score.get('date', '')}", True, (212, 212, 212))
        x_pos = (
            panel_x
            + 20 * scale_factor
            + (col_widths[0] + col_widths[1] + col_widths[2])
            * (panel_width - 40 * scale_factor)
        )
        screen.blit(
            date_text,
            (
                x_pos + 10 * scale_factor,
                row_y + row_height / 2 - date_text.get_height() / 2,
            ),
        )

    # 戻るボタン
    back_button = Button(
        panel_x + panel_width // 2 - 100 * scale_factor,
        panel_y + panel_height - 60 * scale_factor,
        200 * scale_factor,
        40 * scale_factor,
        "戻る",
        action="back",
        bg_color=(58, 58, 58),
        text_color=(212, 212, 212),
    )

    # マウス位置の取得
    mouse_pos = pygame.mouse.get_pos()
    back_button.update(mouse_pos)
    back_button.draw(screen)

    # VSCode風のステータスバー
    status_bar_height = 25 * scale_factor
    pygame.draw.rect(
        screen,
        (0, 122, 204),
        (0, screen_height - status_bar_height, screen_width, status_bar_height),
    )

    # ステータス情報
    status_text = small_font.render(
        f"モード: {game.game_mode.capitalize()}", True, (255, 255, 255)
    )
    screen.blit(
        status_text,
        (
            10 * scale_factor,
            screen_height - status_bar_height / 2 - status_text.get_height() / 2,
        ),
    )

    # ボタンリストを作成
    buttons = [back_button]

    # モードタブをボタンとして追加
    for rect, mode in mode_tabs:
        mode_button = Button(
            rect.x, rect.y, rect.width, rect.height, mode.capitalize(), action=mode
        )
        mode_button.update(mouse_pos)
        buttons.append(mode_button)

    return buttons


# 設定メニューの描画
def draw_settings_menu(scroll_offset=0):
    # 背景
    screen.fill(theme["background"])

    # 背景グラデーション効果
    gradient_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    for i in range(screen_height):
        alpha = max(0, 40 - (i // 10))
        color = (*theme["ui_border"][:3], alpha)
        pygame.draw.line(gradient_surface, color, (0, i), (screen_width, i))
    screen.blit(gradient_surface, (0, 0))

    # 装飾的な背景パターン
    for i in range(20):
        size = random.randint(5, 20) * scale_factor
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        alpha = random.randint(10, 40)
        color = (*theme["ui_border"][:3], alpha)
        pygame.draw.rect(
            screen, color, pygame.Rect(x, y, size, size), border_radius=int(size // 3)
        )

    # メインパネル
    panel_width = 600 * scale_factor
    panel_height = 550 * scale_factor
    panel_x = screen_width // 2 - panel_width // 2
    panel_y = screen_height // 2 - panel_height // 2 - 20 * scale_factor

    # 半透明のパネル背景
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((30, 30, 30, 180))  # 半透明のダークグレー

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(20 * scale_factor)
    pygame.draw.rect(panel, (50, 50, 50, 200), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel, theme["ui_border"], panel_rect, width=2, border_radius=corner_radius
    )

    # グラデーション効果（上部を少し明るく）
    gradient_height = int(panel_height // 3)
    for i in range(gradient_height):
        alpha = 40 - int(40 * i / gradient_height)
        highlight_color = (255, 255, 255, alpha)
        pygame.draw.rect(
            panel,
            highlight_color,
            pygame.Rect(0, i, panel_width, 1),
            border_radius=corner_radius if i == 0 else 0,
        )

    screen.blit(panel, (panel_x, panel_y))

    # タイトル
    title_text = title_font.render("設定", True, theme["text"])
    title_shadow = title_font.render("設定", True, (0, 0, 0, 150))

    # タイトルの影
    screen.blit(
        title_shadow,
        (
            screen_width // 2 - title_text.get_width() // 2 + 3 * scale_factor,
            panel_y + 30 * scale_factor + 3 * scale_factor,
        ),
    )

    # タイトル
    screen.blit(
        title_text,
        (screen_width // 2 - title_text.get_width() // 2, panel_y + 30 * scale_factor),
    )

    # 装飾ライン
    line_y = panel_y + 90 * scale_factor
    line_width = panel_width - 60 * scale_factor
    line_x = panel_x + 30 * scale_factor

    pygame.draw.line(
        screen,
        theme["ui_border"],
        (line_x, line_y),
        (line_x + line_width, line_y),
        width=2,
    )

    # スクロール可能な領域を示す
    scroll_hint_text = small_font.render(
        "↑↓ マウスホイールでスクロール", True, theme["text"]
    )
    screen.blit(
        scroll_hint_text,
        (
            screen_width // 2 - scroll_hint_text.get_width() // 2,
            panel_y + 110 * scale_factor,
        ),
    )

    # スクロール可能な領域を定義
    scroll_area_height = panel_height - 200 * scale_factor
    scroll_area = pygame.Rect(
        panel_x + 30 * scale_factor,
        panel_y + 140 * scale_factor,
        panel_width - 60 * scale_factor,
        scroll_area_height,
    )

    # スクロール可能な領域の背景
    scroll_bg = pygame.Surface((scroll_area.width, scroll_area.height), pygame.SRCALPHA)
    scroll_bg.fill((20, 20, 20, 100))
    pygame.draw.rect(
        scroll_bg,
        (40, 40, 40, 150),
        pygame.Rect(0, 0, scroll_area.width, scroll_area.height),
        border_radius=int(10 * scale_factor),
    )
    pygame.draw.rect(
        scroll_bg,
        (*theme["ui_border"][:3], 100),
        pygame.Rect(0, 0, scroll_area.width, scroll_area.height),
        width=1,
        border_radius=int(10 * scale_factor),
    )
    screen.blit(scroll_bg, (scroll_area.x, scroll_area.y))

    # ボタンの作成
    buttons = []

    # 各ボタンの基本Y位置（スクロールオフセットを適用）
    base_y = panel_y + 160 * scale_factor + scroll_offset

    # ボタン間の間隔
    button_spacing = 70 * scale_factor

    # ボタンの幅と位置
    button_width = panel_width - 100 * scale_factor
    button_x = screen_width // 2 - button_width // 2

    # エフェクト表示切替ボタン
    effects_status = "ON" if settings.get("effects", True) else "OFF"
    effects_button = Button(
        button_x,
        base_y,
        button_width,
        50 * scale_factor,
        f"エフェクト: {effects_status}",
        action="effects",
    )

    # エフェクトタイプ切替ボタン
    effect_type = settings.get("effect_type", "default")
    effect_type_display = {
        "default": "デフォルト",
        "explosion": "爆発",
        "rain": "雨",
        "spiral": "螺旋",
    }.get(effect_type, effect_type)

    effect_type_button = Button(
        button_x,
        base_y + button_spacing,
        button_width,
        50 * scale_factor,
        f"エフェクトタイプ: {effect_type_display}",
        action="effect_type",
    )

    # 音楽切替ボタン
    music_status = "ON" if settings.get("music", True) else "OFF"
    music_button = Button(
        button_x,
        base_y + button_spacing * 2,
        button_width,
        50 * scale_factor,
        f"音楽: {music_status}",
        action="music",
    )

    # 効果音切替ボタン
    sound_status = "ON" if settings.get("sound", True) else "OFF"
    sound_button = Button(
        button_x,
        base_y + button_spacing * 3,
        button_width,
        50 * scale_factor,
        f"効果音: {sound_status}",
        action="sound",
    )

    # ゴーストピース切替ボタン
    ghost_status = "ON" if settings.get("ghost_piece", True) else "OFF"
    ghost_button = Button(
        button_x,
        base_y + button_spacing * 4,
        button_width,
        50 * scale_factor,
        f"ゴーストピース: {ghost_status}",
        action="ghost_piece",
    )

    # キー設定ボタン
    key_config_button = Button(
        button_x,
        base_y + button_spacing * 5,
        button_width,
        50 * scale_factor,
        "キー設定",
        action="key_config",
    )

    # フルスクリーン切替ボタン
    fullscreen_button = Button(
        button_x,
        base_y + button_spacing * 6,
        button_width,
        50 * scale_factor,
        "フルスクリーン切替",
        action="fullscreen",
    )

    # 戻るボタン - 常に画面下部に固定
    back_button = Button(
        screen_width // 2 - 100 * scale_factor,
        panel_y + panel_height - 60 * scale_factor,
        200 * scale_factor,
        50 * scale_factor,
        "戻る",
        action="back",
    )

    # ボタンをリストに追加
    buttons.append(effects_button)
    buttons.append(effect_type_button)
    buttons.append(music_button)
    buttons.append(sound_button)
    buttons.append(ghost_button)
    buttons.append(key_config_button)
    buttons.append(fullscreen_button)

    # マウス位置の取得
    mouse_pos = pygame.mouse.get_pos()

    # スクロール可能なボタンの描画（スクロール領域内のみ表示）
    for button in buttons:
        # ボタンがスクロール領域内にあるかチェック
        if scroll_area.colliderect(button.rect):
            button.update(mouse_pos)
            button.draw(screen)

    # スクロールバーの描画（オプション）
    if len(buttons) > 0:
        # スクロール範囲の計算
        content_height = button_spacing * (len(buttons) - 1) + 50 * scale_factor
        if content_height > scroll_area_height:
            # スクロールバーの背景
            scrollbar_bg_rect = pygame.Rect(
                scroll_area.right + 10 * scale_factor,
                scroll_area.y,
                5 * scale_factor,
                scroll_area_height,
            )
            pygame.draw.rect(
                screen,
                (50, 50, 50, 150),
                scrollbar_bg_rect,
                border_radius=int(2 * scale_factor),
            )

            # スクロールバーのつまみ
            visible_ratio = scroll_area_height / content_height
            thumb_height = max(30 * scale_factor, scroll_area_height * visible_ratio)

            # スクロール位置に基づいてつまみの位置を計算
            max_scroll = content_height - scroll_area_height
            scroll_ratio = min(
                1, max(0, -scroll_offset / max_scroll if max_scroll > 0 else 0)
            )
            thumb_y = scroll_area.y + scroll_ratio * (scroll_area_height - thumb_height)

            thumb_rect = pygame.Rect(
                scroll_area.right + 10 * scale_factor,
                thumb_y,
                5 * scale_factor,
                thumb_height,
            )
            pygame.draw.rect(
                screen,
                theme["ui_border"],
                thumb_rect,
                border_radius=int(2 * scale_factor),
            )

    # 戻るボタンは常に表示（スクロールの影響を受けない）
    back_button.update(mouse_pos)
    back_button.draw(screen)
    buttons.append(back_button)

    return buttons


# キー設定メニューの描画（新規追加）
def draw_key_config_menu(scroll_offset=0):
    # 背景
    screen.fill(theme["background"])

    # 背景グラデーション効果
    gradient_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    for i in range(screen_height):
        alpha = max(0, 40 - (i // 10))
        color = (*theme["ui_border"][:3], alpha)
        pygame.draw.line(gradient_surface, color, (0, i), (screen_width, i))
    screen.blit(gradient_surface, (0, 0))

    # 装飾的な背景パターン
    for i in range(20):
        size = random.randint(5, 20) * scale_factor
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        alpha = random.randint(10, 40)
        color = (*theme["ui_border"][:3], alpha)
        pygame.draw.rect(
            screen, color, pygame.Rect(x, y, size, size), border_radius=int(size // 3)
        )

    # メインパネル
    panel_width = 600 * scale_factor
    panel_height = 550 * scale_factor
    panel_x = screen_width // 2 - panel_width // 2
    panel_y = screen_height // 2 - panel_height // 2 - 20 * scale_factor

    # 半透明のパネル背景
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((30, 30, 30, 180))  # 半透明のダークグレー

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(20 * scale_factor)
    pygame.draw.rect(panel, (50, 50, 50, 200), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel, theme["ui_border"], panel_rect, width=2, border_radius=corner_radius
    )

    # グラデーション効果（上部を少し明るく）
    gradient_height = int(panel_height // 3)
    for i in range(gradient_height):
        alpha = 40 - int(40 * i / gradient_height)
        highlight_color = (255, 255, 255, alpha)
        pygame.draw.rect(
            panel,
            highlight_color,
            pygame.Rect(0, i, panel_width, 1),
            border_radius=corner_radius if i == 0 else 0,
        )

    screen.blit(panel, (panel_x, panel_y))

    # タイトル
    title_text = title_font.render("キー設定", True, theme["text"])
    title_shadow = title_font.render("キー設定", True, (0, 0, 0, 150))

    # タイトルの影
    screen.blit(
        title_shadow,
        (
            screen_width // 2 - title_text.get_width() // 2 + 3 * scale_factor,
            panel_y + 30 * scale_factor + 3 * scale_factor,
        ),
    )

    # タイトル
    screen.blit(
        title_text,
        (screen_width // 2 - title_text.get_width() // 2, panel_y + 30 * scale_factor),
    )

    # 装飾ライン
    line_y = panel_y + 90 * scale_factor
    line_width = panel_width - 60 * scale_factor
    line_x = panel_x + 30 * scale_factor

    pygame.draw.line(
        screen,
        theme["ui_border"],
        (line_x, line_y),
        (line_x + line_width, line_y),
        width=2,
    )

    # 説明テキスト
    instruction_text = font.render(
        "変更したいキーを選択してください", True, theme["text"]
    )
    screen.blit(
        instruction_text,
        (
            screen_width // 2 - instruction_text.get_width() // 2,
            panel_y + 110 * scale_factor,
        ),
    )

    # スクロール可能な領域を示す
    scroll_hint_text = small_font.render(
        "↑↓ マウスホイールでスクロール", True, theme["text"]
    )
    screen.blit(
        scroll_hint_text,
        (
            screen_width // 2 - scroll_hint_text.get_width() // 2,
            panel_y + 140 * scale_factor,
        ),
    )

    # スクロール可能な領域を定義
    scroll_area_height = panel_height - 200 * scale_factor
    scroll_area = pygame.Rect(
        panel_x + 30 * scale_factor,
        panel_y + 170 * scale_factor,
        panel_width - 60 * scale_factor,
        scroll_area_height,
    )

    # スクロール可能な領域の背景
    scroll_bg = pygame.Surface((scroll_area.width, scroll_area.height), pygame.SRCALPHA)
    scroll_bg.fill((20, 20, 20, 100))
    pygame.draw.rect(
        scroll_bg,
        (40, 40, 40, 150),
        pygame.Rect(0, 0, scroll_area.width, scroll_area.height),
        border_radius=int(10 * scale_factor),
    )
    pygame.draw.rect(
        scroll_bg,
        (*theme["ui_border"][:3], 100),
        pygame.Rect(0, 0, scroll_area.width, scroll_area.height),
        width=1,
        border_radius=int(10 * scale_factor),
    )
    screen.blit(scroll_bg, (scroll_area.x, scroll_area.y))

    # ボタンの作成
    buttons = []
    key_bindings = settings.get("key_bindings", {})

    # キー名と表示名のマッピング
    key_names = {
        "move_left": "左移動",
        "move_right": "右移動",
        "rotate_cw": "時計回り回転",
        "rotate_ccw": "反時計回り回転",
        "soft_drop": "ソフトドロップ",
        "hard_drop": "ハードドロップ",
        "hold": "ホールド",
        "pause": "一時停止",
    }

    # ボタンの幅と位置
    button_width = panel_width - 100 * scale_factor
    button_x = screen_width // 2 - button_width // 2

    # ボタン間の間隔
    button_spacing = 60 * scale_factor

    # 各キー設定のボタンを作成
    base_y = panel_y + 190 * scale_factor + scroll_offset

    for i, (key, display_name) in enumerate(key_names.items()):
        key_code = key_bindings.get(key, pygame.K_UNKNOWN)
        key_name = pygame.key.name(key_code).upper()

        button = Button(
            button_x,
            base_y + i * button_spacing,
            button_width,
            50 * scale_factor,
            f"{display_name}: {key_name}",
            action=f"key_{key}",
        )
        buttons.append(button)

    # 戻るボタン - 常に画面下部に固定
    back_button = Button(
        screen_width // 2 - 100 * scale_factor,
        panel_y + panel_height - 60 * scale_factor,
        200 * scale_factor,
        50 * scale_factor,
        "戻る",
        action="back",
    )

    # マウス位置の取得
    mouse_pos = pygame.mouse.get_pos()

    # スクロール可能なボタンの描画（スクロール領域内のみ表示）
    for button in buttons:
        # ボタンがスクロール領域内にあるかチェック
        if scroll_area.colliderect(button.rect):
            button.update(mouse_pos)
            button.draw(screen)

    # スクロールバーの描画
    if len(buttons) > 0:
        # スクロール範囲の計算
        content_height = button_spacing * (len(buttons) - 1) + 50 * scale_factor
        if content_height > scroll_area_height:
            # スクロールバーの背景
            scrollbar_bg_rect = pygame.Rect(
                scroll_area.right + 10 * scale_factor,
                scroll_area.y,
                5 * scale_factor,
                scroll_area_height,
            )
            pygame.draw.rect(
                screen,
                (50, 50, 50, 150),
                scrollbar_bg_rect,
                border_radius=int(2 * scale_factor),
            )

            # スクロールバーのつまみ
            visible_ratio = scroll_area_height / content_height
            thumb_height = max(30 * scale_factor, scroll_area_height * visible_ratio)

            # スクロール位置に基づいてつまみの位置を計算
            max_scroll = content_height - scroll_area_height
            scroll_ratio = min(
                1, max(0, -scroll_offset / max_scroll if max_scroll > 0 else 0)
            )
            thumb_y = scroll_area.y + scroll_ratio * (scroll_area_height - thumb_height)

            thumb_rect = pygame.Rect(
                scroll_area.right + 10 * scale_factor,
                thumb_y,
                5 * scale_factor,
                thumb_height,
            )
            pygame.draw.rect(
                screen,
                theme["ui_border"],
                thumb_rect,
                border_radius=int(2 * scale_factor),
            )

    # 戻るボタンは常に表示（スクロールの影響を受けない）
    back_button.update(mouse_pos)
    back_button.draw(screen)
    buttons.append(back_button)

    return buttons


# キー待ち画面の描画（新規追加）
def draw_waiting_for_key(key_name):
    # 背景
    screen.fill(theme["background"])

    # 背景グラデーション効果
    gradient_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    for i in range(screen_height):
        alpha = max(0, 40 - (i // 10))
        color = (*theme["ui_border"][:3], alpha)
        pygame.draw.line(gradient_surface, color, (0, i), (screen_width, i))
    screen.blit(gradient_surface, (0, 0))

    # 装飾的な背景パターン
    for i in range(20):
        size = random.randint(5, 20) * scale_factor
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        alpha = random.randint(10, 40)
        color = (*theme["ui_border"][:3], alpha)
        pygame.draw.rect(
            screen, color, pygame.Rect(x, y, size, size), border_radius=int(size // 3)
        )

    # メインパネル
    panel_width = 500 * scale_factor
    panel_height = 300 * scale_factor
    panel_x = screen_width // 2 - panel_width // 2
    panel_y = screen_height // 2 - panel_height // 2

    # 半透明のパネル背景
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((30, 30, 30, 180))  # 半透明のダークグレー

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(20 * scale_factor)
    pygame.draw.rect(panel, (50, 50, 50, 200), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel, theme["ui_border"], panel_rect, width=2, border_radius=corner_radius
    )

    # グラデーション効果（上部を少し明るく）
    gradient_height = int(panel_height // 3)
    for i in range(gradient_height):
        alpha = 40 - int(40 * i / gradient_height)
        highlight_color = (255, 255, 255, alpha)
        pygame.draw.rect(
            panel,
            highlight_color,
            pygame.Rect(0, i, panel_width, 1),
            border_radius=corner_radius if i == 0 else 0,
        )

    screen.blit(panel, (panel_x, panel_y))

    # タイトル
    title_text = title_font.render("キー設定", True, theme["text"])
    title_shadow = title_font.render("キー設定", True, (0, 0, 0, 150))

    # タイトルの影
    screen.blit(
        title_shadow,
        (
            screen_width // 2 - title_text.get_width() // 2 + 3 * scale_factor,
            panel_y + 30 * scale_factor + 3 * scale_factor,
        ),
    )

    # タイトル
    screen.blit(
        title_text,
        (screen_width // 2 - title_text.get_width() // 2, panel_y + 30 * scale_factor),
    )

    # 装飾ライン
    line_y = panel_y + 90 * scale_factor
    line_width = panel_width - 60 * scale_factor
    line_x = panel_x + 30 * scale_factor

    pygame.draw.line(
        screen,
        theme["ui_border"],
        (line_x, line_y),
        (line_x + line_width, line_y),
        width=2,
    )

    # 説明テキスト
    key_display_names = {
        "move_left": "左移動",
        "move_right": "右移動",
        "rotate_cw": "時計回り回転",
        "rotate_ccw": "反時計回り回転",
        "soft_drop": "ソフトドロップ",
        "hard_drop": "ハードドロップ",
        "hold": "ホールド",
        "pause": "一時停止",
    }
    display_name = key_display_names.get(key_name, key_name)

    instruction_text = font.render(
        f"{display_name}のキーを押してください", True, theme["text"]
    )
    screen.blit(
        instruction_text,
        (
            screen_width // 2 - instruction_text.get_width() // 2,
            panel_y + 150 * scale_factor,
        ),
    )

    # キー入力待ちアニメーション
    now = pygame.time.get_ticks()
    dots = "." * (1 + (now // 500) % 3)  # 500ミリ秒ごとにドットを増やす
    waiting_text = font.render(f"待機中{dots}", True, theme["ui_border"])
    screen.blit(
        waiting_text,
        (
            screen_width // 2 - waiting_text.get_width() // 2,
            panel_y + 200 * scale_factor,
        ),
    )

    # キャンセル説明
    cancel_text = small_font.render("ESCキーでキャンセル", True, theme["text"])
    screen.blit(
        cancel_text,
        (
            screen_width // 2 - cancel_text.get_width() // 2,
            panel_y + 250 * scale_factor,
        ),
    )


# メイン関数
def main():
    # スクリーンの初期化
    global screen, need_redraw_menus
    screen = initialize_screen(fullscreen=settings.get("fullscreen", False))
    need_redraw_menus = False

    # ゲーム状態
    game_state = "menu"
    game = Tetris()
    menu_buttons = []
    high_score_buttons = []
    game_over_button = None
    pause_buttons = None
    settings_buttons = None
    key_config_buttons = None
    settings_scroll_offset = 0
    key_config_scroll_offset = 0
    settings_scroll_speed = 20 * scale_factor
    settings_max_scroll = -200 * scale_factor  # 最大スクロール量（負の値）
    key_config_scroll_speed = 20 * scale_factor
    key_config_max_scroll = -200 * scale_factor  # 最大スクロール量（負の値）
    waiting_for_key = False
    key_to_configure = None

    # ゲームループの設定
    clock = pygame.time.Clock()
    running = True

    # ゲーム起動時にBGMを再生
    if has_music and settings.get("music", True) and game_state == "playing":
        pygame.mixer.music.play(-1)  # -1で無限ループ

    while running:
        now = pygame.time.get_ticks()
        dt = clock.get_time() / 1000.0  # 前フレームからの経過時間（秒）

        # フルスクリーン切替後のメニュー再描画
        if need_redraw_menus:
            if game_state == "menu":
                menu_buttons = draw_start_menu()
            elif game_state == "settings":
                settings_buttons = draw_settings_menu(settings_scroll_offset)
            elif game_state == "key_config":
                key_config_buttons = draw_key_config_menu(key_config_scroll_offset)
            elif game_state == "high_scores":
                high_score_buttons = draw_high_scores(game)
            elif game_state == "playing" and game.paused:
                pause_buttons = game.draw_pause_menu()
            need_redraw_menus = False

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if waiting_for_key:
                        waiting_for_key = False
                    elif game_state == "key_config":
                        game_state = "settings"
                        settings_buttons = draw_settings_menu(settings_scroll_offset)
                    elif game_state == "settings":
                        game_state = "menu"
                    elif game_state == "playing":
                        if game.paused:
                            game.toggle_pause()
                        else:
                            game_state = "menu"
                            if has_music:
                                pygame.mixer.music.stop()
                    else:
                        running = False

                elif waiting_for_key:
                    # キー設定の保存
                    if key_to_configure:
                        settings["keys"][key_to_configure] = event.key
                        save_settings(settings)
                        waiting_for_key = False
                        key_config_buttons = draw_key_config_menu(
                            key_config_scroll_offset
                        )

                elif event.key == pygame.K_f:
                    is_fullscreen = toggle_fullscreen()
                    # 設定を更新
                    settings["fullscreen"] = is_fullscreen
                    save_settings(settings)

                    # フォントの再初期化
                    init_fonts()

                    # 現在の状態に応じてメニューを再描画
                    if game_state == "menu":
                        menu_buttons = draw_start_menu()
                    elif game_state == "settings":
                        settings_buttons = draw_settings_menu(settings_scroll_offset)
                    elif game_state == "key_config":
                        key_config_buttons = draw_key_config_menu(
                            key_config_scroll_offset
                        )
                    elif game_state == "high_scores":
                        high_score_buttons = draw_high_scores(game)
                    elif game_state == "playing" and game.paused:
                        pause_buttons = game.draw_pause_menu()

                elif game_state == "settings":
                    if event.key == pygame.K_UP:
                        settings_scroll_offset = min(
                            0, settings_scroll_offset + settings_scroll_speed
                        )
                    elif event.key == pygame.K_DOWN:
                        settings_scroll_offset = max(
                            settings_max_scroll,
                            settings_scroll_offset - settings_scroll_speed,
                        )
                        settings_buttons = draw_settings_menu(settings_scroll_offset)

                elif game_state == "key_config":
                    if event.key == pygame.K_UP:
                        key_config_scroll_offset = min(
                            0, key_config_scroll_offset + key_config_scroll_speed
                        )
                    elif event.key == pygame.K_DOWN:
                        key_config_scroll_offset = max(
                            key_config_max_scroll,
                            key_config_scroll_offset - key_config_scroll_speed,
                        )
                        key_config_buttons = draw_key_config_menu(
                            key_config_scroll_offset
                        )

                elif game_state == "playing" and not game.paused and not game.game_over:
                    # キー設定から対応するアクションを取得
                    key_settings = settings.get("keys", {})
                    if event.key == key_settings.get("move_left", pygame.K_LEFT):
                        game.move(-1)
                        game.das_timer = 0  # DASタイマーをリセット
                    elif event.key == key_settings.get("move_right", pygame.K_RIGHT):
                        game.move(1)
                        game.das_timer = 0  # DASタイマーをリセット
                    elif event.key == key_settings.get("rotate_cw", pygame.K_UP):
                        game.rotate(clockwise=True)  # 時計回り回転
                    elif event.key == key_settings.get("rotate_ccw", pygame.K_z):
                        game.rotate(clockwise=False)  # 反時計回り回転
                    elif event.key == key_settings.get("soft_drop", pygame.K_DOWN):
                        game.soft_drop = True
                    elif event.key == key_settings.get("hard_drop", pygame.K_SPACE):
                        game.drop()
                    elif event.key == key_settings.get("hold", pygame.K_c):
                        game.hold_piece()
                    elif event.key == key_settings.get("pause", pygame.K_p):
                        game.toggle_pause()
                elif event.key == pygame.K_r and game.game_over:
                    game = Tetris(game_mode=game.game_mode)

            elif event.type == pygame.KEYUP and game_state == "playing":
                key_settings = settings.get("keys", {})
                if event.key == key_settings.get("soft_drop", pygame.K_DOWN):
                    game.soft_drop = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    if game_state == "menu":
                        for button in menu_buttons:
                            result = button.handle_event(event)
                            if result == "start":
                                game = Tetris(
                                    game_mode=settings.get("game_mode", "marathon")
                                )
                                game_state = "playing"

                                # BGM再生
                                if has_music and settings.get("music", True):
                                    pygame.mixer.music.play(-1)
                            elif result == "theme":
                                cycle_theme()
                            elif result == "game_mode":
                                # ゲームモードを切り替える
                                current_mode = settings.get("game_mode", "marathon")
                                if current_mode == "marathon":
                                    settings["game_mode"] = "sprint"
                                elif current_mode == "sprint":
                                    settings["game_mode"] = "ultra"
                                else:
                                    settings["game_mode"] = "marathon"
                                save_settings(settings)
                                # ボタンのテキストを更新
                                for btn in menu_buttons:
                                    if "モード" in btn.text:
                                        btn.text = f"モード: {settings.get('game_mode', 'marathon').capitalize()}"
                            elif result == "effects":
                                # エフェクト設定の切り替え
                                settings["effects"] = not settings.get("effects", True)
                                save_settings(settings)
                                # ボタンのテキストを更新
                                for btn in menu_buttons:
                                    if btn.action == "effects":
                                        effects_status = (
                                            "ON"
                                            if settings.get("effects", True)
                                            else "OFF"
                                        )
                                        btn.text = f"エフェクト: {effects_status}"
                            elif result == "fullscreen":
                                is_fullscreen = toggle_fullscreen()
                                # 設定を更新（toggle_fullscreen内で既に行われているので不要）
                                # ポーズメニューは自動的に再描画されるのでここでは何もしない
                            elif result == "high_scores":
                                game_state = "high_scores"
                            elif result == "settings":
                                game_state = "settings"
                                settings_scroll_offset = 0  # スクロールをリセット
                                settings_buttons = draw_settings_menu(
                                    settings_scroll_offset
                                )
                            elif result == "quit":
                                game_state = "menu"
                                if has_music:
                                    pygame.mixer.music.stop()

                    elif game_state == "settings":
                        for button in settings_buttons:
                            result = button.handle_event(event)
                            if result == "back":
                                game_state = "menu"
                            elif result == "effect_type":
                                # エフェクトタイプの切り替え
                                current_effect = settings.get("effect_type", "default")
                                effect_types = [
                                    "default",
                                    "explosion",
                                    "rain",
                                    "spiral",
                                ]
                                current_index = effect_types.index(current_effect)
                                next_index = (current_index + 1) % len(effect_types)
                                settings["effect_type"] = effect_types[next_index]
                                save_settings(settings)
                                # ボタンのテキストを更新
                                settings_buttons = draw_settings_menu(
                                    settings_scroll_offset
                                )
                            elif result == "music":
                                # 音楽設定の切り替え
                                settings["music"] = not settings.get("music", True)
                                save_settings(settings)
                                # ボタンのテキストを更新
                                settings_buttons = draw_settings_menu(
                                    settings_scroll_offset
                                )
                                # 音楽の再生/停止
                                if has_music:
                                    if settings.get("music", True):
                                        if game_state == "playing":
                                            pygame.mixer.music.play(-1)
                                    else:
                                        pygame.mixer.music.stop()
                            elif result == "sound":
                                # 効果音設定の切り替え
                                settings["sound"] = not settings.get("sound", True)
                                save_settings(settings)
                                # ボタンのテキストを更新
                                settings_buttons = draw_settings_menu(
                                    settings_scroll_offset
                                )
                            elif result == "fullscreen":
                                is_fullscreen = toggle_fullscreen()
                                # 設定を更新（toggle_fullscreen内で既に行われているので不要）
                                # ポーズメニューは自動的に再描画されるのでここでは何もしない
                            elif result == "key_config":
                                game_state = "key_config"
                                key_config_scroll_offset = 0  # スクロールをリセット
                                key_config_buttons = draw_key_config_menu(
                                    key_config_scroll_offset
                                )

                    elif game_state == "key_config":
                        for button in key_config_buttons:
                            result = button.handle_event(event)
                            if result == "back":
                                game_state = "settings"
                                settings_buttons = draw_settings_menu(
                                    settings_scroll_offset
                                )
                            elif result in [
                                "move_left",
                                "move_right",
                                "rotate_cw",
                                "rotate_ccw",
                                "soft_drop",
                                "hard_drop",
                                "hold",
                                "pause",
                            ]:
                                waiting_for_key = True
                                key_to_configure = result

                elif game_state == "high_scores":
                    for button in high_score_buttons:
                        result = button.handle_event(event)
                        if result == "back":
                            game_state = "menu"
                        elif result in ["marathon", "sprint", "ultra"]:
                            game.game_mode = result
                            # ゲームモード変更後にハイスコア画面を再描画
                            high_score_buttons = draw_high_scores(game)

                elif game_state == "playing":
                    # ゲームオーバー画面のボタン
                    if game.game_over and game_over_buttons:
                        for button in game_over_buttons:
                            result = button.handle_event(event)
                            if result == "retry":
                                game = Tetris(game_mode=game.game_mode)
                            elif result == "menu":
                                game_state = "menu"
                                if has_music:
                                    pygame.mixer.music.stop()

                    # ゲームクリア画面のボタン
                    if game.game_clear and game_over_buttons:
                        for button in game_over_buttons:
                            result = button.handle_event(event)
                            if result == "retry":
                                game = Tetris(game_mode=game.game_mode)
                            elif result == "menu":
                                game_state = "menu"
                                if has_music:
                                    pygame.mixer.music.stop()

                    # ポーズメニューのボタン
                    if game.paused and pause_buttons:
                        for button in pause_buttons:
                            result = button.handle_event(event)
                            if result == "resume":
                                game.toggle_pause()
                            elif result == "theme":
                                cycle_theme()
                            elif result == "fullscreen":
                                is_fullscreen = toggle_fullscreen()
                                # 設定を更新
                                settings["fullscreen"] = is_fullscreen
                                save_settings(settings)
                                # 設定メニューも更新（必要な場合のため）
                                if settings_buttons:
                                    settings_buttons = draw_settings_menu(
                                        settings_scroll_offset
                                    )
                            elif result == "quit":
                                game_state = "menu"
                                if has_music:
                                    pygame.mixer.music.stop()

                elif event.button in [4, 5]:  # マウスホイール
                    if game_state == "settings":
                        # 上方向へのスクロール（値は正）
                        if event.button == 4:
                            settings_scroll_offset = min(
                                0, settings_scroll_offset + settings_scroll_speed
                            )
                        # 下方向へのスクロール（値は負）
                        elif event.button == 5:
                            settings_scroll_offset = max(
                                settings_max_scroll,
                                settings_scroll_offset - settings_scroll_speed,
                            )
                        settings_buttons = draw_settings_menu(settings_scroll_offset)

                    elif game_state == "key_config":
                        # 上方向へのスクロール（値は正）
                        if event.button == 4:
                            key_config_scroll_offset = min(
                                0, key_config_scroll_offset + key_config_scroll_speed
                            )
                        # 下方向へのスクロール（値は負）
                        elif event.button == 5:
                            key_config_scroll_offset = max(
                                key_config_max_scroll,
                                key_config_scroll_offset - key_config_scroll_speed,
                            )
                        key_config_buttons = draw_key_config_menu(
                            key_config_scroll_offset
                        )

        # 状態に応じた更新と描画
        if game_state == "menu":
            # メニューボタンを毎フレーム更新
            menu_buttons = draw_start_menu()

        elif game_state == "settings":
            # 設定メニューの描画
            if not settings_buttons:
                settings_buttons = draw_settings_menu(settings_scroll_offset)

        elif game_state == "key_config":
            # キー設定メニューの描画
            if not key_config_buttons:
                key_config_buttons = draw_key_config_menu(key_config_scroll_offset)

            # キー入力待ち画面
            if waiting_for_key:
                draw_waiting_for_key(key_to_configure)

        elif game_state == "high_scores":
            high_score_buttons = draw_high_scores(game)

        elif game_state == "playing":
            # ゲーム状態の更新
            game.update(dt)

            # ゲーム描画
            game_over_buttons = game.draw()  # 変数名をgame_over_buttonsに変更

            # ポーズメニュー
            pause_buttons = None
            if game.paused:
                pause_buttons = game.draw_pause_menu()

        # 画面の更新
        pygame.display.flip()

        # フレームレート制限
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
