# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-03-16

### Added
- Initial release of Chrysalis
- Lambda calculus combinators (I, K, S, B, C, W, Y, Omega)
- Function utilities (compose, pipe, curry, uncurry, etc.)
- Predicates and data access functions
- Algebraic data types (Optional, Result, and their async variants)
- Lenses for composable data access and manipulation
- Lazy evaluation (Lazy, AsyncLazy, thunk, force)
- Implicit function application and implicit placeholder
- Inline control flow (iif, comprehension)
- Declarative control flow (attempt, using, match)
- Safe function evaluation wrapper
- Async support throughout the library
- Full type hints support
- Zero external dependencies

### Changed
- Renamed from FPLL (Fast Python Lambda Library) to Chrysalis
- Relicensed from AGPL-3.0 to CC0-1.0 (Public Domain)
- Rewrote README for PyPI

### Fixed
- Improved documentation and examples
