#!/usr/bin/env python
import unicodedata
import string

NONE              = 'none'
TRUE              = 'true'
FALSE             = 'false'
INTEGER           = 'integer'
FLOAT             = 'float'
SINGLE_STRING     = 'single-string'
DOUBLE_STRING     = 'double-string'
BACKTICK_STRING   = 'backtick-string'
EXTERN_STRING     = 'extern-string'   # extern = single + double + backtick
INTERN_STRING     = 'intern-string'
STRING            = 'string'          # string = extern + intern
VARARG            = '...'
IDENTIFIER        = 'identifier'
MULTI_IDENTIFIER  = 'multi-identifier'
AND_REMINDER      = 'and-reminder'
AT_WHOLE          = 'at-whole'
CODE_LIST         = 'code-list'
HASH_LIST         = 'hash-list'
LIST_LIST         = 'list-list'
DICT_LIST         = 'dict-list'

UPVALUE           = 'upvalue'
CLOSURE           = 'closure'

# 各种特殊的CODE_LIST
DO_LIST           = 'do-list'         # new scope
MATCH_LIST        = 'match-list'
CASE_LIST         = 'case-list'       # new scope
DEFAULT_LIST      = 'default-list'    # new scope
IF_LIST           = 'if-list'         # new scope
ELIF_LIST         = 'elif-list'       # new scope
ELSE_LIST         = 'else-list'       # new scope
WHILE_LIST        = 'while-list'      # new scope
FOR_LIST          = 'for-list'        # new scope
EACH_LIST         = 'each-list'       # new scope
BREAK_LIST        = 'break-list'
CONTINUE_LIST     = 'continue-list'
FN_LIST           = 'fn-list'         # new scope
LET_LIST          = 'let-list'
VAR_LIST          = 'var-list'
SET_LIST          = 'set-list'
IMPORT_LIST       = 'import-list'
VALUES_LIST       = 'values-list'
AND_LIST          = 'and-list'
OR_LIST           = 'or-list'
NOT_LIST          = 'not-list'
# (? predicate true-expr false-expr)，类似C语言中的 predicate ? true-expr : false-expr
QUESTION_LIST     = '?-list'

TRY_LIST          = 'try-list'        # new scope
CATCH_LIST        = 'catch-list'      # new scope
FINALLY_LIST      = 'finally-list'    # new scope
TRHOW_LIST        = 'throw-list'

# 各种内置的正常CODE_LIST
DOT_LIST          = '.-list'
DOTDOT_LIST       = '..-list'
ADD_LIST          = '+-list'
SUB_LIST          = '--list'
MUL_LIST          = '*-list'
DIV_LIST          = '/-list'
DIVDIV_LIST       = '//-list'
MOD_LIST          = 'mod-list'
EQ_LIST           = '=-list'
NE_LIST           = '!=-list'
LT_LIST           = '<-list'
GT_LIST           = '>-list'
LE_LIST           = '<=-list'
GE_LIST           = '>=-list'
IS_LIST           = 'is-list'  #同一个对象，地址相同
MAP_LIST          = 'map-list'
FILTER_LIST       = 'filter-list'
LEN_LIST          = 'len-list'


new_scope_creators = set(
        'do',
        'case',
        'default',
        'if',
        'elif',
        'else',
        'while',
        'for',
        'each',
        'fn',
        'try',
        'catch',
        'finally',
        )

class Variable:
    def __init__(self, name, ast, isupval=False):
        self.name = name
        self.ast = ast
        self.isupvar = isupval


