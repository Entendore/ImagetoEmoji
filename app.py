import sys
import numpy as np
from PIL import Image, ImageEnhance
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QSpinBox, QProgressBar, 
    QLineEdit, QCheckBox, QGraphicsView, QGraphicsScene, QTabWidget,
    QTextEdit, QComboBox, QSlider, QColorDialog, QFrame, 
    QSplitter, QScrollArea, QStatusBar
)
from PySide6.QtGui import QPixmap, QImage, QPainter, QFont, QFontDatabase, QPalette, QColor, QShortcut, QKeySequence
from PySide6.QtCore import Qt, QThread, Signal

# --- Vectorized Color Conversion Utility ---
def rgb_to_lab_vec(rgb_pixels):
    rgb = rgb_pixels / 255.0
    mask = rgb > 0.04045
    rgb[mask] = ((rgb[mask] + 0.055) / 1.055) ** 2.4
    rgb[~mask] /= 12.92

    x = (rgb[:, 0] * 0.4124 + rgb[:, 1] * 0.3576 + rgb[:, 2] * 0.1805) / 0.95047
    y = (rgb[:, 0] * 0.2126 + rgb[:, 1] * 0.7152 + rgb[:, 2] * 0.0722) / 1.00000
    z = (rgb[:, 0] * 0.0193 + rgb[:, 1] * 0.1192 + rgb[:, 2] * 0.9505) / 1.08883

    mask = x > 0.008856
    x[~mask] = (7.787 * x[~mask]) + (16/116)
    mask = y > 0.008856
    y[~mask] = (7.787 * y[~mask]) + (16/116)
    mask = z > 0.008856
    z[~mask] = (7.787 * z[~mask]) + (16/116)

    L = (116 * y) - 16
    a = 500 * (x - y)
    b = 200 * (y - z)
    return np.stack([L, a, b], axis=-1)

