import json
import sys
import random

sys.path.insert(0, r"./")
import pprint
from pprint import PrettyPrinter
from typing import List, Dict
from dataclasses import dataclass, field, asdict, fields
from peft import TaskType


@dataclass
class AdvanceInstructSample:
    """
    A single training/test example for the Instruct dataset.
    """

    qas_id: str
    system_prompt: str

    question_text: str

    orig_answer_texts: str = None
    answer_lengths: int = None

    # example_template = QA_TEMPLATE()

    def __post_init__(self) -> None:
        # Post validate
        self.answer_lengths = (
            len(self.orig_answer_texts) if self.orig_answer_texts is not None else None
        )

    def __str__(self) -> str:
        return self.__repr__

    @property
    def __repr__(self) -> str:
        s = ""
        s += f"\n Question id: {self.qas_id}"
        s += f"\n System prompt: {self.system_prompt}"
        s += f"\n Question: {self.question_text}"
        if self.orig_answer_texts:
            s += f"\n Answer text: {self.orig_answer_texts}"
            s += f"\n Answer length: {self.answer_lengths}"

        return s

    @property
    def get_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def get_keys() -> List[str]:
        all_fields = fields(AdvanceInstructSample)
        return [v.name for v in all_fields]

    @property
    def get_dict_str(self, indent: int = 4) -> None:
        pp = pprint.PrettyPrinter(indent=indent)
        pp.pprint(self.get_dict)

    def get_example(
        self,
        inputs_column: str = "prompt",
        targets_column: str = "target",
        system_prefix: str = "",
        question_prefix: str = "####### Instruction:",
        response_prefix: str = "%%%%%%% Response:",
        is_training: bool = True,
        do_perplexity_eval: bool = False,
        do_generative_eval: bool = False,
        task_type: str = None,
    ) -> Dict:
        assert task_type, "Please specified the task type inorder to get the example"

        system_msg = " " + system_prefix + "\n" + self.system_prompt + "\n\n"
        question_msg = question_prefix + "\n" + self.question_text + "\n\n"
        prompt = system_msg + " " + question_msg
        label = self.orig_answer_texts + "\n"

        if task_type == "SEQ_2_SEQ_LM":
            return {inputs_column: prompt, targets_column: label}
        elif task_type == "CAUSAL_LM":
            if is_training:
                return {inputs_column: prompt + " " + response_prefix + "\n" + label}

            example_dict = {}
            # The perplexity field is for perplexity evaluation, which needed the full prompt and label
            # while the inputs_column only have prompt and response_prefix for model.generate evaluation
            if do_generative_eval:
                example_dict[inputs_column] = prompt + " " + response_prefix + "\n"
                example_dict[targets_column] = label

            if do_perplexity_eval:
                example_dict["perplexity"] = (
                    prompt + " " + response_prefix + "\n" + label
                )

            if not bool(example_dict):
                raise "Evaluation files is provided but don't know what to do with them..."

            return example_dict
        else:
            raise f"This task type {task_type} is not support"