class AstNode:
    def __init__(self, tag, value=None, suffix=None):
        self.tag = tag
        self.value = value
        self.suffix = suffix
        self.parent = None
        self.boundvars = None    # name set
        self.upvars = None       # name -> ast

    def append(self, value):
        self.value.append(value)
        value.parent = self

    def prev(self):
        if not self.parent:
            return None
        siblings = self.parent.value
        i = siblings.index(self)
        if i == 0: return None
        return siblings[i-1]

    def next(self):
        if not self.parent:
            return None
        siblings = self.parent.value
        i = siblings.index(self)
        if i == len(siblings)-1: return None
        return siblings[i+1]

    def isfn(self):
        if self.tag == HASH_LIST:
            return True
        if self.tag == CODE_LIST:
            v0 = self.value[0]
            if v0.tag == IDENTIFIER and v0.value == 'fn':
                return True
        return False

    def getfn(self):
        node = self
        while node.parent:
            node = self.parent
            if node.isfn():
                return node

    def gethashfn(self):
        fn = self.getfn()
        while fn:
            if fn.tag == HASH_LIST:
                return fn
            fn = fn.getfn()
        return None

    def isscope(self):
        if self.tag == HASH_LIST:
            return True
        elif self.tag == CODE_LIST:
            v0 = self.value[0]
            if v0.tag == IDENTIFIER and v0.value in new_scope_creators:
                return True
        return False

    def getscope(self):
        node = self
        while node.parent:
            node = self.parent
            if node.isscope():
                return node

    def addvar(self, name, candup=False):
        scope = self
        if not scope.isscope():
            raise RuntimeError(f"Not scope to add {name}")
        if scope.boundvars is None:
            scope.boundvars = set()
        if not candup and name in scope.boundvars:
            raise RuntimeError(f"Duplicate definition: {name}")
        scope.boundvars.add(name)

    def addvartoscope(self, name, candup=False):
        scope = self.getscope()
        if not scope:
            raise RuntimeError(f"No scope to add {name}")
        scope.addvar(name, candup)

    def getvar(self, name):
        """在本节点查找变量，包括绑定变量和捕获变量"""
        if not node.isscope():
            return None
        if self.boundvars is None:
            return None
        if name in self.boundvars:
            return Variable(name, self)
        if not node.isfn():
            return None
        if self.upvars is None:
            return None
        if name in self.upvars:
            return Variable(name, self.upvars[name], True)
        return None

    def queryvar(self, name=None):
        """
        在本节点及祖先节点查找变量，包括绑定变量和捕获变量。
        如果是closure之外的变量，保存到closure捕获变量列表。
        """
        name = name if name else self.value
        node = self
        closure = None
        while node:
            var = node.getvar(name)
            if var:
                if closure:
                    var.isupvar = True
                    if closure.upvars is None:
                        closure.upvars = {}
                    closure.upvars[name] = var.ast
                return var
            if not closure and node.isfn():
                closure = node
            node = node.parent
        return None

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
        elif self.tag == AND_REMINDER:
            value = f'&{self.value}'
        elif self.tag == AT_WHOLE:
            value = f'@{self.value}'
        elif self.tag == CODE_LIST:
            value = ' '.join(f'{v}' for v in self.value)
            value = f'({value})'
        elif self.tag == LIST_LIST:
            value = ' '.join(f'{v}' for v in self.value)
            value = f'[{value}]'
        elif self.tag == DICT_LIST:
            value = ' '.join(f'{v}' for v in self.value)
            value = '{' + value + '}'
        elif self.tag == HASH_LIST:
            value = f'#{self.value[0]}'
        if self.suffix:
            return f"{value}{self.suffix}"
        else:
            return f"{value}"


class Frame:
    """
    动态作用域
    """
    def __init__(self, ast):
        self.ast = ast
        self.variables = {}


class Value:
    def __init__(self, tag, value=None):
        self.tag = tag
        self.value = value


class UpValue(Value):
    def __init__(self, frame, name):
        super().__init__(UPVALUE)
        self.isopen = True
        self.frame = frame
        self.name = name


class Closure(Value):
    def __init__(self, fn):
        """
        fn是fn/hashfn的ast
        """
        super().__init__(CLOSURE, fn)
        self.upvalues = {}


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

def is_strict_identifier(ch):
    return ch.isalnum() or ch == '_' or ch == '-'

def is_identifier(ch):
    return is_intern(ch) and ch not in '&@#.'

def is_multi_identifier(ch):
    return is_intern(ch) and ch not in  '&@#'

