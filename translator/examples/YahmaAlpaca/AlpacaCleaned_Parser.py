#!/usr/bin/env python3
"""
AlpacaCleaned VinAI Parser
This script demonstrates how to parse and translate the yahma/alpaca-cleaned dataset
from English to Vietnamese using the high-quality VinAI provider.
"""

import sys
import random
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from tqdm.auto import tqdm

try:
    from google.colab import userdata

    IN_COLAB = True
    print("Running in Google Colab")
except ImportError:
    IN_COLAB = False
    print("Running locally")

from datasets import load_dataset

from configs import BaseConfig
from translator import DataParser
from providers import VinAIProvider

PARSER_NAME = "AlpacaCleaned"


class AlpacaCleaned(DataParser):
    """
    AlpacaCleaned DataParser using VinAI provider for high-quality English to Vietnamese translation.
    This parser processes the yahma/alpaca-cleaned dataset and translates it using the
    vinai/vinai-translate-en2vi model for superior translation quality.
    """

    def __init__(
        self,
        file_path: str,
        output_path: str,
        use_vinai: bool = True,
        sample_size: int = None,
    ):
        """
        Initialize the AlpacaCleaned VinAI parser.

        Args:
            file_path (str): Path to input file (dummy file for this dataset)
            output_path (str): Path where translated dataset will be saved
            use_vinai (bool): Whether to use VinAI provider (True) or fallback to Google (False)
            sample_size (int): Optional - limit the number of examples to process for testing
        """

        self.sample_size = sample_size

        # Initialize the appropriate provider
        if use_vinai:
            try:
                translation_provider = VinAIProvider  # Pass the class, not instance
                provider_name = "VinAI"

            except Exception as e:
                from providers import GoogleProvider

                translation_provider = GoogleProvider  # Pass the class
                provider_name = "Google"
        else:
            from providers import GoogleProvider

            translation_provider = GoogleProvider  # Pass the class
            provider_name = "Google"

        print(f"📋 Using {provider_name} provider for translation")

        # Initialize the parent DataParser with VinAI provider
        super().__init__(
            file_path=file_path,
            output_dir=output_path,
            parser_name=PARSER_NAME,
            target_config=BaseConfig,  # Data config for validation
            target_fields=[
                "question_text",
                "orig_answer_texts",
            ],  # Fields to be translated
            do_translate=True,  # Enable translation
            translator=translation_provider,  # Use VinAI provider
            no_translated_code=True,  # Skip code translation
            verbose=False,  # Show translation progress
            source_lang="en",  # English source language
            target_lang="vi",  # Vietnamese target language
        )

    def read(self) -> None:
        """
        Read the yahma/alpaca-cleaned dataset from HuggingFace.
        """
        # Call parent read function for validation
        super(AlpacaCleaned, self).read()

        try:
            # Load the dataset
            self.data_read = load_dataset("yahma/alpaca-cleaned")

            # Get total count
            total_examples = sum(len(self.data_read[split]) for split in self.data_read)
            print(f"✅ Dataset loaded successfully! Total examples: {total_examples:,}")

            # Show split information
            for split in self.data_read:
                count = len(self.data_read[split])
                print(f"   - {split}: {count:,} examples")

        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            raise

        return None

    def convert(self) -> None:
        """
        Convert the dataset to the required format for translation.
        """
        print("🔄 Converting dataset format...")

        # Call parent convert function for validation
        super(AlpacaCleaned, self).convert()

        # Enhanced system prompts in English (will be translated to Vietnamese)
        system_prompts = [
            "You are an AI assistant, provide a detailed response.",
            "Imagine you are a knowledgeable expert, share your insights.",
            "You have vast knowledge, explain this clearly and comprehensively.",
            "As an AI language model, give a thorough and informative answer.",
            "You are here to help, please provide a detailed response.",
            "You possess a wealth of information, offer a complete explanation.",
            "Your purpose is to inform, provide a comprehensive response.",
            "You are designed to assist, offer a detailed and well-structured answer.",
            "You are a virtual assistant, deliver a comprehensive response.",
            "In your role as an AI, provide a detailed explanation.",
            "Help the user understand this topic with a clear explanation.",
            "Provide accurate and helpful information on this subject.",
            "",  # Empty system prompt
            "",  # Empty system prompt
            "",  # Empty system prompt (to give variety)
        ]

        data_converted = []
        total_processed = 0

        for split in self.data_read:
            split_data = self.data_read[split]

            # Apply sample size limit if specified
            if self.sample_size and len(split_data) > self.sample_size:
                print(
                    f"🔢 Limiting {split} to {self.sample_size} examples (from {len(split_data)})"
                )
                split_data = split_data.select(range(self.sample_size))

            print(f"📝 Converting {len(split_data):,} examples from {split} split...")

            for data in tqdm(split_data, desc=f"Converting {split} data"):
                data_dict = {}

                # Randomly assign system prompt
                data_dict["system_prompt"] = random.choice(system_prompts)

                # Generate unique ID
                data_dict["qas_id"] = self.id_generator()

                # Combine instruction and input for question text
                instruction = data["instruction"].strip() if data["instruction"] else ""
                input_text = data["input"].strip() if data["input"] else ""

                if input_text:
                    data_dict["question_text"] = f"{instruction} {input_text}".strip()
                else:
                    data_dict["question_text"] = instruction

                # Set answer text
                data_dict["orig_answer_texts"] = (
                    data["output"] if data["output"] else ""
                )
                data_dict["answer_lengths"] = None

                data_converted.append(data_dict)
                total_processed += 1

        print(f"✅ Conversion completed! Total examples converted: {total_processed:,}")

        # Assign the final data list to self.converted_data
        self.converted_data = data_converted

        return None


if __name__ == "__main__":
    # Simple direct usage pattern
    current_dir = Path(__file__).parent
    dummy_file = current_dir / "dummy.txt"
    output_dir = current_dir

    # Create dummy file if it doesn't exist
    if not dummy_file.exists():
        dummy_file.touch()

    # Initialize parser with VinAI provider
    alpaca_cleaned_parser = AlpacaCleaned(
        file_path=str(dummy_file),
        output_path=str(output_dir),
        use_vinai=True,  # Set to False to use Google Translate
        sample_size=20,  # Set to a number for testing, None for full dataset
    )

    # Execute the three main steps
    alpaca_cleaned_parser.read()
    alpaca_cleaned_parser.convert()
    alpaca_cleaned_parser.save
