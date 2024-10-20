import re
from typing import List, Tuple

class FileProcessor:
    def process(self, instructions: str) -> Tuple[List[str], List[Tuple[str, int]], List[Tuple[str, int]]]:
        instructions = self._remove_multiline_comments(instructions)
        lines = instructions.split('\n')
        return self._separate_sections(lines)
    
    def _remove_multiline_comments(self, text: str) -> str:
        return re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    def _remove_inline_comments(self, line: str) -> str:
        return re.split(r'\s*//\s*', line)[0].strip()

    def _separate_sections(self, lines: List[str]) -> Tuple[List[str], List[Tuple[str, int]], List[Tuple[str, int]]]:
        cleaned_instructions = []
        data_lines = []
        code_lines = []
        current_section = None

        for line_number, line in enumerate(lines, 1):
            line = self._remove_inline_comments(line).strip()
            if not line:
                continue

            if line in ['DATA:', 'CODE:']:
                if line == 'DATA:' and current_section == 'CODE':
                    raise SyntaxError(f"Línea {line_number}: Sección DATA después de CODE")
                current_section = 'DATA' if line == 'DATA:' else 'CODE'
                cleaned_instructions.append(line)
            elif current_section == 'DATA':
                data_lines.append((line, line_number))
                cleaned_instructions.append(line)
            elif current_section == 'CODE':
                code_lines.append((line, line_number))
                cleaned_instructions.append(line)
            else:
                raise SyntaxError(f"Línea {line_number}: Instrucción fuera de las secciones DATA o CODE")

        if not code_lines:
            raise SyntaxError("Falta la sección CODE en el archivo")

        return cleaned_instructions, data_lines, code_lines