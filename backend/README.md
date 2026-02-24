# rag4gov

[![Release](https://img.shields.io/github/v/release/LafleurTech/rag4gov)](https://img.shields.io/github/v/release/LafleurTech/rag4gov)
[![Build status](https://img.shields.io/github/actions/workflow/status/LafleurTech/rag4gov/main.yml?branch=main)](https://github.com/LafleurTech/rag4gov/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/LafleurTech/rag4gov/branch/main/graph/badge.svg)](https://codecov.io/gh/LafleurTech/rag4gov)
[![Commit activity](https://img.shields.io/github/commit-activity/m/LafleurTech/rag4gov)](https://img.shields.io/github/commit-activity/m/LafleurTech/rag4gov)
[![License](https://img.shields.io/github/license/LafleurTech/rag4gov)](https://img.shields.io/github/license/LafleurTech/rag4gov)

RAG For Government

- **Github repository**: <https://github.com/LafleurTech/rag4gov/>
- **Documentation** <https://LafleurTech.github.io/rag4gov/>

## Getting started with your project

### 1. Create a New Repository

First, create a repository on GitHub with the same name as this project, and then run the following commands:

```bash
git init -b main
git add .
git commit -m "init commit"
git remote add origin git@github.com:LafleurTech/rag4gov.git
git push -u origin main
```

### 2. Set Up Your Development Environment

Then, install the environment and the pre-commit hooks with

```bash
make install
```

This will also generate your `uv.lock` file

### 3. Run the pre-commit hooks

Initially, the CI/CD pipeline might be failing due to formatting issues. To resolve those run:

```bash
uv run pre-commit run -a
```

### 4. Commit the changes

Lastly, commit the changes made by the two steps above to your repository.

```bash
git add .
git commit -m 'Fix formatting issues'
git push origin main
```
