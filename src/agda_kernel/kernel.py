from ipykernel.kernelbase import Kernel
import re
import subprocess
import os
import threading
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
AGDA_ALL_ERRORS = "*All Errors*"
AGDA_ALL_GOALS = "*All Goals*"
AGDA_ALL_GOALS_ERRORS = "*All Goals, Errors*"
AGDA_ALL_WARNINGS = "*All Warnings*"
AGDA_ALL_ERRORS_WARNINGS = "*All Errors, Warnings*"
AGDA_ALL_GOALS_WARNINGS = "*All Goals, Warnings*"
AGDA_ALL_GOALS_ERRORS_WARNINGS = "*All Goals, Errors, Warnings*"
AGDA_GOAL_TYPE_ETC = "*Goal type etc.*"
AGDA_CHECKED = "Checked"
AGDA_INFERRED_TYPE = "*Inferred Type*"
AGDA_AUTO = "*Auto*"
AGDA_TYPECHECKING = "*Type-checking*"
AGDA_INTRO = "*Intro*"

AGDA_ERROR_LIKE = [AGDA_ERROR, AGDA_ALL_ERRORS, AGDA_ALL_GOALS, AGDA_ALL_GOALS_ERRORS, AGDA_ALL_WARNINGS, AGDA_ALL_ERRORS_WARNINGS, AGDA_ALL_GOALS_WARNINGS, AGDA_ALL_GOALS_ERRORS_WARNINGS]

AGDA_CMD_LOAD = "Cmd_load"
AGDA_CMD_INFER = "Cmd_infer"
AGDA_CMD_INFER_TOPLEVEL = "Cmd_infer_toplevel"
AGDA_CMD_GOAL_TYPE_CONTEXT_INFER = "Cmd_goal_type_context_infer"
AGDA_CMD_AUTOONE = "Cmd_autoOne"
AGDA_CMD_AUTO = "Cmd_auto"
AGDA_CMD_COMPUTE = "Cmd_compute"
AGDA_CMD_COMPUTE_TOPLEVEL = "Cmd_compute_toplevel"
AGDA_CMD_REFINE_OR_INTRO = "Cmd_refine_or_intro"
AGDA_CMD_MAKE_CASE = "Cmd_make_case"
AGDA_CMD_GIVE = "Cmd_give"

class AgdaKernel(Kernel):
    implementation = 'agda'
    implementation_version = '0.5'
    language = 'agda'
    language_version = '2.6'
    language_info = {
        'name': 'agda',
        'mimetype': 'text/agda',
        'file_extension': '.agda',
    }

    banner = "Agda kernel"
    cells = {}
    last_code = ""

    agda_version = ""

    notebookName = ""
    cellId = ""
    preamble = ""

    unicodeComplete = True

    '''
    _banner = None

    @property
    def banner(self):
        if self._banner is None:
            self._banner = check_output(['bash', '--version']).decode('utf-8')
        return self._banner

    '''

    #lock = threading.Lock()

    #process = Popen(['agda', '--interaction'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    process = pexpect.spawnu('agda --interaction')

    firstTime = True

    def startAgda(self):
        if self.firstTime:
            self.process.expect('Agda2> ')
            self.print(f'Agda has started.')
            self.firstTime = False
        return

    def __init__(self, **kwargs):
        Kernel.__init__(self, **kwargs)
        self.agda_version = self.readAgdaVersion()