def lex(code):
    i = 0
    prefetch = []
    root = AstNode(CODE_LIST, [AstNode(IDENTIFIER, 'do', ':')])
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

    # 上个元素是否有后缀
    hassuffix = False

    def finish_node(node):
        nonlocal hassuffix
        ch = getc()
        suffix = None
        # ':'和','后可以不用带空白字符
        if ch == ':':
            suffix = ch
            hassuffix = True
        elif ch == ',':
            hassuffix = True
        elif ch:
            ungetc(ch)
        parent = stack[-1]
        if parent.tag == HASH_LIST:
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
        if t == HASH_LIST and stack[-1].tag == HASH_LIST:
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

    # backtick字符串
    backstr = []

    # listbegin元素前无需空白字符，其他元素前必须有空白字符
    listbegin = True

    hasspace = False

    hassuffix = False

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
        if not (listbegin or listend or hassuffix or comment or newline) and not hasspace:
            # 除了列表开头元素/列表结束字符/上个元素有后缀以及注释和新行，其他元素前必须有空白字符
            error(f"{ch}: list elements after the first one should start with whitespace")

        hasspace = False
        hassuffix = False

        if ch in '([{#': # codelist, listlist, dictlist or hashlist
            listbegin = True
        else:
            listbegin = False

        if ch != '`' and backstr:
            # 前面处理了连续的backtick字符串，但当前不是backtick字符串了，
            # 合并为一个字符串
            # 注：多行backtick字符串之间如果有注释或空行，则不能合并，
            #     连续两个多行backtick字符串参数可通过注释或空行分隔，如函数docstring
            #     和返回一个字符串的情况：
            # (fn foo []:
            #   `这是函数foo
            #   `
            #   `本函数没有参数，返回一段神秘字符串
            #
            #   `这是返回的神秘字符串开始
            #   `这是返回的神秘字符串结束
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
                error("invalid &-reminder identifier")
            construct(AND_REMINDER, s)
        elif ch == '@':
            s = get_identifier()
            if not s:
                error("invalid @-whole identifier")
            construct(AT_WHOLE, s)
        elif ch == '#':
            begin_list(HASH_LIST)
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
                    ss = s.split('.')
                    ss[0] = '$1' if ss[0] == '$' else ss[0]
                    s = '.'.join(ss)
                    construct(CODE_LIST, [AstNode(IDENTIFIER, '.'), AstNode(MULTI_IDENTIFIER, s)])
                else:
                    s = '$1' if s == '$' else s
                    construct(CODE_LIST, [AstNode(IDENTIFIER, '.'), AstNode(IDENTIFIER, s)])
            elif '.' in s:
                ss = s.split('.')
                ss[0] = '$1' if ss[0] == '$' else ss[0]
                s = '.'.join(ss)
                construct(MULTI_IDENTIFIER, s)
            else:
                s = '$1' if s == '$' else s
                construct(IDENTIFIER, s)
    if backstr:
        construct(BACKTICK_STRING, ''.join(backstr))
        backstr = []
    return root


builtins = set([
    '.',
    '..',
    '+',
    '-',
    '*',
    '/',
    '//',
    'mod',
    '=',
    '!=',
    '<',
    '>',
    '<=',
    '>=',
    'is',
    'map',
    'filter',
    'len',
])


