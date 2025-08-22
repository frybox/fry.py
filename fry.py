SINGLE_STRING = 'single-string'
DOUBLE_STRING = 'double-string'
BACKTICK_STRING = 'backtick-string'

def issymbolchar(ch):
    return ch.isalnum() or ch == '_' or ch == '-' or ch == '.'

def issymbolstartchar(ch):
    return ch.isalpha() or ch == '_' or ch == '-' or ch == '.'

def isspace(ch):
    return ch.isspace() or ch == ';'

def parse(code):
    size = len(code)
    i = 0
    prefetch = []

    # listbegin元素前无需空白字符，其他元素前必须有空白字符
    listbegin = True

    def getc():
        nonlocal i
        if prefetch:
            return prefetch.pop()
        elif i < size:
            ch = code[i]
            i += 1
            return ch

    def ungetc(ch):
        prefetch.append(ch)

    def error(msg):
        raise msg

    def skipspace():
        """
        空白字符和注释都是space
        """
        hasspace = False
        ch = getc()
        while ch:
            if ch.isspace():
                hasspace = True
                ch = getc()
            elif ch == ';':
                hasspace = True
                ch = getc()
                while ch:
                    if ch == '\n': break
                    ch = getc()
            else:
                ungetc(ch)
                break
        return hasspace

    def construct(t, v):
        ch = getc()

    backstr = []

    while True:
        skipspace()
        ch = getc()
        if not ch:
            break
        elif ch == '`':
            chars = []
            ch = getc()
            while ch:
                chars.append(ch)
                if ch == '\n':
                    ungetc(ch)
                    break
                ch = getc()
            chars = ''.join(chars)
            if chars:
                backstr.append(chars)
        else:
            if backstr:
                yield construct(BACKTICK_STRING, '\n'.join(backstr))
                backstr = []
            if ch == "'" or ch == '"':
                begin = ch
                chars = []
                stype = SINGLE_STRING if ch == "'" else DOUBLE_STRING
                ch = getc()
                while ch:
                    if ch == '\\':
                        ch = getc()
                        if ch:
                            if ch == '\n':
                                error("string is not closed in the same line")
                            chars.append(ch)
                        else: continue
                    elif ch == '\n':
                        error("string is not closed in the same line")
                    elif ch == begin:
                        ch = getc()
                        yield construct(stype, ''.join(chars))
                        chars = []
                        break
                    else:
                        chars.append(ch)
                        ch = getc()
                else: error("string is not closed")
            elif ch == ':':
                pass
            elif ch == '&':
                pass
            elif ch == '.':
                pass
            elif ch == '+':
                pass
            elif ch == '-':
                pass
            elif ch == '*':
                pass
            elif ch == '/':
                pass
            elif ch == '=':
                pass
            elif ch == '!':
                pass
            elif ch == '>':
                pass
            elif ch == '<':
                pass
            elif ch == '(':
                pass
            elif ch == ')':
                pass
            elif ch == '[':
                pass
            elif ch == ']':
                pass
            elif ch == '{':
                pass
            elif ch == '}':
                pass

    if backstr:
        yield construct(BACKTICK_STRING, '\n'.join(backstr))
        backstr = []
