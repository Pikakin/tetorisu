import pygame
import random
import config  # configモジュール全体をインポート


# ボタンクラス
class Button:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        text,
        action=None,
        bg_color=None,
        text_color=None,
        icon=None,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        self.clicked = False
        self.icon = icon

        # デフォルトカラーをテーマから取得
        if bg_color is None:
            self.bg_color = config.theme["button"]
            self.hover_color = config.theme["button_hover"]
        else:
            self.bg_color = bg_color
            # ホバー色は背景色より少し明るく
            r = min(255, bg_color[0] + 20)
            g = min(255, bg_color[1] + 20)
            b = min(255, bg_color[2] + 20)
            self.hover_color = (r, g, b)

        self.text_color = text_color if text_color else config.theme["button_text"]

        # VSCode風のボタンスタイル
        self.border_radius = int(4 * config.scale_factor)
        self.border_color = (70, 70, 70)
        self.shadow_color = (20, 20, 20, 100)
        self.active_border_color = (0, 122, 204)  # VSCodeのアクティブ色

    def update(self, mouse_pos):
        # ホバー状態の更新
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        # 影の描画
        shadow_rect = pygame.Rect(
            self.rect.x + 2 * config.scale_factor,
            self.rect.y + 2 * config.scale_factor,
            self.rect.width,
            self.rect.height,
        )
        pygame.draw.rect(
            surface, self.shadow_color, shadow_rect, border_radius=self.border_radius
        )

        # ボタン本体の描画
        color = self.hover_color if self.hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)

        # ボーダーの描画
        border_color = self.active_border_color if self.hovered else self.border_color
        pygame.draw.rect(
            surface, border_color, self.rect, width=1, border_radius=self.border_radius
        )

        # テキストの描画
        if self.text:
            text_surf = config.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

        # アイコンの描画
        if self.icon:
            icon_rect = self.icon.get_rect(
                midleft=(self.rect.x + 10 * config.scale_factor, self.rect.centery)
            )
            surface.blit(self.icon, icon_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.clicked = True
                if config.has_sound:
                    config.click_sound.play()
                return self.action
        return None


# スタートメニューの描画
def draw_start_menu(screen):
    # 背景
    screen.fill(config.theme["background"])

    # 背景グラデーション効果
    gradient_surface = pygame.Surface(
        (config.screen_width, config.screen_height), pygame.SRCALPHA
    )
    for i in range(config.screen_height):
        alpha = max(0, 40 - (i // 10))
        color = (*config.theme["ui_border"][:3], alpha)
        pygame.draw.line(gradient_surface, color, (0, i), (config.screen_width, i))
    screen.blit(gradient_surface, (0, 0))

    # 装飾的な背景パターン
    for i in range(20):
        size = random.randint(5, 20) * config.scale_factor
        x = random.randint(0, config.screen_width)
        y = random.randint(0, config.screen_height)
        alpha = random.randint(10, 40)
        color = (*config.theme["ui_border"][:3], alpha)
        pygame.draw.rect(
            screen, color, pygame.Rect(x, y, size, size), border_radius=int(size // 3)
        )

    # メインパネル
    panel_width = 500 * config.scale_factor
    panel_height = 550 * config.scale_factor
    panel_x = config.screen_width // 2 - panel_width // 2
    panel_y = config.screen_height // 2 - panel_height // 2 - 20 * config.scale_factor

    # 半透明のパネル背景
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((30, 30, 30, 180))  # 半透明のダークグレー

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(20 * config.scale_factor)
    pygame.draw.rect(panel, (50, 50, 50, 200), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel,
        config.theme["ui_border"],
        panel_rect,
        width=2,
        border_radius=corner_radius,
    )

    # グラデーション効果（上部を少し明るく）
    gradient_height = int(panel_height // 3)
    for i in range(gradient_height):
        alpha = 40 - int(40 * i / gradient_height)
        highlight_color = (255, 255, 255, alpha)
        pygame.draw.rect(
            panel,
            highlight_color,
            pygame.Rect(0, i, panel_width, 1),
            border_radius=corner_radius if i == 0 else 0,
        )

    screen.blit(panel, (panel_x, panel_y))

    # タイトル
    title_text = config.title_font.render("テトリス", True, config.theme["text"])
    title_shadow = config.title_font.render("テトリス", True, (0, 0, 0, 150))

    # タイトルの影
    screen.blit(
        title_shadow,
        (
            config.screen_width // 2
            - title_text.get_width() // 2
            + 3 * config.scale_factor,
            panel_y + 50 * config.scale_factor + 3 * config.scale_factor,
        ),
    )

    # タイトル
    screen.blit(
        title_text,
        (
            config.screen_width // 2 - title_text.get_width() // 2,
            panel_y + 50 * config.scale_factor,
        ),
    )

    # 装飾ライン
    line_y = panel_y + 120 * config.scale_factor
    line_width = panel_width - 60 * config.scale_factor
    line_x = panel_x + 30 * config.scale_factor

    pygame.draw.line(
        screen,
        config.theme["ui_border"],
        (line_x, line_y),
        (line_x + line_width, line_y),
        width=2,
    )

    # ボタンの作成
    buttons = []

    # スタートボタン
    start_button = Button(
        config.screen_width // 2 - 150 * config.scale_factor,
        panel_y + 170 * config.scale_factor,
        300 * config.scale_factor,
        50 * config.scale_factor,
        "ゲームスタート",
        action="start",
    )

    # ゲームモード切替ボタン
    mode_button = Button(
        config.screen_width // 2 - 150 * config.scale_factor,
        panel_y + 240 * config.scale_factor,
        300 * config.scale_factor,
        50 * config.scale_factor,
        f"モード: {config.settings.get('game_mode', 'marathon').capitalize()}",
        action="game_mode",
    )

    # 設定ボタン
    settings_button = Button(
        config.screen_width // 2 - 150 * config.scale_factor,
        panel_y + 310 * config.scale_factor,
        300 * config.scale_factor,
        50 * config.scale_factor,
        "設定",
        action="settings",
    )

    # テーマ切替ボタン
    theme_button = Button(
        config.screen_width // 2 - 150 * config.scale_factor,
        panel_y + 380 * config.scale_factor,
        300 * config.scale_factor,
        50 * config.scale_factor,
        f"テーマ: {config.settings.get('theme', 'classic').capitalize()}",
        action="theme",
    )

    # ハイスコアボタン
    high_scores_button = Button(
        config.screen_width // 2 - 150 * config.scale_factor,
        panel_y + 450 * config.scale_factor,
        300 * config.scale_factor,
        50 * config.scale_factor,
        "ハイスコア",
        action="high_scores",
    )

    # 終了ボタン
    quit_button = Button(
        config.screen_width // 2 - 150 * config.scale_factor,
        panel_y + 520 * config.scale_factor,
        300 * config.scale_factor,
        50 * config.scale_factor,
        "終了",
        action="quit",
    )

    buttons.append(start_button)
    buttons.append(mode_button)
    buttons.append(settings_button)
    buttons.append(theme_button)
    buttons.append(high_scores_button)
    buttons.append(quit_button)

    # マウス位置の取得
    mouse_pos = pygame.mouse.get_pos()

    # ボタンの更新と描画
    for button in buttons:
        button.update(mouse_pos)
        button.draw(screen)

    # バージョン情報
    version_text = config.small_font.render("v1.0.0", True, (150, 150, 150))
    screen.blit(
        version_text,
        (
            config.screen_width - version_text.get_width() - 10 * config.scale_factor,
            config.screen_height - version_text.get_height() - 10 * config.scale_factor,
        ),
    )

    return buttons


# ハイスコア画面の描画
def draw_high_scores(screen, game):
    # 背景
    screen.fill(config.theme["background"])

    # VSCode風のグリッドパターン
    grid_size = 20 * config.scale_factor
    for x in range(0, config.screen_width, int(grid_size)):
        pygame.draw.line(screen, (50, 50, 50, 30), (x, 0), (x, config.screen_height), 1)
    for y in range(0, config.screen_height, int(grid_size)):
        pygame.draw.line(screen, (50, 50, 50, 30), (0, y), (config.screen_width, y), 1)

    # VSCode風のアクティビティバー（左側）
    activity_bar_width = 50 * config.scale_factor
    pygame.draw.rect(
        screen, (40, 40, 40), (0, 0, activity_bar_width, config.screen_height)
    )

    # アイコン（シンプルな形で表現）
    icon_size = 24 * config.scale_factor
    icon_margin = 20 * config.scale_factor

    # ファイルアイコン
    pygame.draw.rect(
        screen,
        (200, 200, 200),
        (activity_bar_width / 2 - icon_size / 2, icon_margin, icon_size, icon_size),
        2,
    )

    # 検索アイコン（円と線）
    pygame.draw.circle(
        screen,
        (200, 200, 200),
        (int(activity_bar_width / 2), int(icon_margin * 2 + icon_size * 1.5)),
        int(icon_size / 3),
        2,
    )

    # メインパネル
    panel_width = 700 * config.scale_factor
    panel_height = 500 * config.scale_factor
    panel_x = config.screen_width // 2 - panel_width // 2
    panel_y = config.screen_height // 2 - panel_height // 2

    # VSCode風のエディタパネル
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((45, 45, 45, 240))  # VSCodeのエディタ背景色

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(8 * config.scale_factor)  # VSCodeは角が少し丸い
    pygame.draw.rect(panel, (50, 50, 50, 255), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel, (70, 70, 70), panel_rect, width=1, border_radius=corner_radius
    )

    # VSCode風のタブバー
    tab_height = 35 * config.scale_factor
    pygame.draw.rect(panel, (37, 37, 38), (0, 0, panel_width, tab_height))

    # アクティブなタブ
    tab_width = 180 * config.scale_factor
    pygame.draw.rect(
        panel, (45, 45, 45), (10 * config.scale_factor, 0, tab_width, tab_height)
    )

    # タブのテキスト
    tab_text = config.small_font.render("highscores.json", True, (212, 212, 212))
    panel.blit(
        tab_text, (20 * config.scale_factor, tab_height / 2 - tab_text.get_height() / 2)
    )

    screen.blit(panel, (panel_x, panel_y))

    # VSCode風の検索バー
    search_bar_height = 40 * config.scale_factor
    search_bar_rect = pygame.Rect(
        panel_x + 20 * config.scale_factor,
        panel_y + 20 * config.scale_factor,
        panel_width - 40 * config.scale_factor,
        search_bar_height,
    )
    pygame.draw.rect(
        screen,
        (60, 60, 60),
        search_bar_rect,
        border_radius=int(4 * config.scale_factor),
    )
    pygame.draw.rect(
        screen,
        (80, 80, 80),
        search_bar_rect,
        width=1,
        border_radius=int(4 * config.scale_factor),
    )

    # 検索アイコン
    icon_size = 16 * config.scale_factor
    pygame.draw.circle(
        screen,
        (180, 180, 180),
        (
            int(panel_x + 40 * config.scale_factor),
            int(panel_y + 20 * config.scale_factor + search_bar_height / 2),
        ),
        int(icon_size / 2),
        1,
    )

    # 検索テキスト
    search_text = config.font.render("ポーズメニュー", True, (180, 180, 180))
    screen.blit(
        search_text,
        (
            panel_x + 60 * config.scale_factor,
            panel_y
            + 20 * config.scale_factor
            + search_bar_height / 2
            - search_text.get_height() / 2,
        ),
    )

    # タイトル
    title_text = config.title_font.render("ハイスコア", True, (212, 212, 212))
    screen.blit(
        title_text,
        (
            panel_x + 20 * config.scale_factor,
            panel_y + tab_height + 20 * config.scale_factor,
        ),
    )

    # ゲームモード選択タブ
    modes = ["marathon", "sprint", "ultra"]
    mode_tabs = []
    mode_tab_width = panel_width / len(modes)

    for i, mode in enumerate(modes):
        mode_tab_rect = pygame.Rect(
            panel_x + i * mode_tab_width,
            panel_y + tab_height + 60 * config.scale_factor,
            mode_tab_width,
            30 * config.scale_factor,
        )

        # アクティブなモードのタブをハイライト
        if mode == game.game_mode:
            pygame.draw.rect(screen, (60, 60, 60), mode_tab_rect)
            pygame.draw.line(
                screen,
                (0, 122, 204),
                (mode_tab_rect.x, mode_tab_rect.y + mode_tab_rect.height - 2),
                (
                    mode_tab_rect.x + mode_tab_rect.width,
                    mode_tab_rect.y + mode_tab_rect.height - 2,
                ),
                2,
            )
            text_color = (255, 255, 255)
        else:
            text_color = (150, 150, 150)

        # モード名
        mode_text = config.font.render(mode.capitalize(), True, text_color)
        screen.blit(
            mode_text,
            (
                mode_tab_rect.x + mode_tab_rect.width / 2 - mode_text.get_width() / 2,
                mode_tab_rect.y + mode_tab_rect.height / 2 - mode_text.get_height() / 2,
            ),
        )

        mode_tabs.append((mode_tab_rect, mode))

    # VSCode風のテーブルヘッダー
    header_y = panel_y + tab_height + 100 * config.scale_factor
    header_height = 30 * config.scale_factor
    col_widths = [0.1, 0.4, 0.25, 0.25]  # 列の幅の比率

    # ヘッダー背景
    pygame.draw.rect(
        screen,
        (60, 60, 60),
        (
            panel_x + 20 * config.scale_factor,
            header_y,
            panel_width - 40 * config.scale_factor,
            header_height,
        ),
    )

    # ヘッダーテキスト
    headers = ["#", "スコア", "レベル", "日付"]
    for i, header in enumerate(headers):
        x_pos = (
            panel_x
            + 20 * config.scale_factor
            + sum(col_widths[:i]) * (panel_width - 40 * config.scale_factor)
        )
        header_text = config.font.render(header, True, (212, 212, 212))
        screen.blit(
            header_text,
            (
                x_pos + 10 * config.scale_factor,
                header_y + header_height / 2 - header_text.get_height() / 2,
            ),
        )

    # ハイスコアの表示
    high_scores = config.load_high_scores()
    mode_scores = high_scores.get(game.game_mode, [])

    row_height = 40 * config.scale_factor
    for i, score in enumerate(mode_scores[:10]):
        row_y = header_y + header_height + i * row_height

        # 交互に背景色を変える（VSCode風）
        if i % 2 == 0:
            pygame.draw.rect(
                screen,
                (50, 50, 50),
                (
                    panel_x + 20 * config.scale_factor,
                    row_y,
                    panel_width - 40 * config.scale_factor,
                    row_height,
                ),
            )

        # 順位
        rank_text = config.font.render(f"{i+1}", True, (212, 212, 212))
        screen.blit(
            rank_text,
            (
                panel_x + 30 * config.scale_factor,
                row_y + row_height / 2 - rank_text.get_height() / 2,
            ),
        )

        # スコア
        score_value = score.get("score", 0)
        if game.game_mode == "sprint":
            minutes = int(score.get("time", 0) // 60)
            seconds = int(score.get("time", 0) % 60)
            score_text = config.font.render(
                f"{minutes}:{seconds:02d}", True, (86, 156, 214)
            )
        else:
            score_text = config.font.render(f"{score_value}", True, (86, 156, 214))

        x_pos = (
            panel_x
            + 20 * config.scale_factor
            + col_widths[0] * (panel_width - 40 * config.scale_factor)
        )
        screen.blit(
            score_text,
            (
                x_pos + 10 * config.scale_factor,
                row_y + row_height / 2 - score_text.get_height() / 2,
            ),
        )

        # レベル
        level_text = config.font.render(
            f"{score.get('level', 1)}", True, (212, 212, 212)
        )
        x_pos = (
            panel_x
            + 20 * config.scale_factor
            + (col_widths[0] + col_widths[1]) * (panel_width - 40 * config.scale_factor)
        )
        screen.blit(
            level_text,
            (
                x_pos + 10 * config.scale_factor,
                row_y + row_height / 2 - level_text.get_height() / 2,
            ),
        )

        # 日付
        date_text = config.font.render(
            f"{score.get('date', '')}", True, (212, 212, 212)
        )
        x_pos = (
            panel_x
            + 20 * config.scale_factor
            + (col_widths[0] + col_widths[1] + col_widths[2])
            * (panel_width - 40 * config.scale_factor)
        )
        screen.blit(
            date_text,
            (
                x_pos + 10 * config.scale_factor,
                row_y + row_height / 2 - date_text.get_height() / 2,
            ),
        )

    # 戻るボタン
    back_button = Button(
        panel_x + panel_width // 2 - 100 * config.scale_factor,
        panel_y + panel_height - 60 * config.scale_factor,
        200 * config.scale_factor,
        40 * config.scale_factor,
        "戻る",
        action="back",
        bg_color=(58, 58, 58),
        text_color=(212, 212, 212),
    )

    # マウス位置の取得
    mouse_pos = pygame.mouse.get_pos()
    back_button.update(mouse_pos)
    back_button.draw(screen)

    # VSCode風のステータスバー
    status_bar_height = 25 * config.scale_factor
    pygame.draw.rect(
        screen,
        (0, 122, 204),
        (
            0,
            config.screen_height - status_bar_height,
            config.screen_width,
            status_bar_height,
        ),
    )

    # ステータス情報
    status_text = config.small_font.render(
        f"モード: {game.game_mode.capitalize()}", True, (255, 255, 255)
    )
    screen.blit(
        status_text,
        (
            10 * config.scale_factor,
            config.screen_height - status_bar_height / 2 - status_text.get_height() / 2,
        ),
    )

    # ボタンリストを作成
    buttons = [back_button]

    # モードタブをボタンとして追加
    for rect, mode in mode_tabs:
        mode_button = Button(
            rect.x, rect.y, rect.width, rect.height, mode.capitalize(), action=mode
        )
        mode_button.update(mouse_pos)
        buttons.append(mode_button)

    return buttons


# 設定メニューの描画
def draw_settings_menu(screen, scroll_offset=0):
    # 背景
    screen.fill(config.theme["background"])

    # 背景グラデーション効果
    gradient_surface = pygame.Surface(
        (config.screen_width, config.screen_height), pygame.SRCALPHA
    )
    for i in range(config.screen_height):
        alpha = max(0, 40 - (i // 10))
        color = (*config.theme["ui_border"][:3], alpha)
        pygame.draw.line(gradient_surface, color, (0, i), (config.screen_width, i))
    screen.blit(gradient_surface, (0, 0))

    # 装飾的な背景パターン
    for i in range(20):
        size = random.randint(5, 20) * config.scale_factor
        x = random.randint(0, config.screen_width)
        y = random.randint(0, config.screen_height)
        alpha = random.randint(10, 40)
        color = (*config.theme["ui_border"][:3], alpha)
        pygame.draw.rect(
            screen, color, pygame.Rect(x, y, size, size), border_radius=int(size // 3)
        )

    # メインパネル
    panel_width = 600 * config.scale_factor
    panel_height = 550 * config.scale_factor
    panel_x = config.screen_width // 2 - panel_width // 2
    panel_y = config.screen_height // 2 - panel_height // 2 - 20 * config.scale_factor

    # 半透明のパネル背景
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((30, 30, 30, 180))  # 半透明のダークグレー

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(20 * config.scale_factor)
    pygame.draw.rect(panel, (50, 50, 50, 200), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel,
        config.theme["ui_border"],
        panel_rect,
        width=2,
        border_radius=corner_radius,
    )

    # グラデーション効果（上部を少し明るく）
    gradient_height = int(panel_height // 3)
    for i in range(gradient_height):
        alpha = 40 - int(40 * i / gradient_height)
        highlight_color = (255, 255, 255, alpha)
        pygame.draw.rect(
            panel,
            highlight_color,
            pygame.Rect(0, i, panel_width, 1),
            border_radius=corner_radius if i == 0 else 0,
        )

    screen.blit(panel, (panel_x, panel_y))

    # タイトル
    title_text = config.title_font.render("設定", True, config.theme["text"])
    title_shadow = config.title_font.render("設定", True, (0, 0, 0, 150))

    # タイトルの影
    screen.blit(
        title_shadow,
        (
            config.screen_width // 2
            - title_text.get_width() // 2
            + 3 * config.scale_factor,
            panel_y + 30 * config.scale_factor + 3 * config.scale_factor,
        ),
    )

    # タイトル
    screen.blit(
        title_text,
        (
            config.screen_width // 2 - title_text.get_width() // 2,
            panel_y + 30 * config.scale_factor,
        ),
    )

    # 装飾ライン
    line_y = panel_y + 90 * config.scale_factor
    line_width = panel_width - 60 * config.scale_factor
    line_x = panel_x + 30 * config.scale_factor

    pygame.draw.line(
        screen,
        config.theme["ui_border"],
        (line_x, line_y),
        (line_x + line_width, line_y),
        width=2,
    )

    # スクロール可能な領域を示す
    scroll_hint_text = config.small_font.render(
        "↑↓ マウスホイールでスクロール", True, config.theme["text"]
    )
    screen.blit(
        scroll_hint_text,
        (
            config.screen_width // 2 - scroll_hint_text.get_width() // 2,
            panel_y + 110 * config.scale_factor,
        ),
    )

    # スクロール可能な領域を定義
    scroll_area_height = panel_height - 200 * config.scale_factor
    scroll_area = pygame.Rect(
        panel_x + 30 * config.scale_factor,
        panel_y + 140 * config.scale_factor,
        panel_width - 60 * config.scale_factor,
        scroll_area_height,
    )

    # スクロール可能な領域の背景
    scroll_bg = pygame.Surface((scroll_area.width, scroll_area.height), pygame.SRCALPHA)
    scroll_bg.fill((20, 20, 20, 100))
    pygame.draw.rect(
        scroll_bg,
        (40, 40, 40, 150),
        pygame.Rect(0, 0, scroll_area.width, scroll_area.height),
        border_radius=int(10 * config.scale_factor),
    )
    pygame.draw.rect(
        scroll_bg,
        (*config.theme["ui_border"][:3], 100),
        pygame.Rect(0, 0, scroll_area.width, scroll_area.height),
        width=1,
        border_radius=int(10 * config.scale_factor),
    )
    screen.blit(scroll_bg, (scroll_area.x, scroll_area.y))

    # ボタンの作成
    buttons = []

    # 各ボタンの基本Y位置（スクロールオフセットを適用）
    base_y = panel_y + 160 * config.scale_factor + scroll_offset

    # ボタン間の間隔
    button_spacing = 70 * config.scale_factor

    # ボタンの幅と位置
    button_width = panel_width - 100 * config.scale_factor
    button_x = config.screen_width // 2 - button_width // 2

    # エフェクト表示切替ボタン
    effects_status = "ON" if config.settings.get("effects", True) else "OFF"
    effects_button = Button(
        button_x,
        base_y,
        button_width,
        50 * config.scale_factor,
        f"エフェクト: {effects_status}",
        action="effects",
    )

    # エフェクトタイプ切替ボタン
    effect_type = config.settings.get("effect_type", "default")
    effect_type_display = {
        "default": "デフォルト",
        "explosion": "爆発",
        "rain": "雨",
        "spiral": "螺旋",
    }.get(effect_type, effect_type)

    effect_type_button = Button(
        button_x,
        base_y + button_spacing,
        button_width,
        50 * config.scale_factor,
        f"エフェクトタイプ: {effect_type_display}",
        action="effect_type",
    )

    # 音楽切替ボタン
    music_status = "ON" if config.settings.get("music", True) else "OFF"
    music_button = Button(
        button_x,
        base_y + button_spacing * 2,
        button_width,
        50 * config.scale_factor,
        f"音楽: {music_status}",
        action="music",
    )

    # 効果音切替ボタン
    sound_status = "ON" if config.settings.get("sound", True) else "OFF"
    sound_button = Button(
        button_x,
        base_y + button_spacing * 3,
        button_width,
        50 * config.scale_factor,
        f"効果音: {sound_status}",
        action="sound",
    )

    # ゴーストピース切替ボタン
    ghost_status = "ON" if config.settings.get("ghost_piece", True) else "OFF"
    ghost_button = Button(
        button_x,
        base_y + button_spacing * 4,
        button_width,
        50 * config.scale_factor,
        f"ゴーストピース: {ghost_status}",
        action="ghost_piece",
    )

    # キー設定ボタン
    key_config_button = Button(
        button_x,
        base_y + button_spacing * 5,
        button_width,
        50 * config.scale_factor,
        "キー設定",
        action="key_config",
    )

    # フルスクリーン切替ボタン
    fullscreen_button = Button(
        button_x,
        base_y + button_spacing * 6,
        button_width,
        50 * config.scale_factor,
        "フルスクリーン切替",
        action="fullscreen",
    )

    # 戻るボタン - 常に画面下部に固定
    back_button = Button(
        config.screen_width // 2 - 100 * config.scale_factor,
        panel_y + panel_height - 60 * config.scale_factor,
        200 * config.scale_factor,
        50 * config.scale_factor,
        "戻る",
        action="back",
    )

    # ボタンをリストに追加
    buttons.append(effects_button)
    buttons.append(effect_type_button)
    buttons.append(music_button)
    buttons.append(sound_button)
    buttons.append(ghost_button)
    buttons.append(key_config_button)
    buttons.append(fullscreen_button)

    # マウス位置の取得
    mouse_pos = pygame.mouse.get_pos()

    # スクロール可能なボタンの描画（スクロール領域内のみ表示）
    for button in buttons:
        # ボタンがスクロール領域内にあるかチェック
        if scroll_area.colliderect(button.rect):
            button.update(mouse_pos)
            button.draw(screen)

    # 戻るボタンの描画（固定位置）
    back_button.update(mouse_pos)
    back_button.draw(screen)

    # スクロールバーの描画（オプション）
    if len(buttons) > 0:
        # スクロール範囲の計算
        content_height = button_spacing * (len(buttons) - 1) + 50 * config.scale_factor
        if content_height > scroll_area_height:
            # スクロールバーの背景
            scrollbar_bg_rect = pygame.Rect(
                scroll_area.right + 10 * config.scale_factor,
                scroll_area.y,
                5 * config.scale_factor,
                scroll_area_height,
            )
            pygame.draw.rect(
                screen,
                (50, 50, 50, 150),
                scrollbar_bg_rect,
                border_radius=int(2 * config.scale_factor),
            )

            # スクロールバーのつまみ
            visible_ratio = scroll_area_height / content_height
            thumb_height = max(
                30 * config.scale_factor, scroll_area_height * visible_ratio
            )

            # スクロール位置に基づいてつまみの位置を計算
            max_scroll = content_height - scroll_area_height
            scroll_ratio = min(
                1, max(0, -scroll_offset / max_scroll if max_scroll > 0 else 0)
            )
            thumb_y = scroll_area.y + scroll_ratio * (scroll_area_height - thumb_height)

            pygame.draw.rect(
                screen,
                (100, 100, 100, 150),
                pygame.Rect(
                    scrollbar_bg_rect.x,
                    thumb_y,
                    scrollbar_bg_rect.width,
                    thumb_height,
                ),
                border_radius=int(2 * config.scale_factor),
            )

    # 戻るボタンをボタンリストに追加
    buttons.append(back_button)

    return buttons


# ポーズメニューの描画
def draw_pause_menu(screen):
    # 半透明のオーバーレイ
    overlay = pygame.Surface(
        (config.screen_width, config.screen_height), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))  # 半透明の黒（より暗く）
    screen.blit(overlay, (0, 0))

    # パネルの寸法と位置
    panel_width = 400 * config.scale_factor
    panel_height = 450 * config.scale_factor
    panel_x = config.screen_width // 2 - panel_width // 2
    panel_y = config.screen_height // 2 - panel_height // 2

    # VSCode風のコマンドパレット風パネル
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((45, 45, 45, 250))  # VSCodeのコマンドパレット背景色

    # パネルの角丸と枠線
    panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
    corner_radius = int(6 * config.scale_factor)  # VSCodeは角が少し丸い
    pygame.draw.rect(panel, (50, 50, 50, 255), panel_rect, border_radius=corner_radius)
    pygame.draw.rect(
        panel, (70, 70, 70), panel_rect, width=1, border_radius=corner_radius
    )

    screen.blit(panel, (panel_x, panel_y))

    # VSCode風の検索バー
    search_bar_height = 40 * config.scale_factor
    search_bar_rect = pygame.Rect(
        panel_x + 20 * config.scale_factor,
        panel_y + 20 * config.scale_factor,
        panel_width - 40 * config.scale_factor,
        search_bar_height,
    )
    pygame.draw.rect(
        screen,
        (60, 60, 60),
        search_bar_rect,
        border_radius=int(4 * config.scale_factor),
    )
    pygame.draw.rect(
        screen,
        (80, 80, 80),
        search_bar_rect,
        width=1,
        border_radius=int(4 * config.scale_factor),
    )

    # 検索アイコン
    icon_size = 16 * config.scale_factor
    pygame.draw.circle(
        screen,
        (180, 180, 180),
        (
            int(panel_x + 40 * config.scale_factor),
            int(panel_y + 20 * config.scale_factor + search_bar_height / 2),
        ),
        int(icon_size / 2),
        1,
    )

    # 検索テキスト
    search_text = config.font.render("ポーズメニュー", True, (180, 180, 180))
    screen.blit(
        search_text,
        (
            panel_x + 60 * config.scale_factor,
            panel_y
            + 20 * config.scale_factor
            + search_bar_height / 2
            - search_text.get_height() / 2,
        ),
    )

    # ボタンの作成（VSCode風のコマンドパレット項目）
    buttons = []
    button_y_start = panel_y + 80 * config.scale_factor
    button_height = 50 * config.scale_factor
    button_spacing = 10 * config.scale_factor
    button_width = panel_width - 40 * config.scale_factor

    # 再開ボタン
    resume_button = Button(
        panel_x + 20 * config.scale_factor,
        button_y_start,
        button_width,
        button_height,
        "ゲームを再開",
        action="resume",
        bg_color=(58, 58, 58),
        text_color=(212, 212, 212),
    )

    # テーマ切替ボタン
    theme_button = Button(
        panel_x + 20 * config.scale_factor,
        button_y_start + (button_height + button_spacing),
        button_width,
        button_height,
        f"テーマ: {config.current_theme.capitalize()}",
        action="theme",
        bg_color=(58, 58, 58),
        text_color=(212, 212, 212),
    )

    # フルスクリーン切替ボタン
    fullscreen_button = Button(
        panel_x + 20 * config.scale_factor,
        button_y_start + (button_height + button_spacing) * 2,
        button_width,
        button_height,
        "フルスクリーン切替",
        action="fullscreen",
        bg_color=(58, 58, 58),
        text_color=(212, 212, 212),
    )

    # メニューに戻るボタン
    quit_button = Button(
        panel_x + 20 * config.scale_factor,
        button_y_start + (button_height + button_spacing) * 3,
        button_width,
        button_height,
        "メニューに戻る",
        action="quit",
        bg_color=(58, 58, 58),
        text_color=(212, 212, 212),
    )

    buttons = [resume_button, theme_button, fullscreen_button, quit_button]

    # マウス位置の取得と更新
    mouse_pos = pygame.mouse.get_pos()
    for button in buttons:
        button.update(mouse_pos)
        button.draw(screen)

    # VSCode風のキーボードショートカット表示
    shortcut_y = panel_y + panel_height - 30 * config.scale_factor
    shortcut_text = config.small_font.render(
        "ESCキーでゲームに戻る", True, (150, 150, 150)
    )
    screen.blit(
        shortcut_text,
        (
            config.screen_width // 2 - shortcut_text.get_width() // 2,
            shortcut_y,
        ),
    )

    return buttons


# ゲームオーバー画面の描画
def draw_game_over_screen(screen, game):
    # 半透明のオーバーレイ
    overlay = pygame.Surface(
        (config.screen_width, config.screen_height), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # メニューパネル
    panel_width = 400 * config.scale_factor
    panel_height = 400 * config.scale_factor
    panel_x = (config.screen_width - panel_width) // 2
    panel_y = (config.screen_height - panel_height) // 2

    pygame.draw.rect(
        screen, config.theme["ui_bg"], (panel_x, panel_y, panel_width, panel_height)
    )
    pygame.draw.rect(
        screen,
        config.theme["ui_border"],
        (panel_x, panel_y, panel_width, panel_height),
        3,
    )

    # タイトル
    title_text = config.title_font.render("ゲームオーバー", True, (255, 100, 100))
    screen.blit(
        title_text,
        (
            config.screen_width // 2 - title_text.get_width() // 2,
            panel_y + 30 * config.scale_factor,
        ),
    )

    # 結果表示
    score_text = config.font.render(f"スコア: {game.score}", True, config.theme["text"])
    level_text = config.font.render(f"レベル: {game.level}", True, config.theme["text"])
    lines_text = config.font.render(
        f"ライン: {game.lines_cleared}", True, config.theme["text"]
    )

    time_minutes = int(game.time_played // 60)
    time_seconds = int(game.time_played % 60)
    time_text = config.font.render(
        f"プレイ時間: {time_minutes}:{time_seconds:02d}", True, config.theme["text"]
    )

    # ハイスコア？
    is_high_score = game.check_high_score()
    high_score_text = None  # 変数を初期化

    if is_high_score:
        # 新記録達成テキストを点滅させる
        if pygame.time.get_ticks() % 1000 < 800:  # 1秒のうち0.8秒間表示
            high_score_text = config.big_font.render(
                "新記録達成！", True, (255, 255, 0)
            )

        # high_score_textが定義されている場合のみ描画
        if high_score_text:
            screen.blit(
                high_score_text,
                (
                    config.screen_width // 2 - high_score_text.get_width() // 2,
                    panel_y + 80 * config.scale_factor,
                ),
            )

    screen.blit(
        score_text,
        (
            config.screen_width // 2 - score_text.get_width() // 2,
            panel_y + 120 * config.scale_factor,
        ),
    )
    screen.blit(
        level_text,
        (
            config.screen_width // 2 - level_text.get_width() // 2,
            panel_y + 160 * config.scale_factor,
        ),
    )
    screen.blit(
        lines_text,
        (
            config.screen_width // 2 - lines_text.get_width() // 2,
            panel_y + 200 * config.scale_factor,
        ),
    )
    screen.blit(
        time_text,
        (
            config.screen_width // 2 - time_text.get_width() // 2,
            panel_y + 240 * config.scale_factor,
        ),
    )

    # リトライボタン
    retry_button = Button(
        panel_x + panel_width // 2 - 100 * config.scale_factor,
        panel_y + 300 * config.scale_factor,
        200 * config.scale_factor,
        40 * config.scale_factor,
        "リトライ",
        action="retry",
    )

    menu_button = Button(
        panel_x + panel_width // 2 - 100 * config.scale_factor,
        panel_y + 350 * config.scale_factor,
        200 * config.scale_factor,
        40 * config.scale_factor,
        "メニューに戻る",
        action="menu",
    )

    mouse_pos = pygame.mouse.get_pos()
    retry_button.update(mouse_pos)
    retry_button.draw(screen)

    menu_button.update(mouse_pos)
    menu_button.draw(screen)

    return [retry_button, menu_button]


# ゲームクリア画面の描画
def draw_game_clear_screen(screen, game):
    # 半透明のオーバーレイ
    overlay = pygame.Surface(
        (config.screen_width, config.screen_height), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # メニューパネル
    panel_width = 400 * config.scale_factor
    panel_height = 400 * config.scale_factor
    panel_x = (config.screen_width - panel_width) // 2
    panel_y = (config.screen_height - panel_height) // 2

    pygame.draw.rect(
        screen, config.theme["ui_bg"], (panel_x, panel_y, panel_width, panel_height)
    )
    pygame.draw.rect(
        screen,
        config.theme["ui_border"],
        (panel_x, panel_y, panel_width, panel_height),
        3,
    )

    # タイトル
    title_text = config.title_font.render("ゲームクリア！", True, (100, 255, 100))
    screen.blit(
        title_text,
        (
            config.screen_width // 2 - title_text.get_width() // 2,
            panel_y + 30 * config.scale_factor,
        ),
    )

    # 結果表示
    score_text = config.font.render(f"スコア: {game.score}", True, config.theme["text"])
    level_text = config.font.render(f"レベル: {game.level}", True, config.theme["text"])
    lines_text = config.font.render(
        f"ライン: {game.lines_cleared}", True, config.theme["text"]
    )

    time_minutes = int(game.time_played // 60)
    time_seconds = int(game.time_played % 60)
    time_text = config.font.render(
        f"クリア時間: {time_minutes}:{time_seconds:02d}", True, config.theme["text"]
    )

    # ハイスコア？
    is_high_score = game.check_high_score()

    if is_high_score:
        high_score_text = config.font.render("新記録達成！", True, (255, 255, 100))
        screen.blit(
            high_score_text,
            (
                config.screen_width // 2 - high_score_text.get_width() // 2,
                panel_y + 80 * config.scale_factor,
            ),
        )

    screen.blit(
        score_text,
        (
            config.screen_width // 2 - score_text.get_width() // 2,
            panel_y + 120 * config.scale_factor,
        ),
    )
    screen.blit(
        level_text,
        (
            config.screen_width // 2 - level_text.get_width() // 2,
            panel_y + 160 * config.scale_factor,
        ),
    )
    screen.blit(
        lines_text,
        (
            config.screen_width // 2 - lines_text.get_width() // 2,
            panel_y + 200 * config.scale_factor,
        ),
    )
    screen.blit(
        time_text,
        (
            config.screen_width // 2 - time_text.get_width() // 2,
            panel_y + 240 * config.scale_factor,
        ),
    )

    # リトライボタン
    retry_button = Button(
        panel_x + panel_width // 2 - 100 * config.scale_factor,
        panel_y + 300 * config.scale_factor,
        200 * config.scale_factor,
        40 * config.scale_factor,
        "リトライ",
        action="retry",
    )

    menu_button = Button(
        panel_x + panel_width // 2 - 100 * config.scale_factor,
        panel_y + 350 * config.scale_factor,
        200 * config.scale_factor,
        40 * config.scale_factor,
        "メニューに戻る",
        action="menu",
    )

    mouse_pos = pygame.mouse.get_pos()
    retry_button.update(mouse_pos)
    retry_button.draw(screen)

    menu_button.update(mouse_pos)
    menu_button.draw(screen)

    return [retry_button, menu_button]