def parse(ast):
    if ast.tag in (NONE, TRUE, FALSE):
        pass
    elif ast.tag in (INTEGER, FLOAT):
        pass
    elif ast.tag in (SINGLE_STRING, DOUBLE_STRING, BACKTICK_STRING, INTERN_STRING):
        pass
    elif ast.tag == VARARG:
        scope = ast.getscope()
        while scope:
            if scope.getvar('...'):
                return
            if scope.isfn():
                raise RuntimeError("vararg ... is not declared in the current function")
            scope = scope.getscope()
        else: raise RuntimeError("vararg ... is not declared in the current function")
    elif ast.tag == IDENTIFIER:
        if ast.value in builtins:
            return
        if len(ast.value) == 2 and ast.value[0] == '$' and ast.value[1].isdigit():
            n = int(ast.value[1])
            hash = ast.gethashfn()
            for i in range(1, n+1):
                arg = f'${i}'
                hash.addvar(arg, True)
        var = ast.queryvar()
        if not var:
            raise RuntimeError(f"Unknown identifier {ast.value}")
    elif ast.tag == MULTI_IDENTIFIER:
        i = ast.value.index['.']
        name = ast.value[:i]
        var = ast.queryvar(name)
        if not var:
            raise RuntimeError(f"Unknown identifier {name}")
    elif ast.tag in (AND_REMINDER, AT_WHOLE):
        raise RuntimeError("Invalid &reminder or @whole")
    elif ast.tag == CODE_LIST:
        parse_code_list(ast)
    elif ast.tag == HASH_LIST:
        if len(ast.value) != 1:
            raise RuntimeError("Invalid hash function")
        parse(ast.value[0])
    elif ast.tag == LIST_LIST:
        for item in ast.value:
            parse(item)
    elif ast.tag == DICT_LIST:
        pairs = []
        key = None
        for item in ast.value:
            if not key:
                if item.suffix == ':':
                    if item.tag == IDENTIFIER:
                        item.tag = INTERN_STRING
                    parse(item)
                    key = item
                    continue
                else:
                    if item.tag == IDENTIFIER:
                        key = AstNode(INTERN_STRING, item.value)
                    elif (item.tag == CODE_LIST and
                          len(item.value) == 2 and
                          item.value[0].tag == IDENTIFIER and
                          item.value[0].value == '.' and
                          item.value[1].tag == IDENTIFIER):
                        key = AstNode(INTERN_STRING, item.value[1].value)
                    else:
                        raise RuntimeError("Invalid dict expression")
            parse(item)
            pairs.append((key, item))
            key = None
        ast.value = pairs
    else:
        error(f"invalid ast: {ast}")
    

def parse_destructure(ast):
    if ast.tag == IDENTIFIER:
        ast.addvartoscope(ast.value)
    elif ast.tag == VARARG:
        ast.addvartoscope('...')
    elif ast.tag == LIST_LIST:
        for item in ast.value:
            if not item.suffix:
                raise RuntimeError(f"Invalid list item suffix '{item.suffix}'")
            elif item.tag in (IDENTIFIER, AND_REMINDER, AT_WHOLE):
                ast.addvartoscope(ast.value)
            elif item.tag in (LIST_LIST, DICT_LIST):
                parse_destructure(item)
            else:
                raise RuntimeError("invalid list destructure")
    elif ast.tag == DICT_LIST:
        pairs = []
        key = None
        for item in ast.value:
            if not key:
                if item.suffix == ':':
                    if item.tag == IDENTIFIER:
                        item.tag = INTERN_STRING
                    parse(item)
                    key = item
                elif item.tag == IDENTIFIER:
                    k = AstNode(INTERN_STRING, item.value)
                    ast.addvartoscope(item.value)
                    pairs.append((k, item))
                elif item.tag == AND_REMINDER:
                    k = AstNode(INTERN_STRING, '&')
                    ast.addvartoscope(item.value)
                    pairs.append((k, item))
                elif item.tag == AT_WHOLE:
                    k = AstNode(INTERN_STRING, '@')
                    ast.addvartoscope(item.value)
                    pairs.append((k, item))
                else:
                    raise RuntimeError("invalid dict destructure")
            elif item.tag in (IDENTIFIER, LIST_LIST, DICT_LIST):
                parse_destructure(item)
                pairs.append((key, item))
                key = None
            else:
                raise RuntimeError(f"Invalid dict value {item}")
        ast.value = pairs
    else:
        error(f"invalid destructure: {ast}")

