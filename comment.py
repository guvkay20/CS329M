import json
import pickle
import openai
import os
import requests
import re
from dependencyParser.parseDependencies import parseDependencies, JavaFile, JavaClass, JavaMethod

NO_DOCS_MODE = False

openai.api_key = os.getenv('OPENAI_API_KEY')
openai_model = 'gpt-4-1106-preview'

def load_cache(file_path):
    '''
    Load the cache from a file.

    Parameters:
    file_path (str): Path to the cache file.

    Returns:
    dict: The loaded cache.
    '''
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_cache(cache, file_path):
    '''
    Save the cache to a file.

    Parameters:
    cache (dict): The cache to be saved.
    file_path (str): Path to the cache file.
    '''
    with open(file_path, 'w') as file:
        json.dump(cache, file, indent=4)

def submitCompletionRequest(request, cache, cacheFile, skipCache):
    '''
    Submit a chat completion request to the OpenAI API, using cache to avoid repeated requests.

    Parameters:
    request (str): The user's request in text format.
    cache (dict): The cache containing previous responses.
    cacheFile (str): Path to the cache file.

    Returns:
    str: The content of the response from the OpenAI chat completion API.
    '''
    # Check if the response is already in the cache
    if not skipCache and request in cache:
        print('cache hit')
        return cache[request]

    messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": request
            }
        ]

    response = openai.chat.completions.create(
        model=openai_model,
        messages=messages,
        temperature=0.1,
        max_tokens=1200
    )

    # Update the cache and save it
    cache[request] = response.choices[0].message.content
    save_cache(cache, cacheFile)

    return response.choices[0].message.content


def formatSinglePrompt(signature, body):
    '''
    Format a function signature and body with a placeholder for the docstring.

    Parameters:
    signature (str): The function signature.
    body (str): The function body.

    Returns:
    str: Formatted function with a placeholder for the docstring.
    '''
    fill_txt = "[DOCSTRING HERE]\n"
    return fill_txt + signature + '{' + body + '\n}'

def generateDocstring(template, context, dep):
    '''
    Generate the prompt for docstring generation.

    Parameters:
    template (str): The function template with a placeholder for the docstring.
    context (str): The context of other functions' documentation.
    dep (object): The dependency

    Returns:
    str: The generated prompt for the docstring.
    '''

    obj_type = 'method'
    if isinstance(dep, JavaFile):
        obj_type = 'file'
    elif isinstance(dep, JavaClass):
        obj_type = 'class'
        print('OBJECT TYPE CLASS')

    pre_prompt = f'''Generate a docstring for the following {obj_type} given the body and
    the context of the other functions' documentation. Return the result as a string, which will
    in its entirety, be used in place of [DOCSTRING HERE] directly, without any other modification.
    '''
    context_prompt = '''Information about this method's dependencies follows below. These are methods
    on which the method directly depends. The comments for those functions are provided, along with 
    their function signature. You can use these to better contextualize your comments.'''
    if context != '':
        return pre_prompt + '\n' + template + '\n\n' + context_prompt + '\n' + context
    else:
        return pre_prompt + '\n' + template + '\n' + context

def stripResponse(text):
    '''
    Extract content between triple backticks in the response. 
    If no backticks exist, return the entire text.

    Parameters:
    text (str): The text to be processed.

    Returns:
    str: The extracted content or the original text if no backticks are found.
    '''
    # Regular expression pattern to match content between triple backticks
    # It also handles an optional language specifier
    pattern = r'```(?:\w*\n)?(.*?)```'

    # Search for the pattern in the text
    match = re.search(pattern, text, re.DOTALL)

    # Return the extracted text or the whole string if no match is found
    return match.group(1) if match else text

def generateContext(deps, docs):
    '''
    Generate the context for docstring generation based on dependencies.

    Parameters:
    deps (list): List of dependencies.
    docs (dict): Dictionary of documented functions.

    Returns:
    str: The generated context.
    '''    
    ctx = ''

    context_added = []

    doc_dict = {k.selfname: (k, v) for k, v in docs.items()}
    for dep in deps:
        doc = doc_dict.get(dep.selfname) if not NO_DOCS_MODE else None
        if doc:
            dep_ctx = doc[1] + dep.selfname + '\n' + doc[0].signature + '\n\n'
            ctx += dep_ctx
            context_added.append(dep.selfname)
    return ctx, context_added

def generateAbridgedClassBody(dep, docs):
    methods = dep.methods
    assigns = dep.fieldAssigns

    body = ''
    body += ''.join(map(lambda x: x[0], dep.fieldAssigns))
    for method in methods:
        doc = docs.get(method) if not NO_DOCS_MODE else None
        if doc:
            body += '\n\t' + doc.replace('\n', '\n\t')
        body += method.signature
    return body

def generateAbridgedFileBody(dep, docs):
    classes = dep.classes

    body = ''
    for clas in classes:
        doc = docs.get(clas) if not NO_DOCS_MODE else None
        if doc:
            body += '\n\t' + doc.replace('\n', '\n\t')
        body += clas.signature
    return body

if __name__ == '__main__':
    # Load or initialize the cache
    cacheFile = 'openai_responses_cache.json'
    cache = load_cache(cacheFile)

    deps = parseDependencies()
    docs = {}

    for index, dep in enumerate(deps[0]):
        try:
            print('================')

            if isinstance(dep, JavaFile):
                signature = dep.filepath
                bodyLines = generateAbridgedFileBody(dep, docs)
                skipCache = False
            elif isinstance(dep, JavaClass):
                signature = dep.signature
                bodyLines = generateAbridgedClassBody(dep, docs)
                skipCache = False
            else:
                signature = dep.signature
                bodyLines = ''.join(dep.bodyLines)
                skipCache = False

            thisDeps = dep.deps

            p = formatSinglePrompt(signature, bodyLines)
            if isinstance(dep, JavaMethod):
                ctx, context_added = generateContext(thisDeps, docs)
                fname = f'prompts/prompt_{index}_{len(context_added)}_dependencies.txt'
            elif isinstance(dep, JavaClass):
                ctx, context_added = '', []
                fname = f'prompts/prompt_{index}.txt'
            else:
                ctx, context_added = '', []
                fname = f'prompts/prompt_{index}.txt'

            promptText = generateDocstring(p, ctx, dep)

#           if isinstance(dep, JavaFile):
#               import code; code.interact(local=locals())

            print(promptText)
            print('---------------')

            # Call submitCompletionRequest with the generated prompt
            res = submitCompletionRequest(promptText, cache, cacheFile, skipCache)

            res = stripResponse(res)
            docs[dep] = res
            function_doc = res + signature + '{' + bodyLines + '\n}'
            print(function_doc)

            f = open('docs.pkl', 'wb')
            pickle.dump(docs, f)
            f.close()

            # Save the prompt to a separate file for each dependency
            with open(fname, 'w') as prompt_file:
                prompt_file.write(promptText)

            # Save the generated documentation to a single file
            with open('function_docs.txt', 'a') as file:
                file.write(function_doc + '\n\n')

            print('================')
        except Exception as e:
            print(dep)
            print(e)
            print('================')
