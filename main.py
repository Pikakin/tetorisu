import pygame
import sys
import config
import key_config
import os

# Pygameの初期化
pygame.init()


def main():
    # スクリーンの初期化
    screen = config.initialize_screen(config.settings.get("fullscreen", False))
    clock = pygame.time.Clock()

    # フォントの初期化
    config.init_fonts()
    print(f"main.py内のconfig.title_font: {config.title_font}")  # Noneでないことを確認

    # サウンドの初期化
    config.init_sounds()

    # キー設定確認
    print("=== キー設定確認 ===")
    current_left = config.settings.get("key_bindings", {}).get(
        "move_left", pygame.K_LEFT
    )
    current_right = config.settings.get("key_bindings", {}).get(
        "move_right", pygame.K_RIGHT
    )
    print(f"現在のキー設定 - 左: {current_left}, 右: {current_right}")
    print("これらは正常なSDL2キーコードです")

    # DAS/ARR用の変数（初期化確認）
    das_timer = 0
    arr_timer = 0
    das_delay = 0.167  # 約10フレーム@60fps
    arr_delay = 0.033  # 約2フレーム@60fps
    last_move_direction = 0

    print(f"DAS/ARR変数初期化完了 - das_delay: {das_delay}, arr_delay: {arr_delay}")

    # キー状態管理（イベント駆動）
    keys_held = {}  # キーが押されている状態を管理

    # ゲーム状態
    game_state = "menu"  # menu, game, pause, game_over, high_scores, settings, online_lobby, online_game
    game = None
    online_lobby = None
    online_game = None

    # 設定のスクロールオフセット
    settings_scroll_offset = 0

    # BGM再生フラグ（ゲーム中のみtrue）
    bgm_playing = False

    # BGMフォルダの確認と作成
    if not os.path.exists("assets/bgm"):
        os.makedirs("assets/bgm")
        print("assets/bgm フォルダを作成しました。BGMファイルを配置してください。")

        # 既存のBGMファイルがある場合は移動
        if os.path.exists("assets/tetris_theme.mp3"):
            import shutil

            try:
                shutil.copy("assets/tetris_theme.mp3", "assets/bgm/tetris_theme.mp3")
                print("既存のBGMファイルを assets/bgm/ に移動しました")
            except Exception as e:
                print(f"BGMファイル移動エラー: {e}")

    # BGM管理の初期化
    import bgm_manager

    bgm_list = bgm_manager.get_bgm_list()
    if bgm_list:
        print(f"利用可能なBGM: {len(bgm_list)}曲")
        # 選択されているBGMが存在するか確認
        current_bgm = config.settings.get("selected_bgm")
        if current_bgm not in bgm_list and bgm_list:
            # 存在しない場合は最初のBGMを選択
            config.settings["selected_bgm"] = bgm_list[0]
            config.save_settings(config.settings)
            print(f"BGMをデフォルトに設定: {bgm_list[0]}")
    else:
        print(
            "BGMが見つかりません。assets/bgmフォルダにMP3, OGG, WAVファイルを追加してください。"
        )

    # BGMの再生（設定がONの場合）
    if config.has_music and config.settings.get("music", True):
        pygame.mixer.music.play(-1)  # 無限ループ

    # ヘルパー関数
    def set_game_state(new_state):
        nonlocal game_state, online_lobby, online_game
        if new_state == "menu":
            if online_lobby:
                online_lobby.disconnect()
                online_lobby = None
            if online_game:
                online_game = None
        game_state = new_state
    
    def start_online_game(client):
        nonlocal online_game, game_state
        print("start_online_game関数が呼ばれました")
        from online_game import OnlineGame
        online_game = OnlineGame(config.screen_width, config.screen_height, client)
        online_game.start_game()
        print(f"ゲーム状態を変更: {game_state} -> online_game")
        game_state = "online_game"

    # メインゲームループ
    while True:
        dt = clock.tick(60) / 1000.0  # フレーム間の時間（秒）

        # マウス位置の取得
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        # イベント処理
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                # キー状態を記録
                keys_held[event.key] = True

                # ESCキーでメニューまたは一時停止
                if event.key == pygame.K_ESCAPE:
                    if game_state == "game":
                        game_state = "pause"
                    elif game_state == "pause":
                        game_state = "game"
                    elif game_state == "high_scores" or game_state == "settings":
                        game_state = "menu"

                # ゲームプレイ中のキー操作
                if game_state == "game" and game:
                    key_bindings = config.settings.get("key_bindings", {})

                    # 左右移動（初回移動 + DAS/ARRタイマー開始）
                    if event.key == key_bindings.get("move_left", pygame.K_LEFT):
                        game.move(-1)
                        # DAS/ARRタイマーを初期化
                        das_timer = 0
                        arr_timer = 0
                        last_move_direction = -1
                    elif event.key == key_bindings.get("move_right", pygame.K_RIGHT):
                        game.move(1)
                        # DAS/ARRタイマーを初期化
                        das_timer = 0
                        arr_timer = 0
                        last_move_direction = 1

                    # 時計回りの回転
                    elif event.key == key_bindings.get("rotate_cw", pygame.K_UP):
                        game.rotate(clockwise=True)

                    # 反時計回りの回転
                    elif event.key == key_bindings.get("rotate_ccw", pygame.K_z):
                        game.rotate(clockwise=False)

                    # ハードドロップ
                    elif event.key == key_bindings.get("hard_drop", pygame.K_SPACE):
                        game.drop()

                    # ホールド
                    elif event.key == key_bindings.get("hold", pygame.K_c):
                        game.hold_piece()

                    # 一時停止
                    elif event.key == key_bindings.get("pause", pygame.K_p):
                        game_state = "pause"

                # 設定画面でのスクロール
                if game_state == "settings":
                    if event.key == pygame.K_UP:
                        settings_scroll_offset += 50 * config.scale_factor
                    elif event.key == pygame.K_DOWN:
                        settings_scroll_offset -= 50 * config.scale_factor

                    # スクロール範囲の制限
                    settings_scroll_offset = max(min(settings_scroll_offset, 0), -400)

            elif event.type == pygame.KEYUP:
                # キー状態を記録
                keys_held[event.key] = False

                # ソフトドロップの解除
                if game_state == "game" and game:
                    if event.key == config.settings.get("key_bindings", {}).get(
                        "soft_drop", pygame.K_DOWN
                    ):
                        game.soft_drop = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    mouse_clicked = True

                # 設定画面でのマウスホイールスクロール
                elif event.button == 4 and game_state == "settings":  # マウスホイール上
                    settings_scroll_offset += 30 * config.scale_factor
                    settings_scroll_offset = min(settings_scroll_offset, 0)
                elif event.button == 5 and game_state == "settings":  # マウスホイール下
                    settings_scroll_offset -= 30 * config.scale_factor
                    settings_scroll_offset = max(settings_scroll_offset, -400)

        # DAS/ARR処理（修正版）
        if game_state == "game" and game:
            # ソフトドロップ
            soft_drop_key = config.settings.get("key_bindings", {}).get(
                "soft_drop", pygame.K_DOWN
            )
            game.soft_drop = keys_held.get(soft_drop_key, False)

            # DAS/ARR処理
            move_left_key = config.settings.get("key_bindings", {}).get(
                "move_left", pygame.K_LEFT
            )
            move_right_key = config.settings.get("key_bindings", {}).get(
                "move_right", pygame.K_RIGHT
            )

            left_pressed = keys_held.get(move_left_key, False)
            right_pressed = keys_held.get(move_right_key, False)

            # 現在の方向を決定
            current_direction = 0

            if left_pressed and right_pressed:
                # 同時押し時は何もしない（ニュートラル）
                current_direction = 0
            elif left_pressed:
                current_direction = -1
            elif right_pressed:
                current_direction = 1

            if current_direction != 0:
                # 方向が変わった場合のみタイマーリセット
                if last_move_direction != current_direction:
                    das_timer = 0
                    arr_timer = 0
                    last_move_direction = current_direction

                # DASタイマーを進める
                das_timer += dt

                # DAS完了後の高速移動
                if das_timer >= das_delay:
                    arr_timer += dt

                    # ARRの間隔で移動
                    if arr_timer >= arr_delay:
                        game.move(current_direction)
                        arr_timer = 0
            else:
                # キーが押されていない場合はリセット
                das_timer = 0
                arr_timer = 0
                last_move_direction = 0

        # 画面の描画
        if game_state == "menu":
            from ui import draw_start_menu

            pygame.mixer.music.stop()
            bgm_playing = False

            buttons = draw_start_menu(screen)

            # ボタンのクリック処理
            if mouse_clicked:
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        action = button.action
                        if action == "start":
                            print("ゲーム開始処理を実行します")
                            # ゲーム開始
                            from game import Tetris

                            game_mode = config.settings.get("game_mode", "marathon")
                            game = Tetris(game_mode=game_mode)
                            game_state = "game"

                            # BGMの再生（設定がONの場合）
                            print(
                                f"has_music: {config.has_music}, music設定: {config.settings.get('music', True)}"
                            )
                            # BGMの再生（設定がONの場合）
                            if config.has_music and config.settings.get("music", True):
                                import bgm_manager

                                bgm_manager.play_bgm()

                        # メニューに戻る処理でBGMを停止
                        elif (
                            action == "menu"
                            or action == "quit"
                            and game_state == "game"
                        ):
                            # メニューに戻る際にBGMを停止
                            if config.has_music:
                                pygame.mixer.music.stop()
                            game_state = "menu"

                        elif action == "game_mode":
                            # ゲームモードの切り替え
                            modes = ["marathon", "sprint", "ultra"]
                            current_mode = config.settings.get("game_mode", "marathon")
                            next_index = (modes.index(current_mode) + 1) % len(modes)
                            config.settings["game_mode"] = modes[next_index]
                            config.save_settings(config.settings)
                        elif action == "online":
                            # オンライン対戦画面へ
                            from lobby import OnlineLobby
                            online_lobby = OnlineLobby(config.screen_width, config.screen_height)
                            online_lobby.on_back_to_menu = lambda: set_game_state("menu")
                            online_lobby.on_game_start = start_online_game
                            game_state = "online_lobby"
                        elif action == "settings":
                            # 設定画面へ
                            game_state = "settings"
                            settings_scroll_offset = 0
                        elif action == "theme":
                            # テーマの切り替えと即時反映
                            new_theme = config.cycle_theme()
                            print(f"テーマ変更: {new_theme}")
                            # 画面を即座に再描画（次のフレームで反映）
                            config.need_redraw_menus = True
                        elif action == "high_scores":
                            # ハイスコア画面へ
                            game_state = "high_scores"
                        elif action == "quit":
                            # ゲーム終了
                            pygame.quit()
                            sys.exit()

        elif game_state == "game":

            if game:
                # ゲームの更新
                game.update(dt)

                # ゲーム画面の描画
                buttons = game.draw(screen)

                # ゲームオーバーまたはゲームクリア時のボタン処理
                if buttons and mouse_clicked:
                    for button in buttons:
                        if button.rect.collidepoint(mouse_pos):
                            if button.action == "retry":
                                # リトライ
                                game_mode = config.settings.get("game_mode", "marathon")
                                game = Tetris(game_mode=game_mode)
                            elif button.action == "menu":
                                # メニューに戻る
                                if config.has_music:
                                    pygame.mixer.music.stop()
                                game_state = "menu"
                                game = None

        elif game_state == "pause":
            if game:
                # ポーズメニューの描画
                buttons = game.draw_pause_menu(screen)

                # ボタンのクリック処理
                if mouse_clicked:
                    for button in buttons:
                        if button.rect.collidepoint(mouse_pos):
                            if button.action == "resume":
                                game_state = "game"
                            elif button.action == "theme":
                                new_theme = config.cycle_theme()
                                print(f"ポーズメニューでテーマ変更: {new_theme}")
                                # ゲーム画面も即座に更新
                                if game:
                                    # ゲーム内のパーティクルシステムのテーマも更新
                                    game.particle_system.set_effect_type(
                                        config.settings.get("effect_type", "default")
                                    )
                            elif button.action == "fullscreen":
                                screen = config.toggle_fullscreen()
                            elif button.action == "quit":
                                if config.has_music:
                                    pygame.mixer.music.stop()
                                game_state = "menu"
                                game = None

        elif game_state == "high_scores":
            from ui import draw_high_scores_screen

            buttons = draw_high_scores_screen(screen)

            # ボタンのクリック処理
            if mouse_clicked:
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        if button.action == "back":
                            game_state = "menu"

        elif game_state == "settings":
            from ui import draw_settings_menu

            buttons = draw_settings_menu(screen, settings_scroll_offset)

            # ボタンのクリック処理
            if mouse_clicked:
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        action = button.action

                        if action == "back":
                            game_state = "menu"
                        elif action == "bgm_selection":
                            # BGM選択画面を実行
                            import bgm_manager

                            bgm_manager.run_bgm_selection(screen)
                        elif action == "key_config":
                            # キー設定画面を実行
                            key_config.run_key_config(screen)
                        elif action.startswith("toggle_"):
                            # 設定のトグル
                            setting_key = action[7:]  # "toggle_"を除去
                            if setting_key in config.settings:
                                config.settings[setting_key] = not config.settings[
                                    setting_key
                                ]
                                config.save_settings(config.settings)
                        elif action.startswith("cycle_"):
                            # 設定の循環
                            setting_key = action[6:]  # "cycle_"を除去
                            if setting_key == "theme":
                                new_theme = config.cycle_theme()
                                print(f"設定画面でテーマ変更: {new_theme}")
                                # 設定画面を即座に再描画
                                config.need_redraw_menus = True
                            elif setting_key == "effect_type":
                                # エフェクトタイプの循環
                                effect_types = [
                                    "default",
                                    "explosion",
                                    "rain",
                                    "spiral",
                                ]
                                current_type = config.settings.get(
                                    "effect_type", "default"
                                )
                                next_index = (
                                    effect_types.index(current_type) + 1
                                ) % len(effect_types)
                                config.settings["effect_type"] = effect_types[
                                    next_index
                                ]
                                config.save_settings(config.settings)

        elif game_state == "bgm_selection":
            import bgm_manager

            buttons, total_height, visible_height = bgm_manager.draw_bgm_selection(
                screen, bgm_scroll_offset
            )

            # ボタンのクリック処理
            if mouse_clicked:
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        if button.action == "back":
                            game_state = "settings"
                        elif button.action == "preview":
                            # プレビュー再生/停止
                            if pygame.mixer.music.get_busy():
                                bgm_manager.stop_bgm()
                            else:
                                bgm_manager.play_bgm()
                        elif button.action.startswith("bgm:"):
                            # BGM選択
                            bgm_file = button.action[4:]  # "bgm:"を除いた部分
                            bgm_manager.change_bgm(bgm_file)
                            # プレビュー再生
                            bgm_manager.play_bgm()

        elif game_state == "online_lobby":
            if online_lobby:
                # オンラインロビーの更新
                online_lobby.update(events, mouse_pos)
                
                # オンラインロビーの描画
                online_lobby.draw(screen)

        elif game_state == "online_game":
            if online_game:
                # オンラインゲームの更新
                online_game.update(events, keys_held, dt)
                
                # オンラインゲームからの退出チェック
                if hasattr(online_game, 'should_exit') and online_game.should_exit:
                    game_state = "online_lobby"
                    online_game = None
                else:
                    # オンラインゲームの描画
                    online_game.draw(screen)

        # 画面の更新
        pygame.display.flip()

    # ゲーム終了時の処理
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        pygame.quit()
        sys.exit()
