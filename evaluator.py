import torch
import transformers
from transformers import LlamaForCausalLM, LlamaTokenizer
from huggingface_hub import login
from dependencyParser.parseDependencies import JavaClass, JavaFile, JavaMethod
import pickle
#import jinja2
#notebook_login()
#modelname="meta-llama/Llama-2-7b-chat-hf"
#modelname = 'meta-llama/Llama-2-13b-chat-hf'#'princeton-nlp/Sheared-LLaMa-1.3B'#'tiiuae/falcon-rw-1b'
#login(token='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')

def modelcalls(inputs):
    model_dir = "./llama2/llama/llama-2-7b/llama-7b"
    model = LlamaForCausalLM.from_pretrained(model_dir)
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir)

    pipeline = transformers.pipeline(
        'text-generation',
        model=model_dir,
        tokenizer=tokenizer,
        torch_dtype=torch.float16,
        device_map='auto'
    )
    #input = "Rate the following comment numerically, between 1 and 5, where higher means more natural, for its naturalness:\n /*\n * This function contorts the input array into its reverse, which it in turn outputs. \n */ \n I rate it as: "
    
    outputs = list()
    import pdb
    pdb.set_trace()
    for input in inputs:
        generation =  pipeline(
            input,
            #max_length=100,
            max_new_tokens=500,
            do_sample=True,
            top_k=5,
            num_return_sequences=1,
            eos_token_id=tokenizer.eos_token_id
            )[0]['generated_text']
        newgen = generation[len(input):]
        outputs.append(newgen)
    #for guess in guesses:
    #    print(guess)

def interpretResults(generation):
    try:
        metricRatings = generation.split("\n")
        ratings = dict()
        for metricRating in metricRatings:
            toks = metricRating.split()
            metricName = toks[1][:-1] # Remove : at end
            rating = toks[-1]
            rating = rating.split("/")[0]
            ratings[metricName] = int(rating)
    except:
        return -1 # Failed
    return ratings

def generatePrompt(items):
    if isinstance (items[0], JavaMethod):
        return generateJMPrompt(items)
    elif isinstance (items[0], JavaClass):
        return generateJCPrompt(items)
    elif isinstance (items[0], JavaFile):
        return generateJFPrompt(items)
    else:
        raise Exception("Unknown item type")

def generateJMPrompt(items):
    prompt = """
    Given a Java method, provide feedback on the following header comment generated to summarize its function and interface, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the method.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the method.

    Method:
    void testFileSent() throws Exception {
        JobExecution execution = jobLauncher.run(job,
                new JobParametersBuilder().addLong("time.stamp", System.currentTimeMillis()).toJobParameters());
        assertEquals(BatchStatus.COMPLETED, execution.getStatus());
        // 2 chunks sent to channel (5 items and commit-interval=3)
        assertEquals(2, count);
    }
    Comment:
    /**
     * This method sets a job named job off and asserts that it gets completed. It ensures that the launched job is timestamped. It also asserts that the batch of jobs thereby launched gets completed. It also ensures testFileBefore is executed prior to its completion.
     */
    Feedback:
    * Naturalness: The language used in the comment is rather fluent and is easily readable. 5/5
    * Thoroughness: The comment makes no mention of the assertion that count must equal 2, but is otherwise is thorough. 4/5
    * Non-Repetitiveness: The comment redundantly mentions the job variable name, while also repeating the assertion on completion. 2/5
    * Brevity: The comment is rather long for such a short function. Its discussion of variable names is questionable at best. 2/5
    * Accuracy: The call to testFileBefore is entirely hallucinatory. 2/5

    Method:
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        Log.e(LOGTAG,"in onCreate");
        super.onCreate(savedInstanceState);
        // Keep the screen on
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        // Set up full screen
        addFullScreenListener();
    }
    Comment:
    /**
     * overriding NativeActivity's method of the same name
     * logs that it is being called, calls the parent's eponymous method,
     * get current window, flags window for keeping the screen on, listens for full screen.
     */
    Feedback:
    * Naturalness: The language used in the comment has a very poor presentation that makes it rather inaccessible, with some degree of unneeded technical detail. It fails to present a big-picture understanding of the purpose of the method. It maintains some degree of grammar. 2/5
    * Thoroughness: The comment discusses all aspects of the method. 5/5
    * Non-Repetitiveness: The comment is not repetitive in any manner. 5/5
    * Brevity: The comment discusses the method in unnecessary amounts of detail, going almost token-by-token. 1/5
    * Accuracy: We can only assume that the references to the parent function are accurately presented. The other information presented in the comment is entirely accurate. 5/5
    Method:
    """ + items[0].cleaned_ms + """
    Comment:
    """ + items[1] + """
    Feedback:
    """
    return prompt

def generateJCPrompt(items):
    return ""

def generateJFPrompt(items):
    return ""

if __name__ == "__main__":
    inp = pickle.load(open("docs.pkl","rb"))
    toRate = list(inp.items())
    prompts = [generatePrompt(tr) for tr in toRate]
    generations = modelcalls(prompts)
    metricRatings = [interpretResults(gen) for gen in generations]
    import pdb
    pdb.set_trace()

        
