import logging
from dataclasses import dataclass
from typing import List, Optional

from src.bridge.pydantic import BaseModel
from src.callbacks import CallbackManager
from src.embeddings import BaseEmbedding
from src.embeddings.utils import EmbedType

from src.node_parser.text.sentence import SentenceSplitter, DEFAULT_CHUNK_SIZE,SENTENCE_CHUNK_OVERLAP
from src.node_parser import TextSplitter
from .schema import TransformComponent

logger = logging.getLogger(__name__)


def _get_default_node_parser(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = SENTENCE_CHUNK_OVERLAP,
    callback_manager: Optional[CallbackManager] = None,
) -> SentenceSplitter:
    """Get default node parser."""
    return SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        callback_manager=callback_manager or CallbackManager(),
    )


class ServiceContextData(BaseModel):
    llm: dict
    llm_predictor: dict
    prompt_helper: dict
    embed_model: dict
    transformations: List[dict]


@dataclass
class ServiceContext:
    """Service Context container.

    The service context container is a utility container for LlamaIndex
    index and query classes. It contains the following:
    - llm_predictor: BaseLLMPredictor
    - prompt_helper: PromptHelper
    - embed_model: BaseEmbedding
    - node_parser: TextNodesParser
    - callback_manager: CallbackManager

    """

    embed_model: BaseEmbedding
    transformations: List[TransformComponent]
    callback_manager: CallbackManager

    @classmethod
    def from_defaults(
        cls,
        embed_model: Optional[EmbedType] = "default",
        node_parser: Optional[SentenceSplitter] = None,
        text_splitter: Optional[TextSplitter] = None,
        transformations: Optional[List[TransformComponent]] = None,
        callback_manager: Optional[CallbackManager] = None,
        # node parser kwargs
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> "ServiceContext":
        """Create a ServiceContext from defaults.
        If an argument is specified, then use the argument value provided for that
        parameter. If an argument is not specified, then use the default value.

        You can change the base defaults by setting llama_index.global_service_context
        to a ServiceContext object with your desired settings.

        Args:
            llm_predictor (Optional[BaseLLMPredictor]): LLMPredictor
            prompt_helper (Optional[PromptHelper]): PromptHelper
            embed_model (Optional[BaseEmbedding]): BaseEmbedding
                or "local" (use local model)
            node_parser (Optional[TextNodesParser]): TextNodesParser
            chunk_size (Optional[int]): chunk_size
            callback_manager (Optional[CallbackManager]): CallbackManager
            system_prompt (Optional[str]): System-wide prompt to be prepended
                to all input prompts, used to guide system "decision making"
            query_wrapper_prompt (Optional[BasePromptTemplate]): A format to wrap
                passed-in input queries.

        """

        callback_manager = callback_manager or CallbackManager([])

        # NOTE: the embed_model isn't used in all indices
        # NOTE: embed model should be a transformation, but the way the service
        # context works, we can't put in there yet.
        embed_model = embed_model
        embed_model.callback_manager = callback_manager

        if text_splitter is not None and node_parser is not None:
            raise ValueError("Cannot specify both text_splitter and node_parser")

        node_parser = (
            text_splitter  # text splitter extends node parser
            or node_parser
            or _get_default_node_parser(
                chunk_size=chunk_size or DEFAULT_CHUNK_SIZE,
                chunk_overlap=chunk_overlap or SENTENCE_CHUNK_OVERLAP,
                callback_manager=callback_manager,
            )
        )

        transformations = transformations or [node_parser]

        return cls(
            embed_model=embed_model,
            transformations=transformations,
            callback_manager=callback_manager,
        )

    @classmethod
    def from_service_context(
        cls,
        service_context: "ServiceContext",
        embed_model: Optional[EmbedType] = "default",
        node_parser: Optional[SentenceSplitter] = None,
        text_splitter: Optional[TextSplitter] = None,
        transformations: Optional[List[TransformComponent]] = None,
        callback_manager: Optional[CallbackManager] = None,
        # node parser kwargs
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> "ServiceContext":
        """Instantiate a new service context using a previous as the defaults."""

        callback_manager = callback_manager or service_context.callback_manager
        # NOTE: the embed_model isn't used in all indices
        # default to using the embed model passed from the service context
        if embed_model == "default":
            embed_model = service_context.embed_model
        embed_model = embed_model 
        embed_model.callback_manager = callback_manager

        transformations = transformations or []
        node_parser_found = False
        for transform in service_context.transformations:
            if isinstance(transform, SentenceSplitter):
                node_parser_found = True
                node_parser = transform
                break

        if text_splitter is not None and node_parser is not None:
            raise ValueError("Cannot specify both text_splitter and node_parser")

        if not node_parser_found:
            node_parser = (
                text_splitter  # text splitter extends node parser
                or node_parser
                or _get_default_node_parser(
                    chunk_size=chunk_size or DEFAULT_CHUNK_SIZE,
                    chunk_overlap=chunk_overlap or SENTENCE_CHUNK_OVERLAP,
                    callback_manager=callback_manager,
                )
            )

        transformations = transformations or service_context.transformations

        return cls(
            embed_model=embed_model,
            transformations=transformations,
            callback_manager=callback_manager,
        )


    @property
    def node_parser(self) -> SentenceSplitter:
        """Get the node parser."""
        for transform in self.transformations:
            if isinstance(transform, SentenceSplitter):
                return transform
        raise ValueError("No node parser found.")

    def to_dict(self) -> dict:
        """Convert service context to dict."""
        embed_model_dict = self.embed_model.to_dict()
        tranform_list_dict = [x.to_dict() for x in self.transformations]

        return ServiceContextData(
            embed_model=embed_model_dict,
            transformations=tranform_list_dict,
        ).dict()
