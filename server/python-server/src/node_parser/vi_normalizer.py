import re
import sys
from typing import Any, List

if sys.version_info < (3, 8):
    from typing_extensions import Final
else:
    from typing import Final

class ViNormalizer:
    """Abstract Text Normalize protocol."""

    language: str

    def __init__(self) -> None:
        """Normalize base on these rules:
        1. lower case
        2. bullets, ordered bullets, multiple spaces, emoticon removal
        3. removal of HTML tags
        """
        self._normalize_fns = [
            self.truncate_text_by_byte,
            self.remove_emoticon,
            self.remove_bullets,
            self.remove_ordered_bullets,
            self.remove_html_tags,
            self.remove_multiple_spaces,
        ]

    def normalize(
        self,
        text: str,
        **add_kwargs: Any,
    ) -> str:
        """
        features:
        - remove icon, (có sẵn)
        - remove bullet (research)
        - html tags:  </p> (research)
        - remove multiple space: strip() (có sẵn)
        """
        from underthesea import text_normalize
        norm_text = text_normalize(text)
        for norm_fun in self._normalize_fns:
            norm_text = norm_fun(norm_text)
        return norm_text

    async def async_normalize(
        self,
        text: str,
        **kwargs: Any,
    ) -> str:
        """
        Asynchronously add nodes with embedding to vector store.
        NOTE: this is not implemented for all vector stores. If not implemented,
        it will just call add synchronously.
        """
        return self.normalize(text)
    
    def truncate_text_by_byte(self, string_input: str) -> str:
        """
        Truncate a string to a certain number of bytes
        """
        encoded = string_input.encode('utf-8')
        if len(encoded) > 65535:
            string_back = encoded[:65535].decode('utf-8', 'ignore')
            return string_back
        return string_input
    
    def remove_emoticon(
        self,
        text: str,
    ) -> str:
        """
        Examples: 'Hello :-)'
        """
        from emot.emo_unicode import EMOTICONS_EMO
        emoticon_pattern = re.compile(re.escape(u"(" + u"|".join(k for k in EMOTICONS_EMO) + u")"))
        return emoticon_pattern.sub(r"", text)
    
    def remove_bullets(
        self, 
        text: str, 
    ) -> str:
        """Cleans unicode bullets from a section of text.

        Example
        -------
        ●  This is an excellent point! -> This is an excellent point!
        """
        UNICODE_BULLETS: Final[List[str]] = [
            "\u0095",
            "\u2022",
            "\u2023",
            "\u2043",
            "\u3164",
            "\u204C",
            "\u204D",
            "\u2219",
            "\u25CB",
            "\u25CF",
            "\u25D8",
            "\u25E6",
            "\u2619",
            "\u2765",
            "\u2767",
            "\u29BE",
            "\u29BF",
            "\u002D",
            "",
            "\*",  # noqa: W605 NOTE(robinson) - skipping qa because we need the escape for the regex
            "\x95",
            "·",
        ]
        BULLETS_PATTERN = "|".join(UNICODE_BULLETS)
        UNICODE_BULLETS_RE = re.compile(f"(?:{BULLETS_PATTERN})(?!{BULLETS_PATTERN})")

        search = UNICODE_BULLETS_RE.match(text)
        if search is None:
            return text

        cleaned_text = UNICODE_BULLETS_RE.sub("", text, 1)
        return cleaned_text.strip()

    def remove_ordered_bullets(
        self, 
        text: str
    ) -> str:
        """Cleans the start of bulleted text sections up to three “sub-section”
        bullets accounting numeric and alphanumeric types.

        Example
        -------
        1.1 This is a very important point -> This is a very important point
        a.b This is a very important point -> This is a very important point
        """
        text_sp = text.split()
        text_cl = " ".join(text_sp[1:])
        if any(["." not in text_sp[0], ".." in text_sp[0]]):
            return text

        bullet = re.split(pattern=r"[\.]", string=text_sp[0])
        if not bullet[-1]:
            del bullet[-1]

        if len(bullet[0]) > 2:
            return text

        return text_cl

    def remove_html_tags(
        self, 
        text: str
    ) -> str:
        """
        The function `remove_html_tags` takes a string `text` as input and removes all HTML tags and
        entities from it, returning the cleaned text.
        :return: the cleaned text without any HTML tags.

        Example
        -------
        <p>A long text........ </p> -> A long text........ 
        """
        CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        cleantext = re.sub(CLEANR, '', text)
        return cleantext

    def remove_multiple_spaces(
        self, 
        text: str
    ) -> str:
        """Trims whitespace in the middle of a string using regular expressions.
        Args:
            text: The string to trim.

        Returns:
            The trimmed string.
        
        Example
        -------
        "       This string has   extra   spaces in the middle." -> This string has extra spaces in the middle.
        """
        return re.sub(r"\s+", " ", text).strip() 
