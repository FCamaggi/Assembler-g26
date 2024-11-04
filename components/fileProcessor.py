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

    def _clean_instruction(self, instruction: str) -> str:
        """Limpia una instrucción eliminando espacios extra y normalizando la sintaxis."""
        # Eliminar espacios al inicio y final
        instruction = instruction.strip()
        
        # Reemplazar múltiples espacios con uno solo
        instruction = ' '.join(instruction.split())
        
        # Normalizar espacios después de comas
        instruction = re.sub(r'\s*,\s*', ', ', instruction)
        
        # Normalizar espacios dentro de paréntesis
        instruction = re.sub(r'\(\s+', '(', instruction)
        instruction = re.sub(r'\s+\)', ')', instruction)
        
        # Asegurar que hay espacio entre instrucción y operandos
        instruction = re.sub(r'^(\w+)([,(])', r'\1 \2', instruction)
        
        # Manejar casos especiales de INC/DEC
        if instruction.startswith(('INC', 'DEC')):
            instruction = re.sub(r'^(INC|DEC)\(', r'\1 (', instruction)
        
        return instruction

    def _separate_sections(self, lines: List[str]) -> Tuple[List[str], List[Tuple[str, int]], List[Tuple[str, int]]]:
        cleaned_instructions = []
        data_lines = []
        code_lines = []
        current_section = None
        current_array_definition = False
        
        for line_number, line in enumerate(lines, 1):
            line = self._remove_inline_comments(line).strip()
            if not line:
                continue

            if line in ['DATA:', 'CODE:']:
                if line == 'DATA:' and current_section == 'CODE':
                    raise SyntaxError(f"Línea {line_number}: Sección DATA después de CODE")
                current_section = 'DATA' if line == 'DATA:' else 'CODE'
                current_array_definition = False
                cleaned_instructions.append(line)
            elif current_section == 'DATA':
                parts = line.split(None, 1)
                if len(parts) == 2:  # Nueva variable o inicio de array
                    current_array_definition = True
                elif current_array_definition and len(parts) == 1:
                    pass
                else:
                    current_array_definition = False
                data_lines.append((line, line_number))
            elif current_section == 'CODE':
                current_array_definition = False
                cleaned_line = self._clean_instruction(line)
                if cleaned_line:
                    code_lines.append((cleaned_line, line_number))
                    cleaned_instructions.append(cleaned_line)
            else:
                raise SyntaxError(f"Línea {line_number}: Instrucción fuera de las secciones DATA o CODE")

        if not code_lines:
            raise SyntaxError("Falta la sección CODE en el archivo")

        return cleaned_instructions, data_lines, code_lines