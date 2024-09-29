class AssemblerError(Exception):
    """Clase base para excepciones del assembler."""
    pass

class InvalidInstructionError(AssemblerError):
    """Se lanza cuando se encuentra una instrucción inválida."""
    pass

class InvalidOperandError(AssemblerError):
    """Se lanza cuando un operando es inválido."""
    pass

class LabelError(AssemblerError):
    """Se lanza cuando hay un problema con una etiqueta."""
    pass

class SyntaxError(AssemblerError):
    """Se lanza cuando hay un error de sintaxis en el código assembly."""
    pass

class MemoryError(AssemblerError):
    """Se lanza cuando hay un problema relacionado con la memoria."""
    pass