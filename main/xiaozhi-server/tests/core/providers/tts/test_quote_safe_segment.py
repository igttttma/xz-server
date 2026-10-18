"""TTSProviderBase._get_segment_text must not cut sentences inside quotes."""
import pytest

from core.providers.tts.base import TTSProviderBase


# Minimal stub: only needs to satisfy the abstract-method instantiation requirements; object.__new__ bypasses
# the abstractmethod check, so adding a new abstract method to the base class will not fail here, which is expected (not called by the tests)
class _TTS(TTSProviderBase):
    async def text_to_speak(self, text, output_file):
        return None


def _segments(text, step, first_sentence=False):
    tts = object.__new__(_TTS)
    tts.punctuations = ("。", "？", "?", "！", "!", "；", ";", "：")
    tts.first_sentence_punctuations = ("，", "~", "、", ",") + tts.punctuations
    tts.tts_text_buff, tts.processed_chars = [], 0
    tts.is_first_sentence, tts.tts_stop_request = first_sentence, False
    out = []
    for i in range(0, len(text), step):
        tts.tts_text_buff.append(text[i:i + step])
        segment = tts._get_segment_text()
        if segment:
            out.append(segment)
    tts.tts_stop_request = True
    rest = tts._get_segment_text()
    if rest:
        out.append(rest)
    return out


@pytest.mark.parametrize("step", [1, 3, 7])
def test_japanese_quote_followed_by_tte_stays_whole(step):
    assert _segments("思わず「わぁ！」って声が出たんだ。きみは？", step) == [
        "思わず「わぁ！」って声が出たんだ",
        "きみは？",
    ]


@pytest.mark.parametrize("step", [1, 4])
def test_chinese_quote_followed_by_speaker_stays_whole(step):
    segments = _segments("He shouted:\u201cGreat!\u201dthen laughed\u3002", step)
    assert not any(seg.startswith("\u201d") for seg in segments)
    # the leading “ is stripped by textUtils, the closing ” must stay with its sentence
    assert any("Great!\u201dthen laughed" in seg for seg in segments)


@pytest.mark.parametrize("step", [1, 5])
def test_closing_quote_then_period_is_not_left_alone(step):
    assert _segments("「すごい！」。次はね、雨！", step) == ["「すごい！」", "次はね、雨"]


@pytest.mark.parametrize("step", [1, 5])
def test_text_without_quotes_is_split_as_before(step):
    assert _segments("普通の文。次の文！最後", step) == ["普通の文", "次の文", "最後"]


@pytest.mark.parametrize("step", [1, 4])
def test_ascii_quote_at_stream_end_stays_whole(step):
    # The old logic cut at the ！ and left an isolated " at the start of the next segment;
    # it now waits for the quote to close and emits the whole sentence at once
    assert _segments('She said, "Hi!"', step) == ['She said, "Hi!"']


_LQ, _RQ = "\u00ab", "\u00bb"        # « » French/Russian guillemet-style quotes
_GOPEN, _GCLOSE = "\u201e", "\u201c"  # „ “ German low-9 quotes


@pytest.mark.parametrize("step", [1, 4])
def test_guillemets_are_not_split(step):
    # ！ sits inside «»; must wait for the closing guillemet before splitting at the sentence-final punctuation
    text = "Il a dit " + _LQ + "Bonjour ! " + _RQ + " puis est parti."
    assert _segments(text, step) == [text]


@pytest.mark.parametrize("step", [1, 4])
def test_german_low9_quotes_stay_whole(step):
    # The closing “ of „…“ is the opening quote of Chinese curly quotes: “ is always counted as an opener
    # by the (“”, ””) pair bookkeeping, so „…“ still looks unbalanced after closing, regardless of following
    # sentence-final punctuation (observed). German can only flush the whole sentence — a conservative
    # expectation under the character conflict, not a defect.
    text = "Er sagte " + _GOPEN + "Hallo!" + _GCLOSE + " und ging."
    assert _segments(text, step) == [text]
    # Closing + Chinese full stop also flushes the whole sentence: the normal path is unreachable because “ has dual semantics
    text2 = "Er sagte " + _GOPEN + "Hallo!" + _GCLOSE + "\u3002Dann geht er\u3002"
    assert _segments(text2, step) == [text2]


@pytest.mark.parametrize("step", [1, 4])
def test_unterminated_quote_flushes_on_stop(step):
    # A single unclosed quote symbol must not stall: wait during streaming, flush the whole segment on stop
    assert _segments('"Hi', step) == ['"Hi']
    assert _segments("「わぁ", step) == ["「わぁ"]


_LB, _RB = "\u3010", "\u3011"  # 【】


@pytest.mark.parametrize("step", [1, 4])
def test_brackets_with_punct_inside_are_not_split(step):
    # ！ inside 【】 must not split (splitting would make the first segment end at "He said【important"),
    # wait for the closing bracket and split at the sentence-final punctuation
    assert _segments("He said" + _LB + "important! steps" + _RB + "\u3002Then left\u3002", step) == [
        "He said" + _LB + "important! steps",
        "Then left",
    ]


def test_nested_mixed_quotes_stay_whole():
    # Nested quotes are counted pair by pair and do not interfere with each other
    assert _segments("\u201cHe said\u300eOK\u300f\u3002\u201dthen left\u3002", 1) == ["He said\u300eOK\u300f\u3002\u201dthen left"]


def test_apostrophes_do_not_block_splitting():
    # Single quotes are ambiguous with apostrophes (don't) and must not be included in the balance check, which would delay whole sentences
    # Note: a flush segment (the remaining text on stop) is emitted as-is without strip
    assert _segments("don't! It's fine.", 1) == ["don't", " It's fine."]


def test_first_sentence_still_splits_at_comma():
    assert _segments("そっか、実習で疲れたんだね。", 1, first_sentence=True)[0] == "そっか"
