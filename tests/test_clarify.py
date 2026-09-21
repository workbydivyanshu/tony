import os
import shutil
import tempfile
import sys
import importlib.machinery
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

def _load_tony():
    loader = importlib.machinery.SourceFileLoader("tony", os.path.join(ROOT, "tony"))
    spec = importlib.util.spec_from_file_location("tony", os.path.join(ROOT, "tony"), loader=loader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _patch_engine_fn(name, fake_fn):
    import lib.engine as eng_mod
    orig = getattr(eng_mod, name)
    setattr(eng_mod, name, fake_fn)
    return orig

def test_clarify_hook_interactive():
    tony = _load_tony()
    tmp = tempfile.mkdtemp()
    
    calls = []
    def fake_role_call(role, model, prompt, workdir, **kw):
        if role == "architect":
            calls.append(prompt)
            if len(calls) == 1:
                return {"status": "ok", "output": "CLARIFY: are you sure?", "outfile": "/tmp/a.md", "duration": 0.1}
            return {"status": "ok", "output": "# Boulder\n## TODOs\n- [ ] 1. done", "outfile": "/tmp/b.md", "duration": 0.1}
        return {"status": "ok", "output": "...", "outfile": "/tmp/b.md", "duration": 0.1}
    
    orig_rc = _patch_engine_fn("role_call", fake_role_call)
    orig_rl = _patch_engine_fn("run_loop", lambda *args, **kw: None)
    orig_vw = _patch_engine_fn("verify_wave", lambda *args, **kw: [])
    
    orig_isatty = sys.stdin.isatty
    sys.stdin.isatty = lambda: True
    
    orig_input = __builtins__.get('input') if isinstance(__builtins__, dict) else builtins.input if hasattr(__builtins__, 'input') else None
    
    import lib.plangate as gate_mod
    orig_confirm = gate_mod.confirm_plan
    gate_mod.confirm_plan = lambda *a, **k: True
    
    try:
        import builtins
        builtins.input = lambda prompt: "yes i am sure"
        
        tony.cmd_mission("my mission", workdir=tmp, yes=False)
        
        assert len(calls) == 2
        assert "[Clarification]: are you sure?" in calls[1]
        assert "[Answer]: yes i am sure" in calls[1]
        
    finally:
        sys.stdin.isatty = orig_isatty
        builtins.input = orig_input
        gate_mod.confirm_plan = orig_confirm
        _patch_engine_fn("role_call", orig_rc)
        _patch_engine_fn("run_loop", orig_rl)
        _patch_engine_fn("verify_wave", orig_vw)
        shutil.rmtree(tmp, ignore_errors=True)

def test_clarify_hook_headless_aborts():
    tony = _load_tony()
    tmp = tempfile.mkdtemp()
    
    def fake_role_call(role, model, prompt, workdir, **kw):
        return {"status": "ok", "output": "CLARIFY: what?", "outfile": "/tmp/a.md", "duration": 0.1}
        
    orig_rc = _patch_engine_fn("role_call", fake_role_call)
    orig_isatty = sys.stdin.isatty
    sys.stdin.isatty = lambda: False
    
    try:
        rc = tony.cmd_mission("my mission", workdir=tmp, yes=False)
        assert rc == 1  # Aborts
    finally:
        sys.stdin.isatty = orig_isatty
        _patch_engine_fn("role_call", orig_rc)
        shutil.rmtree(tmp, ignore_errors=True)
