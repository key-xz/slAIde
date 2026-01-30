"""application constants and configuration"""

# ai model configuration
ALLOWED_AI_MODELS = {'fast', 'openai', 'kimi'}
DEFAULT_AI_MODEL = 'fast'

# file upload constraints
MAX_FILE_SIZE_MB = 50
MAX_CONTENT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024

# image conversion settings
IMAGE_CONVERSION_SCALE = 2
IMAGE_CONVERSION_TIMEOUT_SECONDS = 60

# libreoffice paths to check (in order of preference)
LIBREOFFICE_PATHS = [
    '/Applications/LibreOffice.app/Contents/MacOS/soffice',  # macos
    'libreoffice',  # linux
    'soffice',  # alternative
    '/usr/bin/libreoffice',
    '/usr/local/bin/libreoffice',
]

# image conversion tool resolutions
IMAGE_DPI = {
    'screen': 72,
    'good': 150,
    'high': 300,
}

# text overflow compression settings
COMPRESSION_RATIOS = [0.75, 0.65, 0.55, 0.45, 0.35]
MAX_COMPRESSION_ITERATIONS = 5

# font size calculations (magic numbers extracted to constants)
EMU_PER_POINT = 914400 / 72  # 12700
DEFAULT_FONT_SIZE_PT = 18
CHAR_WIDTH_MULTIPLIER = 0.6
LINE_HEIGHT_MULTIPLIER = 1.5
HEIGHT_BUFFER_MULTIPLIER = 1.1

# ai service timeouts
AI_TIMEOUT_SECONDS = 180
AI_VISION_TIMEOUT_SECONDS = 120

# temp file settings
TEMP_FILE_SUFFIX = '.pptx'

# allowed image types
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
