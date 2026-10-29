# Revisión de exposición de datos — `andresochoa1/meta-ads-mcp`

Fecha de la revisión: 2026-10-29
Alcance: repositorio público `andresochoa1/meta-ads-mcp`, código actual y **todo** el historial de git.

## Resumen

**No se encontró ningún secreto, token, clave de API, correo personal ni dato de cliente**, ni en la versión actual ni en ningún commit del historial.

- Commits revisados: **3 de 3**. Es todo el historial alcanzable desde todas las referencias (`git rev-list --all --count` = 3; el clon no es superficial; 69 objetos git).
- El remoto solo tiene la rama `main`. No hay otras ramas, etiquetas, releases, pull requests ni issues.
- Recomendación: **dejar el repositorio público**. No hace falta limpiar el historial ni archivarlo. Más detalle al final.

| Commit | Fecha | Mensaje |
|---|---|---|
| `dd34782` | 2026-04-03 | Initial commit |
| `189aa24` | 2026-04-03 | feat: initial release — security-first Meta Ads MCP server |
| `49f9cac` | 2026-04-03 | fix: QA audit — all critical issues resolved (HEAD de `main`) |

No hay archivos borrados en ningún commit ni archivos binarios. `git fsck` no reporta objetos inalcanzables en el clon.

## Método

1. **gitleaks 8.21.2** (binario oficial; verifiqué el SHA-256 contra el archivo de checksums del release):
   - `gitleaks git --log-opts="--all" --redact` sobre el historial: 3 commits escaneados, **0 hallazgos**.
   - `gitleaks dir --redact` sobre el árbol de trabajo: **0 hallazgos**.
2. **trufflehog 3.88.0** (binario oficial; SHA-256 verificado):
   - `trufflehog git file://… --no-verification` sobre todo el historial: 67 fragmentos, **0 secretos** (ni verificados ni sin verificar).
   - Usé `--no-verification` a propósito para no enviar posibles secretos a servicios de terceros.
3. **Búsqueda manual con expresiones regulares** sobre `git log -p --all`, que es el diff completo de los 3 commits, con 4486 líneas. Busqué:
   - tokens de Meta (`EAA…`);
   - IDs de cuentas publicitarias (`act_…`) y números largos;
   - correos y teléfonos;
   - IPs y URLs;
   - rutas personales (`/Users/…`, `/home/…`);
   - asignaciones del tipo `token=`, `secret=`, `password=` y `api_key=`;
   - cadenas hexadecimales o base64 largas.

   Revisé uno por uno los resultados (ver tabla abajo).
4. **Metadatos de commits**: autor, committer y mensajes completos de los 3 commits.
5. **Lado de GitHub** (no está en el clon), revisado con la API: ramas, etiquetas, releases, pull requests, issues, ejecuciones de Actions y artefactos de Actions.

## Hallazgos

Ninguno de severidad alta o media. Lo que dio positivo en la búsqueda manual resultó ser marcadores de ejemplo o falsos positivos:

| Tipo de dato | Valor (enmascarado) | Archivo(s) | Commit(s) | Veredicto |
|---|---|---|---|---|
| ID de cuenta publicitaria | `act_…` (2 valores distintos) | `SECURITY.md`, `src/meta_ads_mcp/security.py`, `server.py`, `tools/accounts.py`, `tests/*` | `189aa24`, `49f9cac` | Marcadores de ejemplo en docstrings y tests: la secuencia `1234…` y un `act_…` corto. No son cuentas reales. |
| Número largo | `1234…` | `SECURITY.md`, `security.py`, `tests/test_security.py`, `tests/test_tools.py` | `189aa24`, `49f9cac` | El mismo marcador de ejemplo. |
| Token en tests | `test…`, `FAKE…` | `tests/conftest.py`, `tests/test_client.py`, `tests/test_config.py` | `189aa24`, `49f9cac` | Valores falsos de prueba (nombres explícitos de prueba que empiezan por `test…` y `FAKE…`). |
| Variable de token | `META_ACCESS_TOKEN=` | `.env.example`, `README.md`, `smithery.yaml`, `config.py` | `189aa24` | El valor está vacío o es un texto de ejemplo (`your…`); el código lo lee de `os.environ`. |
| "Correo" | `@app…`, `@pyt…` | `server.py`, `tests/*` | `189aa24`, `49f9cac` | Falso positivo: son decoradores de Python. |
| Correo | `nore…@github.com` | `pyproject.toml` | `189aa24` | Correo genérico *noreply* de GitHub. No es personal. |
| Correo de autor y committer | `nore…@andresochoa1.github.com` | metadatos de los 3 commits | todos | Dirección *noreply*; no expone el correo real. |
| Coautor en el mensaje | `nore…@anthropic.com` | mensajes de commit | `189aa24`, `49f9cac` | Dirección genérica *noreply*. |
| IP | `192.…` | `tests/test_security.py` | `189aa24` | IP privada de ejemplo en un test de protección SSRF. |
| URLs | `evil…`, `loca…`, `grap…` | `tests/test_security.py`, `tests/test_pagination.py` | `189aa24` | URLs de ataque simuladas en tests de SSRF y la URL pública de la Graph API. |

