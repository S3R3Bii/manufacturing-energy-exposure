"""Prespecified source population; no empirical parameter selection."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COUNTRIES=['BE','DE','ES','FR','IT','NL']
YEARS=list(range(2015,2024))
SECTORS=['C10-C12','C13-C15','C16','C17','C18','C19','C20','C21','C22','C23','C24','C25','C26','C27','C28','C29','C30','C31_C32','C33']
ABSOLUTE,RELATIVE=1e-7,1e-9
