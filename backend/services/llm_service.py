"""
LLM Service
Wrapper for llama-cpp-python to handle local LLM inference
"""

from typing import Optional, Dict, Any, Iterator
import logging
from pathlib import Path

from utils.config import settings

logger = logging.getLogger("chatbot.llm_service")


class LLMService:
    """
    LLM Service - manages local language model for chatbot responses

    Uses llama-cpp-python to run GGUF format models locally.
    Provides a clean interface for generating responses with personality.
    """

    def __init__(self):
        self.model = None
        self.model_path = settings.get_model_path()
        self.is_loaded = False

        # Model parameters from settings
        self.context_length = settings.MODEL_CONTEXT_LENGTH
        self.max_tokens = settings.MODEL_MAX_TOKENS
        self.temperature = settings.MODEL_TEMPERATURE
        self.n_gpu_layers = settings.MODEL_N_GPU_LAYERS

    def load_model(self) -> bool:
        """
        Load the LLM model into memory

        Returns:
            bool: True if successful, False otherwise
        """
        if self.is_loaded:
            logger.warning("Model already loaded")
            return True

        try:
            from llama_cpp import Llama

            logger.info(f"Loading LLM model from: {self.model_path}")

            # Check if model file exists
            if not self.model_path.exists():
                logger.error(f"Model file not found at: {self.model_path}")
                logger.error("Please download a model using: ./scripts/download_model.sh")
                return False

            # Load model
            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.context_length,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,  # Reduce llama.cpp logging
            )

            self.is_loaded = True
            logger.info(f"✓ Model loaded successfully")
            logger.info(f"  Context length: {self.context_length}")
            logger.info(f"  GPU layers: {self.n_gpu_layers}")

            return True

        except ImportError:
            logger.error("llama-cpp-python not installed!")
            logger.error("Run: pip install llama-cpp-python")
            return False

        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            return False

    def unload_model(self) -> None:
        """
        Unload the model from memory
        Useful for cleanup on shutdown
        """
        if self.model is not None:
            logger.info("Unloading LLM model...")
            self.model = None
            self.is_loaded = False
            logger.info("✓ Model unloaded")

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[list] = None,
        stream: bool = False,
    ) -> str:
        """
        Generate a response from the LLM

        Args:
            prompt: The full prompt to send to the model
            max_tokens: Maximum tokens to generate (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            stop: List of stop sequences
            stream: Whether to stream the response (not implemented yet)

        Returns:
            Generated text response

        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Use defaults from settings if not provided
        if max_tokens is None:
            max_tokens = self.max_tokens
        if temperature is None:
            temperature = self.temperature

        # Default stop sequences
        if stop is None:
            stop = ["\n\nUser:", "\n\nHuman:", "<|endoftext|>"]

        try:
            logger.debug(f"Generating response (max_tokens={max_tokens}, temp={temperature})")

            # Generate response
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                echo=False,  # Don't include prompt in output
            )

            # Extract text from response
            if isinstance(response, dict) and "choices" in response:
                text = response["choices"][0]["text"].strip()
            else:
                text = str(response).strip()

            logger.debug(f"Generated {len(text)} characters")

            return text

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "I'm having trouble thinking right now. Can you try asking again?"

    def generate_stream(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stop: Optional[list] = None,
    ) -> Iterator[str]:
        """
        Generate a streaming response from the LLM (token by token)

        Args:
            prompt: The full prompt to send to the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: List of stop sequences

        Yields:
            Generated text tokens

        Raises:
            RuntimeError: If model is not loaded
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        if max_tokens is None:
            max_tokens = self.max_tokens
        if temperature is None:
            temperature = self.temperature
        if stop is None:
            stop = ["\n\nUser:", "\n\nHuman:", "<|endoftext|>"]

        try:
            logger.debug("Starting streaming generation")

            # Generate with streaming
            for output in self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
                stream=True,
                echo=False,
            ):
                if isinstance(output, dict) and "choices" in output:
                    token = output["choices"][0]["text"]
                    if token:
                        yield token

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}", exc_info=True)
            yield "I'm having trouble thinking right now. Can you try asking again?"

    def get_embedding(self, text: str) -> list[float]:
        """
        Get embedding vector for text (if model supports it)

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding

        Raises:
            RuntimeError: If model is not loaded
            NotImplementedError: If model doesn't support embeddings
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            embedding = self.model.embed(text)
            return embedding
        except AttributeError:
            raise NotImplementedError("Model does not support embeddings")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model

        Returns:
            Dictionary with model information
        """
        return {
            "loaded": self.is_loaded,
            "model_path": str(self.model_path) if self.model_path else None,
            "context_length": self.context_length,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "gpu_layers": self.n_gpu_layers,
        }


# Global instance
llm_service = LLMService()


# Convenience functions for use in other modules
def load_model() -> bool:
    """Load the LLM model"""
    return llm_service.load_model()


def unload_model() -> None:
    """Unload the LLM model"""
    llm_service.unload_model()


def generate_response(prompt: str, **kwargs) -> str:
    """
    Generate a response from the LLM

    Args:
        prompt: The prompt to generate from
        **kwargs: Additional arguments for generation

    Returns:
        Generated response text
    """
    return llm_service.generate(prompt, **kwargs)


def is_model_loaded() -> bool:
    """Check if the model is loaded"""
    return llm_service.is_loaded


def get_model_info() -> Dict[str, Any]:
    """Get model information"""
    return llm_service.get_model_info()