def parse_pattern(ast):
    if ast.tag in (NONE, TRUE, FALSE):
        pass
    elif ast.tag in (INTEGER, FLOAT):
        pass
    elif ast.tag in (SINGLE_STRING, DOUBLE_STRING, BACKTICK_STRING, INTERN_STRING):
        pass
    elif ast.tag == VARARG:
        ast.addvartoscope('...')
    elif ast.tag == IDENTIFIER:
        ast.addvartoscope(ast.value)
    elif ast.tag == CODE_LIST:
        parse_code_list(ast)
    elif ast.tag == LIST_LIST:
        for item in ast.value:
            if not item.suffix:
                raise RuntimeError(f"Invalid list item suffix '{item.suffix}'")
            elif item.tag in (IDENTIFIER, AND_REMINDER, AT_WHOLE):
                ast.addvartoscope(ast.value)
            elif item.tag in (NONE, TRUE, FALSE, INTEGER, FLOAT,
                              SINGLE_STRING, DOUBLE_STRING, BACKTICK_STRING,
                              INTERN_STRING):
                pass
            elif ast.tag == CODE_LIST:
                parse_code_list(ast)
            elif item.tag in (LIST_LIST, DICT_LIST):
                parse_pattern(item)
            else:
                raise RuntimeError("invalid list destructure")
    elif ast.tag == DICT_LIST:
        pairs = []
        key = None
        for item in ast.value:
            if not key:
                if item.suffix == ':':
                    if item.tag == IDENTIFIER:
                        item.tag = INTERN_STRING
                    parse(item)
                    key = item
                elif item.tag == IDENTIFIER:
                    k = AstNode(INTERN_STRING, item.value)
                    ast.addvartoscope(item.value)
                    pairs.append((k, item))
                elif item.tag == AND_REMINDER:
                    k = AstNode(INTERN_STRING, '&')
                    ast.addvartoscope(item.value)
                    pairs.append((k, item))
                elif item.tag == AT_WHOLE:
                    k = AstNode(INTERN_STRING, '@')
                    ast.addvartoscope(item.value)
                    pairs.append((k, item))
                elif (item.tag == CODE_LIST and
                      len(item.value) == 2 and
                      item.value[0].tag == IDENTIFIER and
                      item.value[0].value == '.' and
                      item.value[1].tag == IDENTIFIER):
                    parse(item)
                    k = AstNode(INTERN_STRING, item.value[1].value)
                    pairs.append((k, item))
                else:
                    raise RuntimeError("invalid dict destructure")
            elif item.tag not in (VARARG, AND_REMINDER, AT_WHOLE, HASH_LIST):
                parse_pattern(item)
                pairs.append((key, item))
                key = None
            else:
                raise RuntimeError(f"Invalid dict value {item}")
        ast.value = pairs
    else:
        error(f"invalid ast: {ast}")
    

