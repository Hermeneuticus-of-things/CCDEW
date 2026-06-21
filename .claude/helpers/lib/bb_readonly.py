"""
BetterBird Profile Read-Only Guard
Acest modul asigură că scripturile CCDEW NU pot modifica profilul BB live.
"""
import os
import shutil
import tempfile

BB_PROFILE = os.path.expanduser("~/.var/app/eu.betterbird.Betterbird/.thunderbird/b8e98ik1.default-default")

def get_safe_profile_path():
    """
    Returnează o copie temporară read-only a profilului BB în /tmp.
    Orice script CCDEW trebuie să folosească ASTA, niciodată BB_PROFILE direct.
    """
    if not os.path.exists(BB_PROFILE):
        raise RuntimeError("BetterBird profile missing!")
    
    # Verifică marcajul de protecție
    protected = os.path.join(BB_PROFILE, ".CCDEW_PROTECTED")
    if os.path.exists(protected):
        with open(protected) as f:
            lines = f.readlines()
            for line in lines:
                if "DO NOT MODIFY" in line:
                    break
            else:
                raise RuntimeError("Profile protection flag invalid!")
    
    temp_dir = tempfile.mkdtemp(prefix="bb_ro_copy_")
    
    # Copiem doar fișierele necesare (ImapMail, logins.json, prefs.js, key4.db)
    for subdir in ["ImapMail"]:
        src = os.path.join(BB_PROFILE, subdir)
        dst = os.path.join(temp_dir, subdir)
        if os.path.exists(src):
            shutil.copytree(src, dst)
    
    for f in ["prefs.js", "logins.json", "key4.db", "cert9.db", "compatibility.ini"]:
        src = os.path.join(BB_PROFILE, f)
        if os.path.exists(src):
            shutil.copy2(src, temp_dir)
    
    return temp_dir

def cleanup_safe_copy(path):
    """Șterge copia temporară după folosire."""
    if path and os.path.exists(path) and "bb_ro_copy_" in path:
        shutil.rmtree(path)
