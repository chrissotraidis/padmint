"""Run the shipped UI JavaScript with deferred responses and inert DOM nodes."""
import json
import shutil
import subprocess
import unittest

from padmint.ui import PAGE


@unittest.skipUnless(shutil.which('node'), 'Node is needed to exercise browser JavaScript')
class FileResponseTests(unittest.TestCase):
    def run_case(self, case):
        page = PAGE.split('<script>')[1].split('</script>')[0]
        data = {'games': [], 'downloads': [], 'later': [], 'text': {'file_ok': 'Selected: {file}'}}
        script = r'''
const assert = require('node:assert/strict');
const element = () => ({value:'',textContent:'',children:[],dataset:{},style:{},
  classList:{add(){},remove(){},toggle(){},contains(){return false}},
  setAttribute(){},scrollIntoView(){},focus(){},append(){},replaceChildren(){}});
const elements = new Map();
const document = {documentElement:{},querySelectorAll:()=>[],createElement:element,
  getElementById:id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id)}};
function scrollTo(){}
''' + page.replace('__TOKEN__', 'fixture').replace('__DATA__', json.dumps(data)) + r'''
cards=()=>{};
D.games=['a','b'].map(id=>({id,name:id,needs_file:true,formats:[],files:[],ids:[],
  platforms:[{id:'ios',label:'iOS'},{id:'macos',label:'Mac'}]}));
const pending=[];
post=(url,body)=>new Promise(resolve=>pending.push({url,body,resolve}));
function select(id){choose(id);dev='ios';ready()}
(async()=>{
''' + case + r'''
})().catch(error=>{console.error(error);process.exitCode=1});
'''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_older_success_cannot_replace_a_newer_rejected_file(self):
        self.run_case(r'''
select('a');
const older=useFile('/old.exe'), newer=useFile('/patch.exe');
pending[1].resolve({problem:'Wrong input'});await newer;
pending[0].resolve({});await older;
assert.equal(file,null);assert.equal($('path').value,'/patch.exe');
assert.equal($('fileState').textContent,'Wrong input');assert.equal($('make').disabled,true);
''')

    def test_switching_away_and_back_discards_old_validation(self):
        self.run_case(r'''
select('a');const old=useFile('/old.exe');
back();select('b');assert.equal(reading,false);
select('a');pending[0].resolve({});await old;
assert.equal(file,null);assert.equal($('fileState').textContent,'');
assert.equal($('make').disabled,true);
''')

    def test_stale_error_does_not_disable_a_new_valid_selection(self):
        self.run_case(r'''
select('a');const old=useFile('/old.exe'), current=useFile('/current.exe');
pending[1].resolve({});await current;
pending[0].resolve({problem:'Old failure'});await old;
assert.equal(file,'/current.exe');assert.equal($('make').disabled,false);
assert.match($('fileState').textContent,/current.exe/);
''')

    def test_cancelled_picker_does_not_orphan_validation_already_in_progress(self):
        self.run_case(r'''
select('a');const checking=useFile('/current.exe'), picking=$('choose').onclick();
pending[1].resolve({path:null,available:true});await picking;
pending[0].resolve({});await checking;
assert.equal(reading,false);assert.equal(file,'/current.exe');assert.equal($('make').disabled,false);
''')

    def test_file_picker_response_is_discarded_after_switching_games(self):
        self.run_case(r'''
select('a');const picking=$('choose').onclick();select('b');
pending[0].resolve({path:'/old.exe',available:true});await picking;
assert.equal(pending.length,1);assert.equal(file,null);assert.equal(reading,false);
''')


if __name__ == '__main__':
    unittest.main()
