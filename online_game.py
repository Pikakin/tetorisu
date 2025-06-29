# オンライン対戦ゲーム
import pygame
import time
import json
from typing import Dict, List, Optional, Any
from game import Tetris
from network.client import TetrisClient
from network.protocol import MessageType, GameAction
import config
from config import scale_factor, font, small_font, big_font, GRID_WIDTH, GRID_HEIGHT, BLOCK_SIZE
from ui import Button


class OnlineGame:
    """オンライン対戦ゲームクラス"""
    
    def __init__(self, screen_width: int, screen_height: int, client: TetrisClient):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.client = client
        
        # ゲーム状態
        self.local_game = Tetris("marathon")  # 自分のゲーム
        self.opponent_game_state = {}  # 相手のゲーム状態
        self.game_started = False
        self.game_over = False
        self.winner = None
        
        # UI要素
        self.buttons = {}
        self.chat_messages = []
        self.chat_input = ""
        self.chat_active = False
        
        # 攻撃システム
        self.attack_lines = 0  # 送信予定のガベージライン数
        self.pending_garbage = []  # 受信したガベージライン
        self.outgoing_attacks = []  # 送信中の攻撃 (delay, lines)
        self.incoming_attacks = []  # 受信中の攻撃 (delay, lines)
        
        # 同期用
        self.last_state_send = 0
        self.send_interval = 1/30  # 30FPS でゲーム状態を送信
        
        # 画面制御
        self.should_exit = False
        
        # レイアウト設定
        self.setup_layout()
        self.setup_buttons()
        
        # クライアントコールバック設定
        if self.client:
            self.client.on_message_received = self._on_message_received
    
    def setup_layout(self):
        """レイアウトを設定"""
        # 自分のゲーム領域（左側中央）
        self.local_game_x = int(50 * scale_factor)
        self.local_game_y = int(50 * scale_factor)
        
        # 相手のゲーム領域（左下に移動）
        self.opponent_game_x = int(50 * scale_factor)
        self.opponent_game_y = self.screen_height - int(250 * scale_factor)
        self.opponent_scale = 0.3  # 小さめに
        
        # 攻撃状況表示領域（右下に移動）
        self.attack_display_x = self.screen_width - int(250 * scale_factor)
        self.attack_display_y = self.screen_height - int(200 * scale_factor)
        self.attack_display_width = int(230 * scale_factor)
        self.attack_display_height = int(180 * scale_factor)
        
        # チャット領域（右上に移動）
        self.chat_x = self.screen_width - int(250 * scale_factor)
        self.chat_y = int(250 * scale_factor)
        self.chat_width = int(230 * scale_factor)
        self.chat_height = int(100 * scale_factor)
    
    def setup_buttons(self):
        """ボタンを設定"""
        button_width = int(120 * scale_factor)
        button_height = int(30 * scale_factor)
        
        self.buttons["surrender"] = Button(
            self.screen_width - int(150 * scale_factor),
            int(20 * scale_factor),
            button_width, button_height,
            "降参", self._surrender
        )
        
        self.buttons["back"] = Button(
            int(20 * scale_factor),
            int(20 * scale_factor),
            button_width, button_height,
            "戻る", self._back_to_lobby
        )
        
        # テスト用攻撃ボタン
        self.buttons["test_attack"] = Button(
            int(160 * scale_factor),
            int(20 * scale_factor),
            button_width, button_height,
            "テスト攻撃", self._test_attack
        )
    
    def start_game(self):
        """ゲーム開始"""
        self.game_started = True
        self.local_game.reset()
        
        # ゲーム開始メッセージを送信
        if self.client:
            start_msg = {
                "event": "game_start",
                "timestamp": time.time()
            }
            self.client.send_game_state(start_msg)
    
    def update(self, events: List[pygame.event.Event], keys_held: Dict, dt: float) -> bool:
        """ゲームを更新"""
        if not self.game_started:
            return True
        
        # イベント処理
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._handle_key_press(event.key)
            elif event.type == pygame.KEYUP:
                self._handle_key_release(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    self._handle_mouse_click(event.pos)
        
        # DAS/ARR処理
        self._handle_das_arr(keys_held, dt)
        
        # ローカルゲームの更新
        if not self.local_game.game_over:
            # ライン消去時の攻撃処理（update前にチェック）
            old_lines_cleared = self.local_game.lines_cleared
            
            self.local_game.update(dt)
            
            # ライン消去数の変化をチェック
            lines_cleared_this_frame = self.local_game.lines_cleared - old_lines_cleared
            
            if lines_cleared_this_frame > 0:
                print(f"ライン消去検出: {lines_cleared_this_frame}ライン (総計: {old_lines_cleared} -> {self.local_game.lines_cleared})")
                self._send_attack(lines_cleared_this_frame)
            
            # 攻撃状況をデバッグ表示
            if self.outgoing_attacks:
                print(f"[DEBUG] 送信中攻撃: {self.outgoing_attacks}")
            if self.incoming_attacks:
                print(f"[DEBUG] 受信中攻撃: {self.incoming_attacks}")
        
        # 攻撃システムの更新
        self._update_attacks(dt)
        
        # ガベージライン処理
        self._process_garbage_lines()
        
        # ゲーム状態の定期送信
        current_time = time.time()
        if current_time - self.last_state_send > self.send_interval:
            self._send_game_state()
            self.last_state_send = current_time
        
        # ゲームオーバー判定
        if self.local_game.game_over and not self.game_over:
            self._handle_game_over("lose")
        
        return True
    
    def draw(self, screen: pygame.Surface):
        """ゲーム画面を描画"""
        # 背景
        screen.fill(config.theme["background"])
        
        if not self.game_started:
            self._draw_waiting_screen(screen)
            return
        
        # 自分のゲーム画面（メイン）
        self._draw_local_game(screen)
        
        # 相手のゲーム画面（小さく）
        self._draw_opponent_game(screen)
        
        # 攻撃状況表示
        self._draw_attack_display(screen)
        
        # UI要素
        self._draw_ui(screen)
        
        # ボタン
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons.values():
            button.update(mouse_pos)
            button.draw(screen)
        
        # ゲームオーバー表示
        if self.game_over:
            self._draw_game_over(screen)
    
    def _draw_waiting_screen(self, screen: pygame.Surface):
        """待機画面を描画"""
        text = big_font.render("対戦相手を待っています...", True, config.theme["text"])
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        screen.blit(text, text_rect)
    
    def _draw_local_game(self, screen: pygame.Surface):
        """自分のゲーム画面を描画"""
        # ゲーム盤面
        self.local_game.grid_x = self.local_game_x
        self.local_game.grid_y = self.local_game_y
        
        # 通常のゲーム描画を使用
        self.local_game.draw(screen)
    
    def _draw_opponent_game(self, screen: pygame.Surface):
        """相手のゲーム画面を描画"""
        if not self.opponent_game_state:
            return
        
        # 相手の盤面タイトル
        title_text = font.render("対戦相手", True, config.theme["text"])
        screen.blit(title_text, (self.opponent_game_x, self.opponent_game_y - int(30 * scale_factor)))
        
        # 相手のグリッド描画（簡易版）
        grid = self.opponent_game_state.get("grid", [])
        if grid:
            self._draw_mini_grid(screen, grid, self.opponent_game_x, self.opponent_game_y)
        
        # 相手のスコア表示
        score = self.opponent_game_state.get("score", 0)
        level = self.opponent_game_state.get("level", 1)
        lines = self.opponent_game_state.get("lines_cleared", 0)
        
        stats_y = self.opponent_game_y + int(300 * scale_factor * self.opponent_scale)
        
        score_text = small_font.render(f"スコア: {score}", True, config.theme["text"])
        screen.blit(score_text, (self.opponent_game_x, stats_y))
        
        level_text = small_font.render(f"レベル: {level}", True, config.theme["text"])
        screen.blit(level_text, (self.opponent_game_x, stats_y + int(15 * scale_factor)))
        
        lines_text = small_font.render(f"ライン: {lines}", True, config.theme["text"])
        screen.blit(lines_text, (self.opponent_game_x, stats_y + int(30 * scale_factor)))
    
    def _draw_mini_grid(self, screen: pygame.Surface, grid: List, x: int, y: int):
        """小さいグリッドを描画"""
        mini_block_size = int(BLOCK_SIZE * scale_factor * self.opponent_scale)
        
        for row in range(min(len(grid), GRID_HEIGHT)):
            for col in range(min(len(grid[row]) if row < len(grid) else 0, GRID_WIDTH)):
                if row < len(grid) and col < len(grid[row]) and grid[row][col] is not None:
                    block_x = x + col * mini_block_size
                    block_y = y + row * mini_block_size
                    
                    # ブロック色（相手の色なので少し暗くする）
                    color = grid[row][col]
                    if isinstance(color, (list, tuple)) and len(color) >= 3:
                        dark_color = tuple(max(0, c - 50) for c in color[:3])
                        pygame.draw.rect(screen, dark_color, 
                                       (block_x, block_y, mini_block_size, mini_block_size))
                        pygame.draw.rect(screen, config.theme["grid_line"], 
                                       (block_x, block_y, mini_block_size, mini_block_size), 1)
    
    def _draw_ui(self, screen: pygame.Surface):
        """UI要素を描画"""
        # チャット欄
        chat_rect = pygame.Rect(self.chat_x, self.chat_y, self.chat_width, self.chat_height)
        pygame.draw.rect(screen, (30, 30, 30, 180), chat_rect)
        pygame.draw.rect(screen, config.theme["grid_line"], chat_rect, 2)
        
        # チャットメッセージ
        y_offset = 5
        for i, msg in enumerate(self.chat_messages[-5:]):  # 最新5件
            msg_text = small_font.render(msg, True, config.theme["text"])
            screen.blit(msg_text, (self.chat_x + 5, self.chat_y + y_offset))
            y_offset += 20
        
        pass
    
    def _draw_attack_display(self, screen: pygame.Surface):
        """攻撃状況を描画"""
        # 攻撃表示パネル
        attack_rect = pygame.Rect(self.attack_display_x, self.attack_display_y, 
                                 self.attack_display_width, self.attack_display_height)
        pygame.draw.rect(screen, (30, 30, 30, 200), attack_rect)
        pygame.draw.rect(screen, config.theme["grid_line"], attack_rect, 2)
        
        # タイトル
        title_text = font.render("攻撃状況", True, config.theme["text"])
        screen.blit(title_text, (self.attack_display_x + 10, self.attack_display_y + 10))
        
        y_offset = 40
        
        # デバッグ情報
        debug_text = small_font.render(f"送信キュー: {len(self.outgoing_attacks)}", True, config.theme["text"])
        screen.blit(debug_text, (self.attack_display_x + 10, self.attack_display_y + y_offset))
        y_offset += 20
        
        debug_text2 = small_font.render(f"受信キュー: {len(self.incoming_attacks)}", True, config.theme["text"])
        screen.blit(debug_text2, (self.attack_display_x + 10, self.attack_display_y + y_offset))
        y_offset += 25
        
        # 送信中の攻撃
        if self.outgoing_attacks:
            out_text = small_font.render("送信中:", True, (255, 150, 150))
            screen.blit(out_text, (self.attack_display_x + 10, self.attack_display_y + y_offset))
            y_offset += 20
            
            for i, (delay, lines) in enumerate(self.outgoing_attacks[:3]):
                attack_text = small_font.render(f"  {lines}ライン (あと{delay:.1f}秒)", True, (255, 100, 100))
                screen.blit(attack_text, (self.attack_display_x + 10, self.attack_display_y + y_offset))
                y_offset += 15
        
        # 受信中の攻撃
        if self.incoming_attacks:
            in_text = small_font.render("受信中:", True, (150, 150, 255))
            screen.blit(in_text, (self.attack_display_x + 10, self.attack_display_y + y_offset))
            y_offset += 20
            
            for i, (delay, lines) in enumerate(self.incoming_attacks[:3]):
                attack_text = small_font.render(f"  {lines}ライン (あと{delay:.1f}秒)", True, (100, 100, 255))
                screen.blit(attack_text, (self.attack_display_x + 10, self.attack_display_y + y_offset))
                y_offset += 15
    
    def _draw_game_over(self, screen: pygame.Surface):
        """ゲームオーバー画面を描画"""
        # 半透明オーバーレイ
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # 結果テキスト
        if self.winner == "local":
            result_text = "勝利！"
            color = (100, 255, 100)
        elif self.winner == "opponent":
            result_text = "敗北..."
            color = (255, 100, 100)
        else:
            result_text = "引き分け"
            color = (255, 255, 100)
        
        text = big_font.render(result_text, True, color)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        screen.blit(text, text_rect)
    
    def _handle_key_press(self, key: int):
        """キー押下処理"""
        action = None
        
        # キー設定から対応するアクションを取得
        key_bindings = config.settings.get("key_bindings", {})
        
        if key == key_bindings.get("move_left", pygame.K_LEFT):
            action = GameAction.MOVE_LEFT
        elif key == key_bindings.get("move_right", pygame.K_RIGHT):
            action = GameAction.MOVE_RIGHT
        elif key == key_bindings.get("rotate_cw", pygame.K_UP):
            action = GameAction.ROTATE_CW
        elif key == key_bindings.get("rotate_ccw", pygame.K_z):
            action = GameAction.ROTATE_CCW
        elif key == key_bindings.get("soft_drop", pygame.K_DOWN):
            action = GameAction.SOFT_DROP
        elif key == key_bindings.get("hard_drop", pygame.K_SPACE):
            action = GameAction.HARD_DROP
        elif key == key_bindings.get("hold", pygame.K_c):
            action = GameAction.HOLD
        
        # ローカルゲームに反映
        if action:
            self._apply_action_to_local_game(action)
            
            # アクションをサーバーに送信
            if self.client:
                self.client.send_game_action(action)
    
    def _apply_action_to_local_game(self, action: GameAction):
        """アクションをローカルゲームに適用"""
        if action == GameAction.MOVE_LEFT:
            self.local_game.move(-1)
        elif action == GameAction.MOVE_RIGHT:
            self.local_game.move(1)
        elif action == GameAction.ROTATE_CW:
            self.local_game.rotate(True)  # 時計回り
        elif action == GameAction.ROTATE_CCW:
            self.local_game.rotate(False)  # 反時計回り
        elif action == GameAction.SOFT_DROP:
            # ソフトドロップフラグを設定
            self.local_game.soft_drop = True
        elif action == GameAction.HARD_DROP:
            self.local_game.drop()  # ハードドロップ
        elif action == GameAction.HOLD:
            self.local_game.hold_piece()
    
    def _handle_das_arr(self, keys_held: Dict, dt: float):
        """DAS/ARR処理"""
        # キー設定を取得
        key_bindings = config.settings.get("key_bindings", {})
        
        # DAS/ARR設定を取得
        das_delay = config.settings.get("das_delay", 0.167)
        arr_delay = config.settings.get("arr_delay", 0.033)
        
        # DAS/ARRタイマーの初期化（初回のみ）
        if not hasattr(self, 'das_left_timer'):
            self.das_left_timer = 0
            self.das_right_timer = 0
            self.arr_left_timer = 0
            self.arr_right_timer = 0
        
        # 左右移動のDAS/ARR処理
        left_key = key_bindings.get("move_left", pygame.K_LEFT)
        right_key = key_bindings.get("move_right", pygame.K_RIGHT)
        
        if keys_held.get(left_key) and not keys_held.get(right_key):
            self.das_left_timer += dt
            if self.das_left_timer >= das_delay:
                self.arr_left_timer += dt
                if self.arr_left_timer >= arr_delay:
                    self.local_game.move(-1)
                    self.arr_left_timer = 0
        elif keys_held.get(right_key) and not keys_held.get(left_key):
            self.das_right_timer += dt
            if self.das_right_timer >= das_delay:
                self.arr_right_timer += dt
                if self.arr_right_timer >= arr_delay:
                    self.local_game.move(1)
                    self.arr_right_timer = 0
        else:
            # どちらも押されていない、または両方押されている場合はリセット
            self.das_left_timer = 0
            self.das_right_timer = 0
            self.arr_left_timer = 0
            self.arr_right_timer = 0
    
    def _handle_key_release(self, key: int):
        """キー離上処理"""
        # ソフトドロップの終了など
        key_bindings = config.settings.get("key_bindings", {})
        if key == key_bindings.get("soft_drop", pygame.K_DOWN):
            self.local_game.soft_drop = False
    
    def _send_attack(self, lines_cleared: int):
        """攻撃を送信（遅延付き）"""
        attack_power = 0
        
        # ライン消去数に応じた攻撃力
        if lines_cleared == 1:
            attack_power = 0  # シングルは攻撃なし
        elif lines_cleared == 2:
            attack_power = 1  # ダブル
        elif lines_cleared == 3:
            attack_power = 2  # トリプル
        elif lines_cleared == 4:
            attack_power = 4  # テトリス
        
        # スピンボーナス
        if hasattr(self.local_game, 'current_spin_type') and self.local_game.current_spin_type:
            if "T-Spin" in self.local_game.current_spin_type:
                attack_power += 2
            else:
                attack_power += 1
        
        print(f"_send_attack呼び出し: lines_cleared={lines_cleared}, attack_power={attack_power}")
        
        if attack_power > 0:
            # まず相殺処理
            cancelled = 0
            for attack in self.incoming_attacks[:]:
                if cancelled < attack_power:
                    cancel_amount = min(attack_power - cancelled, attack[1])
                    attack[1] -= cancel_amount
                    cancelled += cancel_amount
                    if attack[1] <= 0:
                        self.incoming_attacks.remove(attack)
            
            # 相殺後の残り攻撃力
            remaining_attack = attack_power - cancelled
            
            if remaining_attack > 0:
                # 攻撃を遅延キューに追加（2秒後に発動）
                delay = 2.0
                self.outgoing_attacks.append([delay, remaining_attack])
                
                # 相手にも攻撃予告を送信
                if self.client:
                    attack_msg = {
                        "event": "attack_warning",
                        "lines": remaining_attack,
                        "delay": delay,
                        "timestamp": time.time()
                    }
                    self.client.send_game_state(attack_msg)
    
    def _update_attacks(self, dt: float):
        """攻撃の更新処理"""
        # 送信中の攻撃の遅延を減らす
        for attack in self.outgoing_attacks[:]:
            attack[0] -= dt  # delay -= dt
            if attack[0] <= 0:
                # 攻撃を実際に送信
                lines = attack[1]
                if self.client:
                    attack_msg = {
                        "event": "attack",
                        "lines": lines,
                        "timestamp": time.time()
                    }
                    self.client.send_game_state(attack_msg)
                self.outgoing_attacks.remove(attack)
        
        # 受信中の攻撃の遅延を減らす
        for attack in self.incoming_attacks[:]:
            attack[0] -= dt  # delay -= dt
            if attack[0] <= 0:
                # ガベージラインを追加
                lines = attack[1]
                for _ in range(lines):
                    self.pending_garbage.append(1)
                self.incoming_attacks.remove(attack)
    
    def _process_garbage_lines(self):
        """ガベージラインを処理"""
        if self.pending_garbage and not self.local_game.game_over:
            # 一度に1ラインずつ追加
            garbage_count = self.pending_garbage.pop(0)
            self._add_garbage_line()
    
    def _add_garbage_line(self):
        """ガベージラインを追加"""
        # グリッドを上にシフト
        for row in range(1, GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                self.local_game.grid[row - 1][col] = self.local_game.grid[row][col]
        
        # 最下段にガベージラインを追加（1箇所空きを作る）
        empty_col = __import__('random').randint(0, GRID_WIDTH - 1)
        for col in range(GRID_WIDTH):
            if col != empty_col:
                self.local_game.grid[GRID_HEIGHT - 1][col] = (128, 128, 128)  # グレー
            else:
                self.local_game.grid[GRID_HEIGHT - 1][col] = None
    
    def _send_game_state(self):
        """ゲーム状態を送信"""
        if not self.client or self.local_game.game_over:
            return
        
        state = {
            "event": "game_state",
            "grid": self.local_game.grid,
            "score": self.local_game.score,
            "level": self.local_game.level,
            "lines_cleared": self.local_game.lines_cleared,
            "current_piece": {
                "shape": self.local_game.current_piece["shape"] if self.local_game.current_piece else None,
                "x": self.local_game.current_piece["x"] if self.local_game.current_piece else 0,
                "y": self.local_game.current_piece["y"] if self.local_game.current_piece else 0,
                "color": self.local_game.current_piece["color"] if self.local_game.current_piece else None,
            },
            "timestamp": time.time()
        }
        
        self.client.send_game_state(state)
    
    def _handle_mouse_click(self, mouse_pos: tuple):
        """マウスクリック処理"""
        print(f"オンラインゲーム マウスクリック: {mouse_pos}")
        
        # ボタンクリック判定
        for button_name, button in self.buttons.items():
            if button.rect.collidepoint(mouse_pos):
                print(f"ボタンクリック: {button_name}")
                if button.action:
                    button.action()
                return
    
    def _handle_game_over(self, result: str):
        """ゲームオーバー処理"""
        self.game_over = True
        
        if result == "win":
            self.winner = "local"
        elif result == "lose":
            self.winner = "opponent"
        else:
            self.winner = None
        
        # ゲームオーバーメッセージを送信
        if self.client:
            game_over_msg = {
                "event": "game_over",
                "result": result,
                "timestamp": time.time()
            }
            self.client.send_game_state(game_over_msg)
    
    def _on_message_received(self, message: Dict[str, Any]):
        """メッセージ受信コールバック"""
        msg_type = message.get("type")
        data = message.get("data", {})
        
        if msg_type == MessageType.GAME_STATE.value:
            event = data.get("event")
            
            if event == "game_state":
                # 相手のゲーム状態を更新
                self.opponent_game_state = data
            
            elif event == "attack_warning":
                # 攻撃予告を受信
                lines = data.get("lines", 0)
                delay = data.get("delay", 2.0)
                self.incoming_attacks.append([delay, lines])
            
            elif event == "attack":
                # 即座に攻撃を受信（旧システム対応）
                lines = data.get("lines", 0)
                for _ in range(lines):
                    self.pending_garbage.append(1)
            
            elif event == "game_over":
                # 相手のゲームオーバー
                if not self.game_over:
                    self._handle_game_over("win")
        
        elif msg_type == MessageType.CHAT_MESSAGE.value:
            # チャットメッセージを受信
            player_name = data.get("player_name", "相手")
            message_text = data.get("message", "")
            self.chat_messages.append(f"{player_name}: {message_text}")
    
    # ボタンアクション
    def _surrender(self):
        """降参"""
        self._handle_game_over("lose")
    
    def _back_to_lobby(self):
        """ロビーに戻る"""
        if self.client:
            self.client.disconnect()
        # ロビー画面に戻る
        self.should_exit = True
    
    def _test_attack(self):
        """テスト用攻撃"""
        print("[TEST] テスト攻撃ボタンが押されました")
        self._send_attack(2)  # ダブル相当の攻撃をテスト
