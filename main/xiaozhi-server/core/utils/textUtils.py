import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
# The client avatar's expressions (its ExpressionType names, sent as they are)
# and when to use each. The LLM puts a <Name> tag before the sentence where a
# feeling shows (agent-base-prompt.txt); the face changes when that sentence plays.
EXPRESSIONS = [
    ("None", "back to calm"),
    ("Joy", "happy, laughing, having fun"),
    ("Sadness", "sad news, sympathy, grief"),
    ("Anger", "angry, indignant"),
    ("Surprise", "amazed, shocked"),
    ("Fear", "worried, scared, nervous"),
    ("Disgust", "gross, revolting"),
    ("Love", "affection, sweet words"),
    ("Confusion", "puzzled, unsure"),
    ("Skeptical", "doubtful, unimpressed, teasing disbelief"),
    ("Embarrassment", "embarrassed, flattered, awkward"),
    ("Pride", "proud, confident, impressed"),
    ("Desire", "craving, wanting something"),
    ("Relief", "relieved, relaxed, soothing"),
    ("Remorse", "apologising, regret"),
    ("Optimism", "encouraging, hopeful"),
    ("IntenseFocus", "explaining carefully, concentrating"),
]
EXPRESSION_NAMES = {name.lower(): name for name, _ in EXPRESSIONS}
# Text from "<" longer than this without a closing ">" is not a tag
FACE_TAG_MAX_LEN = 20
FACE_TAG_RE = re.compile(r"\s*<\s*(" + "|".join(EXPRESSION_NAMES) + r")\s*>\s*", re.IGNORECASE)


def expression_list_for_prompt():
    return "; ".join(f"{name} ({meaning})" for name, meaning in EXPRESSIONS)


def strip_face_tags(text):
    return FACE_TAG_RE.sub(" ", text).strip() if text else text


def _spoken_len(text):
    # Positions count non-space characters: TTS sentence texts keep those
    return sum(1 for char in text if not char.isspace())


class FaceTagFilter:
    """Strips <Expression> tags from streamed reply text.

    turn is the per-turn dict from ConnectionHandler.face_turn(): "text" counts
    the spoken characters fed to TTS so far and each tag adds a (position,
    expression) cue to "cues". Text that may still become a tag is held back.
    """

    def __init__(self, turn):
        self.turn = turn
        self.buf = ""

    def feed(self, text):
        self.buf += text or ""
        out = []
        while self.buf:
            start = self.buf.find("<")
            if start < 0:
                out.append(self.buf)
                self.buf = ""
                break
            out.append(self.buf[:start])
            self.buf = self.buf[start:]
            end = self.buf.find(">")
            if end < 0:
                if len(self.buf) < FACE_TAG_MAX_LEN:
                    break  # wait for the rest of a possible tag
                out.append(self.buf[0])
                self.buf = self.buf[1:]
                continue
            name = EXPRESSION_NAMES.get(self.buf[1:end].strip().lower())
            if name is None:
                out.append(self.buf[0])
                self.buf = self.buf[1:]
                continue
            pos = self.turn["text"] + _spoken_len("".join(out))
            self.turn["cues"].append((pos, name))
            self.buf = self.buf[end + 1 :].lstrip()
        return self._spoken("".join(out))

    def flush(self):
        rest, self.buf = self.buf, ""
        return self._spoken(rest)

    def _spoken(self, text):
        self.turn["text"] += _spoken_len(text)
        return text


def take_face_cue(turn, sentence_text):
    """The expression whose tag falls in this sentence (the sentences of a turn
    start playing in order), or None"""
    start = turn["played"]
    length = _spoken_len(sentence_text or "")
    turn["played"] += length
    # Half a sentence of slack: TTS may re-segment or substitute words
    due = [c for c in turn["cues"] if c[0] < start + max(1, length // 2)]
    if not due:
        return None
    turn["cues"] = [c for c in turn["cues"] if c not in due]
    return due[-1][1]


EMOJI_RANGES = [
    (0x1F600, 0x1F64F),
    (0x1F300, 0x1F5FF),
    (0x1F680, 0x1F6FF),
    (0x1F900, 0x1F9FF),
    (0x1FA70, 0x1FAFF),
    (0x2600, 0x26FF),
    (0x2700, 0x27BF),
]


def get_string_no_punctuation_or_emoji(s):
    """Remove leading and trailing spaces, punctuation, and emoji from a string"""
    chars = list(s)
    # Process the leading characters
    start = 0
    while start < len(chars) and is_punctuation_or_emoji(chars[start]):
        start += 1
    # Process the trailing characters
    end = len(chars) - 1
    while end >= start and is_punctuation_or_emoji(chars[end]):
        end -= 1
    return "".join(chars[start : end + 1])


def is_punctuation_or_emoji(char):
    """Check whether a character is a space, listed punctuation, or emoji"""
    # Define the Chinese and English punctuation to strip (full-width and half-width)
    punctuation_set = {
        "，",
        ",",  # Chinese comma + English comma
        "。",
        ".",  # Chinese period + English period
        "！",
        "!",  # Chinese exclamation mark + English exclamation mark
        "“",
        "”",
        '"',  # Chinese double quotes + English quote
        "：",
        ":",  # Chinese colon + English colon
        "-",
        "－",  # English hyphen + Chinese full-width dash
        "、",  # Chinese enumeration comma
        "[",
        "]",  # square brackets
        "【",
        "】",  # Chinese square brackets
    }
    if char.isspace() or char in punctuation_set:
        return True
    return is_emoji(char)


async def send_expression(conn: "ConnectionHandler", expression):
    """Tell the client which avatar expression the reply now shows"""
    conn.logger.bind(tag=TAG).info(f"Reply expression: {expression}")
    try:
        await conn.websocket.send(
            json.dumps(
                {
                    "type": "llm",
                    "expression": expression,
                    "session_id": conn.session_id,
                }
            )
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).warning(f"Failed to send the reply expression, error: {e}")


def is_emoji(char):
    """Check whether a character is an emoji"""
    code_point = ord(char)
    return any(start <= code_point <= end for start, end in EMOJI_RANGES)


def check_emoji(text):
    """Remove all emoji from the text"""
    return "".join(char for char in text if not is_emoji(char) and char != "\n")
