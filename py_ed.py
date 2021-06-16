""" Needed to get argument passed """
import sys
""" Needed to get shell command works """
import os

""" Global variables """
G_LOOSE_EXIT_STATUS = False # Do not exit with bad status if a command happens to "fail" (default: False)
G_VERSION = '0.1'           # version number
G_PROMPTING_BOOL = False    # Turn prompting on
G_PROMPTING_STRING = '*'    # Command prompt string
G_DEFAULT_FILE = 'temp'     # Default file to open
G_RESTRICTED = False        # Disable editing files out of the current directory and execution of shell commands
G_SILENT = False            # Disable the printing of bytes count by 'e', 'E', 'r' and 'w' commands and '!' prompt after a '!' command.
G_VERBOSE = False           # Display error explanations
G_MARKED_LINE = {}          # Dictionnary which contains marked line

""" Global runtime variables """
G_COMMAND = ''             # current command
G_COMMAND_LAST = ''        # last command
G_FILE = ''                # file currently edited
G_BUFFER_READ = ['']       # read-only buffer
G_BUFFER_WROTE = ['']      # modified buffer
G_BUFFER_WROTE_LAST = [''] # modified buffer before the last edition command
G_RANGE = [1, 1]           # range selected
G_EXIT_STATUS = 0          # exit status
G_RUNNING = True           # py_ed is running
G_LAST_ERROR = ''          # last error
G_LINE_ADRESSING = False   # if there was a line adressing in this command

""" Global registers """
G_REGISTER_CUT = ''    # register for cut operation
G_REGISTER_DELETE = '' # register for delete operation

def display_error(message, verbose=False):
    global G_LAST_ERROR
    """ Display error """
    if G_SILENT and not verbose:
        pass
    elif G_VERBOSE or verbose:
        print(message)
    else:
        print('?')
    G_LAST_ERROR = message
    raise Exception(message)

def open_file(path):
    """ Open a file """
    global G_BUFFER_WROTE
    global G_BUFFER_READ
    global G_FILE
    global G_RANGE

    if G_RESTRICTED:
        if len(path) >= 1:
            if path[:1] == '/':
                display_error('restricted')
                return 2
            if path[:1] == '!':
                display_error('restricted')
                return 2
        if len(path) >= 3:
            if path[:3] == '../' or path[:3] == '..\\':
                display_error('restricted')
                return 2
            if path[1:3] == ':\\\\':
                display_error('restricted')
                return 2
    if len(path) >= 1:
        if path[:1] == '!':
            """ Result of the shell command """
            cmd = os.popen(path[1:])
            G_BUFFER_READ = cmd.read().split('\n')
            G_BUFFER_WROTE = cmd.read().split('\n')
            G_FILE = G_DEFAULT_FILE
            G_RANGE = [len(G_BUFFER_WROTE), len(G_BUFFER_WROTE)]
            return 0
    with open(path, 'r') as file:
        for i, l in enumerate(file):
            G_BUFFER_READ.append(l)
            G_BUFFER_WROTE.append(l)
        if not G_SILENT:
            print(file.tell())
        G_FILE = path
        G_RANGE = [len(G_BUFFER_WROTE), len(G_BUFFER_WROTE)]
        return 0

def file_changed():
    """ Check if the user edited the current file """
    return G_BUFFER_READ != G_BUFFER_WROTE


