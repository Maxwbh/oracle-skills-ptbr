"""Ordem de execução de deploy_db e deploy_ords (sem banco)."""
import deploy_db
import deploy_ords


def _toca(base, *rels):
    for rel in rels:
        arq = base / rel
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text("SELECT 1 FROM dual;\n")


def test_deploy_db_spec_antes_do_body_e_scripts_por_ultimo(tmp_path):
    db = tmp_path / "db"
    _toca(db, "packages/b.pkb", "packages/a.pkb", "packages/b.pks", "packages/a.pks",
          "tables/t.sql", "sequences/s.sql", "scripts/002_x.sql", "scripts/001_y.sql",
          "scripts/rascunho.sql")
    plano = deploy_db.montar_plano(db, "all")
    rotulos = [r for r, arqs in plano if arqs]
    assert rotulos == ["sequences", "tables", "packages (spec → body)", "scripts pontuais"]
    pkgs = dict(plano)["packages (spec → body)"]
    assert [a.name for a in pkgs] == ["a.pks", "b.pks", "a.pkb", "b.pkb"]
    scripts = dict(plano)["scripts pontuais"]
    assert [a.name for a in scripts] == ["001_y.sql", "002_x.sql"]


def test_deploy_ords_ordem_das_partes_do_modulo(tmp_path):
    ords = tmp_path / "ords"
    _toca(ords, "security/roles.sql", "modules/clientes/handlers.sql",
          "modules/clientes/module.sql", "modules/clientes/templates.sql")
    plano = deploy_ords.montar_plano(ords, None)
    modulo = dict(plano)["módulo clientes"]
    assert [a.name for a in modulo] == ["module.sql", "templates.sql", "handlers.sql"]
    assert [a.name for a in dict(plano)["segurança global"]] == ["roles.sql"]


def test_deploy_ords_sem_pasta_modules_nao_quebra(tmp_path):
    plano = deploy_ords.montar_plano(tmp_path / "ords", None)
    assert all(not arqs for _, arqs in plano)
