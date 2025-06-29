# 通信プロトコル定義
import json
from enum import Enum
from typing import Dict, Any, Optional


class MessageType(Enum):
    """メッセージタイプの定義"""
    # 接続関連
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    
    # ルーム関連
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    LIST_ROOMS = "list_rooms"
    ROOM_INFO = "room_info"
    
    # ゲーム関連
    GAME_START = "game_start"
    GAME_STATE = "game_state"
    PLAYER_ACTION = "player_action"
    GAME_OVER = "game_over"
    
    # チャット関連
    CHAT_MESSAGE = "chat_message"
    
    # エラー
    ERROR = "error"


class GameAction(Enum):
    """ゲーム内アクションの定義"""
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    ROTATE_CW = "rotate_cw"
    ROTATE_CCW = "rotate_ccw"
    SOFT_DROP = "soft_drop"
    HARD_DROP = "hard_drop"
    HOLD = "hold"
    PLACE_PIECE = "place_piece"


class Protocol:
    """通信プロトコルクラス"""
    
    @staticmethod
    def create_message(msg_type: MessageType, data: Optional[Dict[str, Any]] = None) -> str:
        """メッセージを作成してJSON文字列として返す"""
        message = {
            "type": msg_type.value,
            "timestamp": __import__('time').time(),
            "data": data or {}
        }
        return json.dumps(message)
    
    @staticmethod
    def parse_message(json_str: str) -> Optional[Dict[str, Any]]:
        """JSON文字列をパースしてメッセージ辞書として返す"""
        try:
            message = json.loads(json_str)
            if not isinstance(message, dict) or "type" not in message:
                return None
            return message
        except (json.JSONDecodeError, ValueError):
            return None
    
    @staticmethod
    def create_connect_message(player_name: str) -> str:
        """接続メッセージを作成"""
        return Protocol.create_message(MessageType.CONNECT, {
            "player_name": player_name
        })
    
    @staticmethod
    def create_room_message(room_id: str, password: Optional[str] = None) -> str:
        """ルーム作成メッセージを作成"""
        data = {"room_id": room_id}
        if password:
            data["password"] = password
        return Protocol.create_message(MessageType.CREATE_ROOM, data)
    
    @staticmethod
    def create_join_room_message(room_id: str, password: Optional[str] = None) -> str:
        """ルーム参加メッセージを作成"""
        data = {"room_id": room_id}
        if password:
            data["password"] = password
        return Protocol.create_message(MessageType.JOIN_ROOM, data)
    
    @staticmethod
    def create_action_message(action: GameAction, **kwargs) -> str:
        """ゲームアクションメッセージを作成"""
        return Protocol.create_message(MessageType.PLAYER_ACTION, {
            "action": action.value,
            **kwargs
        })
    
    @staticmethod
    def create_game_state_message(game_state: Dict[str, Any]) -> str:
        """ゲーム状態メッセージを作成"""
        return Protocol.create_message(MessageType.GAME_STATE, game_state)
    
    @staticmethod
    def create_chat_message(message: str) -> str:
        """チャットメッセージを作成"""
        return Protocol.create_message(MessageType.CHAT_MESSAGE, {
            "message": message
        })
    
    @staticmethod
    def create_list_rooms_message() -> str:
        """ルーム一覧取得メッセージを作成"""
        return Protocol.create_message(MessageType.LIST_ROOMS)
    
    @staticmethod
    def create_error_message(error_code: str, error_message: str) -> str:
        """エラーメッセージを作成"""
        return Protocol.create_message(MessageType.ERROR, {
            "error_code": error_code,
            "error_message": error_message
        })
