#!/usr/bin/env python3
"""
MiniC compiler for the breadboard CPU.

Compiles a simple C-like language to assembly for the breadboard CPU.

Language features:
  - Variables: var x = 5;
  - Arithmetic: +, -, &, |, ^, ~
  - Comparison: ==, !=, <, >, <=, >=
  - Control flow: if/else, while
  - Functions: fun name() { ... }, return expr;
  - Built-in: out(expr), in()

Example:
  var a = 5;
  var b = 10;
  var c = a + b;
  if (c > 10) {
      out(c);
  }

Usage:
  python compiler.py input.mc [-o output.asm]
"""

import sys
import os
import re
from enum import Enum, auto

# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

class TokenType(Enum):
    NUM = auto()
    IDENT = auto()
    PLUS = auto()
    MINUS = auto()
    AMP = auto()
    PIPE = auto()
    CARET = auto()
    TILDE = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    ASSIGN = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    SEMI = auto()
    COMMA = auto()
    KW_VAR = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_FUN = auto()
    KW_RETURN = auto()
    KW_OUT = auto()
    KW_IN = auto()
    EOF = auto()


KEYWORDS = {
    'var': TokenType.KW_VAR,
    'if': TokenType.KW_IF,
    'else': TokenType.KW_ELSE,
    'while': TokenType.KW_WHILE,
    'fun': TokenType.KW_FUN,
    'return': TokenType.KW_RETURN,
    'out': TokenType.KW_OUT,
    'in': TokenType.KW_IN,
}


class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"


class LexerError(Exception):
    pass


def tokenize(source):
    """Tokenize MiniC source code."""
    tokens = []
    i = 0
    line = 1

    while i < len(source):
        ch = source[i]

        # Whitespace
        if ch in ' \t\r':
            i += 1
            continue

        if ch == '\n':
            line += 1
            i += 1
            continue

        # Comments
        if ch == '/' and i + 1 < len(source) and source[i + 1] == '/':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue

        # Numbers
        if ch.isdigit():
            start = i
            if ch == '0' and i + 1 < len(source) and source[i + 1] in 'xX':
                i += 2
                while i < len(source) and source[i] in '0123456789abcdefABCDEF':
                    i += 1
            else:
                while i < len(source) and source[i].isdigit():
                    i += 1
            tokens.append(Token(TokenType.NUM, int(source[start:i], 0), line))
            continue

        # Identifiers / keywords
        if ch.isalpha() or ch == '_':
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == '_'):
                i += 1
            word = source[start:i]
            tt = KEYWORDS.get(word, TokenType.IDENT)
            tokens.append(Token(tt, word, line))
            continue

        # Two-character operators
        if i + 1 < len(source):
            two = source[i:i + 2]
            if two == '==':
                tokens.append(Token(TokenType.EQ, '==', line)); i += 2; continue
            if two == '!=':
                tokens.append(Token(TokenType.NEQ, '!=', line)); i += 2; continue
            if two == '<=':
                tokens.append(Token(TokenType.LTE, '<=', line)); i += 2; continue
            if two == '>=':
                tokens.append(Token(TokenType.GTE, '>=', line)); i += 2; continue

        # Single-character operators
        single = {
            '+': TokenType.PLUS, '-': TokenType.MINUS,
            '&': TokenType.AMP, '|': TokenType.PIPE,
            '^': TokenType.CARET, '~': TokenType.TILDE,
            '<': TokenType.LT, '>': TokenType.GT,
            '=': TokenType.ASSIGN,
            '(': TokenType.LPAREN, ')': TokenType.RPAREN,
            '{': TokenType.LBRACE, '}': TokenType.RBRACE,
            ';': TokenType.SEMI, ',': TokenType.COMMA,
        }
        if ch in single:
            tokens.append(Token(single[ch], ch, line))
            i += 1
            continue

        raise LexerError(f"Line {line}: Unknown character: {ch!r}")

    tokens.append(Token(TokenType.EOF, None, line))
    return tokens


# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------

class ASTNode:
    pass

class NumLiteral(ASTNode):
    def __init__(self, value):
        self.value = value & 0xFF

