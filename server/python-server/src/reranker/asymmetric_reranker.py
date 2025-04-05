import torch
import logging
from typing import Optional, Any, List, Union, Dict
from .base_reranker import BaseReranker



logger = logging.getLogger(__name__)


class AsymRanker(BaseReranker):
    def __init__(
        self,
        model_name_or_path: Optional[Any] = None,
        model: Optional[Any] = None,
        tokenizer: Optional[Any] = None,
        token: Optional[str] = None,
        device: Union[int, Any] = None,
        methods: Optional[str] = 'huggingface',
        proxies: Optional[str] = None,
    ):
        super(BaseReranker, self).__init__()
        if torch.cuda.is_available():
            if device is None:
                device = ["cuda:{}".format(i) for i in range(torch.cuda.device_count())]
            elif isinstance(device, int):
                device = "cuda:{}".format(device)
            else:
                device = "cpu"
            self.device = device if isinstance(device, str) else device[0]
        else:
            logger.info("CUDA is not available. Set default 2 CPU workers")
            self.device = 'cpu'
            
        assert methods in ['huggingface', 'openvino']
        if methods == 'huggingface':
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
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
            self.client = make_grpc_client(proxies)
            
        # load model
        if model_name_or_path or model:
            if model_name_or_path:
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_name_or_path, token=token
                )
            self.model = model.to(self.device)
        else:
            self.model = None
            
        # load tokenizer
        if tokenizer is None:
            if model_name_or_path is None:
                raise ValueError('model_name_or_path and tokenizer is None')
            tokenizer = AutoTokenizer.from_pretrained(
                model_name_or_path, token=token
            )
        self.tokenizer = tokenizer
        
    @classmethod
    def class_name(cls) -> str:
        return "CrossEncoder"

    def _get_ranker(
        self,
        query_node: Union[List[str], str] = None,
        text_bundle: Union[List[str], str] = None,
    ) -> Dict[str, str]:
       
        pair_collated = self.tokenizer(
            query_node, text_bundle,
            padding=True, truncation=True,
            return_tensors='pt'
        )
        
        with torch.no_grad():
            outputs = self.model(**pair_collated, return_dict=True)
        score = outputs.logits.cpu().detach()
        
        result = []
        for idx in range(len(query_node)):
            result.append({
                'query' : query_node[idx],
                'text_bundle' : text_bundle[idx],
                'score' : score[idx]
            })
            
        result = sorted(result, key=lambda item: item['score'], reverse=True)
        
        return result