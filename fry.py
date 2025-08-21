SINGLE_STRING = 'single-string'
DOUBLE_STRING = 'double-string'
BACKTICK_STRING = 'backtick-string'

def issymbolchar(ch):
    return ch.isalnum() or ch == '_' or ch == '-' or ch == '.'

def issymbolstartchar(ch):
    return ch.isalpha() or ch == '_' or ch == '-' or ch == '.'

def parse(code):
    size = len(code)
    i = 0
    prefetch = []

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

    backstr = []

    while True:
        ch = getc()
        while ch:
            if not ch.isspace():
                break
            ch = getc()
        else: break

        if ch == ';':
            ch = getc()
            while ch:
                if ch == '\n': break
                ch = getc()
            else: break
        elif ch == '`':
            chars = []
            ch = getc()
            while ch:
                chars.append(ch)
                if ch == '\n':
                    break
                ch = getc()
            backstr.append(''.join(chars))
        else:
            if backstr:
                yield BACKTICK_STRING, ''.join(backstr)
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
                        yield stype, ''.join(chars)
                        chars = []
                        break
                    else:
                        chars.append(ch)
                        ch = getc()
                else: error("string is not closed")
            elif ch == ':':

    if backstr:
        yield BACKTICK_STRING, ''.join(backstr)
        backstr = []
