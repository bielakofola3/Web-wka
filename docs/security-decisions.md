# Decyzje bezpieczeństwa – MycoForum

## Hasła (W-02, W-14, W-15)
- Argon2id z parametrami: memory_cost=65536, time_cost=3, parallelism=4
- Minimalna długość 8 znaków, odrzucanie popularnych haseł
- Zmiana hasła wymaga podania starego (do zaimplementowania w pełnej wersji)

## Sesje (W-04, W-05)
- SessionMiddleware z cookie: Secure, HttpOnly, SameSite=Lax
- Nowa sesja przy logowaniu (`session.clear()`)
- Wylogowanie czyści sesję po stronie serwera

## CSRF (W-06)
- Middleware `starlette-csrf`
- Token w każdym formularzu POST
- Operacje zmieniające dane tylko przez POST

## Autoryzacja (W-07)
- Sprawdzanie `author_id == current_user.id` przed edycją/usunięciem
- Brak domyślnych kont

## XSS (W-08)
- Jinja2 auto-escaping + jawne `|e` na treściach użytkowników
- CSP bez unsafe-inline dla skryptów (style dozwolone tymczasowo)

## SQLi (W-09)
- Wyłącznie SQLAlchemy ORM

## Walidacja (W-10)
- Form validation + długości pól + strip()

## Infrastruktura
- Baza oddzielona, połączenie TLS w produkcji
- Load balancer przed aplikacją
- Tylko 80/443 z internetu
- Sekrety w secret managerze / GitHub Secrets

## CI/CD (W-21, W-24–W-28)
- Testy przy każdym PR
- Semgrep SAST
- Dependabot / pip-audit
- Secret scanning
- Deploy z pipeline po merge (do skonfigurowania)

## Logi (W-30)
- Logowanie udanych i nieudanych logowań z IP i czasem
- Brak haseł w logach
