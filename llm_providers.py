"""
LLM Provider Abstraction for NeuralQuery.
Supports Google Gemini and custom fine-tuned NeuralQuery Qwen LoRA adapter.
"""

import os
import sys
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

# Safe UTF-8 console output for Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config import Config

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    def generate(self, query: str, sources: List[Dict]) -> str:
        """
        Generate research synthesis based on query and retrieved sources.

        Args:
            query: The user's research query.
            sources: List of retrieved sources with title, url, snippet, content.

        Returns:
            Synthesized research response string.
        """
        pass


class GeminiProvider(BaseLLMProvider):
    """
    Provider utilizing Google Gemini AI models with cascade fallback.
    """

    def __init__(self):
        self._configured = False

    def _ensure_configured(self):
        """Configure Google Generative AI SDK lazily."""
        if not self._configured:
            if not Config.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY is required for GeminiProvider. "
                    "Please set GEMINI_API_KEY in your environment or .env file."
                )
            import google.generativeai as genai
            genai.configure(api_key=Config.GEMINI_API_KEY, transport='rest')
            self._configured = True

    def generate(self, query: str, sources: List[Dict]) -> str:
        """
        Synthesize sources using Gemini models.
        """
        self._ensure_configured()
        import google.generativeai as genai

        print("🤖 Analyzing with Gemini AI...")

        # Prepare context from sources
        if not sources:
            context = "Note: Web search was unavailable. Please answer this query comprehensively based on your internal knowledge only.\n\n"
        else:
            context = "Research Sources:\n\n"
            for i, source in enumerate(sources, 1):
                context += f"--- Source {i}: {source.get('title', 'Untitled')} ---\n"
                context += f"URL: {source.get('url', '')}\n"
                if source.get('content'):
                    context += f"Content: {source['content']}\n\n"
                else:
                    context += f"Summary: {source.get('snippet', '')}\n\n"

        prompt = f"""You are NeuralQuery, an advanced AI research assistant. Your task is to analyze multiple sources and provide a comprehensive, well-structured answer.

User Query: {query}

{context}

Instructions:
1. Synthesize information from ALL sources above
2. Provide a comprehensive answer to the user's query
3. Highlight key findings and important insights
4. If sources present different perspectives, mention them
5. Structure your response clearly with sections if appropriate
6. Be objective and balanced
7. Keep the response informative but concise (300-500 words)
8. Use markdown formatting for better readability

Provide your analysis:"""

        model_names = [
            Config.AI_DEFAULT_MODEL,
            'models/gemini-2.0-flash',
            'models/gemini-flash-latest',
            'models/gemini-pro-latest',
            'models/gemini-2.0-flash-lite-preview',
            'models/gemini-1.5-flash-latest',
            'models/gemma-3-27b-it'
        ]

        # Deduplicate while preserving order
        unique_model_names = []
        for name in model_names:
            if name and name not in unique_model_names:
                unique_model_names.append(name)

        last_error = "No models attempted"
        ai_text = None

        for name in unique_model_names:
            try:
                print(f"🤖 Attempting generation with: {name}")
                model = genai.GenerativeModel(name)

                try:
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=Config.AI_MAX_TOKENS,
                            temperature=Config.AI_TEMPERATURE,
                        ),
                        request_options={"timeout": Config.AI_REQUEST_TIMEOUT}
                    )
                except Exception as e:
                    if "request_options" in str(e) or "unexpected keyword" in str(e).lower():
                        response = model.generate_content(
                            prompt,
                            generation_config=genai.types.GenerationConfig(
                                max_output_tokens=Config.AI_MAX_TOKENS,
                                temperature=Config.AI_TEMPERATURE,
                            )
                        )
                    else:
                        raise e

                if response.candidates:
                    candidate = response.candidates[0]
                    if candidate.finish_reason != 1:  # 1 is SUCCESS/STOP
                        print(f"⚠️ Model {name} stopped early: {candidate.finish_reason}")
                        if candidate.finish_reason == 3:  # BLOCKED_FOR_SAFETY
                            continue

                ai_text = response.text
                if ai_text:
                    print(f"✅ Success with model {name}")
                    break
            except Exception as e:
                last_error = str(e)
                print(f"⚠️ Model {name} failed: {last_error[:100]}")
                continue

        if not ai_text:
            error_msg = str(last_error)
            print(f"❌ AI analysis error: {error_msg}")

            is_quota_error = "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower()
            if is_quota_error:
                friendly_error = "**Note:** NeuralQuery is currently at its limit for free research (Quota Exceeded). This usually resets in about 30-60 seconds. Please try again in a moment."
            else:
                friendly_error = f"I apologize, but I encountered an error while analyzing the sources: {error_msg}"

            if sources:
                source_list = "\n".join([f"- {s.get('title', 'Untitled')}: {s.get('url', '')}" for s in sources[:5]])
                return f"{friendly_error}\n\nHowever, I found {len(sources)} relevant sources that might help answer your query:\n\n{source_list}"

            if is_quota_error:
                return (
                    "**AI Quota Exceeded**\n\n"
                    "NeuralQuery has reached its temporary limit for AI analysis.\n\n"
                    "**Suggestions:**\n"
                    "1. **Wait 1 minute** (The free tier limit is 2-15 requests per minute)\n"
                    "2. Try asking your question again in a moment\n"
                    "3. If this persists, verify your `GEMINI_API_KEY` in `.env`"
                )

            return (
                "**Research Update:**\n\n"
                f"I couldn't search the live web right now and encountered an issue connecting to the AI model ({error_msg}).\n\n"
                "**Suggestions:**\n"
                "1. Wait a moment and try again\n"
                "2. Verify your `GEMINI_API_KEY` in `.env`\n"
                "3. Try asking a simpler question"
            )

        print(f"✅ AI analysis complete ({len(ai_text)} characters)")
        return ai_text


