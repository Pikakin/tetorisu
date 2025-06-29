#!/usr/bin/env python3
# テトリスサーバー起動スクリプト
import sys
import signal
from network.server import TetrisServer


def signal_handler(signum, frame):
    """シグナルハンドラー（Ctrl+C対応）"""
    print("\nサーバーを停止しています...")
    if hasattr(signal_handler, 'server'):
        signal_handler.server.stop()
    sys.exit(0)


def main():
    # デフォルトのホストとポート
    host = "localhost"
    port = 12345
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("ポート番号は数値で指定してください")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    print(f"テトリスサーバーを起動します...")
    print(f"ホスト: {host}")
    print(f"ポート: {port}")
    print("Ctrl+C で停止")
    print("-" * 40)
    
    # サーバーインスタンスを作成
    server = TetrisServer(host, port)
    signal_handler.server = server
    
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # サーバー開始
        if server.start():
            print("サーバーが正常に開始されました")
        else:
            print("サーバーの開始に失敗しました")
            sys.exit(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"サーバーエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
