"""Run SolidCraft's native bench-open in fresh processes; keep phase-level JSONL."""
import argparse,hashlib,json,subprocess,time,statistics
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--cli',required=True,help='Path to solidcraft-cli (or compatible solvecraft-cli)')
 ap.add_argument('--model',type=Path,default=Path(__file__).resolve().parents[1]/'models/Rover-v7.solidcraft')
 ap.add_argument('--runs',type=int,default=5);ap.add_argument('--timeout',type=float,default=300)
 ap.add_argument('--out',type=Path,default=Path('benchmark-results'))
 a=ap.parse_args()
 if a.runs<1 or a.timeout<=0:ap.error('runs and timeout must be positive')
 a.out.mkdir(parents=True,exist_ok=True)
 version=subprocess.run([a.cli,'--version'],check=True,capture_output=True,text=True).stdout.strip()
 results=[]
 for i in range(a.runs):
  t=time.perf_counter()
  p=subprocess.run([a.cli,'bench-open',str(a.model)],capture_output=True,text=True,encoding='utf-8',timeout=a.timeout)
  wall=(time.perf_counter()-t)*1000
  (a.out/f'run-{i+1:02d}.jsonl').write_text(p.stdout,encoding='utf-8')
  if p.returncode:raise RuntimeError(f'Run {i+1} failed: {p.stderr}')
  rows=[json.loads(x) for x in p.stdout.splitlines() if x.strip()]
  errors=[x for x in rows if x.get('error')]
  if errors:raise RuntimeError(f'Feature errors: {errors}')
  phases={x['step']:x['ms'] for x in rows if x.get('step') in ['read','parse','evaluate','mesh']}
  if set(phases)!={'read','parse','evaluate','mesh'}:raise RuntimeError('Missing benchmark phases')
  mesh=next(x for x in rows if x.get('step')=='mesh')
  result={'run':i+1,'process_wall_ms':wall,'phases_ms':phases,'bodies':mesh['bodies'],'triangles':mesh['triangles']};results.append(result)
  print(json.dumps(result),flush=True)
 summary={'cli_version':version,'fixture':a.model.name,'fixture_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest(),'runs':results,'median_phases_ms':{k:statistics.median(x['phases_ms'][k] for x in results) for k in phases},'median_process_wall_ms':statistics.median(x['process_wall_ms'] for x in results),'scope':'Fresh CLI process per run; OS file cache not flushed. Includes CLI display preparation, not GUI startup or first presented frame.'}
 (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
