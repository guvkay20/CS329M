import os
import re
import pdb
import javalang

def listJavaFiles(directory : str) -> list[str]:
    java_files_list = []

    with os.scandir(directory) as it:
        for entry in it:
            if entry.is_file() and entry.path[-5:]==".java":
                java_files_list.append(entry.path)
            if entry.is_dir():
                java_files_list += listJavaFiles(entry.path)

    return java_files_list

def ls(rem : re.Match) -> list[int]:
    return [int(m.start()) for m in rem]

def javaClean(f):
        #pdb.set_trace()
        linebuffer = []
        commentlessbuffer = []
        paranLevel = 0
        #first = True
        inMLComment = False
        line = f.readline()
        while line:# and (paranLevel > 0) and not first:
            #first = False
            #pdb.set_trace()
            linebuffer.append(line)

            """endMLC = line.find("*/")
            beginSLC = line.find("//")
            beginMLC = line.find("/*")
            if beginSLC >= 0 or beginMLC >= 0 and not inMLComment:
                if beginMLC == -1 or (beginMLC >= 0  and beginSLC < beginMLC):
             #       line = line[:beginSLC]
                else:
                    inMLComment = True
            """
            beginMLCs = ls(re.finditer("/\*", line))
            endMLCs = ls(re.finditer("\*/", line))
            beginSLCs = ls(re.finditer("/?=/", line))
            i = 0
            j = 0
            k = 0
           
            commentlessLine = ""
            endOfLastMLC = 0
            SLCTrigger = False
            while i < len(beginMLCs) or j < len(endMLCs) or k < len(beginSLCs):
                m = min(beginMLCs[i] if i < len(beginMLCs) else 1e10, endMLCs[j] if i < len(endMLCs) else 1e10, beginSLCs[k] if i < len(beginSLCs) else 1e10)
                if m == (endMLCs[j] if i < len(endMLCs) else 1e10):
                    assert(inMLComment)
                    inMLComment = False
                    endOfLastMLC = 2 + m
                    j += 1
                if m == (beginSLCs[k]  if i < len(beginSLCs) else 1e10) and not inMLComment:
                    commentlessLine = commentlessLine + line[endOfLastMLC:m]
                    k += 1
                    SLCTrigger = True
                    break
                if m == (beginSLCs[k] if i < len(beginSLCs) else 1e10) and inMLComment:
                    k += 1
                if m == (beginMLCs[i] if i < len(beginMLCs) else 1e10):
                    if not inMLComment:
                        commentlessLine = commentlessLine + line[endOfLastMLC:m]
                    inMLComment = True
                    i += 1

            if not inMLComment and not SLCTrigger:
                commentlessLine = commentlessLine + line[endOfLastMLC:]

            commentlessbuffer.append(commentlessLine)
            line = f.readline()
        return linebuffer, commentlessbuffer

class MethodCall:
    def __init__(self, methodName, methodOf, methodIn = None):
        self.methodName = methodName
        self.methodOf = methodOf
        self.methodIn = methodIn # Not currently used
        self.hasContext = False
        if (methodOf is None) or (methodOf == ""):
            self.hasContext = True

    def contextualize(self, methodOfBaseType):
        self.methodOfBaseType = methodOfBaseType
        self.hasContext = True

class Extends:
    def __init__(self, extensionClass):
        self.extends = extensionClass

def gatherCalls(line, tree, context, fieldDeclaration=False):
    # Removes left hand of assignment
    #rgx = re.search("(^|[^=])=($|[^=])", line)
    #if rgx is not None:
    #    active = line[rgx.start()+2:]
    #else:
    #    assert (False)
    #    if fieldDeclaration:
    #        return set()
    #    active = line
    
    #tokens = javalang.tokenizer.tokenize(active)
    #parser = javalang.parser.Parser(tokens)
    calls = [(path, node) for path, node in tree.filter(javalang.tree.MethodInvocation)]
    ret = set()
    for call in calls:
        #pdb.set_trace()
        c = MethodCall(call[1].member, call[1].qualifier)
        # seek context
        for contextLevel in [call[0][0]]: # Note how in-order traversal ensures the inner-most and latest context will survive only -> Actually ignore this, [0][0] with in-order traversal should enable the same fxn; the dumb list creation is only for indentation preservation; one small issue if there exists x of type T and the current line declares an x of type P, x will be pulled in type P not X
            # Seek LocalVariableDeclaration at this level
            for path, node in contextLevel:
                if node == call[1]:
                    break # context limit reached at this level
                if isinstance(node, javalang.tree.VariableDeclarator):
                    if c.methodOf is not None:
                        if node.name == c.methodOf.split(".")[0]:
                            c.contextualize(path[-2].type)
        ret.add(c)

    return ret

