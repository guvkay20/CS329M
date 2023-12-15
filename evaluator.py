import torch
import transformers
import pdb
#from transformers import LlamaForCausalLM, LlamaTokenizer
#from huggingface_hub import login
from dependencyParser.parseDependencies import JavaClass, JavaFile, JavaMethod
import pickle
from openai import OpenAI
import json
from tqdm import tqdm
import sys
#import jinja2
#notebook_login()
#modelname="meta-llama/Llama-2-7b-chat-hf"
#modelname = 'meta-llama/Llama-2-13b-chat-hf'#'princeton-nlp/Sheared-LLaMa-1.3B'#'tiiuae/falcon-rw-1b'
#login(token='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')

def modelcalls(inputs):
    # UNCOMMENT FOR LLAMA USE NOTE
    #model_dir = "./llama2/llama/llama-2-7b/llama-7b"
    #model = LlamaForCausalLM.from_pretrained(model_dir)
    #tokenizer = transformers.AutoTokenizer.from_pretrained(model_dir)
    pipeline = transformers.pipeline(
        'text-generation',
        model=model_dir,
        tokenizer=tokenizer,
        torch_dtype=torch.float16,
        device_map='auto'
    )
    #input = "Rate the following comment numerically, between 1 and 5, where higher means more natural, for its naturalness:\n /*\n * This function contorts the input array into its reverse, which it in turn outputs. \n */ \n I rate it as: "
    
    outputs = list()
    #import pdb
    #pdb.set_trace()
    for input in inputs:
        generation =  pipeline(
            input,
            #max_length=100,
            max_new_tokens=max_new_toks,
            do_sample=True,
            top_k=5,
            num_return_sequences=1,
            eos_token_id=tokenizer.eos_token_id
            )[0]['generated_text']
        newgen = generation[len(input):]
        outputs.append(newgen)
    #for guess in guesses:
    #    print(guess)
    return outputs
    
def gptcalls(inputs, max_new_toks=500):
    pdb.set_trace()

    client = OpenAI()
    outputs = list()
    gptcache = pickle.load(open("gptcache.pkl","rb"))
    for input in tqdm(inputs):
        try:
            #messages = [
            #        {"role":"system", "content":"You are math computer."},
            #        {"role":"user","content":"derivative of e^x wrt x?"},
            #        {"role":"assistant","content":"e^x"},
            #        {"role":"user","content":"2+2=?"}
            #]
            messages = input
            if json.dumps(messages,sort_keys=True) in gptcache.keys():
                response = gptcache[json.dumps(messages,sort_keys=True)]
            else:
                response = client.chat.completions.create(
                    model = "gpt-3.5-turbo-1106",
                    messages = messages,
                    max_tokens=500
                )
                gptcache[json.dumps(messages,sort_keys=True)] = response
                print(response.usage)
            out = response.choices[0].message.content
            outputs.append(out) # only the generation
        except:
            outputs.append(-1)
    pickle.dump(gptcache, open("gptcache.pkl","wb"))
    return outputs

def interpretResults(generation):
    #pdb.set_trace()
    try:
        metricRatings = generation.split("\n")
        ratings = dict()
        for metricRating in metricRatings:
            try:
                metricRating = metricRating.strip()
                toks = metricRating.split()
                if toks[0][0]=="*" and toks[1][-1]==":":
                    metricName = toks[1][:-1] # Remove : at end
                    rating = toks[-1]
                    assert(rating[-2:]=="/5")
                    rating = rating.split("/")[0]
                    ratings[metricName] = int(rating)
                elif toks[0][0]=="-" and toks[1][-1]==":":
                    metricName = toks[1][:-1] # Remove : at end
                    rating = toks[-1]
                    assert(rating[-2:]=="/5")
                    rating = rating.split("/")[0]
                    ratings[metricName] = int(rating)
                elif toks[0][-1]==":":
                    metricName = toks[0][:-1] # Remove : at end
                    rating = toks[-1]
                    assert(rating[-2:]=="/5")
                    rating = rating.split("/")[0]
                    ratings[metricName] = int(rating)
            except:
                pass
    except:
        return -1 # Failed
    return ratings

def interpretDoubleResults(generation):
    try:
        metricRatings = generation.split("\n")
        ratings = dict()
        for metricRating in metricRatings:
            try:
                metricRating = metricRating.strip()
                toks = metricRating.split()
                if toks[0][0]=="*" and toks[1][-1]==":":
                    metricName = toks[1][:-1] # Remove : at end
                    rating = toks[-1]
                    assert(rating=="1" or rating=="2")
                    ratings[metricName] = int(rating)
                elif toks[0][0]=="-" and toks[1][-1]==":":
                    metricName = toks[1][:-1] # Remove : at end
                    rating = toks[-1]
                    assert(rating=="1" or rating=="2")
                    ratings[metricName] = int(rating)
                elif toks[0][-1]==":":
                    metricName = toks[0][:-1] # Remove : at end
                    rating = toks[-1]
                    assert(rating=="1" or rating=="2")
                    ratings[metricName] = int(rating)
            except:
                pass
    except:
        return -1 # Failed
    return ratings    