### Observación de baja severidad (informativa)

- **Usuario anterior de GitHub `Andr…`**. Las URLs de `README.md`, `SECURITY.md` y `manifest.json` del commit `189aa24` apuntaban a otra cuenta de GitHub. El commit `49f9cac` las corrigió a `andresochoa1`, pero el nombre sigue en el historial y en el mensaje de ese commit. No es un secreto. Solo vincula públicamente las dos cuentas. Si al dueño no le importa ese vínculo, no hay que hacer nada.

### GitHub (fuera del clon)

| Elemento | Estado |
|---|---|
| Ramas | Solo `main` |
| Etiquetas y releases | Ninguna |
| Pull requests | Ninguno (antes de este) |
| Issues | Ninguno |
| Ejecuciones de Actions | 1 (`Tests`, 2026-04-03, terminó en *failure*). Sin artefactos. El workflow no usa `secrets.*` ni variables de entorno sensibles, así que sus logs no pueden contener un token. |

## Sobre el incidente con el token de Meta

En este repositorio **no hay rastro de ningún token de Meta**: ningún valor con forma `EAA…`, ningún `.env` versionado (`.env` está en `.gitignore` desde el primer commit con código) y ningún archivo borrado. Si el token se filtró, no fue por este repositorio, o al menos no por su historial de git. Para cerrar el incidente, recomiendo:

- confirmar que el token afectado ya fue **revocado o rotado** en Meta (Business Settings → System Users / Access Tokens), sin importar por dónde se haya filtrado;
- revisar los otros repositorios, gists y variables de CI del dueño donde haya estado ese token.

## Recomendación

**Dejar el repositorio público.**

- El historial completo (3 commits) está limpio para dos herramientas independientes (gitleaks y trufflehog) y para la revisión manual.
- **Limpiar el historial** (`git filter-repo`/BFG + force push) no tiene sentido: no hay nada que borrar, y reescribir rompería los clones y forks existentes sin ningún beneficio.
- **Archivar** el repositorio solo tendría sentido si el dueño ya no piensa mantenerlo. Por exposición no hace falta.

Medidas preventivas opcionales que debe decidir el dueño (no las apliqué):

- Activar en GitHub *Secret scanning* y *Push protection* (Settings → Code security). Son gratis en repositorios públicos.
- Opcionalmente, agregar un hook de pre-commit con gitleaks.

## Límites de esta revisión

- No pude consultar las **alertas de secret scanning** de GitHub del repositorio. Conviene que el dueño las vea en Security → Secret scanning.
- No revisé los **forks** de terceros, si existen. Como el historial está limpio, un fork no puede contener secretos de este repositorio salvo que se los hayan agregado después.
- Los **logs** de la única ejecución de Actions no los leí línea por línea. Me basé en que el workflow no recibe ningún secreto.
- Es posible que existan objetos que GitHub conserva y que no se ven en el clon, por ejemplo de un force push antiguo. Nada en el clon lo indica: no hay reflogs del remoto ni pull requests, y las fechas y los padres de los commits son lineales.