class NeuralQueryProvider(BaseLLMProvider):
    """
    Provider utilizing local fine-tuned Qwen2.5-1.5B-Instruct + LoRA adapter.
    Model weights and tokenizer are loaded lazily on demand.
    """

    def __init__(self):
        self.base_model_name = Config.NEURALQUERY_BASE_MODEL
        self.adapter_path = Config.NEURALQUERY_ADAPTER_PATH
        self.device_setting = Config.NEURALQUERY_DEVICE
        self.fallback_to_gemini = Config.NEURALQUERY_FALLBACK_TO_GEMINI

        self._model = None
        self._tokenizer = None
        self._device = None
        self._is_loaded = False

    def _detect_device(self):
        """Safely detect appropriate computation device and dtype."""
        import torch

        if self.device_setting in ['cuda', 'gpu']:
            if torch.cuda.is_available():
                return 'cuda', torch.float16
            print("⚠️ Warning: CUDA requested via NEURALQUERY_DEVICE but no CUDA device available. Falling back to CPU.")
            return 'cpu', torch.float32

        if self.device_setting == 'mps':
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return 'mps', torch.float16
            return 'cpu', torch.float32

        if self.device_setting == 'cpu':
            return 'cpu', torch.float32

        # Auto detection
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"🚀 Detected GPU: {device_name}. Using CUDA with float16.")
            return 'cuda', torch.float16
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("🍎 Detected Apple Silicon MPS. Using float16.")
            return 'mps', torch.float16
        else:
            print("💻 No GPU detected. Running on CPU with float32. (Inference latency will be higher).")
            return 'cpu', torch.float32

    def _load_model(self):
        """
        Lazily load base model and attach PEFT LoRA adapter.
        """
        if self._is_loaded:
            return

        print(f"\n{'='*60}")
        print("🧠 Initializing NeuralQuery Custom LLM Engine...")
        print(f"   Base Model:   {self.base_model_name}")
        print(f"   Adapter Path: {self.adapter_path}")
        print(f"{'='*60}")

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel
        except ImportError as e:
            raise ImportError(
                f"Missing required ML libraries for NeuralQueryProvider: {e}. "
                f"Install them via: pip install torch transformers peft accelerate safetensors"
            )

        self._device, torch_dtype = self._detect_device()

        # Load Tokenizer
        tokenizer_src = self.adapter_path if os.path.isdir(self.adapter_path) else self.base_model_name
        print(f"📚 Loading tokenizer from: {tokenizer_src}")
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                tokenizer_src,
                trust_remote_code=True,
                padding_side="left"
            )
        except Exception:
            print(f"⚠️ Could not load tokenizer from {tokenizer_src}, falling back to base model {self.base_model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.base_model_name,
                trust_remote_code=True,
                padding_side="left"
            )

        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        # Load Base Model
        print(f"📦 Loading base causal LM: {self.base_model_name} ({torch_dtype})...")
        device_map = "auto" if self._device == "cuda" else None

        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch_dtype,
            device_map=device_map,
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )

        if self._device == 'cpu' and device_map is None:
            base_model = base_model.to('cpu')
        elif self._device == 'mps' and device_map is None:
            base_model = base_model.to('mps')

        # Attach LoRA Adapter
        if not os.path.exists(self.adapter_path):
            raise FileNotFoundError(
                f"Adapter directory not found at: '{self.adapter_path}'. "
                f"Please ensure your fine-tuned LoRA adapter is placed in this path or configure NEURALQUERY_ADAPTER_PATH."
            )

        adapter_weight_safetensors = os.path.join(self.adapter_path, 'adapter_model.safetensors')
        adapter_weight_bin = os.path.join(self.adapter_path, 'adapter_model.bin')

        if not (os.path.exists(adapter_weight_safetensors) or os.path.exists(adapter_weight_bin)):
            print(
                f"⚠️ Notice: Adapter directory '{self.adapter_path}' exists with configs, "
                f"but 'adapter_model.safetensors' weight file was not found. "
                f"Running with base model '{self.base_model_name}' until weights are placed in this directory."
            )
            self._model = base_model
        else:
            print(f"🔗 Attaching fine-tuned PEFT LoRA adapter from: {self.adapter_path}")
            self._model = PeftModel.from_pretrained(
                base_model,
                self.adapter_path,
                is_trainable=False
            )

        self._model.eval()
        self._is_loaded = True
        print("✅ NeuralQuery Custom LLM Engine loaded successfully!\n")

    def _build_prompt(self, query: str, sources: List[Dict]) -> str:
        """
        Construct structured grounded research prompt separating Research Question and Evidence.
        """
        if not sources:
            evidence_text = "No external web sources available. Please respond conservatively, explicitly noting the absence of verified source evidence."
        else:
            evidence_blocks = []
            for idx, source in enumerate(sources, 1):
                title = source.get('title', 'Untitled')
                url = source.get('url', '')
                content = source.get('content') or source.get('snippet', '')
                evidence_blocks.append(
                    f"[Source {idx}]: {title}\nURL: {url}\nEvidence Content:\n{content.strip()}\n"
                )
            evidence_text = "\n".join(evidence_blocks)

        system_instruction = (
            "You are NeuralQuery, an expert AI research intelligence engine specialized in grounded evidence synthesis.\n\n"
            "CRITICAL OPERATIONAL CONSTRAINTS:\n"
            "1. Answer using ONLY the provided evidence. Prioritize verified, supported information.\n"
            "2. If sources present conflicting claims, explicitly identify the disagreement and cite the differing sources.\n"
            "3. Ignore irrelevant or tangential information that does not answer the user's research question.\n"
            "4. REJECT unsupported claims: If the evidence does not contain sufficient facts to answer a question or claim, "
            "explicitly state that the evidence does not support it. Do NOT speculate or invent facts from general knowledge.\n"
            "5. Communicate uncertainty clearly when evidence is incomplete, ambiguous, or speculative.\n"
            "6. DO NOT invent URLs or fabricate citations. Attribute claims clearly to [Source X].\n"
            "7. Provide a structured, coherent research synthesis in markdown format."
        )

        user_content = f"""Research Question:
{query}

Retrieved Evidence:
{evidence_text}

Produce a rigorous, grounded research analysis adhering to all grounding constraints:"""

        # Format using Qwen Chat Template
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ]

        if hasattr(self._tokenizer, 'apply_chat_template'):
            prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            prompt = (
                f"<|im_start|>system\n{system_instruction}<|im_end|>\n"
                f"<|im_start|>user\n{user_content}<|im_end|>\n"
                f"<|im_start|>assistant\n"
            )

        return prompt

    def generate(self, query: str, sources: List[Dict]) -> str:
        """
        Execute grounded generation using fine-tuned Qwen LoRA adapter.
        """
        try:
            self._load_model()
        except Exception as e:
            error_msg = f"Failed to initialize NeuralQuery LLM: {e}"
            print(f"❌ {error_msg}")

            if self.fallback_to_gemini:
                print("🔄 Falling back to GeminiProvider (as configured in NEURALQUERY_FALLBACK_TO_GEMINI)...")
                try:
                    gemini_fallback = GeminiProvider()
                    return gemini_fallback.generate(query, sources)
                except Exception as fb_err:
                    print(f"❌ Gemini fallback also failed: {fb_err}")
                    return (
                        f"**NeuralQuery Provider Error:**\n\n"
                        f"{error_msg}\n\n"
                        f"*(Gemini fallback also failed: {fb_err})*\n\n"
                        f"**Troubleshooting:**\n"
                        f"- Verify model weights exist at `{self.adapter_path}`\n"
                        f"- Check PyTorch and Transformers installation\n"
                        f"- Set `MODEL_PROVIDER=gemini` and check `GEMINI_API_KEY` in `.env`"
                    )

            # Informative error message without silent blank returns
            return (
                f"### ⚠️ NeuralQuery Model Loading Error\n\n"
                f"The custom NeuralQuery model could not be loaded:\n"
                f"> **Details:** {e}\n\n"
                f"**Diagnostics & Steps to Resolve:**\n"
                f"1. **Check Dependencies:** Ensure required ML packages are installed: `pip install torch transformers peft accelerate safetensors`\n"
                f"2. **Check Adapter Weights:** Verify that `adapter_model.safetensors` exists in `{self.adapter_path}`.\n"
                f"3. **Hardware / Memory:** If running on CPU, verify sufficient system RAM (min 8GB). If CUDA, check GPU VRAM.\n"
                f"4. **Fallback:** To allow automatic fallback to Gemini on error, set `NEURALQUERY_FALLBACK_TO_GEMINI=true` in `.env`."
            )

        try:
            import torch

            print(f"🔬 Running grounded synthesis with NeuralQuery LLM on {self._device}...")
            prompt = self._build_prompt(query, sources)

            inputs = self._tokenizer(prompt, return_tensors="pt")
            if self._device in ['cuda', 'mps']:
                inputs = {k: v.to(self._device) for k, v in inputs.items()}

            input_length = inputs['input_ids'].shape[1]

            with torch.no_grad():
                output_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=min(Config.AI_MAX_TOKENS, 1024),
                    temperature=max(Config.AI_TEMPERATURE, 0.1),
                    do_sample=(Config.AI_TEMPERATURE > 0.1),
                    top_p=0.9,
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                )

            generated_ids = output_ids[0][input_length:]
            response_text = self._tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

            if not response_text:
                response_text = (
                    "**NeuralQuery Synthesis:** The retrieved evidence was processed, but generated an empty synthesis. "
                    "Please refine your research query."
                )

            print(f"✅ NeuralQuery synthesis complete ({len(response_text)} chars)")
            return response_text

        except Exception as e:
            error_msg = f"Inference execution error: {e}"
            print(f"❌ {error_msg}")

            if self.fallback_to_gemini:
                print("🔄 Falling back to GeminiProvider after generation error...")
                try:
                    return GeminiProvider().generate(query, sources)
                except Exception as fb_err:
                    print(f"❌ Gemini fallback also failed: {fb_err}")

            return (
                f"### ⚠️ NeuralQuery Inference Error\n\n"
                f"An error occurred during model generation:\n"
                f"> **Error:** {e}\n\n"
                f"Retrieved {len(sources)} sources successfully, but synthesis could not be completed."
            )


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function returning the configured LLM provider.
    Inspects Config.MODEL_PROVIDER.
    """
    provider_name = (Config.MODEL_PROVIDER or 'gemini').strip().lower()

    if provider_name == 'neuralquery':
        print("⚙️  Using LLM Provider: NeuralQuery (Qwen2.5-1.5B + LoRA Adapter)")
        return NeuralQueryProvider()
    elif provider_name == 'gemini':
        print("⚙️  Using LLM Provider: Google Gemini (Cloud API)")
        return GeminiProvider()
    else:
        print(f"⚠️ Unknown MODEL_PROVIDER '{provider_name}'. Defaulting to Gemini.")
        return GeminiProvider()
