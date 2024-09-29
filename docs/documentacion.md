# Assembler para Arquitectura de Computadores

Este proyecto implementa un assembler para el curso IIC2343 - Arquitectura de Computadores. El assembler traduce código assembly a código de máquina y puede programar directamente la ROM de una placa Basys3.

## Características

- Soporte para instrucciones específicas del proyecto
- Manejo de etiquetas y variables
- Soporte para números en base decimal, binaria y hexadecimal
- Manejo de arrays y strings en la sección de datos
- Interfaz de línea de comandos flexible
- Capacidad de programar directamente la ROM de Basys3

## Requisitos

- Python 3.7+
- Librería `iic2343` (para programar la Basys3)

## Instalación

Instala las dependencias:

```bash
   pip install iic2343
```

## Uso

El assembler se puede usar de varias maneras:

### Uso básico

```bash
python main.py codigo_fuente.txt
```

Esto ensamblará el código en `codigo_fuente.txt` y generará el archivo de salida `output.txt`.

### Opciones adicionales

- `-o`, `--output`: Especifica un archivo de salida diferente

```bash
  python main.py codigo_fuente.txt -o salida.bin
```

- `-s`, `--setup`: Usa un archivo de configuración personalizado

```bash
  python main.py codigo_fuente.txt -s mi_config.json
```

- `-v`, `--verbose`: Muestra información detallada durante el proceso

```bash
  python main.py codigo_fuente.txt -v
```

- `--debug`: Activa el modo de depuración

```bash
  python main.py codigo_fuente.txt --debug
```

- `--program-basys`: Programa la ROM de la Basys3 después del ensamblaje

```bash
  python main.py codigo_fuente.txt --program-basys
```

- `--port`: Especifica el puerto serial para la Basys3

```bash
  python main.py codigo_fuente.txt --program-basys --port COM3
```

## Estructura del código fuente

El código fuente debe seguir esta estructura:

```assembly
DATA:
variable1 42
array [1, 2, 3]
string "Hola, mundo!"
CODE:
MOV A, variable1
ADD A, 10
LABEL:
JMP LABEL
```

- La sección `DATA:` define variables y arrays.
- La sección `CODE:` contiene las instrucciones del programa.
- Se pueden usar etiquetas para saltos y llamadas a subrutinas.

## Formatos numéricos soportados

- Decimal: `42`
- Binario: `1010b`
- Hexadecimal: `2Ah`
- Caracteres: `'A'`

## Instrucciones soportadas

- MOV, ADD, SUB, AND, OR, XOR
- NOT, SHL, SHR
- INC, DEC
- CMP
- JMP, JEQ, JNE, JGT, JGE, JLT, JLE, JCR
- NOP
- PUSH, POP
- CALL, RET

## Estructura del Código Binario

El assembler genera código binario de 36 bits para cada instrucción, siguiendo esta estructura:

| Opcode | Param 1 | Param 2 | Literal/Dirección |
| ------ | ------- | ------- | ----------------- |
| 6 bits | 3 bits  | 3 bits  | 24 bits           |

### Campos

1. **Opcode** (6 bits): Identifica la instrucción.
2. **Param 1** (3 bits): Tipo del primer parámetro.
3. **Param 2** (3 bits): Tipo del segundo parámetro.
4. **Literal/Dirección** (24 bits): Valor literal o dirección de memoria.

### Tipos de Parámetros

- `001`: Registro A
- `010`: Registro B
- `011`: Dirección de memoria
- `100`: Valor literal
- `101`: Indirección a través del registro A
- `110`: Indirección a través del registro B

### Ejemplos

1. `MOV A, 42`

```example
Opcode: 000001 (MOV)
Param 1: 001 (Registro A)
Param 2: 100 (Valor literal)
Literal: 000000000000000000101010 (42 en binario)
Resultado: 000001001100000000000000000000101010
```

1. `ADD B, (1234)`

```example
Opcode: 000010 (ADD)
Param 1: 010 (Registro B)
Param 2: 011 (Dirección de memoria)
Dirección: 000000000000010011010010 (1234 en binario)
Resultado: 000010010011000000000000010011010010
```

1. `JMP LABEL` (asumiendo que LABEL está en la dirección 50)

```example
Opcode: 010000 (JMP)
Param 1: 000 (No usado)
Param 2: 000 (No usado)
Dirección: 000000000000000000110010 (50 en binario)
Resultado: 010000000000000000000000000000110010
```

1. `MOV (A), B`

```example
Opcode: 000001 (MOV)
Param 1: 101 (Indirección a través de A)
Param 2: 010 (Registro B)
Literal: 000000000000000000000000 (No usado)
Resultado: 000001101010000000000000000000000000
```

Nota: La estructura exacta puede variar según la configuración en el archivo `setup.json`.
