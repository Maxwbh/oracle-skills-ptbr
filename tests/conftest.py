"""Configuração comum dos testes.

Os scripts DevOps importam ``oracle_devops_utils`` a partir da própria pasta.
No repo a fonte única fica em ``shared/assets/`` (o build propaga), então os
testes colocam as duas pastas no ``sys.path``.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for pasta in (RAIZ / "shared" / "assets", RAIZ / "skills" / "oracle-devops-ptbr" / "assets"):
    if str(pasta) not in sys.path:
        sys.path.insert(0, str(pasta))
