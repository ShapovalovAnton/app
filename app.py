import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from parser import SyntaxAnalyzer

from rpn_generator import RPNGenerator

NONECODE = 0
ACCEPTCODE = 1
ERRORCODE = -1

KEYWORDS = {
    "program": 1,
    "var": 2,
    "begin": 3,
    "end.": 4,
    "integer": 5,
    "real": 6,
    "read": 7,
    "write": 8,
    "for": 9,
    "to": 10,
    "by": 11,
    "while": 12,
    "rof": 13,
    "if": 14
}

SINGLE_OPS = {
    ";": 18,
    ",": 19,
    "+": 20,
    "-": 21,
    "*": 22,
    "/": 23,
    "(": 24,
    ")": 25,
    "{": 26,
    "}": 27
}

ID_CODE = 34
CONST_CODE = 35


class LexicalAnalyzer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.n = len(text)
        self.tokens_table = []
        self.idn_table = []
        self.con_table = []
        self.errors = []

    def next_char(self):
        if self.pos < self.n:
            ch = self.text[self.pos]
            self.pos += 1
            if ch == '\n':
                self.line += 1
            return ch
        return None

    def ret_pos(self):
        if self.pos > 0:
            self.pos -= 1
            if self.text[self.pos] == '\n':
                self.line -= 1

    def skip_whitespace(self):
        while self.pos < self.n:
            ch = self.text[self.pos]
            if ch in (' ', '\t', '\r', '\n'):
                if ch == '\n':
                    self.line += 1
                self.pos += 1
            else:
                break

    def add_lex(self, lexeme, code, line_num):
        idx_val = "-"
        if code == ID_CODE:
            if lexeme in KEYWORDS:
                code = KEYWORDS[lexeme]
            else:
                if lexeme not in self.idn_table:
                    self.idn_table.append(lexeme)
                idx_val = self.idn_table.index(lexeme) + 1
        elif code == CONST_CODE:
            if lexeme not in self.con_table:
                self.con_table.append(lexeme)
            idx_val = self.con_table.index(lexeme) + 1

        self.tokens_table.append((line_num, lexeme, code, idx_val))

    def step_get_token(self):
        self.skip_whitespace()
        if self.pos >= self.n:
            return False

        state = 1
        result = NONECODE
        s = ""
        token_line = self.line

        while result == NONECODE:
            match state:
                case 1:
                    c = self.next_char()
                    if c is None:
                        break
                    s += c

                    if c.isalpha():
                        state = 2
                    elif c.isdigit():
                        state = 3
                    elif c == '.':
                        state = 5
                    elif c == ':':
                        state = 6
                    elif c == '=':
                        state = 7
                    elif c == '!':
                        state = 8
                    elif c == '>':
                        state = 9
                    elif c == '<':
                        state = 10
                    elif c in SINGLE_OPS:
                        self.add_lex(c, SINGLE_OPS[c], token_line)
                        result = ACCEPTCODE
                    else:
                        self.errors.append(f"Рядок {token_line}: Неприпустимий символ '{c}'")
                        result = ERRORCODE

                case 2:
                    c = self.next_char()
                    if c is not None and (c.isalnum()):
                        s += c
                        state = 2
                    elif c == '.' and s == "end":
                        s += c
                        self.add_lex(s, KEYWORDS["end."], token_line)
                        result = ACCEPTCODE
                    else:
                        if c is not None:
                            self.ret_pos()
                        self.add_lex(s, ID_CODE, token_line)
                        result = ACCEPTCODE

                case 3:
                    c = self.next_char()
                    if c is not None and c.isdigit():
                        s += c
                        state = 3
                    elif c == '.':
                        s += c
                        state = 4
                    else:
                        if c is not None:
                            self.ret_pos()
                        self.add_lex(s, CONST_CODE, token_line)
                        result = ACCEPTCODE

                case 4:
                    c = self.next_char()
                    if c is not None and c.isdigit():
                        s += c
                        state = 4
                    else:
                        if c is not None:
                            self.ret_pos()
                        self.add_lex(s, CONST_CODE, token_line)
                        result = ACCEPTCODE

                case 5:
                    c = self.next_char()
                    if c is not None and c.isdigit():
                        s += c
                        state = 4
                    else:
                        if c is not None:
                            self.ret_pos()
                        self.errors.append(f"Рядок {token_line}: Неприпустимий символ після '.' або незавершене число")
                        result = ERRORCODE

                case 6:
                    c = self.next_char()
                    if c == '=':
                        self.add_lex(":=", 15, token_line)
                    else:
                        if c is not None:
                            self.ret_pos()
                        self.add_lex(":", 17, token_line)
                    result = ACCEPTCODE

                case 7:
                    c = self.next_char()
                    if c == '=':
                        self.add_lex("==", 28, token_line)
                    else:
                        if c is not None:
                            self.ret_pos()
                        self.add_lex("=", 16, token_line)
                    result = ACCEPTCODE

                case 8:
                    c = self.next_char()
                    if c == '=':
                        self.add_lex("!=", 29, token_line)
                        result = ACCEPTCODE
                    else:
                        if c is not None:
                            self.ret_pos()
                        self.errors.append(f"Рядок {token_line}: Очікувалось '=' після '!' (знайдено '{c}')")
                        result = ERRORCODE

                case 9:
                    c = self.next_char()
                    if c == '=':
                        self.add_lex(">=", 33, token_line)
                    else:
                        if c is not None:
                            self.ret_pos()
                        self.add_lex(">", 32, token_line)
                    result = ACCEPTCODE

                case 10:
                    c = self.next_char()
                    if c == '=':
                        self.add_lex("<=", 31, token_line)
                    else:
                        if c is not None:
                            self.ret_pos()
                        self.add_lex("<", 30, token_line)
                    result = ACCEPTCODE

        return True

    def run(self):
        while self.step_get_token():
            pass


