import os
import sys
import glob
import re
from typing import List, Dict, Tuple, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.assembler import Assembler
from components.configuration import Configuration
from utils.exceptions import AssemblerError
import json

class AssemblerTester:
    def __init__(self, setup_file: str = 'utils/setup.json'):
        setup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), setup_file)
        with open(setup_path, 'r') as f:
            self.setup = json.load(f)
        self.config = Configuration(self.setup)
        self.assembler = Assembler(self.setup, verbose=False)

    def extract_labels(self, content: str) -> Dict[int, str]:
        """
        Extrae las etiquetas y sus líneas correspondientes del código.
        Retorna un diccionario {número_línea: nombre_etiqueta}
        """
        labels = {}
        current_line = 0
        in_code_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line == 'CODE:':
                in_code_section = True
                continue
                
            if in_code_section:
                if line.endswith(':') and not line.startswith('DATA'):
                    label_name = line[:-1].strip()
                    labels[current_line] = label_name
                else:
                    if not self.is_section_marker(line):
                        current_line += 1
        
        return labels

    def extract_variables(self, content: str) -> Dict[str, int]:
        """
        Extrae las variables y sus valores del código.
        Retorna un diccionario {nombre_variable: valor}
        """
        variables = {}
        in_data_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line == 'DATA:':
                in_data_section = True
                continue
                
            if in_data_section:
                parts = line.split()
                if len(parts) == 3:
                    var_name = parts[0]
                    var_value = int(parts[2], 16)
                    variables[var_name] = var_value
        
        return variables

    def get_label_at_line(self, labels: Dict[int, str], line_number: int) -> Optional[str]:
        """Obtiene la etiqueta en una línea específica."""
        return labels.get(line_number)

    def is_section_marker(self, line: str) -> bool:
        """Verifica si una línea es un marcador de sección (CODE: o DATA:)."""
        return line.strip() in ['CODE:', 'DATA:']

    def normalize_instruction(self, instruction: str) -> str:
        """Normaliza una instrucción para comparación."""
        # Eliminar comentarios
        instruction = re.split(r'\s*//.*', instruction)[0].strip()
        
        # Si es un marcador de sección o etiqueta, ignorarlo
        if self.is_section_marker(instruction) or instruction.endswith(':'):
            return None
            
        # Normalizar números hexadecimales y binarios
        def normalize_number(match):
            value = match.group(1)
            if value.endswith('h'):
                return str(int(value[:-1], 16))
            elif value.endswith('b'):
                return str(int(value[:-1], 2))
            return value
        
        instruction = re.sub(r'(?<=\s|,)(\d+[hb])', normalize_number, instruction)
        
        # Normalizar espacios alrededor de comas
        instruction = re.sub(r'\s*,\s*', ',', instruction)
        
        # Normalizar espacios múltiples
        instruction = ' '.join(instruction.split())
        
        # Normalizar paréntesis
        instruction = re.sub(r'\(\s+', '(', instruction)
        instruction = re.sub(r'\s+\)', ')', instruction)
        
        # Normalizar registros (asegurar mayúsculas)
        instruction = re.sub(r'\b[aA]\b', 'A', instruction)
        instruction = re.sub(r'\b[bB]\b', 'B', instruction)
        
        return instruction


    def decode_instruction(self, binary: str, labels: Dict[int, str] = None) -> str:
        try:
            opcode = binary[:self.config.instruction_params['bits']]
            params = binary[self.config.instruction_params['bits']:
                        self.config.instruction_params['bits'] + self.config.types_params['bits']]
            literal = binary[self.config.instruction_params['bits'] + 
                        self.config.types_params['bits']:]

            # Find the instruction
            instruction = None
            for name, details in self.config.instructions.items():
                if details['opcode'] == opcode:
                    instruction = name
                    break

            if not instruction:
                return f"Unknown instruction (opcode: {opcode})"

            param1 = params[:3]
            param2 = params[3:6] if len(params) >= 6 else ''

            # Special instructions
            if instruction in ['NOP', 'RET1', 'RET2']:
                if instruction in ['RET1', 'RET2']:
                    return 'RET' if instruction == 'RET1' else None
                return instruction

            # Unify POP1/POP2
            if instruction == 'POP1':
                return f"POP {self.config.types_inverse.get(param1, '')}"
            if instruction == 'POP2':
                return None

            # Jump and CALL instructions with labels
            if instruction in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR', 'CALL']:
                jump_address = int(literal, 2)
                # Check if the address has a label and use it
                if labels and jump_address in labels:
                    return f"{instruction} {labels[jump_address]}"
                return f"{instruction} {jump_address}"

            # Regular instructions
            param1_text = self.config.types_inverse.get(param1, '')
            param2_text = self.config.types_inverse.get(param2, '')

            result = instruction
            if param1_text:
                if param1_text in ['A', 'B']:
                    result += f" {param1_text}"
                elif param1_text == '(dir)':
                    # Convert the literal to the address representation
                    dir_value = int(literal, 2)
                    # Check if the value has an associated label
                    if labels and dir_value in labels:
                        result += f" ({labels[dir_value]})"
                    else:
                        result += f" ({dir_value})"
                else:
                    result += f" {param1_text}"

                if param2_text:
                    if param2_text == 'lit':
                        lit_value = int(literal, 2)
                        result += f",{lit_value if lit_value < 16 else hex(lit_value)[2:].upper() + 'h'}"
                    elif param2_text == '(dir)':
                        # Convert the literal to the address representation for the second parameter
                        dir_value = int(literal, 2)
                        if labels and dir_value in labels:
                            result += f",({labels[dir_value]})"
                        else:
                            result += f",({dir_value})"
                    else:
                        result += f",{param2_text}"

                elif param1_text.startswith('(') and literal:
                    lit_value = int(literal, 2)
                    if lit_value > 0:
                        result += f",{lit_value}"

            return result

        except Exception as e:
            return f"Error decoding: {str(e)}"



    def process_test_file(self, file_path: str) -> Dict:
        try:
            with open(file_path, 'r') as f:
                original_code = f.read()
            
            # Extraer etiquetas y mantener un registro de las instrucciones originales con sus binarios
            labels = self.extract_labels(original_code)
            labels_by_name = {v: k for k, v in labels.items()}
            instruction_mapping = []  # [(original_line, binary, line_number)]
            
            # Filtrar líneas relevantes y mantener el binario correspondiente
            binary_instructions = self.assembler.assemble(original_code)
            binary_index = 0
            original_lines = []
            
            in_code_section = False  # Variable para verificar si estamos en la sección CODE
            for line in original_code.split('\n'):
                line = line.strip()
                
                if '//' in line:
                    line = line.split('//')[0].strip()
                # Identificar el inicio de DATA y CODE
                if 'DATA:' in line:
                    in_code_section = False
                    continue
                elif 'CODE:' in line:
                    in_code_section = True
                    continue
                
                # Procesar solo las líneas dentro de CODE
                if in_code_section and line and not line.endswith(':') and not self.is_section_marker(line):
                    norm_line = self.normalize_instruction(line)
                    if norm_line:
                        binary = binary_instructions[binary_index] if binary_index < len(binary_instructions) else None
                        instruction_mapping.append((line, binary, binary_index))
                        original_lines.append((line, norm_line))
                        binary_index += 1

            # Decodificar instrucciones y verificar etiquetas
            decoded_instructions = []
            for binary in binary_instructions:
                decoded = self.decode_instruction(binary, labels)
                if decoded:
                    norm_decoded = self.normalize_instruction(decoded)
                    if norm_decoded:
                        decoded_instructions.append((decoded, norm_decoded))

            # Si no se encontraron líneas en la sección CODE
            if not original_lines:
                print("Error: No se encontraron instrucciones en la sección CODE.")
                return {
                    'file': os.path.basename(file_path),
                    'success': False,
                    'error': "No instructions found in CODE section"
                }

            # Analizar direccionamiento directo
            print(f"\nAnálisis detallado para {os.path.basename(file_path)}:")
            print("=" * 50)
            
            addressing_errors = []
            for orig_line, binary, line_num in instruction_mapping:
                if '(' in orig_line and ')' in orig_line and 'JMP' not in orig_line:
                    # Extraer el número entre paréntesis del original
                    orig_num = re.search(r'\((\d+)\)', orig_line)
                    if orig_num:
                        orig_num = int(orig_num.group(1))
                        # Extraer el literal del binario
                        literal_start = self.config.instruction_params['bits'] + self.config.types_params['bits']
                        literal = int(binary[literal_start:], 2)
                        
                        if orig_num != literal:
                            error_info = {
                                'line': line_num,
                                'original': orig_line,
                                'orig_num': orig_num,
                                'binary_num': literal,
                                'binary': binary
                            }
                            addressing_errors.append(error_info)
                            print(f"\nPosible error de direccionamiento directo:")
                            print(f"Línea original: {orig_line}")
                            print(f"Número original: {orig_num}")
                            print(f"Número en binario: {literal}")
                            print(f"Binario completo: {binary}")
                            print(f"Posición en archivo: línea {line_num}")
            
            print("=" * 50)

            # Decodificar instrucciones
            decoded_instructions = []
            for binary in binary_instructions:
                decoded = self.decode_instruction(binary, labels)
                if decoded:
                    norm_decoded = self.normalize_instruction(decoded)
                    if norm_decoded:
                        decoded_instructions.append((decoded, norm_decoded))

            # Preparar resultado
            test_result = {
                'file': os.path.basename(file_path),
                'success': True,
                'details': [],
                'original_count': len(original_lines),
                'decoded_count': len(decoded_instructions),
                'addressing_errors': []
            }

            # Comparar instrucciones
            max_length = max(len(original_lines), len(decoded_instructions))
            for i in range(max_length):
                detail = {
                    'index': i,
                    'matched': False,
                    'original': original_lines[i][0] if i < len(original_lines) else None,
                    'binary': binary_instructions[i] if i < len(binary_instructions) else None,
                    'decoded': decoded_instructions[i][0] if i < len(decoded_instructions) else None
                }

                if i < len(original_lines) and i < len(decoded_instructions):
                    orig_parts = original_lines[i][1].split()
                    decoded_parts = decoded_instructions[i][1].split()
                    
                    if orig_parts[0] in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR', 'CALL']:
                        orig_label = orig_parts[1]
                        if orig_label in labels_by_name:
                            detail['matched'] = decoded_parts[0] == orig_parts[0]
                        else:
                            detail['matched'] = original_lines[i][1] == decoded_instructions[i][1]
                    else:
                        detail['matched'] = original_lines[i][1] == decoded_instructions[i][1]

                if not detail['matched']:
                    test_result['success'] = False

                test_result['details'].append(detail)

            return test_result

        except Exception as e:
            return {
                'file': os.path.basename(file_path),
                'success': False,
                'error': str(e)
            }

    def run_tests(self, test_dir: str = None) -> List[Dict]:
        if test_dir is None:
            test_dir = os.path.join(os.path.dirname(__file__), 'inputs')
        
        test_files = sorted(glob.glob(os.path.join(test_dir, 'test*.txt')))
        return [self.process_test_file(test_file) for test_file in test_files]

    def print_results(self, results: List[Dict]) -> None:
        """Imprime los resultados de las pruebas de manera formateada."""
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get('success', False))
        
        print(f"\nResultados de las pruebas:")
        print(f"========================")
        print(f"Total de pruebas: {total_tests}")
        print(f"Pruebas exitosas: {successful_tests}")
        print(f"Pruebas fallidas: {total_tests - successful_tests}")
        print("\nDetalles:\n")
        
        for result in results:
            print(f"Archivo: {result['file']}")
            if 'error' in result:
                print(f"  Error: {result['error']}")
                continue
                
            print(f"  Estado: {'✓ Éxito' if result['success'] else '✗ Fallo'}")
            print(f"  Instrucciones originales: {result['original_count']}")
            print(f"  Instrucciones decodificadas: {result['decoded_count']}")
            
            if result.get('addressing_errors'):
                print("\n  Errores de direccionamiento directo detectados:")
                for err in result['addressing_errors']:
                    print(f"    Línea {err['line']}:")
                    print(f"      Original: {err['original']}")
                    print(f"      Número original: {err['orig_num']}")
                    print(f"      Número en binario: {err['binary_num']}")
            
            if not result['success']:
                print("\n  Diferencias encontradas:")
                for detail in result['details']:
                    if not detail['matched']:
                        print(f"\n    Índice {detail['index']}:")
                        if detail['original']:
                            print(f"      Original: {detail['original']}")
                        if detail['binary']:
                            print(f"      Binario:  {detail['binary']}")
                        if detail['decoded']:
                            print(f"      Decoded:  {detail['decoded']}")
            print("\n" + "="*50 + "\n")

def main():
    tester = AssemblerTester()
    results = tester.run_tests()
    tester.print_results(results)

if __name__ == '__main__':
    main()