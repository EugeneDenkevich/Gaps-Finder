"""Поиск пропусков слов (отрывков) в аудиофайле с начитанным текстом"""

import re
import json
import difflib
from typing import Dict, List, Union

from colorama import Fore
import whisper


AUDIO_FILE_PATH = "assets/audio.wav"
ORIGIN_TEXT_PATH = "assets/text.txt"
RECOGNIZED_TEXT_PATH = "assets/text_recognized.json" # Нужно, для хранения распознанной речи.


def recognize_speach() -> str:
    """Распознать текст"""
    
    try:
        with open(RECOGNIZED_TEXT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        model = whisper.load_model("large")
        recognized_text = model.transcribe(
            AUDIO_FILE_PATH,
            word_timestamps=True,
        )
        with open(RECOGNIZED_TEXT_PATH, "w", encoding="utf-8") as f:
            json.dump(recognized_text, f, indent=2, ensure_ascii=False)
        return recognized_text


def get_recognized_words(text_recognized):
    words = text_recognized["segments"][0]["words"]
    for word in words:
        word.pop("probability")
        word["word"] = re.sub(r"[^\w\s]", "", word["word"]).strip().lower()
        word["start"] = round(float(word["start"]), 2)
        word["end"] = round(float(word["end"]), 2)

    return words


def get_origin_words() -> str:
    """Получить распознанный текст"""

    with open(ORIGIN_TEXT_PATH, "r") as f:
        text = f.read()

    raw = re.sub(r"[^\w\s]", "", text).lower()
    res = ""
    for word in raw.split():
        res += word.strip() + " "
    words = []
    for word in res.split():
        words.append(
            {
                "word": word,
            },
        )
    return words


def find_gaps(
    original: List[Dict[str, Union[str, float]]],
    recognized: List[Dict[str, Union[str, float]]],
) -> bool:
    """"Найти пропуски"""

    i = 0
    flag = False
    for word1, word2 in zip(original, recognized):
        word1 = original[i]
        matcher = difflib.SequenceMatcher(None, word1["word"], word2["word"])
        if matcher.ratio() < 0.85:
            flag = True
            start = i
            gasped_snippet = original[start + 1:]
            for word_in_snipped in gasped_snippet:
                matcher = difflib.SequenceMatcher(
                    None,
                    word_in_snipped["word"],
                    word2["word"],
                )
                if matcher.ratio() >= 0.85:
                    i += 1
                    break
                i += 1
            original_text = [word["word"] for word in original]
            snippet = " ".join(original_text[start:i])
            print(
                Fore.RED +
                f"Пропущен отрывок:\n" +
                Fore.WHITE +
                f"\"{snippet}\"\n" +
                Fore.YELLOW +
                f"Начало: {word2['start']} сек.\n" +
                f"Конец: {word2['end']} сек.\n" +
                Fore.WHITE
            )
        i += 1
    return flag


def main() -> None:
    """Запуск"""

    text_recognized = recognize_speach()
    recognized_words = get_recognized_words(text_recognized)
    origin_words = get_origin_words()
    
    gaps = find_gaps(
        origin_words,
        recognized_words,
    )

    if not gaps:
        print("Пропусков текста нет.")


__name__ == "__main__" and main()