class VarRef(ASTNode):
    def __init__(self, name):
        self.name = name

class UnaryOp(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

class BinOp(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class InExpr(ASTNode):
    pass

class VarDecl(ASTNode):
    def __init__(self, name, init_expr):
        self.name = name
        self.init_expr = init_expr

class Assignment(ASTNode):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr

class OutStmt(ASTNode):
    def __init__(self, expr):
        self.expr = expr

class IfStmt(ASTNode):
    def __init__(self, cond, then_body, else_body=None):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

class WhileStmt(ASTNode):
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

class FunDecl(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class CallExpr(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ReturnStmt(ASTNode):
    def __init__(self, expr):
        self.expr = expr

class Block(ASTNode):
    def __init__(self, stmts):
        self.stmts = stmts


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, tt):
        t = self.advance()
        if t.type != tt:
            raise ParseError(f"Line {t.line}: Expected {tt}, got {t.type} ({t.value!r})")
        return t

    def match(self, tt):
        if self.peek().type == tt:
            return self.advance()
        return None

    def parse_program(self):
        stmts = []
        while self.peek().type != TokenType.EOF:
            stmts.append(self.parse_top_level())
        return Block(stmts)

    def parse_top_level(self):
        if self.peek().type == TokenType.KW_FUN:
            return self.parse_fun_decl()
        return self.parse_statement()

    def parse_fun_decl(self):
        self.expect(TokenType.KW_FUN)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LPAREN)
        params = []
        if self.peek().type != TokenType.RPAREN:
            params.append(self.expect(TokenType.IDENT).value)
            while self.match(TokenType.COMMA):
                params.append(self.expect(TokenType.IDENT).value)
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        return FunDecl(name, params, body)

    def parse_block(self):
        self.expect(TokenType.LBRACE)
        stmts = []
        while self.peek().type != TokenType.RBRACE:
            stmts.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        return Block(stmts)

    def parse_statement(self):
        tt = self.peek().type

        if tt == TokenType.KW_VAR:
            return self.parse_var_decl()
        elif tt == TokenType.KW_IF:
            return self.parse_if()
        elif tt == TokenType.KW_WHILE:
            return self.parse_while()
        elif tt == TokenType.KW_RETURN:
            return self.parse_return()
        elif tt == TokenType.KW_OUT:
            return self.parse_out()
        elif tt == TokenType.IDENT:
            # Could be assignment or call statement
            name = self.advance()
            if self.peek().type == TokenType.ASSIGN:
                self.advance()
                expr = self.parse_expr()
                self.expect(TokenType.SEMI)
                return Assignment(name.value, expr)
            elif self.peek().type == TokenType.LPAREN:
                self.advance()
                args = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self.parse_expr())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                self.expect(TokenType.SEMI)
                return OutStmt(CallExpr(name.value, args))  # Expression statement
            else:
                raise ParseError(f"Line {name.line}: Expected '=' or '(' after identifier")
        else:
            raise ParseError(f"Line {self.peek().line}: Unexpected token {tt}")

    def parse_var_decl(self):
        self.expect(TokenType.KW_VAR)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.ASSIGN)
        expr = self.parse_expr()
        self.expect(TokenType.SEMI)
        return VarDecl(name, expr)

    def parse_if(self):
        self.expect(TokenType.KW_IF)
        self.expect(TokenType.LPAREN)
        cond = self.parse_expr()
        self.expect(TokenType.RPAREN)
        then_body = self.parse_block()
        else_body = None
        if self.match(TokenType.KW_ELSE):
            if self.peek().type == TokenType.KW_IF:
                else_body = Block([self.parse_if()])
            else:
                else_body = self.parse_block()
        return IfStmt(cond, then_body, else_body)

    def parse_while(self):
        self.expect(TokenType.KW_WHILE)
        self.expect(TokenType.LPAREN)
        cond = self.parse_expr()
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        return WhileStmt(cond, body)

    def parse_return(self):
        self.expect(TokenType.KW_RETURN)
        expr = None
        if self.peek().type != TokenType.SEMI:
            expr = self.parse_expr()
        self.expect(TokenType.SEMI)
        return ReturnStmt(expr)

    def parse_out(self):
        self.expect(TokenType.KW_OUT)
        self.expect(TokenType.LPAREN)
        expr = self.parse_expr()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMI)
        return OutStmt(expr)

    # Expression parsing with precedence climbing
    def parse_expr(self):
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_additive()
        while self.peek().type in (TokenType.EQ, TokenType.NEQ, TokenType.LT,
                                    TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self.advance()
            right = self.parse_additive()
            left = BinOp(op.value, left, right)
        return left

    def parse_additive(self):
        left = self.parse_bitwise()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance()
            right = self.parse_bitwise()
            left = BinOp(op.value, left, right)
        return left

    def parse_bitwise(self):
        left = self.parse_unary()
        while self.peek().type in (TokenType.AMP, TokenType.PIPE, TokenType.CARET):
            op = self.advance()
            right = self.parse_unary()
            left = BinOp(op.value, left, right)
        return left

    def parse_unary(self):
        if self.peek().type == TokenType.TILDE:
            op = self.advance()
            operand = self.parse_primary()
            return UnaryOp('~', operand)
        if self.peek().type == TokenType.MINUS:
            op = self.advance()
            operand = self.parse_primary()
            # -x = 0 - x
            return BinOp('-', NumLiteral(0), operand)
        return self.parse_primary()

    def parse_primary(self):
        t = self.peek()

        if t.type == TokenType.NUM:
            self.advance()
            return NumLiteral(t.value)

        if t.type == TokenType.KW_IN:
            self.advance()
            self.expect(TokenType.LPAREN)
            self.expect(TokenType.RPAREN)
            return InExpr()

        if t.type == TokenType.IDENT:
            self.advance()
            if self.peek().type == TokenType.LPAREN:
                # Function call expression
                self.advance()
                args = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self.parse_expr())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                return CallExpr(t.value, args)
            return VarRef(t.value)

        if t.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return expr

        raise ParseError(f"Line {t.line}: Unexpected token {t.type} ({t.value!r})")


