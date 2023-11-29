import os
import re
import pdb
import javalang

complement = dict()
complement["["] = "]"
complement["]"] = "["
complement["("] = ")"
complement[")"] = "("
complement["{"] = "}"
complement["}"] = "{"
complement[""] = ""

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
            beginSLCs = ls(re.finditer("//", line))
            i = 0
            j = 0
            k = 0
           
            commentlessLine = ""
            endOfLastMLC = 0
            SLCTrigger = False
            while i < len(beginMLCs) or j < len(endMLCs) or k < len(beginSLCs):
                m = min(beginMLCs[i] if i < len(beginMLCs) else 1e10, endMLCs[j] if j < len(endMLCs) else 1e10, beginSLCs[k] if k < len(beginSLCs) else 1e10)
                if m == (endMLCs[j] if j < len(endMLCs) else 1e10):
                    assert(inMLComment)
                    inMLComment = False
                    endOfLastMLC = 2 + m
                    j += 1
                if m == (beginSLCs[k]  if k < len(beginSLCs) else 1e10) and not inMLComment:
                    commentlessLine = commentlessLine + line[endOfLastMLC:m]
                    k += 1
                    SLCTrigger = True
                    break
                if m == (beginSLCs[k] if k < len(beginSLCs) else 1e10) and inMLComment:
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
        self.isOfClass = False
        
        if (methodOf is None) or (methodOf == ""):
            self.hasContext = True
            self.isOfClass = True

    def contextualize(self, methodOfBaseType):
        self.methodOfBaseType = methodOfBaseType
        self.methodOf = methodOfBaseType.name
        self.hasContext = True

    def __repr__(self):
        return "MethodCall("+self.selfname+")"

## ClassDep is for extends; ClassImp is for imports (and extends mapped to them); ClassInc is for files>class hierarchy
class ClassDep:
    def __init__(self, c_lass):
        self.clas = c_lass
    def __repr__(self):
        return "ClassDep("+self.selfname+")"
class ClassImp:
    def __init__(self, c_lass):
        self.clas = c_lass
    def __repr__(self):
        return "ClassImp("+self.selfname+")"
#class ClassInc:
#    def __init__(self, c_lass):
#        self.clas = c_lass
#    def __repr__(self):
#        return "ClassInc("+self.clas.selfname+")"


