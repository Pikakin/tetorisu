# サーバー側通信
import socket
import threading
import time
import json
from typing import Dict, List, Optional, Any
from network.protocol import Protocol, MessageType, GameAction


class TetrisPlayer:
    """プレイヤー情報クラス"""
    
    def __init__(self, socket: socket.socket, address: tuple, player_id: str):
        self.socket = socket
        self.address = address
        self.player_id = player_id
        self.player_name = ""
        self.room_id = ""
        self.connected = True
        self.last_heartbeat = time.time()


class TetrisRoom:
    """ルーム情報クラス"""
    
    def __init__(self, room_id: str, password: Optional[str] = None, max_players: int = 2):
        self.room_id = room_id
        self.password = password
        self.max_players = max_players
        self.players: List[TetrisPlayer] = []
        self.game_started = False
        self.created_at = time.time()
    
    def add_player(self, player: TetrisPlayer) -> bool:
        """プレイヤーをルームに追加"""
        if len(self.players) >= self.max_players:
            return False
        
        self.players.append(player)
        player.room_id = self.room_id
        return True
    
    def remove_player(self, player: TetrisPlayer):
        """プレイヤーをルームから削除"""
        if player in self.players:
            self.players.remove(player)
            player.room_id = ""
    
    def is_empty(self) -> bool:
        """ルームが空かどうか"""
        return len(self.players) == 0
    
    def is_full(self) -> bool:
        """ルームが満員かどうか"""
        return len(self.players) >= self.max_players
    
    def broadcast_message(self, message: str, exclude_player: Optional[TetrisPlayer] = None):
        """ルーム内の全プレイヤーにメッセージを送信"""
        for player in self.players[:]:  # コピーを作成して安全にイテレート
            if player != exclude_player and player.connected:
                try:
                    TetrisServer._send_message_to_player(player, message)
                except:
                    # 送信失敗したプレイヤーは削除
                    self.remove_player(player)