# ГРАФІЧНИЙ ІНТЕРФЕЙС
class CompilerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лексичний, синтаксичний аналізатор (МПА) та побудова ПОЛІЗ — Лаб №4 (Варіант 15)")
        self.root.geometry("1260x740")

        self.parser_steps = []
        self.current_step_idx = -1

        self.rpn_steps = []
        self.current_rpn_idx = -1
        self.poliz_result_str = ""

        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Ліва частина: редактор
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        lbl_input = ttk.Label(left_frame, text="Текст програми (навчальна мова):", font=("Segoe UI", 10, "bold"))
        lbl_input.pack(anchor=tk.W, pady=2)

        self.txt_source = tk.Text(left_frame, wrap=tk.NONE, font=("Consolas", 11), undo=True)
        self.txt_source.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=6)

        btn_load = ttk.Button(btn_frame, text="Відкрити файл...", command=self.load_file)
        btn_load.pack(side=tk.LEFT, padx=3)

        btn_run = ttk.Button(btn_frame, text="▶ Запустити аналіз (Сканер + Парсер + ПОЛІЗ)", command=self.run_analysis)
        btn_run.pack(side=tk.RIGHT, padx=3)

        # Права частина: вкладки з результатами
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Вкладка 1: Покроковий режим МПА (Лаб 3)
        tab_parser = ttk.Frame(self.notebook)
        self.notebook.add(tab_parser, text="Покроковий розбір МПА")

        # Панель керування покроковим переглядом МПА
        step_ctrl_frame = ttk.Frame(tab_parser)
        step_ctrl_frame.pack(fill=tk.X, padx=4, pady=4)

        self.btn_first_step = ttk.Button(step_ctrl_frame, text="⏮ На початок", command=self.step_first, state=tk.DISABLED)
        self.btn_first_step.pack(side=tk.LEFT, padx=2)

        self.btn_prev_step = ttk.Button(step_ctrl_frame, text="◀ Попередній крок", command=self.step_prev, state=tk.DISABLED)
        self.btn_prev_step.pack(side=tk.LEFT, padx=2)

        self.btn_next_step = ttk.Button(step_ctrl_frame, text="Наступний крок ▶", command=self.step_next, state=tk.DISABLED)
        self.btn_next_step.pack(side=tk.LEFT, padx=2)

        self.btn_all_steps = ttk.Button(step_ctrl_frame, text="⏭ Показати всі", command=self.step_show_all, state=tk.DISABLED)
        self.btn_all_steps.pack(side=tk.LEFT, padx=2)

        self.lbl_step_status = ttk.Label(step_ctrl_frame, text="Крок: 0 / 0", font=("Segoe UI", 9, "bold"))
        self.lbl_step_status.pack(side=tk.RIGHT, padx=6)

        # Інформаційна картка поточного стану МПА
        info_frame = ttk.LabelFrame(tab_parser, text="Поточна конфігурація МПА")
        info_frame.pack(fill=tk.X, padx=4, pady=(0, 4))

        self.lbl_cur_token = ttk.Label(info_frame, text="Поточна лексема: —", font=("Consolas", 10))
        self.lbl_cur_token.pack(anchor=tk.W, padx=6, pady=1)

        self.lbl_cur_state = ttk.Label(info_frame, text="Стан автомата: —", font=("Consolas", 10))
        self.lbl_cur_state.pack(anchor=tk.W, padx=6, pady=1)

        self.lbl_cur_stack = ttk.Label(info_frame, text="Вміст стека: —", font=("Consolas", 10))
        self.lbl_cur_stack.pack(anchor=tk.W, padx=6, pady=1)

        # Таблиця кроків розбору МПА
        self.tree_steps = ttk.Treeview(
            tab_parser,
            columns=("step", "line", "token", "state", "stack", "action"),
            show="headings"
        )
        self.tree_steps.heading("step", text="Крок")
        self.tree_steps.heading("line", text="Рядок")
        self.tree_steps.heading("token", text="Поточна лексема")
        self.tree_steps.heading("state", text="Стан")
        self.tree_steps.heading("stack", text="Вміст стека")
        self.tree_steps.heading("action", text="Дія МПА")

        self.tree_steps.column("step", width=50, anchor=tk.CENTER)
        self.tree_steps.column("line", width=50, anchor=tk.CENTER)
        self.tree_steps.column("token", width=130)
        self.tree_steps.column("state", width=60, anchor=tk.CENTER)
        self.tree_steps.column("stack", width=120, anchor=tk.CENTER)
        self.tree_steps.column("action", width=230)
        self.tree_steps.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # Вкладка 2: Побудова ПОЛІЗ (Лаб 4)
        tab_poliz = ttk.Frame(self.notebook)
        self.notebook.add(tab_poliz, text="ПОЛІЗ (покроково)")

        rpn_ctrl_frame = ttk.Frame(tab_poliz)
        rpn_ctrl_frame.pack(fill=tk.X, padx=4, pady=4)

        self.btn_rpn_first = ttk.Button(rpn_ctrl_frame, text="⏮ На початок", command=self.rpn_step_first, state=tk.DISABLED)
        self.btn_rpn_first.pack(side=tk.LEFT, padx=2)

        self.btn_rpn_prev = ttk.Button(rpn_ctrl_frame, text="◀ Попередній крок", command=self.rpn_step_prev, state=tk.DISABLED)
        self.btn_rpn_prev.pack(side=tk.LEFT, padx=2)

        self.btn_rpn_next = ttk.Button(rpn_ctrl_frame, text="Наступний крок ▶", command=self.rpn_step_next, state=tk.DISABLED)
        self.btn_rpn_next.pack(side=tk.LEFT, padx=2)

        self.btn_rpn_all = ttk.Button(rpn_ctrl_frame, text="⏭ Показати всі", command=self.rpn_step_show_all, state=tk.DISABLED)
        self.btn_rpn_all.pack(side=tk.LEFT, padx=2)

        self.lbl_rpn_status = ttk.Label(rpn_ctrl_frame, text="Крок: 0 / 0", font=("Segoe UI", 9, "bold"))
        self.lbl_rpn_status.pack(side=tk.RIGHT, padx=6)

        rpn_info_frame = ttk.LabelFrame(tab_poliz, text="Результат побудови ПОЛІЗ")
        rpn_info_frame.pack(fill=tk.X, padx=4, pady=(0, 4))

        self.lbl_poliz_result = ttk.Label(
            rpn_info_frame,
            text="Підсумковий ПОЛІЗ: —",
            font=("Consolas", 10, "bold"),
            wraplength=760,
            justify=tk.LEFT
        )
        self.lbl_poliz_result.pack(anchor=tk.W, padx=6, pady=3)

        self.lbl_rpn_cur_token = ttk.Label(rpn_info_frame, text="Вхідна лексема: —", font=("Consolas", 10))
        self.lbl_rpn_cur_token.pack(anchor=tk.W, padx=6, pady=1)

        self.lbl_rpn_cur_stack = ttk.Label(rpn_info_frame, text="Стек операторів / міток: —", font=("Consolas", 10))
        self.lbl_rpn_cur_stack.pack(anchor=tk.W, padx=6, pady=1)

        self.lbl_rpn_cur_out = ttk.Label(
            rpn_info_frame,
            text="Поточний вихідний рядок ПОЛІЗ: —",
            font=("Consolas", 10),
            wraplength=760,
            justify=tk.LEFT
        )
        self.lbl_rpn_cur_out.pack(anchor=tk.W, padx=6, pady=(1, 3))

        self.tree_poliz = ttk.Treeview(
            tab_poliz,
            columns=("step", "token", "stack", "poliz"),
            show="headings"
        )
        self.tree_poliz.heading("step", text="Крок")
        self.tree_poliz.heading("token", text="Вхідна лексема")
        self.tree_poliz.heading("stack", text="Стек")
        self.tree_poliz.heading("poliz", text="Вихідний рядок ПОЛІЗ")

        self.tree_poliz.column("step", width=60, anchor=tk.CENTER)
        self.tree_poliz.column("token", width=160)
        self.tree_poliz.column("stack", width=190)
        self.tree_poliz.column("poliz", width=360)
        self.tree_poliz.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # Вкладка 3: Вихідна таблиця лексем
        tab_tokens = ttk.Frame(self.notebook)
        self.notebook.add(tab_tokens, text="Вихідна таблиця лексем")
        self.tree_tokens = ttk.Treeview(tab_tokens, columns=("line", "lexeme", "code", "index"), show="headings")
        self.tree_tokens.heading("line", text="Рядок")
        self.tree_tokens.heading("lexeme", text="Лексема")
        self.tree_tokens.heading("code", text="Код")
        self.tree_tokens.heading("index", text="Індекс IDN/CON")
        self.tree_tokens.column("line", width=60, anchor=tk.CENTER)
        self.tree_tokens.column("lexeme", width=120)
        self.tree_tokens.column("code", width=60, anchor=tk.CENTER)
        self.tree_tokens.column("index", width=110, anchor=tk.CENTER)
        self.tree_tokens.pack(fill=tk.BOTH, expand=True)

        # Вкладка 4: Таблиця IDN
        tab_idn = ttk.Frame(self.notebook)
        self.notebook.add(tab_idn, text="Таблиця IDN")
        self.tree_idn = ttk.Treeview(tab_idn, columns=("index", "name"), show="headings")
        self.tree_idn.heading("index", text="Індекс")
        self.tree_idn.heading("name", text="Ідентифікатор")
        self.tree_idn.column("index", width=60, anchor=tk.CENTER)
        self.tree_idn.pack(fill=tk.BOTH, expand=True)

        # Вкладка 5: Таблиця CON
        tab_con = ttk.Frame(self.notebook)
        self.notebook.add(tab_con, text="Таблиця CON")
        self.tree_con = ttk.Treeview(tab_con, columns=("index", "value"), show="headings")
        self.tree_con.heading("index", text="Індекс")
        self.tree_con.heading("value", text="Константа")
        self.tree_con.column("index", width=60, anchor=tk.CENTER)
        self.tree_con.pack(fill=tk.BOTH, expand=True)

        # Нижня частина: консоль повідомлень та помилок
        bottom_frame = ttk.Frame(root)
        bottom_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        lbl_log = ttk.Label(bottom_frame, text="Консоль повідомлень та помилок:", font=("Segoe UI", 9, "bold"))
        lbl_log.pack(anchor=tk.W)

        self.txt_log = tk.Text(bottom_frame, height=5, font=("Consolas", 10))
        self.txt_log.tag_configure("error", foreground="red")
        self.txt_log.tag_configure("success", foreground="green")
        self.txt_log.pack(fill=tk.X)

        self._set_default_program()

    def _set_default_program(self):
        sample_code = (
            "program myprog\n"
            "var a, b : real;\n"
            "    i : integer\n"
            "begin\n"
            "  read(a, b);\n"
            "  for i = 1 to 10 by 2 while (a <= b)\n"
            "    a := a + 3.14\n"
            "  rof;\n"
            "  if a != b {\n"
            "    write(a)\n"
            "  }\n"
            "end.\n"
        )
        self.txt_source.insert("1.0", sample_code)

    def load_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            with open(filename, "r", encoding="utf-8") as f:
                self.txt_source.delete("1.0", tk.END)
                self.txt_source.insert("1.0", f.read())

    def _update_step_view(self):
        for row in self.tree_steps.get_children():
            self.tree_steps.delete(row)

        total = len(self.parser_steps)
        if total == 0 or self.current_step_idx < 0:
            self.lbl_step_status.config(text=f"Крок: 0 / {total}")
            self.lbl_cur_token.config(text="Поточна лексема: —")
            self.lbl_cur_state.config(text="Стан автомата: —")
            self.lbl_cur_stack.config(text="Вміст стека: —")
            self.btn_first_step.config(state=tk.DISABLED)
            self.btn_prev_step.config(state=tk.DISABLED)
            self.btn_next_step.config(state=tk.DISABLED)
            self.btn_all_steps.config(state=tk.DISABLED)
            return

        last_item = None
        for i in range(self.current_step_idx + 1):
            last_item = self.tree_steps.insert("", tk.END, values=self.parser_steps[i])

        if last_item:
            self.tree_steps.selection_set(last_item)
            self.tree_steps.see(last_item)

        step_num, line_num, token_disp, state, stack_str, action = self.parser_steps[self.current_step_idx]
        self.lbl_step_status.config(text=f"Крок: {step_num} / {total}")
        self.lbl_cur_token.config(text=f"Поточна лексема: {token_disp}  (рядок {line_num})")
        self.lbl_cur_state.config(text=f"Стан автомата:   {state}")
        self.lbl_cur_stack.config(text=f"Вміст стека:     {stack_str}")

        self.btn_first_step.config(state=tk.NORMAL if self.current_step_idx > 0 else tk.DISABLED)
        self.btn_prev_step.config(state=tk.NORMAL if self.current_step_idx > 0 else tk.DISABLED)
        self.btn_next_step.config(state=tk.NORMAL if self.current_step_idx < total - 1 else tk.DISABLED)
        self.btn_all_steps.config(state=tk.NORMAL if self.current_step_idx < total - 1 else tk.DISABLED)

    def _update_rpn_view(self):
        for row in self.tree_poliz.get_children():
            self.tree_poliz.delete(row)

        total = len(self.rpn_steps)
        if total == 0 or self.current_rpn_idx < 0:
            self.lbl_rpn_status.config(text=f"Крок: 0 / {total}")
            self.lbl_poliz_result.config(text="Підсумковий ПОЛІЗ: —")
            self.lbl_rpn_cur_token.config(text="Вхідна лексема: —")
            self.lbl_rpn_cur_stack.config(text="Стек операторів / міток: —")
            self.lbl_rpn_cur_out.config(text="Поточний вихідний рядок ПОЛІЗ: —")
            self.btn_rpn_first.config(state=tk.DISABLED)
            self.btn_rpn_prev.config(state=tk.DISABLED)
            self.btn_rpn_next.config(state=tk.DISABLED)
            self.btn_rpn_all.config(state=tk.DISABLED)
            return

        self.lbl_poliz_result.config(text=f"Підсумковий ПОЛІЗ: {self.poliz_result_str}")

        last_item = None
        for i in range(self.current_rpn_idx + 1):
            last_item = self.tree_poliz.insert("", tk.END, values=self.rpn_steps[i])

        if last_item:
            self.tree_poliz.selection_set(last_item)
            self.tree_poliz.see(last_item)

        step_num, token_str, stack_str, poliz_str = self.rpn_steps[self.current_rpn_idx]
        self.lbl_rpn_status.config(text=f"Крок: {step_num} / {total}")
        self.lbl_rpn_cur_token.config(text=f"Вхідна лексема:              {token_str}")
        self.lbl_rpn_cur_stack.config(text=f"Стек операторів / міток:     {stack_str}")
        self.lbl_rpn_cur_out.config(text=f"Поточний вихідний рядок ПОЛІЗ: {poliz_str}")

        self.btn_rpn_first.config(state=tk.NORMAL if self.current_rpn_idx > 0 else tk.DISABLED)
        self.btn_rpn_prev.config(state=tk.NORMAL if self.current_rpn_idx > 0 else tk.DISABLED)
        self.btn_rpn_next.config(state=tk.NORMAL if self.current_rpn_idx < total - 1 else tk.DISABLED)
        self.btn_rpn_all.config(state=tk.NORMAL if self.current_rpn_idx < total - 1 else tk.DISABLED)

    def step_first(self):
        if self.parser_steps:
            self.current_step_idx = 0
            self._update_step_view()

    def step_prev(self):
        if self.current_step_idx > 0:
            self.current_step_idx -= 1
            self._update_step_view()

    def step_next(self):
        if self.current_step_idx < len(self.parser_steps) - 1:
            self.current_step_idx += 1
            self._update_step_view()

    def step_show_all(self):
        if self.parser_steps:
            self.current_step_idx = len(self.parser_steps) - 1
            self._update_step_view()

    def rpn_step_first(self):
        if self.rpn_steps:
            self.current_rpn_idx = 0
            self._update_rpn_view()

    def rpn_step_prev(self):
        if self.current_rpn_idx > 0:
            self.current_rpn_idx -= 1
            self._update_rpn_view()

    def rpn_step_next(self):
        if self.current_rpn_idx < len(self.rpn_steps) - 1:
            self.current_rpn_idx += 1
            self._update_rpn_view()

    def rpn_step_show_all(self):
        if self.rpn_steps:
            self.current_rpn_idx = len(self.rpn_steps) - 1
            self._update_rpn_view()

    def run_analysis(self):
        for tree in (self.tree_tokens, self.tree_idn, self.tree_con, self.tree_steps, self.tree_poliz):
            for row in tree.get_children():
                tree.delete(row)
        self.txt_log.delete("1.0", tk.END)
        self.parser_steps = []
        self.current_step_idx = -1
        self.rpn_steps = []
        self.current_rpn_idx = -1
        self.poliz_result_str = ""

        # 1. Етап лексичного аналізу
        source = self.txt_source.get("1.0", tk.END)
        scanner = LexicalAnalyzer(source)
        scanner.run()

        for row in scanner.tokens_table:
            self.tree_tokens.insert("", tk.END, values=row)

        for idx, name in enumerate(scanner.idn_table, start=1):
            self.tree_idn.insert("", tk.END, values=(idx, name))

        for idx, val in enumerate(scanner.con_table, start=1):
            self.tree_con.insert("", tk.END, values=(idx, val))

        if scanner.errors:
            for err in scanner.errors:
                self.txt_log.insert(tk.END, "[Лексична помилка] " + err + "\n", "error")
            self._update_step_view()
            self._update_rpn_view()
            messagebox.showwarning("Помилка", f"Лексичний аналіз зупинено через помилки ({len(scanner.errors)}).")
            return

        self.txt_log.insert(tk.END, "1. Лексичний аналіз виконано успішно. Помилок не виявлено.\n", "success")

        # 2. Етап синтаксичного аналізу (МПА)
        parser = SyntaxAnalyzer(scanner.tokens_table)
        is_valid = parser.parse()

        self.parser_steps = parser.steps
        if self.parser_steps:
            self.current_step_idx = len(self.parser_steps) - 1
        self._update_step_view()

        if is_valid:
            self.txt_log.insert(
                tk.END,
                f"2. Синтаксичний аналіз (МПА) виконано успішно за {len(parser.steps)} кроків. Програма синтаксично правильна.\n",
                "success"
            )

            # 3. Етап побудови ПОЛІЗ (запускається лише після успішного парсингу)
            rpn_gen = RPNGenerator(scanner.tokens_table)
            self.poliz_result_str = rpn_gen.generate()
            self.rpn_steps = rpn_gen.steps
            if self.rpn_steps:
                self.current_rpn_idx = len(self.rpn_steps) - 1
            self._update_rpn_view()

            self.txt_log.insert(
                tk.END,
                f"3. Побудову ПОЛІЗ виконано за {len(self.rpn_steps)} кроків: {self.poliz_result_str}\n",
                "success"
            )
            self.notebook.select(1)  # Перемикаємо на вкладку ПОЛІЗ
        else:
            self._update_rpn_view()
            for err in parser.errors:
                self.txt_log.insert(tk.END, "[Синтаксична помилка] " + err + "\n", "error")
            self.notebook.select(0)
            messagebox.showerror("Синтаксична помилка", parser.errors[0])


if __name__ == "__main__":
    app_root = tk.Tk()
    app = CompilerApp(app_root)
    app_root.mainloop()
