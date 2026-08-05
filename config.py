from PyQt6.QtGui import QColor

DEBUG_LOG = 1

# Bảng màu theo code nhóm cổ phiếu (index = code value)
# None = không tô màu (mặc định)
CODE_COLORS = [
    None,               # 0: mặc định
    (173, 216, 230),    # 1: light blue
    (144, 238, 144),    # 2: light green
    (255, 255, 153),    # 3: light yellow
    (255, 182, 193),    # 4: light pink
    (255, 200, 150),    # 5: light orange
    (221, 160, 221),    # 6: plum
    (175, 238, 238),    # 7: pale turquoise
    (255, 228, 181),    # 8: moccasin
    (176, 224, 230),    # 9: powder blue
    (240, 230, 140),    # 10: khaki
    (152, 251, 152),    # 11: pale green
    (255, 160, 122),    # 12: light salmon
    (135, 206, 250),    # 13: light sky blue
    (255, 218, 185),    # 14: peach puff
    (230, 230, 250),    # 15: lavender
    (255, 240, 245),    # 16: lavender blush
    (240, 255, 240),    # 17: honeydew
    (255, 250, 205),    # 18: lemon chiffon
    (224, 255, 255),    # 19: light cyan
]

FIRST_ROW_SYMBOL_B = 0

FIRST_ROW_SYMBOL = -1

LIGHT_BLUE_COLOR = QColor(173, 216, 230)
LIGHT_ORANGE_COLOR = QColor(255, 200, 150)  # light orange