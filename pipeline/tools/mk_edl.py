# mk_edl.py name : reads edl spec from $W/edl_<name>.txt (docstring \n---\n KEEPS body \n---\n HOOK line) -> pipeline/edl_<name>.py
import sys, os
n = sys.argv[1]; doc, keeps, hook = open(os.path.join(os.path.dirname(__file__), f"edl_{n}.txt")).read().split("\n---\n")
s = open('pipeline/edl_work_light6.py').read()
a = s.index('"""'); b = s.index('"""', 3) + 3
s = s[:a] + '"""' + doc.strip() + '\n"""' + s[b:]
a = s.index('KEEPS = ['); b = s.index('MANUAL_CUTS')
s = s[:a] + 'KEEPS = [\n' + keeps.strip('\n') + '\n]\n' + s[b:]
s = s.replace('HOOK = dict(video=(0.00, 2.98), voice=None, drill_gain=1.0)', hook.strip())
open(f'pipeline/edl_{n}.py', 'w').write(s); print("ok")