# --- Presets ---
PALETTE_PRESETS = {
    "Custom": "",
    "Mega Gamut (100+ Emojis)": "⬛⬜🟥🟧🟨🟩🟦🟪🟫❤️🧡💛💚💙💜🤎🖤🤍🩶🩷🩵🔴🟠🟡🟢🔵🟣🟤⚪⚫🍎🍊🍋🥝🫐🍇🍓🍉🍒🥥🥑🥦🌽🥕🌶️🫑🍅🍆🥬🥔🍠🥐🍞🧀🥚🍳🥞🥓🍔🍟🍕🌭🥪🌮🌯🥗🥘🍝🍜🍲🍛🍣🍱🥟🍤🍙🍚🍘🍥🥠🥮🍢🍡🍧🍨🍦🥧🍰🎂🍮🍭🍬🍫🍿🍩🍪🌰🥜🍯🥛☕🍵🧋🍺🥂🍷🥃🔥🌿🌸🌵🌺🌻🌞🦓🐘🐬🦖🍄🐶🐱🦊🦁🐻🐼🐨🐯🦒🦘🦔🐾🎃👻🤖🛸👾🌈✨⭐🌟⚡🏀⚽🏈⚾🎾🏐🏉🎱🏓🏸🥅⛳🪐☄️🌪️🌊🧊❄️☃️⛄🦩🕊️🦄🐲",
    "Standard Shapes": "⬛⬜🟥🟧🟨🟩🟦🟪🟫",
    "Hearts": "❤️🧡💛💚💙💜🤎🖤🤍🩶🩷🩵💔❣️💕💞💓💗💖💘💝",
    "Sweets & Desserts": "🍰🧁🍪🍫🍬🍭🍮🍯🥧🍩🍦🍨🍧🧋🥤☕🍵🥛🍯🎂🥮🍡🍥🧇🥞🍰",
    "Halloween / Spooky": "🎃👻💀☠️🦇🕷️🕸️🧟‍♂️🧛‍♂️🧙‍♀️🔮🗡️🔪🩸🌑🦉🐈‍⬛🪦👽👾🛸",
    "Christmas / Winter": "🎄🎅🤶🦌⛄☃️❄️🎁🔔🟢🔴⚪🟤✨🕯️🧦🥛🍪🌟🧣🧤",
    "Valentines / Romance": "💘💝💟💌💖💗💓💞💕❣️💔❤️‍🔥🌹🧸💍👰‍♀️🤵‍♂️🍫🍾💋👩‍❤️‍👨",
    "Sports & Balls": "⚽🏀🏈⚾🥎🎾🏐🏉🥏🎱🏓🏸🏒🏑🥍🏏🥅⛳🏹🥊🥋🎽🛹🏂⛷️🏂",
    "Tech & Sci-Fi": "🤖👾🛸🚀⌨️🖱️💻💾💿📟🔌🔋🧲📡🔭🖥️📱☎️📞⏰⏳💡🔦🛰️",
    "Vibrant Nature": "🌳🌲🌴🌿🍃🍁🍂🌸🌼🌻🍄🌵☘️🍀🌱🪴🪵🪨⛰️🏔️🗻🌋🌍🌎🌏🌑🌒🌓🌔🌕🌖🌗🌘🌙🌚🌛🌜☀️🌝🌞⭐🌟✨⚡🔥💧🌊",
    "Ocean & Ice": "🌊🫧🧊❄️☃️💧🩵💙🟦🟪🐬🐳🐟🦈🐠🐙🦑🦞🦀🦐🦭🦢🐚🪸",
    "Warm & Fire": "🔥❤️🧡💛☀️🌅🌻🌼🌽🍯🦊🦁🐯🐨🦒🐪🐂🐃🐄🐎🐖🐏🐑🐐🦌🐕🐩🐈🐓🦃🦚🦜🦢🕊️🐇🦝🦡☀️🌞⭐🌟💫⚡🌋",
    "Cool & Pastel": "🌸🦩🍑🧠☁️⭐🐤🌷🐣🍩🩷🩵🤍🎈🪁🎀🧸🧵🧶👗👕🧥🦄🐘🦚🦩🐨🐉☀️🌙",
    "Grayscale / Mono": "⬛⬜◼️◻️▪️▫️🖤🤍🩶🐦‍⬛🐼🐧🦛👻🛢️🖨️⚗️🛰️💻⌨️🖱️💾📼🎥📷📸",
    "Fruits & Veggies": "🍎🍊🍋🥝🫐🍇🍓🍉🍒🥥🥑🥦🌽🥕🧄🧅🌶️🫑🍅🍆🥬🥔🍠🥐🍞🧀🥚🍳🥞🥓🍔🍟🍕🌭🥪🌮🌯🥗🥘🍝🍜🍲🍛🍣🍱🥟🍤🍙🍚🍘🍥🥠🥮🍢🍡",
    "Animals": "🐶🐱🐭🐹🐰🦊🐻🐼🐨🐯🦁🐮🐷🐽🐸🐵🙈🙉🙊🐒🐔🐧🐦🐤🐣🐥🦆🦅🦉🦇🐺🐗🐴🦄🐝🐛🦋🐌🐞🐜🦟🦗🕷️🕸️🦂🐢🐍🦎🦖🦕🐙🦑🦐🦞🦀🐡🐠🐟🐬🐳🐋🦈🐊🐅🐆🦓🦍🦧🦣🐘🦛🦏🐪🐫🦒🦘🐃🐂🐄🐎🐖🐏🐑🐐🦌🐕🐩🦮🐈🐓🦃🦚🦜🦢🦩🕊️🐇🦝🦨🦔"
}

