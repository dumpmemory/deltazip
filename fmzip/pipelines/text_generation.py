import torch
from loguru import logger
from typing import List, Dict, Tuple
from transformers import AutoTokenizer
from timeit import default_timer as timer
from fmzip import AutoFMZipModelForCausalLM, BaseCompressionConfig
from fmzip.modeling.gpt_neox import parallelize_neox

def _get_submodules(model, key):
    parent = model.get_submodule(".".join(key.split(".")[:-1]))
    target_name = key.split(".")[-1]
    target = model.get_submodule(key)
    return parent, target, target_name

class MixedPrecisionModel():
    def __init__(self, base_model: str) -> None:
        compress_config = BaseCompressionConfig(
            bits = 4,
            group_size=128,
            sparsity=1,
            prunen=0,
            prunem=0,
            lossless='gdeflate',
            damp_percent=0.02
        )
        self.tokenizer =  AutoTokenizer.from_pretrained(base_model, use_fast=True)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        self.base_model = AutoFMZipModelForCausalLM.from_pretrained(
            base_model,
            compress_config=compress_config
        )
        self.base_model = self.base_model.to(torch.device('cuda'))
        logger.info("based model loaded")
        parallelize_neox()
        self.model_pool = {}

    def generate(self, queries: List[Tuple]):
        batch = self.prepare_batch(
            queries, self.tokenizer, self.base_model, None
        )
        deltas = [x[1] for x in queries]
        for delta in deltas:
            for key, module in self.model_pool[delta].model.named_modules():
                key_to_base = key
                base_module = _get_submodules(self.base_model, key_to_base)
                setattr(self.base_model, 'delta', module)
        output = self.base_model.generate(**batch)
        print(output)
        return output
    def load_delta(self, delta_model: str):
        logger.info("Loading target model")
        start = timer()
        self.model_pool[delta_model] = AutoFMZipModelForCausalLM.from_compressed(
            delta_model,
            unpack=False,
        )
        end = timer()
        logger.info(f"Loading finished. Takes {end-start} seconds")
        
    def forward(self, **kwargs):
        pass

    def prepare_batch(self, inputs, tokenizer, model, lora_map):
        """Tokenizes inputs and sets the batch_lora_ids for the model."""
        batch = tokenizer([inp[0] for inp in inputs], return_tensors="pt", padding=True)
        batch['input_ids'] = batch['input_ids'].to(torch.device('cuda'))
        batch['attention_mask'] = batch['attention_mask'].to(torch.device('cuda'))
        # inp_loras = [lora_map[inp[1]] for inp in inputs]
        # for _, module in model.named_modules():
        #     module.batch_lora_ids = inp_loras
        return batch