def generatePromptSPSD(items):
    if isinstance (items[0], JavaMethod):
        return generateJMPromptSPSD(items)
    elif isinstance (items[0], JavaClass):
        return generateJCPromptSPSD(items)
    elif isinstance (items[0], JavaFile):
        return generateJFPromptSPSD(items)
    else:
        raise Exception("Unknown item type")

def generatePromptDPSD(items):
    if isinstance (items[0][0], JavaMethod):
        return generateJMPromptDPSD(items)
    elif isinstance (items[0][0], JavaClass):
        return generateJCPromptDPSD(items)
    elif isinstance (items[0][0], JavaFile):
        return generateJFPromptDPSD(items)
    else:
        raise Exception("Unknown item type")
    
def generatePromptDPDD(items):
    if isinstance (items[0][0], JavaMethod):
        return generateJMPromptDPSD(items)
    elif isinstance (items[0][0], JavaClass):
        return generateJCPromptDPDD(items)
    elif isinstance (items[0][0], JavaFile):
        return generateJFPromptDPDD(items)
    else:
        raise Exception("Unknown item type")    

def generatePromptSPDD(items):
    if isinstance (items[0], JavaMethod):
        return generateJMPromptSPSD(items)
    elif isinstance (items[0], JavaClass):
        return generateJCPromptSPDD(items)
    elif isinstance (items[0], JavaFile):
        return generateJFPromptSPDD(items)
    else:
        raise Exception("Unknown item type")

def generateJMPromptSPSD(items):
    messages = [
            {"role":"system", "content": """Given a Java method, provide feedback on the following header comment generated to summarize its function and interface, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the method.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the method.
    Make sure to follow the format in the examples and provide your ratings out of 5."""},
            {"role":"user", "content":"""Method:
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
     */"""},
            {"role":"assistant", "content":"""Feedback:
    * Naturalness: The language used in the comment is rather fluent and is easily readable. 5/5
    * Thoroughness: The comment makes no mention of the assertion that count must equal 2, but is otherwise is thorough. 4/5
    * Non-Repetitiveness: The comment redundantly mentions the job variable name, while also repeating the assertion on completion. 2/5
    * Brevity: The comment is rather long for such a short function. Its discussion of variable names is questionable at best. 2/5
    * Accuracy: The call to testFileBefore is entirely hallucinatory. 2/5"""},
            {"role":"user", "content":"""Method:
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
     */"""},
            {"role":"assistant","content":"""Feedback:
    * Naturalness: The language used in the comment has a very poor presentation that makes it rather inaccessible, with some degree of unneeded technical detail. It fails to present a big-picture understanding of the purpose of the method. It maintains some degree of grammar. 2/5
    * Thoroughness: The comment discusses all aspects of the method. 5/5
    * Non-Repetitiveness: The comment is not repetitive in any manner. 5/5
    * Brevity: The comment discusses the method in unnecessary amounts of detail, going almost token-by-token. 1/5
    * Accuracy: We can only assume that the references to the parent function are accurately presented. The other information presented in the comment is entirely accurate. 5/5"""},
            {"role":"user","content":"""Method:
    """ + items[0].cleaned_ms + """
    Comment:
    """ + items[1]}
    ]
    return messages

def generateJMPromptDPSD(items):
    messages = [
            {"role":"system", "content": """Given a Java method, provide comparative feedback on the following header comments generated to summarize its function and interface, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the method.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the method.
    Provide your ratings as preferences: On each metric, numerically report either 1 or 2 at the end of your feedback, indicating if you prefer the first or the second comment, respectively. Follow the format from the examples."""},
            {"role":"user", "content":"""Method:
    void testFileSent() throws Exception {
        JobExecution execution = jobLauncher.run(job,
                new JobParametersBuilder().addLong("time.stamp", System.currentTimeMillis()).toJobParameters());
        assertEquals(BatchStatus.COMPLETED, execution.getStatus());
        // 2 chunks sent to channel (5 items and commit-interval=3)
        assertEquals(2, count);
    }
    Comment 1:
    /**
     * This method sets a job named job off and asserts that it gets completed. It ensures that the launched job is timestamped. It also asserts that the batch of jobs thereby launched gets completed. It also ensures testFileBefore is executed prior to its completion.
     */
    Comment 2:
    /**
     * Methods runs job, ensure is completed.
     */"""},
            {"role":"assistant", "content":"""Feedback:
    * Naturalness: The language used in the first comment is rather fluent and is easily readable while the second comment is rather choppy and contains grammatical inconsistencies: 1
    * Thoroughness: The first comment makes no mention of the assertion that count must equal 2, but is otherwise is thorough, whereas the second comment omits both the time stamping and the count assertions: 1
    * Non-Repetitiveness: The first comment redundantly mentions the job variable name, while also repeating the assertion on completion. The second comment is not repetitive at all: 2
    * Brevity: The first comment is rather long for such a short function and contains unneded variable name information. The second comment is quite to the point: 2
    * Accuracy: The call to testFileBefore is entirely hallucinatory in the first comment. The second comment does not contain any incorrect information: 2"""},
            {"role":"user", "content":"""Method:
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        Log.e(LOGTAG,"in onCreate");
        super.onCreate(savedInstanceState);
        // Keep the screen on
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        // Set up full screen
        addFullScreenListener();
    }
    Comment 1:
    /**
     * overriding NativeActivity's method of the same name
     * logs that it is being called, calls the parent's eponymous method,
     * get current window, flags window for keeping the screen on, listens for full screen.
     */
    Comment 2:
    /**
     * Turns on a full screen on creation, setting up a full screen.
     */"""},
            {"role":"assistant","content":"""Feedback:
    * Naturalness: The language used in the first comment has a very poor presentation that makes it rather inaccessible, with some degree of unneeded technical detail. It fails to present a big-picture understanding of the purpose of the method. The second comment is much more natural: 2
    * Thoroughness: The first comment discusses all aspects of the method, whereas the second comment makes no mention of logging or the call to the inherited method: 1
    * Non-Repetitiveness: The first comment is not repetitive in any manner, whereas the second comment repeats the claim it makes: 1
    * Brevity: The first comment discusses the method in unnecessary amounts of detail, going almost token-by-token, whereas the second token manages to restrain itself to a short description: 2
    * Accuracy: We can only assume that the references to the parent function are accurately presented for the first comment; the other information presented in the comment is entirely accurate. The second comment falsely implies that the screen will be newly turned-on, whereas it exists before the call in actuality: 1"""},
            {"role":"user","content":"""Method:
    """ + items[0][0].cleaned_ms + """
    Comment 1:
    """ + items[0][1] + """
    Comment 2:
    """ + items[1][1]}
    ]
    return messages

