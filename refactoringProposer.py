import torch
import transformers
import pdb
from dependencyParser.parseDependencies import JavaClass, JavaFile, JavaMethod
import pickle
from openai import OpenAI
import json
from tqdm import tqdm
from evaluator import gptcalls


def pkgLevelPrompt(jfItems, commentDict):
    perFileComments = list()
    for fileItem in jfItems:
        perClassComments = []
        for classKey in fileItem[0].classes:

            perClassComments.append(
                "\n".join(["\n".join(["Signature of Class:",classKey.signature]),
                             commentDict[classKey],
                            "\n".join(["Methods of Class:"] + [m.signature for m in classKey.methods])]))


        perFileComments.append( "\n".join(["File Path:",fileItem[0].filepath] + \
                (["Package Name of File:",fileItem[0].packageName] if fileItem[0].packageName!="" and fileItem[0].packageName != "not_in_package" else []) + \
                ["File Header Comment:", fileItem[1]] + \
                ["Class(es) of File"] + perClassComments))
        
    compiledPrompt = "\n\n".join(perFileComments)
    prompt = [
        {"role":"system","content":"Given a list of file-level headers from Java Files, the signatures and class header comments for Java Classes contained within, as well as the signatures of all of the methods contained therein, suggest possible refactorings that may be performed on this project. Explain reasoning for each proposal."},
        {"role":"user","content":compiledPrompt},
        {"role":"system","content":"Now generate refactoring proposals."}
              ]
    return prompt
    
if __name__ == "__main__":
    common_start = "generations"
    base1 = "out_fullcontext"   
    common_end = "docs.pkl"
    results = list()
    for common_task in ["AnomalyDetection","Captcha","PageRecycler","metazelda"]:
        #common_task = "metazelda"
        taskpath = "outputs_"+common_task    
        # No agg will leave taskpath as metazelda, which is the one we want as it is the most complex
        pathTo = "/".join([common_start,base1,taskpath,common_end])
        inp = pickle.load(open(pathTo,"rb")) # inp is our sought dict already
        #pdb.set_trace()    
        fileItems = list()
        for item in inp.items():
            if isinstance(item[0], JavaFile):
                fileItems.append(item)
        #pdb.set_trace()    
        genprompt = pkgLevelPrompt(fileItems,inp)
        result = gptcalls([genprompt],2000)[0]
        results.append(result)
    open("tmp.txt","w").write("\n\n\n".join(results).replace("\\n","\n"))
    pdb.set_trace()
