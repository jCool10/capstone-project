import json
import sys
import random

sys.path.insert(0, r"./")
import pprint
from pprint import PrettyPrinter
from typing import List, Dict
from dataclasses import dataclass, field, asdict, fields

from .response_template import QA_TEMPLATE


@dataclass
class AdvanceQAExample:
    """
    A single training/test example for the QA dataset.
    """

    qas_id: str
    question_text: str

    is_impossible: bool = None
    is_trivial: bool = None

    doc_tokens: List[str] = field(default_factory=list)
    docs_lengths: List[int] = None

    orig_answer_texts: str = None
    answer_lengths: int = None

    # example_template = QA_TEMPLATE()

    def __post_init__(self) -> None:
        # Post validate
        self.is_impossible = True if self.orig_answer_texts is None else False
        self.is_trivial = False if self.orig_answer_texts is None else self.is_trivial

        self.answer_lengths = (
            len(self.orig_answer_texts) if self.orig_answer_texts is not None else None
        )

        if self.doc_tokens:
            self.docs_lengths = [len(doc) for doc in self.doc_tokens]
            random.shuffle(self.doc_tokens)

    def __str__(self) -> str:
        return self.__repr__

    @property
    def __repr__(self) -> str:
        s = ""
        s += f"\n Question id: {self.qas_id}"
        s += f"\n Question: {self.question_text}"
        if self.doc_tokens:
            s += f"\n Doc tokens: {self.straighten_docs(self.doc_tokens)}"
            s += f"\n Doc lengths: {self.docs_lengths}"
        if self.orig_answer_texts:
            s += f"\n Answer text: {self.orig_answer_texts}"
            s += f"\n Answer length: {self.answer_lengths}"
        if self.is_impossible is not None:
            s += f"\n Is impossiple: {self.is_impossible}"
        if self.is_trivial is not None:
            s += f"\n Is trivial: {self.is_trivial} \n"

        return s

    @property
    def get_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def get_keys() -> List[str]:
        all_fields = fields(AdvanceQAExample)
        return [v.name for v in all_fields]

    @property
    def get_dict_str(self, indent: int = 4) -> None:
        pp = pprint.PrettyPrinter(indent=indent)
        pp.pprint(self.get_dict)

    def get_example(
        self,
        is_training: bool = False,
        inputs_column: str = "prompt",
        targets_column: str = "target",
    ) -> Dict:
        if is_training:
            straightened_docs = self.straighten_docs(self.doc_tokens)
            prompt = QA_TEMPLATE().get_random_prompt(
                question=self.question_text, context=straightened_docs
            )
            if not self.is_impossible:
                if self.is_trivial and not self.doc_tokens:
                    label = QA_TEMPLATE().get_random_trivial_response(
                        question=self.question_text, answer=self.orig_answer_texts
                    )
                elif self.doc_tokens:
                    label = QA_TEMPLATE().get_random_norm_response(
                        answer=self.orig_answer_texts
                    )
                else:
                    label = QA_TEMPLATE().get_random_neg_response(
                        question=self.question_text
                    )
            else:
                label = QA_TEMPLATE().get_random_neg_response(
                    question=self.question_text
                )

            return {inputs_column: prompt, targets_column: label}

    @staticmethod
    def straighten_docs(docs_list: List[str]) -> str:
        ctxs = []
        if not docs_list:
            return f"[ERROR]{QA_TEMPLATE().get_no_docs_msg(id=1)}[ERROR]"
        for idx, doc in enumerate(docs_list):
            ctxs.append(f" [CTX{idx}]: {doc} [ECTX{idx}] ")
        return "".join(ctxs)