def generateJCPromptSPSD(items):
    prompt = [{"role":"system","content":"""
    Given the signature of a Java class, its field assignments, and its methods' signatures, provide feedback on the following header comment generated to summarize its function, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the class.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the class.
    Make sure to follow the format in the examples and provide your ratings out of 5."""},
        {"role":"user","content":"""Class Signature:
    public class IntMap<V> extends TreeMap<Integer,V> 
    Field Assignments:
    private static final long serialVersionUID = 1L;
    Method Signatures:
    public int newInt()
    Comment:
    /**
     * This method implements an integer-keyed tree map structure, extending the Java base class of the same name. 
     * It provides a utility to generate new keys.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The language used in the comment is rather fluent and is mostly accessible. The discussion of the extension is not necessary. 4/5
    * Thoroughness: The comment is quite thorough. 5/5
    * Non-Repetitiveness: There is not much repetition in the comment. 5/5
    * Brevity: The discussion of the tree map extension could have been much briefer with more high-level detail. 3/5
    * Accuracy: The comment is accurate to our best ability to tell. 5/5"""},
        {"role":"user","content":"""Class Signature:
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
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The language of the comment is needlessly technical, although it is otherwise accessible. 3/5
    * Thoroughness: The comment fails to discuss the non-block interfaces provided by the class. 3/5
    * Non-Repetitiveness: The comment needlessly notes how the class provides an interface in two different ways. 2/5
    * Brevity: The comment remains sufficiently high-level for a reader to quickly understand the purpose of. 5/5
    * Accuracy: The comment does not notice how abstract methods are not implemented in Java; meaning that it is not possible for it to implement retrieving these block aspects. The general purpose of the class is still correct. 2/5"""},
        {"role":"user","content":"""Class Signature:
    """ + items[0].signature + """
    Field Assignments:
    """ + "\n".join([fa[0].strip() for fa in items[0].fieldAssigns]) + """
    Method Signatures:
    """ + "\n".join([m.signature for m in items[0].methods]) + """
    Comment:
    """ + items[1]}]
    return prompt

def generateJCPromptDPSD(items):
    prompt = [{"role":"system","content":"""
    Given the signature of a Java class, its field assignments, and its methods' signatures, provide comparative feedback on the following header comments generated to summarize its function, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the class.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the class.
    Provide your ratings as preferences: On each metric, numerically report either 1 or 2 at the end of your feedback, indicating if you prefer the first or the second comment, respectively. Follow the format from the examples."""},
        {"role":"user","content":"""Class Signature:
    public class IntMap<V> extends TreeMap<Integer,V> 
    Field Assignments:
    private static final long serialVersionUID = 1L;
    Method Signatures:
    public int newInt()
    Comment 1:
    /**
     * This method implements an integer-keyed tree map structure, extending the Java base class of the same name. 
     * It provides a utility to generate new keys for the integer-keyed tree map structure.
     */
    Comment 2:
    /**
      * This method creates an IntMap, extending TreeMap.
      */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The language used in the first comment is rather fluent and is mostly accessible but its discussion of the extension is not necessary. The second comment also suffers from the extension issue, but by failing to explain the mentioned terminology at all, it fails completely at naturalness: 1
    * Thoroughness: The first comment is quite thorough, whereas the second is quite cursory: 1
    * Non-Repetitiveness: The first comment mentions the keying basis of the structure twice but there is no repetition is the second comment: 2
    * Brevity: The discussion of the tree map extension could have been much briefer with more high-level detail, whereas that of the second method is brief: 2
    * Accuracy: Both comments are accurate to our best ability to tell, but as the second one's claim is rather useless, we prefer the first one: 1"""},
        {"role":"user","content":"""Class Signature:
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
    Comment 1:
    /**
     * Creates an interface for captcha implementations. This is done by creating the CaptchaStrategy abstract class. Implements how to get various aspects of a captcha block.
     */
    Comment 2:
    /**
     * This class works to provide an interface for implementing catcha placement in mobile apps, leaving many methods to be implemented by inheriting subclasses.
     * Accordingly, it sets out quite a few methods to be implemented with respect to the captcha block, such as setting the shape and getting the position of the block, with there existing quite a few such methods defined here.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The language of the first comment is needlessly technical, although it is otherwise accessible. The second comment also uses some technical terminology but presents it in a more naturally readable way, with appropriate explanations: 2
    * Thoroughness: The first comment fails to discuss the non-block interfaces provided by the class, while the second one describes the kinds of interfaces the class provides in greater detail: 2
    * Non-Repetitiveness: The first comment needlessly notes how the class provides an interface in two different ways, whereas the second comment is long but not repetitive: 2
    * Brevity: The first comment remains sufficiently high-level for a reader to quickly understand the purpose of, whereas the second one is needlessly long as a result of fanciful word choices and too much detail: 1
    * Accuracy: The first comment does not notice how abstract methods are not implemented in Java; meaning that it is not possible for it to implement retrieving these block aspects. The general purpose of the class is still correct in the first comment. The second comment is simply accurate according to our best ability to discern: 2"""},
        {"role":"user","content":"""Class Signature:
    """ + items[0][0].signature + """
    Field Assignments:
    """ + "\n".join([fa[0].strip() for fa in items[0][0].fieldAssigns]) + """
    Method Signatures:
    """ + "\n".join([m.signature for m in items[0][0].methods]) + """
    Comment 1:
    """ + items[0][1] + """
    Comment 2:
    """ + items[1][1]}]
    return prompt

