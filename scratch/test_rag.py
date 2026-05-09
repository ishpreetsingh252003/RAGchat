import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Testing imports...")
from phases.phase_3.generation.answer import synthesize
print("Synthesize imported.")

result = synthesize("test query")
print(f"Result: {result['grounded']}")