def get_first_adress(string):
    """ return first adress recognised (error if the start of the string is not related to an adress) """
    if string[0] == ' ':
        if len(string) > 1:
            adress_number, adress_index = get_first_adress(string[1:])
            return adress_number, adress_index + 1
        else:
            return 0, 0
    elif string[0] == '.':
        return G_RANGE[1]
    elif string[0] == '$':
        return len(G_BUFFER_WROTE)
    else:
        """ can be a combination (like 23 or ++++) """
        if string[0] == '\'':
            if len(string) > 1:
                if string[1] in G_MARKED_LINE:
                    number = G_MARKED_LINE[string[1]]
                    index_char = 2
                    if len(string) > 2:
                        if string[2] in (' ', '-', '+'):
                            offset_number, offset_index = get_offset(string[2:])
                            number += offset_number
                            index_char += offset_index
                else:
                    display_error('not_marked')
            else:
                display_error('missing_mark_key')
        elif string[0] == '+':
            """ start with + """
            number = G_RANGE[1]
            if len(string) > 1:
                if string[1] == '+':
                    for index_char in range(len(string)):
                        if string[index_char] == '+':
                            number += 1
                        else:
                            if string[index_char] in (' ', '-', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'):
                                """ offset """
                                if string[index_char].isnumeric():
                                    number -= 1

                                offset_number, offset_index = get_offset(string[index_char:])
                                number += offset_number
                                index_char += offset_index
                                break
                            else:
                                """ unexpected symbol """
                                return number, index_char
                elif string[1].isnumeric():
                    """ add a number of line to current line number """
                    offset = False
                    for index_char in range(1, len(string)):
                        if string[index_char].isnumeric():
                            pass
                        if string[index_char] in (' ', '+', '-'):
                            """ manage offset """
                            offset = True
                            number += int(string[1:index_char])
                            offset_number, offset_index = get_offset(string[index_char:])
                            number += offset_number
                            index_char += offset_index
                            break
                        else:
                            """ unexpected symbol """
                            return number + int(string[1:index_char+1]), index_char+1
                    if not offset:
                        """ no offset """
                        number += int(string[1:])
                else:
                    """ strange case where someone want to go one line after the current one minus an offset """
                    number += 1
                    if string[1] in (' ', '-'):
                        """ manage offset """
                        offset_number, offset_index = get_offset(string[2:])
                        return number - offset_number, 2 + offset_index
                    else:
                        """ unexpected symbol """
                        return number, 2
            else:
                return number+1, 2
        elif string[0] == '-':
            """ begin with - """
            number = G_RANGE[1]
            if len(string) > 1:
                if string[1] == '-':
                    for index_char in range(len(string)):
                        if string[index_char] == '-':
                            number -= 1
                        else:
                            if string[index_char] in (' ', '+', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'):
                                """ manage offset """
                                offset_number, offset_index = get_offset(string[index_char:])
                                number += offset_number
                                index_char += offset_index
                                break
                            else:
                                """ unexpected symbol """
                                return number, index_char
                elif string[1].isnumeric():
                    offset = False
                    for index_char in range(1, len(string)):
                        if string[index_char].isnumeric():
                            pass
                        elif string[index_char] in ('+', '-', ' '):
                            offset = True
                            number -= int(string[1:index_char])
                            offset_number, offset_index = get_offset(string[index_char:])
                            number += offset_number
                            index_char += offset_index
                            break
                        else:
                            """ unexpected symbol """
                            return number - int(string[1:index_char+1]), index_char+1
                    if not offset:
                        """ no offset """
                        number -= int(string[1:])
                else:
                    """ strange case where someone want to go one line below the current one plus an offset """
                    number -= 1
                    if string[1] in (' ', '+'):
                        """ manage offset """
                        offset_number, offset_index = get_offset(string[1:])
                        return number + offset_number, 2 + offset_index
                    else:
                        """ unexpected symbol """
                        return number, 2
            else:
                return number-1, 2
        else:
            """ a simple number """
            if not string[0].isnumeric():
                return 0, 0
            number = 0
            offset = False
            for index_char in range(len(string)):
                if string[index_char].isnumeric():
                    pass
                elif string[index_char] in (' ', '+', '-'):
                    offset = True
                    number += int(string[:index_char])
                    offset_number, offset_index = get_offset(string[index_char:])
                    number += offset_number
                    index_char += offset_index
                    break
                else:
                    """ unexpected symbol """
                    return number + int(string[:index_char]), index_char
            if not offset:
                """ no offset """
                number += int(string)
        return number, index_char

def get_offset(string):
    """ return all first linked offset in a string """
    if string[0] == ' ':
        if len(string) > 1:
            offset_number, offset_index = get_offset(string[1:])
            return offset_number, 1 + offset_index
        else:
            return 0, 1
    if string[0] == '+':
        """ begin with + """
        if len(string) > 1:
            if string[1] in (' ', '+', '-'):
                offset_number, offset_index = get_offset(string[1:])
                return 1 + offset_number, 1 + offset_index
            elif string[1].isnumeric():
                offset_number, offset_index = get_offset(string[1:])
                return offset_number, 1 + offset_index
            else:
                """ unexpected symbol """
                return 1, 1
        else:
            return 1, 1
    elif string[0] == '-':
        """ begin with - """
        if len(string) > 1:
            if string[1] in (' ', '+', '-'):
                offset_number, offset_index = get_offset(string[1:])
                return offset_number - 1, offset_index + 1
            if string[1].isnumeric():
                """ cannot do number = -number_offset because of the mathematical order """
                for index_char in range(2, len(string)):
                    if string[index_char] in (' ', '+', '-'):
                        offset_1_number, offset_1_index = get_offset(string[1:index_char])
                        offset_2_number, offset_2_index = get_offset(string[index_char:])
                        return -offset_1_number + offset_2_number, offset_1_index + offset_2_index + 1
                    offset_1_number, offset_1_index = get_offset(string[1:index_char])
                    return -offset_1_number, offset_1_index + 1
            else:
                """ unexpected symbol """
                return -1, 1
        else:
            return -1, 1
    elif string[0].isnumeric():
        """ simple number """
        for index_char in range(len(string)):
            if string[index_char].isnumeric():
                pass
            elif string[index_char] in (' ', '+', '-'):
                number = int(string[:index_char])
                offset_number, offset_index = get_offset(string[index_char:])
                return number + offset_number, index_char + offset_index
            else:
                """ unexpected symbol """
                return int(string[:index_char]), index_char
        return int(string), index_char + 1
    else:
        """ unexpected symbol """
        return 0, 0

def get_text():
    """ Get text (input mode) """
    text_line, text = '', []
    while text_line != '.':
        text_line = input()
        text.append(text_line + '\n')
    return text[:-1]

""" Commands argument interpretation process """
index = 1
while index < len(sys.argv):
    try:
        if sys.argv[index][0] == '-':
            if sys.argv[index] == '-h' or sys.argv[index] == '--help':
                print("""py_ed: py_ed [-h|--help]|[-V|--version]|[[-E|--extended-regexp][-G|--traditional][-l|--loose-exit-status][-p [string]|--prompt=[string]][-r|--restricted][-s|--quiet|--silent][-v|--verbose]] [file]
        Run the py_ed editor in this shell.

        py_ed is a remake of ed on python.

        Options :
          -h
          --help
                     print this help and exit
          -V
          --version
                     print the version number of py_ed and python and exit. This version number should be included in all bug reports
          -E
          --extended-regexp
                     use extended regular expression instead of the basic regular expression mandated by POSIX (not implemented yet)
          -G
          --traditional
                     force  backward compatibility (affect some commands which had behavior changes) (not implemented yet)
          -l
          --loose-exit-status
                     exit everytime with the exit status 0
          -p [string]
          --prompt=[string]
                     allows to specifies the command prompt string, and turns prompting on
          -r
          --restricted
                     run in restricted mode, which makes py_ed unable to edit file outside the current directory and unable to execute shell command
          -s
          --quiet --silent
                     py_ed will not display diagnostics, byte counts and '!' prompt
          -v
          --verbose
                     py_ed will give more detailed error""")
                sys.exit(0);
            elif sys.argv[index] == '-V' or sys.argv[index] == '--version':
                print('py_ed: ' + str(G_VERSION) + '\npython: ' + str(sys.version))
                sys.exit(0)
            elif sys.argv[index] == '-l' or sys.argv[index] == '--loose-exit-status':
                G_LOOSE_EXIT_STATUS = True
            elif sys.argv[index] == '-p' or sys.argv[index][:9] == '--prompt=':
                if sys.argv[index] == '-p':
                    index += 1
                    if len(sys.argv) > index:
                        G_PROMPTING_STRING = sys.argv[index]
                    else:
                        display_error('unexpected_argument_shell')
                else:
                    G_PROMPTING_STRING = sys.argv[index][9:]
                G_PROMPTING_BOOL = True
            elif sys.argv[index] == '-r' or sys.argv[index] == '--restricted':
                G_RESTRICTED = True
            elif sys.argv[index] == '-s' or sys.argv[index] == '--quiet' or sys.argv[index] == '--silent':
                G_SILENT = True
            elif sys.argv[index] == '-v' or sys.argv[index] == '--verbose':
                G_VERBOSE = True
            else:
                display_error('unexpected_argument_shell')
        else:
            if index == len(sys.argv)-1:
                G_EXIT_STATUS = open_file(sys.argv[index])
            else:
                display_error('unexpected_argument_shell')
        index += 1
    except Exception as error:
        sys.exit(1)

while G_RUNNING:
    """ main loop """
    try:
        if G_PROMPTING_BOOL:
            G_COMMAND = input(G_PROMPTING_STRING)
        else:
            G_COMMAND = input()
        command = G_COMMAND.split()

        if command[0] == 'e':
            """ edit a file (if current saved) """
            if len(command) > 2:
                display_error('too many arguments')
            elif len(command) == 2:
                if not file_changed():
                    G_EXIT_STATUS = open_file(command[1])
                else:
                    display_error('unsaved_change')
            else:
                display_error('missing_argument')
        elif command[0] == 'E':
            """ edit a file """
            if len(command) > 2:
                display_error('too many arguments')
            elif len(command) == 2:
                G_EXIT_STATUS = open_file(command[1])
            else:
                display_error('missing_argument')
        elif command[0] == 'f':
            """ change or show default file """
            if len(command) > 2:
                display_error('too many arguments')
            elif len(command) == 2:
                G_DEFAULT_FILE = command[1]
            else:
                print(G_DEFAULT_FILE)
        elif command[0] == 'q':
            """ exit (if changes saved) """
            if len(command) > 1:
                display_error('too many arguments')
            elif not file_changed():
                G_RUNNING = False
            else:
                display_error('unsaved_change')
        elif command[0] == 'Q':
            """ exit """
            if len(command) > 1:
                display_error('too many arguments')
            else:
                G_RUNNING = False
        elif command[0] == 'P':
            """ toggle prompting """
            if len(command) > 1:
                display_error('too many arguments')
            else:
                G_PROMPTING_BOOL = not G_PROMPTING_BOOL
        elif command[0] == 'h':
            """ show last error """
            if len(command) > 1:
                display_error('too many arguments')
            else:
                display_error(G_LAST_ERROR, True)
        elif command[0] == 'H':
            """ toggle verbose """
            if len(command) > 1:
                display_error('too many arguments')
            else:
                G_VERBOSE = not G_VERBOSE
        elif command[0] == 'u':
            """ cancel last change """
            if len(command) > 1:
                display_error('too many arguments')
            else:
                G_BUFFER_WROTE, G_BUFFER_WROTE_LAST = G_BUFFER_WROTE_LAST, G_BUFFER_WROTE
        elif G_COMMAND[0] == '!':
            """ invoke console """
            if not G_RESTRICTED:
                if len(G_COMMAND) > 1:
                    commands = G_COMMAND[1:]
                    os.system(commands)
                    if not G_SILENT:
                        print('!')
                else:
                    display_error('missing_argument')
            else:
                display_error('restricted')
        elif command[0][0] in ('\'', ',', ';', '$', '+', '-', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
            """ there is line adressing """
            G_LINE_ADRESSING = True
            index = 1
            if G_COMMAND[0][0] == ';':
                G_RANGE = [G_RANGE[1], len(G_BUFFER_WROTE)]
            elif G_COMMAND[0][0] == ',':
                G_RANGE = [0, len(G_BUFFER_WROTE)]
            elif G_COMMAND[0][0] == '.':
                G_RANGE = [G_RANGE[1], G_RANGE[1]]
            else:
                first_number, first_index = get_first_adress(G_COMMAND)
                if first_number > len(G_BUFFER_WROTE) or first_number < 0:
                    display_error('invalid_adress')
                index = first_index
                if len(G_COMMAND) > first_index:
                    if G_COMMAND[first_index] != ',':
                        G_RANGE = [first_number, first_number]
                    else:
                        second_number, second_index = get_first_adress(G_COMMAND[first_index+1:])
                        if second_number > len(G_BUFFER_WROTE) or second_number < 0:
                            display_error('invalid_adress')
                        if (second_number, second_index) == (0, 0):
                            second_number = first_number
                            second_index = first_index
                        if second_number < first_number:
                            display_error('invalid_adress')
                        else:
                            G_RANGE = [first_number, second_number]
                        index = first_index + 1 + second_index
                else:
                    G_RANGE = [first_number, first_number]
            command = G_COMMAND[index:].split()
        else:
            display_error('unknown_command')
        if command[0] == 'a':
            """ append to line """
            G_RANGE[0] = G_RANGE[1]
            text = get_text()
            if len(text) > 0:
                G_BUFFER_WROTE_LAST = G_BUFFER_WROTE
                if not G_LINE_ADRESSING:
                    """ . """
                    pass
                if G_RANGE == [0, 0]:
                    G_BUFFER_WROTE = text + G_BUFFER_WROTE
                    G_RANGE = [1, 1]
                else:
                    """ adding text to the adressed line """
                    G_BUFFER_WROTE[G_RANGE[1]] = G_BUFFER_WROTE[G_RANGE[1]][:-1] + text[0]
                    if len(text) > 1:
                        """ Adding lines """
                        G_BUFFER_WROTE = G_BUFFER_WROTE[:G_RANGE[1]+1] + text[1:] + G_BUFFER_WROTE[G_RANGE[1]+1:]
                        G_RANGE = [G_RANGE[1] + len(text) - 1, G_RANGE[1] + len(text) - 1]
        elif command[0] == 'i':
            """ insert text before """
            G_RANGE[0] = G_RANGE[1]
            text = get_text()
            if len(text) > 0:
                G_BUFFER_WROTE_LAST = G_BUFFER_WROTE
                if not G_LINE_ADRESSING:
                    """ . """
                    pass
                if G_RANGE == [0, 0]:
                    G_BUFFER_WROTE = text + G_BUFFER_WROTE
                    G_RANGE = [1, 1]
                else:
                    """ adding text before the adressed line """
                    G_BUFFER_WROTE = G_BUFFER_WROTE[:G_RANGE[1]] + text + G_BUFFER_WROTE[G_RANGE[1]:]
                    G_RANGE = [G_RANGE[1] + len(text), G_RANGE[1] + len(text)]
        elif command[0] == 'l':
            """ print lines unambiguously """
            if not G_LINE_ADRESSING:
                """ .,. """
                G_RANGE[0] = G_RANGE[1]
            for lines in G_BUFFER_WROTE[G_RANGE[0]:G_RANGE[1]+1]:
                print(lines[:-1].replace('$', '\$') + '$')
            G_RANGE[1] = G_RANGE[0]
        elif command[0] == 'p':
            """ print lines """
            if not G_LINE_ADRESSING:
                """ .,. """
                G_RANGE[0] = G_RANGE[1]
            for lines in G_BUFFER_WROTE[G_RANGE[0]:G_RANGE[1]+1]:
                print(lines, end='')
            G_RANGE[1] = G_RANGE[0]
        elif command[0] == 'c':
            """ change lines """
            text = get_text()
            G_BUFFER_WROTE_LAST = G_BUFFER_WROTE
            G_REGISTER_CUT = G_BUFFER_WROTE[G_RANGE[0]:G_RANGE[1]+1]
            if len(text) > 0:
                if not G_LINE_ADRESSING:
                    """ .,. """
                    G_RANGE[0] = G_RANGE[1]
                G_BUFFER_WROTE = G_BUFFER_WROTE[:G_RANGE[0]] + text + G_BUFFER_WROTE[G_RANGE[1] + 1:]
                if len(G_BUFFER_WROTE) > G_RANGE[0] + len(text) - 1:
                    G_RANGE = [G_RANGE[0] + len(text) - 1, G_RANGE[0] + len(text) - 1]
                else:
                    G_RANGE = [len(G_BUFFER_WROTE), len(G_BUFFER_WROTE)]
            else:
                G_BUFFER_WROTE = G_BUFFER_WROTE[:G_RANGE[0]] + G_BUFFER_WROTE[G_RANGE[1] + 1:]
                if len(G_BUFFER_WROTE) >= G_RANGE[0]:
                    G_RANGE[1] = G_RANGE[0]
                else:
                    G_RANGE = [G_RANGE[0] - 1, G_RANGE[0] - 1]
        elif command[0] == 'd':
            """ delete lines """
            G_BUFFER_WROTE_LAST = G_BUFFER_WROTE
            if not G_LINE_ADRESSING:
                """ .,. """
                G_RANGE[0] = G_RANGE[1]
            G_REGISTER_DELETE = G_BUFFER_WROTE[G_RANGE[0]:G_RANGE[1]+1]
            G_BUFFER_WROTE = G_BUFFER_WROTE[:G_RANGE[0]] + G_BUFFER_WROTE[G_RANGE[1]+1:]
            if len(G_BUFFER_WROTE) >= G_RANGE[0]:
                G_RANGE[1] = G_RANGE[0]
            else:
                G_RANGE = [G_RANGE[0] - 1, G_RANGE[0] - 1]
        elif command[0] == "j":
            """ join lines """
            if not G_LINE_ADRESSING:
                """ .,.+1 """
                G_RANGE = [G_RANGE[1], G_RANGE[1]+1]
            if G_RANGE[0] != G_RANGE[1]:
                G_BUFFER_WROTE_LAST = G_BUFFER_WROTE
                G_BUFFER_WROTE = G_BUFFER_WROTE[:G_RANGE[0]] + [''.join(G_BUFFER_WROTE[G_RANGE[0]:G_RANGE[1]]).replace('\n', '')] + G_BUFFER_WROTE[G_RANGE[1]:]
                G_RANGE[1] = G_RANGE[0]
        elif command[0][0] == 'k':
            if len(command[0]) > 2:
                display_error('unknown_command')
            if command[0][1] in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'):
                if not G_LINE_ADRESSING:
                    """ . """
                    G_RANGE[0] = G_RANGE[1]
                G_MARKED_LINE[command[0][1]] = G_RANGE[1]
        elif command[0][0] == 'm':
            """ move lines """
            if not G_LINE_ADRESSING:
                """ .,. """
                G_RANGE[0] = G_RANGE[1]
            if len(command) > 1:
                number, index = get_first_adress(command[0][1:] + ''.join(command[1:]))
            else:
                number, index = get_first_adress(command[0][1:])
            if (number, index) == (0, 0):
                display_error('invalid_adress')
            G_BUFFER_WROTE_LAST = G_BUFFER_WROTE
            if number == 0:
                G_BUFFER_WROTE = G_BUFFER_WROTE[G_RANGE[0]:G_RANGE[1]+1] + G_BUFFER_WROTE[:G_RANGE[0]] + G_BUFFER_WROTE[G_RANGE[1]+1:]
            elif number >= G_RANGE[0] and number <= G_RANGE[1]:
                display_error('invalid_adress')
            else:
                if number < G_RANGE[0]:
                    G_BUFFER_WROTE = G_BUFFER_WROTE[:number+1] + G_BUFFER_WROTE[G_RANGE[0]:G_RANGE[1]+1] + G_BUFFER_WROTE[number+1:G_RANGE[0]] + G_BUFFER_WROTE[G_RANGE[1]+1:]
                else:
                    G_BUFFER_WROTE = G_BUFFER_WROTE[:G_RANGE[0]] + G_BUFFER_WROTE[G_RANGE[1]+1:number+1] + G_BUFFER_WROTE[G_RANGE[0]:G_RANGE[1]+1] + G_BUFFER_WROTE[number+1:]
        elif command[0] == 'n':
            if not G_LINE_ADRESSING:
                """ .,. """
                G_RANGE[0] = G_RANGE[1]
            for i in range(G_RANGE[0], G_RANGE[1]):
                print(str(i) + '	' + G_BUFFER_WROTE[i][:-1])
            G_RANGE[0] = G_RANGE[1]
        elif G_LINE_ADRESSING:
            display_error('unknown_command')
        if G_EXIT_STATUS != 0:
            """ An error ocurred """
            G_RUNNING = False
        """ reinitialize toggles """
        G_LINE_ADRESSING = False
    except Exception as error:
        """ reinitialize toggles """
        raise(error)
        G_LINE_ADRESSING = False
if G_LOOSE_EXIT_STATUS:
    sys.exit(0)
sys.exit(G_EXIT_STATUS)
