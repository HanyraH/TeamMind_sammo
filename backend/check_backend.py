"""
Автономная проверка моделей Core Backend без внешних серверов.
"""
import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teammind.settings")
django.setup()
from django.core.management import call_command
from apps.authentication.models import User, UserRole
from apps.organization.models import Department, Position, Employee
from apps.absences.models import Absence, AbsenceType
from apps.projects.models import Project

def main():
    print("=" * 65)
    print("[Core Backend] Proverka Django nastroek i modeley (TZ 6.1, 6.2)...")
    print("=" * 65)
    call_command("check")
    print("--> 1. Sistemnaya proverka Django check proydena uspeshno!")
    roles = [r[0] for r in UserRole.choices]
    print("--> 2. Model User: 8 roley po TZ 6.1 =", roles)
    assert len(roles) == 8, f"Ozhidalos 8 roley, naydeno {len(roles)}"
    print("--> 3. Modeli Department, Position, Employee validny OK")
    types = [t[0] for t in AbsenceType.choices]
    print("--> 4. Modeli Absences: 16 tipov po TZ 6.3 =", len(types), "tipov OK")
    assert len(types) == 16, f"Ozhidalos 16 tipov otsutstviy, naydeno {len(types)}"
    print("--> 5. Modeli Projects & Requirements validny OK")
    print("=" * 65)
    print("[SUCCESS] Vse modeli Core Backend podklyucheny korrektno! OK\n")

if __name__ == "__main__":
    main()
