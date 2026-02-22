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
    SHL = auto()
    SHR = auto()
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
    KW_ASM = auto()
    STRING = auto()
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
    'asm': TokenType.KW_ASM,
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

        # Strings
        if ch == '"':
            start = i + 1
            i += 1
            while i < len(source) and source[i] != '"':
                if source[i] == '\n':
                    line += 1
                i += 1
            if i >= len(source):
                raise LexerError(f"Line {line}: Unterminated string literal")
            val = source[start:i]
            tokens.append(Token(TokenType.STRING, val, line))
            i += 1
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
            if two == '<<':
                tokens.append(Token(TokenType.SHL, '<<', line)); i += 2; continue
            if two == '>>':
                tokens.append(Token(TokenType.SHR, '>>', line)); i += 2; continue

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

class AsmStmt(ASTNode):
    def __init__(self, asm_code):
        self.asm_code = asm_code

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
        elif tt == TokenType.KW_ASM:
            return self.parse_asm_stmt()
        elif tt == TokenType.IDENT:
            # Could be assignment or call statement
            name = self.advance()
            if self.peek().type == TokenType.ASSIGN:
                self.advance()
                expr = self.parse_expr()
                self.expect(TokenType.SEMI)
                return Assignment(name.value, expr)
            elif self.peek().type == TokenType.LPAREN:
                # Function call as a statement
                self.advance()
                args = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self.parse_expr())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expr())
                self.expect(TokenType.RPAREN)
                self.expect(TokenType.SEMI)
                return OutStmt(CallExpr(name.value, args))  # Wrap in OutStmt for now, or create a new ExprStmt
            else:
                raise ParseError(f"Line {name.line}: Expected '=' or '(' after identifier")
        else:
            # Any other expression followed by a semicolon is an expression statement
            return self.parse_expr_stmt()

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

    def parse_asm_stmt(self):
        self.expect(TokenType.KW_ASM)
        self.expect(TokenType.LPAREN)
        str_token = self.expect(TokenType.STRING)
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMI)
        return AsmStmt(str_token.value)

    def parse_expr_stmt(self):
        expr = self.parse_expr()
        self.expect(TokenType.SEMI)
        # For now, just return the expression. A dedicated ExprStmt AST node might be better.
        # If the expression has side effects (like a function call), it's valid.
        # If it doesn't, it's a no-op.
        return expr # Or a new AST node like ExpressionStatement(expr)

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
        left = self.parse_shift()
        while self.peek().type in (TokenType.AMP, TokenType.PIPE, TokenType.CARET):
            op = self.advance()
            right = self.parse_shift()
            left = BinOp(op.value, left, right)
        return left

    def parse_shift(self):
        left = self.parse_unary()
        while self.peek().type in (TokenType.SHL, TokenType.SHR):
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

        # Calling convention for Structural emulator:
        # A and B hold the return address! We must push them FIRST before doing anything else.
        self.emit(f"    PUSH A          ; save ret high")
        self.emit(f"    PUSH B          ; save ret low")

        old_func = self.current_func
        self.current_func = node.name

        # Allocate variables in RAM as usual?
        # Actually, variables could be on the stack, but the existing compiler allocates them sequentially in RAM.
        # We'll leave local variables allocated in RAM (static allocation) for simplicity,
        # but function arguments come from the stack.
        # Arguments were pushed by caller.
        # Stack structure upon entry before our push:
        # SP+0: arg N
        # ...
        # SP+(N-1): arg 1
        # Now we pushed A and B:
        # SP+0: B (ret_lo)
        # SP+1: A (ret_hi)
        # SP+2: arg N
        # ...
        # To load arg i (0-indexed, 0 is first arg): it's at offset 2 + (N - i).

        N = len(node.params)
        for i, param in enumerate(node.params):
            val_offset = 2 + (N - i)
            addr = self.alloc_var(param)
            self.emit(f"    LSA {val_offset}            ; load arg {param}")
            self.emit(f"    STA [0x{addr:04X}]    ; param {param}")

        # Compile body
        for stmt in node.body.stmts:
            self.compile_stmt(stmt)

        # Default return path (used if no return stmt is hit)
        self.emit("    POP C           ; restore ret low")
        self.emit("    POP D           ; restore ret high")
        # Pop args from caller (by discarding them? No, caller cleans up args?
        # Let's say callee doesn't clean up args, or caller cleans up.
        # Actually, a standard C calling convention has caller clean up.
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
            self.emit("    POP C           ; restore ret low")
            self.emit("    POP D           ; restore ret high")
            self.emit("    RET")

        elif isinstance(node, AsmStmt):
            # Format using self.variables, rendering addresses as 4-digit hex
            formatted_vars = {k: f"{v:04X}" for k, v in self.variables.items()}
            formatted_asm = node.asm_code
            try:
                formatted_asm = formatted_asm.format(**formatted_vars)
            except Exception as e:
                raise CompileError(f"Failed to expand variables in AsmStmt: {e}")
                
            for line in formatted_asm.split('\n'):
                self.emit(line)

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
            self.emit("    TAB             ; B = right")
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
            if node.op in ('+', '-', '&', '|', '^', '<<', '>>'):
                self.compile_expr(node.left)
                self.emit("    PUSH A          ; save left")
                self.compile_expr(node.right)
                self.emit("    TAB             ; B = right")
                self.emit("    POP A           ; A = left")

                if node.op == '<<':
                    self.emit("    SHL")  # Note: Right operand isn't effectively used by SHL in 1 CPU cycle, but structurally works
                elif node.op == '>>':
                    self.emit("    SHR")
                else:
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

        # Evaluate arguments left-to-right (or right-to-left, doesn't matter for C but left-to-right is fine)
        # We push each evaluated argument onto the stack.
        for arg in node.args:
            self.compile_expr(arg)
            self.emit("    PUSH A          ; push arg")

        label = self.functions[node.name]
        self.emit(f"    CAL {label}")
        
        # Caller cleans up stack: SP += len(node.args)
        # We don't have ADD SP, imm. 
        # But wait, does structural emulator SP have ADD? No. SP is 193 counters.
        # We must POP into A or B and discard!
        # Actually POP A / POP B will do SP++.
        if len(node.args) > 0:
            self.emit(f"    ; caller cleans up stack ({len(node.args)} args)")
            # Wait, popping into A or B will clobber the function's return value (which is in A)!
            # So if we want to preserve A (the return value), we can only POP into B, or push A then pop discard then pop A.
            # But we can just POP B! (Unless >1 args, then we just POP B repeatedly).
            # We have POP B.
            self.emit("    PUSH A          ; temporarily save return val")
            for _ in range(len(node.args)):
                self.emit("    POP B           ; discard arg")
            self.emit("    POP A           ; restore return val")


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
