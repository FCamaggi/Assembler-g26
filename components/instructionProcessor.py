from typing import Dict, List, Tuple, Union
from components.memory import Memory
from utils.exceptions import InvalidInstructionError, InvalidOperandError
from components.configuration import Configuration
from components.valueConverter import ValueConverter

class InstructionProcessor:
    def __init__(self, config: Configuration):
        self.config = config
        # Instrucciones que pueden tener un solo operando
        self.single_operand_instructions = {
            'INC', 'DEC', 'PUSH'
        }
        # Instrucciones que pueden tener uno o dos operandos
        self.flexible_operand_instructions = {
            'NOT', 'SHL', 'SHR'
        }
        # Instrucciones sin operandos
        self.no_operand_instructions = {
            'NOP', 'RET1', 'RET2'
        }
        # Instrucciones de salto
        self.jump_instructions = {
            'JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 
            'JLT', 'JLE', 'JCR', 'CALL'
        }

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

    
    def get_opcode(self, instruction: str, labels: Dict[str, int], data: Dict[str, int], memory: Memory, instruction_address: int) -> Union[str, List[str]]:
        instruction_name, operands = self._parse_instruction(instruction)

        # Manejo especial para POP
        if instruction_name == 'POP':
            if len(operands) != 1:
                raise InvalidOperandError("POP requiere exactamente un operando (A o B)")
            if operands[0] not in ['A', 'B']:
                raise InvalidOperandError("POP solo acepta A o B como operando")
            
            # Primera instrucción (POP1)
            binary1 = self.config.instructions['POP1']['opcode']
            param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
            binary1 += param_binary.ljust(self.config.types_params['bits'], '0')
            binary1 = binary1.ljust(self.config.word_length, '0')
            
            # Segunda instrucción (POP2)
            binary2 = self.config.instructions['POP2']['opcode']
            param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
            binary2 += param_binary.ljust(self.config.types_params['bits'], '0')
            binary2 = binary2.ljust(self.config.word_length, '0')
            
            return [binary1, binary2]

        # Manejo especial para RET
        if instruction_name == 'RET':
            if operands:
                raise InvalidOperandError("RET no debe tener operandos")
            
            # Primera instrucción (RET1)
            binary1 = self.config.instructions['RET1']['opcode'].ljust(self.config.word_length, '0')
            
            # Segunda instrucción (RET2)
            binary2 = self.config.instructions['RET2']['opcode'].ljust(self.config.word_length, '0')
            
            return [binary1, binary2]
        
        if instruction_name not in self.config.instructions:
            raise InvalidInstructionError(f"Instrucción desconocida: {instruction_name}")

        binary = self.config.instructions[instruction_name]['opcode']

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
                    jump_address = ValueConverter.parse_numeric(jump_target)
                except ValueError:
                    raise InvalidOperandError(f"Operando de salto inválido: {jump_target}")
            return binary + '0' * self.config.types_params['bits'] + format(jump_address, f'0{self.config.lit_params["bits"]}b')
        
        # Instrucciones flexibles (NOT, SHL, SHR)
        if instruction_name in self.flexible_operand_instructions:
            if len(operands) == 1:
                # Formato de un operando
                param_type = ValueConverter.get_type(operands[0], self.config.types)
                param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
                return binary + param_binary.ljust(self.config.types_params['bits'], '0') + '0' * self.config.lit_params['bits']
            elif len(operands) == 2:
                # Formato de dos operandos
                dest, source = operands
                param_binary = ''
                param_binary += ValueConverter.param_to_binary(dest, self.config.types, self.config.types_params)[:3]
                param_binary += ValueConverter.param_to_binary(source, self.config.types, self.config.types_params)[:3]
                
                # Manejar literales y direcciones para el destino si es necesario
                literal_value = '0' * self.config.lit_params['bits']
                if dest.startswith('(') and dest.endswith(')'):
                    var_name = dest[1:-1]
                    if var_name in data:
                        literal_value = format(memory.get_address(var_name), f'0{self.config.lit_params["bits"]}b')
                    elif ValueConverter.is_numeric(var_name):
                        address = ValueConverter.parse_numeric(var_name)
                        literal_value = format(address, f'0{self.config.lit_params["bits"]}b')
                
                return binary + param_binary.ljust(self.config.types_params['bits'], '0') + literal_value
            else:
                raise InvalidOperandError(f"Instrucción {instruction_name} requiere uno o dos operandos")

        # Instrucciones de un solo operando
        if instruction_name in self.single_operand_instructions:
            if len(operands) != 1:
                raise InvalidOperandError(f"Instrucción {instruction_name} requiere un operando")
            
            param_type = ValueConverter.get_type(operands[0], self.config.types)
            param_binary = ValueConverter.param_to_binary(operands[0], self.config.types, self.config.types_params)
            
            literal_value = '0' * self.config.lit_params['bits']
            if operands[0].startswith('('):
                inner = operands[0][1:-1]
                if inner in data:
                    literal_value = format(memory.get_address(inner), f'0{self.config.lit_params["bits"]}b')
                elif ValueConverter.is_numeric(inner):
                    address = ValueConverter.parse_numeric(inner)
                    literal_value = format(address, f'0{self.config.lit_params["bits"]}b')
            
            return binary + param_binary.ljust(self.config.types_params['bits'], '0') + literal_value

        # Instrucciones con dos operandos
        if len(operands) != 2:
            raise InvalidOperandError(f"Instrucción {instruction_name} requiere dos operandos")

        dest, source = operands
        dest_type = ValueConverter.get_type(dest, self.config.types)
        source_type = ValueConverter.get_type(source, self.config.types)

        param_binary = ''
        param_binary += ValueConverter.param_to_binary(dest, self.config.types, self.config.types_params)[:3]
        param_binary += ValueConverter.param_to_binary(source, self.config.types, self.config.types_params)[:3]
        param_binary = param_binary.ljust(self.config.types_params['bits'], '0')

        literal_value = '0' * self.config.lit_params['bits']
        
        if source_type == 'lit':
            literal_value = ValueConverter.literal_or_direct_value(source, self.config.types, self.config.lit_params, labels, data, memory, instruction_address)
        elif source in data:
            literal_value = format(memory.get_address(source), f'0{self.config.lit_params["bits"]}b')
        elif source.startswith('(') and source.endswith(')'):
            var_name = source[1:-1]
            if var_name in data:
                literal_value = format(memory.get_address(var_name), f'0{self.config.lit_params["bits"]}b')
            elif ValueConverter.is_numeric(var_name):
                address = ValueConverter.parse_numeric(var_name)
                literal_value = format(address, f'0{self.config.lit_params["bits"]}b')

        return binary + param_binary + literal_value