# クライアント側通信
import socket
import threading
import json
import time
from typing import Callable, Optional, Dict, Any
from network.protocol import Protocol, MessageType, GameAction


class TetrisClient:
    """テトリスクライアント通信クラス"""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.player_name = ""
        self.room_id = ""
        
        # コールバック関数
        self.on_message_received: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str, str], None]] = None
        
        # 受信スレッド
        self.receive_thread: Optional[threading.Thread] = None
        self.running = False
    
    def connect(self, host: str, port: int, player_name: str) -> bool:
        """サーバーに接続"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)  # 10秒タイムアウト
            self.socket.connect((host, port))
            
            self.player_name = player_name
            self.connected = True
            self.running = True
            
            # 接続メッセージを送信
            connect_msg = Protocol.create_connect_message(player_name)
            self._send_message(connect_msg)
            
            # 受信スレッドを開始
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            if self.on_connected:
                self.on_connected()
            
            return True
            
        except Exception as e:
            self.connected = False
            if self.on_error:
                self.on_error("CONNECTION_ERROR", f"接続エラー: {str(e)}")
            return False
    
    def disconnect(self):
        """サーバーから切断"""
        if self.connected:
            try:
                # 切断メッセージを送信
                disconnect_msg = Protocol.create_message(MessageType.DISCONNECT)
                self._send_message(disconnect_msg)
            except:
                pass
        
        self._close_connection()
    
    def create_room(self, room_id: str, password: Optional[str] = None) -> bool:
        """ルームを作成"""
        if not self.connected:
            return False
        
        try:
            message = Protocol.create_room_message(room_id, password)
            self._send_message(message)
            return True
        except Exception as e:
            if self.on_error:
                self.on_error("ROOM_ERROR", f"ルーム作成エラー: {str(e)}")
            return False
    
    def join_room(self, room_id: str, password: Optional[str] = None) -> bool:
        """ルームに参加"""
        if not self.connected:
            return False
        
        try:
            message = Protocol.create_join_room_message(room_id, password)
            self._send_message(message)
            return True
        except Exception as e:
            if self.on_error:
                self.on_error("ROOM_ERROR", f"ルーム参加エラー: {str(e)}")
            return False
    
    def leave_room(self) -> bool:
        """ルームから退出"""
        if not self.connected:
            return False
        
        try:
            message = Protocol.create_message(MessageType.LEAVE_ROOM)
            self._send_message(message)
            self.room_id = ""
            return True
        except Exception as e:
            if self.on_error:
                self.on_error("ROOM_ERROR", f"ルーム退出エラー: {str(e)}")
            return False
    
    def send_game_action(self, action: GameAction, **kwargs) -> bool:
        """ゲームアクションを送信"""
        if not self.connected:
            return False
        
        try:
            message = Protocol.create_action_message(action, **kwargs)
            self._send_message(message)
            return True
        except Exception as e:
            if self.on_error:
                self.on_error("GAME_ERROR", f"アクション送信エラー: {str(e)}")
            return False
    
    def send_game_state(self, game_state: Dict[str, Any]) -> bool:
        """ゲーム状態を送信"""
        if not self.connected:
            return False
        
        try:
            message = Protocol.create_game_state_message(game_state)
            self._send_message(message)
            return True
        except Exception as e:
            if self.on_error:
                self.on_error("GAME_ERROR", f"ゲーム状態送信エラー: {str(e)}")
            return False
    
    def send_chat_message(self, message: str) -> bool:
        """チャットメッセージを送信"""
        if not self.connected:
            return False
        
        try:
            chat_msg = Protocol.create_chat_message(message)
            self._send_message(chat_msg)
            return True
        except Exception as e:
            if self.on_error:
                self.on_error("CHAT_ERROR", f"チャット送信エラー: {str(e)}")
            return False
    
    def _send_message(self, message: str):
        """メッセージを送信（内部用）"""
        if self.socket and self.connected:
            try:
                # メッセージ長を先頭に付けて送信
                message_bytes = message.encode('utf-8')
                length = len(message_bytes)
                self.socket.sendall(length.to_bytes(4, byteorder='big') + message_bytes)
            except Exception as e:
                self._handle_connection_error(f"送信エラー: {str(e)}")
    
    def _receive_loop(self):
        """受信ループ（別スレッドで実行）"""
        while self.running and self.connected:
            try:
                # メッセージ長を受信
                length_bytes = self._recv_exactly(4)
                if not length_bytes:
                    break
                
                message_length = int.from_bytes(length_bytes, byteorder='big')
                if message_length <= 0 or message_length > 1024 * 1024:  # 1MBまで
                    break
                
                # メッセージ本体を受信
                message_bytes = self._recv_exactly(message_length)
                if not message_bytes:
                    break
                
                message_str = message_bytes.decode('utf-8')
                message_data = Protocol.parse_message(message_str)
                
                if message_data and self.on_message_received:
                    self.on_message_received(message_data)
                
            except Exception as e:
                if self.running:  # 正常終了時はエラーを報告しない
                    self._handle_connection_error(f"受信エラー: {str(e)}")
                break
        
        self._close_connection()
    
    def _recv_exactly(self, size: int) -> Optional[bytes]:
        """指定したサイズのデータを確実に受信"""
        data = b''
        while len(data) < size:
            try:
                chunk = self.socket.recv(size - len(data))
                if not chunk:
                    return None
                data += chunk
            except:
                return None
        return data
    
    def _handle_connection_error(self, error_message: str):
        """接続エラーを処理"""
        if self.on_error:
            self.on_error("CONNECTION_ERROR", error_message)
        self._close_connection()
    
    def _close_connection(self):
        """接続を閉じる"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.on_disconnected:
            self.on_disconnected("接続が切断されました")
    
    def is_connected(self) -> bool:
        """接続状態を取得"""
        return self.connected
    
    def get_player_name(self) -> str:
        """プレイヤー名を取得"""
        return self.player_name
    
    def get_room_id(self) -> str:
        """現在のルームIDを取得"""
        return self.room_id
