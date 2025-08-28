#!/usr/bin/env python
import unicodedata
import string

NONE              = 'none'
TRUE              = 'true'
FALSE             = 'false'
VARARG            = '...'
INTEGER           = 'integer'
FLOAT             = 'float'
SINGLE_STRING     = 'single-string'
DOUBLE_STRING     = 'double-string'
BACKTICK_STRING   = 'backtick-string'
INTERN_STRING     = 'intern-string'
IDENTIFIER        = 'identifier'
MULTI_IDENTIFIER  = 'multi-identifier'
LIST_REMINDER     = 'list-reminder'
CODE_LIST         = 'code-list'
LIST_LIST         = 'list-list'
DICT_LIST         = 'dict-list'
HASHFN_LIST       = 'hashfn-list'


# 各种CODE_LIST
DO_LIST           = 'do-list'
MATCH_LIST        = 'match-list'
CASE_LIST         = 'case-list'
DEFAULT_LIST      = 'default-list'
COND_LIST         = 'cond-list'
IF_LIST           = 'if-list'
ELIF_LIST         = 'elif-list'
ELSE_LIST         = 'else-list'
WHILE_LIST        = 'while-list'
FOR_LIST          = 'for-list'
EACH_LIST         = 'each-list'
FN_LIST           = 'fn-list'
LET_LIST          = 'let-list'
VAR_LIST          = 'var-list'
IMPORT_LIST       = 'import-list'
VALUES_LIST       = 'values-list'

class AstNode:
    def __init__(self, tag, value=None, suffix=None):
        self.tag = tag
        self.value = value
        self.suffix = suffix

    def append(self, value):
        self.value.append(value)

    def last(self):
        return self.value[-1]

    def __repr__(self):
        if self.tag in (NONE, TRUE, FALSE, VARARG):
            value = self.tag
        elif self.tag in (INTEGER, FLOAT, IDENTIFIER, MULTI_IDENTIFIER):
            value = self.value
        elif self.tag == SINGLE_STRING:
            value = f"'{self.value}'"
        elif self.tag == DOUBLE_STRING:
            value = f'"{self.value}"'
        elif self.tag == BACKTICK_STRING:
            value = f'`{self.value}`'
        elif self.tag == INTERN_STRING:
            value = f':{self.value}'
        elif self.tag == LIST_REMINDER:
            value = f'&{self.value}'
        elif self.tag == CODE_LIST:
            value = ' '.join(f'{v}' for v in self.value)
            value = f'({value})'
        elif self.tag == LIST_LIST:
            value = ' '.join(f'{v}' for v in self.value)
            value = f'[{value}]'
        elif self.tag == DICT_LIST:
            value = ' '.join(f'{v}' for v in self.value)
            value = '{' + value + '}'
        elif self.tag == HASHFN_LIST:
            value = f'#{self.value[0]}'
        if self.suffix:
            return f"{value}{self.suffix}"
        else:
            return f"{value}"


# ascii字符的printable字符（string.printable)共有100个字符，包括：
# - 26个大写字母   (string.ascii_uppercase)
# - 26个小写字母   (string.ascii_lowercase)
# - 10个阿拉伯数字 (string.digits)
# - 32个标点符号   (string.punctuation)
# - 6个空白字符    (string.whitespace)
# 6个空白字符: [9, 13] or 32
# 其他94个printable字符: [33, 127)

# str.isspace()除了6个ascii空白字符外，还包含对全角空格等空白字符的检测，
# 比下面这个is_whitespace_ascii强
def is_whitespace_ascii(ch):
    n = ord(ch)
    return n == 32 or (n >= 9 and n <=13)

def is_visible_ascii(ch):
    n = ord(ch)
    return n >= 32 and n < 127

