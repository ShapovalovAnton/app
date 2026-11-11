import tkinter as tk
from tkinter import ttk, messagebox, filedialog

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
        # Масиви для зберігання даних таюлиць 
        self.tokens_table = []
        self.idn_table = []
        self.con_table = []
        self.errors = []

# Зчитування наступного символу
    def next_char(self):
        if self.pos < self.n:
            ch = self.text[self.pos]
            self.pos += 1
            if ch == '\n':
                self.line += 1
            return ch
        return None
# Повернення до попереднього символу
    def ret_pos(self):
        if self.pos > 0:
            self.pos -= 1
            if self.text[self.pos] == '\n':
                self.line -= 1
# Ігнорування незначущих роздільників
    def skip_whitespace(self):
        while self.pos < self.n:
            ch = self.text[self.pos]
            if ch in (' ', '\t', '\r', '\n'):
                if ch == '\n':
                    self.line += 1
                self.pos += 1
            else:
                break
# Додає лексему в таблиці
    def add_lex(self, lexeme, code, line_num):
        idx_val = "-"
        if code == ID_CODE:
            # Обробка зарезервованих слів (блок j=0)
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

                    # Гілка на ідентифікатори та службові слова
                    if c.isalpha():
                        state = 2
                    # Гілка на цілі числа
                    elif c.isdigit():
                        state = 3
                    # Гілка на дробові числа без цілої частини (.5)
                    elif c == '.':
                        state = 5
                    # Гілка на оператор присвоєння або двокрапку
                    elif c == ':':
                        state = 6
                    # Гілка на перевірку рівності '==' або '='
                    elif c == '=':
                        state = 7
                    # Гілка на нерівність '!=' 
                    elif c == '!':
                        state = 8
                    # Гілка на більше або більше-рівне ('>', '>=')
                    elif c == '>':
                        state = 9
                    # Гілка на менше або менше-рівне ('<', '<=')
                    elif c == '<':
                        state = 10
                    # Односимвольні роздільники та операції
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


#ГРВФІЧНИЙ ІНТЕРФЕЙС
class CompilerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лексичний аналізатор — Лабораторна робота №2 (Варіант 15)")
        self.root.geometry("1100x680")

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

        btn_run = ttk.Button(btn_frame, text="▶ Запустити сканер", command=self.run_scanner)
        btn_run.pack(side=tk.RIGHT, padx=3)

        # Таблиці результатів
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        tab_tokens = ttk.Frame(notebook)
        notebook.add(tab_tokens, text="Вихідна таблиця лексем")
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

        tab_idn = ttk.Frame(notebook)
        notebook.add(tab_idn, text="Таблиця IDN")
        self.tree_idn = ttk.Treeview(tab_idn, columns=("index", "name"), show="headings")
        self.tree_idn.heading("index", text="Індекс")
        self.tree_idn.heading("name", text="Ідентифікатор")
        self.tree_idn.column("index", width=60, anchor=tk.CENTER)
        self.tree_idn.pack(fill=tk.BOTH, expand=True)

        tab_con = ttk.Frame(notebook)
        notebook.add(tab_con, text="Таблиця CON")
        self.tree_con = ttk.Treeview(tab_con, columns=("index", "value"), show="headings")
        self.tree_con.heading("index", text="Індекс")
        self.tree_con.heading("value", text="Константа")
        self.tree_con.column("index", width=60, anchor=tk.CENTER)
        self.tree_con.pack(fill=tk.BOTH, expand=True)

        # Нижня частина: консоль повідомлень та помилок
        bottom_frame = ttk.Frame(root)
        bottom_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        lbl_log = ttk.Label(bottom_frame, text="Консоль помилок:", font=("Segoe UI", 9, "bold"))
        lbl_log.pack(anchor=tk.W)

        self.txt_log = tk.Text(bottom_frame, height=5, font=("Consolas", 10), foreground="red")
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
            "    a := a + 3.14;\n"
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

    def run_scanner(self):
        for tree in (self.tree_tokens, self.tree_idn, self.tree_con):
            for row in tree.get_children():
                tree.delete(row)
        self.txt_log.delete("1.0", tk.END)

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
                self.txt_log.insert(tk.END, err + "\n")
            messagebox.showwarning("Помилка", f"Знайдено помилок: {len(scanner.errors)}. Перевірте консоль.")
        else:
            self.txt_log.insert(tk.END, "Лексичний аналіз виконано успішно. Помилок не виявлено.\n")


if __name__ == "__main__":
    app_root = tk.Tk()
    app = CompilerApp(app_root)
    app_root.mainloop()