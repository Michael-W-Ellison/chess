"""
LLM Service
Wrapper for llama-cpp-python to handle local LLM inference with optimized loading
Includes response caching for improved performance
"""

from typing import Optional, Dict, Any, Iterator
import logging
from pathlib import Path
import threading
import time
import hashlib

from utils.config import settings
from utils.cache import TTLCache, generate_cache_key, cache_cleanup_scheduler

logger = logging.getLogger("chatbot.llm_service")


class LLMService:
    """
    LLM Service - manages local language model for chatbot responses

    Uses llama-cpp-python to run GGUF format models locally.
    Provides a clean interface for generating responses with personality.
    Optimized for fast loading with mmap and background initialization.
    """

    def __init__(self):
        self.model = None
        self.model_path = settings.get_model_path()
        self.is_loaded = False
        self.is_loading = False
        self.load_error = None
        self.load_start_time = None

        # Model parameters from settings
        self.context_length = settings.MODEL_CONTEXT_LENGTH
        self.max_tokens = settings.MODEL_MAX_TOKENS
        self.temperature = settings.MODEL_TEMPERATURE
        self.n_gpu_layers = settings.MODEL_N_GPU_LAYERS

        # Thread-safe lock for loading
        self._load_lock = threading.Lock()
        self._loading_thread = None

        # Response cache - configurable via settings
        # Only caches identical prompts with same parameters
        cache_ttl = getattr(settings, 'CACHE_TTL_SECONDS', 3600)
        cache_max_size = getattr(settings, 'CACHE_MAX_SIZE', 500)
        self._response_cache = TTLCache(default_ttl=cache_ttl, max_size=cache_max_size)
        self._cache_enabled = getattr(settings, 'ENABLE_RESPONSE_CACHE', True)

        # Register cache for periodic cleanup
        cache_cleanup_scheduler.register_cache(self._response_cache)

    def load_model(self, blocking: bool = True, use_mmap: bool = True) -> bool:
        """
        Load the LLM model into memory with optimizations

        Args:
            blocking: If True, wait for load to complete. If False, load in background.
            use_mmap: If True, use memory-mapped files for faster loading (recommended)

        Returns:
            bool: True if successful (or started), False otherwise
        """
        with self._load_lock:
            if self.is_loaded:
                logger.warning("Model already loaded")
                return True

            if self.is_loading:
                logger.warning("Model is already loading")
                return blocking and self._wait_for_load()

            if blocking:
                return self._load_model_sync(use_mmap)
            else:
                return self._load_model_async(use_mmap)

    def _load_model_sync(self, use_mmap: bool = True) -> bool:
        """
        Synchronous model loading (blocks until complete)

        Args:
            use_mmap: Use memory-mapped files for faster loading

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from llama_cpp import Llama

            logger.info(f"Loading LLM model from: {self.model_path}")
            self.load_start_time = time.time()
            self.is_loading = True

            # Check if model file exists
            if not self.model_path.exists():
                logger.error(f"Model file not found at: {self.model_path}")
                logger.error("Please download a model using: ./scripts/download_model.sh")
                self.is_loading = False
                return False

            # Load model with optimizations
            logger.info("Optimization: Using memory-mapped files for faster loading" if use_mmap else "Optimization: Disabled mmap")

            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.context_length,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False,  # Reduce llama.cpp logging
                use_mmap=use_mmap,  # Memory-mapped files for faster loading
                use_mlock=False,  # Don't lock memory (can cause issues on some systems)
                n_threads=None,  # Auto-detect optimal thread count
            )

            load_time = time.time() - self.load_start_time
            self.is_loaded = True
            self.is_loading = False
            logger.info(f"✓ Model loaded successfully in {load_time:.2f}s")
            logger.info(f"  Context length: {self.context_length}")
            logger.info(f"  GPU layers: {self.n_gpu_layers}")
            logger.info(f"  Memory-mapped: {use_mmap}")

            return True

        except ImportError:
            logger.error("llama-cpp-python not installed!")
            logger.error("Run: pip install llama-cpp-python")
            self.is_loading = False
            self.load_error = "llama-cpp-python not installed"
            return False

        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            self.is_loading = False
            self.load_error = str(e)
            return False

    def _load_model_async(self, use_mmap: bool = True) -> bool:
        """
        Asynchronous model loading (loads in background thread)

        Args:
            use_mmap: Use memory-mapped files for faster loading

        Returns:
            bool: True if loading started, False if couldn't start
        """
        def load_worker():
            """Background worker that loads the model"""
            self._load_model_sync(use_mmap)

        try:
            self._loading_thread = threading.Thread(target=load_worker, daemon=True)
            self._loading_thread.start()
            logger.info("Started background model loading...")
            return True
        except Exception as e:
            logger.error(f"Failed to start background loading: {e}")
            return False

    def _wait_for_load(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for background loading to complete

        Args:
            timeout: Maximum seconds to wait (None = wait forever)

        Returns:
            bool: True if loaded successfully, False on timeout or error
        """
        if self.is_loaded:
            return True

        if not self.is_loading:
            return False

        if self._loading_thread is None:
            return False

        self._loading_thread.join(timeout=timeout)

        return self.is_loaded

    def ensure_loaded(self, timeout: float = 30.0) -> bool:
        """
        Ensure model is loaded, waiting if necessary

        Args:
            timeout: Maximum seconds to wait for loading

        Returns:
            bool: True if model is loaded, False otherwise
        """
        if self.is_loaded:
            return True

        if self.is_loading:
            logger.info("Waiting for model to finish loading...")
            return self._wait_for_load(timeout)

        logger.info("Model not loaded, loading now...")
        return self.load_model(blocking=True)

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
        use_cache: bool = True,
    ) -> str:
        """
        Generate a response from the LLM with optional caching

        Args:
            prompt: The full prompt to send to the model
            max_tokens: Maximum tokens to generate (defaults to settings)
            temperature: Sampling temperature (defaults to settings)
            stop: List of stop sequences
            stream: Whether to stream the response (not implemented yet)
            use_cache: Whether to use response cache (default: True)

        Returns:
            Generated text response

        Raises:
            RuntimeError: If model is not loaded or cannot be loaded
        """
        # Ensure model is loaded (lazy loading)
        if not self.is_loaded:
            logger.info("Model not loaded, attempting lazy load...")
            if not self.ensure_loaded():
                raise RuntimeError(f"Model could not be loaded: {self.load_error or 'Unknown error'}")

        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Use defaults from settings if not provided
        if max_tokens is None:
            max_tokens = self.max_tokens
        if temperature is None:
            temperature = self.temperature

        # Default stop sequences
        if stop is None:
            stop = ["\n\nUser:", "\n\nHuman:", "<|endoftext|>"]

        # Check cache if enabled
        if self._cache_enabled and use_cache:
            cache_key = self._generate_cache_key(prompt, max_tokens, temperature, stop)
            cached_response = self._response_cache.get(cache_key)

            if cached_response is not None:
                logger.debug(f"Cache HIT for prompt: {prompt[:50]}...")
                return cached_response

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

            # Cache the response if caching is enabled
            if self._cache_enabled and use_cache:
                self._response_cache.set(cache_key, text)

            return text

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "I'm having trouble thinking right now. Can you try asking again?"

    def _generate_cache_key(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop: list
    ) -> str:
        """
        Generate a cache key for LLM parameters

        Args:
            prompt: The prompt text
            max_tokens: Max tokens setting
            temperature: Temperature setting
            stop: Stop sequences

        Returns:
            Hash string for cache key
        """
        # Create dictionary of all parameters that affect output
        key_data = {
            'prompt': prompt,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'stop': sorted(stop) if stop else [],
        }

        # Use the utility function to generate hash
        return generate_cache_key(**key_data)

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
            RuntimeError: If model is not loaded or cannot be loaded
        """
        # Ensure model is loaded (lazy loading)
        if not self.is_loaded:
            logger.info("Model not loaded, attempting lazy load...")
            if not self.ensure_loaded():
                raise RuntimeError(f"Model could not be loaded: {self.load_error or 'Unknown error'}")

        if self.model is None:
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

    def clear_cache(self) -> Dict[str, int]:
        """
        Clear the response cache

        Returns:
            Dictionary with cache stats before clearing
        """
        stats = self._response_cache.get_stats()
        self._response_cache.clear()
        logger.info("LLM response cache cleared")
        return stats

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get response cache statistics

        Returns:
            Dictionary with cache statistics
        """
        return self._response_cache.get_stats()

    def set_cache_enabled(self, enabled: bool) -> None:
        """
        Enable or disable response caching

        Args:
            enabled: True to enable, False to disable
        """
        self._cache_enabled = enabled
        logger.info(f"LLM response cache {'enabled' if enabled else 'disabled'}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model

        Returns:
            Dictionary with model information including loading status and cache stats
        """
        load_time = None
        if self.load_start_time and self.is_loaded:
            load_time = time.time() - self.load_start_time

        return {
            "loaded": self.is_loaded,
            "loading": self.is_loading,
            "load_error": self.load_error,
            "load_time": f"{load_time:.2f}s" if load_time else None,
            "model_path": str(self.model_path) if self.model_path else None,
            "context_length": self.context_length,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "gpu_layers": self.n_gpu_layers,
            "cache_enabled": self._cache_enabled,
            "cache_stats": self.get_cache_stats(),
        }


# Global instance
llm_service = LLMService()


# Convenience functions for use in other modules
def load_model(blocking: bool = True, use_mmap: bool = True) -> bool:
    """
    Load the LLM model with optimizations

    Args:
        blocking: If True, wait for load. If False, load in background.
        use_mmap: If True, use memory-mapped files for faster loading.

    Returns:
        bool: True if successful or started
    """
    return llm_service.load_model(blocking=blocking, use_mmap=use_mmap)


def unload_model() -> None:
    """Unload the LLM model"""
    llm_service.unload_model()


def generate_response(prompt: str, **kwargs) -> str:
    """
    Generate a response from the LLM (with lazy loading)

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


def is_model_loading() -> bool:
    """Check if the model is currently loading"""
    return llm_service.is_loading


def get_model_info() -> Dict[str, Any]:
    """Get model information including loading status"""
    return llm_service.get_model_info()
