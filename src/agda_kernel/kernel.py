from ipykernel.kernelbase import Kernel
import re
import subprocess
import os
from IPython.utils.tokenutil import token_at_cursor, line_at_cursor
from subprocess import Popen, PIPE, STDOUT
import pexpect

AGDA_STATUS_ACTION = "agda2-status-action"
AGDA_INFO_ACTION = "agda2-info-action"
AGDA_GIVE_ACTION = "agda2-give-action"
AGDA_MAKE_CASE_ACTION = "agda2-make-case-action"

AGDA_ERROR = "*Error*"
AGDA_NORMAL_FORM = "*Normal Form*"
AGDA_ALL_DONE = "*All Done*"
AGDA_ALL_GOALS = "*All Goals*"
AGDA_GOAL_TYPE_ETC = "*Goal type etc.*"
AGDA_CHECKED = "Checked"
AGDA_INFERRED_TYPE = "*Inferred Type*"
AGDA_AUTO = "*Auto*"
AGDA_TYPECHECKING = "*Type-checking*"

AGDA_CMD_LOAD = "Cmd_load"
AGDA_CMD_INFER = "Cmd_infer"
AGDA_CMD_INFER_TOPLEVEL = "Cmd_infer_toplevel"
AGDA_CMD_GOAL_TYPE_CONTEXT_INFER = "Cmd_goal_type_context_infer"
AGDA_CMD_AUTOONE = "Cmd_autoOne"
AGDA_CMD_COMPUTE = "Cmd_compute"
AGDA_CMD_COMPUTE_TOPLEVEL = "Cmd_compute_toplevel"
AGDA_CMD_REFINE_OR_INTRO = "Cmd_refine_or_intro"
AGDA_CMD_MAKE_CASE = "Cmd_make_case"

