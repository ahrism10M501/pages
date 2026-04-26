import sys
from pathlib import Path

# scripts/ 모듈을 테스트하기 위한 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
