ID_CODE = 34
CONST_CODE = 35

# Таблиця переходів МПА:
# state -> {
#     "transitions": { мітка_лексеми: (наступний_стан, push_у_стек_або_None) },
#     "eps": (наступний_стан_або_"EXIT", push_або_None, pop_зі_стека_True/False, чи_зсувати_лексему_True/False),
#     "expected": "текстовий опис очікуваних лексем для повідомлення про помилку"
# }
MPA_TABLE = {
    # --- Головний МПА <програма> (Схема 1) ---
    1: {
        "transitions": {"program": (2, None)},
        "expected": "ключове слово 'program'"
    },
    2: {
        "transitions": {"id": (3, None)},
        "expected": "ідентифікатор (назва програми)"
    },
    3: {
        "transitions": {"var": (4, None)},
        "expected": "ключове слово 'var'"
    },
    4: {
        "transitions": {"id": (5, None)},
        "expected": "ідентифікатор змінної"
    },
    5: {
        "transitions": {
            ",": (4, None),
            ":": (6, None)
        },
        "expected": "',' або ':'"
    },
    6: {
        "transitions": {
            "integer": (7, None),
            "real": (7, None)
        },
        "expected": "тип даних ('integer' або 'real')"
    },
    7: {
        "transitions": {
            ";": (4, None),
            "begin": (51, 8)
        },
        "expected": "';' або ключове слово 'begin'"
    },
    8: {
        "transitions": {
            ";": (51, 8),
            "end.": ("ACCEPT", None)
        },
        "expected": "';' або 'end.'"
    },

    # Підавтомат <опер.> (Схема 2)
    51: {
        "transitions": {
            "id": (52, None),
            "read": (54, None),
            "write": (54, None),
            "if": (71, 57),
            "for": (59, None)
        },
        "expected": "початок оператора (ідентифікатор, 'read', 'write', 'if' або 'for')"
    },
    52: {
        "transitions": {":=": (81, 53)},
        "expected": "оператор присвоєння ':='"
    },
    53: {
        "transitions": {},
        "eps": ("POP", None, True, False),
        "expected": ""
    },
    54: {
        "transitions": {"(": (55, None)},
        "expected": "відкриваючу дужку '('"
    },
    55: {
        "transitions": {"id": (56, None)},
        "expected": "ідентифікатор змінної"
    },
    56: {
        "transitions": {
            ",": (55, None),
            ")": ("POP", None)
        },
        "expected": "',' або закриваючу дужку ')'"
    },
    57: {
        "transitions": {"{": (51, 58)},
        "expected": "відкриваючу фігурну дужку '{'"
    },
    58: {
        "transitions": {
            ";": (51, 58),
            "}": ("POP", None)
        },
        "expected": "';' або закриваючу фігурну дужку '}'"
    },
    59: {
        "transitions": {"id": (60, None)},
        "expected": "ідентифікатор параметра циклу"
    },
    60: {
        "transitions": {"=": (81, 61)},
        "expected": "знак '=' у заголовку циклу 'for'"
    },
    61: {
        "transitions": {"to": (81, 62)},
        "expected": "ключове слово 'to'"
    },
    62: {
        "transitions": {"by": (81, 63)},
        "expected": "ключове слово 'by'"
    },
    63: {
        "transitions": {"while": (64, None)},
        "expected": "ключове слово 'while'"
    },
    64: {
        "transitions": {"(": (71, 65)},
        "expected": "відкриваючу дужку '(' після 'while'"
    },
    65: {
        "transitions": {")": (51, 66)},
        "expected": "закриваючу дужку ')' після умови 'while'"
    },
    66: {
        "transitions": {
            ";": (51, 66),
            "rof": ("POP", None)
        },
        "expected": "';' або ключове слово 'rof'"
    },

    # Підавтомат <відношення> 
    71: {
        "transitions": {},
        "eps": (81, 72, False, False),
        "expected": ""
    },
    72: {
        "transitions": {
            "==": (81, 73),
            "!=": (81, 73),
            "<": (81, 73),
            "<=": (81, 73),
            ">": (81, 73),
            ">=": (81, 73)
        },
        "expected": "знак порівняння ('==', '!=', '<', '<=', '>', '>=')"
    },
    73: {
        "transitions": {},
        "eps": ("POP", None, True, False),
        "expected": ""
    },

    # Підавтомат <вираз> (Схема 4)
    81: {
        "transitions": {
            "id": (83, None),
            "const": (83, None),
            "(": (81, 82)
        },
        "expected": "ідентифікатор, константу або '('"
    },
    82: {
        "transitions": {")": (83, None)},
        "expected": "закриваючу дужку ')'"
    },
    83: {
        "transitions": {
            "+": (81, None),
            "-": (81, None),
            "*": (81, None),
            "/": (81, None)
        },
        "eps": ("POP", None, True, False),
        "expected": ""
    }
}


