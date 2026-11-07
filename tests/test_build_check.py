"""build.py --check: validação própria, sem depender de /mnt/skills (Fase 4)."""
import importlib.util
import textwrap
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def build(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("build_mod", RAIZ / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "SKILLS", tmp_path / "skills")
    monkeypatch.setattr(mod, "SHARED", tmp_path / "shared")
    monkeypatch.setattr(mod, "ROOT", tmp_path)       # isola de um .clientes-proibidos.txt local
    monkeypatch.delenv("CLIENTES_PROIBIDOS", raising=False)
    return mod


def _skill(base: Path, nome="oracle-x-ptbr", *, frontmatter=None, arquivos=None,
           changelog_versao="1.0.0", manifest=None):
    d = base / "skills" / nome
    d.mkdir(parents=True)
    fm = frontmatter if frontmatter is not None else textwrap.dedent(f"""\
        name: {nome}
        description: "Teste. ATIVE em x. NÃO ATIVE em y."
        metadata:
          version: "1.0.0"
          suite_size: 2
        """)
    (d / "SKILL.md").write_text(f"---\n{fm}---\n\n# Corpo\n", encoding="utf-8")
    (d / "CHANGELOG.md").write_text(f"# Changelog\n\n## [{changelog_versao}] - 2026-11-06\n- x\n")
    for rel, conteudo in (arquivos if arquivos is not None else {"assets/a.sql": "SELECT 1 FROM dual;\n"}).items():
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(conteudo, encoding="utf-8")
    if manifest:
        (d / "manifest.yml").write_text(manifest)
    return d


def test_skill_valida_nao_tem_problemas(build, tmp_path):
    assert build.verificar(_skill(tmp_path)) == []


def test_nao_depende_de_mnt_skills(build, tmp_path, monkeypatch):
    # Mesmo que o validador externo exista ou não, o resultado é o mesmo.
    monkeypatch.setattr(Path, "exists", Path.exists)
    assert build.verificar(_skill(tmp_path)) == []


def test_yaml_invalido(build, tmp_path):
    d = _skill(tmp_path, frontmatter="name: [quebrado\n")
    assert any("YAML" in p for p in build.verificar(d))


def test_name_diferente_da_pasta(build, tmp_path):
    fm = 'name: outro-nome\ndescription: "x"\nmetadata:\n  version: "1.0.0"\n  suite_size: 2\n'
    assert any("name" in p for p in build.verificar(_skill(tmp_path, frontmatter=fm)))


def test_description_maior_que_1024(build, tmp_path):
    fm = f'name: oracle-x-ptbr\ndescription: "{"a" * 1025}"\nmetadata:\n  version: "1.0.0"\n  suite_size: 2\n'
    assert any("1024" in p for p in build.verificar(_skill(tmp_path, frontmatter=fm)))


def test_version_ausente(build, tmp_path):
    fm = 'name: oracle-x-ptbr\ndescription: "x"\nmetadata:\n  suite_size: 2\n'
    assert any("version" in p for p in build.verificar(_skill(tmp_path, frontmatter=fm)))


def test_suite_size_diferente_da_contagem_real(build, tmp_path):
    d = _skill(tmp_path, arquivos={"assets/a.sql": "x", "assets/b.sql": "y"})
    assert any("suite_size" in p for p in build.verificar(d))  # real = 3 (2 + CHANGELOG)


def test_suite_size_conta_shared_propagado_e_ignora_manifest_e_cache(build, tmp_path):
    (tmp_path / "shared" / "assets").mkdir(parents=True)
    (tmp_path / "shared" / "assets" / "util.py").write_text("x = 1\n")
    fm = 'name: oracle-x-ptbr\ndescription: "x"\nmetadata:\n  version: "1.0.0"\n  suite_size: 3\n'
    d = _skill(tmp_path, frontmatter=fm,
               arquivos={"assets/a.sql": "x", "assets/__pycache__/m.pyc": "lixo"},
               manifest="shared:\n  assets:\n    - util.py\n")
    assert build.verificar(d) == []


def test_cliente_real_em_qualquer_arquivo_de_texto(build, tmp_path, monkeypatch):
    # Nomes fictícios: a lista real só existe no secret/arquivo local.
    monkeypatch.setenv("CLIENTES_PROIBIDOS", "Cliente Fictício")
    d = _skill(tmp_path, arquivos={"assets/a.sql": "-- ambiente do CLIENTE FICTICIO\nSELECT 1 FROM dual;\n"})
    assert any("cliente real" in p for p in build.verificar(d))


def test_sem_lista_configurada_a_trava_fica_inativa(build, tmp_path, monkeypatch):
    d = _skill(tmp_path, arquivos={"assets/a.sql": "-- ambiente do Cliente Fictício\n"})
    assert build.verificar(d) == []
    assert build.clientes_proibidos() == []


def test_lista_por_arquivo_local(build, tmp_path):
    (tmp_path / ".clientes-proibidos.txt").write_text("# comentário\nOutro Cliente\n")
    d = _skill(tmp_path, arquivos={"references/r.md": "Projeto do outro cliente.\n"})
    assert any("Outro Cliente" in p for p in build.verificar(d))


def test_cliente_extra_por_variavel_de_ambiente(build, tmp_path, monkeypatch):
    monkeypatch.setenv("CLIENTES_PROIBIDOS", "Acme Saude, Outro")
    d = _skill(tmp_path, arquivos={"assets/a.py": "# feito para a ACME SAUDE\n"})
    assert any("cliente real" in p for p in build.verificar(d))


def test_changelog_da_skill_desatualizado(build, tmp_path):
    d = _skill(tmp_path, changelog_versao="0.9.0")
    assert any("CHANGELOG" in p for p in build.verificar(d))


def test_marketplace_divergente(build, tmp_path):
    _skill(tmp_path)
    mk = tmp_path / "marketplace.yml"
    mk.write_text('skills:\n  - name: "oracle-x-ptbr"\n    version: "0.1.0"\n')
    problemas = build.verificar_marketplace(mk)
    assert any("0.1.0" in p for p in problemas)


# ─── dist/ versionado em dia ─────────────────────────────────────────────────

def _dist(build, tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    monkeypatch.setattr(build, "DIST", dist)
    monkeypatch.setattr(build, "BUILD_TMP", tmp_path / ".build_tmp")
    return dist


def test_dist_em_dia_passa(build, tmp_path, monkeypatch):
    _dist(build, tmp_path, monkeypatch)
    d = _skill(tmp_path)
    build.empacotar_skill(d)
    build.gerar_checksums()
    assert build.verificar_dist([d]) == []


def test_dist_desatualizado_ou_ausente_ou_sobrando(build, tmp_path, monkeypatch):
    dist = _dist(build, tmp_path, monkeypatch)
    d = _skill(tmp_path)
    build.empacotar_skill(d)
    (dist / "oracle-velha-ptbr.skill").write_bytes(b"PK")          # sobra
    build.gerar_checksums()
    (d / "assets" / "a.sql").write_text("SELECT 2 FROM dual;\n")   # fonte mudou
    problemas = build.verificar_dist([d])
    assert any("desatualizado" in p for p in problemas)
    assert any("oracle-velha-ptbr.skill" in p for p in problemas)
    (dist / "oracle-x-ptbr.skill").unlink()
    assert any("ausente" in p for p in build.verificar_dist([d]))


def test_dist_checksum_divergente(build, tmp_path, monkeypatch):
    dist = _dist(build, tmp_path, monkeypatch)
    d = _skill(tmp_path)
    build.empacotar_skill(d)
    (dist / "checksums.sha256").write_text("0" * 64 + "  oracle-x-ptbr.skill\n")
    assert any("checksums" in p for p in build.verificar_dist([d]))