class DepGL:
    def __init__(self):
        self.PL = list()
        self.PDG = dict()
        self.DGLMode = "master"
        self.prefix = ""

    def __repr__(self):
        return "DepGL of mode "+self.DGLMode+" where DP is: \n " + "\n".join([str(it) for it in self.PL]) + "\n and PDG is \n" + "\n".join([str(pair[0])+"    :    "+str(pair[1]) for pair in self.PDG.items()])

    def register_method(self, jm, deps): 
        self.DGLMode = "method"
        if "updateLevel" not in dir(jm) or jm.updateLevel == "method":
            jm.selfname = jm.getMethodName()
        for dep in deps:
            if dep=='':
                continue
            if "updateLevel" not in dir(dep):
                try:
                    dep.updateLevel = "method"
                except:
                    pdb.set_trace()
        deps = [dep for dep in deps if dep!='']
        self.PDG[jm] = deps

    def register_class(self, jc, deps):
        self.DGLMode = "class"
        self.prefix = jc.getClassName()
        jc.selfname = jc.getClassName()
        for dep in deps:
            if isinstance(dep, ClassDep):
                dep.selfname = dep.clas
            if "updateLevel" not in dir(dep) or dep.updateLevel == "method":
                dep.updateLevel = "class"
            if isinstance(dep, JavaMethod):
                 dep.selfname = self.prefix +"."+ dep.getMethodName()
               

        self.PDG[jc] = deps

    def register_file(self, jf, deps):
        self.DGLMode = "file"
        self.prefix = jf.packageName
        jf.selfname = jf.packageName
        self.file = jf
        jf.updateLevel = "file"
        for dep in deps:
            if isinstance(dep, JavaClass):
                dep.selfname = self.prefix+"."+dep.getClassName()
            if isinstance(dep, ClassImp):
                dep.selfname = dep.clas
            dep.updateLevel = "file"
        self.PDG[jf] = deps

    def addDGL(self, other):
        #pdb.set_trace()
        if self.DGLMode=="file":
            impSuffixes = [imp.split(".")[-1] for imp in self.file.imports]       
            impSuffixes.extend(["Math","String"])
            #self.imports.extend(["java.lang.Math","java.lang.String"])
        # Merge other's PL onto self; for that end, append self name to their starts
        for el in other.PL:
            if el.updateLevel != self.DGLMode:
                el.selfname = self.prefix+"."+el.selfname if self.prefix!="" else el.selfname
            el.updateLevel = self.DGLMode
            self.PL.append(el)

        # Merge other's PDG onto self; do the same for their dpees and deps alike
        # TODO
        for dependee, deps in other.PDG.items():
            #if dependee.selfname.split(".")[-1]=="onMeasure":
            #    pdb.set_trace()
            if dependee.updateLevel != self.DGLMode:
                dependee.selfname = self.prefix+"."+dependee.selfname if self.prefix!= "" else dependee.selfname
                dependee.updateLevel = self.DGLMode
            new_deps = set()
            for dep in deps:
                if dep.updateLevel != self.DGLMode:
                    if isinstance(dep, ClassImp):
                        dep.selfname = dep.selfname
                    elif isinstance(dep, MethodCall) and "selfname" not in dir(dep):
                            if dep.methodOf is None or dep.methodOf=="":
                                dep.selfname = (self.prefix+"."+dep.methodName) if self.prefix != "" else dep.methodName
                            else:
                                dep.selfname = dep.methodOf + "." +  dep.methodName
                    elif isinstance(dep, ClassDep) and self.DGLMode=="file" and (dep.selfname in impSuffixes):
                        try:
                            dep = self.imports[impSuffixes.index(dep.selfname)]
                        except:
                            dep = -1
                    else:
                        try:
                            if self.DGLMode=="file" and isinstance(dep, MethodCall) and isinstance(dep.methodOf, str) and (0 < len(dep.methodOf.split("."))) and (dep.methodOf.split(".")[0] in impSuffixes):
                                try:
                                    dep = self.imports[impSuffixes.index(dep.methodOf.split(".")[0])]             
                                except:
                                    dep = -1
                            else:
                                dep.selfname = (self.prefix+"."+dep.selfname) if self.prefix != "" else dep.selfname
                        except:
                            pdb.set_trace()
                if dep !=-1:
                    dep.updateLevel = self.DGLMode
                    new_deps.add(dep)
            self.PDG[dependee] = new_deps

        #TODO, how to merge PLs and PDGs (appending is not enough, prefixes must be altered, see note below)

    def attempt_resolve(self):  # TODO this manner of comparison, see note below
        #pdb.set_trace()
        progress = True
        while progress:
            resolved = set([it.selfname for it in self.PL])
            torem = list()
            progress = False
            for dependee, deps in self.PDG.items():
                #if isinstance(dependee, JavaClass) and dependee.selfname == "PageIndicatorView":
                #    pdb.set_trace()
                #if isinstance(dependee, JavaMethod) and dependee.selfname.split(".")[-1] == "PageRecyclerView":
                #    pdb.set_trace()
             
                dd = list(deps)
                flag = True
                for d in dd:
                    if not (d in self.PL or ("selfname" in dir(d) and d.selfname in resolved)):
                        flag = False
                    else:
                        deps.remove(d)
                if flag:
                    progress = True
                    resolved.add(dependee)
                    self.PL.append(dependee)
                    torem.append(dependee)
            for tr in torem:
                del self.PDG[tr]

        #pdb.set_trace()
        pass

    def force_resolve(self):  

        # STEP 1 Begin by resolving external dependencies
        # Go through every single ClassImp, and if not in customPkgs, resolve it by removing the dep, then attempt resolve
        for dependee, deps in self.PDG.items():
            newdeps = set()
            for dep in deps:
                if isinstance(dep, ClassImp):
                    sn = dep.selfname
                    if sn[0] == ".":
                        sn = sn[1:]
                    snd = ".".join(sn.split(".")[:-1])
                    if sn in self.customPkgs or snd in self.customPkgs:
                        newdeps.add(dep)
                else:
                    newdeps.add(dep)
            self.PDG[dependee] = newdeps

        self.attempt_resolve()

        # STEP 2 Remove all MethodCalls that use ___UNK
        for dependee, deps in self.PDG.items():
            newdeps = set()
            for dep in deps:
                if isinstance(dep, MethodCall) and ("___UNK" in dep.selfname.split(".")):
                    pass
                else:
                    newdeps.add(dep)
            self.PDG[dependee] = newdeps
        self.attempt_resolve()

        # STEP -1 Heuristic by forcing resolution of methods' methodcall dependencies as they are likely result of hard concepts like member subclasses and inherited methods of other packages that are simply very difficult to resolve
        for dependee, deps in self.PDG.items():
            if isinstance(dependee, JavaMethod):
                removelist = list()
                for dep in deps:
                    if isinstance(dep, MethodCall):
                        removelist.append(dep)
                for rlm in removelist:
                    self.PDG[dependee].remove(rlm)
        self.attempt_resolve()
        
        #pdb.set_trace()

        #TODO; force empty into PL; figure out a good heuristic for it
        # Cycles should be detected and broken up at "random" point (heuristic for least distruption)
        return (self.PL, self.PDG)

    #TODO need a way of learning hierarchy, registering something should give the added ones that prefix
    
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
    
    for i, call in enumerate(calls):
        #pdb.set_trace()
        c = MethodCall(call[1].member, call[1].qualifier if (i==0 or call[1].qualifier!=None) else "___UNK")
        # seek context
        for contextLevel in [call[0][0]]: # Note how in-order traversal ensures the inner-most and latest context will survive only -> Actually ignore this, [0][0] with in-order traversal should enable the same fxn; the dumb list creation is only for indentation preservation; one small issue if there exists x of type T and the current line declares an x of type P, x will be pulled in type P not X
            # Seek LocalVariableDeclaration at this level
            for path, node in contextLevel:
                if node == call[1]:
                    break # context limit reached at this level
                if isinstance(node, javalang.tree.VariableDeclarator):
                    if c.methodOf is not None:
                        #if c.methodOf == "context":
                        #    pdb.set_trace()
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
        #if self.signature.split()[-2]=="@interface": # Is an interface, not a method - no support for this in our system
        if "@interface" in self.cleaned_ms.split():
            raise Exception("isinterface")
        self.fxnbody = ms[ms.find("{")+1:-1]

        self.bodyLines = []
        buff = ""
        #paranLevel = 0
        remainder = self.fxnbody
        seekstack = [] # Keep track of []{}()''""
        while remainder != "":
            #if self.signature == "public static void main(String[] args) " and len(self.bodyLines)==4:
            #    pdb.set_trace()

            S = remainder.find(";")
            if len(seekstack) != 0:
                S = 1e10
            rgx = re.search("[\{\}\[\]\(\)'\"\\\\]", remainder)
            if rgx is None:
                R = -1
            else:
                R = rgx.start()
            m = min(S,R)
            if m==-1:
                m = max(S,R)
                if m==-1:
                        assert(remainder.strip()=="")
                        break
           
            try:
                buff = buff + remainder[:m+1]
            except:
                pdb.set_trace()
            remainder = remainder[m+1:]
            
            if m == R:
               c = buff[-1] 
               l = seekstack[-1] if len(seekstack)>0 else ""


               if l == "'" or l == '"':
                   if c == "\\":
                       buff = buff + remainder[0]
                       remainder = remainder[1:]
                   elif c==l:
                        seekstack.pop()
               elif c==complement[l]:
                    seekstack.pop()
               else:
                   seekstack.append(c)               

            if m == S and len(seekstack)==0:
                if len(self.bodyLines)>0 and self.bodyLines[-1].strip().split()[0]=="if" and buff.strip().split()[0]=="else": #Append up (if-)else[if-else...]
                    self.bodyLines[-1] = self.bodyLines[-1] + buff
                else:
                    self.bodyLines.append(buff)
                buff = ""
            if m == R and buff[-1]=="}" and len(seekstack)==0:

                if len(self.bodyLines)>0 and self.bodyLines[-1].strip().split()[0]=="do" and buff.strip().split()[0]=="while" and buff[-1]==";": # Append up (do-)while
                    self.bodyLines[-1] = self.bodyLines[-1] + buff
                elif len(self.bodyLines)>0 and self.bodyLines[-1].strip().split()[0]=="if" and buff.strip().split()[0]=="else": #Append up (if-)else[if-else...]
                    self.bodyLines[-1] = self.bodyLines[-1] + buff
                elif len(self.bodyLines)>0 and self.bodyLines[-1].strip().split()[0]=="try" and buff.strip().split()[0]=="catch": #Append up (try-)catch
                    self.bodyLines[-1] = self.bodyLines[-1] + buff
                elif len(self.bodyLines)>0 and self.bodyLines[-1].strip().split()[0]=="try" and buff.strip().split()[0]=="finally": #Append up (try-[catch]+-)finally
                    self.bodyLines[-1] = self.bodyLines[-1] + buff
                else:
                    self.bodyLines.append(buff)
                buff = ""
         

        self.deps = set()

    def __repr__(self):
        return "JavaMethod ("+self.selfname+")"

    def gatherDeps(self):
        if len(self.deps) > 0:
            return self.deps 

        #if self.AST.name=="KeyLevelRoomMapping":
        #    pdb.set_trace()

        #if self.getMethodName()=="dip2px":
        #    pdb.set_trace()
        
        methodLocalVars = dict()
        if isinstance(self.AST, javalang.tree.MethodDeclaration): # TODO class subclasses really shouldn't fall here
            for formalParameter in self.AST.parameters:
                methodLocalVars[formalParameter.name] = formalParameter.type

        for i, bl in enumerate(self.bodyLines):
            try:
                lineDeps = gatherCalls(bl, self.AST.body[i], self.cleaned_ms)
            except:
                pdb.set_trace()

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
                        dep.contextualize(methodLocalVars[dep.methodOf.split(".")[0]])

            # Update that context list
            if isinstance(self.AST.body[i], javalang.tree.LocalVariableDeclaration):
                t = self.AST.body[i].type
                for d in self.AST.body[i].declarators:
                    methodLocalVars[d.name] = t

            self.deps |= lineDeps
       
        # We should now contextualize all these calls

        return self.deps

    def getMethodName(self):
        return self.AST.name

    def constructDGL(self):
        DGL = DepGL()
        DGL.register_method(self, self.deps)
        DGL.attempt_resolve()
        return DGL

