import pygame
import random
import uuid
from datetime import datetime
import config
from config import GRID_WIDTH, GRID_HEIGHT, BLOCK_SIZE, grid_x, grid_y, theme, settings
from config import scale_factor, font, small_font, big_font, title_font
from config import move_sound, rotate_sound, drop_sound, clear_sound, tetris_sound
from config import level_up_sound, hold_sound, game_over_sound, has_sound, has_music
from particles import ParticleSystem, FloatingText
from utils import load_high_scores, save_high_scores


try:
    from ui import Button
except ImportError:
    # ui.pyが利用できない場合のフォールバック
    class Button:
        def __init__(
            self, x, y, width, height, text, action=None, bg_color=None, text_color=None
        ):
            self.rect = pygame.Rect(x, y, width, height)
            self.text = text
            self.action = action
            self.bg_color = bg_color or (60, 60, 60)
            self.text_color = text_color or (255, 255, 255)
            self.hovered = False

        def update(self, mouse_pos):
            self.hovered = self.rect.collidepoint(mouse_pos)

        def draw(self, screen):
            color = (80, 80, 80) if self.hovered else self.bg_color
            pygame.draw.rect(screen, color, self.rect)
            pygame.draw.rect(screen, (100, 100, 100), self.rect, 1)

            # フォントを安全に取得
            try:
                from config import font

                text_surf = font.render(self.text, True, self.text_color)
            except:
                fallback_font = pygame.font.Font(None, 24)
                text_surf = fallback_font.render(self.text, True, self.text_color)

            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)


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
        self.das_delay = settings.get("das", 0.167)  # 秒
        self.arr_delay = settings.get("arr", 0.033)  # 秒
        self.das_timer = 0
        self.arr_timer = 0

        # キー状態管理
        self.prev_left_pressed = False
        self.prev_right_pressed = False
        self.left_key_time = 0  # 左キーが押されている時間
        self.right_key_time = 0  # 右キーが押されている時間
        self.last_key_pressed = None  # 最後に押されたキー
        self.das_charged = False  # DAS充電完了フラグ
        self.initial_move_done = False  # 初回移動完了フラグ
        self.current_direction = 0  # ★この行を追加

        self.is_tspin = False  # 後方互換性のため維持
        self.current_spin_type = None  # 現在のスピンタイプ
        self.spin_count = {
            "T-Spin": 0,
            "I-Spin": 0,
            "J-Spin": 0,
            "L-Spin": 0,
            "S-Spin": 0,
            "Z-Spin": 0,
        }

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
        # 修正：本家準拠のロックディレイシステム
        self.lock_delay = 0
        self.max_lock_delay = 0.5  # 基本ロックディレイ（本家準拠）
        self.lock_delay_resets = 0  # ロックディレイリセット回数
        self.max_lock_delay_resets = 15  # 最大リセット回数（本家準拠）
        self.is_on_ground = False  # 接地状態フラグ
        self.last_move_reset_lock = (
            False  # 最後の移動でロックディレイがリセットされたか
        )
        self.has_ever_been_grounded = False  # 追加：一度でも接地したかのフラグ

        # ゲーム時間
        self.time_played = 0

        # ラインクリア用
        self.clearing_lines = False
        self.lines_to_clear = []

        # T-Spinフラグをリセット
        self.is_tspin = False
        self.current_spin_type = None
        
        # オンライン対戦用
        self.lines_cleared_this_frame = 0

        # BGMの再開処理を追加
        try:
            if (
                hasattr(config, "has_music")
                and config.has_music
                and hasattr(config, "settings")
                and config.settings.get("music", True)
            ):
                # BGMが停止している場合は再開
                if not pygame.mixer.music.get_busy():
                    # bgm_managerを使用してBGMを再生
                    import bgm_manager

                    bgm_manager.play_bgm()
        except Exception as e:
            print(f"BGM再開処理でエラーが発生しました: {e}")

        # キー状態をリセット
        self.das_timer = 0
        self.arr_timer = 0
        self.prev_left_pressed = False
        self.prev_right_pressed = False
        self.left_key_time = 0
        self.right_key_time = 0
        self.last_key_pressed = None
        self.das_charged = False
        self.initial_move_done = False
        self.current_direction = 0  # ★この行を追加

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
            "color": config.theme["blocks"][
                TETROMINOS[piece_index]["color"]
            ],  # 動的テーマ色
            "x": GRID_WIDTH // 2 - len(TETROMINOS[piece_index]["shape"][0]) // 2,
            "y": 0,
            "rotation": 0,
            "index": piece_index,
        }
        return piece

    # 修正箇所：新しいメソッドを追加
    def update_piece_colors(self):
        """既存のピースの色をテーマに合わせて更新"""
        if self.current_piece:
            self.current_piece["color"] = config.theme["blocks"][
                self.current_piece["index"]
            ]

        if self.held_piece:
            self.held_piece["color"] = config.theme["blocks"][self.held_piece["index"]]

        for piece in self.next_pieces:
            piece["color"] = config.theme["blocks"][piece["index"]]

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

    # 修正：接地状態をチェックする新しいメソッド
    def is_piece_on_ground(self):
        """現在のピースが接地しているかチェック"""
        if not self.current_piece:
            return False
        return not self.valid_move(self.current_piece, y_offset=1)

    # 修正：ロックディレイをリセットする新しいメソッド
    def reset_lock_delay(self):
        """ロックディレイをリセット（インフィニティシステム）"""
        if self.is_on_ground and self.lock_delay_resets < self.max_lock_delay_resets:
            self.lock_delay = 0
            self.lock_delay_resets += 1
            self.last_move_reset_lock = True
            return True
        return False

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

        # 壁や他のブロックとの衝突をチェック
        # まず基本的な位置で回転が可能かチェック
        if self.valid_move(self.current_piece):
            # 基本回転では通常スピンにならない（キックが必要）
            self.current_spin_type = None

            # 修正：回転時のロックディレイリセット
            if self.is_on_ground:
                self.reset_lock_delay()

            # ゴーストピースの更新
            self.ghost_piece = self.get_ghost_piece()
            return

        # 基本位置で回転できない場合、キックテストを実行
        # キック用のパターンキー
        kick_key = f"{original_rotation}{new_rotation}"

        # I型ピースと他の形状で異なるキックパターンを使用
        if self.current_piece["index"] == 0:  # I型
            kicks = I_KICKS[kick_key]
        else:
            kicks = KICKS[kick_key]

        # キックテストを実行
        for kick_x, kick_y in kicks:
            if self.valid_move(self.current_piece, x_offset=kick_x, y_offset=kick_y):
                self.current_piece["x"] += kick_x
                self.current_piece["y"] += kick_y

                # キック成功時のみスピンチェック（キックによる回転がスピンの条件）
                is_spin, spin_type = self.check_spin_after_kick(original_x, original_y, kick_x, kick_y)
                self.current_spin_type = spin_type

                # ゴーストピースの更新
                self.ghost_piece = self.get_ghost_piece()
                return

        # 回転が不可能な場合は元に戻す
        self.current_piece["shape"] = original_shape
        self.current_piece["rotation"] = original_rotation
        self.current_piece["x"] = original_x
        self.current_piece["y"] = original_y
        # 回転失敗時はスピン状態をリセット
        self.current_spin_type = None

    def rotate_matrix(self, matrix):
        """行列を時計回りに90度回転"""
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        result = [[0 for _ in range(rows)] for _ in range(cols)]

        for i in range(rows):
            for j in range(cols):
                result[j][rows - 1 - i] = matrix[i][j]

        return result

    def rotate_matrix_ccw(self, matrix):
        """行列を反時計回りに90度回転"""
        rows = len(matrix)
        cols = len(matrix[0]) if rows > 0 else 0
        result = [[0 for _ in range(rows)] for _ in range(cols)]

        for i in range(rows):
            for j in range(cols):
                result[cols - 1 - j][i] = matrix[i][j]

        return result

    def check_spin_after_kick(self, original_x, original_y, kick_x, kick_y):
        """キック後のスピン判定をチェックする（キックが発生した場合のみスピンとする）"""
        if not self.current_piece:
            return False, None

        piece_index = self.current_piece["index"]
        
        # S型とZ型のみキック時にスピン判定
        if piece_index == 5:  # S型
            return True, "S-Spin"
        elif piece_index == 6:  # Z型
            return True, "Z-Spin"
        elif piece_index == 2:  # T型
            # T型は従来の判定を使用
            is_spin, spin_type = self.check_t_spin(self.current_piece["x"], self.current_piece["y"])
            return is_spin, spin_type
        elif piece_index == 0:  # I型
            # I型も従来の判定を使用
            is_spin, spin_type = self.check_i_spin(self.current_piece["x"], self.current_piece["y"])
            return is_spin, spin_type
        elif piece_index == 3:  # J型
            is_spin, spin_type = self.check_j_spin(self.current_piece["x"], self.current_piece["y"])
            return is_spin, spin_type
        elif piece_index == 4:  # L型
            is_spin, spin_type = self.check_l_spin(self.current_piece["x"], self.current_piece["y"])
            return is_spin, spin_type
        
        return False, None

    def check_spin(self):
        """全テトロミノのスピン判定をチェックする"""
        if not self.current_piece:
            self.is_tspin = False
            return False, None

        piece_index = self.current_piece["index"]
        piece_x, piece_y = self.current_piece["x"], self.current_piece["y"]

        # スピン判定結果
        spin_type = None
        is_spin = False

        if piece_index == 0:  # I型
            is_spin, spin_type = self.check_i_spin(piece_x, piece_y)
        elif piece_index == 1:  # O型
            is_spin, spin_type = self.check_o_spin(piece_x, piece_y)
        elif piece_index == 2:  # T型
            is_spin, spin_type = self.check_t_spin(piece_x, piece_y)
        elif piece_index == 3:  # J型
            is_spin, spin_type = self.check_j_spin(piece_x, piece_y)
        elif piece_index == 4:  # L型
            is_spin, spin_type = self.check_l_spin(piece_x, piece_y)
        elif piece_index == 5:  # S型
            is_spin, spin_type = self.check_s_spin(piece_x, piece_y)
        elif piece_index == 6:  # Z型
            is_spin, spin_type = self.check_z_spin(piece_x, piece_y)

        # T-Spinフラグは後方互換性のため維持
        self.is_tspin = piece_index == 2 and is_spin

        return is_spin, spin_type

    def check_t_spin(self, t_x, t_y):
        """T-Spinの条件をチェックする"""
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

        corners_filled = 0
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
        is_spin = corners_filled >= 3
        return is_spin, "T-Spin" if is_spin else None

    def check_i_spin(self, i_x, i_y):
        """I-Spinの条件をチェックする"""
        rotation = self.current_piece["rotation"]

        # I型は4x4グリッドの中心付近をチェック
        if rotation % 2 == 0:  # 水平状態
            center_x = i_x + 2
            center_y = i_y + 1
        else:  # 垂直状態
            center_x = i_x + 1
            center_y = i_y + 2

        # I型の周囲8マスをチェック
        surrounding_filled = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                cx, cy = center_x + dx, center_y + dy
                if (
                    cx < 0
                    or cx >= GRID_WIDTH
                    or cy < 0
                    or cy >= GRID_HEIGHT
                    or (cy >= 0 and cx >= 0 and self.grid[cy][cx] is not None)
                ):
                    surrounding_filled += 1

        # I-Spinの条件：周囲の6マス以上が埋まっている
        is_spin = surrounding_filled >= 6
        return is_spin, "I-Spin" if is_spin else None

    def check_j_spin(self, j_x, j_y):
        """J-Spinの条件をチェックする"""
        # J型の中心座標（3x3グリッドの中心）
        center_x = j_x + 1
        center_y = j_y + 1

        # 4隅の座標
        corners = [
            (center_x - 1, center_y - 1),  # 左上
            (center_x + 1, center_y - 1),  # 右上
            (center_x - 1, center_y + 1),  # 左下
            (center_x + 1, center_y + 1),  # 右下
        ]

        corners_filled = 0
        for cx, cy in corners:
            if (
                cx < 0
                or cx >= GRID_WIDTH
                or cy < 0
                or cy >= GRID_HEIGHT
                or (cy >= 0 and cx >= 0 and self.grid[cy][cx] is not None)
            ):
                corners_filled += 1

        # J-Spinの条件：3つ以上の隅が埋まっている
        is_spin = corners_filled >= 3
        return is_spin, "J-Spin" if is_spin else None

    def check_l_spin(self, l_x, l_y):
        """L-Spinの条件をチェックする"""
        # L型の中心座標（3x3グリッドの中心）
        center_x = l_x + 1
        center_y = l_y + 1

        # 4隅の座標
        corners = [
            (center_x - 1, center_y - 1),  # 左上
            (center_x + 1, center_y - 1),  # 右上
            (center_x - 1, center_y + 1),  # 左下
            (center_x + 1, center_y + 1),  # 右下
        ]

        corners_filled = 0
        for cx, cy in corners:
            if (
                cx < 0
                or cx >= GRID_WIDTH
                or cy < 0
                or cy >= GRID_HEIGHT
                or (cy >= 0 and cx >= 0 and self.grid[cy][cx] is not None)
            ):
                corners_filled += 1

        # L-Spinの条件：3つ以上の隅が埋まっている
        is_spin = corners_filled >= 3
        return is_spin, "L-Spin" if is_spin else None

    def check_s_spin(self, s_x, s_y):
        """S-Spinの条件をチェックする"""
        rotation = self.current_piece["rotation"]
        
        # S型のスピン判定は回転状態によって判定する位置が異なる
        if rotation == 0 or rotation == 2:  # 水平状態
            # 水平のS型の場合、上下の特定位置をチェック
            check_positions = [
                (s_x, s_y - 1),      # 上側中央
                (s_x + 1, s_y - 1),  # 上側右
                (s_x + 1, s_y + 2),  # 下側右
                (s_x + 2, s_y + 2),  # 下側右端
            ]
        else:  # 垂直状態 (rotation == 1 or rotation == 3)
            # 垂直のS型の場合、左右の特定位置をチェック
            check_positions = [
                (s_x - 1, s_y),      # 左側上
                (s_x - 1, s_y + 1),  # 左側下
                (s_x + 2, s_y + 1),  # 右側下
                (s_x + 2, s_y + 2),  # 右側下端
            ]

        filled_count = 0
        for cx, cy in check_positions:
            if (
                cx < 0
                or cx >= GRID_WIDTH
                or cy < 0
                or cy >= GRID_HEIGHT
                or (cy >= 0 and cx >= 0 and self.grid[cy][cx] is not None)
            ):
                filled_count += 1

        # S-Spinの条件：3つ以上の特定位置が埋まっている
        is_spin = filled_count >= 3
        return is_spin, "S-Spin" if is_spin else None

    def check_z_spin(self, z_x, z_y):
        """Z-Spinの条件をチェックする"""
        rotation = self.current_piece["rotation"]
        
        # Z型のスピン判定は回転状態によって判定する位置が異なる
        if rotation == 0 or rotation == 2:  # 水平状態
            # 水平のZ型の場合、上下の特定位置をチェック
            check_positions = [
                (z_x + 1, z_y - 1),  # 上側中央
                (z_x + 2, z_y - 1),  # 上側右
                (z_x, z_y + 2),      # 下側左
                (z_x + 1, z_y + 2),  # 下側中央
            ]
        else:  # 垂直状態 (rotation == 1 or rotation == 3)
            # 垂直のZ型の場合、左右の特定位置をチェック
            check_positions = [
                (z_x - 1, z_y + 1),  # 左側中
                (z_x - 1, z_y + 2),  # 左側下
                (z_x + 2, z_y),      # 右側上
                (z_x + 2, z_y + 1),  # 右側中
            ]

        filled_count = 0
        for cx, cy in check_positions:
            if (
                cx < 0
                or cx >= GRID_WIDTH
                or cy < 0
                or cy >= GRID_HEIGHT
                or (cy >= 0 and cx >= 0 and self.grid[cy][cx] is not None)
            ):
                filled_count += 1

        # Z-Spinの条件：3つ以上の特定位置が埋まっている
        is_spin = filled_count >= 3
        return is_spin, "Z-Spin" if is_spin else None

    def check_o_spin(self, o_x, o_y):
        """O-Spinの条件をチェックする（O型は回転しないため常にFalse）"""
        # O型は回転しないため、スピンは発生しない
        return False, None

    def toggle_pause(self):
        """ゲームの一時停止/再開を切り替える"""
        self.paused = not self.paused

        # BGMの一時停止/再開
        if (
            hasattr(config, "has_music")
            and config.has_music
            and hasattr(config, "settings")
            and config.settings.get("music", True)
        ):
            if self.paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    def move(self, direction):
        """ピースを左右に移動する"""
        if self.game_over or self.paused or not self.current_piece:
            return False

        if self.valid_move(self.current_piece, x_offset=direction):
            self.current_piece["x"] += direction
            # ゴーストピースの更新
            self.ghost_piece = self.get_ghost_piece()

            # 移動時はスピン状態をリセット（回転後の移動でスピンが無効になる）
            self.current_spin_type = None

            # 修正：移動時のロックディレイリセット
            if self.is_on_ground:
                self.reset_lock_delay()

            # 効果音
            if move_sound and has_sound and settings.get("sound", True):
                move_sound.play()

            return True
        return False

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

    def lock_piece(self):
        """現在のピースをグリッドに固定する"""
        # ピースが存在しない場合は何もしない
        if not self.current_piece:
            return

        # スピンチェックは回転時に既に実行済みなので、ここでは再実行しない
        # current_spin_typeの値をそのまま使用

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
                            # 現在のグローバル変数を取得
                            from config import grid_x, grid_y, scale_factor

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

        # 修正：ロックディレイシステムをリセット
        self.lock_delay = 0
        self.lock_delay_resets = 0
        self.is_on_ground = False
        self.last_move_reset_lock = False
        self.has_ever_been_grounded = False

        # ホールドリセット
        self.can_hold = True

        # 次のピースを取得
        self.current_piece = self.next_pieces.pop(0)
        self.next_pieces.append(self.get_next_piece())

        # スピン状態をリセット
        self.current_spin_type = None

        # ゴーストピースの更新
        self.ghost_piece = self.get_ghost_piece()

        # ゲームオーバーチェック（新しいピースが配置できない場合）
        if not self.valid_move(self.current_piece):
            self.game_over = True
            # ゲームオーバー時にBGMを停止
            try:
                if hasattr(config, "has_music") and config.has_music:
                    pygame.mixer.music.stop()
                if (
                    game_over_sound
                    and hasattr(config, "has_sound")
                    and config.has_sound
                    and hasattr(config, "settings")
                    and config.settings.get("sound", True)
                ):
                    game_over_sound.play()
            except Exception as e:
                print(f"ゲームオーバー処理でエラーが発生しました: {e}")

    def check_lines(self):
        """完成したラインをチェックして消去する"""
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(cell is not None for cell in self.grid[y]):
                lines_to_clear.append(y)

        lines_count = len(lines_to_clear)
        # オンライン対戦用のライン消去数を記録
        self.lines_cleared_this_frame = lines_count
        
        if lines_count == 0:
            # ラインが消去されない場合はコンボをリセット
            self.combo = 0
            return

        # 効果音を決定
        clear_sound_to_play = None
        if lines_count == 4 and tetris_sound:
            clear_sound_to_play = tetris_sound
        elif lines_count > 0 and clear_sound:
            clear_sound_to_play = clear_sound

        # スコア計算
        # スピンボーナス
        spin_bonus = 0
        spin_text = ""
        if self.current_spin_type:
            self.spin_count[self.current_spin_type] += 1
            spin_text = f"{self.current_spin_type} "

            # スピンタイプ別ボーナス
            if self.current_spin_type == "T-Spin":
                spin_bonus = 400 * self.level
            elif self.current_spin_type == "I-Spin":
                spin_bonus = 300 * self.level
            elif self.current_spin_type in ["J-Spin", "L-Spin"]:
                spin_bonus = 250 * self.level
            elif self.current_spin_type in ["S-Spin", "Z-Spin"]:
                spin_bonus = 200 * self.level

        # ライン消去ボーナス
        line_bonus = 0
        if lines_count == 1:
            line_bonus = 100 * self.level
            line_text = "Single"
        elif lines_count == 2:
            line_bonus = 300 * self.level
            line_text = "Double"
        elif lines_count == 3:
            line_bonus = 500 * self.level
            line_text = "Triple"
        elif lines_count == 4:
            line_bonus = 800 * self.level
            line_text = "Tetris!"

        # 合計スコア
        self.score += line_bonus + spin_bonus

        # コンボボーナス
        self.combo += 1
        if self.combo > 1:
            combo_bonus = 50 * self.combo * self.level
            self.score += combo_bonus
            # コンボテキスト表示
            combo_text = f"{self.combo} Combo!"
            # グローバル変数を正しく参照
            import config

            self.add_floating_text(
                config.grid_x + (GRID_WIDTH * BLOCK_SIZE * config.scale_factor) // 2,
                config.grid_y + (GRID_HEIGHT * BLOCK_SIZE * config.scale_factor) // 2,
                combo_text,
                (255, 255, 0),
                36,
            )

        # ライン消去テキスト表示
        if lines_count > 0:
            clear_text = f"{spin_text}{line_text}"
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
            import config

            self.add_floating_text(
                config.grid_x + (GRID_WIDTH * BLOCK_SIZE * config.scale_factor) // 2,
                config.grid_y
                + (GRID_HEIGHT * BLOCK_SIZE * config.scale_factor) // 2
                - 80,
                f"Level Up! {self.level}",
                (255, 255, 0),
                36,
            )
            # 落下速度の更新
            self.fall_speed = max(0.05, 1 - ((self.level - 1) * 0.05))
            # レベルアップ効果音
            if level_up_sound and has_sound and settings.get("sound", True):
                level_up_sound.play()

        # 効果音
        if clear_sound_to_play and has_sound and settings.get("sound", True):
            clear_sound_to_play.play()

        # パーティクルエフェクト
        if settings.get("effects", True):
            import config

            for y in lines_to_clear:
                # ライン全体にエフェクトを追加
                self.particle_system.create_line_clear_effect(
                    config.grid_x,
                    config.grid_y + (y + 0.5) * BLOCK_SIZE * config.scale_factor,
                    (255, 255, 255),  # 白色のパーティクル
                    30,  # パーティクル数
                )

                # 各ブロックにもエフェクトを追加
                for x in range(GRID_WIDTH):
                    if self.grid[y][x]:
                        self.particle_system.create_explosion(
                            config.grid_x
                            + (x + 0.5) * BLOCK_SIZE * config.scale_factor,
                            config.grid_y
                            + (y + 0.5) * BLOCK_SIZE * config.scale_factor,
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

    def update(self, dt):
        """ゲームの状態を更新する"""
        if self.game_over or self.paused:
            return

        # フレーム毎の初期化
        self.lines_cleared_this_frame = 0

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

        # 修正：接地状態の更新
        was_on_ground = self.is_on_ground
        self.is_on_ground = self.is_piece_on_ground()

        # 新しく接地した場合のみ、ロックディレイリセット回数をリセット
        if not was_on_ground and self.is_on_ground:
            # 初回接地時のみリセット回数をリセット
            if not self.has_ever_been_grounded:
                self.lock_delay_resets = 0
                self.has_ever_been_grounded = True
                print(f"初回接地 - リセット回数: {self.lock_delay_resets}")
            else:
                print(f"再接地 - リセット回数維持: {self.lock_delay_resets}")
            self.last_move_reset_lock = False

        if self.fall_time >= fall_speed:
            self.fall_time = 0
            # 下に移動できるかチェック
            if self.valid_move(self.current_piece, y_offset=1):
                self.current_piece["y"] += 1
                # 自然落下時のみロックディレイをリセット（リセット回数は保持）
                if not self.is_on_ground:
                    self.lock_delay = 0
                    # リセット回数は保持（一度接地したピースの延命回数を維持）
            else:
                # 修正：接地している場合、ロックディレイを増加
                if self.is_on_ground:
                    self.lock_delay += dt

                    # レベルに応じたロックディレイの調整
                    adjusted_lock_delay = self.max_lock_delay
                    if self.level >= 20:
                        adjusted_lock_delay = max(
                            0.1, self.max_lock_delay - (self.level - 20) * 0.01
                        )

                    # ロックディレイが最大値に達した場合、ピースを固定
                    if self.lock_delay >= adjusted_lock_delay:
                        self.lock_piece()

        # 接地状態でもロックディレイを進める（移動やローテーション後の処理用）
        elif not self.valid_move(self.current_piece, y_offset=1):
            self.lock_delay += dt
            if self.lock_delay >= self.max_lock_delay:
                self.lock_piece()

        # DAS/ARR処理（長押し時の高速移動）
        # DAS/ARR処理はmain.pyで実装

    def draw(self, screen):
        """ゲーム画面を描画する"""
        # 現在のグローバル変数を取得
        from config import grid_x, grid_y, scale_factor

        # 背景
        screen.fill(config.theme["background"])  # 動的テーマ参照

        # グリッド背景
        pygame.draw.rect(
            screen,
            config.theme["grid_bg"],  # 動的テーマ参照
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
                config.theme["grid_line"],  # 動的テーマ参照
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
                config.theme["grid_line"],  # 動的テーマ参照
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
                    self.draw_block(screen, x, y, self.grid[y][x])

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
                            screen,
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

        # 現在のスピン状態表示（ホールド表示の下）
        if self.current_spin_type:
            spin_indicator_text = small_font.render(
                f"準備中: {self.current_spin_type}", True, (255, 255, 100)
            )
            screen.blit(
                spin_indicator_text,
                (
                    grid_x - 150 * scale_factor,
                    grid_y + 180 * scale_factor,
                ),
            )

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

        # スピン統計の表示（スコア情報の下に追加）
        spin_stats_y = score_y + 160 * scale_factor

        # T-Spin統計（後方互換性）
        if self.spin_count["T-Spin"] > 0:
            tspin_stat_text = font.render(
                f"T-Spin: {self.spin_count['T-Spin']}", True, theme["text"]
            )
            screen.blit(tspin_stat_text, (score_x, spin_stats_y))
            spin_stats_y += 25 * scale_factor

        # その他のスピン統計
        other_spins = ["I-Spin", "J-Spin", "L-Spin", "S-Spin", "Z-Spin"]
        for spin_type in other_spins:
            if self.spin_count[spin_type] > 0:
                spin_stat_text = small_font.render(
                    f"{spin_type}: {self.spin_count[spin_type]}", True, theme["text"]
                )
                screen.blit(spin_stat_text, (score_x, spin_stats_y))
                spin_stats_y += 20 * scale_factor

        # パーティクルの描画
        self.particle_system.draw(screen)

        # フローティングテキストの描画
        for text in self.floating_texts:
            text.draw(screen)

        # ゲームオーバー画面
        if self.game_over:
            return self.draw_game_over_screen(screen)

        # ゲームクリア画面
        if self.game_clear:
            return self.draw_game_clear_screen(screen)

        return None

    def draw_block(self, screen, x, y, color):
        """ブロックを描画する"""
        # 現在のグローバル変数を取得
        from config import grid_x, grid_y, scale_factor

        block_rect = pygame.Rect(
            grid_x + x * BLOCK_SIZE * scale_factor,
            grid_y + y * BLOCK_SIZE * scale_factor,
            BLOCK_SIZE * scale_factor,
            BLOCK_SIZE * scale_factor,
        )
        pygame.draw.rect(screen, color, block_rect)
        pygame.draw.rect(screen, theme["ui_border"], block_rect, 1)

    def draw_game_over_screen(self, screen):
        """ゲームオーバー画面を描画する"""
        # 半透明のオーバーレイ
        overlay = pygame.Surface(
            (screen.get_width(), screen.get_height()), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # メニューパネル
        panel_width = 400 * scale_factor
        panel_height = 400 * scale_factor
        panel_x = (screen.get_width() - panel_width) // 2
        panel_y = (screen.get_height() - panel_height) // 2

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
                screen.get_width() // 2 - title_text.get_width() // 2,
                panel_y + 240 * scale_factor,
            ),
        )

        # スピン統計表示
        total_spins = sum(self.spin_count.values())
        if total_spins > 0:
            spin_summary_text = small_font.render(
                f"総スピン数: {total_spins}", True, theme["text"]
            )
            screen.blit(
                spin_summary_text,
                (
                    screen.get_width() // 2 - spin_summary_text.get_width() // 2,
                    panel_y + 270 * scale_factor,
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
                        screen.get_width() // 2 - high_score_text.get_width() // 2,
                        panel_y + 80 * scale_factor,
                    ),
                )

        screen.blit(
            score_text,
            (
                screen.get_width() // 2 - score_text.get_width() // 2,
                panel_y + 120 * scale_factor,
            ),
        )
        screen.blit(
            level_text,
            (
                screen.get_width() // 2 - level_text.get_width() // 2,
                panel_y + 160 * scale_factor,
            ),
        )
        screen.blit(
            lines_text,
            (
                screen.get_width() // 2 - lines_text.get_width() // 2,
                panel_y + 200 * scale_factor,
            ),
        )
        screen.blit(
            time_text,
            (
                screen.get_width() // 2 - time_text.get_width() // 2,
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
            action="retry",
        )

        menu_button = Button(
            panel_x + panel_width // 2 - 100 * scale_factor,
            panel_y + 350 * scale_factor,
            200 * scale_factor,
            40 * scale_factor,
            "メニューに戻る",
            action="menu",
        )

        mouse_pos = pygame.mouse.get_pos()
        retry_button.update(mouse_pos)
        retry_button.draw(screen)
        menu_button.update(mouse_pos)
        menu_button.draw(screen)

        return [retry_button, menu_button]

    def draw_game_clear_screen(self, screen):
        """ゲームクリア画面を描画する"""
        # 半透明のオーバーレイ
        overlay = pygame.Surface(
            (screen.get_width(), screen.get_height()), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # メニューパネル
        panel_width = 400 * scale_factor
        panel_height = 400 * scale_factor
        panel_x = (screen.get_width() - panel_width) // 2
        panel_y = (screen.get_height() - panel_height) // 2

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
                screen.get_width() // 2 - title_text.get_width() // 2,
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
                    screen.get_width() // 2 - high_score_text.get_width() // 2,
                    panel_y + 80 * scale_factor,
                ),
            )

        screen.blit(
            score_text,
            (
                screen.get_width() // 2 - score_text.get_width() // 2,
                panel_y + 120 * scale_factor,
            ),
        )
        screen.blit(
            level_text,
            (
                screen.get_width() // 2 - level_text.get_width() // 2,
                panel_y + 160 * scale_factor,
            ),
        )
        screen.blit(
            lines_text,
            (
                screen.get_width() // 2 - lines_text.get_width() // 2,
                panel_y + 200 * scale_factor,
            ),
        )
        screen.blit(
            time_text,
            (
                screen.get_width() // 2 - time_text.get_width() // 2,
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
            action="retry",
        )

        menu_button = Button(
            panel_x + panel_width // 2 - 100 * scale_factor,
            panel_y + 350 * scale_factor,
            200 * scale_factor,
            40 * scale_factor,
            "メニューに戻る",
            action="menu",
        )

        mouse_pos = pygame.mouse.get_pos()
        retry_button.update(mouse_pos)
        retry_button.draw(screen)

        menu_button.update(mouse_pos)
        menu_button.draw(screen)

        return [retry_button, menu_button]

    def draw_pause_menu(self, screen):
        """ポーズメニューを描画する"""
        # 半透明のオーバーレイ
        overlay = pygame.Surface(
            (screen.get_width(), screen.get_height()), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))  # 半透明の黒（より暗く）
        screen.blit(overlay, (0, 0))

        # パネルの寸法と位置
        panel_width = 400 * scale_factor
        panel_height = 450 * scale_factor
        panel_x = screen.get_width() // 2 - panel_width // 2
        panel_y = screen.get_height() // 2 - panel_height // 2

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
            f"テーマ: {settings.get('theme', 'classic').capitalize()}",
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
                screen.get_width() // 2 - shortcut_text.get_width() // 2,
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
            if score.get("id") == new_score["id"]:
                is_high_score = True
                break

        return is_high_score

    def add_floating_text(self, x, y, text, color, size=28, life=1.5):
        """フローティングテキストを追加する"""
        self.floating_texts.append(FloatingText(x, y, text, color, size, life))

    def update_screen_values(
        self, screen_width, screen_height, grid_x, grid_y, scale_factor
    ):
        """画面サイズ変更時に、ゲーム内部の値を更新する"""
        # グローバル変数から直接参照せず、パラメータとして受け取った値を使用
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.scale_factor = scale_factor

        # ゴーストピースの更新
        self.ghost_piece = self.get_ghost_piece()
