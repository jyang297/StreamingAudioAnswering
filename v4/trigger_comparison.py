import json,os,subprocess,time,sys,argparse
from pathlib import Path
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--output-dir',required=True)
out=Path(parser.parse_args().output_dir).resolve();out.mkdir(parents=True,exist_ok=False)
turns=[{'partials':['I would like to know','I would like to know the price of Chai','I would like to know the price of Chai in this sample catalog'], 'final':'I would like to know the price of Chai in this sample catalog. Please give its unit price, rather than the total value of its stock.', 'gap_ms':250}, {'partials':[],'final':'Chang price?'}, {'partials':['Stock?'],'final':'Stock?','gap_ms':250}]
(out/'turns.json').write_text(json.dumps(turns))
for policy in ['time','text','hybrid']:
 with (out/(policy+'.json')).open('w') as stdout,(out/(policy+'.jsonl')).open('w') as stderr:
  r=subprocess.run([sys.executable,'-m','rag_poc.cli','--credential-file','postgres-fixture/.env','--speculate','--trigger-policy',policy,'--trigger-ms','150','--change-units','3','--turns-file',str(out/'turns.json')],cwd=root,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},stdout=stdout,stderr=stderr,timeout=180)
 print(policy,'exit',r.returncode,flush=True)
 if r.returncode:break
