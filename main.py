import pygame
import sys
import config
import key_config

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

    # ゲーム状態
    game_state = "menu"  # menu, game, pause, game_over, high_scores, settings
    game = None

    # 設定のスクロールオフセット
    settings_scroll_offset = 0

    # BGM再生フラグ（ゲーム中のみtrue）
    bgm_playing = False

    # BGMの再生（設定がONの場合）
    if config.has_music and config.settings.get("music", True):
        pygame.mixer.music.play(-1)  # 無限ループ

    # メインゲームループ
    while True:
        dt = clock.tick(60) / 1000.0  # フレーム間の時間（秒）

        # マウス位置の取得
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
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

                    # 左移動
                    if event.key == key_bindings.get("move_left", pygame.K_LEFT):
                        game.move(-1)

                    # 右移動
                    elif event.key == key_bindings.get("move_right", pygame.K_RIGHT):
                        game.move(1)

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

        # キー長押し処理（ソフトドロップ）
        keys = pygame.key.get_pressed()
        if game_state == "game" and game:
            soft_drop_key = config.settings.get("key_bindings", {}).get(
                "soft_drop", pygame.K_DOWN
            )
            game.soft_drop = keys[soft_drop_key]

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
                            if config.has_music and config.settings.get("music", True):
                                try:
                                    print("BGMを読み込み中: assets/tetris_theme.mp3")
                                    pygame.mixer.music.load("assets/tetris_theme.mp3")
                                    pygame.mixer.music.set_volume(0.5)  # 音量を確認
                                    pygame.mixer.music.play(-1)  # 無限ループで再生
                                    print("BGM再生開始")
                                except Exception as e:
                                    print(f"BGM再生エラー: {e}")

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
                        elif action == "settings":
                            # 設定画面へ
                            game_state = "settings"
                            settings_scroll_offset = 0
                        elif action == "theme":
                            # テーマの切り替え
                            config.cycle_theme()
                        elif action == "high_scores":
                            # ハイスコア画面へ
                            game_state = "high_scores"
                        elif action == "quit":
                            # ゲーム終了
                            pygame.quit()
                            sys.exit()

        elif game_state == "game":
            # ゲームの更新
            game.update(dt)

            # ゲーム画面の描画
            buttons = game.draw(screen)

            # ゲームオーバーまたはゲームクリア時のボタン処理
            if buttons and mouse_clicked:
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        action = button.action
                        if action == "retry":
                            # リトライ
                            from game import Tetris

                            game_mode = game.game_mode
                            game = Tetris(game_mode=game_mode)
                        elif action == "menu":
                            # メニューに戻る
                            game_state = "menu"

        elif game_state == "pause":
            # ゲーム画面を描画
            game.draw(screen)

            # ポーズメニューの描画
            from ui import draw_pause_menu

            buttons = draw_pause_menu(screen)

            # ボタンのクリック処理
            if mouse_clicked:
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        action = button.action
                        if action == "resume":
                            # ゲーム再開時にBGMも再開
                            game_state = "game"
                            if config.has_music and config.settings.get("music", True):
                                pygame.mixer.music.unpause()
                        elif action == "theme":
                            # テーマの切り替え
                            config.cycle_theme()
                        elif action == "fullscreen":
                            # フルスクリーン切り替え
                            screen = config.toggle_fullscreen()
                            # 存在する場合は、ゲームオブジェクトも更新
                            if game:
                                game.update_screen_values(
                                    config.screen_width,
                                    config.screen_height,
                                    config.grid_x,
                                    config.grid_y,
                                    config.scale_factor,
                                )

                        elif action == "quit":
                            # メニューに戻る際にBGMを停止
                            if config.has_music:
                                pygame.mixer.music.stop()
                            game_state = "menu"

        elif game_state == "high_scores":
            # ハイスコア画面の描画
            from ui import draw_high_scores
            from game import Tetris

            buttons = draw_high_scores(screen, game if game else Tetris())

            # ボタンのクリック処理
            if mouse_clicked:
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        action = button.action
                        if action == "back":
                            # メニューに戻る
                            game_state = "menu"
                        # モード切替のクリック処理
                        elif action in ["marathon", "sprint", "ultra"]:
                            if game:
                                game.game_mode = action
                            else:
                                game = Tetris(game_mode=action)

        elif game_state == "settings":
            # 設定画面の描画
            from ui import draw_settings_menu

            buttons = draw_settings_menu(screen, settings_scroll_offset)

            # ボタンのクリック処理
            if mouse_clicked:
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        action = button.action
                        if action == "back":
                            # メニューに戻る
                            game_state = "menu"
                        elif action == "effects":
                            # エフェクト切替
                            config.settings["effects"] = not config.settings.get(
                                "effects", True
                            )
                            config.save_settings(config.settings)
                        elif action == "effect_type":
                            # エフェクトタイプ切替
                            effect_types = ["default", "explosion", "rain", "spiral"]
                            current_type = config.settings.get("effect_type", "default")
                            next_index = (effect_types.index(current_type) + 1) % len(
                                effect_types
                            )
                            config.settings["effect_type"] = effect_types[next_index]
                            config.save_settings(config.settings)
                            # 現在のゲームにも反映
                            if game:
                                game.particle_system.set_effect_type(
                                    config.settings["effect_type"]
                                )
                        elif action == "music":
                            # 音楽切替
                            config.settings["music"] = not config.settings.get(
                                "music", True
                            )
                            config.save_settings(config.settings)
                            # 音楽の再生/停止
                            if config.has_music:
                                if config.settings["music"]:
                                    pygame.mixer.music.play(-1)
                                else:
                                    pygame.mixer.music.stop()
                        elif action == "sound":
                            # 効果音切替
                            config.settings["sound"] = not config.settings.get(
                                "sound", True
                            )
                            config.save_settings(config.settings)
                        elif action == "ghost_piece":
                            # ゴーストピース切替
                            config.settings["ghost_piece"] = not config.settings.get(
                                "ghost_piece", True
                            )
                            config.save_settings(config.settings)
                        # 既存の設定メニュー処理部分に追加
                        elif action == "key_config":
                            # キー設定画面に移動
                            key_config.load_key_settings()  # 現在の設定を読み込み
                            key_config.run_key_config(screen)
                            game_state = "settings"  # 設定メニューに戻る
                        elif action == "reset_high_scores":
                            # ハイスコアをリセット
                            reset_high_scores()
                            # ハイスコア画面に戻る
                            game_state = "high_scores"
                        elif action == "reset_settings":
                            # 設定をリセット
                            config.reset_settings()
                            # 設定画面に戻る
                            game_state = "settings"
                        elif action == "reset_key_settings":
                            # キー設定をリセット
                            key_config.reset_key_settings()
                            # 設定画面に戻る
                            game_state = "settings"
                        elif action == "reset_all":
                            # 設定、ハイスコア、キー設定をリセット
                            reset_high_scores()
                            config.reset_settings()
                            key_config.reset_key_settings()
                            # メニューに戻
                        elif action == "fullscreen":
                            # フルスクリーン切替して返された新しいスクリーンを使用
                            screen = config.toggle_fullscreen()

                            # 存在する場合は、ゲームオブジェクトも更新
                            if game:
                                game.update_screen_values(
                                    config.screen_width,
                                    config.screen_height,
                                    config.grid_x,
                                    config.grid_y,
                                    config.scale_factor,
                                )

        # 画面の更新
        pygame.display.flip()


if __name__ == "__main__":
    main()
