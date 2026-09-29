"""Constants for the TartuNLP TTS integration."""

DOMAIN = "tartunlp_tts"
DEFAULT_LANG = "et"
DEFAULT_VOICE = "mari"
CONF_VOICE = "voice"
CONF_BASE_URL = "base_url"
CONF_SPEED = "speed"
DEFAULT_BASE_URL = "https://api.tartunlp.ai/text-to-speech/v2"
DEFAULT_SPEED = 1.0
MIN_SPEED = 0.5
MAX_SPEED = 2.0

SUPPORTED_VOICES = [
    "albert",
    "indrek",
    "kalev",
    "kylli",
    "lee",
    "liivika",
    "luukas",
    "mari",
    "meelis",
    "peeter",
    "tambet",
    "vesta"
]