class JavaClass:
    def __init__(self, lbf, cbf, cs): # Line buffer, cleaned buffer (aligned with line buffer), and cleaned class string # TODO later dcs
        #pdb.set_trace()

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
        #paranLevel = 0
        seekstack = []
        i = 0
        while remainder != "":
            S = remainder.find(";")
            if len(seekstack) != 0:
                S = -1
            rgx = re.search("[\{\}\(\)\[\]'\"\\\\]", remainder)
            if rgx is None:
                R = -1
            else:
                R = rgx.start()
            m = min(S,R)
            if m == -1:
                m = max(S,R)
                if m == -1:
                        assert(remainder.strip()=="")
                        break

            buff = buff + remainder[:m+1]
            remainder = remainder[m+1:]
            
            if m==R:
                c = buff[-1]
                l = seekstack[-1] if len(seekstack)>0 else ""


                if l == "'" or l == '"':
                    if c == "\\":
                        buff =buff + remainder[0]
                        remainder = remainder[1:]
                    elif c==l:
                        seekstack.pop()
                elif c==complement[l]:
                    seekstack.pop()
                else:
                    seekstack.append(c)

            if m == R and buff[-1]=="}" and len(seekstack)==0 and (isinstance(self.AST.body[i],javalang.tree.MethodDeclaration) or isinstance(self.AST.body[i],javalang.tree.ClassDeclaration) or isinstance(self.AST.body[i],javalang.tree.ConstructorDeclaration) or isinstance(self.AST.body[i],javalang.tree.InterfaceDeclaration)):
                try:
                    methodStrs.append((buff,self.AST.body[i]))
                except:
                    pdb.set_trace()
                buff = ""
                i += 1
            elif m==S and len(seekstack)==0 and buff==";": # Happens after enum declarations, which we treat as methods
                buff = ""
            elif m == S and len(seekstack)==0:
                if isinstance(self.AST.body[i],javalang.tree.MethodDeclaration):
                    methodStrs.append((buff,self.AST.body[i]))
                else:
                    self.fieldAssigns.append((buff,self.AST.body[i]))
                buff = ""
                i += 1

        #if self.AST.name=="DungeonGenerator":
        #    pdb.set_trace()

        self.methods = []
        for i, ms in enumerate(methodStrs):
            try:
                self.methods.append(JavaMethod(lbf, cbf, ms[0], ms[1]))#, dirtyCSs[i])
            except Exception as e:
                if str(e) == "isinterface":
                    continue
                else:
                    raise



        self.deps = set()

    def __repr__(self):
        return "JavaClass ("+self.selfname+")"

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
        self.extension = ""
        if self.AST.extends is not None:
            for _, node in self.AST.extends.filter(javalang.tree.ReferenceType):
                self.extension = ClassDep(node.name)
                self.deps.add(self.extension)

        # PART 2, FIELD ASSIGNS
        self.faDeps = set()
        for fa in self.fieldAssigns:
            self.faDeps |= set(gatherCalls(fa[0], fa[1], self.cleaned_cs, fieldDeclaration = True))
        self.deps |= self.faDeps

        # PART 3, METHODS
        for m in self.methods:
            self.deps |= set(m.gatherDeps())

        # handle non-contextualized deps to fields of this clas by getting the fields' types and contextualizing them
        # First Gather Field Assigns' Types
        fields = dict()
        for fa in self.fieldAssigns:
            try:
                for vd in fa[1].declarators:
                    fields[vd.name] = fa[1].type
            except:
                if isinstance(fa[1], javalang.tree.EnumDeclaration):
                    fields[fa[1].name] = "enum"
                else:
                    raise
        # Then look thru them
        for dep in self.deps:
            if isinstance(dep, MethodCall) and not dep.hasContext:
                if dep.methodOf.split(".")[0] in fields:
                    dep.contextualize(fields[dep.methodOf.split(".")[0]])


        #  predicateless methods are of this class, note it down or bear in mind for graph construction by not propping them further
        # 1) Do not separately register dependencies to inherited methods as they are implicit; instead, make them a dependency on the inherited, and also make methods note this is applicable (i.e. not a FA)
        newdeps = set()
        depsToRemoveFromMethods = set()
        for dep in self.deps:
            if isinstance(dep, MethodCall) and (dep.methodOf == None or dep.methodOf == "" or dep.methodOf== "self") and dep.methodName not in [m.getMethodName() for m in self.methods]: # Inherited method call
                # No need to add extension to deps list, but only to those of the methods that gave it
                # Add to list to remove from methods' deps
                depsToRemoveFromMethods.add(dep)
            else:
                newdeps.add(dep)
        self.deps = newdeps
        # Remove from methods' deps
        for m in self.methods:
            prelen = len(m.deps)
            m.deps = m.deps - depsToRemoveFromMethods
            if len(m.deps) != prelen:
                #if self.extension =="":
                    #pdb.set_trace()
                m.deps.add(self.extension)

        # 2) Do not pass to file any internal methods' dependencies
        return self.stripSelfRefs(self.deps)

    def getClassName(self):
        return self.AST.name

    def constructDGL(self):
        DGL = DepGL()
        deps = set()
        deps |= self.faDeps
        if self.extension != "":
            deps.add(self.extension)
        for m in self.methods:
            deps.add(m)
        DGL.register_class(self, deps)
        for m in self.methods:
            DGL.addDGL(m.constructDGL())
        DGL.attempt_resolve()
        return DGL

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
        if (pkgline[0] == "package"):
            self.packageName = pkgline[1].split(";")[0]
            assert(len(pkgline)==2 or (len(pkgline)==3 and pkgline[2] ==";"));
        else:
            self.packageName = "not_in_package"
       
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
        seekstack = []
        classStrs = []
        while remainder != "":
            rgx = re.search("[\[\]\{\}\(\)'\"\\\\]", remainder)
            if rgx is None:
                m = -1
            else:
                m = rgx.start()
            if m == -1:
                        assert(remainder.strip()=="")
                        break
                    #classbuffer = classbuffer + remainder
                    #classStrs.append(classbuffer)
            classbuffer = classbuffer + remainder[:m+1]
            remainder = remainder[m+1:]
           
            if True:
                c = classbuffer[-1]
                l = seekstack[-1] if len(seekstack)>0 else ""

                if l == "'" or l == '"':
                    if c == "\\":
                        classbuffer = classbuffer + remainder[0]
                        remainder = remainder[1:]
                    elif c==l:
                        seekstack.pop()
                elif c==complement[l]:
                    seekstack.pop()
                else:
                    seekstack.append(c)
            

            if len(seekstack)==0 and classbuffer[-1]=="}":
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

        print("instances created")

    def __repr__(self):
        return "JavaFile at "+self.filepath + " for package "+self.packageName

    def gatherDeps(self):
        print("deps gathering for ", self.filepath)
       
        if len(self.deps) > 0:
            return self.deps 

        for c in self.classes:
            self.deps |= set(c.gatherDeps())

        return self.deps

    def constructDGL(self):
        DGL = DepGL()
        deps = set()
        #for c in self.classes:
        #    deps.add(ClassInc(c))
        deps |= set(self.classes)
        DGL.imports = list()
        for imp in self.imports:
            ci = ClassImp(imp)
            deps.add(ci)
            DGL.imports.append(ci)
        DGL.register_file(self, deps)
        for c in self.classes:
            DGL.addDGL(c.constructDGL())
        DGL.attempt_resolve()
        return DGL