class SyntaxAnalyzer:
    def __init__(self, tokens_table):
        self.tokens = tokens_table
        self.pos = 0
        self.state = 1
        self.stack = []
        self.steps = []       
        self.errors = []
        self.success = False

    def _get_token_label(self, token):
        _, lexeme, code, _ = token
        if code == ID_CODE:
            return "id"
        if code == CONST_CODE:
            return "const"
        return lexeme

    def _format_stack(self):
        return "[" + ", ".join(str(s) for s in self.stack) + "]" if self.stack else "порожній"

    def parse(self):
        if not self.tokens:
            self.errors.append("Рядок 1: Порожній вхідний файл. Очікувалась програма.")
            return False

        step_num = 1
        max_steps = 10000 

        while step_num <= max_steps:
            has_token = self.pos < len(self.tokens)
            if has_token:
                line_num, lexeme, code, _ = self.tokens[self.pos]
                label = self._get_token_label(self.tokens[self.pos])
                token_display = f"{lexeme} ({label})" if label in ("id", "const") else lexeme
            else:
                line_num = self.tokens[-1][0]
                lexeme = "<EOF>"
                label = "<EOF>"
                token_display = "<кінець файлу>"

            state_info = MPA_TABLE.get(self.state)
            if not state_info:
                self.errors.append(f"Рядок {line_num}: Внутрішня помилка автомата (невідомий стан {self.state}).")
                return False

            transitions = state_info.get("transitions", {})
            eps_rule = state_info.get("eps")
            stack_before = self._format_stack()
            current_state = self.state

            # Перевірка переходу по поточній лексемі [=]
            if has_token and label in transitions:
                next_state, push_val = transitions[label]
                action_desc = f"[=] Зчитано '{lexeme}'"

                if push_val is not None:
                    self.stack.append(push_val)
                    action_desc += f", стек ↓{push_val}"

                if next_state == "ACCEPT":
                    self.steps.append((step_num, line_num, token_display, current_state, stack_before, "[=] Успішний вихід (програма коректна)"))
                    if self.pos + 1 < len(self.tokens):
                        extra_line, extra_lex, _, _ = self.tokens[self.pos + 1]
                        self.errors.append(f"Рядок {extra_line}: Неочікуваний текст '{extra_lex}' після 'end.'.")
                        return False
                    self.success = True
                    return True

                elif next_state == "POP":
                    if not self.stack:
                        self.errors.append(f"Рядок {line_num}: Помилка повернення зі стека у стані {current_state}.")
                        return False
                    ret_state = self.stack.pop()
                    action_desc += f", вихід з п/а ↑{ret_state}"
                    self.state = ret_state
                else:
                    self.state = next_state

                self.steps.append((step_num, line_num, token_display, current_state, stack_before, action_desc))
                self.pos += 1
                step_num += 1

            # Перевірка переходу по [≠] (¢)
            elif eps_rule is not None:
                next_state, push_val, do_pop, advance_token = eps_rule
                action_desc = "[≠] Перехід без зчитування лексеми"

                if push_val is not None:
                    self.stack.append(push_val)
                    action_desc += f", стек ↓{push_val}"

                if do_pop:
                    if not self.stack:
                        self.errors.append(f"Рядок {line_num}: Помилка стека (стек порожній при виході зі стану {current_state}).")
                        return False
                    ret_state = self.stack.pop()
                    action_desc = f"[≠] Вихід з п/а ↑{ret_state}"
                    self.state = ret_state
                else:
                    self.state = next_state

                self.steps.append((step_num, line_num, token_display, current_state, stack_before, action_desc))
                if advance_token and has_token:
                    self.pos += 1
                step_num += 1

            # Синтаксична помилка [≠] помилка
            else:
                expected_msg = state_info.get("expected", "іншу конструкцію")
                found_msg = f"'{lexeme}'" if has_token else "кінець файлу"
                err_text = f"Рядок {line_num} (стан {current_state}): Синтаксична помилка — очікувалось {expected_msg}, але знайдено {found_msg}."
                self.steps.append((step_num, line_num, token_display, current_state, stack_before, "[≠] ПОМИЛКА"))
                self.errors.append(err_text)
                return False

        return False