def is_visible_utf8(ch):
    if ch.isspace():
        return False
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
    i = 0
    prefetch = []
    root = AstNode(CODE_LIST, [])
    stack = [root]

    def getc():
        nonlocal i
        if prefetch:
            return prefetch.pop()
        elif i < len(code):
            ch = code[i]
            i += 1
            return ch

    def ungetc(ch):
        prefetch.append(ch)

    def get_intern():
        chars = []
        ch = getc()
        while ch:
            if is_intern(ch):
                chars.append(ch)
                ch = getc()
            else:
                ungetc(ch)
                break
        return ''.join(chars)

    def get_identifier():
        chars = []
        ch = getc()
        while ch:
            if is_identifier(ch):
                chars.append(ch)
                ch = getc()
            else:
                ungetc(ch)
                break
        return ''.join(chars)

    def get_multi_identifier():
        chars = []
        ch = getc()
        while ch:
            if is_multi_identifier(ch):
                chars.append(ch)
                ch = getc()
            else:
                ungetc(ch)
                break
        return ''.join(chars)

    def tonumber(s):
        try:
            return 'int', int(s, 0)
        except ValueError:
            try:
                return 'float', float(s)
            except ValueError:
                return 'nan', 0

    def error(msg):
        print(root)
        raise RuntimeError(msg)

    def finish_node(node):
        ch = getc()
        suffix = None
        if ch == ':':
            suffix = ch
        elif ch == ',':
            pass
        elif ch:
            ungetc(ch)
        parent = stack[-1]
        if parent.tag == HASHFN_LIST:
            parent.append(node)
            parent.suffix = suffix
            node = stack.pop()
            parent = stack[-1]
        elif parent.tag not in (CODE_LIST, LIST_LIST, DICT_LIST):
            error(f"Invalid parent node: {parent}")
        else:
            node.suffix = suffix
        parent.append(node)
        return node

    def construct(t, v=None):
        node = AstNode(t, v)
        return finish_node(node)

    def begin_list(t):
        # 1. list不能处理后缀，否则会把':'前缀吃掉
        # 2. list需要处理enstack逻辑
        if t == HASHFN_LIST and stack[-1].tag == HASHFN_LIST:
            error("Hashfn does not support hashfn")
        node = AstNode(t, [])
        stack.append(node)
        return node

    def finish_list(t):
        if stack[-1].tag != t:
            print(stack[-1])
            error("unpaired )/]/}")
        if stack[-1] is root:
            error("redundant ')'")
        node = stack.pop()
        return finish_node(node)

    # listbegin元素前无需空白字符，其他元素前必须有空白字符
    listbegin = True
    hasspace = False

    # backtick字符串
    backstr = []

    while True:
        """
        略过空白字符。
        空白字符字符串不跨行(这里的空白字符不包括\n)，空行用来分隔反引号字符串
        如果存在空白字符，设置hasspace为True
        """
        ch = getc()
        while ch:
            if ch != '\n' and ch.isspace():
                hasspace = True
                ch = getc()
            else: break
        else: break
        listend = ch in ')]}'
        comment = ch == ';'
        newline = ch == '\n'
        if not (listbegin or listend or comment or newline) and not hasspace:
            # 除了列表开头元素/列表结束字符以及注释和新行，其他元素前必须有空白字符
            error(f"{ch}: list elements after the first one should start with whitespace")

        hasspace = False

        if ch in '([{#':
            listbegin = True
        else:
            listbegin = False

        if ch != '`' and backstr:
            # 当前不是backtick字符串了，前面有连续的backtick字符串行的话，
            # 合并为一个字符串
            # 注：遇到注释和空行，多行backtick字符串也不能合并，这对于
            #     连续两个多行backtick字符串参数很有用，如函数docstring
            #     和返回一个字符串的情况：
            # (fn foo []:
            #   `这是函数foo
            #   `
            #   `本函数没有参数，返回一段神秘字符串
            #
            #   `这是神秘字符串开始
            #   `这是神秘字符串结束
            # )
            construct(BACKTICK_STRING, ''.join(backstr))
            backstr = []

        if ch == '\n':
            hasspace = True
        elif ch == ';':
            ch = getc()
            while ch:
                if ch == '\n':
                    hasspace = True
                    break
                ch = getc()
        elif ch == '`':
            chars = []
            ch = getc()
            while ch:
                chars.append(ch)
                if ch == '\n':
                    hasspace = True
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
                    else: break
                    ch = getc()
                elif ch == '\n':
                    error("string is not closed in the same line")
                elif ch == begin:
                    construct(stype, ''.join(chars))
                    chars = []
                    break
                else:
                    chars.append(ch)
                    ch = getc()
            else: error("string is not closed")
        elif ch == ':':
            s = get_intern()
            if not s:
                error("invalid intern string")
            construct(INTERN_STRING, s)
        elif ch == '&':
            s = get_identifier()
            if not s:
                error("invalid reminder list identifier")
            construct(LIST_REMINDER, s)
        elif ch == '#':
            begin_list(HASHFN_LIST)
        elif ch == '(':
            begin_list(CODE_LIST)
        elif ch == ')':
            finish_list(CODE_LIST)
        elif ch == '[':
            begin_list(LIST_LIST)
        elif ch == ']':
            finish_list(LIST_LIST)
        elif ch == '{':
            begin_list(DICT_LIST)
        elif ch == '}':
            finish_list(DICT_LIST)
        else:
            ungetc(ch)
            s = get_multi_identifier()
            if not s:
                error("invalid character")
            nt, n = tonumber(s)
            if nt == 'int':
                construct(INTEGER, n)
            elif nt == 'float':
                construct(FLOAT, n)
            elif s == 'true':
                construct(TRUE)
            elif s == 'false':
                construct(FALSE)
            elif s == 'none':
                construct(NONE)
            elif s == '...':
                construct(VARARG)
            elif s in ('..', '.'):
                construct(IDENTIFIER, s)
            elif '..' in s:
                error(f"Invalid multi-identifier: {s}")
            elif s[0] == '.':
                s = s[1:]
                if '.' in s:
                    construct(CODE_LIST, [AstNode(IDENTIFIER, '.'), AstNode(MULTI_IDENTIFIER, s)])
                else:
                    construct(CODE_LIST, [AstNode(IDENTIFIER, '.'), AstNode(IDENTIFIER, s)])
            elif '.' in s:
                construct(MULTI_IDENTIFIER, s)
            else:
                construct(IDENTIFIER, s)
    if backstr:
        construct(BACKTICK_STRING, ''.join(backstr))
        backstr = []
    return root

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <.fry file>")
        sys.exit(1)
    with open(sys.argv[1], encoding='utf-8') as f:
        data = f.read()
    ast = parse(data)
    print(ast)