class JavaMethod:
    def __init__(self, lbf, cbs, ms, mast):
        ms = ms.strip()
        self.cleaned_ms = ms
        self.AST = mast

        # get signature
        self.signature = ms[:ms.find("{")]
        self.fxnbody = ms[ms.find("{")+1:-1]

        # TODO split
        self.bodyLines = []
        buff = ""
        paranLevel = 0
        remainder = self.fxnbody
        while remainder != "":
            S = remainder.find(";")
            if paranLevel != 0:
                S = 1e10
            L = remainder.find("{")
            R = remainder.find("}")
            m = min(L,R,S)
            if m == -1:
                m = min (max(L,R),max(S,R),max(S,L))
                if m == -1:
                    m = max(S,L,R)
                    if m == -1:
                        break
            if m == L:
                paranLevel += 1
            if m == R:
                paranLevel -= 1
            
            buff = buff + remainder[:m+1]
            remainder = remainder[m+1:]
            
            if paranLevel == 0 and m == S:
                self.bodyLines.append(buff)
                buff = ""
         

        self.deps = set()

    def gatherDeps(self):
        if len(self.deps) > 0:
            return self.deps 
        
        methodLocalVars = dict()
        for i, bl in enumerate(self.bodyLines):
            lineDeps = gatherCalls(bl, self.AST.body[i], self.cleaned_ms)
            
            """ THAT IS NO EXCUSE, THEY ARE STILL DEPENDENT
            # If methods are not of something, they must be of self. If so, remove them from deps
            newDeps = set()
            for dep in lineDeps:
                if (dep.methodOf is None) or (dep.methodOf == ""):
                    pass
                else:
                    newDeps.add(dep)
            """

            # If call have not been contextualized yet, maybe they are of local vars and should be contextualized by prior lines of method
            for dep in lineDeps:
                if not dep.hasContext:
                    if dep.methodOf.split(".")[0] in methodLocalVars.keys():
                        dep.contextualize(methodLocalVars[dep.MethodOf.split(".")[0]])

            # Update that context list
            if isinstance(self.AST.body[i], javalang.tree.LocalVariableDeclaration):
                t = self.AST.body[i].type
                for d in self.AST.body[i].declarators:
                    methodLocalVars[d.name] = t

            self.deps |= lineDeps
       
        # We should now contextualize all these calls

        return self.deps


class JavaClass:
    def __init__(self, lbf, cbf, cs): # Line buffer, cleaned buffer (aligned with line buffer), and cleaned class string # TODO later dcs
        cs = cs.strip()
        self.cleaned_cs = cs
        self.AST = javalang.parse.parse(cs).types[0]

        # get signature
        self.signature = cs[:cs.find("{")]

        # get commented cs TODO 

        # get all methods
        # get all fields
        remainder = cs[cs.find("{")+1:-1] # strip the outer {}s
        methodStrs = []
        self.fieldAssigns = []
        buff = ""
        paranLevel = 0
        i = 0
        while remainder != "":
            S = remainder.find(";")
            if paranLevel != 0:
                S = 1e10
            L = remainder.find("{")
            R = remainder.find("}")
            m = min(L,R,S)
            if m == -1:
                m = min (max(L,R),max(S,R),max(S,L))
                if m == -1:
                    m = max(S,L,R)
                    if m == -1:
                        break
                        #buff = buff + remainder
                        #classStrs.append(classbuffer)
            if m == L:
                paranLevel += 1
            if m == R:
                paranLevel -= 1
            
            buff = buff + remainder[:m+1]
            remainder = remainder[m+1:]
            
            if paranLevel == 0 and m == R and buff[-1]=="}":
                methodStrs.append((buff,self.AST.body[i]))
                buff = ""
                i += 1
            if paranLevel == 0 and m == S:
                self.fieldAssigns.append((buff,self.AST.body[i]))
                buff = ""
                i += 1

        self.methods = []
        for i, ms in enumerate(methodStrs):
            self.methods.append(JavaMethod(lbf, cbf, ms[0], ms[1]))#, dirtyCSs[i])

        self.deps = set()

    def stripSelfRefs(self, deps):
        ret = set()
        for dep in deps:
            if isinstance(dep, MethodCall):
                if (dep.methodOf is None) or (dep.methodOf == ""):
                    pass
                else:
                    ret.add(dep)
        return ret

    def gatherDeps(self):
        if len(self.deps) > 0:
            return self.stripSelfRefs(self.deps)

        # PART 1 , EXTENSION
        """splitSign = self.signature.strip().split()
        inSign = False
        for i, token in enumerate(splitSign):
            if inSign:
                self.deps.add((token, "Class"))
            if not inSign and token == "extends":
                inSign = True"""
        if self.AST.extends is not None:
            for _, node in self.AST.extends.filter(javalang.tree.ReferenceType):
                self.deps.add(Extends(node.name))

        # PART 2, FIELD ASSIGNS
        for fa in self.fieldAssigns:
            self.deps |= set(gatherCalls(fa[0], fa[1], self.cleaned_cs, fieldDeclaration = True))

        # PART 3, METHODS
        for m in self.methods:
            self.deps |= set(m.gatherDeps())

        # handle non-contextualized deps to fields of this clas by getting the fields' types and contextualizing them
        # First Gather Field Assigns' Types
        fields = dict()
        for fa in self.fieldAssigns:
            for vd in fa[1].declarators:
                fields[vd.name] = fa[1].type
        # Then look thru them
        for dep in self.deps:
            if isinstance(dep, MethodCall) and not dep.hasContext:
                if dep.methodOf.split(".")[0] in fields:
                    dep.contextualize(fields[dep.methodOf.split(".")[0]])


        #  predicateless methods are of this class, note it down or bear in mind for graph construction
        return self.stripSelfRefs(self.deps)

