"""Operadores del bytecode (OP 0x54), en el orden de snoot-ps1 (tools/script_compiler/opcodes.py)."""
OPERATORS = ["==", "!=", "<", "<=", ">", ">=", "and", "or", "not", "+", "-", "*"]
OP_CODE = {name: i for i, name in enumerate(OPERATORS)}