def generateJCPromptDPDD(items):
    prompt = [{"role":"system","content":"""
    Given the signature of a Java class, its field assignments and its methods, provide comparative feedback on the following header comments generated to summarize its function, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the class.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the class.
    Provide your ratings as preferences: On each metric, numerically report either 1 or 2 at the end of your feedback, indicating if you prefer the first or the second comment, respectively. Follow the format from the examples."""},
        {"role":"user","content":"""Class:
public class IntMap<V> extends TreeMap<Integer,V> {
    private static final long serialVersionUID = 1L;

    public int newInt() {
        int k = size();
        while (containsKey(k)) k++;
        return k;
    }
    
}
    Comment 1:
    /**
     * This method implements an integer-keyed tree map structure, extending the Java base class of the same name. 
     * It provides a utility to generate new keys for the integer-keyed tree map structure.
     */
    Comment 2:
    /**
      * This method creates an IntMap, extending TreeMap.
      */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The language used in the first comment is rather fluent and is mostly accessible but its discussion of the extension is not necessary. The second comment also suffers from the extension issue, but by failing to explain the mentioned terminology at all, it fails completely at naturalness: 1
    * Thoroughness: The first comment is quite thorough, whereas the second is quite cursory: 1
    * Non-Repetitiveness: The first comment mentions the keying basis of the structure twice but there is no repetition is the second comment: 2
    * Brevity: The discussion of the tree map extension could have been much briefer with more high-level detail, whereas that of the second method is brief: 2
    * Accuracy: Both comments are accurate to our best ability to tell, but as the second one's claim is rather useless, we prefer the first one: 1"""},
        {"role":"user","content":"""Class:
public abstract class CaptchaStrategy {

    protected Context mContext;

    public CaptchaStrategy(Context ctx) {
        this.mContext = ctx;
    }

    protected Context getContext() {
        return mContext;
    }

    public abstract Path getBlockShape(int blockSize);

    public abstract PositionInfo getBlockPostionInfo(int width, int height, int blockSize);

    public PositionInfo getPositionInfoForSwipeBlock(int width, int height, int blockSize){
        return getBlockPostionInfo(width,height,blockSize);
    }

    public abstract Paint getBlockShadowPaint();

    public abstract Paint getBlockBitmapPaint();

    public void decoreateSwipeBlockBitmap(Canvas canvas, Path shape) {

    }
}
    Comment 1:
    /**
     * Creates an interface for captcha implementations. This is done by creating the CaptchaStrategy abstract class. Implements how to get various aspects of a captcha block.
     */
    Comment 2:
    /**
     * This class works to provide an interface for implementing catcha placement in mobile apps, leaving many methods to be implemented by inheriting subclasses.
     * Accordingly, it sets out quite a few methods to be implemented with respect to the captcha block, such as setting the shape and getting the position of the block, with there existing quite a few such methods defined here.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The language of the first comment is needlessly technical, although it is otherwise accessible. The second comment also uses some technical terminology but presents it in a more naturally readable way, with appropriate explanations: 2
    * Thoroughness: The first comment fails to discuss the non-block interfaces provided by the class, while the second one describes the kinds of interfaces the class provides in greater detail: 2
    * Non-Repetitiveness: The first comment needlessly notes how the class provides an interface in two different ways, whereas the second comment is long but not repetitive: 2
    * Brevity: The first comment remains sufficiently high-level for a reader to quickly understand the purpose of, whereas the second one is needlessly long as a result of fanciful word choices and too much detail: 1
    * Accuracy: The first comment does not notice how abstract methods are not implemented in Java; meaning that it is not possible for it to implement retrieving these block aspects. The general purpose of the class is still correct in the first comment. The second comment is simply accurate according to our best ability to discern: 2"""},
        {"role":"user","content":"""Class:
    """ + items[0][0].cleaned_cs + """
    Comment 1:
    """ + items[0][1] + """
    Comment 2:
    """ + items[1][1]}]
    return prompt

