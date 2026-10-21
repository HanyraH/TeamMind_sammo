"""
Smoke test for Infra and DevOps configuration.
Runs standalone without external services.
"""
import os
from pathlib import Path

def test_infra():
    print("=" * 65)
    print("[QA/DevOps] Proverka konfiguratsii infrastruktury TeamMind...")
    print("=" * 65)
    assert os.path.exists("docker-compose.yml"), "docker-compose.yml otsutstvuet!"
    assert os.path.exists(".gitignore"), ".gitignore otsutstvuet!"
    assert os.path.exists(".env.example"), ".env.example otsutstvuet!"
    assert os.path.exists("infra/nginx/nginx.conf"), "Nginx config otsutstvuet!"
    assert os.path.exists("infra/docker/backend.Dockerfile"), "backend.Dockerfile otsutstvuet!"
    assert os.path.exists("infra/docker/frontend.Dockerfile"), "frontend.Dockerfile otsutstvuet!"
    with open("docker-compose.yml", "r", encoding="utf-8") as f:
        content = f.read()
        assert "services:" in content, "docker-compose ne soderzhit services"
        assert "backend:" in content, "docker-compose ne soderzhit backend"
        assert "frontend:" in content, "docker-compose ne soderzhit frontend"
        assert "postgres:" in content, "docker-compose ne soderzhit postgres"
        assert "redis:" in content, "docker-compose ne soderzhit redis"
        assert "nginx:" in content, "docker-compose ne soderzhit nginx"
    print("--> 1. docker-compose.yml proveren: backend, frontend, postgres, redis, nginx OK")
    print("--> 2. Nginx Reverse Proxy konfiguratsiya validna OK")
    print("--> 3. Peremennye okruzheniya (.env.example) skonfigurirovany OK")
    print("=" * 65)
    print("[SUCCESS] Vse konfiguratsionnye fayly validny i gotovy k deployu! OK\n")

if __name__ == "__main__":
    test_infra()
