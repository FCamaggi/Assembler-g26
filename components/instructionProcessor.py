from typing import Dict, List, Tuple, Union
from components.memory import Memory
from utils.exceptions import InvalidInstructionError, InvalidOperandError
from components.configuration import Configuration
from components.valueConverter import ValueConverter

class InstructionProcessor:
    def __init__(self, config: Configuration):
        self.config = config
        self.single_operand_instructions = {
            'PUSH'  # INC y DEC se manejan por separado
        }
        self.flexible_operand_instructions = {
            'NOT', 'SHL', 'SHR'
        }
        self.no_operand_instructions = {
            'NOP', 'RET1', 'RET2'
        }
        self.jump_instructions = {
            'JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 
            'JLT', 'JLE', 'JCR', 'CALL'
        }
        # Definir operandos válidos para INC y DEC
        self.inc_valid_operands = {'A', 'B', '(Dir)', '(B)'}
        self.dec_valid_operands = {'A'}

    def _parse_instruction(self, instruction: str) -> Tuple[str, List[str]]:
        parts = instruction.split(maxsplit=1)
        if not parts:
            raise InvalidInstructionError("Instrucción vacía")
            
        instruction_name = parts[0]
        
        if len(parts) == 1:
            return instruction_name, []
            
        operands_str = parts[1]
        operands = []
        current = []
        in_parentheses = False
        
        for char in operands_str:
            if char == '(':
                in_parentheses = True
                current.append(char)
            elif char == ')':
                in_parentheses = False
                current.append(char)
            elif char == ',' and not in_parentheses:
                if current:
                    operands.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        
        if current:
            operands.append(''.join(current).strip())
            
        operands = [op.strip() for op in operands if op.strip()]
        
        return instruction_name, operands


    def _parse_numeric_value(self, value: str) -> int:
        """Procesa un valor numérico en cualquier formato soportado."""
        value = value.strip()
        try:
            if value.endswith('h'):
                return int(value[:-1], 16)
            elif value.endswith('b'):
                return int(value[:-1], 2)
            elif value.endswith('d'):
                return int(value[:-1])
            return int(value)
        except ValueError:
            raise InvalidOperandError(f"Valor numérico inválido: {value}")

    def _process_memory_reference(self, operand: str, data: Dict[str, int], memory: Memory) -> str:
        """Procesa referencias a memoria, manejando variables y direcciones directas."""
        if operand.startswith('(') and operand.endswith(')'):
            inner = operand[1:-1].strip()
            
            # Si es una variable definida en DATA
            if inner in data:
                return format(memory.get_address(inner), f'0{self.config.lit_params["bits"]}b')
            
            # Si es un registro A o B
            if inner in ['A', 'B']:
                return '0' * self.config.lit_params['bits']
            
            # Si es un número (decimal, hexadecimal o binario)
            try:
                address = self._parse_numeric_value(inner)
                return format(address, f'0{self.config.lit_params["bits"]}b')
            except InvalidOperandError:
                raise InvalidOperandError(f"Referencia a memoria inválida: {operand}")
                
        return '0' * self.config.lit_params['bits']

    def _validate_inc_dec_operand(self, instruction_name: str, operand: str) -> None:
        """Valida que el operando sea válido para INC/DEC según las especificaciones."""
        if instruction_name == 'INC':
            # Para INC, validar que el operando sea A, B, (Dir) o (B)
            if operand not in ['A', 'B'] and not (
                operand.startswith('(') and operand.endswith(')') and (
                    operand[1:-1] == 'B' or 
                    operand[1:-1].isdigit() or 
                    operand[1:-1].endswith('h') or 
                    operand[1:-1].endswith('b')
                )
            ):
                raise InvalidOperandError(f"Operando inválido para INC: {operand}")
        elif instruction_name == 'DEC':
            # Para DEC, solo permitir el operando A
            if operand != 'A':
                raise InvalidOperandError("DEC solo acepta el operando A")

    def get_opcode(self, instruction: str, labels: Dict[str, int], data: Dict[str, int], memory: Memory, instruction_address: int) -> Union[str, List[str]]:
        instruction_name, operands = self._parse_instruction(instruction)

        # Manejo de instrucciones especiales (POP y RET)
        if instruction_name == 'POP':
            if len(operands) != 1 or operands[0] not in ['A', 'B']:
                raise InvalidOperandError("POP requiere exactamente un operando (A o B)")
            binary1 = self.config.instructions['POP1']['opcode']
            binary2 = self.config.instructions['POP2']['opcode']
            param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
            return [
                binary1 + param_binary.ljust(self.config.types_params['bits'], '0') + '0' * self.config.lit_params['bits'],
                binary2 + param_binary.ljust(self.config.types_params['bits'], '0') + '0' * self.config.lit_params['bits']
            ]

        if instruction_name == 'RET':
            if operands:
                raise InvalidOperandError("RET no debe tener operandos")
            return [
                self.config.instructions['RET1']['opcode'].ljust(self.config.word_length, '0'),
                self.config.instructions['RET2']['opcode'].ljust(self.config.word_length, '0')
            ]

        if instruction_name not in self.config.instructions:
            raise InvalidInstructionError(f"Instrucción desconocida: {instruction_name}")

        binary = self.config.instructions[instruction_name]['opcode']

        # Manejar INC y DEC específicamente
        if instruction_name in ['INC', 'DEC']:
            if len(operands) != 1:
                raise InvalidOperandError(f"{instruction_name} requiere exactamente un operando")
            
            self._validate_inc_dec_operand(instruction_name, operands[0])
            
            param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
            param_binary = param_binary.ljust(self.config.types_params['bits'], '0')
            
            # Literal 1 solo para INC A y DEC A
            if operands[0] == 'A':
                literal_value = format(1, f'0{self.config.lit_params["bits"]}b')
            else:
                if operands[0].startswith('('):
                    literal_value = self._process_memory_reference(operands[0], data, memory)
                else:
                    literal_value = '0' * self.config.lit_params['bits']
            
            return binary + param_binary + literal_value

        # Instrucciones sin operandos
        if instruction_name in self.no_operand_instructions:
            return binary.ljust(self.config.word_length, '0')

        # Instrucciones de salto
        if instruction_name in self.jump_instructions:
            if len(operands) != 1:
                raise InvalidOperandError(f"Instrucción {instruction_name} requiere un operando")
            jump_target = operands[0]
            if jump_target in labels:
                jump_address = labels[jump_target]
            else:
                try:
                    jump_address = self._parse_numeric_value(jump_target)
                except InvalidOperandError:
                    raise InvalidOperandError(f"Operando de salto inválido: {jump_target}")
            return binary + '0' * self.config.types_params['bits'] + format(jump_address, f'0{self.config.lit_params["bits"]}b')

        # Preparar parámetros binarios
        param_binary = ''
        literal_value = '0' * self.config.lit_params['bits']

        # Instrucciones con formato flexible
        if instruction_name in self.flexible_operand_instructions:
            if len(operands) == 1:
                # Formato de un operando
                operand = operands[0]
                param_binary = ValueConverter.param_to_binary(operand, self.config.types, self.config.types_params)
                param_binary = param_binary.ljust(self.config.types_params['bits'], '0')
                if operand.startswith('('):
                    literal_value = self._process_memory_reference(operand, data, memory)
            else:
                # Formato de dos operandos
                dest, source = operands
                param_binary = ''
                param_binary += ValueConverter.param_to_binary(dest, self.config.types, self.config.types_params)[:3]
                param_binary += ValueConverter.param_to_binary(source, self.config.types, self.config.types_params)[:3]
                param_binary = param_binary.ljust(self.config.types_params['bits'], '0')
                if dest.startswith('('):
                    literal_value = self._process_memory_reference(dest, data, memory)
            return binary + param_binary + literal_value

        # Instrucciones de un solo operando
        if instruction_name in self.single_operand_instructions:
            if len(operands) != 1:
                raise InvalidOperandError(f"Instrucción {instruction_name} requiere un operando")
            
            operand = operands[0]
            param_binary = ValueConverter.param_to_binary(operand, self.config.types, self.config.types_params)
            param_binary = param_binary.ljust(self.config.types_params['bits'], '0')
            
            if operand.startswith('('):
                literal_value = self._process_memory_reference(operand, data, memory)
            return binary + param_binary + literal_value

        # Instrucciones con dos operandos
        if len(operands) != 2:
            raise InvalidOperandError(f"Instrucción {instruction_name} requiere dos operandos")

        # Procesar primer operando
        param_binary += ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)[:3]
        
        # Procesar segundo operando
        param_binary += ValueConverter.param_to_binary(operands[1], self.config.types, self.config.types_params)[:3]
        param_binary = param_binary.ljust(self.config.types_params['bits'], '0')

        # Manejar literales y referencias a memoria
        if operands[1].startswith('('):
            literal_value = self._process_memory_reference(operands[1], data, memory)
        elif ValueConverter.is_numeric(operands[1]):
            value = self._parse_numeric_value(operands[1])
            literal_value = format(value, f'0{self.config.lit_params["bits"]}b')

        return binary + param_binary + literal_value