def generateJCPromptSPDD(items):
    prompt = [{"role":"system","content":"""
    Given a Java class, including its field assignments and its methods, provide feedback on the following header comment generated to summarize its function, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the class.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the class.
    Make sure to follow the format in the examples and provide your ratings out of 5."""},
        {"role":"user","content":"""Class:
public class IntMap<V> extends TreeMap<Integer,V> {
    private static final long serialVersionUID = 1L;

    public int newInt() {
        int k = size();
        while (containsKey(k)) k++;
        return k;
    }
    
}
    Comment:
    /**
     * This method implements an integer-keyed tree map structure, extending the Java base class of the same name. 
     * It provides a utility to generate new keys.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The language used in the comment is rather fluent and is mostly accessible. The discussion of the extension is not necessary. 4/5
    * Thoroughness: The comment is quite thorough. 5/5
    * Non-Repetitiveness: There is not much repetition in the comment. 5/5
    * Brevity: The discussion of the tree map extension could have been much briefer with more high-level detail. 3/5
    * Accuracy: The comment is accurate to our best ability to tell. 5/5"""},
        {"role":"user","content":"""Class:
public abstract class CaptchaStrategy {

    protected Context mContext;

    public CaptchaStrategy(Context ctx) {
        this.mContext = ctx;
    }

    protected Context getContext() {
        return mContext;
    }

    public abstract Path getBlockShape(int blockSize);

    public abstract PositionInfo getBlockPostionInfo(int width, int height, int blockSize);

    public PositionInfo getPositionInfoForSwipeBlock(int width, int height, int blockSize){
        return getBlockPostionInfo(width,height,blockSize);
    }

    public abstract Paint getBlockShadowPaint();

    public abstract Paint getBlockBitmapPaint();

    public void decoreateSwipeBlockBitmap(Canvas canvas, Path shape) {

    }
}
    Comment:
    /**
     * Creates an interface for captcha implementations. This is done by creating the CaptchaStrategy abstract class. Implements how to get various aspects of a captcha block.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The language of the comment is needlessly technical, although it is otherwise accessible. 3/5
    * Thoroughness: The comment fails to discuss the non-block interfaces provided by the class. 3/5
    * Non-Repetitiveness: The comment needlessly notes how the class provides an interface in two different ways. 2/5
    * Brevity: The comment remains sufficiently high-level for a reader to quickly understand the purpose of. 5/5
    * Accuracy: The comment does not notice how abstract methods are not implemented in Java; meaning that it is not possible for it to implement retrieving these block aspects. The general purpose of the class is still correct. 2/5"""},
        {"role":"user","content":"""Class:
    """ + items[0].cleaned_cs + """
    Comment:
    """ + items[1]}]
    return prompt
    
def generateJFPromptSPSD(items):
    prompt = [{"role":"system","content":"""Given a Java file's class signatures, provide feedback on the following header comment generated to summarize the file's purpose, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the file.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the file.
    Make sure to follow the format in the examples and provide your ratings out of 5."""},
        {"role":"user","content":"""Class Signatures:
    public class MainActivity extends Activity
    Comment:
    /**
     * This file contains a file that works to track user clicks in order to generate videos from GIFs upon demand. This class will generate the video corresponding to a GIF upon being clicked on.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The comment is very legible and natural in its language. 5/5
    * Thoroughness: The comment describes the purpose of the only single class present in the file quite well. 5/5
    * Non-Repetitiveness: The comment is rather repetitive, describing the same function twice. 2/5
    * Brevity: The comment is reasonably brief and remains high-level, although it suffers from some repetition. 4/5
    * Accuracy: The comment mistakenly calls the class in the file a file. It is otherwise accurate, to our best ability to provide feedback. 3/5"""},
        {"role":"user","content":"""Class Signatures:
    public class Parser
    public class Lexer
    Comment:
    /**
     * This file has two classes. Parser: Parses a lexed file in language. Lexer: Lexes a code file in language.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The comment is not very natural in its language and structure, choosing to interrupt the flow of language to subdivide the discussion of the file by classes. It fails to provide any higher-level overview. 2/5
    * Thoroughness: While the file header mentions both classes and their functions in very basic terms, a lot of important details, such as the choice of language and the purpose of these tools are omitted. There is a lack of high-level details. 2/5
    * Non-Repetitiveness: The comment is not repetitive. 5/5
    * Brevity: The comment is very brief. 5/5
    * Accuracy: The comment does not contain any inaccurate information, to our best ability to tell. 5/5"""},
        {"role":"user","content":"""Class Signatures:
    """ + "\n".join([c.signature for c in items[0].classes]) + """
    Comment:
    """ + items[1]}]
    return prompt