class EmojiWorker(QThread):
    progress = Signal(int)
    finished = Signal(object, object)
    error = Signal(str)

    def __init__(self, img, width, height, palette, emoji_size, dithering, bg_color, b_factor, c_factor, s_factor):
        super().__init__()
        self.img = img
        self.width = width
        self.height = height
        self.palette = palette 
        self.emoji_size = emoji_size
        self.dithering = dithering
        self.bg_color = bg_color
        self.b_factor = b_factor
        self.c_factor = c_factor
        self.s_factor = s_factor

    def run(self):
        try:
            self.progress.emit(5)
            img = ImageEnhance.Brightness(self.img).enhance(self.b_factor)
            img = ImageEnhance.Contrast(img).enhance(self.c_factor)
            img = ImageEnhance.Color(img).enhance(self.s_factor)
            
            small_img = img.resize((self.width, self.height), Image.Resampling.LANCZOS).convert("RGBA")
            
            palette_imgs_scaled = [p[0].resize((self.emoji_size, self.emoji_size), Image.Resampling.LANCZOS) for p in self.palette]
            palette_chars = [p[3] for p in self.palette]
            
            result_img = Image.new("RGBA", (self.width * self.emoji_size, self.height * self.emoji_size), self.bg_color)
            text_grid = [[" " for _ in range(self.width)] for _ in range(self.height)]

            pal_colors_rgb = np.array([p[1] for p in self.palette], dtype=np.float32)
            pal_colors_lab = np.array([p[2] for p in self.palette], dtype=np.float32)

            img_array = np.array(small_img, dtype=np.float32)
            alpha_mask = img_array[:, :, 3] > 128
            
            if not self.dithering:
                self.progress.emit(20)
                rgb_pixels = img_array[:, :, :3].reshape(-1, 3)
                flat_alpha = alpha_mask.flatten()
                
                opaque_pixels = rgb_pixels[flat_alpha]
                if len(opaque_pixels) > 0:
                    img_lab = rgb_to_lab_vec(opaque_pixels)
                    diff = img_lab[:, None, :] - pal_colors_lab[None, :, :]
                    dists = np.sum(diff * diff, axis=2)
                    best_indices_local = np.argmin(dists, axis=1)
                    
                    full_indices = np.zeros(rgb_pixels.shape[0], dtype=np.int32)
                    full_indices[flat_alpha] = best_indices_local
                    best_indices_2d = full_indices.reshape((self.height, self.width))
                else:
                    best_indices_2d = np.zeros((self.height, self.width), dtype=np.int32)
                
                self.progress.emit(50)
                for x in range(self.width):
                    for y in range(self.height):
                        if alpha_mask[y, x]:
                            idx = best_indices_2d[y, x]
                            result_img.paste(palette_imgs_scaled[idx], (x * self.emoji_size, y * self.emoji_size), palette_imgs_scaled[idx])
                            text_grid[y][x] = palette_chars[idx]
                    self.progress.emit(50 + int((x / self.width) * 50))
                    
            else:
                total = self.height * self.width
                count = 0
                for y in range(self.height):
                    for x in range(self.width):
                        if img_array[y, x, 3] < 128:
                            text_grid[y][x] = " "
                            count += 1
                            continue
                            
                        old_pixel = img_array[y, x, :3]
                        old_lab = rgb_to_lab_vec(old_pixel.reshape(1, 3))[0]
                        
                        dists = np.sqrt(((pal_colors_lab - old_lab) ** 2).sum(axis=1))
                        best_idx = np.argmin(dists)
                        new_pixel = pal_colors_rgb[best_idx]
                        
                        result_img.paste(palette_imgs_scaled[best_idx], (x * self.emoji_size, y * self.emoji_size), palette_imgs_scaled[best_idx])
                        text_grid[y][x] = palette_chars[best_idx]
                        
                        error = old_pixel - new_pixel
                        if x + 1 < self.width:
                            img_array[y, x + 1, :3] += error * 7/16
                        if y + 1 < self.height:
                            if x > 0:
                                img_array[y + 1, x - 1, :3] += error * 3/16
                            img_array[y + 1, x, :3] += error * 5/16
                            if x + 1 < self.width:
                                img_array[y + 1, x + 1, :3] += error * 1/16
                                
                        count += 1
                        if count % 1000 == 0:
                            self.progress.emit(int((count / total) * 100))

            self.progress.emit(100)
            self.finished.emit(result_img, text_grid)
        except Exception as e:
            self.error.emit(str(e))

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event):
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(zoom_factor, zoom_factor)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro Emoji Art Studio")
        self.resize(1500, 950)
        self.setup_dark_mode()
        self.setAcceptDrops(True) # Enable Drag & Drop for the whole window

        self.original_pil = None
        self.result_pil = None
        self.palette = []
        self.worker = None
        self.aspect_ratio = 1.0
        self.bg_color = QColor(30, 30, 30, 255)

        self.init_ui()
        self.setup_shortcuts()
        self.on_preset_selected("Mega Gamut (100+ Emojis)")
        self.show_drop_placeholder()

    def setup_dark_mode(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(40, 40, 40))
        dark_palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { color: #e0e0e0; }
            QScrollArea { border: none; background-color: #252525; }
            QFrame#Header { background-color: #2d2d2d; border-bottom: 1px solid #111; }
            QFrame#Sidebar { background-color: #252525; border-right: 1px solid #111; }
            QFrame#Section { background-color: transparent; border: none; }
            QLabel#SectionTitle { 
                color: #aaaaaa; 
                font-size: 11px; 
                font-weight: bold; 
                padding: 2px 0px 8px 0px;
            }
            QPushButton { 
                padding: 8px 12px; 
                border-radius: 4px; 
                background-color: #3a3a3a; 
                border: 1px solid #444;
            }
            QPushButton:hover { background-color: #4a4a4a; border: 1px solid #555; }
            QPushButton:pressed { background-color: #2a2a2a; }
            QPushButton#PrimaryBtn { background-color: #007acc; border: none; color: white; font-weight: bold; }
            QPushButton#PrimaryBtn:hover { background-color: #1c8cd6; }
            QPushButton#SecondaryBtn { background-color: #2d2d2d; border: 1px solid #444; font-weight: bold; }
            QPushButton#SecondaryBtn:hover { background-color: #3d3d3d; }
            QComboBox, QSpinBox, QLineEdit { 
                padding: 6px; 
                border: 1px solid #444; 
                border-radius: 4px; 
                background-color: #333;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QSlider::groove:horizontal { border: 1px solid #444; height: 6px; background: #2a2a2a; border-radius: 3px; }
            QSlider::handle:horizontal { background: #007acc; width: 16px; margin: -6px 0; border-radius: 8px; }
            QSlider::handle:horizontal:hover { background: #1c8cd6; }
            QProgressBar { text-align: center; border: 1px solid #444; border-radius: 4px; background-color: #2a2a2a; height: 20px; }
            QProgressBar::chunk { background-color: #007acc; border-radius: 3px; }
            QTabWidget::pane { border: none; background-color: #1e1e1e; }
            QTabBar::tab { background: #252525; padding: 10px 20px; border: 1px solid #111; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #1e1e1e; border-bottom: 2px solid #007acc; }
            QGraphicsView { border: 1px solid #111; border-radius: 4px; background-color: #181818; }
            QSplitter::handle { background-color: #111; width: 2px; }
            QStatusBar { background-color: #007acc; color: white; font-size: 12px; }
            QStatusBar QLabel { color: white; }
            QTextEdit { border: none; background-color: #181818; }
        """)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- TOP HEADER TOOLBAR ---
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(50)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        title_label = QLabel("🎨 Pro Emoji Art Studio")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.btn_save_img = QPushButton("💾  Save PNG")
        self.btn_save_img.setObjectName("SecondaryBtn")
        self.btn_save_img.clicked.connect(self.save_image)
        self.btn_save_img.setEnabled(False)
        header_layout.addWidget(self.btn_save_img)

        self.btn_generate = QPushButton("✨  GENERATE ART")
        self.btn_generate.setObjectName("PrimaryBtn")
        self.btn_generate.clicked.connect(self.start_generation)
        self.btn_generate.setEnabled(False)
        header_layout.addWidget(self.btn_generate)

        main_layout.addWidget(header)

        # --- BODY (Sidebar + Main Content) ---
        body_splitter = QSplitter(Qt.Horizontal)
        body_splitter.setChildrenCollapsible(False)
        main_layout.addWidget(body_splitter, 1)

        # --- LEFT SIDEBAR ---
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(320)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        sidebar_layout.setSpacing(20)

        # Section 1: Image Source
        sec1 = QFrame()
        sec1.setObjectName("Section")
        sec1_l = QVBoxLayout(sec1)
        sec1_l.setContentsMargins(0,0,0,0)
        sec1_l.addWidget(self.create_section_label("1. Image Source"))
        self.btn_load = QPushButton("📂  Load Image File")
        self.btn_load.clicked.connect(self.load_image_dialog)
        sec1_l.addWidget(self.btn_load)
        
        self.btn_paste = QPushButton("📋  Paste from Clipboard (Ctrl+V)")
        self.btn_paste.clicked.connect(self.paste_from_clipboard)
        sec1_l.addWidget(self.btn_paste)
        
        sidebar_layout.addWidget(sec1)

        # Section 2: Palette
        sec2 = QFrame()
        sec2.setObjectName("Section")
        sec2_l = QVBoxLayout(sec2)
        sec2_l.setContentsMargins(0,0,0,0)
        sec2_l.addWidget(self.create_section_label("2. Emoji Palette"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItems(PALETTE_PRESETS.keys())
        self.combo_presets.currentTextChanged.connect(self.on_preset_selected)
        sec2_l.addWidget(self.combo_presets)
        sec2_l.addWidget(QLabel("Custom Emojis:"))
        self.txt_emojis = QLineEdit()
        self.txt_emojis.textChanged.connect(lambda: self.combo_presets.setCurrentText("Custom"))
        sec2_l.addWidget(self.txt_emojis)
        self.btn_update_palette = QPushButton("Apply Custom Palette")
        self.btn_update_palette.clicked.connect(self.update_palette_from_text)
        sec2_l.addWidget(self.btn_update_palette)
        sidebar_layout.addWidget(sec2)

        # Section 3: Output Settings
        sec3 = QFrame()
        sec3.setObjectName("Section")
        sec3_l = QVBoxLayout(sec3)
        sec3_l.setContentsMargins(0,0,0,0)
        sec3_l.addWidget(self.create_section_label("3. Output Settings"))
        
        out_row1 = QHBoxLayout()
        self.chk_lock_ar = QCheckBox("Lock AR")
        self.chk_lock_ar.setChecked(True)
        out_row1.addWidget(self.chk_lock_ar)
        out_row1.addStretch()
        out_row1.addWidget(QLabel("W:"))
        self.spin_width = QSpinBox()
        self.spin_width.setMinimum(10)
        self.spin_width.setMaximum(500)
        self.spin_width.setValue(80)
        self.spin_width.valueChanged.connect(self.on_width_changed)
        out_row1.addWidget(self.spin_width)
        out_row1.addWidget(QLabel("H:"))
        self.spin_height = QSpinBox()
        self.spin_height.setMinimum(10)
        self.spin_height.setMaximum(500)
        self.spin_height.setValue(60)
        self.spin_height.valueChanged.connect(self.on_height_changed)
        out_row1.addWidget(self.spin_height)
        sec3_l.addLayout(out_row1)

        out_row2 = QHBoxLayout()
        out_row2.addWidget(QLabel("Emoji Size (px):"))
        self.spin_size = QSpinBox()
        self.spin_size.setMinimum(8)
        self.spin_size.setMaximum(64)
        self.spin_size.setValue(16)
        out_row2.addWidget(self.spin_size)
        sec3_l.addLayout(out_row2)

        self.chk_dither = QCheckBox("Dithering (High Detail)")
        self.chk_dither.setChecked(True)
        sec3_l.addWidget(self.chk_dither)

        out_row3 = QHBoxLayout()
        out_row3.addWidget(QLabel("Background:"))
        self.btn_bg_color = QPushButton()
        self.btn_bg_color.setFixedHeight(28)
        self.btn_bg_color.setStyleSheet(f"background-color: {self.bg_color.name()}; border: 1px solid #888; border-radius: 4px;")
        self.btn_bg_color.clicked.connect(self.pick_bg_color)
        out_row3.addWidget(self.btn_bg_color)
        sec3_l.addLayout(out_row3)
        sidebar_layout.addWidget(sec3)

        # Section 4: Adjustments
        sec4 = QFrame()
        sec4.setObjectName("Section")
        sec4_l = QVBoxLayout(sec4)
        sec4_l.setContentsMargins(0,0,0,0)
        sec4_l.addWidget(self.create_section_label("4. Image Adjustments"))
        
        sec4_l.addWidget(QLabel("Brightness:"))
        self.slider_brightness = QSlider(Qt.Horizontal)
        self.slider_brightness.setRange(0, 200)
        self.slider_brightness.setValue(100)
        sec4_l.addWidget(self.slider_brightness)

        sec4_l.addWidget(QLabel("Contrast:"))
        self.slider_contrast = QSlider(Qt.Horizontal)
        self.slider_contrast.setRange(0, 200)
        self.slider_contrast.setValue(100)
        sec4_l.addWidget(self.slider_contrast)

        sec4_l.addWidget(QLabel("Saturation:"))
        self.slider_saturation = QSlider(Qt.Horizontal)
        self.slider_saturation.setRange(0, 200)
        self.slider_saturation.setValue(100)
        sec4_l.addWidget(self.slider_saturation)
        sidebar_layout.addWidget(sec4)
        
        sidebar_layout.addStretch(1)
        
        # Progress bar at bottom of sidebar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        sidebar_layout.addWidget(self.progress)

        body_splitter.addWidget(sidebar)

        # --- RIGHT MAIN AREA ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.tabs = QTabWidget()
        
        # Image Tab
        img_tab = QWidget()
        img_tab_layout = QVBoxLayout(img_tab)
        img_tab_layout.setContentsMargins(10, 10, 10, 10)
        img_tab_layout.setSpacing(5)
        
        # Splitter for Original and Result
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        
        orig_container = QWidget()
        orig_lay = QVBoxLayout(orig_container)
        orig_lay.setContentsMargins(0,0,0,0)
        orig_lay.setSpacing(5)
        orig_header = QHBoxLayout()
        orig_header.addWidget(QLabel("<b>Original Image</b>"))
        orig_header.addStretch()
        btn_fit_orig = QPushButton("Fit")
        btn_fit_orig.setFixedWidth(50)
        btn_fit_orig.clicked.connect(lambda: self.orig_view.fitInView(self.orig_scene.sceneRect(), Qt.KeepAspectRatio))
        orig_header.addWidget(btn_fit_orig)
        orig_lay.addLayout(orig_header)
        
        self.orig_view = QGraphicsView()
        self.orig_scene = QGraphicsScene()
        self.orig_view.setScene(self.orig_scene)
        orig_lay.addWidget(self.orig_view, 1)
        
        res_container = QWidget()
        res_lay = QVBoxLayout(res_container)
        res_lay.setContentsMargins(0,0,0,0)
        res_lay.setSpacing(5)
        res_header = QHBoxLayout()
        res_header.addWidget(QLabel("<b>Emoji Result</b>"))
        res_header.addStretch()
        btn_fit_res = QPushButton("Fit")
        btn_fit_res.setFixedWidth(50)
        btn_fit_res.clicked.connect(lambda: self.res_view.fitInView(self.res_scene.sceneRect(), Qt.KeepAspectRatio))
        res_header.addWidget(btn_fit_res)
        res_lay.addLayout(res_header)
        
        self.res_view = ZoomableGraphicsView()
        self.res_scene = QGraphicsScene()
        self.res_view.setScene(self.res_scene)
        res_lay.addWidget(self.res_view, 1)
        
        self.splitter.addWidget(orig_container)
        self.splitter.addWidget(res_container)
        self.splitter.setSizes([400, 600])
        
        img_tab_layout.addWidget(self.splitter)
        self.tabs.addTab(img_tab, "Visual Preview")

        # Text Tab
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        text_layout.setContentsMargins(10,10,10,10)
        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        self.txt_result.setStyleSheet("font-family: 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji'; font-size: 16px;")
        text_layout.addWidget(self.txt_result)
        
        text_btns = QHBoxLayout()
        text_btns.addStretch(1)
        btn_copy = QPushButton("📋  Copy to Clipboard")
        btn_copy.setObjectName("SecondaryBtn")
        btn_copy.clicked.connect(self.copy_text)
        text_btns.addWidget(btn_copy)
        btn_save_txt = QPushButton("💾  Save as .txt")
        btn_save_txt.setObjectName("SecondaryBtn")
        btn_save_txt.clicked.connect(self.save_text)
        text_btns.addWidget(btn_save_txt)
        text_layout.addLayout(text_btns)
        
        self.tabs.addTab(text_tab, "Text Output")
        
        right_layout.addWidget(self.tabs, 1)
        body_splitter.addWidget(right_panel)
        body_splitter.setSizes([320, 1180])

        # --- STATUS BAR ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Drag & Drop, Paste (Ctrl+V), or click Load Image to begin.")

    def setup_shortcuts(self):
        # Ctrl+V to paste
        self.shortcut_paste = QShortcut(QKeySequence("Ctrl+V"), self)
        self.shortcut_paste.activated.connect(self.paste_from_clipboard)
        # Ctrl+S to save image
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_image)
        # Ctrl+G to generate
        self.shortcut_generate = QShortcut(QKeySequence("Ctrl+G"), self)
        self.shortcut_generate.activated.connect(self.start_generation)

    def create_section_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("SectionTitle")
        return lbl

    # --- IMPORT FEATURES (Drag & Drop, Clipboard, File Dialog) ---

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            url = mime_data.urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                ext = file_path.lower().split('.')[-1]
                if ext in ['png', 'jpg', 'jpeg', 'bmp']:
                    try:
                        img = Image.open(file_path).convert("RGBA")
                        self.load_pil_image(img, file_path.split('/')[-1])
                    except Exception as e:
                        self.status_bar.showMessage(f"Error loading dropped file: {e}")
        elif mime_data.hasImage():
            qimg = mime_data.imageData()
            pil_img = self.qimage_to_pil(qimg)
            if pil_img:
                self.load_pil_image(pil_img, "Dropped Image")

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        
        if mime.hasImage():
            qimg = clipboard.image()
            if not qimg.isNull():
                pil_img = self.qimage_to_pil(qimg)
                if pil_img:
                    self.load_pil_image(pil_img, "Pasted Image")
                    return
        
        if mime.hasUrls():
            url = mime.urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                ext = file_path.lower().split('.')[-1]
                if ext in ['png', 'jpg', 'jpeg', 'bmp']:
                    try:
                        img = Image.open(file_path).convert("RGBA")
                        self.load_pil_image(img, file_path.split('/')[-1])
                        return
                    except:
                        pass
        
        self.status_bar.showMessage("Clipboard does not contain a valid image.")

    def load_image_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            try:
                img = Image.open(file_name).convert("RGBA")
                self.load_pil_image(img, file_name.split('/')[-1])
            except Exception as e:
                self.status_bar.showMessage(f"Error loading file: {e}")

    def qimage_to_pil(self, qimg):
        try:
            qimg = qimg.convertToFormat(QImage.Format_RGBA8888)
            ptr = qimg.bits()
            ptr.setsize(qimg.sizeInBytes())
            pil_img = Image.frombytes("RGBA", (qimg.width(), qimg.height()), bytes(ptr))
            return pil_img
        except Exception as e:
            self.status_bar.showMessage(f"Image conversion error: {e}")
            return None

    def load_pil_image(self, pil_img, name="Image"):
        self.original_pil = pil_img
        self.aspect_ratio = self.original_pil.height / self.original_pil.width
        
        self.spin_width.blockSignals(True)
        self.spin_height.blockSignals(True)
        self.spin_width.setValue(80)
        self.on_width_changed(80)
        self.spin_width.blockSignals(False)
        self.spin_height.blockSignals(False)

        self.display_pil_on_scene(self.original_pil, self.orig_scene)
        self.orig_view.fitInView(self.orig_scene.sceneRect(), Qt.KeepAspectRatio)
        self.btn_generate.setEnabled(True)
        self.btn_save_img.setEnabled(False)
        self.progress.setValue(0)
        self.res_scene.clear()
        self.txt_result.clear()
        self.status_bar.showMessage(f"Loaded: {name}")

    def show_drop_placeholder(self):
        text = "Drag & Drop Image Here\nor\nClick 'Load Image'\nor\nPress Ctrl+V to Paste"
        item = self.orig_scene.addText(text, QFont("Segoe UI", 14))
        item.setDefaultTextColor(QColor("#555555"))
        text_rect = item.boundingRect()
        self.orig_scene.setSceneRect(0, 0, text_rect.width(), text_rect.height())

    def on_preset_selected(self, text):
        preset_emojis = PALETTE_PRESETS.get(text, "")
        if preset_emojis:
            self.txt_emojis.setText(preset_emojis)
            self.update_palette_from_text()

    def pick_bg_color(self):
        color = QColorDialog.getColor(self.bg_color, self, "Select Background Color", QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.bg_color = color
            self.btn_bg_color.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888; border-radius: 4px;")

    def on_width_changed(self, val):
        if self.chk_lock_ar.isChecked() and self.aspect_ratio > 0:
            self.spin_height.blockSignals(True)
            self.spin_height.setValue(int(val * self.aspect_ratio))
            self.spin_height.blockSignals(False)
        self.update_status_bar()

    def on_height_changed(self, val):
        if self.chk_lock_ar.isChecked() and self.aspect_ratio > 0 and val > 0:
            self.spin_width.blockSignals(True)
            self.spin_width.setValue(int(val / self.aspect_ratio))
            self.spin_width.blockSignals(False)
        self.update_status_bar()

    def update_status_bar(self):
        w = self.spin_width.value()
        h = self.spin_height.value()
        s = self.spin_size.value()
        total_emojis = w * h
        res_w = w * s
        res_h = h * s
        self.status_bar.showMessage(f"Grid: {w}x{h} emojis | Total Emojis: {total_emojis:,} | Final Image Resolution: {res_w}x{res_h}px")

    def update_palette_from_text(self):
        text = self.txt_emojis.text().strip()
        if text:
            self.generate_emoji_palette(text)

    def generate_emoji_palette(self, emoji_string):
        self.palette = []
        font_families = ["Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", "DejaVu Sans"]
        font = QFont()
        for fam in font_families:
            if fam in QFontDatabase.families():
                font.setFamily(fam)
                break
        font.setPointSize(32)

        import unicodedata
        chars = []
        current_char = ""
        for c in emoji_string:
            if unicodedata.combining(c) or c == '\uFE0F' or c == '\u200D':
                current_char += c
            else:
                if current_char:
                    chars.append(current_char)
                current_char = c
        if current_char:
            chars.append(current_char)

        for emoji_char in chars:
            if emoji_char.isspace(): continue
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji_char)
            painter.end()

            qimg = pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)
            ptr = qimg.bits()
            ptr.setsize(qimg.sizeInBytes())
            pil_img = Image.frombytes("RGBA", (64, 64), bytes(ptr))

            pixels = list(pil_img.getdata())
            r_sum, g_sum, b_sum, count = 0, 0, 0, 0
            for p in pixels:
                if p[3] > 0:
                    r_sum += p[0]
                    g_sum += p[1]
                    b_sum += p[2]
                    count += 1
            
            if count > 0:
                avg_rgb = (r_sum // count, g_sum // count, b_sum // count)
                avg_lab = rgb_to_lab_vec(np.array([avg_rgb], dtype=np.float32))[0]
                self.palette.append((pil_img, avg_rgb, avg_lab, emoji_char))

    def start_generation(self):
        if not self.original_pil or not self.palette:
            return

        w = self.spin_width.value()
        h = self.spin_height.value()
        size = self.spin_size.value()
        dither = self.chk_dither.isChecked()
        
        bg = (self.bg_color.red(), self.bg_color.green(), self.bg_color.blue(), self.bg_color.alpha())
        b = self.slider_brightness.value() / 100.0
        c = self.slider_contrast.value() / 100.0
        s = self.slider_saturation.value() / 100.0

        self.btn_generate.setEnabled(False)
        self.progress.setValue(0)
        self.status_bar.showMessage("Generating...")

        self.worker = EmojiWorker(self.original_pil, w, h, self.palette, size, dither, bg, b, c, s)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.error.connect(self.on_generation_error)
        self.worker.start()

    def on_generation_finished(self, result_img, text_grid):
        self.result_pil = result_img
        self.display_pil_on_scene(self.result_pil, self.res_scene)
        self.res_view.fitInView(self.res_scene.sceneRect(), Qt.KeepAspectRatio)
        
        text_string = "\n".join("".join(row) for row in text_grid)
        self.txt_result.setPlainText(text_string)
        
        self.btn_generate.setEnabled(True)
        self.btn_save_img.setEnabled(True)
        self.tabs.setCurrentIndex(0)
        self.update_status_bar()

    def on_generation_error(self, err_msg):
        self.progress.setValue(0)
        self.res_scene.clear()
        self.res_scene.addText(f"Error: {err_msg}")
        self.btn_generate.setEnabled(True)
        self.status_bar.showMessage(f"Error: {err_msg}")

    def copy_text(self):
        cb = QApplication.clipboard()
        cb.setText(self.txt_result.toPlainText())
        self.status_bar.showMessage("Text copied to clipboard!")

    def save_text(self):
        if not self.txt_result.toPlainText(): return
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Text", "emoji_art.txt", "Text Files (*.txt)")
        if file_name:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(self.txt_result.toPlainText())
            self.status_bar.showMessage(f"Saved text to {file_name}")

    def save_image(self):
        if not self.result_pil: return
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", "emoji_art.png", "PNG Files (*.png)")
        if file_name:
            self.result_pil.save(file_name)
            self.status_bar.showMessage(f"Saved image to {file_name}")

    def resizeEvent(self, event):
        self.orig_view.fitInView(self.orig_scene.sceneRect(), Qt.KeepAspectRatio)
        self.res_view.fitInView(self.res_scene.sceneRect(), Qt.KeepAspectRatio)
        super().resizeEvent(event)

    def display_pil_on_scene(self, pil_img, scene):
        data = pil_img.tobytes("raw", "RGBA")
        qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimg.copy())
        
        scene.clear()
        scene.addPixmap(pixmap)
        scene.setSceneRect(0, 0, pil_img.width, pil_img.height)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())