# ---------------------------------------------------------------------------
# Code generator
# ---------------------------------------------------------------------------

class CompileError(Exception):
    pass


class Compiler:
    """Generates assembly from AST."""

    def __init__(self):
        self.asm_lines = []
        self.variables = {}       # name -> RAM address
        self.next_var_addr = 0x8000 # Next available RAM address
        self.label_counter = 0
        self.functions = {}       # name -> label
        self.current_func = None

    def new_label(self, prefix="L"):
        self.label_counter += 1
        return f"__{prefix}_{self.label_counter}"

    def emit(self, line):
        self.asm_lines.append(line)

    def emit_label(self, label):
        self.asm_lines.append(f"{label}:")

    def alloc_var(self, name):
        if name in self.variables:
            raise CompileError(f"Variable '{name}' already declared")
        addr = self.next_var_addr
        if addr > 0xFFFF:
            raise CompileError("Out of variable RAM")
        self.variables[name] = addr
        self.next_var_addr += 1
        return addr

    def var_addr(self, name):
        if name not in self.variables:
            raise CompileError(f"Undefined variable: {name}")
        return self.variables[name]

    def compile(self, ast):
        """Compile an AST program to assembly source."""
        self.emit("; Generated by MiniC compiler")
        self.emit(".org 0x0000")
        self.emit("")

        # First pass: collect function declarations
        main_stmts = []
        for stmt in ast.stmts:
            if isinstance(stmt, FunDecl):
                self.functions[stmt.name] = f"__fn_{stmt.name}"
            else:
                main_stmts.append(stmt)

        # Emit main code (non-function statements)
        self.emit("; --- main ---")
        for stmt in main_stmts:
            self.compile_stmt(stmt)
        self.emit("    HLT")
        self.emit("")

        # Emit function code
        for stmt in ast.stmts:
            if isinstance(stmt, FunDecl):
                self.compile_fun(stmt)

        return "\n".join(self.asm_lines) + "\n"

    def compile_fun(self, node):
        self.emit(f"; --- function {node.name} ---")
        label = self.functions[node.name]
        self.emit_label(label)

        # Save old variable scope for params
        old_func = self.current_func
        self.current_func = node.name

        # Calling convention: first arg in A, extra args in __arg1, __arg2, etc.
        if len(node.params) > 0:
            # First param comes in A register
            addr = self.alloc_var(node.params[0])
            self.emit(f"    STA [0x{addr:04X}]    ; param {node.params[0]}")

        if len(node.params) > 1:
            # Extra params were stored by caller in __arg slots
            for i, p in enumerate(node.params[1:]):
                arg_name = f"__arg{i+1}"
                if arg_name not in self.variables:
                    self.alloc_var(arg_name)
                src_addr = self.var_addr(arg_name)
                addr = self.alloc_var(p)
                self.emit(f"    LDA [0x{src_addr:04X}]    ; load arg {p}")
                self.emit(f"    STA [0x{addr:04X}]    ; param {p}")

        # Compile body
        for stmt in node.body.stmts:
            self.compile_stmt(stmt)

        # Default return
        self.emit("    RET")
        self.emit("")
        self.current_func = old_func

    def compile_stmt(self, node):
        if isinstance(node, VarDecl):
            addr = self.alloc_var(node.name)
            self.compile_expr(node.init_expr)  # Result in A
            self.emit(f"    STA [0x{addr:04X}]    ; {node.name}")

        elif isinstance(node, Assignment):
            addr = self.var_addr(node.name)
            self.compile_expr(node.expr)  # Result in A
            self.emit(f"    STA [0x{addr:04X}]    ; {node.name}")

        elif isinstance(node, OutStmt):
            if isinstance(node.expr, CallExpr) and node.expr.name in self.functions:
                self.compile_call(node.expr)
            else:
                self.compile_expr(node.expr)
                self.emit("    OUT")

        elif isinstance(node, IfStmt):
            self.compile_if(node)

        elif isinstance(node, WhileStmt):
            self.compile_while(node)

        elif isinstance(node, ReturnStmt):
            if node.expr:
                self.compile_expr(node.expr)
            self.emit("    RET")

        elif isinstance(node, Block):
            for s in node.stmts:
                self.compile_stmt(s)

        else:
            raise CompileError(f"Unknown statement type: {type(node).__name__}")

    def compile_if(self, node):
        else_label = self.new_label("else")
        end_label = self.new_label("endif")

        self.compile_condition(node.cond, else_label)

        # Then body
        for stmt in node.then_body.stmts:
            self.compile_stmt(stmt)

        if node.else_body:
            self.emit(f"    JMP {end_label}")

        self.emit_label(else_label)

        if node.else_body:
            for stmt in node.else_body.stmts:
                self.compile_stmt(stmt)
            self.emit_label(end_label)

    def compile_while(self, node):
        loop_label = self.new_label("while")
        end_label = self.new_label("endwhile")

        self.emit_label(loop_label)
        self.compile_condition(node.cond, end_label)

        for stmt in node.body.stmts:
            self.compile_stmt(stmt)

        self.emit(f"    JMP {loop_label}")
        self.emit_label(end_label)

    def compile_condition(self, node, false_label):
        """
        Compile a condition expression and emit a conditional jump
        to false_label if the condition is false.
        """
        if isinstance(node, BinOp) and node.op in ('==', '!=', '<', '>', '<=', '>='):
            # Compile both sides, then compare
            self.compile_expr(node.left)
            self.emit("    PSA             ; save left")
            self.compile_expr(node.right)
            self.emit("    MVB             ; B = right")
            self.emit("    PPA             ; A = left")
            self.emit("    CMP             ; flags = A - B")

            # Emit conditional jump based on operator
            if node.op == '==':
                self.emit(f"    JNZ {false_label}")
            elif node.op == '!=':
                self.emit(f"    JZ {false_label}")
            elif node.op == '<':
                # A < B  iff  A-B has carry (borrow)
                self.emit(f"    JNC {false_label}")
                # Also need to check not-equal (for <= vs <)
                # Actually C flag is set when A < B (borrow), so JNC skips if A >= B
            elif node.op == '>':
                # A > B  iff  A-B has no carry AND not zero
                self.emit(f"    JC {false_label}")   # if A < B, skip
                self.emit(f"    JZ {false_label}")   # if A == B, skip
            elif node.op == '<=':
                # A <= B  iff  carry OR zero
                lbl_ok = self.new_label("le_ok")
                self.emit(f"    JC {lbl_ok}")
                self.emit(f"    JZ {lbl_ok}")
                self.emit(f"    JMP {false_label}")
                self.emit_label(lbl_ok)
            elif node.op == '>=':
                # A >= B  iff  no carry
                self.emit(f"    JC {false_label}")
        else:
            # General expression: treat as boolean (non-zero = true)
            self.compile_expr(node)
            self.emit("    CMI #0")
            self.emit(f"    JZ {false_label}")

    def compile_expr(self, node):
        """Compile an expression. Result ends up in A register."""
        if isinstance(node, NumLiteral):
            self.emit(f"    LDA #{node.value}")

        elif isinstance(node, VarRef):
            addr = self.var_addr(node.name)
            self.emit(f"    LDA [0x{addr:04X}]    ; {node.name}")

        elif isinstance(node, InExpr):
            self.emit("    IN")

        elif isinstance(node, UnaryOp):
            if node.op == '~':
                self.compile_expr(node.operand)
                self.emit("    NOT")

        elif isinstance(node, BinOp):
            # Compile left into A, push, compile right into A,
            # move to B, pop left into A, then operate.
            if node.op in ('+', '-', '&', '|', '^'):
                self.compile_expr(node.left)
                self.emit("    PSA             ; save left")
                self.compile_expr(node.right)
                self.emit("    MVB             ; B = right")
                self.emit("    PPA             ; A = left")

                op_map = {
                    '+': 'ADD', '-': 'SUB',
                    '&': 'AND', '|': 'OR', '^': 'XOR',
                }
                self.emit(f"    {op_map[node.op]}")

            elif node.op in ('==', '!=', '<', '>', '<=', '>='):
                # Comparison as expression: return 1 if true, 0 if false
                true_label = self.new_label("cmp_true")
                end_label = self.new_label("cmp_end")
                false_label = self.new_label("cmp_false")

                self.compile_condition(node, false_label)
                self.emit(f"    LDA #1")
                self.emit(f"    JMP {end_label}")
                self.emit_label(false_label)
                self.emit(f"    LDA #0")
                self.emit_label(end_label)

        elif isinstance(node, CallExpr):
            self.compile_call(node)

        else:
            raise CompileError(f"Unknown expression type: {type(node).__name__}")

    def compile_call(self, node):
        """Compile a function call. Result in A."""
        if node.name not in self.functions:
            raise CompileError(f"Undefined function: {node.name}")

        # Store extra args to __arg slots (avoids stack/return-address conflicts)
        if len(node.args) > 1:
            for i, arg in enumerate(node.args[1:]):
                self.compile_expr(arg)
                arg_name = f"__arg{i+1}"
                if arg_name not in self.variables:
                    self.alloc_var(arg_name)
                addr = self.var_addr(arg_name)
                self.emit(f"    STA [0x{addr:04X}]    ; pass arg {i+1}")

        # First arg in A
        if node.args:
            self.compile_expr(node.args[0])

        label = self.functions[node.name]
        self.emit(f"    CAL {label}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def compile_file(filename):
    """Compile a MiniC file and return assembly source."""
    with open(filename, 'r') as f:
        source = f.read()

    tokens = tokenize(source)
    parser = Parser(tokens)
    ast = parser.parse_program()
    compiler = Compiler()
    asm = compiler.compile(ast)
    return asm


def main():
    if len(sys.argv) < 2:
        print("Usage: python compiler.py input.mc [-o output.asm]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = None

    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".asm"

    asm = compile_file(input_file)

    with open(output_file, 'w') as f:
        f.write(asm)

    print(f"Compiled {input_file} -> {output_file}")
    print(f"Assembly output:")
    print(asm)


if __name__ == "__main__":
    main()