def constructDep(files):
    # We want to have a list of JavaFiles, JavaClasses, and JavaMethods
    # At each level, we want a partial list of all of the applicable ones, alongside a dictionary listing remaining deps
    # We will process at each level all orderable deps at that level, yielding up only what we cannot resolve
    # At top level, we will try to resolve what we can, but will go the heuristic route if we cannot

    #pdb.set_trace()
    DGL = DepGL()
    for file in files:
        DGL.addDGL(file.constructDGL())
    print("All files constructed DGL")
    DGL.attempt_resolve()
    print("Soft attempt done")
    DGL.customPkgs = list()
    for file in files:
        if file.packageName != "not_in_package":
            DGL.customPkgs.append(file.packageName)
    return DGL.force_resolve()

def parseDependencies():
    # Generate List of Java files
    javaList = listJavaFiles("tmp")

    # For each Java file, find methods, find dependencies
    files = [JavaFile(path) for path in javaList]
    [jf.gatherDeps() for jf in files]

    # Construct graph of dependencies, including external ones
    # (Retrieve external dependencies' comments, if available)
    # Create traversal order for dependencies, keep in mind inheritances and calls (calls include field assignments and in-method calls)
    dependencyList = constructDep(files)
    return dependencyList


if __name__ == "__main__":
    #pdb.set_trace()
    print(parseDependencies())