#        self.kernel_lock = threading.Lock()

    def sendResponse(self, text):
        try:
            self.send_response(self.iopub_socket, 'stream', {'name': 'stdout', 'text': text})
        except AttributeError: # during testing there is no such method, just ignore
            self.print("Ignoring call to self.send_response")

    def sendInfoResponse(self, text):
        # ignore otherwise
        if self.sendInfoMessages:
            try:
                self.send_response(self.iopub_socket, 'stream', {'name': 'stdinfo', 'text': text})
            except AttributeError: # during testing there is no such method, just ignore
                self.print("Ignoring call to self.send_response")

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

            # self.print(f'line {i} has length {len(line)}, cumulative {j}')

            i += 1
            j += len(line) + 1 # need to additionally record the '\n'

        if found:
            return i, n - j
        else:
            return -1, -1

    def readAgdaVersion(self):
        p = pexpect.spawn('agda --version')
        p.expect(pexpect.EOF)
        result = str(p.before)
        tokens = result.split(" ")
        version = tokens[2] # remove initial "Agda version "
        version = version[:-5] # remove trailing "\r\n"
        self.print(f'Detected Agda version: {version}')
        return version

    def interact(self, cmd):

        self.print("Interacting with Agda: %s" % cmd)

        #cmd = cmd.encode() # create a byte representation
        #result = self.process.communicate(input=cmd)[0]

        #cmd = cmd + "\n"
        self.process.sendline(cmd)
        result = ""

        while True:
            #this more robust version will survive an unexpected end of output from Agda
            prompt = self.process.expect([pexpect.TIMEOUT, pexpect.EOF, 'Agda2> ', '\(agda2-info-action "\*Type-checking\*"'], timeout=240)
            response = self.process.before
            result += response

            if prompt == 0 or prompt == 1:
                break
            elif prompt == 2:
                self.sendInfoResponse("DONE")
                break
            elif prompt == 3:
                # keep jupyter informed about agda's partial responses
                self.sendInfoResponse(response)
                continue

        #skip the first line (it's a copy of cmd)
        result = result[result.index('\n')+1:]

        #result = result.decode()
        self.print(f'Agda replied: {result}')

        lines = result.split('\n')

        result = {}
        
        # parse the response
        for line in lines:
            start = line.find("agda2")
            # parse only lines containing "agda2", and from that position on
            if start != -1:

                tokens = line[start:].split(' ')
                key = tokens[0]
                rest = line[start + len(key):]
                #rest = rest.replace("\\n", "\n")

                # extract all the strings in quotation marks "..."
                rest = rest.replace("\\\"", "§") # replace \" with §
                values = re.findall('"([^"]*)"', rest) # find all strings in quotation marks "..."
                values = [val.replace("§", "\"") for val in values] # replace § with " (no escape)

                if not key in result:
                    result[key] = []

                # in this case the format is "(agda2-give-action 0 'no-paren)"
                # return the goal index 0
                if key == AGDA_GIVE_ACTION:
                    result[key] = [tokens[1]]

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
                moduleName = re.sub(r'module *', "", line) # delete prefix
                moduleName = re.sub(r' *where.*', "", moduleName) # delete suffix

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

    def do_execute(self, in_code, silent, store_history=True, user_expressions=None, allow_stdin=False):

        self.startAgda()
        fileName = self.getFileName(in_code)
        dirName = self.getDirName(in_code)
        moduleName = self.getModuleName(in_code)
        absoluteFileName = os.path.abspath(fileName)

        preambleLength = 0

        self.sendInfoMessages = False

        if user_expressions and "sendInfoMessages" in user_expressions and user_expressions["sendInfoMessages"] == "yes":
            self.sendInfoMessages = True

        if user_expressions and "agdaCMD" in user_expressions:
            self.agdaCMD = user_expressions["agdaCMD"]
            self.print(f'agdaCMD = {self.agdaCMD}')
        else:
            self.print(f'agdaCMD NOT given')
            self.agdaCMD = "" # reset if not given

        # printing this may expose the user's github password
        # self.print(f'user_expressions: {user_expressions}')

        if user_expressions and "persistent" in user_expressions:
            persistent = user_expressions["persistent"] == "yes"
        else:
            persistent = False

        # set unicodeComplete only if passed in user_expressions;
        # otherwise, remember the previous value
        if user_expressions and "unicodeComplete" in user_expressions:
            self.unicodeComplete = user_expressions["unicodeComplete"] == "yes"

        if user_expressions and "loadFromStore" in user_expressions and user_expressions["loadFromStore"] == "yes":

            self.print(f'loadFromStore = yes')

            try:                
                fileHandle = open(fileName, "r+")
                code = fileHandle.read()
                fileHandle.close()
                self.print(f'executing code from file: {code}')
            except:
                self.print(f"file {fileName} not found, executing from given code")
                code = in_code

        else:
            code = in_code
            self.print(f'loadFromStore = no')
            self.print(f'executing code: {code}')

        if user_expressions:
            # get notebook name (if any)
            if "notebookName" in user_expressions:
                self.notebookName = user_expressions["notebookName"]

            # get cell id
            if "cellId" in user_expressions:
                self.cellId = user_expressions["cellId"]

            if "preamble" in user_expressions:
                self.preamble = user_expressions["preamble"]

        notebookName = self.notebookName
        cellId = self.cellId
        preamble = self.preamble

        #if notebookName == "":
        #    error = True
        #    self.print(f'empty notebook name!')
        #    result = "the cell should be evaluated first..."
        #else:
        error = False

        self.print(f'detected fileName: {fileName}, dirName: {dirName}, moduleName: {moduleName}, notebookName: {notebookName}, cellId: {cellId}, preamble: {preamble}')

        # use the provided preamble only if the module name is missing
        if fileName == "" and not error:

            # if no line \"module [modulename] where\" is provided,
            # we create a standard one ourselves
            preambleLength = len(preamble.split("\n")) - 1

            if preamble == "":
                error = True
                self.print(f'a preamble of the form "module xxx where" should be provided')
                result = 'a preamble of the form "module xxx where" should be provided'

            else:
                new_code = preamble + code

                fileName = self.getFileName(new_code)
                dirName = self.getDirName(new_code)
                moduleName = self.getModuleName(new_code)
                absoluteFileName = os.path.abspath(fileName)
                self.print(f'redetected fileName: {fileName}, dirName: {dirName}, moduleName: {moduleName}, notebookName: {notebookName}, cellId: {cellId}, new code: {new_code}')

                code = new_code

        if not error:

            self.fileName = fileName
            lines = code.split('\n')
            numLines = len(lines)

            self.print(f"writing to file: {fileName}")

            if dirName != "" and not os.path.exists(dirName):
                os.makedirs(dirName)

            fileHandle = open(fileName, "w+")

            for i in range(numLines):
                if i < numLines - 1:
                    fileHandle.write("%s\n" % lines[i])
                else:
                    fileHandle.write("%s" % lines[i])

            fileHandle.close()

            # if the persistent option is turned on, do a git commit
            if persistent:

                def git_push():
                    # push the changes
                    #branch = "main"

                    if user_expressions and "username" in user_expressions:
                        username = user_expressions["username"]
                    else:
                        self.print(f'No username provided')
                        username = ""

                    self.print(f'Pushing, username: {username}') #to branch {branch}')
                    self.sendInfoResponse(f'Pushing, username: {username}\n')

                    if user_expressions and "password" in user_expressions:
                        self.print("Storing password")
                        password = user_expressions["password"]
                        self.sendInfoResponse(f'Storing password\n')
                    else:
                        self.print("No password provided")
                        password = ""
                        self.sendInfoResponse('No password provided\n')

                    child = pexpect.spawn(f'git push origin')

                    while True:

                        prompt = child.expect([
                            "Username for 'https://github.com':",
                            f"Password for 'https://{username}@github.com':",
                            pexpect.EOF]
                        )

                        self.print(f'Prompt = {prompt}')
                        self.sendInfoResponse(f'Prompt = {prompt}\n')

                        if prompt == 0:
                            child.sendline(username)

                        elif prompt == 1:
                            child.sendline(password)
                                
                        elif prompt == 2:
                            child.close()
                            break

                    if child.exitstatus != 0:
                        text = child.before.decode()
                        self.print(text)
                        self.sendInfoResponse(text)

                    self.print(f'Pushed!')
                    self.sendInfoResponse("Pushed!")

                def persist(): #(self, fileName):

                    #with lock:
                        self.print(f'Git commit & push: {fileName}')

                        os.system('git pull')
                        os.system(f'git add {fileName}')
                        os.system(f'git commit -m "do_execute: updated {fileName}"')
                        self.print(f'Time to push...')
                        git_push()

                self.print(f'Persist is on, asynchronously committing to github')

                thr = threading.Thread(target=persist, args=(), kwargs={})
                thr.start()

            # load the code in Agda
            result, error = self.runCmd(code, -1, -1, "", AGDA_CMD_LOAD)
            result = deescapify(result)

            # try:
            #     #remove the .agdai file
            #     agdai = fileName + "i"
            #     os.remove(agdai)
            # except:
            #     self.print("*.agdai file '%s' not found" % agdai)

        # self.print("output: %s" % result)

            if result == "":
                result = "OK"

            #save the result of the last evaluation
            self.cells[fileName] = result

            # save the code that was executed
            self.code = code

        if not silent or error != "":
            self.sendResponse(result)

        # return all holes
        holes_as_pairs_of_positions = self.findAllHoles(code)

        # pairs are just lists of length 2 (join the lists)
        holes_as_positions = sum(map(lambda x: [x[0], x[1]], holes_as_pairs_of_positions), []) 
        #self.print(f'holes_as_positions = {holes_as_positions}')

        # replace each absolute position with the pair (line number, relative position)
        holes_as_lines_rel_pos = list(map(lambda x: self.line_of(code, x), holes_as_positions))

        # the first component is the line, the second the relative position within the line;
        # project to the line number;
        # additinally remove the shift possibly caused by the defaul preamble
        holes_as_lines = list(map(lambda x: x[0] - preambleLength, holes_as_lines_rel_pos)) 
        #self.print(f'holes_as_lines = {holes_as_lines}')

        # remove trailing newlines
        code = code.rstrip('\n')

        user_expressions_return = {
            "fileName": absoluteFileName,
            "moduleName": moduleName,
            "holes": holes_as_lines,
            "preambleLength" : preambleLength,
            "isError": error,
            "code": code,
            "result": result # return the agda response here too for further processing
        }

        self.print(f"Returning user_expressions_return: {user_expressions_return}")

        return {'status': 'ok' if not error else 'error',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': user_expressions_return,
               }

    # def do_execute(self, in_code, silent, store_history=True, user_expressions=None, allow_stdin=False):
    #     with self.kernel_lock:
    #         return self._do_execute(in_code, silent, store_history, user_expressions, allow_stdin)
     
    def inComment(self, code, pos):

        # check whether there is a "--" on the left of pos, but not going to the previous line
        while pos >= 0 and code[pos:pos+1] != "\n":
            if code[pos:pos+2] == "--":
                return True
            pos -= 1

        return False

    def find_expression(self, code, cursor_pos):

        forbidden = [" ", "\n", "(", ")", "{", "}", ":", ";"]
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
        self.print(f'the expression "{exp}" is a hole? {result}')

        return result

    def runCmd(self, code, cursor_start, cursor_end, exp, cmd):

        fileName = self.fileName if hasattr(self, 'fileName') else self.getFileName(code)
        absoluteFileName = os.path.abspath(fileName)

        self.print(f"running command: {cmd}, cursor_start: {cursor_start}, cursor_end: {cursor_end}")

        if fileName == "":
            return "empty filename", True

        if (fileName not in self.cells or self.cells[fileName] == "") and cmd != AGDA_CMD_LOAD:
            return "the cell should be evaluated first", True

        if cmd != AGDA_CMD_LOAD:
            # find out line and column of the cursors
            row1, col1 = self.line_of(code, cursor_start)
            row2, col2 = self.line_of(code, cursor_end)

            if self.agda_version <= "2.5.1":
                intervalsToRange = f'(Range [Interval (Pn (Just (mkAbsolute "{absoluteFileName}")) {cursor_start+1} {row1+1} {col1+1}) (Pn (Just (mkAbsolute "{absoluteFileName}")) {cursor_end+1} {row2+1} {col2+1})])'
            else:
                intervalsToRange = f'(intervalsToRange (Just (mkAbsolute "{absoluteFileName}")) [Interval (Pn () {cursor_start+1} {row1+1} {col1+1}) (Pn () {cursor_end+1} {row2+1} {col2+1})])'

            interactionId = self.findCurrentHole(code, cursor_start)

            if row1 == -1 or row2 == -1: # should not happen
                return "Internal error", True

        inside_exp = exp[2:-2]
        result = ""

        if cmd == AGDA_CMD_LOAD:
            query = f'IOTCM "{absoluteFileName}" NonInteractive Indirect (Cmd_load "{absoluteFileName}" [])'
        elif cmd == AGDA_CMD_INFER:
            query = f'IOTCM "{absoluteFileName}" NonInteractive Indirect ({AGDA_CMD_INFER} Simplified {interactionId} {intervalsToRange} "{exp}")'
        elif cmd == AGDA_CMD_INFER_TOPLEVEL:
            query = f'IOTCM "{absoluteFileName}" None Indirect ({AGDA_CMD_INFER_TOPLEVEL} Simplified "{exp}")'
        elif cmd == AGDA_CMD_GOAL_TYPE_CONTEXT_INFER:
            query = f'IOTCM "{absoluteFileName}" NonInteractive Indirect ({AGDA_CMD_GOAL_TYPE_CONTEXT_INFER} Simplified {interactionId} {intervalsToRange} "{exp}")'
        elif cmd in [AGDA_CMD_AUTO, AGDA_CMD_AUTOONE]:
            hints = exp #"" if exp == "?" else inside_exp
            query = f'IOTCM "{absoluteFileName}" NonInteractive Indirect ({cmd} {interactionId} {intervalsToRange} "{hints}")'
        elif cmd == AGDA_CMD_COMPUTE:
            query = f'IOTCM "{absoluteFileName}" NonInteractive Indirect ({AGDA_CMD_COMPUTE} DefaultCompute {interactionId} {intervalsToRange} "{exp}")'
        elif cmd == AGDA_CMD_COMPUTE_TOPLEVEL:
            query = f'IOTCM "{absoluteFileName}" None Indirect ({AGDA_CMD_COMPUTE_TOPLEVEL} DefaultCompute "{exp}")'
        elif cmd == AGDA_CMD_REFINE_OR_INTRO:
            flag = "False" # "True" if the goal has functional type
            query = f'IOTCM "{absoluteFileName}" NonInteractive Indirect ({AGDA_CMD_REFINE_OR_INTRO} {flag} {interactionId} {intervalsToRange} "{inside_exp}")'
        elif cmd == AGDA_CMD_MAKE_CASE:
            query = f'IOTCM "{absoluteFileName}" NonInteractive Indirect ({AGDA_CMD_MAKE_CASE} {interactionId} {intervalsToRange} "{inside_exp}")'
        elif cmd == AGDA_CMD_GIVE:
            query = f'IOTCM "{absoluteFileName}" NonInteractive Indirect ({AGDA_CMD_GIVE} WithoutForce {interactionId} {intervalsToRange} "{inside_exp}")'
        else:
            return f"Unrecognised command: {cmd}", True
        
        # send the type query to agda
        response = self.interact(query)

        if AGDA_INFO_ACTION in response:
            info_action_type, info_action_message = response[AGDA_INFO_ACTION][0][0], deescapify(response[AGDA_INFO_ACTION][0][1])
            info_action_types = [item[0] for item in response[AGDA_INFO_ACTION]]
        else:
            info_action_type, info_action_message = "", ""

        if AGDA_INFO_ACTION in response:

            self.print(f"there is AGDA_INFO_ACTION")

            if AGDA_GIVE_ACTION in response: # if there is a give action, it has priority

                result = response[AGDA_GIVE_ACTION]
                self.print(f"there is AGDA_GIVE_ACTION, with content {result}, and interactionId = {interactionId}")

                if cmd in [AGDA_CMD_GIVE, AGDA_CMD_REFINE_OR_INTRO] and len(result) > 0 and int(result[0]) == interactionId:
                    self.print(f"got matching hole!")

                    if cmd == AGDA_CMD_GIVE:
                        return "OK", False
                    elif cmd == AGDA_CMD_REFINE_OR_INTRO and len(result) > 1 and result[1] != "":
                        self.print(f"returning: {result[1][0]}")
                        return deescapify(result[1][0]), False
                    else:
                        return "OK", False
            elif AGDA_ALL_GOALS in info_action_types:

                self.print(f"there is AGDA_ALL_GOALS")

                goals = "".join([deescapify(item[1]) if item[0] == AGDA_ALL_GOALS else "" for item in response[AGDA_INFO_ACTION]])
                self.print(f"deescapified goals: {goals}")
                return goals, False
            elif AGDA_ALL_DONE in info_action_types:
                return "OK", False
            elif any(x in AGDA_ERROR_LIKE for x in info_action_types):
                info_action_message = "".join([f"{item[0]}: {deescapify(item[1])}" if item[0] in AGDA_ERROR_LIKE else "" for item in response[AGDA_INFO_ACTION]])

                if cmd != AGDA_CMD_LOAD:
                    # error recovery: if there is a string "did you mean 'new_exp'?",
                    # then call again with new_exp (except if we are loading)
                    matches = re.findall(r'did you mean \'([^\']*)\'\?', info_action_message)
                    if len(matches) > 0:
                        new_exp = matches[0]
                        if new_exp != exp: # avoid a potential infinite loop
                            self.print(f'trying error recovery with new expression: {new_exp}')
                            return self.runCmd(code, cursor_start, cursor_end, new_exp, cmd)

                return info_action_message, True
            elif AGDA_INFERRED_TYPE in info_action_types:
                inferred_type = info_action_message
                return f'{inferred_type}', False # if inferred_type != "" else str(response)
            elif AGDA_GOAL_TYPE_ETC in info_action_types:
                result = info_action_message
                blocks = result.split('————————————————————————————————————————————————————————————')
                result = blocks[0] + blocks[1]

                # find the maximal line length
                lines = result.split('\n')
                max_len = max(list(map(len, lines)))

                result = blocks[0] + ("-" * max_len) + blocks[1]
                self.print(f'AGDA_GOAL_TYPE_ETC case, max_len: {max_len}, result: {result}')

                return result, False
            elif AGDA_AUTO in info_action_types:
                return info_action_message, False
            elif AGDA_NORMAL_FORM in info_action_types:
                return info_action_message, False
            else:
                return info_action_message, True

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

    def get_expression(self, code, cursor_pos):

        if len(code) < len(self.code):
            # we are in a selection and the cursor is at the beginning of the selection
            if  cursor_pos + len(code) <= len(self.code) and self.code[cursor_pos:cursor_pos+len(code)] == code:
                #self.print(f'we are in a selected text, cursor at the beginning')
                cursor_start, cursor_end, exp = cursor_pos, cursor_pos + len(code), code
            # we are in a selection and the cursor is at the end of the selection
            elif cursor_pos - len(code) >= 0 and cursor_pos <= len(self.code) and self.code[cursor_pos-len(code):cursor_pos] == code:
                #self.print(f'we are in a selected text, cursor at the end')
                cursor_start, cursor_end, exp = cursor_pos - len(code), cursor_pos, code
            else:
                error = True
                self.print(f'no other case possible: the cursor is either at the beginning or at the end of a selection')
                #return {'status': 'ok', 'found': True, 'data': {'text/plain': 'load the cell first'}, 'metadata': {}}
        # we are not in a selection, or an error above occurred
        else: # if exp == "":
            cursor_start, cursor_end, exp = self.find_expression(code, cursor_pos)
            #cursor_start += 1
        
        return cursor_start, cursor_end, exp

    def infer_top_level(self, cursor_start, cursor_end, exp):

        inferred_type, error2 = self.runCmd(self.code, cursor_start, cursor_end, exp, AGDA_CMD_INFER_TOPLEVEL)
        normal_form, error3 = self.runCmd(self.code, cursor_start, cursor_end, exp, AGDA_CMD_COMPUTE_TOPLEVEL)

        error = error2 and error3

        if not error:
            result = f"{exp.strip()} EVALUATES TO \n{normal_form.strip()} OF TYPE\n {inferred_type.strip()}"
        elif not error2:
            result = f"{exp.strip()} : {inferred_type.strip()}"
        elif not error3:
            result = f"{exp.strip()} = {normal_form.strip()}"
        else: # this is an error message
            result = normal_form.strip()

        return error, f"{result}"

    def infer_local(self, cursor_start, cursor_end, exp):

        goal, error1 = self.runCmd(self.code, cursor_start, cursor_end, exp, AGDA_CMD_GOAL_TYPE_CONTEXT_INFER)
        inferred_type, error2 = self.runCmd(self.code, cursor_start, cursor_end, exp, AGDA_CMD_INFER)
        normal_form, error3 = self.runCmd(self.code, cursor_start, cursor_end, exp, AGDA_CMD_COMPUTE)

        result = ""

        #self.print(f'gathered: error1 = {error1}, error2 = {error2}, error3 = {error3}')

        if not error2 and not error3:
            normalisation = f"Eval: {exp.strip()} --> {normal_form.strip()} : {inferred_type.strip()}"
        elif not error2:
            normalisation = f"{exp.strip()} : {inferred_type.strip()}"
        elif not error3:
            normalisation = f"Eval: {exp.strip()} --> {normal_form.strip()}"
        else:
            normalisation = ""

        padding = "=" * len(normalisation)

        if not error1 and goal and goal != "":
            result = f"{goal.strip()} \n{padding}\n"
        else:
            return True, f"{normal_form.strip()}" # this contains the error message

        return False, result

    # get the type of the current expression
    # triggered by SHIFT+TAB
    # code is either the current selection, or the whole cell otherwise
    # cursor_pos is always at the beginning or at the end of the selection;
    def do_inspect(self, code, cursor_pos, detail_level=0):

        #if self.code == "" or not code in self.code:
        #    return {'status': 'error', 'found': True, 'data': {'text/plain': "must load the cell first"}}

        self.print(f'do_inspect cursor_pos: {cursor_pos}, selection: "{code}" of length {len(code)}, code: "{self.code}" of length {len(self.code)}')

        # load the code to check that there are no errors
        #response = self.do_execute(self.code, False)
        response = self.do_execute(code, False)

        if response['status'] == 'error':
            return {'status': 'error', 'found': False, 'data': {'text/plain': "unable to inspect, the code contain errors"}}

        cursor_start, cursor_end, exp = self.get_expression(code, cursor_pos)            
        # self.print(f'current exp: "{exp}", pos: {cursor_pos}, start: {cursor_start}, end: {cursor_end}')

        old_code = self.code

        # if we are not in a hole, try the top level inspection first
        if not self.isHole(exp):
            error, result = self.infer_top_level(cursor_start, cursor_end, exp)
            if not error:
                return {'status': 'ok', 'found': True, 'data': {'text/plain': result}}
            else:
                # if we are not in a hole,
                # create an artificial hole around the current selection and reload
                self.code = self.code[:cursor_start-1] + "{! " + exp + " !}" + self.code[cursor_end:]
                #self.print(f'new_code: {self.code}')
                response = self.do_execute(self.code, False)

                # adding the hole creates an error
                if response['status'] == 'error':
                    self.print(f'unexpected error when adding temporary hole: {response}')

                cursor_start, cursor_end, exp = self.find_expression(self.code, cursor_start)

        # at this point we are in a hole,
        # either the original one, or the one we created
        if exp != "?":
            exp = exp[2:-2] # strip the initial "{!" and final "!}"
            #self.print(f'considering inside exp: {exp}')

        #self.print(f'considering exp: {exp}, pos: {cursor_pos}, start: {cursor_start}, end: {cursor_end}')
        error, result = self.infer_local(cursor_start, cursor_end, exp)

        # undo file modifications if we created a new hole
        if self.code != old_code:
            self.code = old_code
            self.do_execute(self.code, False)

        return {'status': 'error' if error else 'ok', 'found': True, 'data': {'text/plain': result}}

    # handle unicode completion here
    def do_complete(self, code, cursor_pos):

        #self.print(f'considering code: {code}, pos: {cursor_pos}')

        half_subst = {
            'Nat' : 'ℕ',
            '<=<>' : '≤⟨⟩',
            '<==<>' : '≤≡⟨⟩',
            '=<>' : '≡⟨⟩',
            '-><>' : '↝<>',
            '->*<>' : '↝*<>',
            'top' : '⊤',
            'bot' : '⊥',
            'neg' : '¬',
            '/\\' : '∧',
            '\\/' : '∨',
            '\\' : 'λ', # it is important that this comes after /\
            'Pi' : 'Π',
            'Sigma' : 'Σ',
            '->' : '→',
            '→' :  '↦',
            '↦' : '↝',
            '↝' : '->',
            'iff' : '⟺',
            '<=>' : '⟺',
            '=>' : '⇒',
            '<' : '⟨',
            '>' : '⟩', # it is important that this comes after ->
            '⟩' : '≻',
            '≻' : '>',
            'forall' : '∀',
            'exists' : '∃',
            'A' : '𝔸',
            'B' : '𝔹',
            'C' : 'ℂ',
            'N' : 'ℕ',
            'Q' : 'ℚ',
            'R' : 'ℝ',
            'Z' : 'ℤ',
            ':=' : '≔',
            '/=' : '≢',
            'leq' : '≤',
            '<=' : '≤',
            'geq' : '≥',
            '>=' : '≥',
            '[=' : '⊑',
            '=' : '≡',
            'alpha' : 'α',
            'beta' : 'β',
            'gamma' : 'γ',
            'rho' : 'ρ',
            'e' : 'ε',
            'mu' : 'μ',
            'kappa': 'κ',
            'xor' : '⊗',
            'emptyset' : '∅',
            'qed' : '∎',
            '.' : '·',
            'd' : '∇',
            'Delta' : 'Δ',
            'delta' : 'δ',
            'notin' : '∉',
            'in' : '∈',
            '[' : '⟦',
            ']' : '⟧',
            '::' : '∷',
            '0' : '𝟬', # '𝟢',
            '𝟬' : '₀',
            '₀' : '0',
            '1' : '𝟭', # '𝟣'
            '𝟭' : '₁',
            '₁' : '1',
            '2' : '₂',
            '3' : '₃',
            '4' : '₄',
            '5' : '₅',
            '6' : '₆',
            '7' : '₇',
            '8' : '₈',
            '9' : '₉',
            '+' : '⨁',
            '~' : '≈',
            'x' : '×',
            'o' : '∘',
            'phi' : 'φ',
            'psi' : 'ψ',
            'xi' : 'ξ',
            #'??' : "{! !}",
            'w'  : 'ω ',
            'omega' : 'ω',
            'Gamma' : 'Γ',
            'tau' : 'τ',
            'sigma' : 'σ',
            #';' : ';', very bad idea: the second semicolon lloks the same but it is a different unicode symbol...
            ';' : '⨟',
            '(' : '⟬',
            '⟬' : '｟',
            ')' : '⟭',
            '⟭' : '｠',
            'b' : 'ᵇ',
            'empty' : '∅',
            '|-' : '⊢',
            'models' : '⊨',
            '|=' : '⊨',
            'cup' : '⊔',
            'l' : 'ℓ',
            'op' : 'ᵒᵖ',
            '{{' : '⦃',
            '}}' : '⦄',
            '--' : '−−', # they are not the same!
            '−−' : '--', # they are the other way around!
            ':' : '꞉', # they are not the same!
            '꞉' : ':', # they are the other way around!
            'subseteq' : '⊆',
            '⊆' : 'subseteq'
        }

        other_half = {val : key for (key, val) in half_subst.items() if val not in list(half_subst.keys())}
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

        def cmdAuto():

            # call Agsy, options: -c (case splitting) -m (hints) -r (refine) -l (list) -s k (select result k)
            """options = lambda k: f'  -m -s {k}  '
            k = 0
            while True:
                result, error = self.runCmd(code, cursor_start, cursor_end, options(k), AGDA_CMD_AUTOONE)
                self.print(f'result is: {result}, error is: {error}')
                if error or result in ["No solution found", "No candidate found", "Only 1 solution found", f'Only {k} solutions found']:
                    if matches == []:
                        matches = ["{! !}"] # transform "?" into "{! !}" when Agsy fails

                    break
                else:
                    matches += [result] if result != "" else []

                k += 1
            """
            options = "-m -l" # list solutions
            self.print(f'Agsy options are: {options}')
            result, error = self.runCmd(code, cursor_start, cursor_end, options, AGDA_CMD_AUTOONE if self.agda_version >= "2.5.4" else AGDA_CMD_AUTO)
            self.print(f'result is: {result}, error is: {error}')

            if result.find("Listing solution(s)") != -1:
                matches = self.listing_solution_parser(result)

            elif error or result in ["No solution found", "No candidate found", "No solution found after timeout (1000ms)"]:
                matches = ["{! !}"] # transform "?" into "{! !}" when Agsy fails
            else:
                self.print(f'Unexpected answer: {result}, error is: {error}')

            return result, error, matches

        # didn't apply a textual substitution,
        # or such substitutions are disabled
        if not self.unicodeComplete or matches == []:

            # reset the list of matches in any case
            matches = []

            cursor_start_orig, cursor_end_orig, exp_orig = self.find_expression(code, cursor_pos)
            cursor_start, cursor_end = cursor_start_orig, cursor_end_orig
            exp = escapify(exp_orig)
            #cursor_start += 1

            agdaCMD = self.agdaCMD

            # if we have a specific command to pass to Agda, just do it
            if agdaCMD != "":

                self.print(f'Passing command directly to Agda: {agdaCMD}')

                if agdaCMD == AGDA_CMD_AUTO or agdaCMD == AGDA_CMD_AUTOONE:
                    result, error, matches = cmdAuto()
                else:
                    result, error = self.runCmd(code, cursor_start, cursor_end, exp, agdaCMD)

                    self.print(f'result is: {result}, error is: {error}')

                    if error:
                        cursor_start, cursor_end = cursor_pos, cursor_pos
                    elif agdaCMD == AGDA_CMD_GIVE and result == "OK":
                        result = "(" + re.search(r'\{! *(.*) *!\}', exp).group(1).strip() + ")"
                        self.print(f'gave hole: {result}')
                    elif agdaCMD == AGDA_CMD_MAKE_CASE:
                        # need to replace the current row with result
                        while cursor_start > 0 and code[cursor_start - 1] != "\n":
                            cursor_start -= 1
                        while cursor_end < length and code[cursor_end] != "\n":
                            cursor_end += 1
                    # elif agdaCMD == AGDA_CMD_REFINE_OR_INTRO:
                        
                    # else:
                    #     cursor_start, cursor_end = cursor_pos, cursor_pos
                    #     result = ""

                    matches = [result] if result != "" else []

            else:

                # load the current contents
                self.do_execute(code, False)

                if exp == "?":
                    result, error, matches = cmdAuto()

                # continue the chain if Agsy fails
                if self.isHole(exp) and (exp != "?" or matches == ["{! !}"]):

                    # first, try to replace the hole with its current contents
                    result, error = self.runCmd(code, cursor_start, cursor_end, exp, AGDA_CMD_GIVE)

                    self.print(f'AGDA_CMD_GIVE, result: {result}, error: {error}')

                    if error:
                        # second, try to automatically refine the current contents
                        result, error = self.runCmd(code, cursor_start, cursor_end, exp, AGDA_CMD_REFINE_OR_INTRO)

                        if error: # try case
                            # need to reload to make it work (??)
                            _, _ = self.runCmd(code, -1, -1, "", AGDA_CMD_LOAD)

                            # third, try to introduce a case analysis
                            result, error = self.runCmd(code, cursor_start, cursor_end, exp, AGDA_CMD_MAKE_CASE)

                            if error or result == "OK":
                                cursor_start, cursor_end = cursor_pos, cursor_pos
                                result = ""
                            else:
                                # need to replace the current row with result
                                while cursor_start > 0 and code[cursor_start - 1] != "\n":
                                    cursor_start -= 1
                                while cursor_end < length and code[cursor_end] != "\n":
                                    cursor_end += 1

                        elif result == "OK":
                            # cannot close the hole
                            result1 = re.search(r'\{! *(.*) *!\}', exp).group(1).strip()
                            self.print(f'not closing hole: {result1}')
                        else:
                            # in this case result is a refined goal and we can refine the hole
                            result = result
                    elif result == "OK":
                        # close the hole
                        result = "(" + re.search(r'\{! *(.*) *!\}', exp).group(1).strip() + ")"
                        self.print(f'gave hole: {result}')

                    matches = [result] if result != "" else []

                self.print(f'exp: {exp}, matches: {matches}')

                # always replace "?" with a hole in case there is no match
                if exp == "?" and matches == []:
                    matches = ["{! !}"]
                    cursor_start, cursor_end = cursor_start_orig, cursor_end_orig
                    self.print(f'cursor_start: {cursor_start}, cursor_end: {cursor_end}')
                    error = False
    
        return {'matches': matches, 'cursor_start': cursor_start,
                'cursor_end': cursor_end, 'metadata': {},
                'status': 'ok' if not error else 'error'}

    def listing_solution_parser(self, str):
        # example: Listing solution(s) 0-9\n0  cong suc (+-assoc m n p)\n1  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m p p)) ⟩\nsuc (m + (n + p)) ∎\n2  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m p n)) ⟩\nsuc (m + (n + p)) ∎\n3  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m p m)) ⟩\nsuc (m + (n + p)) ∎\n4  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m n p)) ⟩\nsuc (m + (n + p)) ∎\n5  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m n n)) ⟩\nsuc (m + (n + p)) ∎\n6  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m n m)) ⟩\nsuc (m + (n + p)) ∎\n7  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m m p)) ⟩\nsuc (m + (n + p)) ∎\n8  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m m n)) ⟩\nsuc (m + (n + p)) ∎\n9  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m m m)) ⟩\nsuc (m + (n + p)) ∎\n
        solutions = re.split('\n[0-9]+ +', str)[1:] # skip the first line

        # need to insert two extra spaces for multiline solutions in order to preserve indentation
        solutions = [ '\n  '.join(re.split('\n', solution)) for solution in solutions]

        # strip trailing newlines and spaces
        solutions = [ solution.rstrip() for solution in solutions]
        
        self.print(f"solutions is: {solutions}")
        #    solution = " ".join(tokens[2:]) # skip the first "20  " (plus the extra space!) and put the tokens back
        return solutions

    def findAllHoles(self, code):
        i = 0
        length = len(code)
        holes = []

        while i < length:
            if code[i:i+2] == "--": # we are in a line comment
                while i < length and code[i] != "\n":
                    i += 1 # skip to the end of the line
            elif code[i:i+2] == "{-": # we are in a block comment
                i += 2
                k = 1
                while i < length and k > 0:
                    if code[i:i+2] == "{-":
                        k += 1
                        i += 2
                    elif code[i:i+2] == "-}":
                        k -= 1
                        i += 2
                    else:
                        i += 1
            elif code[i:i+1] == "?" and i+1 == length:
                holes.append((i, i+1))
                i += 1
            elif code[i:i+2] in ["(?"]:
                holes.append((i+1, i+2))
                i += 2
            elif code[i:i+2] in ["?)", "?;"]:
                holes.append((i, i+1))
                i += 1
            elif code[i:i+3] in [" ?\n", " ? ", "(?)"] or (code[i:i+2] == " ?" and i+2 == length):
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