import os
import pygame
import json
import config

# サポートする音楽ファイル形式
SUPPORTED_FORMATS = [".mp3", ".ogg", ".wav"]


# BGMを停止する関数
def stop_bgm():
    if config.has_music:
        pygame.mixer.music.stop()
        print("BGM停止")


# BGMがポーズ状態か確認
def is_paused():
    return pygame.mixer.music.get_busy() == 0 and config.has_music


# BGMリストを取得する関数
def get_bgm_list():
    bgm_list = []
    bgm_dir = "assets/bgm"

    # フォルダが存在しなければ作成
    if not os.path.exists(bgm_dir):
        os.makedirs(bgm_dir)
        print(f"{bgm_dir} フォルダを作成しました")
        return bgm_list

    # フォルダ内のファイルをスキャン
    for file in os.listdir(bgm_dir):
        # 拡張子をチェック
        file_ext = os.path.splitext(file)[1].lower()
        if file_ext in SUPPORTED_FORMATS:
            bgm_list.append(file)

    return bgm_list


# 現在選択されているBGMを取得
def get_current_bgm():
    return config.settings.get("selected_bgm", "tetris_theme.mp3")


# BGMを変更する関数
def change_bgm(bgm_file):
    # 設定を更新
    config.settings["selected_bgm"] = bgm_file
    config.save_settings(config.settings)

    # 現在再生中の場合は、新しいBGMに切り替え
    if pygame.mixer.music.get_busy() and config.has_music:
        play_bgm()


# BGMを再生する関数
def play_bgm():
    if not config.has_music:
        return

    try:
        # 現在のBGMを取得
        bgm_file = get_current_bgm()
        bgm_path = os.path.join("assets", "bgm", bgm_file)

        # BGMが存在するか確認
        if not os.path.exists(bgm_path):
            # 存在しない場合はデフォルトに戻す
            default_bgm = get_first_available_bgm()
            if default_bgm:
                config.settings["selected_bgm"] = default_bgm
                config.save_settings(config.settings)
                bgm_path = os.path.join("assets", "bgm", default_bgm)
            else:
                print("利用可能なBGMがありません")
                return

        # BGMを読み込んで再生
        pygame.mixer.music.load(bgm_path)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)  # ループ再生
        print(f"BGM再生: {bgm_file}")
    except Exception as e:
        print(f"BGM再生エラー: {e}")


# 最初に見つかった利用可能なBGMを返す
def get_first_available_bgm():
    bgm_list = get_bgm_list()
    return bgm_list[0] if bgm_list else None


