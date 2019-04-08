from ipykernel.kernelbase import Kernel
import re
import subprocess
import os
from IPython.utils.tokenutil import token_at_cursor, line_at_cursor
from subprocess import Popen, PIPE, STDOUT
import pexpect

AGDA_STATUS_ACTION = "agda2-status-action"
AGDA_INFO_ACTION = "agda2-info-action"

AGDA_ERROR = "*Error*"
AGDA_NORMAL_FORM = "*Normal Form*"
AGDA_ALL_DONE = "*All Done*"
AGDA_CHECKED = "Checked"
AGDA_INFERRED_TYPE = "*Inferred Type*"

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

        self.log.error(f'line {i} has length {len(line)}, cumulative {j}')

        i += 1
        j += len(line) + 1 # need to additionally record the '\n'

    if found:
        return i, n - j
    else:
        return -1, -1

class AgdaKernel(Kernel):
    implementation = 'agda'
    implementation_version = '0.2'
    language = 'agda'
    language_version = '0.2'
    language_info = {
        'name': 'Agda', # any text
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

    def interact(self, cmd):

        self.log.error("Telling Agda: %s" % cmd)
        
        #cmd = cmd.encode() # create a byte representation
        #result = self.process.communicate(input=cmd)[0]

        #cmd = cmd + "\n"
        self.process.sendline(cmd)
        self.process.expect('Agda2> ')
        result = str(self.process.before) # str(...) added to make lint happy

        #skip the first line
        result = result[result.index('\n')+1:]

        #result = result.decode()
        self.log.error("Agda replied: %s" % result)

        #TODO: extract agda2-info-action, agda2-status-action

        lines = result.split('\n')

        result = {}
        
        #parse the response
        for line in lines:
            
            # remove fist "(" and last ")"
            line = line[1:-2]
            self.log.error("line: %s" % line)

            tokens = line.split(' ')

            # parse only lines starting with "agda"
            if tokens[0].startswith("agda"):
                key = tokens[0]
                rest = line[len(key):]

                # extract all the strings in quotation marks "..."
                rest = rest.replace("\\\"", "§") # replace \" with §
                values = re.findall('"([^"]*)"', rest) # find all strings in quotation marks "..."
                values = [val.replace("§", "\"") for val in values] # replace § with " (no escape)

                if not key in result:
                    result[key] = []

                # add the new values to the dictionary
                result[key].append(values)

        self.log.error("result: %s" % result)

        return result

    def getModuleName(self, code):

        lines = code.split('\n')
        firstLine = lines[0]

        if not bool(re.match(r'module *[a-zA-Z0-9.\-]* *where', firstLine)):

            return ""

        else:

            # fileName = "tmp/" + re.sub(r"-- *", "", firstLine)
            moduleName = re.sub(r'module *', "", firstLine)
            moduleName = re.sub(r' *where', "", moduleName)
            moduleName = moduleName

            return moduleName

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

        self.log.error(f'detected fileName: {fileName}, dirName: {dirName}')

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

            cmd = f'IOTCM "{fileName}" NonInteractive Indirect (Cmd_load "{fileName}" [])'
            response = self.interact(cmd)

            result = ""

            for info in response[AGDA_INFO_ACTION]:
                result += info[0] + ("(" + info[1] + ")" if len(info) > 1 and len(info[1]) > 0 else "") + "\n"

            result = result.replace("\\n", "\n") # replace escaped \n with actual new line

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
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }
               
    def find_expression(self, code, cursor_pos):

        length = len(code)
        i = cursor_pos

        forbidden = [" ", "\n", "(", ")", "{", "}", ":"]

        if code[cursor_pos] in forbidden:
            # go left until you find a parenthesis
            while code[i] not in ["(", ")"] and i > 0:
                i -= 1

        start = i
        end = -1
        expression = ""
        p = code[start]

        # we found a parenthesis
        if p in ["(", ")"]:

            # if "(", go right to find the matching ")"
            # if ")", go left to find the matching "("

            q = "(" if p == ")" else ")" # the opposite parenthesis
            d = 1 if p == "(" else -1

            self.log.error(f'going for parentheses "{p}" and "{q}"; i = {i}, len = {length}')

            n = 0

            while i >= 0 and i < length:
                n += 1 if code[i] == p else -1 if code[i] == q else 0
                i += d

                if n == 0: # bingo!
                    end = i - d # undo the last step

                    if start > end: # swap if necessary
                        start, end = end, start

                    expression = code[start : end + 1]
                    self.log.error(f'bingo! i = {i}, n = {n}, token = {expression}')

                    break
        # no parentheses to be found
        else:

            self.log.error(f'going for spaces')

            start = cursor_pos - 1

            while start >= 0 and code[start] not in forbidden:
                start -= 1

            end = cursor_pos

            while end < length and code[end] not in forbidden:
                end += 1

            expression = code[start + 1 : end]

        expression = escapify(expression)
             
        self.log.error(f'considering expression: \"{expression}\"')
        return start, end, expression

    # get the type of the current expression
    # triggered by SHIFT+TAB
    def do_inspect(self, code, cursor_pos, detail_level=0):

        fileName = self.getFileName(code)
        cursor_start, cursor_end, exp = self.find_expression(code, cursor_pos)

        error = False

        if fileName != "" and exp != "":

            if fileName in self.cells and self.cells[fileName] != "":

                # find out line and column of the cursors
                line1, col1 = line_of(self, code, cursor_start)
                line2, col2 = line_of(self, code, cursor_end)

                if line1 == -1 or line2 == -1: # should not happen
                    result = "Internal error"
                else:
                    # send the type query to agda
                    cmd = f'IOTCM \"{fileName}\" None Indirect (Cmd_infer_toplevel Simplified \"{exp}\")'
                    #cmd = f'IOTCM \"{fileName}\" NonInteractive Indirect (Cmd_infer Simplified 0 (intervalsToRange (Just (mkAbsolute \"{fileName}\")) [Interval (Pn () {cursor_start+1} {line1+1} {col1+1}) (Pn () {cursor_end+1} {line2+1} {col2+1})]) \"{exp}\")'
                    response = self.interact(cmd)

                    inferred_type = ""
                    resp = deescapify(response[AGDA_INFO_ACTION][0][1])

                    if response[AGDA_STATUS_ACTION][0][0] in [AGDA_CHECKED, ""]:
                        if response[AGDA_INFO_ACTION][0][0] == AGDA_INFERRED_TYPE:
                            inferred_type = resp
                            result = f'{exp} : {inferred_type}' if inferred_type != "" else str(response)
                    
                    if response[AGDA_INFO_ACTION][0][0] == AGDA_ERROR:
                        result = f'{exp} : ERROR: {resp}'

            else:
                error = True
                result = "the cell should be evaluated first"
        else:
            result = ""

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
            'metadata' : {}
        }

        return content

    # handle unicode completion here
    def do_complete(self, code, cursor_pos):

        fileName = self.getFileName(code)

        half_subst = {
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
            '+' : "⨁"
        }

        other_half = {val : key for (key, val) in half_subst.items()}
        subst = {**half_subst, **other_half} # merge the two dictionaries
        keys = [key for (key, val) in subst.items()]

        matches = []

        for key in keys:
            n = len(key)
            cursor_start = cursor_pos - n
            cursor_end = cursor_pos
            s = code[cursor_start:cursor_pos]

            if s == key:
                # we have a match
                matches = [subst[key]]
                break

        # didn't apply a textual substitution, go for normalisation
        if matches == []:
            cursor_start, cursor_end, exp_orig = self.find_expression(code, cursor_pos)
            exp = escapify(exp_orig)
            cursor_start += 1

            if fileName != "" and exp != "":

                if fileName in self.cells and self.cells[fileName] != "":

                    pos1 = cursor_start
                    pos2 = cursor_end

                    line1, column1 = line_of(self, code, pos1)
                    line2, column2 = line_of(self, code, pos2)

                    if line1 == -1 or line2 == -1: # should not happen
                        result = "Internal error"
                    else:
                        # send the normalisation command to Agda
                        cmd = f'IOTCM \"{fileName}\" None Indirect (Cmd_compute_toplevel DefaultCompute \"{exp}\")'
                        #cmd = f'IOTCM \"{fileName}\" NonInteractive Indirect (Cmd_compute DefaultCompute 0 (intervalsToRange (Just (mkAbsolute \"{fileName}\")) [Interval (Pn () {pos1} {line1} {column1}) (Pn () {pos2} {line2} {column2})]) \"{exp}\")'
                        result = self.interact(cmd)

                        info = result[AGDA_INFO_ACTION][0]

                        code = info[0]
                        message = info[1]

                        if code == AGDA_NORMAL_FORM:
                            # return the normal form
                            self.log.error(f'agda gave us: {message}')
                            result = deescapify(message)
                            self.log.error(f'deescapified: {result}')

                            # remove parentheses if it was already in normal form
                            #if result == exp_orig:
                            #    cursor_start -= 1
                            #    cursor_end += 1
                                
                        elif code == AGDA_ERROR:
                            result = "" # "Error: " + message # there was an error
                        else:
                            result = "Unexpected error. Agda said:\n\n" + str(result)

                else:
                    result = "the cell should be evaluated first"

            matches = [result] if result != "" else []

        return {'matches': sorted(matches), 'cursor_start': cursor_start,
                'cursor_end': cursor_end, 'metadata': dict(),
            'status': 'ok'}

def escapify(s):
    # escape quotations, new lines
    result = s.replace("\"", "\\\"").replace("\n", "\\n")
    return result

def deescapify(s):
     # go back
    result = s.replace("\\\"", "\"").replace("\\n", "\n")
    return result
