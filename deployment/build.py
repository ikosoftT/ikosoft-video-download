from pathlib import Path
import shutil
root = Path(__file__).resolve().parents[1]
output = root / 'deployment' / 'vercel' / 'public'
output.mkdir(exist_ok=True)
for file in (root / 'static').iterdir():
    if file.is_file(): shutil.copy2(file, output / file.name)
print('Vercel frontend built:', output)