# BGM選択画面を描画
def draw_bgm_selection(screen, scroll_offset=0):
    # 循環インポートを避けるため、ここでインポート
    from ui import Button

    # 背景
    screen.fill(config.theme["background"])

    # 画面サイズ取得
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    # パネルの寸法と位置
    panel_width = 600 * config.scale_factor
    panel_height = 500 * config.scale_factor
    panel_x = screen_width // 2 - panel_width // 2
    panel_y = screen_height // 2 - panel_height // 2

    # パネル描画
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((45, 45, 45, 250))

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(8 * config.scale_factor)
    pygame.draw.rect(panel, (50, 50, 50, 255), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel, (70, 70, 70), panel_rect, width=1, border_radius=corner_radius
    )

    screen.blit(panel, (panel_x, panel_y))

    # タイトル
    title_text = config.title_font.render("BGM選択", True, config.theme["text"])
    screen.blit(
        title_text,
        (
            screen_width // 2 - title_text.get_width() // 2,
            panel_y + 20 * config.scale_factor,
        ),
    )

    # BGMリストの取得
    bgm_list = get_bgm_list()
    current_bgm = get_current_bgm()

    # BGMが見つからない場合のメッセージ
    if not bgm_list:
        no_bgm_text = config.font.render(
            "BGMファイルが見つかりません", True, config.theme["text"]
        )
        screen.blit(
            no_bgm_text,
            (
                screen_width // 2 - no_bgm_text.get_width() // 2,
                panel_y + 200 * config.scale_factor,
            ),
        )

        note_text = config.small_font.render(
            "assets/bgm フォルダにMP3, OGG, WAVファイルを追加してください",
            True,
            config.theme["text"],
        )
        screen.blit(
            note_text,
            (
                screen_width // 2 - note_text.get_width() // 2,
                panel_y + 240 * config.scale_factor,
            ),
        )

    # BGMリスト表示用の領域
    list_area_y = panel_y + 80 * config.scale_factor
    list_area_height = 320 * config.scale_factor

    # スクロールを適用したY位置調整
    list_y = list_area_y + scroll_offset

    # BGMリストを表示
    buttons = []
    button_height = 40 * config.scale_factor
    button_spacing = 10 * config.scale_factor
    button_width = panel_width - 80 * config.scale_factor

    for i, bgm_file in enumerate(bgm_list):
        # ボタンのY位置を計算
        y_pos = list_y + i * (button_height + button_spacing)

        # 表示範囲内のみ描画
        if (
            y_pos + button_height > list_area_y
            and y_pos < list_area_y + list_area_height
        ):
            # 現在選択中のBGMは背景色を変える
            bg_color = (70, 90, 120) if bgm_file == current_bgm else (60, 60, 60)

            # 表示名（拡張子なし）
            display_name = os.path.splitext(bgm_file)[0]

            # ボタン作成
            bgm_button = Button(
                panel_x + 40 * config.scale_factor,
                y_pos,
                button_width,
                button_height,
                display_name,
                action=f"bgm:{bgm_file}",
                bg_color=bg_color,
            )

            buttons.append(bgm_button)

    # プレビューボタン（曲が存在する場合のみ）
    if bgm_list:
        preview_text = "■ 停止" if pygame.mixer.music.get_busy() else "▶ 再生"
        preview_button = Button(
            panel_x + 40 * config.scale_factor,
            panel_y + panel_height - 110 * config.scale_factor,
            button_width,
            40 * config.scale_factor,
            preview_text,
            action="preview",
        )
        buttons.append(preview_button)

    # 戻るボタン
    back_button = Button(
        panel_x + panel_width // 2 - 100 * config.scale_factor,
        panel_y + panel_height - 60 * config.scale_factor,
        200 * config.scale_factor,
        40 * config.scale_factor,
        "戻る",
        action="back",
    )

    buttons.append(back_button)

    # スクロールバー（BGMリストが表示領域より大きい場合）
    total_list_height = len(bgm_list) * (button_height + button_spacing)
    if total_list_height > list_area_height:
        scrollbar_height = list_area_height * (list_area_height / total_list_height)
        scrollbar_pos = list_area_y - scroll_offset * (
            list_area_height / total_list_height
        )

        # スクロールバーの背景
        pygame.draw.rect(
            screen,
            (40, 40, 40),
            (
                panel_x + panel_width - 20 * config.scale_factor,
                list_area_y,
                10 * config.scale_factor,
                list_area_height,
            ),
        )

        # スクロールバーのつまみ
        pygame.draw.rect(
            screen,
            (100, 100, 100),
            (
                panel_x + panel_width - 20 * config.scale_factor,
                scrollbar_pos,
                10 * config.scale_factor,
                scrollbar_height,
            ),
        )

    # マウス位置取得とボタン更新
    mouse_pos = pygame.mouse.get_pos()
    for button in buttons:
        button.update(mouse_pos)
        button.draw(screen)

    return buttons, total_list_height, list_area_height


# BGM選択画面の実行
def run_bgm_selection(screen):
    scroll_offset = 0
    max_scroll = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # マウスホイールスクロール
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset += event.y * 30 * config.scale_factor

                # スクロール制限
                scroll_offset = min(0, max(-max_scroll, scroll_offset))

            # マウスクリック
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

                # ボタン処理
                buttons, _, _ = draw_bgm_selection(screen, scroll_offset)
                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        if button.action == "back":
                            return
                        elif button.action == "preview":
                            # プレビュー再生/停止
                            if pygame.mixer.music.get_busy():
                                stop_bgm()
                            else:
                                play_bgm()
                        elif button.action.startswith("bgm:"):
                            # BGM選択
                            bgm_file = button.action[4:]  # "bgm:"を除いた部分
                            change_bgm(bgm_file)

                            # プレビュー再生
                            play_bgm()

        # 画面描画
        buttons, total_height, visible_height = draw_bgm_selection(
            screen, scroll_offset
        )
        max_scroll = max(0, total_height - visible_height)

        # 画面更新
        pygame.display.flip()
        pygame.time.delay(30)