def generateJFPromptDPSD(items):
    prompt = [{"role":"system","content":"""Given a Java file's class signatures, provide comparative feedback on the following header comments generated to summarize the file's purpose, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the file.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the file.
    Provide your ratings as preferences: On each metric, numerically report either 1 or 2 at the end of your feedback, indicating if you prefer the first or the second comment, respectively. Follow the format from the examples."""},
        {"role":"user","content":"""Class Signatures:
    public class MainActivity extends Activity
    Comment 1:
    /**
     * This file contains a file that works to track user clicks in order to generate videos from GIFs upon demand. This class will generate the video corresponding to a GIF upon being clicked on.
     */
    Comment 2:
    /**
     * MainActivity: Click GIF -> Generate Video
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The first comment is very legible and natural in its language; the second comment does not even attempt to bother with sentences, which is not desirable in documentation: 1
    * Thoroughness: The first comment describes the purpose of the only single class present in the file quite well. The second comment fails to mention the user click tracking aspect: 1
    * Non-Repetitiveness: The first comment is rather repetitive, describing the same function twice; whereas the second comment has no such issue: 2
    * Brevity: The first comment is reasonably brief and remains high-level, although it suffers from some repetition, the second comment is even more to the point: 2
    * Accuracy: The first comment mistakenly calls the class in the file a file. It is otherwise accurate, to our best ability to provide feedback. The second comment is also accurate to the best extent of our understanding, but does not suffer from the same error: 2"""},
        {"role":"user","content":"""Class Signatures:
    public class Parser
    public class Lexer
    Comment 1:
    /**
     * This file has two classes. Parser: Parses a lexed file in language. Lexer: Lexes a code file in language.
     */
    Comment 2:
    /**
     * Given a Python file, it provides tools for lexing the file (that is, identifies the tokens in the file, and removes comments and whitespace without semantic meaning) and 
     * then parsing a lexed file to generate a parse tree for the file. This will then enable a Java compiler to use the parse tree to generate code from the file.
     * Thus; the file contains tools for the first half of compiling a Java file.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The first comment is not very natural in its language and structure, choosing to interrupt the flow of language to subdivide the discussion of the file by classes. It fails to provide any higher-level overview. On the other hand, the second comment is written very naturally, providing explanations for all the key technical terms used. It also provides a high level overview of the purpose of the file: 2
    * Thoroughness: While the first file header mentions both classes and their functions in very basic terms, a lot of important details, such as the choice of language and the purpose of these tools are omitted. There is a lack of high-level details. On the other hand, the second header comment is quite specific in the function of either class and their higher-level purpose: 2
    * Non-Repetitiveness: The first comment is not repetitive but the second comment contains some redundant information, such as on the parse tree's creation and use: 1
    * Brevity: The first comment is very brief, the second comment is rather overlong: 1
    * Accuracy: The first comment does not contain any inaccurate information, to our best ability to tell; whereas the second comment contradicts itself on what language it is compiling: 1"""},
        {"role":"user","content":"""Class Signatures:
    """ + "\n".join([c.signature for c in items[0][0].classes]) + """
    Comment 1:
    """ + items[0][1] + """
    Comment 2:
    """ + items[1][1] }]
    return prompt

def generateJFPromptDPDD(items):
    prompt = [{"role":"system","content":"""Given a Java file's class signatures, and their respective method signatures, provide comparative feedback on the following header comments generated to summarize the file's purpose, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the file.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the file.
    Provide your ratings as preferences: On each metric, numerically report either 1 or 2 at the end of your feedback, indicating if you prefer the first or the second comment, respectively. Follow the format from the examples."""},
        {"role":"user","content":"""Class Signatures:
    public class MainActivity extends Activity {
        Method Signatures:
	    @Override protected void onCreate(Bundle savedInstanceState)         
	    @Override public boolean onCreateOptionsMenu(Menu menu)         
	    public void onGifClick(View v)         
    }
    Comment 1:
    /**
     * This file contains a file that works to track user clicks in order to generate videos from GIFs upon demand. This class will generate the video corresponding to a GIF upon being clicked on.
     */
    Comment 2:
    /**
     * MainActivity: Click GIF -> Generate Video
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The first comment is very legible and natural in its language; the second comment does not even attempt to bother with sentences, which is not desirable in documentation: 1
    * Thoroughness: The first comment describes the purpose of the only single class present in the file quite well. The second comment fails to mention the user click tracking aspect: 1
    * Non-Repetitiveness: The first comment is rather repetitive, describing the same function twice; whereas the second comment has no such issue: 2
    * Brevity: The first comment is reasonably brief and remains high-level, although it suffers from some repetition, the second comment is even more to the point: 2
    * Accuracy: The first comment mistakenly calls the class in the file a file. It is otherwise accurate, to our best ability to provide feedback. The second comment is also accurate to the best extent of our understanding, but does not suffer from the same error: 2"""},
        {"role":"user","content":"""Class Signatures:
    public class Parser {
        Method Signatures:
        public Parser()
        public boolean parseFilesinHierarchy (UnparsedHierarchy hier)
        public boolean parseFile (UnparsedFile file)
        private boolean parseClass (UnparsedChunk class)
        private boolean parseMethod (UnparsedChunk method)
        private boolean parseStatement (UnparsedChunk statement)
    }
    public class Lexer {
        Method Signatures:         
        public Lexer()
        public boolean lexHierarchy(String rootpath)
        private boolean lexFile(String filepath)
    }
    Comment 1:
    /**
     * This file has two classes. Parser: Parses a lexed file in language. Lexer: Lexes a code file in language.
     */
    Comment 2:
    /**
     * Given a Python file, it provides tools for lexing the file (that is, identifies the tokens in the file, and removes comments and whitespace without semantic meaning) and 
     * then parsing a lexed file to generate a parse tree for the file. This will then enable a Java compiler to use the parse tree to generate code from the file.
     * Thus; the file contains tools for the first half of compiling a Java file.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The first comment is not very natural in its language and structure, choosing to interrupt the flow of language to subdivide the discussion of the file by classes. It fails to provide any higher-level overview. On the other hand, the second comment is written very naturally, providing explanations for all the key technical terms used. It also provides a high level overview of the purpose of the file: 2
    * Thoroughness: While the first file header mentions both classes and their functions in very basic terms, a lot of important details, such as the choice of language and the purpose of these tools are omitted. There is a lack of high-level details. On the other hand, the second header comment is quite specific in the function of either class and their higher-level purpose: 2
    * Non-Repetitiveness: The first comment is not repetitive but the second comment contains some redundant information, such as on the parse tree's creation and use: 1
    * Brevity: The first comment is very brief, the second comment is rather overlong: 1
    * Accuracy: The first comment does not contain any inaccurate information, to our best ability to tell; whereas the second comment contradicts itself on what language it is compiling: 1"""},
        {"role":"user","content":"""Class Signatures:
    """ + "\n".join(["\n".join([c.signature + " {", "      Method Signatures:"] + [m.signature for m in c.methods] + ["}"]) for c in items[0][0].classes]) + """
    Comment 1:
    """ + items[0][1] + """
    Comment 2:
    """ + items[1][1] }]
    return prompt

