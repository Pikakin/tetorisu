import pygame
import json
import os

# 親モジュールのimport
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# キー名と表示名のマッピング
KEY_NAMES = {
    "move_left": "左に移動",
    "move_right": "右に移動",
    "rotate_cw": "時計回りに回転",
    "rotate_ccw": "反時計回りに回転",
    "soft_drop": "ソフトドロップ",
    "hard_drop": "ハードドロップ",
    "hold": "ホールド",
    "pause": "一時停止",
}


# Pygameのキーコードを表示用の文字列に変換する
def key_code_to_string(key_code):
    key_name = pygame.key.name(key_code).upper()
    if key_name == "RETURN":
        return "ENTER"
    elif key_name == "ESCAPE":
        return "ESC"
    elif key_name == "RIGHT":
        return "→"
    elif key_name == "LEFT":
        return "←"
    elif key_name == "UP":
        return "↑"
    elif key_name == "DOWN":
        return "↓"
    return key_name


# キー設定画面の描画
def draw_key_config_screen(screen, current_key=None):
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
    panel.fill((45, 45, 45, 250))  # 半透明パネル

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(8 * config.scale_factor)
    pygame.draw.rect(panel, (50, 50, 50, 255), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel, (70, 70, 70), panel_rect, width=1, border_radius=corner_radius
    )

    screen.blit(panel, (panel_x, panel_y))

    # タイトル
    title_text = config.title_font.render("キー設定", True, config.theme["text"])
    screen.blit(
        title_text,
        (
            screen_width // 2 - title_text.get_width() // 2,
            panel_y + 20 * config.scale_factor,
        ),
    )

    # 説明文
    instruction = "設定するキーを選択してください"
    if current_key:
        instruction = f"{KEY_NAMES[current_key]}に使うキーを押してください"

    instruction_text = config.font.render(instruction, True, config.theme["text"])
    screen.blit(
        instruction_text,
        (
            screen_width // 2 - instruction_text.get_width() // 2,
            panel_y + 70 * config.scale_factor,
        ),
    )

    # キー設定の表示
    buttons = []
    y_start = panel_y + 120 * config.scale_factor
    button_height = 40 * config.scale_factor
    button_spacing = 15 * config.scale_factor
    button_width = panel_width - 80 * config.scale_factor

    # 各キーの設定ボタン
    for i, (key_name, display_name) in enumerate(KEY_NAMES.items()):
        y_pos = y_start + i * (button_height + button_spacing)

        # 現在選択中のキーは色を変える
        bg_color = (70, 70, 130) if current_key == key_name else (60, 60, 60)

        # 設定値の表示
        key_value = config.settings["key_bindings"].get(key_name, pygame.K_UNKNOWN)
        key_display = key_code_to_string(key_value)

        button_text = f"{display_name}: {key_display}"

        # ボタン生成
        from ui import Button  # 既存のButtonクラスを使用

        key_button = Button(
            panel_x + 40 * config.scale_factor,
            y_pos,
            button_width,
            button_height,
            button_text,
            action=key_name,
            bg_color=bg_color,
        )

        buttons.append(key_button)

    # 戻るボタン
    back_button = Button(
        panel_x + panel_width // 2 - 100 * config.scale_factor,
        panel_y + panel_height - 60 * config.scale_factor,
        200 * config.scale_factor,
        40 * config.scale_factor,
        "保存して戻る",
        action="back",
    )

    buttons.append(back_button)

    # マウス位置取得とボタン更新
    mouse_pos = pygame.mouse.get_pos()
    for button in buttons:
        button.update(mouse_pos)
        button.draw(screen)

    return buttons


# キー入力待機画面を表示し、設定を変更する
def wait_for_key_press(screen, key_name):
    pygame.event.clear()  # イベントキューをクリア

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ESCキーが押されたら設定をキャンセルして戻る
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                else:
                    # 押されたキーを設定に保存
                    config.settings["key_bindings"][key_name] = event.key
                    save_key_settings()
                    return True

        # キー待機画面を描画
        draw_key_config_screen(screen, key_name)

        # 画面更新
        pygame.display.flip()
        pygame.time.delay(30)


# 設定の保存
def save_key_settings():
    with open("saves/key_settings.json", "w") as f:
        # キー設定部分だけを抽出して保存
        key_data = {"key_bindings": config.settings["key_bindings"]}
        json.dump(key_data, f)

    # 通常の設定ファイルにも保存
    config.save_settings(config.settings)


# 設定の読み込み
def load_key_settings():
    try:
        with open("saves/key_settings.json", "r") as f:
            key_data = json.load(f)
            # 読み込んだデータで設定を更新
            config.settings["key_bindings"] = key_data["key_bindings"]
    except:
        # ファイルが存在しない場合はデフォルト設定
        if "key_bindings" not in config.settings:
            config.settings["key_bindings"] = {
                "move_left": pygame.K_LEFT,
                "move_right": pygame.K_RIGHT,
                "rotate_cw": pygame.K_UP,
                "rotate_ccw": pygame.K_z,
                "soft_drop": pygame.K_DOWN,
                "hard_drop": pygame.K_SPACE,
                "hold": pygame.K_c,
                "pause": pygame.K_p,
            }


# メイン関数 - 独立して実行する場合のエントリーポイント
def run_key_config(screen):
    current_key = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # マウスクリック処理
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # ボタンの取得
                buttons = draw_key_config_screen(screen, current_key)

                for button in buttons:
                    if button.rect.collidepoint(mouse_pos):
                        if button.action == "back":
                            return  # 設定画面を終了
                        else:
                            # キー設定モードに入る
                            current_key = button.action
                            wait_for_key_press(screen, current_key)
                            current_key = None

        # 画面描画
        draw_key_config_screen(screen, current_key)

        # 画面更新
        pygame.display.flip()
        pygame.time.delay(30)
