import os
import sys
import glob
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.assembler import Assembler
from components.configuration import Configuration
from utils.exceptions import AssemblerError
import json

class InstructionType(Enum):
    JUMP = 'jump'
    REGULAR = 'regular'
    SPECIAL = 'special'

@dataclass
class InstructionDetail:
    index: int
    matched: bool
    original: str
    binary: str
    decoded: str

class AssemblerTester:
    JUMP_INSTRUCTIONS = {'JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR', 'CALL'}
    SPECIAL_INSTRUCTIONS = {'NOP', 'RET', 'RET1', 'RET2', 'POP1', 'POP2'}
    SECTION_MARKERS = {'CODE:', 'DATA:'}

    def __init__(self, setup_file: str = 'utils/setup.json'):
        setup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), setup_file)
        with open(setup_path, 'r') as f:
            self.setup = json.load(f)
        self.config = Configuration(self.setup)
        self.assembler = Assembler(self.setup, verbose=False)

    def extract_labels(self, content: str) -> Dict[int, str]:
        """Extrae las etiquetas y sus líneas correspondientes del código."""
        labels = {}
        current_line = 0
        in_code_section = False
        
        cleaned_lines = self._clean_line(content.split('\n'))
        
        for line in cleaned_lines:
            if line == 'CODE:':
                in_code_section = True
                continue
                
            if in_code_section:
                if line.endswith(':') and not line.startswith('DATA'):
                    label_name = line[:-1].strip()
                    labels[current_line] = label_name
                elif not self._is_section_marker(line):
                    current_line += 1
        
        return labels

    def process_variables(self, content: str) -> Dict[str, int]:
        """Procesa las variables y asigna direcciones de memoria."""
        variables = {}
        current_address = 0
        in_data_section = False
        
        for line in self._clean_line(content.split('\n')):
            if line == 'DATA:':
                in_data_section = True
                continue
            elif line == 'CODE:':
                break
            
            if in_data_section:
                # Eliminar comentarios y dividir en partes
                parts = line.split()
                if len(parts) >= 2:
                    var_name = parts[0]
                    # El valor no importa para la dirección, solo necesitamos asignar secuencialmente
                    variables[var_name] = current_address
                    current_address += 1
        
        return variables

    def _clean_line(self, lines: List[str]) -> List[str]:
        """Limpia las líneas de código eliminando comentarios y espacios."""
        cleaned_lines = []
        for line in lines:
            if isinstance(line, list):
                line = ''.join(line)  # Convertir lista de caracteres a string si es necesario
            line = line.strip()
            if line:
                if '//' in line:
                    line = line.split('//')[0].strip()
                if line:
                    cleaned_lines.append(line)
        return cleaned_lines

    def _is_section_marker(self, line: str) -> bool:
        """Verifica si una línea es un marcador de sección."""
        if isinstance(line, list):
            line = ''.join(line)  # Convertir lista de caracteres a string si es necesario
        return line.strip() in self.SECTION_MARKERS

    def _normalize_number(self, match_or_value) -> str:
        """Normaliza un número a su valor decimal."""
        value = match_or_value.group(1) if hasattr(match_or_value, 'group') else match_or_value
        value = value.strip()
        
        try:
            if isinstance(value, str):
                if value.endswith('h'):
                    return str(int(value[:-1], 16))
                elif value.endswith('b'):
                    return str(int(value[:-1], 2))
                elif value.endswith('d'):
                    return str(int(value[:-1], 10))
                return str(int(value))  # Intentar convertir como decimal si no tiene sufijo
        except ValueError:
            return value

    def compare_instructions(self, original: str, decoded: str, variables: Dict[str, int]) -> bool:
        """Compara dos instrucciones teniendo en cuenta los valores de las variables."""
        def normalize_for_comparison(instruction: str) -> str:
            instruction = instruction.strip()
            instruction = re.sub(r'\s+', ' ', instruction)
            
            def convert_value(match):
                value = match.group(1).strip()
                # Si es un nombre de variable, verificar su dirección en memoria
                if value in variables:
                    return str(variables[value])
                # Si es un número con formato
                try:
                    if value.endswith('h'):
                        return str(int(value[:-1], 16))
                    elif value.endswith('b'):
                        return str(int(value[:-1], 2))
                    elif value.endswith('d'):
                        return str(int(value[:-1]))
                    return str(int(value))
                except ValueError:
                    return value
            
            # Mantener registros indirectos como están
            instruction = re.sub(r'\(([AB])\)', r'(\1)', instruction)
            
            # Convertir variables y números en direccionamiento directo
            instruction = re.sub(r'\(([^)]+)\)', lambda m: f'({convert_value(m)})', instruction)
            
            # Convertir números literales
            instruction = re.sub(r'(?<![(\w])([a-zA-Z0-9]+[hbd]?)(?![)\w])', convert_value, instruction)
            
            # Normalizar espacios y comas
            instruction = re.sub(r'\s*,\s*', ',', instruction)
            
            return instruction.strip().upper()
        
        norm_original = normalize_for_comparison(original)
        norm_decoded = normalize_for_comparison(decoded)
        
        if norm_original != norm_decoded:
            print(f"Debug - Original normalizado: '{norm_original}'")
            print(f"Debug - Decodificado normalizado: '{norm_decoded}'")
        
        return norm_original == norm_decoded

    def normalize_instruction(self, instruction: str) -> Optional[str]:
        """Normaliza una instrucción para comparación."""
        if not instruction:
            return None
        
        if isinstance(instruction, list):
            instruction = ''.join(instruction)
                
        instruction = instruction.strip()
        if self._is_section_marker(instruction) or instruction.endswith(':'):
            return None

        parts = instruction.split(None, 1)
        if len(parts) == 1:
            return parts[0]
        
        instruction_name = parts[0]
        operands = parts[1]

        operands = re.sub(r'\s*\(\s*', '(', operands)
        operands = re.sub(r'\s*\)\s*', ')', operands)
        operands = re.sub(r'\s*,\s*', ',', operands)

        operands = re.sub(r'\(([^)]+)\)', lambda m: f'({self._normalize_number(m)})', operands)
        operands = re.sub(r'(?<![(\w])(\d+[hbd]?)(?![)\w])', self._normalize_number, operands)

        normalized = f"{instruction_name} {operands}"
        normalized = re.sub(r'\b[aA]\b', 'A', normalized)
        normalized = re.sub(r'\b[bB]\b', 'B', normalized)

        return normalized.strip()

    def decode_instruction(self, binary: str, labels: Dict[int, str]) -> Optional[str]:
        """Decodifica una instrucción binaria a su representación en assembly."""
        try:
            # Extraer partes de la instrucción
            opcode = binary[:self.config.instruction_params['bits']]
            params = binary[self.config.instruction_params['bits']:
                        self.config.instruction_params['bits'] + self.config.types_params['bits']]
            literal = binary[self.config.instruction_params['bits'] + 
                        self.config.types_params['bits']:]

            # Encontrar la instrucción
            instruction = next((name for name, details in self.config.instructions.items() 
                            if details['opcode'] == opcode), None)
            if not instruction:
                return f"Unknown instruction (opcode: {opcode})"

            param1 = params[:3]
            param2 = params[3:6] if len(params) >= 6 else ''

            # Manejar instrucciones especiales
            if instruction in self.SPECIAL_INSTRUCTIONS:
                if instruction in ['RET1', 'RET2']:
                    return 'RET' if instruction == 'RET1' else None
                if instruction == 'POP1':
                    return f"POP {self.config.types_inverse.get(param1, '')}"
                if instruction == 'POP2':
                    return None
                return instruction

            # Manejar instrucciones de salto
            if instruction in self.JUMP_INSTRUCTIONS:
                jump_address = int(literal, 2)
                label_name = next((name for name, addr in labels.items() 
                                if addr == jump_address), None)
                return f"{instruction} {label_name or jump_address}"

            # Construir instrucción regular
            return self._build_regular_instruction(instruction, param1, param2, literal, labels)

        except Exception as e:
            return f"Error decoding: {str(e)}"

    def _build_regular_instruction(self, instruction: str, param1: str, param2: str, 
                                literal: str, labels: Dict[int, str]) -> str:
        """Construye una instrucción regular a partir de sus componentes."""
        param1_text = self.config.types_inverse.get(param1, '')
        param2_text = self.config.types_inverse.get(param2, '')
        
        result = [instruction]
        
        # Construir la representación del primer operando
        if param1_text:
            if param1_text in ['A', 'B']:
                result.append(param1_text)
            elif param1_text == '(dir)':
                # Siempre usar el valor numérico para direccionamiento directo
                dir_value = int(literal, 2)
                result.append(f"({dir_value})")
            elif param1_text.startswith('(') and param1_text.endswith(')'):
                result.append(param1_text)
            else:
                result.append(param1_text)

            # Construir la representación del segundo operando
            if param2_text:
                result[-1] = result[-1] + ','  # Agregar coma al primer operando
                if param2_text == 'lit':
                    lit_value = int(literal, 2)
                    result.append(str(lit_value))
                elif param2_text == '(dir)':
                    # Siempre usar el valor numérico para direccionamiento directo
                    dir_value = int(literal, 2)
                    result.append(f"({dir_value})")
                elif param2_text.startswith('(') and param2_text.endswith(')'):
                    result.append(param2_text)
                else:
                    result.append(param2_text)

        return ' '.join(result)

    def process_test_file(self, file_path: str) -> Dict:
        """Procesa un archivo de prueba y retorna los resultados."""
        try:
            with open(file_path, 'r') as f:
                original_code = f.read()
            
            # Procesar variables primero
            self.variables = self.process_variables(original_code)
            
            # Extraer etiquetas
            labels = {}
            current_line = 0
            in_code_section = False
            
            for line in self._clean_line(original_code.split('\n')):
                if line == 'CODE:':
                    in_code_section = True
                    continue
                
                if in_code_section:
                    if line.endswith(':'):
                        label_name = line[:-1].strip()
                        labels[label_name] = current_line
                    elif not self._is_section_marker(line):
                        current_line += 1

            # Procesar instrucciones
            instructions = []
            in_code_section = False
            
            for line in self._clean_line(original_code.split('\n')):
                if line == 'CODE:':
                    in_code_section = True
                    continue
                
                if in_code_section and not line.endswith(':') and not self._is_section_marker(line):
                    norm_line = self.normalize_instruction(line)
                    if norm_line:
                        instructions.append((line, norm_line))

            if not instructions:
                return {
                    'file': os.path.basename(file_path),
                    'success': False,
                    'error': "No instructions found in CODE section"
                }

            # Ensamblar y decodificar
            try:
                binary_instructions = self.assembler.assemble(original_code)
                decoded = []
                
                for binary in binary_instructions:
                    instruction = self.decode_instruction(binary, labels)
                    if instruction:
                        norm_instruction = self.normalize_instruction(instruction)
                        if norm_instruction:
                            decoded.append((instruction, norm_instruction))

                # Comparar instrucciones
                comparison_results = []
                max_length = max(len(instructions), len(decoded))
                
                for i in range(max_length):
                    detail = InstructionDetail(
                        index=i,
                        matched=False,
                        original=instructions[i][0] if i < len(instructions) else None,
                        binary=binary_instructions[i] if i < len(binary_instructions) else None,
                        decoded=decoded[i][0] if i < len(decoded) else None
                    )

                    if i < len(instructions) and i < len(decoded):
                        # Usar el método compare_instructions existente
                        detail.matched = self.compare_instructions(
                            instructions[i][1],
                            decoded[i][1],
                            self.variables
                        )
                    
                    comparison_results.append(detail)

                return {
                    'file': os.path.basename(file_path),
                    'success': all(r.matched for r in comparison_results),
                    'details': comparison_results,
                    'original_count': len(instructions),
                    'decoded_count': len(decoded)
                }

            except Exception as e:
                return {
                    'file': os.path.basename(file_path),
                    'success': False,
                    'error': f"Error in assembly or decoding: {str(e)}"
                }

        except Exception as e:
            return {
                'file': os.path.basename(file_path),
                'success': False,
                'error': str(e)
            }
    def run_tests(self, test_dir: str = None) -> List[Dict]:
        """Ejecuta todas las pruebas en el directorio especificado."""
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
        
        for result in results:
            self._print_test_result(result)

    def _print_test_result(self, result: Dict) -> None:
        """Imprime el resultado de una prueba individual."""
        print(f"\nArchivo: {result['file']}")
        if 'error' in result:
            print(f"  Error: {result['error']}")
            return
            
        print(f"  Estado: {'✓ Éxito' if result['success'] else '✗ Fallo'}")
        print(f"  Instrucciones originales: {result.get('original_count', 0)}")
        print(f"  Instrucciones decodificadas: {result.get('decoded_count', 0)}")
        
        if not result['success']:
            print("\n  Diferencias encontradas:")
            for detail in result['details']:
                if not detail.matched:
                    print(f"\n    Índice {detail.index}:")
                    if detail.original:
                        print(f"      Original: {detail.original}")
                    if detail.binary:
                        print(f"      Binario:  {detail.binary}")
                    if detail.decoded:
                        print(f"      Decoded:  {detail.decoded}")
        print("\n" + "="*50)

    def _process_instructions(self, original_code: str, variables: Dict[str, int]) -> List[Tuple[str, str]]:
        """
        Procesa las instrucciones del código original.
        Retorna una lista de tuplas (instrucción_original, instrucción_normalizada)
        """
        instructions = []
        in_code_section = False
        
        for line in self._clean_line(original_code.split('\n')):
            if line == 'CODE:':
                in_code_section = True
                continue
            
            if in_code_section and not line.endswith(':') and not self._is_section_marker(line):
                # Reemplazar referencias a variables con sus direcciones
                modified_line = line
                for var_name, address in variables.items():
                    modified_line = modified_line.replace(f'({var_name})', f'({address})')
                
                norm_line = self.normalize_instruction(modified_line)
                if norm_line:
                    instructions.append((line, norm_line))
        
        return instructions

    def _decode_instructions(self, binary_instructions: List[str], labels: Dict[int, str]) -> List[Tuple[str, str]]:
        """
        Decodifica las instrucciones binarias.
        Retorna una lista de tuplas (instrucción_decodificada, instrucción_normalizada)
        """
        decoded = []
        for binary in binary_instructions:
            instruction = self.decode_instruction(binary, labels)
            if instruction:
                for label_name, line_num in labels.items():
                    if f' {line_num}' in instruction:
                        instruction = instruction.replace(f' {line_num}', f' {label_name}')
                norm_instruction = self.normalize_instruction(instruction)
                if norm_instruction:
                    decoded.append((instruction, norm_instruction))
        return decoded

    def _compare_instructions(self, 
                            original_instructions: List[Tuple[str, str]], 
                            decoded_instructions: List[Tuple[str, str]], 
                            binary_instructions: List[str],
                            variables: Dict[str, int],
                            labels: Dict[str, int]) -> List[InstructionDetail]:
        """
        Compara las instrucciones originales con las decodificadas.
        Retorna una lista de InstructionDetail con los resultados de la comparación.
        """
        max_length = max(len(original_instructions), len(decoded_instructions))
        results = []
        
        for i in range(max_length):
            detail = InstructionDetail(
                index=i,
                matched=False,
                original=original_instructions[i][0] if i < len(original_instructions) else None,
                binary=binary_instructions[i] if i < len(binary_instructions) else None,
                decoded=decoded_instructions[i][0] if i < len(decoded_instructions) else None
            )

            if i < len(original_instructions) and i < len(decoded_instructions):
                orig_parts = original_instructions[i][1].split()
                decoded_parts = decoded_instructions[i][1].split()
                
                if orig_parts[0] in self.JUMP_INSTRUCTIONS:
                    detail.matched = (
                        decoded_parts[0] == orig_parts[0] and
                        (decoded_parts[1] == orig_parts[1] or 
                         (orig_parts[1] in labels and str(labels[orig_parts[1]]) == decoded_parts[1]))
                    )
                else:
                    detail.matched = self.compare_instructions(
                        original_instructions[i][1],
                        decoded_instructions[i][1],
                        variables
                    )
            
            results.append(detail)
        
        return results

def main():
    tester = AssemblerTester()
    results = tester.run_tests()
    tester.print_results(results)

if __name__ == '__main__':
    main()