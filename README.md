# BibliothecaFabulae [![Commit Status](https://github.com/LegendarySpork9/BibliothecaFabulae/actions/workflows/Commit.yml/badge.svg?event=push)](https://github.com/LegendarySpork9/BibliothecaFabulae/actions/workflows/Commit.yml) [![PR Status](https://github.com/LegendarySpork9/BibliothecaFabulae/actions/workflows/Pull%20Request.yml/badge.svg)](https://github.com/LegendarySpork9/BibliothecaFabulae/actions/workflows/Pull%20Request.yml)

Self-hosted personal fanfiction archive and reader. Downloads fics from bookmarks and favourites across 100+ supported sites (AO3, FFNet, Wattpad, SpaceBattles, Royal Road, etc.), stores them locally with full metadata, and provides a private web interface for reading, searching, and organising your collection. Integrates with the separate Archive Scanner project for new work discovery by relationship tag. Includes a multi-phase text-to-speech reader with gender-differentiated and character-specific voice cloning.

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend language |
| FastAPI | Backend framework |
| React | Frontend SPA |
| Tailwind CSS | Styling |
| SQLite | Database (WAL mode, FTS5) |
| SQLAlchemy | ORM |
| Alembic | Database migrations |
| FanFicFare | Download engine (100+ sites) |
| edge-tts | Text-to-speech |
| Coqui XTTS v2 | Voice cloning |
| BookNLP | Dialogue attribution |
| pytest | Testing |

## Status

Active development

## Documentation

Setup, configuration, and usage documentation is available on the [LegendarySpork9 Wiki](https://wiki.legendaryspork9.co.uk).

---

Copyright © 2026 Toby Hunter, All rights reserved.
