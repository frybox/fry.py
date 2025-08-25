NUMBER          = 'number'
SINGLE_STRING   = 'single-string'
DOUBLE_STRING   = 'double-string'
BACKTICK_STRING = 'backtick-string'
SYMBOL          = 'symbol'             #符号
MULTI_SYMBOL    = 'multi-symbol'       #联符
IDENTIFIER      = 'identifier'
DO_LIST         = 'do-list'
MATCH_LIST      = 'match-list'
CASE_LIST       = 'case-list'
DEFAULT_LIST    = 'default-list'
COND_LIST       = 'cond-list'
IF_LIST         = 'if-list'
ELIF_LIST       = 'elif-list'
ELSE_LIST       = 'else-list'
WHILE_LIST      = 'while-list'
FOR_LIST        = 'for-list'
EACH_LIST       = 'each-list'
LIST_LIST       = 'list-list'
DICT_LIST       = 'dict-list'
FN_LIST         = 'fn-list'
CALL_LIST       = 'call-list'
LET_LIST        = 'let-list'
VAR_LIST        = 'var-list'
IMPORT_LIST     = 'import-list'

class AstNode:
    def __init__(self, tag, value, suffix=None):
        self.tag = tag
        self.value = value
        self.suffix = suffix

    def append(self, value):
        self.value.append(value)

    def last(self):
        return self.value[-1]


def issymbolchar(ch):
    return ch.isalnum() or ch == '_' or ch == '-'

def ismultisymbolchar(ch):
    return issymbolchar(ch) or ch == '.'

def issymbolstartchar(ch):
    return ch.isalpha() or ch == '_'

def isspace(ch):
    return ch.isspace() or ch == ';'

def parse(code):
    size = len(code)
    i = 0
    prefetch = []
    root = AstNode(DO_LIST, [])
    stack = [root]

    # listbegin元素前无需空白字符，其他元素前必须有空白字符
    listbegin = True
    hasspace = False

    backstr = []

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
        略过空白字符和注释。
        如果存在空白字符和注释，设置hasspace为True
        """
        nonlocal hasspace
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

    def construct(t, v=None):
        ch = getc()
        suffix = None
        if ch == ':' suffix = ch
        ungetc(ch)
        node = AstNode(t, v, suffix)
        stack[-1].append(node)


    while True:
        skipspace()
        ch = getc()
        if not ch:
            break
        listend = ch in ')]}'
        if not listbegin and not listend and not hasspace:
            # 除了列表开头元素和列表结束字符，其他元素前必须有空白字符
            error("list element except first one should start with space")

        if ch in '([{':
            listbegin = True
        else:
            listbegin = False

        if ch != '`' and backstr:
            # 当前不是backtick字符串了，前面有backtick字符串的话，需要合并为一个字符串
            construct(BACKTICK_STRING, '\n'.join(backstr))
            backstr = []

        if ch == '`':
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
        elif ch == "'" or ch == '"':
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
                    construct(stype, ''.join(chars))
                    chars = []
                    break
                else:
                    chars.append(ch)
                    ch = getc()
            else: error("string is not closed")
        elif ch == ':':
            chars = []
            ch = getc()
            if issymbolstartchar(ch):
                chars.append(ch)
            else:
                error("invalid symbol")
            while ch:
                if issymbolchar(ch):
                    chars.append(ch)
                    ch = getc()
                else: break
            construct(SYMBOL, ''.join(chars))
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
        else:
            pass

    if backstr:
        construct(BACKTICK_STRING, '\n'.join(backstr))
        backstr = []
    return root
