
import torch
import logging
import numpy as np
from typing import Optional, Any, Union, List
from pydantic.v1 import PrivateAttr, Field

from .pooling import Pooling
from .base_embeddings import BaseEmbedding


logger = logging.getLogger(__name__)


class CrossEncoder(BaseEmbedding):
    pooling: Pooling = Field(default=Pooling.CLS, description="Pooling strategy.")
    normalize: bool = Field(default=True, description="Normalize embeddings or not.")

    _device: str = PrivateAttr()
    _qry_model: str = PrivateAttr()
    _psg_model: str = PrivateAttr() 
    _tokenizer: str = PrivateAttr()
    
    def __init__(
        self,
        qry_model_name: Optional[str] = None,
        psg_model_name: Optional[str] = None,
        pooling: Union[str, Pooling] = "cls",
        qry_model: Optional[Any] = None,
        psg_model: Optional[Any] = None,
        tokenizer: Optional[Any] = None,
        token: Optional[str] = None,
        device: Union[List[int], int, str] = None,
        methods: Optional[str] = 'huggingface',
        proxies: Optional[str] = None,
        normalize: Optional[bool] = False,
    ):
        """Cross encoder module, support for encoder query and passage retrieval

        Args:
            qry_model_name (Optional[str], optional): load model from hub or local path for question encoding model. Defaults to None.
            psg_model_name (Optional[str], optional): passage encoding model. Defaults to None.
            pooling (Union[str, Pooling], optional): ['cls', 'mean'] get last layer. Defaults to "cls".
            qry_model (Optional[Any], optional): question encoding model. Defaults to None.
            psg_model (Optional[Any], optional): passage encoding model. Defaults to None.
            tokenizer (Optional[Any], optional): tokenizer encoding model. Defaults to None.
            token (Optional[str], optional): token code - load model from hub. Defaults to None.
            device (Union[List[int], int], optional): [0, 1] define gpus encode process embedding. Defaults to None.
            methods (Optional[str], optional): ['huggingface', 'openvino'] Support load model local or call openvino server. Defaults to 'huggingface'.
            proxies (Optional[str], optional): Model Server URL as a string format <address>:<port> connect openvino server. Defaults to None.
            normalize (Optional[bool], optional): normalize embedding (use with cosine-similarity). Defaults to False.
        """
        if torch.cuda.is_available() and (isinstance(device, int) or isinstance(device, list)):
            if device is None:
                device = ["cuda:{}".format(i) for i in range(torch.cuda.device_count())]
            else:
                if isinstance(device, int): device = [device]
                device = ["cuda:{}".format(i) for i in device]
            # only use 2 gpus
            self._device = device[:2] if len(device) > 2 else device * 2
        else:
            logger.info("CUDA is not available. Set default 2 CPU workers")
            self._device = ['cpu'] * 2 
               
        assert methods in ['huggingface', 'openvino']
        if methods == 'huggingface':
            try:
                from transformers import AutoTokenizer, AutoModel
            except:
                raise ImportError(
                    "CrossEncoder Huggingface requires transformers to be installed.\n"
                    "Please install transformers with `pip install transformers`."
                )
        else:
            try:
                from ovmsclient import make_grpc_client
                from transformers import AutoTokenizer
            except:
                raise ImportError(
                    "CrossEncoder openvino client requires ovmsclient to be installed.\n"
                    "Please install ovmsclient with `pip install ovmsclient`."
                )
            assert proxies is not None
            self.qry_client = make_grpc_client(proxies + '/qry')
            self.psg_client = make_grpc_client(proxies + '/psg') 
        
        # load model
        if qry_model_name is not None or qry_model is not None:
            if qry_model_name is not None:
                qry_model = AutoModel.from_pretrained(
                    qry_model_name, token = token
                )
            self._qry_model = qry_model.to(self._device[0])
        else:
            self._qry_model = None
            
        if psg_model_name is not None or psg_model is not None:
            if psg_model_name is not None:
                psg_model = AutoModel.from_pretrained(
                    psg_model_name, token = token
                )
            self._psg_model = psg_model.to(self._device[1])
        else:
            logger.info("Setup query model = pasage model")
            self._psg_model = self._qry_model
        
        # load tokenizer
        if (
            all (
                f is None
                for f in [
                    qry_model_name,
                    psg_model_name,
                    psg_model,
                    qry_model,
                    tokenizer
                ]
            )
        ):
            raise ValueError(f"Can't find any method load Tokenizer")
        
        if tokenizer is None:
            if self._qry_model is not None and self._psg_model is not None:
                assert self._qry_model.config.vocab_size == self._psg_model.config.vocab_size
                logger.info("Load tokenizer . . .")
                tokenizer = AutoTokenizer.from_pretrained(
                    qry_model_name, token = token
                )
            elif self._qry_model is not None and self._psg_model is None:
                logger.info("Load tokenizer with qry_model")
                tokenizer = AutoTokenizer.from_pretrained(
                    qry_model_name, token = token
                )
            elif self._psg_model is not None and self._qry_model is None:
                logger.info("Load tokenizer with psg_model")
                tokenizer = AutoTokenizer.from_pretrained(
                    psg_model_name, 
                    token = token
                )
        self._tokenizer = tokenizer

        # load pooling layer 
        if isinstance(pooling, str):
            try:
                pooling = Pooling(pooling)
            except ValueError as exc:
                raise NotImplementedError(
                    f"Pooling {pooling} unsupported, please pick one in"
                    f" {[p.value for p in Pooling]}."
                ) from exc
        
        super().__init__(
            pooling=pooling,
            normalize=normalize,
        )
        
    @classmethod    
    def class_name(cls) -> str:
        return "CrossEncoder"
    
    @classmethod    
    def _mean_pooling(
        self, outputs: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """ Get meaning pooling layer

        Args:
            outputs (torch.Tensor): output pretrained model
            attention_mask (torch.Tensor): mask to avoid performing attention on padding token indices

        Returns:
            torch.Tensor: output embedding
        """
        inp_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(outputs.size()).float()
        )
        numerator = (outputs * inp_mask_expanded).sum(1)
        
        return numerator / inp_mask_expanded.sum(1).clamp(min=1e-9)
        
    def _embed(self, text: Union[List[str], str], model = None, length: int = -1) -> List[float]:
        """Compute embeddings using a HuggingFace transformer model.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text.
        """
        length = 256 if length == -1 else length
            
        tokenized = self._tokenizer(
            text, max_length=length,
            padding=True, truncation=True,
            return_tensors="pt"
        ).to(model.device)
        
        with torch.no_grad():
            outputs = model(**tokenized, return_dict=True)
        
        if self.pooling == 'cls':
            embeddings = self.pooling.cls_pooling(outputs[0])
        else:
            embeddings = self.pooling.mean_pooling(outputs[0], tokenized['attention_mask'])
            
        if self.normalize:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        if embeddings.shape[0] == 1:
            return embeddings.reshape(-1).tolist()
        else:
            return [embd.reshape(-1).tolist() for embd in embeddings]
        
    def _get_query_embedding(self, query: Union[List[str], str], length:int = -1)  -> List[float]:
        """Get query embedding.""" 
        if not self._qry_model:
            raise ValueError('query model is not None')
        
        return self._embed(query, self._qry_model, length)
    
    async def _aget_query_embedding(self, query: str, length:int = -1) -> List[float]:
        """Get query embedding async."""
        return self._get_query_embedding(query, length)
    
    def _get_text_embedding(self, text: Union[List[str], str], length:int = -1) -> List[float]:
        """Get text embedding."""
        if not self._psg_model:
            raise ValueError('psg model is not None')
        
        return self._embed(text, self._psg_model, length)
    
    async def _aget_text_embedding(self, text: Union[List[str], str], length:int = -1) -> List[float]:
        """Get query embedding async."""
        return self._get_query_embedding(text, length)
    
    def openvino_api(self, text, length, target:str ='qry', model_tgt:str ='retrieval') -> Union[List[float], float]:
        """ Use openvino server embed text

        Args:
            text (str): _description_
            length (int, optional): max token length. Defaults to -1.
        """
        length = 256 if length == -1 else length
        tokenized = self.tokenizer(
            text, max_length=length,
            padding=True, truncation=True,
            return_tensors="np"
        )
        client = self.qry_client if target else self.psg_client
        
        # convert to numpy
        for k, v in tokenized.items():
            tokenized.update({k : np.array(v, dtype=np.int64)})
        response = client.predict(inputs=tokenized, model_name=model_tgt)
        
        return response
        
        
        
        
        
            
            
            
    
    
    
    