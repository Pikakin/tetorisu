# UDP クライアント実装
import socket
import threading
import json
import time
from typing import Callable, Optional, Dict, Any
from network.protocol import Protocol, MessageType, GameAction


class UDPTetrisClient:
    """テトリス UDP クライアント通信クラス"""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.server_addr: Optional[tuple] = None
        self.connected = False
        self.player_name = ""
        self.player_id = ""
        self.room_id = ""
        
        # シーケンス番号（パケットの順序管理用）
        self.sequence = 0
        
        # コールバック関数
        self.on_message_received: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str, str], None]] = None
        
        # 受信スレッド
        self.receive_thread: Optional[threading.Thread] = None
        self.running = False
        
        # ハートビート
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.last_heartbeat = time.time()
    
    def connect(self, host: str, port: int, player_name: str) -> bool:
        """UDPサーバーに接続"""
        print(f"UDP接続開始: {host}:{port}, player={player_name}")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(5.0)  # 5秒タイムアウト
            # localhostを127.0.0.1に解決
            if host == "localhost":
                host = "127.0.0.1"
            self.server_addr = (host, port)
            print(f"UDPソケット作成完了: {self.server_addr}")
            
            self.player_name = player_name
            self.connected = True
            self.running = True
            
            # 接続メッセージを送信
            connect_msg = Protocol.create_connect_message(player_name)
            print(f"接続メッセージ送信: {connect_msg}")
            self._send_message(connect_msg)
            
            # 受信スレッドを開始
            print("受信スレッド開始...")
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            # ハートビートスレッドを開始
            print("ハートビートスレッド開始...")
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            print(f"コールバック実行...on_connected={self.on_connected is not None}")
            if self.on_connected:
                self.on_connected()
            
            print("UDP接続完了")
            return True
            
        except Exception as e:
            self.connected = False
            if self.on_error:
                self.on_error("CONNECTION_ERROR", f"UDP接続エラー: {str(e)}")
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
        print(f"UDPクライアント: create_room実行 room_id={room_id}, connected={self.connected}")
        if not self.connected:
            print("UDPクライアント: 接続されていないため作成失敗")
            return False
        
        try:
            message = Protocol.create_room_message(room_id, password)
            print(f"UDPクライアント: ルーム作成メッセージ送信 {message}")
            self._send_message(message)
            return True
        except Exception as e:
            print(f"UDPクライアント: ルーム作成エラー {str(e)}")
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
    
    def list_rooms(self) -> bool:
        """ルーム一覧を取得"""
        if not self.connected:
            return False
        
        try:
            message = Protocol.create_list_rooms_message()
            self._send_message(message)
            return True
        except Exception as e:
            if self.on_error:
                self.on_error("ROOM_ERROR", f"ルーム一覧取得エラー: {str(e)}")
            return False
    
    def send_game_action(self, action: GameAction, **kwargs) -> bool:
        """ゲームアクションを送信（高頻度・低遅延）"""
        if not self.connected:
            return False
        
        try:
            message = Protocol.create_action_message(action, **kwargs)
            self._send_message_fast(message)  # 高速送信
            return True
        except Exception as e:
            if self.on_error:
                self.on_error("GAME_ERROR", f"アクション送信エラー: {str(e)}")
            return False
    
    def send_game_state(self, game_state: Dict[str, Any]) -> bool:
        """ゲーム状態を送信（高頻度・低遅延）"""
        if not self.connected:
            return False
        
        try:
            message = Protocol.create_game_state_message(game_state)
            self._send_message_fast(message)  # 高速送信
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
    
    def _send_message(self, message_str: str):
        """メッセージを送信（通常版）"""
        if self.socket and self.connected and self.server_addr:
            try:
                # JSONパース
                message_dict = json.loads(message_str)
                
                # シーケンス番号を追加
                self.sequence += 1
                message_dict['sequence'] = self.sequence
                message_dict['player_id'] = self.player_id
                
                # 再エンコード
                message_bytes = json.dumps(message_dict).encode('utf-8')
                
                self.socket.sendto(message_bytes, self.server_addr)
                
            except Exception as e:
                self._handle_connection_error(f"送信エラー: {str(e)}")
    
    def _send_message_fast(self, message_str: str):
        """メッセージを高速送信（ゲーム用・エラーハンドリング最小）"""
        if self.socket and self.connected and self.server_addr:
            try:
                message_dict = json.loads(message_str)
                self.sequence += 1
                message_dict['sequence'] = self.sequence
                message_dict['player_id'] = self.player_id
                
                message_bytes = json.dumps(message_dict).encode('utf-8')
                self.socket.sendto(message_bytes, self.server_addr)
                
            except:
                # ゲーム用なのでエラーは無視（遅延を避けるため）
                pass
    
    def _receive_loop(self):
        """受信ループ（別スレッドで実行）"""
        print("受信ループが開始されました")
        while self.running and self.connected:
            try:
                data, addr = self.socket.recvfrom(4096)  # 4KB受信
                print(f"パケット受信: from {addr}, expected {self.server_addr}")
                
                if addr != self.server_addr:
                    print(f"アドレス不一致: {addr} != {self.server_addr}")
                    continue  # 不正なアドレスからのパケットは無視
                
                message_str = data.decode('utf-8')
                print(f"UDPクライアント受信: {message_str}")
                message_data = Protocol.parse_message(message_str)
                
                if message_data and self.on_message_received:
                    print(f"コールバック実行: {message_data.get('type')}")
                    self.on_message_received(message_data)
                else:
                    print(f"コールバック実行されず: message_data={message_data is not None}, callback={self.on_message_received is not None}")
                
                self.last_heartbeat = time.time()
                
            except socket.timeout:
                # タイムアウトは正常（ハートビートで生存確認）
                continue
            except Exception as e:
                if self.running:
                    self._handle_connection_error(f"受信エラー: {str(e)}")
                break
        
        self._close_connection()
    
    def _heartbeat_loop(self):
        """ハートビートループ"""
        while self.running and self.connected:
            try:
                # 30秒間隔でハートビート送信
                time.sleep(30)
                
                if self.connected:
                    heartbeat_msg = Protocol.create_message(MessageType.HEARTBEAT)
                    self._send_message_fast(heartbeat_msg)
                
                # 90秒間応答がない場合はタイムアウト
                if time.time() - self.last_heartbeat > 90:
                    self._handle_connection_error("サーバーからの応答がありません")
                    break
                    
            except Exception as e:
                if self.running:
                    self._handle_connection_error(f"ハートビートエラー: {str(e)}")
                break
    
    def _handle_connection_error(self, error_message: str):
        """接続エラーを処理"""
        print(f"UDPクライアント接続エラー: {error_message}")
        if self.on_error:
            self.on_error("CONNECTION_ERROR", error_message)
        self._close_connection()
    
    def _close_connection(self):
        """接続を閉じる"""
        print("UDPクライアント: 接続を閉じています")
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
    
    def get_latency_info(self) -> Dict[str, Any]:
        """レイテンシ情報を取得（UDP版では簡易実装）"""
        return {
            "connected": self.connected,
            "last_heartbeat": self.last_heartbeat,
            "sequence": self.sequence,
            "protocol": "UDP"
        }