def parse_code_list(ast):
        if not ast.value:
            raise RuntimeError("Invalid empty code list")
        specials = {
            'do': parse_do,
            'match': parse_match,
            'case': parse_case,
            'default': parse_default,
            'if': parse_if,
            'elif': parse_elif,
            'else': parse_else,
            'while': parse_while,
            'for': parse_for,
            'each': parse_each,
            'break': parse_break,
            'continue': parse_continue,
            'fn': parse_fn,
            'let': parse_let,
            'var': parse_var,
            'set': parse_set,
            'import': parse_import,
            'values': parse_values,
            'and': parse_and,
            'or': parse_or,
            'not': parse_not,
            '?': parse_question,
            'try': parse_try,
            'catch': parse_catch,
            'finally': parse_finally,
            'throw': parse_throw,
        }

        def parse_do():
            op = ast.value[0]
            if op.suffix != ':':
                raise RuntimeError("No ':' after do")
            ast.special = DO_LIST
            for item in ast.value[1:]:
                parse(item)
        def parse_match():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid match expression")
            ast.special = MATCH_LIST
            expr = ast.value[1]
            if expr.suffix != ':':
                raise RuntimeError("No ':' after match expression")
            parse(expr)
            for item in ast.value[2:]:
                parse(item)
        def parse_case():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid case expression")
            if ast.parent.special != MATCH_LIST:
                raise RuntimeError("case expression must be in match expression")
            ast.special = CASE_LIST
            pattern = ast.value[1]
            if pattern.suffix != ':':
                raise RuntimeError("No ':' after case pattern")
            if pattern.tag != CODE_LIST:
                parse_pattern(pattern)
            elif not pattern.value:
                raise RuntimeError("Invalid case pattern")
            elif pattern.value[0].tag != IDENTIFIER:
                raise RuntimeError("Invalid case pattern")
            elif pattern.value[0].value == 'values':
                for p in pattern.values[1:]:
                    parse_pattern(p)
            elif pattern.value[0].value == 'and':
                if len(pattern.value) < 2:
                    raise RuntimeError("Invalid case pattern")
                parse_pattern(pattern.value[1])
                for item in pattern.value[2:]:
                    parse(item)
            elif pattern.value[0].value == 'or':
                if len(pattern.value) < 2:
                    raise RuntimeError("Invalid case pattern")
                for p in pattern.values[1:]:
                    parse_pattern(p)
            else:
                raise RuntimeError("Invalid case pattern")
            for item in ast.value[2:]:
                parse(item)
        def parse_default():
            if len(ast.value) < 2:
                raise RuntimeError("Invalid default expression")
            if ast.parent.special != MATCH_LIST:
                raise RuntimeError("default expression must be in match expression")
            if ast.value[0].suffix != ':':
                raise RuntimeError("No ':' after default")
            ast.special = DEFAULT_LIST
            for item in ast.value[1:]:
                parse(item)
        def parse_if():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid if expression")
            ast.special = IF_LIST
            pred = ast.value[1]
            if pred.suffix != ':':
                raise RuntimeError("No ':' after if predication")
            for item in ast.value[1:]:
                parse(item)
        def parse_elif():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid elif expression")
            if ast.prev().special not in (IF_LIST, ELIF_LIST):
                raise RuntimeError("No previous if/elif expression")
            ast.special = ELIF_LIST
            pred = ast.value[1]
            if pred.suffix != ':':
                raise RuntimeError("No ':' after elif predication")
            for item in ast.value[1:]:
                parse(item)
        def parse_else():
            if len(ast.value) < 2:
                raise RuntimeError("Invalid else expression")
            if ast.value[0].suffix != ':':
                raise RuntimeError("No ':' after else")
            if ast.prev().special not in (IF_LIST, ELIF_LIST, WHILE_LIST, FOR_LIST, EACH_LIST):
                raise RuntimeError("No previous if/elif/while/for/each expression")
            ast.special = ELSE_LIST
            for item in ast.value[1:]:
                parse(item)
        def parse_while():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid while expression")
            ast.special = WHILE_LIST
            pred = ast.value[1]
            if pred.suffix != ':':
                raise RuntimeError("No ':' after while predication")
            for item in ast.value[1:]:
                parse(item)
        def parse_for():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid for expression")
            ast.special = FOR_LIST
            pred = ast.value[1]
            if pred.suffix != ':':
                raise RuntimeError("No ':' after for parameter list")
            if pred.tag != LIST_LIST:
                raise RuntimeError("Invalid for parameter list")
            if len(pred.value) not in (3, 4):
                raise RuntimeError("Invalid for parameter list")
            if pred.value[0].tag != IDENTIFIER:
                raise RuntimeError("Invalid for parameter")
            pred.addvartoscope(pred.value[0].value)
            for item in pred.value[1:]:
                parse(item)
            for item in ast.value[2:]:
                parse(item)
        def parse_each():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid each expression")
            ast.special = EACH_LIST
            pred = ast.value[1]
            if pred.suffix != ':':
                raise RuntimeError("No ':' after each parameter list")
            if pred.tag != LIST_LIST:
                raise RuntimeError("Invalid each parameter list")
            if len(pred.value) < 2:
                raise RuntimeError("Invalid each parameter list")
            for item in pred.value[:-1]:
                parse_destructure(item)
            parse(pred.value[-1])
            for item in ast.value[2:]:
                parse(item)
        def parse_break():
            ast.special = BREAK_LIST
        def parse_continue():
            ast.special = CONTINUE_LIST
        def parse_fn():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid fn expression")
            ast.special = FN_LIST
            ai = 1
            if ast.value[1].tag == IDENTIFIER:
                ast.addvartoscope(ast.value[1].value)
                ai = 2
            arglist = ast.value[ai]
            if arglist.suffix != ':':
                raise RuntimeError("No ':' after fn parameter list")
            if arglist.tag != LIST_LIST:
                raise RuntimeError("Invalid fn parameter list")
            for arg in arglist.value:
                if arg.tag != IDENTIFIER:
                    raise RuntimeError("Invalid fn argument")
                arg.addvartoscope(arg.value)
            for item in ast.value[ai+1:]:
                parse(item)
        def parse_let():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid let expression")
            ast.special = LET_LIST
            for item in ast.value[1:-1]:
                parse_destructure(item)
            parse(ast.value[-1])
        def parse_var():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid var expression")
            ast.special = VAR_LIST
            for item in ast.value[1:-1]:
                parse_destructure(item)
            parse(ast.value[-1])
        def parse_set():
            if len(ast.value) != 3:
                raise RuntimeError("Invalid set expression")
            ast.special = SET_LIST
            for item in ast.value[1:]:
                parse(item)
        def parse_import():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid import expression")
            ast.special = IMPORT_LIST
            for item in ast.value[1:-1]:
                parse_destructure(item)
            parse(ast.value[-1])
        def parse_values():
            if len(ast.value) < 2:
                raise RuntimeError("Invalid values expression")
            ast.special = VALUES_LIST
            for item in ast.value[1:]:
                parse(item)
        def parse_and():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid and expression")
            ast.special = AND_LIST
            for item in ast.value[1:]:
                parse(item)
        def parse_or():
            if len(ast.value) < 3:
                raise RuntimeError("Invalid or expression")
            ast.special = AND_LIST
            for item in ast.value[1:]:
                parse(item)
        def parse_not():
            if len(ast.value) != 2:
                raise RuntimeError("Invalid not expression")
            ast.special = NOT_LIST
            parse(ast.value[1])
        def parse_question():
            if len(ast.value) != 4:
                raise RuntimeError("Invalid ? expression")
            ast.special = QUESTION_LIST
            for item in ast.value[1:]:
                parse(item)
        def parse_try():
            raise RuntimeError("not support try")
        def parse_catch():
            raise RuntimeError("not support catch")
        def parse_finally():
            raise RuntimeError("not support finally")
        def parse_throw():
            raise RuntimeError("not support throw")

        op = ast.value[0]
        if op.tag == IDENTIFIER and op.value in specials:
                specials[op.value](ast)
        else:
            for item in ast.value:
                parse(item)


