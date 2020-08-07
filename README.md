# Ger2KiCad

A simple python script to convert Gerber files (RS274X) to .kicad_mod files that can be easily imported by KiCad. It is possible to read multiple files and specify the import layer (F.Cu, In1.Cu, ..., B.Cu). 

This script was mainly designed to import RF structures in KiCad, but should handle all polygon based designs (Uses G36/G37 codes of the RS274X standard).

This script uses the [pcb-tools](https://github.com/curtacircuitos/pcb-tools) package. 
