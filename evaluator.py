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
    prompt = """
    Given the signature of a Java class, its field assignments, and its methods' signatures, provide feedback on the following header comment generated to summarize its function, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the class.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the class.

    Class Signature:
    public class IntMap<V> extends TreeMap<Integer,V> 
    Field Assignments:
    private static final long serialVersionUID = 1L;
    Method Signatures:
    public int newInt()
    Comment:
    /**
     * This method implements an integer-keyed tree map structure, extending the Java base class of the same name. 
     * It provides a utility to generate new keys.
     */
    Feedback:
    * Naturalness: The language used in the comment is rather fluent and is mostly accessible. The discussion of the extension is not necessary. 4/5
    * Thoroughness: The comment is quite thorough. 5/5
    * Non-Repetitiveness: There is not much repetition in the comment. 5/5
    * Brevity: The discussion of the tree map extension could have been much briefer with more high-level detail. 3/5
    * Accuracy: The comment is accurate to our best ability to tell. 5/5

    Class Signature:
    public abstract class CaptchaStrategy
    Field Assignments:
    protected Context mContext;
    Method Signatures:
    public CaptchaStrategy(Context ctx)
    protected Context getContext()
    public abstract Path getBlockShape(int blockSize)
    public abstract PositionInfo getBlockPostionInfo(int width, int height, int blockSize)
    public PositionInfo getPositionInfoForSwipeBlock(int width, int height, int blockSize)
    public abstract Paint getBlockShadowPaint()
    public abstract Paint getBlockBitmapPaint()
    public void decoreateSwipeBlockBitmap(Canvas canvas, Path shape) 
    Comment:
    /**
     * Creates an interface for captcha implementations. This is done by creating the CaptchaStrategy abstract class. Implements how to get various aspects of a captcha block.
     */
    Feedback:
    * Naturalness: The language of the comment is needlessly technical, although it is otherwise accessible. 3/5
    * Thoroughness: The comment fails to discuss the non-block interfaces provided by the class. 3/5
    * Non-Repetitiveness: The comment needlessly notes how the class provides an interface in two different ways. 2/5
    * Brevity: The comment remains sufficiently high-level for a reader to quickly understand the purpose of. 5/5
    * Accuracy: The comment does not notice how abstract methods are not implemented in Java; meaning that it is not possible for it to implement retrieving these block aspects. The general purpose of the class is still correct. 2/5
    
    Class Signature:
    """ + items[0].signature + """
    Field Assignments:
    """ + "\n".join(items[0].fieldAssigns) + """
    Method Signatures:
    """ + "\n".join([m.signature for m in items[0].methods]) + """
    Comment:
    """ + items[1] + """
    Feedback:
    """
    return prompt
    
def generateJFPrompt(items):
    prompt = """
    Given a Java file's class signatures, provide feedback on the following header comment generated to summarize the file's purpose, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the fuke.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the file.

    Class Signatures:
    public class MainActivity extends Activity
    Comment:
    /**
     * This file contains a file that works to track user clicks in order to generate videos from GIFs upon demand. This class will generate the video corresponding to a GIF upon being clicked on.
     */
    Feedback:
    * Naturalness: The comment is very legible and natural in its language. 5/5
    * Thoroughness: The comment describes the purpose of the only single class present in the file quite well. 5/5
    * Non-Repetitiveness: The comment is rather repetitive, describing the same function twice. 2/5
    * Brevity: The comment is reasonably brief and remains high-level, although it suffers from some repetition. 4/5
    * Accuracy: The comment mistakenly calls the class in the file a file. It is otherwise accurate, to our best ability to provide feedback. 3/5

    Class Signatures:
    public class Parser
    public class Lexer
    Comment:
    /**
     * This file has two classes. Parser: Parses a lexed file in language. Lexer: Lexes a code file in language.
     */
    Feedback:
    * Naturalness: The comment is not very natural in its language and structure, choosing to interrupt the flow of language to subdivide the discussion of the file by classes. It fails to provide any higher-level overview. 2/5
    * Thoroughness: While the file header mentions both classes and their functions in very basic terms, a lot of important details, such as the choice of language and the purpose of these tools are omitted. There is a lack of high-level details. 2/5
    * Non-Repetitiveness: The comment is not repetitive. 5/5
    * Brevity: The comment is very brief. 5/5
    * Accuracy: The comment does not contain any inaccurate information, to our best ability to tell. 5/5
    
    Class Signatures:
    """ + "\n".join([c.signature for c in items[0].classes]) + """
    Comment:
    """ + items[1] + """
    Feedback:
    """
    return prompt
    
if __name__ == "__main__":
    inp = pickle.load(open("docs.pkl","rb"))
    toRate = list(inp.items())
    prompts = [generatePrompt(tr) for tr in toRate]
    generations = modelcalls(prompts)
    metricRatings = [interpretResults(gen) for gen in generations]
    import pdb
    pdb.set_trace()

        
