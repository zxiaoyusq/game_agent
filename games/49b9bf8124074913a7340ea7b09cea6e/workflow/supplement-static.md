# 用户补充静态片段登记

来源：本轮 request_user_input 的真实用户回答，不属于原ZIP。用户声明目标ELF SHA-256为 `4cf2ba474fc9aefda142fbdca46cf7b4d3ebf06a2114ecd8487a3e48448710b4`，地址为link VA。没有收到原始ELF、提取工具日志或只读数据段。本文件逐项保留用户提供的地址、字节、助记符和操作数；不是重新执行反汇编的产物。

字节列按用户给出的内存字节顺序保存（AArch64小端）。

## S-01：标称起点0x18b9d34的调用方节选

| VA | 字节 | 指令 |
|---|---|---|
|18b9fd0|9ae3ff97|bl #0x18b2e38|
|18b9fd4|e00316aa|mov x0, x22|
|18b9fd8|0840601e|fmov d8, d0|
|18b9fdc|e2c20094|bl #0x18eab64|
|18b9fe0|e00314aa|mov x0, x20|
|18b9fe4|e10316aa|mov x1, x22|
|18b9fe8|e20315aa|mov x2, x21|
|18b9fec|2940601e|fmov d9, d1|
|18b9ff0|ce130094|bl #0x18bef28|
|18b9ff4|0a40601e|fmov d10, d0|
|18b9ff8|8ae5ff97|bl #0x18b3620|
|18b9ffc|2be6ff97|bl #0x18b38a8|
|18ba000|0b1040fd|ldr d11, [x0, #0x20]|
|18ba004|87e5ff97|bl #0x18b3620|
|18ba008|28e6ff97|bl #0x18b38a8|
|18ba00c|011440fd|ldr d1, [x0, #0x28]|
|18ba010|6041601e|fmov d0, d11|
|18ba014|60d000d0|adrp x0, #0x32c8000|
|18ba018|00a02791|add x0, x0, #0x9e8|
|18ba01c|87e3ff97|bl #0x18b2e38|
|18ba020|0b40601e|fmov d11, d0|
|18ba024|0041601e|fmov d0, d8|
|18ba028|e00316aa|mov x0, x22|
|18ba02c|2141601e|fmov d1, d9|
|18ba030|8f760394|bl #0x1997a6c|
|18ba034|e8c30091|add x8, sp, #0x30|
|18ba038|e00314aa|mov x0, x20|
|18ba03c|e10316aa|mov x1, x22|
|18ba040|e20315aa|mov x2, x21|

## S-02：标称起点0x18b2e38的目标节选

| VA | 字节 | 指令 |
|---|---|---|
|18b2e38|0020611e|fcmp d0, d1|
|18b2e3c|41000054|b.ne #0x18b2e44|
|18b2e40|c0035fd6|ret|
|18b2e44|080040f9|ldr x8, [x0]|
|18b2e48|e9919752|mov w9, #0xbc8f|
|18b2e4c|aa0080d2|mov x10, #5|
|18b2e50|4a00c0f2|movk x10, #2, lsl #32|
|18b2e54|2020601e|fcmp d1, d0|
|18b2e58|087d099b|mul x8, x8, x9|
|18b2e5c|0a7dca9b|umulh x10, x8, x10|
|18b2e60|0b010acb|sub x11, x8, x10|
|18b2e64|4a054b8b|add x10, x10, x11, lsr #1|
|18b2e68|4afd5ed3|lsr x10, x10, #0x1e|
|18b2e6c|4a7d0acb|sub x10, x10, x10, lsl #31|
|18b2e70|08010a8b|add x8, x8, x10|
|18b2e74|2a0080d2|mov x10, #1|
|18b2e78|097d099b|mul x9, x8, x9|
|18b2e7c|2a00a0f2|movk x10, #1, lsl #16|
|18b2e80|080500d1|sub x8, x8, #1|
|18b2e84|0a00d0f2|movk x10, #0x8000, lsl #32|
|18b2e88|0201639e|ucvtf d2, x8|
|18b2e8c|c8d1ff90|adrp x8, #0x12ea000|
|18b2e90|04ed41fd|ldr d4, [x8, #0x3d8]|
|18b2e94|c8d1ff90|adrp x8, #0x12ea000|
|18b2e98|2a7dca9b|umulh x10, x9, x10|
|18b2e9c|4afd4ed3|lsr x10, x10, #0xe|
|18b2ea0|4a7d0acb|sub x10, x10, x10, lsl #31|
|18b2ea4|29010a8b|add x9, x9, x10|
|18b2ea8|2a0500d1|sub x10, x9, #1|
|18b2eac|090000f9|str x9, [x0]|
|18b2eb0|4301639e|ucvtf d3, x10|
|18b2eb4|6208441f|fmadd d2, d3, d4, d2|
|18b2eb8|037142fd|ldr d3, [x8, #0x4e0]|
|18b2ebc|4218631e|fdiv d2, d2, d3|
|18b2ec0|034c611e|fcsel d3, d0, d1, mi|
|18b2ec4|204c601e|fcsel d0, d1, d0, mi|
|18b2ec8|6138601e|fsub d1, d3, d0|
|18b2ecc|2000421f|fmadd d0, d1, d2, d0|
|18b2ed0|c0035fd6|ret|