def generateJFPromptSPDD(items):
    prompt = [{"role":"system","content":"""Given a Java file's class signatures, and their respective method signatures, provide feedback on the following header comment generated to summarize the file's purpose, based on the following criteria:
    * Naturalness: The generated comment is accessible to human readers and is fluent in its language.
    * Thoroughness: The generated comment does not omit any important aspect of the file.
    * Non-Repetitiveness: The generated comment does not repeat information.
    * Brevity: The generated comment remains brief and does not delve into unnecessary detail.
    * Accuracy: The generated comment does not contain inaccurate information about the file.
    Make sure to follow the format in the examples and provide your ratings out of 5."""},
        {"role":"user","content":"""Class Signatures:
    public class MainActivity extends Activity {
        Method Signatures:
	    @Override protected void onCreate(Bundle savedInstanceState)         
	    @Override public boolean onCreateOptionsMenu(Menu menu)         
	    public void onGifClick(View v)         
    }
    Comment:
    /**
     * This file contains a file that works to track user clicks in order to generate videos from GIFs upon demand. This class will generate the video corresponding to a GIF upon being clicked on.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The comment is very legible and natural in its language. 5/5
    * Thoroughness: The comment describes the purpose of the only single class present in the file quite well. 5/5
    * Non-Repetitiveness: The comment is rather repetitive, describing the same function twice. 2/5
    * Brevity: The comment is reasonably brief and remains high-level, although it suffers from some repetition. 4/5
    * Accuracy: The comment mistakenly calls the class in the file a file. It is otherwise accurate, to our best ability to provide feedback. 3/5"""},
        {"role":"user","content":"""Class Signatures:
    public class Parser {
        Method Signatures:
        public Parser()
        public boolean parseFilesinHierarchy (UnparsedHierarchy hier)
        public boolean parseFile (UnparsedFile file)
        private boolean parseClass (UnparsedChunk class)
        private boolean parseMethod (UnparsedChunk method)
        private boolean parseStatement (UnparsedChunk statement)
    }
    public class Lexer {
        Method Signatures:         
        public Lexer()
        public boolean lexHierarchy(String rootpath)
        private boolean lexFile(String filepath)
    }
    Comment:
    /**
     * This file has two classes. Parser: Parses a lexed hierarchy in language. Lexer: Lexes a code hierarchy in language.
     */"""},
        {"role":"assistant","content":"""Feedback:
    * Naturalness: The comment is not very natural in its language and structure, choosing to interrupt the flow of language to subdivide the discussion of the file by classes. It keeps the term 'hierarchy' from the code verbatim, without explaining its purpose. It fails to provide any higher-level overview. 2/5
    * Thoroughness: While the file header mentions both classes and their functions in very basic terms, a lot of important details, such as the choice of language and the purpose of these tools are omitted. There is a lack of high-level details. 2/5
    * Non-Repetitiveness: The comment is not repetitive. 5/5
    * Brevity: The comment is very brief. 5/5
    * Accuracy: The comment does not contain any inaccurate information, to our best ability to tell. 5/5"""},
        {"role":"user","content":"""Class Signatures:
    """ + "\n".join(["\n".join([c.signature + " {", "      Method Signatures:"] + [m.signature for m in c.methods] + ["}"]) for c in items[0].classes]) + """
    Comment:
    """ + items[1]}]
    return prompt

def singularPromptSingleDepth(inp):
    toRate = list(inp.items())
    prompts = list()
    for tr in toRate:
        prompts.append(generatePromptSPSD(tr))
    #prompts = [generatePrompt(tr) for tr in toRate] # did not work for some reason
    #generations = modelcalls(prompts)
    generations = gptcalls(prompts)
    metricRatings = [interpretResults(gen) for gen in generations]
    #for i in range(len(generations)):
    #    if metricRatings[i]=={}:
    #        print(generations[i])
    return metricRatings
 