# Assumes a degree of good formatting
class JavaFile:
    def __init__(self, filepath):
        print("proc ", filepath)
        f = open(filepath)
        self.classes = []
        self.imports = []
        self.packageName = ""
        self.filepath = filepath

        """line = f.readline()
        while line:
            if line.split()[0]=="import":
                self.imports.append(line)
            elif "class" in set(line.split()):
                self.classes.append(JavaClass(line, f))
            line = f.readline()
        """
        self.linebuffer, self.cleanbuffer = javaClean(f)
       
        print("buffers constructed")
        #pdb.set_trace()
        #PROCESS HEADER
        i = -1
        statementBuffer = ""
        remainder = ""
        headerLines = []
        while True:
            if remainder == "":
                i += 1
                if i == len(self.cleanbuffer):
                    headerLines.append(statementBuffer)
                    break
                remainder = self.cleanbuffer[i]
            statementBreak = remainder.find(";")
            if statementBreak == -1:
                statementBuffer = statementBuffer + remainder
                remainder = ""
            else:
                statementBuffer = statementBuffer + remainder[:1+statementBreak]
                headerLines.append(statementBuffer)
                statementBuffer = ""
                remainder = remainder[1+statementBreak:]
        
        pkgline = headerLines[0].split()
        assert(pkgline[0] == "package")
        self.packageName = pkgline[1].split(";")[0]
        assert(len(pkgline)==2 or (len(pkgline)==3 and pkgline[2] ==";"));
       
        i = 1
        while True:
             l = headerLines[i].split()
             if l[0] == "import":
                 self.imports.append(l[1].split(";")[0])
                 assert(len(l)==2 or (len(l)==3 and l[2]==";"))
             else:
                 break
             i += 1

        postheader = "".join((headerLines[i:]))
        
        
        # DETECT CLASS BOUNDARIES #TODO not really verified
        classbuffer = ""
        remainder = postheader
        paranLevel = 0
        classStrs = []
        while remainder != "":
            L = remainder.find("{")
            R = remainder.find("}")
            m = min(L,R)
            if m == -1:
                m = max(L,R)
                if m == -1:
                    break
                    #classbuffer = classbuffer + remainder
                    #classStrs.append(classbuffer)
            if m == L:
                paranLevel += 1
            else:
                paranLevel -= 1
            classbuffer = classbuffer + remainder[:m+1]
            remainder = remainder[m+1:]
            
            if paranLevel == 0:
                classStrs.append(classbuffer)
                classbuffer = ""

        # TODO dirty CSs propagate
        #dirtyCSs = []
        #csindex = 0
        #lineindex = 0
        #while csindex < len(classStrs):

        
        for i, cs in enumerate(classStrs):
            self.classes.append(JavaClass(self.linebuffer, self.cleanbuffer, cs))#, dirtyCSs[i])
        self.deps = set()

    def gatherDeps(self):
        print("deps gathering for ", self.filepath)
       
        if len(self.deps) > 0:
            return self.deps 

        for c in self.classes:
            self.deps |= set(c.gatherDeps())

        return self.deps

def parseDependencies():
    # Generate List of Java files
    javaList = listJavaFiles("tmp")

    # For each Java file, find methods, find dependencies
    files = [JavaFile(path) for path in javaList]
    [jf.gatherDeps() for jf in files]

    # Construct graph of dependencies, including external ones

    # (Retrieve external dependencies' comments, if available)
    # Create traversal order for dependencies, keep in mind inheritances and calls (calls include field assignments and in-method calls)

if __name__ == "__main__":
    #pdb.set_trace()
    parseDependencies()
