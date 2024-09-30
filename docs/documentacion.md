# Assembler para Arquitectura de Computadores

Este proyecto implementa un assembler para el curso IIC2343 - Arquitectura de Computadores. El assembler traduce código assembly a código de máquina y puede programar directamente la ROM de una placa Basys3.

## Características

- Soporte para instrucciones específicas del proyecto
- Manejo de etiquetas y variables
- Soporte para números en base decimal, binaria y hexadecimal
- Manejo de arrays y strings en la sección de datos
- Interfaz de línea de comandos flexible
- Capacidad de programar directamente la ROM de Basys3
- Opción para cargar datos iniciales como instrucciones

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
- `-s`, `--setup`: Usa un archivo de configuración personalizado
- `-v`, `--verbose`: Muestra información detallada durante el proceso
- `--debug`: Activa el modo de depuración
- `--program-basys`: Programa la ROM de la Basys3 después del ensamblaje
- `--port`: Especifica el puerto serial para la Basys3
- `--load-data`: Carga los datos iniciales como instrucciones

## Problema: Verificador de Palíndromo Binario

El siguiente código verifica si un número de 16 bits es un palíndromo en binario. Un palíndromo es un número que se lee igual de izquierda a derecha que de derecha a izquierda.

### Codigo Fuente

```assembly
DATA:
num 384  // Número a verificar
res 0    // Resultado: 0 = No es palíndromo, 1 = Sí es palíndromo
temp 0   // Variable temporal para operaciones
count 16 // Contador para 16 bits
one 1    // Constante 1 para operaciones bit a bit

CODE:
// Inicialización
MOV A,(num)  // Carga el número en A
MOV B,0      // B se usará como el número invertido

// Invertir el número
loop:
    MOV (temp),A  // Guarda A en temp
    MOV A,(one)   // Carga 1 en A
    AND A,(temp)  // Aislar el bit menos significativo
    MOV (temp),A  // Guarda el resultado en temp
    SHL B         // Desplaza B a la izquierda
    ADD B,(temp)  // Añade el bit menos significativo a B
    MOV A,(temp)  // Recupera el valor original de A
    SHR A         // Desplaza A a la derecha

    MOV A,(count)
    DEC A
    MOV (count),A
    CMP A,0
    JNE loop      // Continúa si el contador no es cero

// Comparar el número original con su inverso
MOV A,(num)
CMP A,B
JEQ is_palindrome

// No es palíndromo
MOV A,0
MOV (res),A
JMP end

// Es palíndromo
is_palindrome:
MOV A,1
MOV (res),A

// Fin del programa
end:
MOV A,(res)
MOV B,(res)
```

### Explicación del Código

1. **Inicialización**: Se carga el número a verificar en el registro A y se inicializa B a 0.
2. **Inversión del número**: Se utiliza un bucle para invertir el número bit a bit.
   - Se aísla el bit menos significativo de A.
   - Se desplaza B a la izquierda y se añade el bit aislado.
   - Se desplaza A a la derecha.
   - Se repite 16 veces (para un número de 16 bits).
3. **Comparación**: Se compara el número original (A) con su inverso (B).
4. **Resultado**: Se almacena 1 en `res` si es palíndromo, 0 si no lo es.

### Cómo Ejecutar

Para ensamblar y ejecutar este programa:

1. Guarda el código en un archivo (por ejemplo, `palindromo.txt`).
2. Ejecuta el assembler:

   ```bash
   python main.py palindromo.txt -v
   ```

   O si quieres cargar los datos como instrucciones:

   ```bash
   python main.py palindromo.txt -v --load-data
   ```

3. El assembler generará el código de máquina en `output.txt`.
4. Si usas `--program-basys`, el código se cargará directamente en la placa Basys3.

### Interpretación del Resultado

- Si `res` es 1, el número es un palíndromo binario.
- Si `res` es 0, el número no es un palíndromo binario.

En este ejemplo, 384 (110000000 en binario) no es un palíndromo binario, por lo que `res` será 0.

## Estructura del Código Binario

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

## Estructura de la palabra de instrucción

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

### Ejemplo

1. `MOV A, 42`

```example
Opcode: 000001 (MOV)
Param 1: 001 (Registro A)
Param 2: 100 (Valor literal)
Literal: 000000000000000000101010 (42 en binario)
Resultado: 000001001100000000000000000000101010
```

Nota: La estructura exacta puede variar según la configuración en el archivo `setup.json`.
