"""Closed deployment for the two audited PHP files; caller provides PAYLOAD.

No API/mailbox calls, database access, service restart or credential changes.
Originals stay in a root-only backup. No source containing secrets is exported.
"""
import datetime,hashlib,json,os,pathlib,re,stat,subprocess,uuid,urllib.request
ROOT=pathlib.Path('/srv/legacy-staging/20260912/codigos.elgamermexicano.com')
assert os.getuid()==0 and re.fullmatch('[0-9a-f]{40}',PAYLOAD['sha'])
scope={};exec(PAYLOAD['portal_patch.py'],scope)
originals={name:(ROOT/name).read_bytes() for name in scope['BASELINES']}
proposed={name:scope['transform'](name,data) for name,data in originals.items()}
assert {name:hashlib.sha256(data).hexdigest() for name,data in proposed.items()}==PAYLOAD['expected_target_hashes'],'QA_PACKAGE_MISMATCH'
helper=ROOT/'universal_activation.php';assert not helper.exists(),'HELPER_ALREADY_EXISTS'
proposed['universal_activation.php']=PAYLOAD['universal_activation.php'].encode('utf-8')
backend=pathlib.Path('/srv/legacy-staging/20260912/correos.elgamermexicano.com')
protected={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [backend/'.env',backend/'app/Models/TMail.php',backend/'app/Http/Controllers/APIController.php']}
backup=pathlib.Path('/var/backups/codigos-universal-activation')
backup.mkdir(mode=0o700,exist_ok=True)
assert not backup.is_symlink() and backup.stat().st_uid==0 and stat.S_IMODE(backup.stat().st_mode)==0o700
backup=backup/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+PAYLOAD['sha'][:12]);backup.mkdir(mode=0o700)
metadata={name:(ROOT/name).stat() for name in originals}
for name,data in originals.items():
 (backup/name).write_bytes(data);(backup/name).chmod(0o600)
 assert hashlib.sha256((backup/name).read_bytes()).digest()==hashlib.sha256(data).digest()
def install(name,data,info):
 target=ROOT/name;assert not target.is_symlink()
 temp=ROOT/('.universal-'+uuid.uuid4().hex)
 try:
  fd=os.open(temp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.chown(temp,info.st_uid,info.st_gid);temp.chmod(stat.S_IMODE(info.st_mode));os.replace(temp,target)
 finally:
  if temp.exists():temp.unlink()
manifest={'sha':PAYLOAD['sha'],'backup_path':str(backup),'before':{name:hashlib.sha256(data).hexdigest() for name,data in originals.items()},'after':{name:hashlib.sha256(data).hexdigest() for name,data in proposed.items()},'protected':protected,'status':'PREPARED'}
def save():
 (backup/'manifest.json').write_text(json.dumps(manifest,indent=2));(backup/'manifest.json').chmod(0o600)
save()
try:
 # Recheck exact production baseline immediately before changing either entrypoint.
 assert all((ROOT/name).read_bytes()==data for name,data in originals.items()),'CONCURRENT_SOURCE_CHANGE'
 install('universal_activation.php',proposed['universal_activation.php'],metadata['inbox.php'])
 for name in originals:install(name,proposed[name],metadata[name])
 for name in proposed:
  assert subprocess.run(['php','-l',str(ROOT/name)],capture_output=True).returncode==0,'PHP_LINT_FAILED'
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==manifest['after'][name]
 assert all(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==digest for p,digest in protected.items()),'PROTECTED_SOURCE_CHANGED'
 with urllib.request.urlopen('https://codigos.elgamermexicano.com/consult.php',timeout=15) as response:assert response.status==200
 manifest['status']='DEPLOYED';save()
except BaseException:
 for name,data in originals.items():install(name,data,metadata[name])
 if helper.exists():helper.unlink()
 manifest['status']='ROLLED_BACK';save();raise
print(json.dumps({'sha':PAYLOAD['sha'],'backup_path':str(backup),'backup_verified':True,'files_verified':True,'protected_sources_unchanged':True,'http_status':200,'migrations':0,'mailbox_calls':0,'status':manifest['status'],'after_hashes':manifest['after']}))