class AgdaKernel(Kernel):
    implementation = 'agda'
    implementation_version = '0.3'
    language = 'agda'
    language_version = '0.3'
    language_info = {
        'name': 'agda',
        'mimetype': 'text/agda',
        'file_extension': '.agda',
    }

    banner = "Agda kernel"
    cells = {}

    '''
    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            self._banner = check_output(['bash', '--version']).decode('utf-8')
        return self._banner

    '''

    #process = Popen(['agda', '--interaction'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    process = pexpect.spawnu('agda --interaction')

    firstTime = True

    def startAgda(self):

        if self.firstTime:
            self.process.expect('Agda2> ')
            self.firstTime = False

        return

    # return line and column of an position in a string
    def line_of(self, s, n):

        lines = s.split('\n')
        
        i = 0 # current line
        j = 0 # cumulative length

        found = False

        for line in lines:

            if n >= j and n <= j + len(line):
                found = True
                break

            self.print(f'line {i} has length {len(line)}, cumulative {j}')

            i += 1
            j += len(line) + 1 # need to additionally record the '\n'

        if found:
            return i, n - j
        else:
            return -1, -1

    def interact(self, cmd):

        self.print("Telling Agda: %s" % cmd)
        
        #cmd = cmd.encode() # create a byte representation
        #result = self.process.communicate(input=cmd)[0]

        #cmd = cmd + "\n"
        self.process.sendline(cmd)
        self.process.expect('Agda2> ')
        result = str(self.process.before) # str(...) added to make lint happy

        #skip the first line (it's a copy of cmd)
        result = result[result.index('\n')+1:]

        #result = result.decode()
        self.print(f'Agda replied: {result}')

        lines = result.split('\n')

        result = {}
        
        #parse the response
        for line in lines:
            start = line.find("agda2")
            # parse only lines containing "agda2", and from that position on
            if start != -1:

                tokens = line[start:].split(' ')
                key = tokens[0]
                rest = line[start + len(key):]

                # extract all the strings in quotation marks "..."
                rest = rest.replace("\\\"", "§") # replace \" with §
                values = re.findall('"([^"]*)"', rest) # find all strings in quotation marks "..."
                values = [val.replace("§", "\"") for val in values] # replace § with " (no escape)

                if not key in result:
                    result[key] = []

                # add the new values to the dictionary
                result[key].append(values)

        self.print("result: %s" % result)

        return result

    def getModuleName(self, code):

        code = self.removeComments(code)
        lines = code.split('\n')

        #look for the first line matching "module name where"
        for line in lines:
            if bool(re.match(r'module *[a-zA-Z0-9.\-]* *where', line)):
                # fileName = "tmp/" + re.sub(r"-- *", "", firstLine)
                moduleName = re.sub(r'module *', "", line)
                moduleName = re.sub(r' *where *', "", moduleName)
                moduleName = moduleName #[:-1] # apparently it produces an extra space at the end

                return moduleName

        return ""

    def getFileName(self, code):

        moduleName = self.getModuleName(code)
        return moduleName.replace(".", "/") + ".agda" if moduleName != "" else ""

    def getDirName(self, code):

        moduleName = self.getModuleName(code)
        last = moduleName.rfind(".")
        prefixName = moduleName[:last]
        return prefixName.replace(".", "/") if last != -1 else ""

    def do_shutdown(self, restart):
        return

    def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):

        self.startAgda()
        fileName = self.getFileName(code)
        dirName = self.getDirName(code)

        self.print(f'detected fileName: {fileName}, dirName: {dirName}')
        error = False

        if fileName == "":
            err = "Error: the first line of the cell should be in the format \"module [modulename] where\""
            result = err
        else:
            #self.log.error("file: %s" % fileName)

            if dirName != "" and not os.path.exists(dirName):
                os.makedirs(dirName)

            lines = code.split('\n')
            numLines = len(lines)

            fileHandle = open(fileName, "w+")

            for i in range(numLines):
                fileHandle.write("%s\n" % lines[i])

            fileHandle.close()

            #subprocess.run(["agda", fileName])
            #result = os.popen("agda %s" % fileName).read()

            result, error = self.runCmd(code, -1, -1, "", AGDA_CMD_LOAD)
            result = deescapify(result)

            try:
                #remove the .agdai file
                agdai = fileName + "i"
                os.remove(agdai)
            except:
                print("*.agdai file not found")

        # self.log.error("output: %s" % result)

            if result == "":
                result = "OK"

            #save the result of the last evaluation
            self.cells[fileName] = result

        if not silent or err != "":
            stream_content = {'name': 'stdout', 'text': result}
            try:
                self.send_response(self.iopub_socket, 'stream', stream_content)
            except AttributeError: # during testing there is no such method, just ignore
                self.print("Ignoring call to self.send_response")

        return {'status': 'ok' if not error else 'error',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }
               
    def inComment(self, code, pos):

        # check whether there is a "--" on the left of pos, but not going to the previous line
        while pos >= 0 and code[pos:pos+1] != "\n":
            if code[pos:pos+2] == "--":
                return True
            pos -= 1

        return False

    def find_expression(self, code, cursor_pos):

        forbidden = [" ", "\n", "(", ")", "{", "}", ":"]
        length = len(code)

        hole_left = cursor_pos
        # go left until you find the beginning of a hole
        while code[hole_left : hole_left + 2] != "{!" and hole_left > 0:
            hole_left -= 1

        hole_left_found = code[hole_left : hole_left + 2] == "{!" and not self.inComment(code, hole_left)

        self.print(f'found hole left? {hole_left_found}')

        hole_right = cursor_pos - 2
        # go right until you find the beginning of a hole
        while code[hole_right : hole_right + 2] != "!}" and hole_right < length:
            hole_right += 1

        hole_right_found = code[hole_right : hole_right + 2] == "!}" and not self.inComment(code, hole_right)

        self.print(f'found hole right? {hole_right_found}')

        # check if the cursor is inside a hole
        if hole_left_found and hole_right_found:
            start = hole_left
            end = hole_right + 2
            expression = code[start : end]
            self.print(f'found hole left {start} and right {end}: token = {expression}')
        else:

            self.print(f'going for spaces')

            start = cursor_pos

            while start >= 1 and code[start - 1:start] not in forbidden:
                start -= 1

            end = cursor_pos

            while end < length and code[end] not in forbidden:
                end += 1

            expression = code[start : end]

        expression = escapify(expression)
             
        self.print(f'considering expression: \"{expression}\"')
        return start, end, expression

    def isHole(self, exp):
        result = exp == "?" or re.search("\\{!.*!\\}", exp) != None
        #self.log.error(f'the expression "{exp}" is a hole? {result}')
        return result

    def runCmd(self, code, cursor_start, cursor_end, exp, cmd):

        fileName = self.getFileName(code)
        absoluteFileName = os.path.abspath(fileName)

        self.print(f"running command: {cmd}")

        if fileName == "":
            return "empty filename", True
        
        if (fileName not in self.cells or self.cells[fileName] == "") and cmd != AGDA_CMD_LOAD:
            return "the cell should be evaluated first", True

        if cmd != AGDA_CMD_LOAD:
            # find out line and column of the cursors
            row1, col1 = self.line_of(code, cursor_start)
            row2, col2 = self.line_of(code, cursor_end)

            intervalsToRange = f'(intervalsToRange (Just (mkAbsolute "{absoluteFileName}")) [Interval (Pn () {cursor_start+1} {row1+1} {col1+1}) (Pn () {cursor_end+1} {row2+1} {col2+1})])'
            interactionId = self.findCurrentHole(code, cursor_start)

            if row1 == -1 or row2 == -1: # should not happen
                return "Internal error", True

        inside_exp = exp[2:-2]
        result = ""

        if cmd == AGDA_CMD_LOAD:
            query = f'IOTCM "{absoluteFileName}" NonInteractive Indirect (Cmd_load "{absoluteFileName}" [])'
        elif cmd == AGDA_CMD_INFER:
            query = f'IOTCM "{absoluteFileName}\" NonInteractive Indirect ({AGDA_CMD_INFER} Simplified {interactionId} {intervalsToRange} "{exp}")'
        elif cmd == AGDA_CMD_INFER_TOPLEVEL:
            query= f'IOTCM "{absoluteFileName}\" None Indirect ({AGDA_CMD_INFER_TOPLEVEL} Simplified "{exp}")'
        elif cmd == AGDA_CMD_GOAL_TYPE_CONTEXT_INFER:
            query = f'IOTCM "{absoluteFileName}\" NonInteractive Indirect ({AGDA_CMD_GOAL_TYPE_CONTEXT_INFER} Simplified {interactionId} {intervalsToRange} "{exp}")'
        elif cmd == AGDA_CMD_AUTOONE:
            hints = exp #"" if exp == "?" else inside_exp
            query = f'IOTCM \"{absoluteFileName}\" NonInteractive Indirect ({AGDA_CMD_AUTOONE} {interactionId} {intervalsToRange} "{hints}")'
        elif cmd == AGDA_CMD_COMPUTE:
            query = f'IOTCM \"{absoluteFileName}\" NonInteractive Indirect ({AGDA_CMD_COMPUTE} DefaultCompute {interactionId} {intervalsToRange} "{exp}")'
        elif cmd == AGDA_CMD_COMPUTE_TOPLEVEL:
            query = f'IOTCM \"{absoluteFileName}\" None Indirect ({AGDA_CMD_COMPUTE_TOPLEVEL} DefaultCompute "{exp}")'
        elif cmd == AGDA_CMD_REFINE_OR_INTRO:
            flag = "False" # "True" if the goal has functional type
            query = f'IOTCM \"{absoluteFileName}\" NonInteractive Indirect ({AGDA_CMD_REFINE_OR_INTRO} {flag} {interactionId} {intervalsToRange} "{inside_exp}")'
        elif cmd == AGDA_CMD_MAKE_CASE:
            query = f'IOTCM \"{absoluteFileName}\" NonInteractive Indirect ({AGDA_CMD_MAKE_CASE} {interactionId} {intervalsToRange} "{inside_exp}")'
        else:
            return f"Unrecognised command: {cmd}", True
        
        # send the type query to agda
        response = self.interact(query)

        if AGDA_INFO_ACTION in response:
            info_action_type, info_action_message = response[AGDA_INFO_ACTION][0][0], deescapify(response[AGDA_INFO_ACTION][0][1])
        else:
            info_action_type, info_action_message = "", ""

        if info_action_type == AGDA_ERROR:
            return f'ERROR: {info_action_message}', True
        elif info_action_type == AGDA_INFERRED_TYPE:
            inferred_type = info_action_message
            return f'{exp} : {inferred_type}', False # if inferred_type != "" else str(response)
        elif info_action_type == AGDA_GOAL_TYPE_ETC:
            return info_action_message, False
        elif info_action_type == AGDA_AUTO:
            return info_action_message, True
        elif info_action_type == AGDA_NORMAL_FORM:
            return info_action_message, False
        elif info_action_type in [AGDA_ALL_DONE, AGDA_ALL_GOALS]:
            if AGDA_GIVE_ACTION in response:
                result = response[AGDA_GIVE_ACTION][0]
                if len(result) > 0:
                    return result[0], False
        elif AGDA_MAKE_CASE_ACTION in response: # in this case we need to parse Agda's response again
            case_list = response[AGDA_MAKE_CASE_ACTION][0]
            result = "\n".join(case_list)
            self.print(f"Case list: {result}")
            return result, False
        elif cmd == AGDA_CMD_LOAD:
            if AGDA_INFO_ACTION in response:
                result = "\n".join(list(map(lambda info: " ".join(info), response[AGDA_INFO_ACTION])))
                return result, False

        return str(response), True

    # get the type of the current expression
    # triggered by SHIFT+TAB
    def do_inspect(self, code, cursor_pos, detail_level=0):

        # update with the current cell contents
        self.do_execute(code, False)

        cursor_start, cursor_end, exp = self.find_expression(code, cursor_pos)
        cursor_start += 1
        
        if(self.isHole(exp)):

            if exp != "?":
                exp = exp[2:-2] # strip the initial "{!" and final "!}"
                self.print(f'considering inside exp: {exp}')

            result1, error1 = self.runCmd(code, cursor_pos, cursor_end, exp, AGDA_CMD_GOAL_TYPE_CONTEXT_INFER)
            result2, error2 = self.runCmd(code, cursor_pos, cursor_end, exp, AGDA_CMD_INFER)
            result3, error3 = self.runCmd(code, cursor_pos, cursor_end, exp, AGDA_CMD_COMPUTE)

            result = result1 + "\n===========\nInfer: " + result2 + "\n===========\nCompute: " + result3
            error = error1 or error2 or error3
        else:
            result, error = self.runCmd(code, cursor_pos, cursor_end, exp, AGDA_CMD_INFER_TOPLEVEL)

        data = {}
        
        if result != "":
            data['text/plain'] = result

        content = {
            # 'ok' if the request succeeded or 'error', with error information as in all other replies.
            'status' : 'error' if error else 'ok',

            # found should be true if an object was found, false otherwise
            'found' : True if result != "" else False,

            # data can be empty if nothing is found
            'data' : data,
            'metadata' : data
        }

        return content

    # handle unicode completion here
    def do_complete(self, code, cursor_pos):

        half_subst = {
            'Nat' : 'ℕ',
            '<=<>' : '≤⟨⟩',
            '<==<>' : '≤≡⟨⟩',
            '=<>' : '≡⟨⟩',
            'top' : '⊤',
            'bot' : '⊥',
            'neg' : '¬',
            '/\\' : '∧',
            '\\/' : '∨',
            '\\' : 'λ', # it is important that this comes after /\
            'Pi' : 'Π',
            'Sigma' : 'Σ',
            '->' : '→',
            '<' : '⟨',
            '>' : '⟩', # it is important that this comes after ->
            'forall' : '∀',
            'exists' : '∃',
            'A' : '𝔸',
            'B' : '𝔹',
            'C' : 'ℂ',
            'N' : 'ℕ',
            'Q' : 'ℚ',
            'R' : 'ℝ',
            'Z' : 'ℤ',
            '/=' : '≢',
            '<=' : '≤',
            '=' : '≡',
            '[=' : '⊑',
            'alpha' : 'α',
            'beta' : 'β',
            'e' : 'ε',
            'xor' : '⊗',
            'emptyset' : '∅',
            'qed' : '∎',
            '.' : '·',
            'd' : '∇',
            'notin' : '∉',
            'in' : '∈',
            '[' : '⟦',
            ']' : '⟧',
            '::' : '∷',
            '0' : '𝟬', # '𝟢',
            '1' : '𝟭', # '𝟣'
            '+' : '⨁',
            '~' : '≈',
            'x' : '×',
            'o' : '∘',
            'phi' : 'φ',
            'psi' : 'ψ',
            '??' : "{! !}"
        }

        other_half = {val : key for (key, val) in half_subst.items()}
        subst = {**half_subst, **other_half} # merge the two dictionaries
        keys = [key for (key, val) in subst.items()]

        length = len(code)
        matches = []
        error = False

        for key in keys:
            n = len(key)
            cursor_start = cursor_pos - n
            cursor_end = cursor_pos
            s = code[cursor_start:cursor_pos]

            if s == key:
                # we have a match
                matches = [subst[key]]
                break

        # didn't apply a textual substitution
        if matches == []:

            # load the current contents
            self.do_execute(code, False)

            cursor_start, cursor_end, exp_orig = self.find_expression(code, cursor_pos)
            exp = escapify(exp_orig)
            #cursor_start += 1

            if exp == "?":
                # call Agsy, options: -c (case splitting) -m (hints) -r (refine) -l (list) -s k (select result k)
                """options = lambda k: f'  -m -s {k}  '
                k = 0
                while True:
                    result, error = self.runCmd(code, cursor_start, cursor_end, options(k), AGDA_CMD_AUTOONE)
                    self.log.error(f'result is: {result}, error is: {error}')
                    if error or result in ["No solution found", "No candidate found", "Only 1 solution found", f'Only {k} solutions found']:
                        if matches == []:
                            matches = ["{! !}"] # transform "?" into "{! !}" when Agsy fails

                        break
                    else:
                        matches += [result] if result != "" else []

                    k += 1
                """
                options = "-m -l" # list solutions
                result, error = self.runCmd(code, cursor_start, cursor_end, options, AGDA_CMD_AUTOONE)
                self.print(f'result is: {result}, error is: {error}')

                if result.find("Listing solution(s)") != -1:
                    # example: Listing solution(s) 20-29\n20  f (f a left left) y x\n21  f (f a right left) y x\n22  f (f a left right) y x\n23  f (f a right right) y x\n24  f (f a left left) x x\n25  f (f a right left) x x\n26  f (f a left right) x x\n27  f (f a right right) x x\n28  f a (f a y y) y\n29  f a (f a x y) y\n
                    lines = result.split('\n')[1:-1] # skip the first and last lines
                    for line in lines:
                        tokens = line.split(' ') 
                        self.print(f"line is: {line}, tokens is: {tokens}")
                        solution = " ".join(tokens[2:]) # skip the first "20  " (plus the extra space!) and put the tokens back
                        matches += [solution]
                elif error or result in ["No solution found", "No candidate found"]:
                     matches = ["{! !}"] # transform "?" into "{! !}" when Agsy fails
                else:
                    self.print(f'Unexpected answer: {result}, error is: {error}')
                
            elif self.isHole(exp):

                result, error = self.runCmd(code, cursor_start, cursor_end, exp, AGDA_CMD_REFINE_OR_INTRO)

                if error: # try case
                    # need to reload to make it work
                    _, _ = self.runCmd(code, -1, -1, "", AGDA_CMD_LOAD)
                    result, error = self.runCmd(code, cursor_start, cursor_end, exp, AGDA_CMD_MAKE_CASE)

                    if error:
                        cursor_start, cursor_end = cursor_pos, cursor_pos
                    else:
                        # need to replace the current whole row with result
                        while cursor_start > 0 and code[cursor_start - 1] != "\n":
                            cursor_start -= 1
                        while cursor_end < length and code[cursor_end] != "\n":
                            cursor_end += 1

                matches = [result] if result != "" else []

           # the hole is not of the form "?"
           #if matches == []:

        return {'matches': sorted(matches), 'cursor_start': cursor_start,
                'cursor_end': cursor_end, 'metadata': {},
            'status': 'ok' if not error else 'error'}

    def findAllHoles(self, code):
        i = 0
        length = len(code)
        holes = []

        while i < length:
            if code[i:i+2] == "--": # we are in a comment
                while i < length and code[i] != "\n":
                    i += 1 # skip to the end of the line
            elif code[i:i+1] == "?" and i+1 == length:
                holes.append((i, i+1))
                i += 1
            elif code[i:i+3] in [" ?\n", " ? "] or (code[i:i+2] == " ?" and i+2 == length):
                holes.append((i+1, i+2))
                i += 2
            elif code[i:i+2] == "{!": # beginning of a hole
                start = i
                i += 2
                while i < length: # find the end of the hole (no nested holes)
                    if code[i:i+2] == "!}":
                        holes.append((start, i+2))
                        i += 2
                        break
                    i += 1
            else:
                i += 1

        self.print(f'found holes: {holes}')
        return holes

    def findCurrentHole(self, code, pos):

        holes = self.findAllHoles(code)
        self.print(f'looking for hole at position: {pos}')

        k = 0
        for (i, j) in holes:
            if i <= pos and pos <= j: # allow the cursor to be one position to the right of the hole
                return k
            k += 1

        return -1 # no hole found

    def removeComments(self, code):

        level = 0
        i = 0
        length = len(code)
        result = ""

        while i < length:
            if level == 0 and code[i:i+2] == "--": # skip till the end of the line
                while i < length and code[i] != "\n":
                    i += 1

                result += "\n" if code[i:i+1] == "\n" else ""
            elif code[i:i+2] == "{-":
                level += 1
                i += 1
            elif code[i:i+2] == "-}" and level > 0:
                level -= 1
                i += 1
            elif level == 0:
                result += code[i]

            i += 1

        return result

    def print(self, msg):
        try:
            self.log.error(msg)
        except AttributeError:
            print(msg)

def escapify(s):
    # escape quotations, new lines
    result = s.replace("\"", "\\\"").replace("\n", "\\n")
    return result

def deescapify(s):
     # go back
    result = s.replace("\\\"", "\"").replace("\\n", "\n")
    return result