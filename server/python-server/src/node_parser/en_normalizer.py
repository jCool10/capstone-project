import re
from typing import Any

class EngNormalizer:
    """Abstract Text Normalize protocol."""

    language: str

    def __init__(self) -> None:
        """Normalize base on these rules:
        1. lower case
        2. emoji / emoticon removal
        3. removal of URL and HTML tags
        """
        self._normalize_fns = [
            self.remove_emoji,
            self.remove_emoticon,
            self.remove_html,
            self.remove_urls,
        ]

    def normalize(
        self,
        text: str,
        **add_kwargs: Any,
    ) -> str:
        norm_text = text
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
    
    def remove_emoji(
        self,
        string: str,
        **add_kwargs: Any,
    ) -> str:
        emoji_pattern = re.compile( 
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", 
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r"", string)

    def remove_urls(
        self,
        text: str,
        **add_kwargs: Any,        
    ) -> str:
        url_pattern = re.compile(r"https?://\S+|www\.\S+")
        return url_pattern.sub(r"", text)
    
    def remove_html(
        self,
        text: str,
        **add_kwargs: Any,
    ) -> str:
        #Function for removing html tags
        from bs4 import BeautifulSoup
        return BeautifulSoup(text, "lxml").text
    
    def remove_emoticon(
        self,
        text: str,
        **add_kwargs: Any,
    ) -> str:
        """
        Examples: 'Hello :-)'
        """
        from emot.emo_unicode import UNICODE_EMO, EMOTICONS
        emoticon_pattern = re.compile(u"(" + u"|".join(k for k in EMOTICONS) + u")")
        return emoticon_pattern.sub(r"", text)