def doublePromptSingleDepth(in1,in2):
    toRate = zip(list(in1.items()),list(in2.items()))
    prompts = list()
    for tr in toRate:
        prompts.append(generatePromptDPSD(tr))
    #prompts = [generatePrompt(tr) for tr in toRate] # did not work for some reason
    #generations = modelcalls(prompts)
    generations = gptcalls(prompts)
    #pdb.set_trace()
    metricRatings = [interpretDoubleResults(gen) for gen in generations]
    #for i in range(len(generations)):
    #    if metricRatings[i]=={}:
    #        print(generations[i])
    return metricRatings    

def doublePromptDoubleDepth(in1,in2):
    toRate = zip(list(in1.items()),list(in2.items()))
    prompts = list()
    for tr in toRate:
        prompts.append(generatePromptDPDD(tr))
    #prompts = [generatePrompt(tr) for tr in toRate] # did not work for some reason
    #generations = modelcalls(prompts)
    generations = gptcalls(prompts)
    #pdb.set_trace()
    metricRatings = [interpretDoubleResults(gen) for gen in generations]
    #for i in range(len(generations)):
    #    if metricRatings[i]=={}:
    #        print(generations[i])
    return metricRatings   

def singularPromptDoubleDepth(inp):
    toRate = list(inp.items())
    prompts = list()
    for tr in toRate:
        prompts.append(generatePromptSPDD(tr))
    #pdb.set_trace()
    #prompts = [generatePrompt(tr) for tr in toRate] # did not work for some reason
    #generations = modelcalls(prompts)
    generations = gptcalls(prompts)
    metricRatings = [interpretResults(gen) for gen in generations]
    #for i in range(len(generations)):
    #    if metricRatings[i]=={}:
    #        print(generations[i])
    #pdb.set_trace()
    return metricRatings

def aggregateSingularRatings(sr):
    agg = dict()
    for r in sr:
        for r_name, r_val in r.items():
            if r_name not in agg:
                agg[r_name] = [0,0]
            agg[r_name][0] += r_val
            agg[r_name][1] += 5
    for r_name in agg:
        agg[r_name].append(agg[r_name][0]/agg[r_name][1])
    return agg

def aggregateDoubleRatings(sr):
    agg = dict()
    for r in sr:
        for r_name, r_val in r.items():
            if r_name not in agg:
                agg[r_name] = [0,0]
            agg[r_name][r_val-1] += 1
    for r_name in agg:
        agg[r_name].append(agg[r_name][0]/(agg[r_name][0]+agg[r_name][1]))
    return agg

# Should be ordered in parallel and the keys should match
def compareTwoPKLs(pathTo1,pathTo2):
   inp1 = pickle.load(open(pathTo1,"rb"))
   res1 = singularPromptDoubleDepth(inp1)
   ares1 = aggregateSingularRatings(res1)
   inp2 = pickle.load(open(pathTo2,"rb"))
   res2 = singularPromptDoubleDepth(inp2)   
   ares2 = aggregateSingularRatings(res2)
   res3 = doublePromptDoubleDepth(inp1,inp2)
   ares3 = aggregateDoubleRatings(res3)
   res4 = doublePromptDoubleDepth(inp2,inp1)
   ares4 = aggregateDoubleRatings(res4)
   bres1 = {k:v[2] for k,v in ares1.items()}
   bres2 = {k:v[2] for k,v in ares2.items()}
   bres3 = {k:v[2] for k,v in ares3.items()}
   bres4 = {k:v[2] for k,v in ares4.items()}
   #pdb.set_trace()
   attrs = bres1.keys() &  bres2.keys() &  bres3.keys() &  bres4.keys()
   resagg = {attr:[bres1[attr],bres2[attr],bres3[attr],bres4[attr]] for attr in attrs}
   delta = {key:[res[1]-res[0],(res[3]+(1-res[2]))/2] for key,res in resagg.items()}
   return resagg, delta#(bres1,bres2,bres3,bres4)

if __name__ == "__main__":
    ress1 = []
    deltas1 = []
    ress2 = []
    deltas2 = []

    common_start = "generations"
    base1 = "out_baseline"
    base2 = "out_fullcontext"
    base3 = "out_CodeLlama"
    common_end = "docs.pkl"
     
    for common_task in ["AnomalyDetection","Captcha","PageRecycler","metazelda"]:
        taskpath = "outputs_"+common_task
        path1 = "/".join([common_start,base1,taskpath,common_end])
        path2 = "/".join([common_start,base2,taskpath,common_end])

        res,delta = compareTwoPKLs(path1,path2)
        ress1.append(res)
        deltas1.append(delta)
        print(delta)
    for common_task in ["AnomalyDetection","Captcha","PageRecycler","metazelda"]:
        taskpath = "outputs_"+common_task
        path3 = "/".join([common_start,base3,taskpath,common_end])
        path2 = "/".join([common_start,base2,taskpath,common_end])

        res,delta = compareTwoPKLs(path1,path2)
        ress2.append(res)
        deltas2.append(delta)
        print(delta)
    pdb.set_trace()
        
