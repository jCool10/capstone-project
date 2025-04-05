import re
import logging
from typing import Optional, List, Any, Iterable, Callable

from src.bridge.pydantic import Field
from src.callbacks.callback_manager import CallbackManager, CBEventType, EventPayload
from src.node_parser.base import TextSplitter
from src.constants import DEFAULT_CHUNK_SIZE
from src.utils.utils import get_tokenizer

SENTENCE_CHUNK_OVERLAP = 200

logger = logging.getLogger(__name__)

class RecursiveCharacterTextSplitter(TextSplitter):
    """Splitting text by recursively look at characters.

    Recursively tries to split by different characters to find one
    that works.
    """

    chunk_size: int = Field(
        description="The token chunk size for each chunk.",
        gt=0,
    )
    chunk_overlap: int = Field(
        description="The token overlap of each chunk when splitting.",
        gte=0,
    )
    separators: List[str] = Field(
        description="Default separator for splitting into words"
    )
    tokenizer: Callable = Field(
        description="Default separator for splitting into words"
    )

    is_separator_regex: bool = Field(
        default=False, description="Whether or not to consider metadata when splitting."
    )
    keep_separator: bool = Field(
        default=False, description="Whether to keep the separator in the chunks"
    )
    add_start_index: bool = Field(
        default=False, description="includes chunk's start index in metadata"
    )
    strip_whitespace: bool = Field(
        default=True, description="strips whitespace from the start and end of every splits"
    )
    

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = SENTENCE_CHUNK_OVERLAP,
        separators: Optional[List[str]] = None,
        is_separator_regex: bool = False,
        keep_separator: bool = False,
        add_start_index: bool = False,
        strip_whitespace: bool = True,
        tokenizer: Optional[Callable] = None,
        callback_manager: Optional[CallbackManager] = None,
        **kwargs: Any,
    ) -> None:
        """Create a new TextSplitter.

        keep_separator (bool): Whether to keep the separator in the chunks

        """
        if chunk_overlap > chunk_size:
            raise ValueError(
                f"Got a larger chunk overlap ({chunk_overlap}) than chunk size "
                f"({chunk_size}), should be smaller."
            )

        separators = separators or ["\n\n", "\n", " ", ""]
        callback_manager = callback_manager or CallbackManager()
        tokenizer = tokenizer or get_tokenizer()

        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap = chunk_overlap,
            separators=separators,
            keep_separator = keep_separator,
            is_separator_regex = is_separator_regex,
            add_start_index = add_start_index,
            strip_whitespace = strip_whitespace,
            tokenizer = tokenizer,
            callback_manager=callback_manager,
            **kwargs
        )


    def split_text(self, text: str, separators: List[str]) -> List[str]:
        """
        Main Function
        """
        with self.callback_manager.event(
            CBEventType.CHUNKING, payload={EventPayload.CHUNKS: [text]}
        ) as event:
            # call main function of this class
            chunks = self._split_text(text, separators)
            # ending event
            event.on_end(payload={EventPayload.CHUNKS: chunks})
        return chunks

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Split incoming text and return chunks."""
        final_chunks = []
        # Get appropriate separator to use
        separator = separators[-1]
        new_separators = []
        for i, _s in enumerate(separators):
            _separator = _s if self.is_separator_regex else re.escape(_s)
            if _s == "":
                separator = _s
                break
            if re.search(_separator, text):
                separator = _s
                new_separators = separators[i + 1 :]
                break

        _separator = separator if self.is_separator_regex else re.escape(separator)
        splits = self._split_text_with_regex(text, _separator, self.keep_separator)

        # Now go merging things, recursively splitting longer texts.
        _good_splits = []
        _separator = "" if self.keep_separator else separator
        for s in splits:
            if self._token_size(s) < self.chunk_size:
                _good_splits.append(s)
            else:
                if _good_splits:
                    merged_text = self._merge(_good_splits, _separator)
                    final_chunks.extend(merged_text)
                    _good_splits = []
                if not new_separators:
                    final_chunks.append(s)
                else:
                    other_info = self._split_text(s, new_separators)
                    final_chunks.extend(other_info)
        if _good_splits:
            merged_text = self._merge(_good_splits, _separator)
            final_chunks.extend(merged_text)
        return final_chunks

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, self.separators)

    def _split_text_with_regex(
        self,
        text: str, 
        separator: str, 
        keep_separator: bool
    ) -> List[str]:
        # Now that we have the separator, split the text
        if separator:
            if keep_separator:
                # The parentheses in the pattern keep the delimiters in the result.
                _splits = re.split(f"({separator})", text)
                splits = [_splits[i] + _splits[i + 1] for i in range(1, len(_splits), 2)]
                if len(_splits) % 2 == 0:
                    splits += _splits[-1:]
                splits = [_splits[0]] + splits
            else:
                splits = re.split(separator, text)
        else:
            splits = list(text)
        return [s for s in splits if s != ""]
    
    def _merge(self, splits: Iterable[str], separator: str) -> List[str]:
        # We now want to combine these smaller pieces into medium size
        # chunks to send to the LLM.
        separator_len = self._token_size(separator)

        docs = []
        current_doc: List[str] = []
        total = 0
        for d in splits:
            _len = self._token_size(d)
            if (
                total + _len + (separator_len if len(current_doc) > 0 else 0)
                > self.chunk_size
            ):
                if total > self.chunk_size:
                    logger.warning(
                        f"Created a chunk of size {total}, "
                        f"which is longer than the specified {self.chunk_size}"
                    )
                if len(current_doc) > 0:
                    doc = self._join_docs(current_doc, separator)
                    if doc is not None:
                        docs.append(doc)
                    # Keep on popping if:
                    # - we have a larger chunk than in the chunk overlap
                    # - or if we still have any chunks and the length is long
                    while total > self.chunk_overlap or (
                        total + _len + (separator_len if len(current_doc) > 0 else 0)
                        > self.chunk_size
                        and total > 0
                    ):
                        total -= self._token_size(current_doc[0]) + (
                            separator_len if len(current_doc) > 1 else 0
                        )
                        current_doc = current_doc[1:]
            current_doc.append(d)
            total += _len + (separator_len if len(current_doc) > 1 else 0)
        doc = self._join_docs(current_doc, separator)
        if doc is not None:
            docs.append(doc)
        return docs
    
    def _join_docs(self, docs: List[str], separator: str) -> Optional[str]:
        text = separator.join(docs)
        if self.strip_whitespace:
            text = text.strip()
        if text == "":
            return None
        else:
            return text

    def _token_size(self, text: str) -> int:
        return len(self.tokenizer(text))