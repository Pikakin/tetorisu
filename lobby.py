# オンライン対戦ロビー画面
import pygame
import threading
import time
from typing import Dict, List, Optional, Callable
from ui import Button
try:
    from network.client import TetrisClient
    from network.udp_client import UDPTetrisClient
    from network.protocol import MessageType
except ImportError:
    # モジュールが見つからない場合のフォールバック
    TetrisClient = None
    UDPTetrisClient = None
    MessageType = None
import config
from config import scale_factor, font, small_font, big_font


class RoomInfo:
    """ルーム情報クラス"""
    
    def __init__(self, room_id: str, players: List[str], max_players: int = 2, has_password: bool = False):
        self.room_id = room_id
        self.players = players
        self.max_players = max_players
        self.has_password = has_password
        self.created_at = time.time()
    
    def is_full(self) -> bool:
        return len(self.players) >= self.max_players
    
    def get_status_text(self) -> str:
        if self.is_full():
            return "満員"
        return f"{len(self.players)}/{self.max_players}"


class OnlineLobby:
    """オンライン対戦ロビークラス"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # ネットワーククライアント
        self.client = None  # TetrisClient または UDPTetrisClient
        self.connected = False
        self.use_udp = True  # デフォルトでUDPを使用
        
        # ロビー状態
        self.current_screen = "connect"  # "connect", "lobby", "room", "matching"
        self.rooms: Dict[str, RoomInfo] = {}
        self.current_room_id = ""
        self.selected_room_id = ""
        self.player_name = ""
        self.chat_messages: List[Dict] = []
        self.matching_status = ""
        self.last_room_list_request = 0
        
        # UI要素
        self.buttons = {}
        self.text_inputs = {}
        self.selected_room_id = ""
        self.scroll_offset = 0
        
        # 入力状態
        self.input_text = ""
        self.input_active = False
        self.input_field = ""
        
        # コールバック
        self.on_game_start: Optional[Callable] = None
        self.on_back_to_menu: Optional[Callable] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI要素を初期化"""
        button_width = int(200 * scale_factor)
        button_height = int(40 * scale_factor)
        
        # 接続画面のボタン
        self.buttons["connect"] = Button(
            self.screen_width // 2 - button_width // 2,
            self.screen_height // 2 + int(100 * scale_factor),
            button_width, button_height,
            "接続", self._connect_to_server
        )
        
        # ロビー画面のボタン
        self.buttons["create_room"] = Button(
            int(50 * scale_factor),
            self.screen_height - int(100 * scale_factor),
            button_width, button_height,
            "ルーム作成", self._create_room
        )
        
        self.buttons["join_room"] = Button(
            int(270 * scale_factor),
            self.screen_height - int(100 * scale_factor),
            button_width, button_height,
            "ルーム参加", self._join_selected_room
        )
        
        self.buttons["quick_match"] = Button(
            int(490 * scale_factor),
            self.screen_height - int(100 * scale_factor),
            button_width, button_height,
            "クイックマッチ", self._start_quick_match
        )
        
        self.buttons["back_lobby"] = Button(
            int(50 * scale_factor),
            int(50 * scale_factor),
            button_width, button_height,
            "戻る", self._back_to_menu
        )
        
        # ルーム画面のボタン
        self.buttons["leave_room"] = Button(
            int(50 * scale_factor),
            self.screen_height - int(100 * scale_factor),
            button_width, button_height,
            "ルーム退出", self._leave_room
        )
        
        self.buttons["start_game"] = Button(
            self.screen_width - int(250 * scale_factor),
            self.screen_height - int(100 * scale_factor),
            button_width, button_height,
            "ゲーム開始", self._start_game
        )
    
    def connect_to_server(self, host: str = "localhost", port: int = 12346, player_name: str = "Player"):
        """サーバーに接続"""
        self.player_name = player_name
        
        if self.client:
            self.client.disconnect()
        
        # UDPまたはTCPクライアントを選択
        if self.use_udp and UDPTetrisClient:
            self.client = UDPTetrisClient()
            print(f"UDP接続を使用: {host}:{port}")
        elif TetrisClient:
            self.client = TetrisClient()
            port = 12345  # TCPポート
            print(f"TCP接続を使用: {host}:{port}")
        else:
            return False
        
        # コールバック設定
        print("ロビー: コールバック設定中...")
        self.client.on_connected = self._on_connected
        self.client.on_disconnected = self._on_disconnected
        self.client.on_message_received = self._on_message_received
        self.client.on_error = self._on_error
        print(f"ロビー: コールバック設定完了 - on_message_received={self.client.on_message_received is not None}")
        
        # 接続試行
        if self.client.connect(host, port, player_name):
            self.matching_status = "接続中..."
            return True
        else:
            self.matching_status = "接続失敗"
            return False
    
    def disconnect(self):
        """サーバーから切断"""
        if self.client:
            self.client.disconnect()
        self.connected = False
        self.current_screen = "connect"
    
    def update(self, events: List[pygame.event.Event], mouse_pos: tuple) -> bool:
        """ロビーを更新"""
        # ロビー画面でルーム一覧を定期的に更新
        if self.current_screen == "lobby" and self.connected and self.client:
            current_time = time.time()
            if current_time - self.last_room_list_request > 5:  # 5秒間隔
                print(f"ルーム一覧を要求中... (前回: {self.last_room_list_request:.1f}秒前)")
                self.client.list_rooms()
                self.last_room_list_request = current_time
        # キーボード入力処理
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.input_active:
                    if event.key == pygame.K_RETURN:
                        self._submit_input()
                    elif event.key == pygame.K_ESCAPE:
                        self.input_active = False
                        self.input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    else:
                        if len(self.input_text) < 20 and event.unicode.isprintable():
                            self.input_text += event.unicode
                
                elif event.key == pygame.K_ESCAPE:
                    if self.current_screen == "lobby":
                        self._back_to_menu()
                    elif self.current_screen == "room":
                        self._leave_room()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    self._handle_mouse_click(mouse_pos)
        
        # ボタン更新（画面に応じて制限）
        valid_buttons = []
        if self.current_screen == "connect":
            valid_buttons = ["connect"]
        elif self.current_screen == "lobby":
            valid_buttons = ["create_room", "join_room", "quick_match", "back_lobby"]
        elif self.current_screen == "room":
            valid_buttons = ["leave_room", "start_game"]
        elif self.current_screen == "matching":
            valid_buttons = ["back_lobby"]
        
        for button_name, button in self.buttons.items():
            if button_name in valid_buttons:
                button.update(mouse_pos)
        
        return True
    
    def draw(self, screen: pygame.Surface):
        """ロビーを描画"""
        # 背景
        screen.fill(config.theme["background"])
        
        if self.current_screen == "connect":
            self._draw_connect_screen(screen)
        elif self.current_screen == "lobby":
            self._draw_lobby_screen(screen)
        elif self.current_screen == "room":
            self._draw_room_screen(screen)
        elif self.current_screen == "matching":
            self._draw_matching_screen(screen)
    
    def _draw_connect_screen(self, screen: pygame.Surface):
        """接続画面を描画"""
        # タイトル
        title_text = big_font.render("オンライン対戦", True, config.theme["text"])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, int(200 * scale_factor)))
        screen.blit(title_text, title_rect)
        
        # 入力フィールド
        input_y = int(300 * scale_factor)
        
        # プレイヤー名入力
        name_label = font.render("プレイヤー名:", True, config.theme["text"])
        screen.blit(name_label, (self.screen_width // 2 - int(100 * scale_factor), input_y))
        
        name_rect = pygame.Rect(
            self.screen_width // 2 - int(100 * scale_factor),
            input_y + int(30 * scale_factor),
            int(200 * scale_factor),
            int(30 * scale_factor)
        )
        
        color = config.theme["button_hover"] if self.input_active and self.input_field == "name" else config.theme["grid_line"]
        pygame.draw.rect(screen, color, name_rect, 2)
        
        name_text = font.render(self.input_text if self.input_active and self.input_field == "name" else self.player_name, True, config.theme["text"])
        screen.blit(name_text, (name_rect.x + 5, name_rect.y + 5))
        
        # 接続ボタン
        self.buttons["connect"].draw(screen)
        
        # 戻るボタン
        self.buttons["back_lobby"].draw(screen)
        
        # ステータス表示
        if self.matching_status:
            status_text = font.render(self.matching_status, True, config.theme["text"])
            status_rect = status_text.get_rect(center=(self.screen_width // 2, int(400 * scale_factor)))
            screen.blit(status_text, status_rect)
    
    def _draw_lobby_screen(self, screen: pygame.Surface):
        """ロビー画面を描画"""
        # タイトル
        title_text = big_font.render("オンラインロビー", True, config.theme["text"])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, int(50 * scale_factor)))
        screen.blit(title_text, title_rect)
        
        # デバッグ: 現在の状態表示
        debug_text = font.render(f"画面: {self.current_screen}, 接続: {self.connected}", True, config.theme["text"])
        screen.blit(debug_text, (int(50 * scale_factor), int(70 * scale_factor)))
        
        # プレイヤー名表示
        player_text = font.render(f"プレイヤー: {self.player_name}", True, config.theme["text"])
        screen.blit(player_text, (int(50 * scale_factor), int(100 * scale_factor)))
        
        # ルームリスト
        self._draw_room_list(screen)
        
        # ボタン
        self.buttons["create_room"].draw(screen)
        self.buttons["join_room"].draw(screen)
        self.buttons["quick_match"].draw(screen)
        self.buttons["back_lobby"].draw(screen)
    
    def _draw_room_list(self, screen: pygame.Surface):
        """ルームリストを描画"""
        list_y = int(150 * scale_factor)
        list_height = int(300 * scale_factor)
        
        # ヘッダー
        header_text = font.render("ルーム一覧", True, config.theme["text"])
        screen.blit(header_text, (int(50 * scale_factor), list_y))
        
        # リスト背景
        list_rect = pygame.Rect(
            int(50 * scale_factor),
            list_y + int(30 * scale_factor),
            self.screen_width - int(100 * scale_factor),
            list_height
        )
        pygame.draw.rect(screen, config.theme["grid_line"], list_rect, 2)
        
        # ルーム項目
        item_height = int(40 * scale_factor)
        y_offset = 0
        
        for i, (room_id, room_info) in enumerate(self.rooms.items()):
            if y_offset >= list_height:
                break
            
            item_y = list_rect.y + y_offset + int(5 * scale_factor)
            
            # 選択ハイライト
            if room_id == self.selected_room_id:
                highlight_rect = pygame.Rect(list_rect.x + 2, item_y, list_rect.width - 4, item_height)
                pygame.draw.rect(screen, config.theme["button_hover"], highlight_rect)
            
            # ルーム情報
            room_text = f"{room_id} ({room_info.get_status_text()})"
            if room_info.has_password:
                room_text += " 🔒"
            
            # 満員の場合は少し暗い色を使用
            text_color = tuple(c//2 for c in config.theme["text"]) if room_info.is_full() else config.theme["text"]
            room_surface = font.render(room_text, True, text_color)
            screen.blit(room_surface, (list_rect.x + int(10 * scale_factor), item_y + int(10 * scale_factor)))
            
            y_offset += item_height
    
    def _draw_room_screen(self, screen: pygame.Surface):
        """ルーム画面を描画"""
        # タイトル
        title_text = big_font.render(f"ルーム: {self.current_room_id}", True, config.theme["text"])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, int(50 * scale_factor)))
        screen.blit(title_text, title_rect)
        
        # プレイヤーリスト
        # TODO: 実装
        
        # チャット
        # TODO: 実装
        
        # ボタン
        self.buttons["leave_room"].draw(screen)
        self.buttons["start_game"].draw(screen)
    
    def _draw_matching_screen(self, screen: pygame.Surface):
        """マッチング画面を描画"""
        # タイトル
        title_text = big_font.render("マッチング中...", True, config.theme["text"])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        screen.blit(title_text, title_rect)
        
        # ステータス
        if self.matching_status:
            status_text = font.render(self.matching_status, True, config.theme["text"])
            status_rect = status_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + int(50 * scale_factor)))
            screen.blit(status_text, status_rect)
    
    def _handle_mouse_click(self, mouse_pos: tuple):
        """マウスクリックを処理"""
        print(f"マウスクリック: {mouse_pos}, current_screen={self.current_screen}")
        
        # 画面に応じて有効なボタンを制限
        valid_buttons = []
        if self.current_screen == "connect":
            valid_buttons = ["connect"]
        elif self.current_screen == "lobby":
            valid_buttons = ["create_room", "join_room", "quick_match", "back_lobby"]
        elif self.current_screen == "room":
            valid_buttons = ["leave_room", "start_game"]
        elif self.current_screen == "matching":
            valid_buttons = ["back_lobby"]
        
        # ボタンクリック判定
        for button_name, button in self.buttons.items():
            if button_name in valid_buttons and button.rect.collidepoint(mouse_pos):
                print(f"ボタンクリック: {button_name}")
                if button.action:
                    button.action()
                return
        
        # ルームリスト選択
        if self.current_screen == "lobby":
            self._handle_room_list_click(mouse_pos)
        
        # 入力フィールドクリック
        if self.current_screen == "connect":
            self._handle_input_field_click(mouse_pos)
    
    def _handle_room_list_click(self, mouse_pos: tuple):
        """ルームリストクリックを処理"""
        list_y = int(180 * scale_factor)
        list_height = int(300 * scale_factor)
        list_rect = pygame.Rect(
            int(50 * scale_factor),
            list_y,
            self.screen_width - int(100 * scale_factor),
            list_height
        )
        
        if list_rect.collidepoint(mouse_pos):
            item_height = int(40 * scale_factor)
            relative_y = mouse_pos[1] - list_rect.y
            item_index = int(relative_y // item_height)
            
            room_ids = list(self.rooms.keys())
            if 0 <= item_index < len(room_ids):
                self.selected_room_id = room_ids[item_index]
    
    def _handle_input_field_click(self, mouse_pos: tuple):
        """入力フィールドクリックを処理"""
        input_y = int(330 * scale_factor)
        name_rect = pygame.Rect(
            self.screen_width // 2 - int(100 * scale_factor),
            input_y,
            int(200 * scale_factor),
            int(30 * scale_factor)
        )
        
        if name_rect.collidepoint(mouse_pos):
            self.input_active = True
            self.input_field = "name"
            self.input_text = self.player_name
        else:
            self.input_active = False
            self.input_field = ""
    
    # ボタンアクション
    def _connect_to_server(self):
        """サーバー接続ボタン"""
        if self.input_text:
            self.player_name = self.input_text
        
        if not self.player_name:
            self.matching_status = "プレイヤー名を入力してください"
            return
        
        self.connect_to_server(player_name=self.player_name)
    
    def _create_room(self):
        """ルーム作成ボタン"""
        print(f"ルーム作成ボタンクリック! client={self.client is not None}, connected={self.connected}")
        if self.client and self.connected:
            room_id = f"room_{int(time.time())}"
            print(f"ルーム作成実行: room_id={room_id}")
            self.client.create_room(room_id)
        else:
            print("ルーム作成失敗: クライアントが接続されていません")
    
    def _join_selected_room(self):
        """選択されたルームに参加"""
        if self.selected_room_id and self.client and self.connected:
            self.client.join_room(self.selected_room_id)
    
    def _start_quick_match(self):
        """クイックマッチ開始"""
        self.current_screen = "matching"
        self.matching_status = "対戦相手を探しています..."
        # TODO: マッチメイキング実装
    
    def _leave_room(self):
        """ルーム退出"""
        if self.client and self.connected:
            self.client.leave_room()
            self.current_screen = "lobby"
            self.current_room_id = ""
    
    def _start_game(self):
        """ゲーム開始"""
        if self.client and self.connected:
            # ゲーム開始メッセージを送信
            start_msg = {
                "event": "start_game",
                "timestamp": time.time()
            }
            self.client.send_game_state(start_msg)
            
            if self.on_game_start:
                self.on_game_start(self.client)
    
    def _back_to_menu(self):
        """メニューに戻る"""
        self.disconnect()
        if self.on_back_to_menu:
            self.on_back_to_menu()
    
    def _submit_input(self):
        """入力確定"""
        if self.input_field == "name":
            self.player_name = self.input_text
        
        self.input_active = False
        self.input_field = ""
        self.input_text = ""
    
    # ネットワークコールバック
    def _on_connected(self):
        """接続成功コールバック"""
        print(f"_on_connected: 現在の画面={self.current_screen}")
        self.connected = True
        # 画面が"connect"の時のみ"lobby"に変更（他の画面は保持）
        if self.current_screen == "connect":
            self.current_screen = "lobby"
            print(f"_on_connected: 画面をlobbyに変更")
        else:
            print(f"_on_connected: 画面を{self.current_screen}のまま保持")
        # ルーム一覧タイマーをリセット
        self.last_room_list_request = 0
        print("ルーム一覧タイマーをリセットしました")
        self.matching_status = "接続完了"
    
    def _on_disconnected(self, reason: str):
        """切断コールバック"""
        self.connected = False
        self.current_screen = "connect"
        self.matching_status = f"切断: {reason}"
    
    def _on_message_received(self, message: Dict):
        """メッセージ受信コールバック"""
        if not MessageType:
            return
            
        msg_type = message.get("type")
        data = message.get("data", {})
        
        print(f"ロビー受信メッセージ: Type={msg_type}, Data={data}")
        print(f"現在の画面: {self.current_screen}")
        print(f"MessageType.CREATE_ROOM.value: {MessageType.CREATE_ROOM.value}")
        
        # 接続成功時の処理
        if msg_type == MessageType.CONNECT.value and data.get("success"):
            if hasattr(self.client, 'player_id'):
                self.client.player_id = data.get("player_id", "")
                print(f"プレイヤーID設定: {self.client.player_id}")
        
        if msg_type == MessageType.CREATE_ROOM.value:
            print(f"CREATE_ROOMメッセージ処理: success={data.get('success')}, room_id={data.get('room_id', '')}")
            if data.get("success"):
                self.current_room_id = data.get("room_id", "")
                self.current_screen = "room"
                print(f"ルーム作成成功! 画面を切り替え: {self.current_screen}, room_id={self.current_room_id}")
        
        elif msg_type == MessageType.JOIN_ROOM.value:
            if data.get("success"):
                self.current_room_id = data.get("room_id", "")
                self.current_screen = "room"
        
        elif msg_type == MessageType.LIST_ROOMS.value:
            # ルーム一覧更新
            rooms_data = data.get("rooms", [])
            self.rooms.clear()
            for room_data in rooms_data:
                room_id = room_data.get("room_id", "")
                if room_id:
                    self.rooms[room_id] = RoomInfo(
                        room_id=room_id,
                        players=room_data.get("players", []),
                        max_players=room_data.get("max_players", 2),
                        has_password=room_data.get("has_password", False)
                    )
        
        elif msg_type == MessageType.ROOM_INFO.value:
            # ルーム情報更新
            pass
        
        elif msg_type == MessageType.GAME_STATE.value:
            print(f"GAME_STATEメッセージ受信: {data}")
            # ゲーム開始処理
            event = data.get("event")
            if event in ["start_game", "game_start"]:
                print("ゲーム開始イベント検出 - オンラインゲームを開始")
                if self.on_game_start:
                    self.on_game_start(self.client)
        
        elif msg_type == MessageType.ERROR.value:
            self.matching_status = data.get("error_message", "エラーが発生しました")
    
    def _on_error(self, error_code: str, error_message: str):
        """エラーコールバック"""
        self.matching_status = f"エラー: {error_message}"
