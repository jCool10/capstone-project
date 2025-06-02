import sys

sys.path.insert(0, r"/")
import warnings
from typing import Union, List
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, BitsAndBytesConfig
import torch


try:
    from .base_provider import Provider
    from .utils import throttle
except ImportError:
    from base_provider import Provider
    from utils import throttle

# Suppress warnings from transformers
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")


class VinAIProvider(Provider):
    """
    VinAI Provider using vinai/vinai-translate-en2vi model for English to Vietnamese translation.
    This is a high-quality neural machine translation model specifically designed for EN->VI translation.
    """

    # Class-level cache for model and tokenizer to avoid reloading
    _model_cache = {}
    _tokenizer_cache = {}

    def __init__(
        self,
        model_name: str = "vinai/vinai-translate-en2vi",
        device: str = "auto",
        use_quantization: bool = True,
    ):
        """
        Initialize the VinAI provider.

        Args:
            model_name (str): The model name on HuggingFace Hub. Default is "vinai/vinai-translate-en2vi"
            device (str): Device to run the model on. "auto" for automatic selection, "cpu" or "cuda"
            use_quantization (bool): Whether to use 4-bit quantization to save memory
        """
        super().__init__()

        self.model_name = model_name
        self.use_quantization = use_quantization

        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Create cache key for this configuration
        cache_key = f"{model_name}_{self.device}_{use_quantization}"

        # Check if model and tokenizer are already cached
        if cache_key in self._model_cache and cache_key in self._tokenizer_cache:
            print(f"✅ Using cached VinAI model ({cache_key})")
            self.model = self._model_cache[cache_key]
            self.tokenizer = self._tokenizer_cache[cache_key]
        else:
            print(f"Loading VinAI translation model on {self.device}...")
            if self.use_quantization and self.device != "cpu":
                print("Using 4-bit quantization for memory efficiency...")

            # Load tokenizer and model
            try:
                # Load tokenizer first
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name, use_fast=True
                )

                # Configure quantization if enabled and using GPU
                model_kwargs = {}
                if (
                    self.use_quantization
                    and self.device != "cpu"
                    and torch.cuda.is_available()
                ):
                    try:
                        double_quant_config = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_compute_dtype=torch.bfloat16,
                            bnb_4bit_quant_type="nf4",
                        )
                        model_kwargs.update(
                            {
                                "device_map": "auto",
                                "quantization_config": double_quant_config,
                                "torch_dtype": torch.bfloat16,
                            }
                        )
                        print("✅ 4-bit quantization enabled")
                    except Exception as e:
                        print(
                            f"⚠️ Quantization failed, loading without quantization: {e}"
                        )
                        self.use_quantization = False

                # Load model
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name, **model_kwargs
                )

                # Move to device if not using device_map
                if "device_map" not in model_kwargs:
                    self.model.to(self.device)

                self.model.eval()  # Set to evaluation mode

                # Cache the model and tokenizer
                self._model_cache[cache_key] = self.model
                self._tokenizer_cache[cache_key] = self.tokenizer

                print(f"VinAI model {self.model_name} loaded and cached successfully!")

            except Exception as e:
                raise RuntimeError(
                    f"Failed to load VinAI model {self.model_name}: {str(e)}"
                )

        # Set the translator (required by base class)
        self.translator = self._translate_with_model

    def _translate_text(self, text: str, max_length: int = 512) -> str:
        """
        Translate a single text using the VinAI model.

        Args:
            text (str): Text to translate (in English)
            max_length (int): Maximum length of the generated translation

        Returns:
            str: Translated text in Vietnamese
        """
        if not text or not text.strip():
            return text

        try:
            # Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
            )

            # Move inputs to device if not using device_map
            if not self.use_quantization or self.device == "cpu":
                inputs = {key: value.to(self.device) for key, value in inputs.items()}

            # Generate translation
            with torch.no_grad():
                generate_kwargs = {
                    "max_length": max_length,
                    "num_beams": 5,
                    "length_penalty": 1.0,
                    "early_stopping": True,
                    "num_return_sequences": 1,
                    "do_sample": False,
                }

                # Add decoder start token if the tokenizer supports it
                try:
                    if (
                        hasattr(self.tokenizer, "lang_code_to_id")
                        and "vi_VN" in self.tokenizer.lang_code_to_id
                    ):
                        generate_kwargs["decoder_start_token_id"] = (
                            self.tokenizer.lang_code_to_id["vi_VN"]
                        )
                except:
                    pass  # Continue without special decoder token

                outputs = self.model.generate(**inputs, **generate_kwargs)

            # Decode the output
            translated_texts = self.tokenizer.batch_decode(
                outputs, skip_special_tokens=True
            )

            # Return the first (and only) translation
            translated_text = translated_texts[0] if translated_texts else text
            return translated_text.strip()

        except Exception as e:
            print(f"Error translating text: {e}")
            return text  # Return original text if translation fails

    def _translate_batch(
        self, texts: List[str], max_length: int = 512, batch_size: int = 4
    ) -> List[str]:
        """
        Translate multiple texts in batches for better performance.

        Args:
            texts (List[str]): List of texts to translate (in English)
            max_length (int): Maximum length of the generated translation
            batch_size (int): Number of texts to process in each batch

        Returns:
            List[str]: List of translated texts in Vietnamese
        """
        if not texts:
            return texts

        # Filter out empty texts and keep track of original positions
        text_mapping = []
        non_empty_texts = []

        for i, text in enumerate(texts):
            if text and text.strip():
                text_mapping.append((i, len(non_empty_texts)))
                non_empty_texts.append(text.strip())
            else:
                text_mapping.append((i, -1))  # -1 indicates empty text

        if not non_empty_texts:
            return texts

        translated_results = [""] * len(texts)

        try:
            # Process in batches
            for batch_start in range(0, len(non_empty_texts), batch_size):
                batch_end = min(batch_start + batch_size, len(non_empty_texts))
                batch_texts = non_empty_texts[batch_start:batch_end]

                # Tokenize batch
                inputs = self.tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=max_length,
                )

                # Move inputs to device if not using device_map
                if not self.use_quantization or self.device == "cpu":
                    inputs = {
                        key: value.to(self.device) for key, value in inputs.items()
                    }

                # Generate translations
                with torch.no_grad():
                    generate_kwargs = {
                        "max_length": max_length,
                        "num_beams": 5,
                        "length_penalty": 1.0,
                        "early_stopping": True,
                        "num_return_sequences": 1,
                        "do_sample": False,
                    }

                    # Add decoder start token if the tokenizer supports it
                    try:
                        if (
                            hasattr(self.tokenizer, "lang_code_to_id")
                            and "vi_VN" in self.tokenizer.lang_code_to_id
                        ):
                            generate_kwargs["decoder_start_token_id"] = (
                                self.tokenizer.lang_code_to_id["vi_VN"]
                            )
                    except:
                        pass  # Continue without special decoder token

                    outputs = self.model.generate(**inputs, **generate_kwargs)

                # Decode batch outputs
                batch_translations = self.tokenizer.batch_decode(
                    outputs, skip_special_tokens=True
                )

                # Store batch results
                for i, translation in enumerate(batch_translations):
                    non_empty_texts[batch_start + i] = translation.strip()

            # Map translations back to original positions
            non_empty_index = 0
            for original_pos, mapped_pos in text_mapping:
                if mapped_pos == -1:  # Empty text
                    translated_results[original_pos] = texts[original_pos]
                else:
                    translated_results[original_pos] = non_empty_texts[mapped_pos]

            return translated_results

        except Exception as e:
            print(f"Error in batch translation: {e}")
            # Fallback to individual translation
            return [self._translate_text(text) for text in texts]

    def _translate_with_model(
        self, input_data: Union[str, List[str]], **kwargs
    ) -> Union[str, List[str]]:
        """
        Internal method to translate using the loaded model.
        This method is assigned to self.translator.
        """
        if isinstance(input_data, str):
            return self._translate_text(input_data)
        elif isinstance(input_data, list):
            return self._translate_batch(input_data)
        else:
            raise TypeError(f"Unsupported input type: {type(input_data)}")

    @throttle(
        calls_per_minute=120, verbose=False
    )  # Reasonable throttling for local model
    def _do_translate(
        self,
        input_data: Union[str, List[str]],
        src: str,
        dest: str,
        fail_translation_code: str = "P1OP1_F",
        **kwargs,
    ) -> Union[str, List[str]]:
        """
        Perform translation of input data from source language to destination language.

        Args:
            input_data (Union[str, List[str]]): The input data to be translated
            src (str): Source language code (should be 'en' for English)
            dest (str): Destination language code (should be 'vi' for Vietnamese)
            fail_translation_code (str): Code returned when translation fails

        Returns:
            Union[str, List[str]]: The translated output data
        """

        # VinAI model only supports EN->VI translation
        if src.lower() not in ["en", "eng", "english"]:
            print(
                f"Warning: VinAI model only supports English source language, but got '{src}'. Proceeding anyway."
            )

        if dest.lower() not in ["vi", "vie", "vietnamese"]:
            print(
                f"Warning: VinAI model only supports Vietnamese target language, but got '{dest}'. Proceeding anyway."
            )

        try:
            if isinstance(input_data, str):
                if not input_data.strip():
                    return input_data
                return self._translate_text(input_data)

            elif isinstance(input_data, list):
                if not input_data:
                    return input_data

                results = []
                for text in input_data:
                    if not text or not text.strip():
                        results.append(text)
                    else:
                        translated = self._translate_text(text)
                        results.append(translated)
                return results

            else:
                raise TypeError(f"Unsupported input type: {type(input_data)}")

        except Exception as e:
            print(f"Translation failed: {e}")
            if isinstance(input_data, str):
                return fail_translation_code
            else:
                return [fail_translation_code] * len(input_data)

    def __del__(self):
        """Cleanup method to free GPU memory when the provider is destroyed."""
        try:
            if hasattr(self, "model") and self.model is not None:
                del self.model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        except:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    test = VinAIProvider()
    print(test.translate("Hello", src="en", dest="vi"))
    print(test.translate(["Hello", "How are you today ?"], src="en", dest="vi"))
