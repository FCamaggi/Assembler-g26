from typing import Dict, List, Tuple, Union
from components.memory import Memory
from utils.exceptions import InvalidInstructionError, InvalidOperandError
from components.configuration import Configuration
from components.valueConverter import ValueConverter

class InstructionProcessor:
    def __init__(self, config: Configuration):
        self.config = config
        self.single_operand_instructions = {
            'PUSH', 'INC', 'DEC'
        }
        self.flexible_format_instructions = {
            'NOT', 'SHL', 'SHR'
        }
        self.no_operand_instructions = {
            'NOP', 'RET1', 'RET2'
        }
        self.jump_instructions = {
            'JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 
            'JLT', 'JLE', 'JCR', 'CALL'
        }
        self.binary_ops = {
            'ADD', 'SUB', 'AND', 'OR', 'XOR'
        }
        self.double_instructions = {'POP', 'RET'}
        self.valid_reg_A_instructions = {'DEC'}

    def process_instruction(self, instruction: str, labels: Dict[str, int], data: Dict, memory: Memory, instruction_address: int) -> Union[str, List[str]]:
        instruction_name, operands = self._parse_instruction(instruction)
        
        # Manejar POP que ahora requiere generación de dos instrucciones
        if instruction_name == 'POP':
            if len(operands) != 1 or operands[0] not in ['A', 'B']:
                raise InvalidOperandError("POP requiere exactamente un operando (A o B)")
            return [
                self._generate_pop_instruction('POP1', operands[0]),
                self._generate_pop_instruction('POP2', operands[0])
            ]
        
        # Manejar RET que ahora requiere generación de dos instrucciones
        if instruction_name == 'RET':
            if operands:
                raise InvalidOperandError("RET no debe tener operandos")
            return [
                self._generate_basic_instruction('RET1'),
                self._generate_basic_instruction('RET2')
            ]

        # Validaciones específicas para registros
        if instruction_name in self.valid_reg_A_instructions and operands[0] != 'A':
            raise InvalidOperandError(f"{instruction_name} solo puede usar el registro A")

        # Validaciones para INC
        if instruction_name == 'INC':
            if len(operands) != 1:
                raise InvalidOperandError("INC requiere exactamente un operando")
            if not any(operands[0].startswith(valid) for valid in self.inc_valid_operands):
                raise InvalidOperandError(f"Operando inválido para INC: {operands[0]}")

        return self._generate_instruction(instruction_name, operands, labels, data, memory, instruction_address)

    def _generate_pop_instruction(self, pop_type: str, register: str) -> str:
        """Genera una instrucción POP (POP1 o POP2)"""
        binary = self.config.instructions[pop_type]['opcode']
        param_binary = ValueConverter.param_to_binary(register, self.config.types, self.config.types_params)
        return binary + param_binary.ljust(self.config.types_params['bits'], '0') + '0' * self.config.lit_params['bits']

    def _generate_basic_instruction(self, instruction_name: str) -> str:
        """Genera una instrucción básica sin operandos"""
        return self.config.instructions[instruction_name]['opcode'].ljust(self.config.word_length, '0')

    def _generate_instruction(self, instruction_name: str, operands: List[str], labels: Dict[str, int], 
                            data: Dict, memory: Memory, instruction_address: int) -> str:
        """Genera una instrucción binaria estándar"""
        if instruction_name not in self.config.instructions:
            raise InvalidInstructionError(f"Instrucción desconocida: {instruction_name}")

        binary = self.config.instructions[instruction_name]['opcode']
        
        # Instrucciones sin operandos
        if instruction_name in self.no_operand_instructions:
            return binary.ljust(self.config.word_length, '0')

        # Instrucciones de salto
        if instruction_name in self.jump_instructions:
            if len(operands) != 1:
                raise InvalidOperandError(f"{instruction_name} requiere un operando")
            return self._process_jump_instruction(binary, operands[0], labels)

        # Procesamiento de operandos
        param_binary = self._process_operands(instruction_name, operands)
        literal_value = self._process_literal(operands, data, memory)

        return binary + param_binary + literal_value

    def _process_jump_instruction(self, binary: str, target: str, labels: Dict[str, int]) -> str:
        """Procesa una instrucción de salto"""
        if target in labels:
            address = labels[target]
        else:
            try:
                address = ValueConverter.parse_numeric(target)
            except ValueError:
                raise InvalidOperandError(f"Destino de salto inválido: {target}")
        return binary + '0' * self.config.types_params['bits'] + format(address, f'0{self.config.lit_params["bits"]}b')

    def _process_operands(self, instruction_name: str, operands: List[str]) -> str:
        """Procesa los operandos de una instrucción"""
        if len(operands) == 0:
            return '0' * self.config.types_params['bits']
        
        if len(operands) == 1:
            param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
            return param_binary.ljust(self.config.types_params['bits'], '0')
        
        param1_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
        param2_binary = ValueConverter.param_to_binary(operands[1], self.config.types, self.config.types_params)
        return (param1_binary[:3] + param2_binary[:3]).ljust(self.config.types_params['bits'], '0')

    def _process_literal(self, operands: List[str], data: Dict, memory: Memory) -> str:
        """Procesa el valor literal de una instrucción"""
        if not operands:
            return '0' * self.config.lit_params['bits']
            
        operand = operands[-1]
        if operand.startswith('('):
            return ValueConverter.literal_or_direct_value(operand, self.config.types, self.config.lit_params, {}, data, memory, 0)
        elif ValueConverter.is_numeric(operand):
            value = ValueConverter.parse_numeric(operand)
            return format(value, f'0{self.config.lit_params["bits"]}b')
        return '0' * self.config.lit_params['bits']

    def _parse_instruction(self, instruction: str) -> Tuple[str, List[str]]:
        """Parsea una instrucción en su nombre y operandos"""
        parts = instruction.split(maxsplit=1)
        if not parts:
            raise InvalidInstructionError("Instrucción vacía")
            
        instruction_name = parts[0]
        if len(parts) == 1:
            return instruction_name, []
            
        operands = []
        current = []
        in_parentheses = False
        
        for char in parts[1]:
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
        
        return instruction_name, [op.strip() for op in operands if op.strip()]

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

        # Manejo especial para operaciones binarias
        if instruction_name in self.binary_ops:
            return self._handle_binary_operation(instruction_name, operands, labels, data, memory, instruction_address)

        # Manejo especial para instrucciones flexibles (NOT, SHL, SHR)
        if instruction_name in self.flexible_format_instructions:
            return self._handle_flexible_instruction(instruction_name, operands, labels, data, memory, instruction_address)

        # Manejo especial para INC
        if instruction_name == 'INC':
            return self._handle_inc_instruction(operands, labels, data, memory, instruction_address)

        # Manejo de POP
        if instruction_name == 'POP':
            return self._handle_pop_instruction(operands)

        # Manejo de RET
        if instruction_name == 'RET':
            return self._handle_ret_instruction(operands)
        



        if instruction_name not in self.config.instructions:
            raise InvalidInstructionError(f"Instrucción desconocida: {instruction_name}")

        binary = self.config.instructions[instruction_name]['opcode']

        # Instrucciones sin operandos
        if instruction_name in self.no_operand_instructions:
            return binary.ljust(self.config.word_length, '0')

        # Instrucciones de salto
        if instruction_name in self.jump_instructions:
            return self._handle_jump_instruction(instruction_name, binary, operands, labels)

        # Validaciones específicas para registros
        if instruction_name in self.valid_reg_A_instructions and operands[0] != 'A':
            raise InvalidOperandError(f"{instruction_name} solo puede usar el registro A")

        # Instrucciones con un operando
        if instruction_name in self.single_operand_instructions:
            return self._handle_single_operand_instruction(instruction_name, operands, labels, data, memory, instruction_address)

        # Instrucciones con dos operandos
        return self._handle_double_operand_instruction(instruction_name, operands, labels, data, memory, instruction_address)

    def _handle_flexible_instruction(self, instruction_name: str, operands: List[str], labels: Dict[str, int], 
                                   data: Dict[str, int], memory: Memory, instruction_address: int) -> str:
        """Maneja instrucciones NOT, SHL, SHR que pueden tener diferentes formatos"""
        if len(operands) == 0:
            raise InvalidOperandError(f"{instruction_name} requiere al menos un operando")
            
        binary = self.config.instructions[instruction_name]['opcode']
        
        if len(operands) == 1:
            # Formato de un operando
            param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
            param_binary = param_binary.ljust(self.config.types_params['bits'], '0')
            literal_value = '0' * self.config.lit_params['bits']
        else:
            # Formato de dos operandos
            dest, source = operands[:2]
            param1_binary = ValueConverter.param_to_binary(dest, self.config.types, self.config.types_params)[:3]
            param2_binary = ValueConverter.param_to_binary(source, self.config.types, self.config.types_params)[:3]
            param_binary = (param1_binary + param2_binary).ljust(self.config.types_params['bits'], '0')
            
            if dest.startswith('('):
                literal_value = ValueConverter.literal_or_direct_value(
                    dest,
                    self.config.types,
                    self.config.lit_params,
                    labels,
                    data,
                    memory,
                    instruction_address
                )
            else:
                literal_value = '0' * self.config.lit_params['bits']
                
        return binary + param_binary + literal_value

    def _handle_inc_instruction(self, operands: List[str], labels: Dict[str, int], data: Dict[str, int], 
                              memory: Memory, instruction_address: int) -> str:
        """Maneja la instrucción INC"""
        if len(operands) != 1:
            raise InvalidOperandError("INC requiere exactamente un operando")
            
        operand = operands[0]
        binary = self.config.instructions['INC']['opcode']
        param_binary = ValueConverter.param_to_binary(operand, self.config.types, self.config.types_params)
        
        if operand.startswith('('):
            literal_value = ValueConverter.literal_or_direct_value(operand, self.config.types, self.config.lit_params, labels, data, memory, instruction_address)
        else:
            literal_value = '0' * self.config.lit_params['bits']
            
        return binary + param_binary.ljust(self.config.types_params['bits'], '0') + literal_value

    def _handle_pop_instruction(self, operands: List[str]) -> List[str]:
        """Maneja la instrucción POP"""
        if len(operands) != 1 or operands[0] not in ['A', 'B']:
            raise InvalidOperandError("POP requiere exactamente un operando (A o B)")
            
        param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
        pad_bits = '0' * self.config.lit_params['bits']
        
        return [
            self.config.instructions['POP1']['opcode'] + param_binary.ljust(self.config.types_params['bits'], '0') + pad_bits,
            self.config.instructions['POP2']['opcode'] + param_binary.ljust(self.config.types_params['bits'], '0') + pad_bits
        ]

    def _handle_ret_instruction(self, operands: List[str]) -> List[str]:
        """Maneja la instrucción RET"""
        if operands:
            raise InvalidOperandError("RET no debe tener operandos")
        return [
            self.config.instructions['RET1']['opcode'].ljust(self.config.word_length, '0'),
            self.config.instructions['RET2']['opcode'].ljust(self.config.word_length, '0')
        ]

    def _handle_jump_instruction(self, instruction_name: str, binary: str, operands: List[str], 
                               labels: Dict[str, int]) -> str:
        """Maneja las instrucciones de salto"""
        if len(operands) != 1:
            raise InvalidOperandError(f"{instruction_name} requiere un operando")
            
        target = operands[0]
        if target in labels:
            address = labels[target]
        else:
            try:
                address = ValueConverter.parse_numeric(target)
            except ValueError:
                raise InvalidOperandError(f"Destino de salto inválido: {target}")
                
        return binary + '0' * self.config.types_params['bits'] + format(address, f'0{self.config.lit_params["bits"]}b')

    def _handle_single_operand_instruction(self, instruction_name: str, operands: List[str], labels: Dict[str, int], 
                                         data: Dict[str, int], memory: Memory, instruction_address: int) -> str:
        """Maneja instrucciones con un solo operando"""
        if len(operands) != 1:
            raise InvalidOperandError(f"{instruction_name} requiere un operando")
            
        binary = self.config.instructions[instruction_name]['opcode']
        param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
        
        if operands[0].startswith('('):
            literal_value = ValueConverter.literal_or_direct_value(operands[0], self.config.types, self.config.lit_params, labels, data, memory, instruction_address)
        else:
            literal_value = '0' * self.config.lit_params['bits']
            
        return binary + param_binary.ljust(self.config.types_params['bits'], '0') + literal_value

    def _handle_double_operand_instruction(self, instruction_name: str, operands: List[str], labels: Dict[str, int], 
                                         data: Dict[str, int], memory: Memory, instruction_address: int) -> str:
        """Maneja instrucciones con dos operandos"""
        if len(operands) != 2:
            raise InvalidOperandError(f"{instruction_name} requiere dos operandos")
            
        binary = self.config.instructions[instruction_name]['opcode']
        param1_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)[:3]
        param2_binary = ValueConverter.param_to_binary(operands[1], self.config.types, self.config.types_params)[:3]
        param_binary = (param1_binary + param2_binary).ljust(self.config.types_params['bits'], '0')
        
        if operands[1].startswith('('):
            literal_value = ValueConverter.literal_or_direct_value(operands[1], self.config.types, self.config.lit_params, labels, data, memory, instruction_address)
        elif ValueConverter.is_numeric(operands[1]):
            literal_value = ValueConverter.literal_or_direct_value(operands[1], self.config.types, self.config.lit_params, labels, data, memory, instruction_address)
        else:
            literal_value = '0' * self.config.lit_params['bits']
            
        return binary + param_binary + literal_value

    def _handle_binary_operation(self, instruction_name: str, operands: List[str], labels: Dict[str, int], 
                               data: Dict[str, int], memory: Memory, instruction_address: int) -> str:
        """Maneja las operaciones binarias (ADD, SUB, AND, OR, XOR)"""
        binary = self.config.instructions[instruction_name]['opcode']

        # Caso especial: un solo operando (Dir)
        if len(operands) == 1:
            operand = operands[0]
            if not (operand.startswith('(') and operand.endswith(')')):
                raise InvalidOperandError(f"{instruction_name} con un operando debe usar direccionamiento directo")
            
            # Usamos tipo (dir) para el destino y A implícito como fuente
            param_binary = ValueConverter.param_to_binary(operand, self.config.types, self.config.types_params)
            param_binary = param_binary.ljust(self.config.types_params['bits'], '0')
            
            literal_value = ValueConverter.literal_or_direct_value(
                operand,
                self.config.types,
                self.config.lit_params,
                labels,
                data,
                memory,
                instruction_address
            )
            
            return binary + param_binary + literal_value

        # Caso normal: dos operandos
        if len(operands) != 2:
            raise InvalidOperandError(f"{instruction_name} requiere uno o dos operandos")

        # Procesamiento normal para dos operandos
        param1_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)[:3]
        param2_binary = ValueConverter.param_to_binary(operands[1], self.config.types, self.config.types_params)[:3]
        param_binary = (param1_binary + param2_binary).ljust(self.config.types_params['bits'], '0')
        
        # Determinar el valor literal según el segundo operando
        if operands[1].startswith('('):
            literal_value = ValueConverter.literal_or_direct_value(
                operands[1],
                self.config.types,
                self.config.lit_params,
                labels,
                data,
                memory,
                instruction_address
            )
        elif ValueConverter.is_numeric(operands[1]):
            literal_value = ValueConverter.literal_or_direct_value(
                operands[1],
                self.config.types,
                self.config.lit_params,
                labels,
                data,
                memory,
                instruction_address
            )
        else:
            literal_value = '0' * self.config.lit_params['bits']
            
        return binary + param_binary + literal_value