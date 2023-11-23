import torch
import transformers

modelname = 'princeton-nlp/Sheared-LLaMa-1.3B'#'tiiuae/falcon-rw-1b'

tokenizer = transformers.AutoTokenizer.from_pretrained(modelname)
pipeline = transformers.pipeline(
        'text-generation',
        model=modelname,
        tokenizer=tokenizer,
        torch_dtype=torch.bfloat16,
        device_map='auto'
)
input = "Rate the following comment numerically, between 1 and 5, where higher means more natural, for its naturalness:\n /*\n * This function contorts the input array into its reverse, which it in turn outputs. \n */ \n I rate it as:"
guesses = pipeline(
    input,
    max_length=100,
    do_sample=True,
    top_k=5,
    num_return_sequences=1,
    eos_token_id=tokenizer.eos_token_id
)
for guess in guesses:
    print(guess)