class TetrisServer:
    """テトリスサーバークラス"""
    
    def __init__(self, host: str = "localhost", port: int = 12345):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        
        # プレイヤー管理
        self.players: Dict[str, TetrisPlayer] = {}
        self.players_lock = threading.Lock()
        
        # ルーム管理
        self.rooms: Dict[str, TetrisRoom] = {}
        self.rooms_lock = threading.Lock()
        
        # 統計情報
        self.total_connections = 0
        self.start_time = time.time()
    
    def start(self) -> bool:
        """サーバーを開始"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
            
            self.running = True
            print(f"テトリスサーバーが {self.host}:{self.port} で開始されました")
            
            # ハートビートスレッドを開始
            heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            heartbeat_thread.start()
            
            # クリーンアップスレッドを開始
            cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            cleanup_thread.start()
            
            # クライアント接続を待機
            while self.running:
                try:
                    client_socket, address = self.socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except socket.error:
                    if self.running:
                        print("クライアント接続受付エラー")
            
            return True
            
        except Exception as e:
            print(f"サーバー開始エラー: {e}")
            return False
    
    def stop(self):
        """サーバーを停止"""
        print("サーバーを停止中...")
        self.running = False
        
        # 全プレイヤーに切断通知
        with self.players_lock:
            for player in list(self.players.values()):
                self._disconnect_player(player)
        
        # ソケットを閉じる
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print("サーバーが停止されました")
    
    def _handle_client(self, client_socket: socket.socket, address: tuple):
        """クライアント接続を処理"""
        player_id = f"player_{self.total_connections}_{int(time.time())}"
        self.total_connections += 1
        
        player = TetrisPlayer(client_socket, address, player_id)
        
        try:
            with self.players_lock:
                self.players[player_id] = player
            
            print(f"クライアント接続: {address} (ID: {player_id})")
            
            # メッセージ受信ループ
            while self.running and player.connected:
                try:
                    # メッセージ長を受信
                    length_bytes = self._recv_exactly(client_socket, 4)
                    if not length_bytes:
                        break
                    
                    message_length = int.from_bytes(length_bytes, byteorder='big')
                    if message_length <= 0 or message_length > 1024 * 1024:  # 1MBまで
                        break
                    
                    # メッセージ本体を受信
                    message_bytes = self._recv_exactly(client_socket, message_length)
                    if not message_bytes:
                        break
                    
                    message_str = message_bytes.decode('utf-8')
                    message_data = Protocol.parse_message(message_str)
                    
                    if message_data:
                        self._process_message(player, message_data)
                    
                    # ハートビート更新
                    player.last_heartbeat = time.time()
                    
                except Exception as e:
                    print(f"メッセージ処理エラー (Player {player_id}): {e}")
                    break
        
        except Exception as e:
            print(f"クライアント処理エラー: {e}")
        
        finally:
            self._disconnect_player(player)
    
    def _process_message(self, player: TetrisPlayer, message: Dict[str, Any]):
        """受信メッセージを処理"""
        msg_type = message.get("type")
        data = message.get("data", {})
        
        try:
            if msg_type == MessageType.CONNECT.value:
                self._handle_connect(player, data)
            elif msg_type == MessageType.DISCONNECT.value:
                self._handle_disconnect(player)
            elif msg_type == MessageType.CREATE_ROOM.value:
                self._handle_create_room(player, data)
            elif msg_type == MessageType.JOIN_ROOM.value:
                self._handle_join_room(player, data)
            elif msg_type == MessageType.LEAVE_ROOM.value:
                self._handle_leave_room(player)
            elif msg_type == MessageType.PLAYER_ACTION.value:
                self._handle_player_action(player, data)
            elif msg_type == MessageType.GAME_STATE.value:
                self._handle_game_state(player, data)
            elif msg_type == MessageType.CHAT_MESSAGE.value:
                self._handle_chat_message(player, data)
            elif msg_type == MessageType.HEARTBEAT.value:
                # ハートビートは自動的に処理される
                pass
            else:
                self._send_error(player, "UNKNOWN_MESSAGE", f"不明なメッセージタイプ: {msg_type}")
        
        except Exception as e:
            self._send_error(player, "PROCESSING_ERROR", f"メッセージ処理エラー: {str(e)}")
    
    def _handle_connect(self, player: TetrisPlayer, data: Dict[str, Any]):
        """接続メッセージを処理"""
        player_name = data.get("player_name", "")
        player.player_name = player_name
        
        # 接続成功を通知
        response = Protocol.create_message(MessageType.CONNECT, {
            "success": True,
            "player_id": player.player_id,
            "server_info": {
                "name": "Tetorisu Server",
                "version": "1.0.0"
            }
        })
        self._send_message_to_player(player, response)
    
    def _handle_create_room(self, player: TetrisPlayer, data: Dict[str, Any]):
        """ルーム作成を処理"""
        room_id = data.get("room_id", "")
        password = data.get("password")
        
        with self.rooms_lock:
            if room_id in self.rooms:
                self._send_error(player, "ROOM_EXISTS", "ルームが既に存在します")
                return
            
            room = TetrisRoom(room_id, password)
            if room.add_player(player):
                self.rooms[room_id] = room
                
                response = Protocol.create_message(MessageType.CREATE_ROOM, {
                    "success": True,
                    "room_id": room_id
                })
                self._send_message_to_player(player, response)
            else:
                self._send_error(player, "ROOM_FULL", "ルームに参加できませんでした")
    
    def _handle_join_room(self, player: TetrisPlayer, data: Dict[str, Any]):
        """ルーム参加を処理"""
        room_id = data.get("room_id", "")
        password = data.get("password")
        
        with self.rooms_lock:
            room = self.rooms.get(room_id)
            if not room:
                self._send_error(player, "ROOM_NOT_FOUND", "ルームが見つかりません")
                return
            
            if room.password and room.password != password:
                self._send_error(player, "INVALID_PASSWORD", "パスワードが間違っています")
                return
            
            if room.is_full():
                self._send_error(player, "ROOM_FULL", "ルームが満員です")
                return
            
            room.add_player(player)
            
            # 参加成功を通知
            response = Protocol.create_message(MessageType.JOIN_ROOM, {
                "success": True,
                "room_id": room_id,
                "players": [p.player_name for p in room.players]
            })
            self._send_message_to_player(player, response)
            
            # 他のプレイヤーに参加を通知
            notification = Protocol.create_message(MessageType.ROOM_INFO, {
                "event": "player_joined",
                "player_name": player.player_name,
                "players": [p.player_name for p in room.players]
            })
            room.broadcast_message(notification, exclude_player=player)
    
    def _handle_leave_room(self, player: TetrisPlayer):
        """ルーム退出を処理"""
        if not player.room_id or not player.room_id.strip():
            return
        
        with self.rooms_lock:
            room = self.rooms.get(player.room_id)
            if room:
                room.remove_player(player)
                
                # 他のプレイヤーに退出を通知
                if not room.is_empty():
                    notification = Protocol.create_message(MessageType.ROOM_INFO, {
                        "event": "player_left",
                        "player_name": player.player_name,
                        "players": [p.player_name for p in room.players]
                    })
                    room.broadcast_message(notification)
                
                # 空のルームを削除
                if room.is_empty() and player.room_id in self.rooms:
                    del self.rooms[player.room_id]
        
        # 退出成功を通知（プレイヤーが接続中の場合のみ）
        if player.connected:
            try:
                response = Protocol.create_message(MessageType.LEAVE_ROOM, {"success": True})
                self._send_message_to_player(player, response)
            except:
                # 送信に失敗した場合は無視（既に切断されている）
                pass
    
    def _handle_player_action(self, player: TetrisPlayer, data: Dict[str, Any]):
        """プレイヤーアクションを処理"""
        if not player.room_id:
            return
        
        with self.rooms_lock:
            room = self.rooms.get(player.room_id)
            if room:
                # アクションを他のプレイヤーに転送
                message = Protocol.create_message(MessageType.PLAYER_ACTION, {
                    "player_id": player.player_id,
                    "player_name": player.player_name,
                    **data
                })
                room.broadcast_message(message, exclude_player=player)
    
    def _handle_game_state(self, player: TetrisPlayer, data: Dict[str, Any]):
        """ゲーム状態を処理"""
        if not player.room_id:
            return
        
        with self.rooms_lock:
            room = self.rooms.get(player.room_id)
            if room:
                # ゲーム状態を他のプレイヤーに転送
                message = Protocol.create_message(MessageType.GAME_STATE, {
                    "player_id": player.player_id,
                    "player_name": player.player_name,
                    **data
                })
                room.broadcast_message(message, exclude_player=player)
    
    def _handle_chat_message(self, player: TetrisPlayer, data: Dict[str, Any]):
        """チャットメッセージを処理"""
        if not player.room_id:
            return
        
        with self.rooms_lock:
            room = self.rooms.get(player.room_id)
            if room:
                # チャットメッセージを他のプレイヤーに転送
                message = Protocol.create_message(MessageType.CHAT_MESSAGE, {
                    "player_id": player.player_id,
                    "player_name": player.player_name,
                    "message": data.get("message", ""),
                    "timestamp": time.time()
                })
                room.broadcast_message(message)
    
    def _handle_disconnect(self, player: TetrisPlayer):
        """切断メッセージを処理"""
        player.connected = False
    
    def _disconnect_player(self, player: TetrisPlayer):
        """プレイヤーを切断"""
        print(f"プレイヤー切断: {player.address} (ID: {player.player_id})")
        
        # ルームから退出
        if player.room_id and player.room_id.strip():
            self._handle_leave_room(player)
        
        # プレイヤーリストから削除
        with self.players_lock:
            if player.player_id in self.players:
                del self.players[player.player_id]
        
        # ソケットを閉じる
        player.connected = False
        try:
            player.socket.close()
        except:
            pass
    
    def _send_error(self, player: TetrisPlayer, error_code: str, error_message: str):
        """エラーメッセージを送信"""
        error_msg = Protocol.create_error_message(error_code, error_message)
        self._send_message_to_player(player, error_msg)
    
    @staticmethod
    def _send_message_to_player(player: TetrisPlayer, message: str):
        """プレイヤーにメッセージを送信"""
        if not player.connected:
            return
        
        try:
            message_bytes = message.encode('utf-8')
            length = len(message_bytes)
            player.socket.sendall(length.to_bytes(4, byteorder='big') + message_bytes)
        except Exception as e:
            player.connected = False
            raise e
    
    @staticmethod
    def _recv_exactly(sock: socket.socket, size: int) -> Optional[bytes]:
        """指定したサイズのデータを確実に受信"""
        data = b''
        while len(data) < size:
            try:
                chunk = sock.recv(size - len(data))
                if not chunk:
                    return None
                data += chunk
            except:
                return None
        return data
    
    def _heartbeat_loop(self):
        """ハートビートループ"""
        while self.running:
            time.sleep(30)  # 30秒間隔
            
            current_time = time.time()
            disconnected_players = []
            
            with self.players_lock:
                for player in self.players.values():
                    if current_time - player.last_heartbeat > 60:  # 60秒タイムアウト
                        disconnected_players.append(player)
            
            # タイムアウトしたプレイヤーを切断
            for player in disconnected_players:
                self._disconnect_player(player)
    
    def _cleanup_loop(self):
        """クリーンアップループ"""
        while self.running:
            time.sleep(300)  # 5分間隔
            
            # 空のルームを削除
            with self.rooms_lock:
                empty_rooms = [room_id for room_id, room in self.rooms.items() if room.is_empty()]
                for room_id in empty_rooms:
                    del self.rooms[room_id]
                    print(f"空のルームを削除: {room_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """サーバー統計を取得"""
        with self.players_lock, self.rooms_lock:
            return {
                "players": len(self.players),
                "rooms": len(self.rooms),
                "total_connections": self.total_connections,
                "uptime": time.time() - self.start_time
            }


# サーバー単体実行用
if __name__ == "__main__":
    server = TetrisServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nサーバーを停止します...")
        server.stop()