def interpret(root):
    interns = set()
    g = Frame(root)
    stack = [g]
    openupvals = {}
    none = Value(NONE)
    true = Value(TRUE)
    false = Value(FALSE)

    def error(msg):
        raise RuntimeError(msg)

    def eval(ast):
        if ast.tag == NONE:
            return none
        elif ast.tag == TRUE:
            return true
        elif ast.tag == FALSE:
            return false
        elif ast.tag in (INTEGER, FLOAT):
            return Value(ast.tag, ast.value)
        elif ast.tag in (SINGLE_STRING, DOUBLE_STRING, BACKTICK_STRING, INTERN_STRING):
            return Value(STRING, ast.value)
        elif ast.tag == VARARG:
            return Value(VARARG)
        elif ast.tag == IDENTIFIER:
            frame = stack[-1]
            if ast.value in frame.variables:
                return frame.variables[ast.value]
            
        elif ast.tag == MULTI_IDENTIFIER:
            pass
        elif ast.tag == AND_REMINDER:
            pass
        elif ast.tag == AT_WHOLE:
            pass
        elif ast.tag == CODE_LIST:
            pass
        elif ast.tag == HASH_LIST:
            pass
        elif ast.tag == LIST_LIST:
            pass
        elif ast.tag == DICT_LIST:
            pass
        else:
            error(f"invalid ast: {ast}")
    return eval(root, g)
    

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <.fry file>")
        sys.exit(1)
    with open(sys.argv[1], encoding='utf-8') as f:
        data = f.read()
    ast = lex(data)
    print()
    print(f"========== {sys.argv[1]} ==========")
    print(data)
    print("-----------------------")
    print(ast)
    print()

