import unicodedata
import string

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


# ascii字符的printable字符（string.printable)共有100个字符，包括：
# - 26个大写字母   (string.ascii_uppercase)
# - 26个小写字母   (string.ascii_lowercase)
# - 10个阿拉伯数字 (string.digits)
# - 32个标点符号   (string.punctuation)
# - 6个空白字符    (string.whitespace)
# 6个空白字符: [9, 13] or 32
# 其他94个printable字符: [33, 127)
# str.isspace()包含对全角空格等空白字符的检测，比下面这个is_whitespace_ascii强
def is_whitespace_ascii(ch):
    n = ord(ch)
    return n == 32 or (n >= 9 and n <=13)

def is_visible_ascii(ch):
    n = ord(ch)
    return n >= 32 and n < 127

def is_visible_utf8(ch):
    if is_visible_ascii(ch):
        return True
    category = unicodedata.category(ch)
    if category[0] in 'CZ' or category in ('Mn', 'Me'):
        return False
    return True

def is_intern(ch):
    return is_visible_utf8(ch) and ch not in ':;,\'"`()[]{}'

def is_identifier(ch):
    return is_intern(ch) and ch not in '&@#.'

def is_multi_identifier(ch):
    return is_intern(ch) and ch not in  '&@#'

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
        略过空白字符。
        空白字符字符串不跨行(空白字符不包括\n)，空行用来分隔反引号字符串
        如果存在空白字符，设置hasspace为True
        """
        nonlocal hasspace
        ch = getc()
        while ch:
            if ch != '\n' and ch.isspace():
                hasspace = True
                ch = getc()
            else:
                ungetc(ch)
                break

    def construct(t, v=None):
        ch = getc()
        suffix = None
        if ch == ':'
            suffix = ch
            ungetc(ch)
        elif ch == ',':
            pass
        node = AstNode(t, v, suffix)
        stack[-1].append(node)


    while True:
        skipspace()
        ch = getc()
        if not ch:
            break
        listend = ch in ')]}'
        comment = ch == ';'
        if not (listbegin or listend or comment) and not hasspace:
            # 除了列表开头元素/列表结束字符以及注释，其他元素前必须有空白字符
            error("list element except first one should start with space")

        hasspace = False

        if ch in '([{':
            listbegin = True
        else:
            listbegin = False

        if ch != '`' and backstr:
            # 当前不是backtick字符串了，前面有backtick字符串行的话，合并为一个字符串
            # 注：遇到注释和空行，多行backtick字符串也不能合并
            construct(BACKTICK_STRING, '\n'.join(backstr))
            backstr = []

        if ch == '\n':
            hasspace = True
        elif ch == ';':
            ch = getc()
            while ch:
                if ch == '\n':
                    ungetc(ch)
                    break
                ch = getc()
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
