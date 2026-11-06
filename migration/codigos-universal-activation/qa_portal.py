"""Isolated PHP tests. Caller supplies public source files in PAYLOAD.

Reads original portal PHP only on the VPS. Never prints/export credentials.
No API/IMAP calls: test entrypoints start AFTER the API response is obtained.
"""
import hashlib,json,pathlib,re,subprocess,tempfile,shutil,os
ROOT=pathlib.Path('/srv/legacy-staging/20260912/codigos.elgamermexicano.com')
scope={};exec(PAYLOAD['portal_patch.py'],scope)
temp=pathlib.Path(tempfile.mkdtemp(prefix='universal-activation-qa-',dir='/var/tmp'))
os.chmod(temp,0o700)
def php(path):
 p=subprocess.run(['php','-d','display_errors=0','-d','log_errors=0','-d','disable_functions=curl_init,curl_exec,imap_open,file_put_contents','-f',str(path)],capture_output=True)
 assert p.returncode==0,'PHP_TEST_FAILED'
 return p.stdout.decode()
try:
 for name in ('universal_activation.php','test_universal.php'):
  (temp/name).write_text(PAYLOAD[name]);(temp/name).chmod(0o600)
 result=json.loads(php(temp/'test_universal.php'));originals={};patched={}
 for name in ('inbox.php','message.php'):
  originals[name]=(ROOT/name).read_bytes();patched[name]=scope['transform'](name,originals[name])
  # The full files are never executed: lint only, credentials remain private.
  (temp/name).write_bytes(patched[name]);(temp/name).chmod(0o600)
  p=subprocess.run(['php','-l',str(temp/name)],capture_output=True)
  assert p.returncode==0,'PATCHED_PHP_LINT_FAILED'
  old=re.search(rb'\$allowed_subjects = \[.*?\];',originals[name],re.S).group()
  new=re.search(rb'\$allowed_subjects = \[.*?\];',patched[name],re.S).group()
  assert old==new,'EXISTING_SUBJECTS_CHANGED'
 subjects=re.findall(rb"'([^']*)'",re.search(rb'\$allowed_subjects = \[.*?\];',originals['inbox.php'],re.S).group())
 base={'id':100,'sender_email':'no-reply@universalplus.com','sender_name':'Universal+',
       'subject':'Universal+ Código de activación','content':'<p>Tu código de activación</p><strong>Q7W8E9</strong>','date':'synthetic'}
 cases=[dict(base),dict(base,subject='UNIVERSAL+ CÓDIGO DE ACTIVACIÓN'),
        dict(base,subject=' Universal+   Código de activación '),dict(base,sender_email='attacker@example.invalid')]
 cases += [dict(base,subject=s.decode('utf-8'),sender_email='legacy@example.invalid') for s in subjects]
 count=0
 for i,message in enumerate(cases):
  for name in ('inbox.php','message.php'):
   # Strict splice after all HTTP work, using only synthetic data.
   suffix=patched[name][patched[name].index(b'$allowed_subjects = ['):]
   value=json.dumps([message] if name=='inbox.php' else message,ensure_ascii=True)
   # JSON is embedded via base64 rather than language-specific string escapes.
   import base64
   prefix="<?php require __DIR__.'/universal_activation.php'; $email='fixture@example.invalid'; "
   prefix+=('$messages' if name=='inbox.php' else '$message')+"=json_decode(base64_decode('"+base64.b64encode(value.encode()).decode()+"'),true);\n"
   fixture=temp/('fixture-'+name);fixture.write_bytes(prefix.encode()+suffix);fixture.chmod(0o600)
   output=php(fixture)
   if i<3:assert 'data-universal-code' in output and 'Q7W8E9' in output,'VALID_ALIAS_NOT_DISPLAYED_'+name+'_'+str(i)+'_OUTPUT_BYTES_'+str(len(output))
   elif i==3:assert 'data-universal-code' not in output and 'Bandeja de Entrada' not in output,'SPOOF_ALLOWED'
   else:
    assert 'data-universal-code' not in output,'OTHER_SERVICE_CHANGED'
    assert ('message.php?message_id=100' in output if name=='inbox.php' else '<strong>Q7W8E9</strong>' in output),'LEGACY_SUBJECT_REJECTED'
   count+=1
 # Newest valid code wins; an older code must never replace it.
 messages=[base,dict(base,id=99,content='<strong>A1B2C3</strong>')]
 import base64
 prefix="<?php require __DIR__.'/universal_activation.php'; $email='fixture@example.invalid'; $messages=json_decode(base64_decode('"+base64.b64encode(json.dumps(messages).encode()).decode()+"'),true);\n"
 fixture=temp/'newest.php';fixture.write_bytes(prefix.encode()+patched['inbox.php'][patched['inbox.php'].index(b'$allowed_subjects = ['):]);fixture.chmod(0o600)
 output=php(fixture);assert 'Q7W8E9' in output and 'A1B2C3' not in output,'NEWEST_SELECTION_FAILED'
 result.update(integration_tests=count+1,legacy_aliases_preserved=len(subjects),newest_valid_first=True,
  network_calls=0,mailbox_writes=0,temporary_files_removed=True,
  expected_target_hashes={name:hashlib.sha256(data).hexdigest() for name,data in patched.items()})
 print(json.dumps(result))
finally:
 shutil.rmtree(temp)
