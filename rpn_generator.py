# rpn_generator.py
# Побудова ПОЛІЗ (Польського інверсного запису) за алгоритмом Дейкстри
# Варіант 15

PRIORITIES = {
    "(": 0,
    ")": 1,
    ":=": 2,
    "<": 3,
    ">": 3,
    "<=": 3,
    ">=": 3,
    "!=": 3,
    "==": 3,
    "+": 4,
    "-": 4,
    "*": 5,
    "/": 5,
}


class RPNGenerator:

    def __init__(self, tokens_table):
        self.tokens = tokens_table
        self.pos = 0
        self.n = len(tokens_table)

        self.stack = []         
        self.output = []       
        self.steps = []         
        self.label_counter = 0

    def _new_label(self):
        self.label_counter += 1
        return f"m{self.label_counter}"

    def _cur(self):
        if self.pos < self.n:
            return self.tokens[self.pos]
        return None

    def _advance(self):
        tok = self._cur()
        if tok is not None:
            self.pos += 1
        return tok

    def _fmt_stack(self):
        if not self.stack:
            return "порожній"
        parts = []
        for item in self.stack:
            if isinstance(item, dict):
                kind = item.get("kind", "")
                if kind == "if":
                    parts.append(f"if({item['m_end']})")
                elif kind == "for":
                    m_cond = item.get("m_cond", "?")
                    m_end = item.get("m_end", "?")
                    step_info = f", by {item['by_tokens'][0]}" if item.get("by_tokens") else ""
                    parts.append(f"for({m_cond}, {m_end}{step_info})")
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return ", ".join(parts)

    def _fmt_output(self):
        return " ".join(self.output) if self.output else "(порожньо)"

    def _record_step(self, token_str):
        step_num = len(self.steps) + 1
        self.steps.append((
            step_num,
            token_str,
            self._fmt_stack(),
            self._fmt_output(),
        ))

    def _pop_operators_while(self, predicate):
        while self.stack:
            top = self.stack[-1]
            if isinstance(top, dict):
                break
            if predicate(top):
                self.stack.pop()
                self.output.append(top)
            else:
                break

    def _push_operator(self, op):
        op_prio = PRIORITIES[op]
        self._pop_operators_while(
            lambda top: top in PRIORITIES and top != "(" and PRIORITIES[top] >= op_prio
        )
        self.stack.append(op)

    def _handle_paren_close(self):
        while self.stack:
            top = self.stack[-1]
            if isinstance(top, dict):
                break
            self.stack.pop()
            if top == "(":
                break
            self.output.append(top)

    def _pop_enclosing(self, kind):
        for idx in range(len(self.stack) - 1, -1, -1):
            item = self.stack[idx]
            if isinstance(item, dict) and item.get("kind") == kind:
                return self.stack.pop(idx)
        return None

    def _collect_until_keywords(self, stop_lexemes):
        expr_tokens = []
        while self._cur() is not None:
            _, lex, _, _ = self._cur()
            if lex in stop_lexemes:
                break
            expr_tokens.append(self._advance())
        return expr_tokens

    def _tokens_to_rpn_list(self, expr_tokens):
        local_stack = []
        res = []

        for _, lex, _, _ in expr_tokens:
            if lex == ",":
                while local_stack and local_stack[-1] != "(":
                    res.append(local_stack.pop())
                continue

            if lex == "(":
                local_stack.append("(")
            elif lex == ")":
                while local_stack and local_stack[-1] != "(":
                    res.append(local_stack.pop())
                if local_stack and local_stack[-1] == "(":
                    local_stack.pop()
            elif lex in PRIORITIES:
                prio = PRIORITIES[lex]
                while local_stack:
                    top = local_stack[-1]
                    if top != "(" and top in PRIORITIES and PRIORITIES[top] >= prio:
                        res.append(local_stack.pop())
                    else:
                        break
                local_stack.append(lex)
            else:
                res.append(lex)

        while local_stack:
            top = local_stack.pop()
            if top != "(":
                res.append(top)

        return res

    def generate(self):
        self.stack = []
        self.output = []
        self.steps = []
        self.label_counter = 0

        # Пропускаємо заголовок та блок оголошень var ... begin
        while self._cur() is not None:
            _, lex, _, _ = self._cur()
            if lex == "begin":
                self._advance()
                break
            self._advance()

        while self._cur() is not None:
            tok = self._cur()
            line, lex, code, idx_val = tok
            tok_disp = f"{lex} (р.{line})"

            # Кінець програми
            if lex == "end.":
                self._advance()
                self._pop_operators_while(
                    lambda top: top in PRIORITIES and top not in ("(", ")")
                )
                self._record_step(tok_disp)
                break

            # Обробка read(...) та write(...)
            if lex in ("read", "write"):
                cmd = lex
                self._advance()
                args = []
                if self._cur() is not None and self._cur()[1] == "(":
                    self._advance()  # '('
                    while self._cur() is not None and self._cur()[1] != ")":
                        arg_tok = self._advance()
                        if arg_tok[1] != ",":
                            args.append(arg_tok[1])
                            self.output.append(arg_tok[1])
                    if self._cur() is not None and self._cur()[1] == ")":
                        self._advance()  # ')'
                self.output.append(cmd)
                args_str = ", ".join(args)
                self._record_step(f"{cmd}({args_str})")
                continue

            # Обробка умовного оператора: if <відношення> { <сп.опер.> }
            if lex == "if":
                self._advance()
                m_end = self._new_label()
                self.stack.append({"kind": "if", "m_end": m_end})
                self._record_step(tok_disp)

                cond_tokens = self._collect_until_keywords({"{", "end."})
                cond_rpn = self._tokens_to_rpn_list(cond_tokens)
                self.output.extend(cond_rpn)
                self.output.extend([m_end, "УПХ"])
                self._record_step("<відношення> перед '{'")

                if self._cur() is not None and self._cur()[1] == "{":
                    brace_tok = self._advance()
                    self._record_step(f"{brace_tok[1]} (р.{brace_tok[0]})")
                continue

            # Кінець тіла умовного оператора '}'
            if lex == "}":
                self._advance()
                if_ctx = self._pop_enclosing("if")
                m_end = if_ctx["m_end"] if if_ctx else self._new_label()
                self._pop_operators_while(
                    lambda top: top in PRIORITIES and top not in ("(", ")")
                )
                self.output.append(f"{m_end}:")
                self._record_step(tok_disp)
                continue

            # Обробка циклу: 
            if lex == "for":
                self._advance()
                m_cond = self._new_label()
                m_end = self._new_label()

                id_tok = self._advance()
                loop_var = id_tok[1] if id_tok else "i"

                if self._cur() is not None and self._cur()[1] == "=":
                    self._advance()

                init_tokens = self._collect_until_keywords({"to", "by", "while", "rof", "end."})
                init_rpn = self._tokens_to_rpn_list(init_tokens)
                self.output.extend([loop_var, *init_rpn, "=", f"{m_cond}:"])

                ctx = {
                    "kind": "for",
                    "var": loop_var,
                    "m_cond": m_cond,
                    "m_end": m_end,
                    "by_tokens": None,
                }
                self.stack.append(ctx)
                self._record_step(f"for {loop_var} = {' '.join(init_rpn)}")

                if self._cur() is not None and self._cur()[1] == "to":
                    self._advance()
                    bound_tokens = self._collect_until_keywords({"by", "while", "rof", "end."})
                    bound_rpn = self._tokens_to_rpn_list(bound_tokens)
                    self.output.extend([loop_var, *bound_rpn, "<=", m_end, "УПХ"])
                    self._record_step(f"to {' '.join(bound_rpn)}")

                if self._cur() is not None and self._cur()[1] == "by":
                    self._advance()
                    by_tokens = self._collect_until_keywords({"while", "rof", "end."})
                    by_rpn = self._tokens_to_rpn_list(by_tokens)
                    ctx["by_tokens"] = by_rpn if by_rpn else ["1"]
                    self._record_step(f"by {' '.join(by_rpn)}")

                if self._cur() is not None and self._cur()[1] == "while":
                    self._advance()
                    cond_tokens = []
                    paren_depth = 0
                    started_paren = False
                    while self._cur() is not None:
                        c_tok = self._cur()
                        c_lex = c_tok[1]
                        if c_lex == "(":
                            started_paren = True
                            paren_depth += 1
                            cond_tokens.append(self._advance())
                        elif c_lex == ")":
                            paren_depth -= 1
                            cond_tokens.append(self._advance())
                            if started_paren and paren_depth <= 0:
                                break
                        else:
                            if started_paren and paren_depth <= 0:
                                break
                            if c_lex in ("rof", "end.", ";", "{", "}"):
                                break
                            cond_tokens.append(self._advance())

                    if cond_tokens and cond_tokens[0][1] == "(" and cond_tokens[-1][1] == ")":
                        inner_tokens = cond_tokens[1:-1]
                    else:
                        inner_tokens = [t for t in cond_tokens if t[1] not in ("(", ")")]

                    rel_rpn = self._tokens_to_rpn_list(inner_tokens)
                    self.output.extend([*rel_rpn, m_end, "УПХ"])
                    self._record_step(f"while ({' '.join(rel_rpn)})")

                continue

            # Завершення циклу 'rof'
            if lex == "rof":
                self._advance()
                self._pop_operators_while(
                    lambda top: top in PRIORITIES and top not in ("(", ")")
                )
                for_ctx = self._pop_enclosing("for")
                if for_ctx:
                    var_name = for_ctx["var"]
                    m_cond = for_ctx["m_cond"]
                    m_end = for_ctx["m_end"]
                    step_tokens = for_ctx.get("by_tokens") or ["1"]

                    self.output.extend([var_name, var_name, *step_tokens, "+", "="])
                    self.output.extend([m_cond, "БП"])
                    self.output.append(f"{m_end}:")

                self._record_step(tok_disp)
                continue

            # Роздільник операторів ';'
            if lex == ";":
                self._advance()
                self._pop_operators_while(
                    lambda top: top in PRIORITIES and top not in ("(", ")")
                )
                self._record_step(tok_disp)
                continue

            # Закриваюча дужка ')'
            if lex == ")":
                self._advance()
                self._handle_paren_close()
                self._record_step(tok_disp)
                continue

            # Оператори з таблиці пріоритетів
            if lex in PRIORITIES:
                self._advance()
                if lex == "(":
                    self.stack.append("(")
                else:
                    self._push_operator(lex)
                self._record_step(tok_disp)
                continue

            # Ідентифікатор або константа
            self._advance()
            self.output.append(lex)
            self._record_step(tok_disp)

        self._pop_operators_while(
            lambda top: top in PRIORITIES and top not in ("(", ")")
        )

        return self._fmt_output()