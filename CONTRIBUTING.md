# Contributing to n8n Automation Hub

Thank you for your interest in contributing to **n8n Automation Hub**! This repository provides open-source, production-ready AI automation workflows designed to run on self-hosted n8n instances.

---

## 🌟 How to Contribute

1. **Fork the Repository** on GitHub.
2. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/new-workflow-or-fix
   ```
3. **Add or Update Workflows**:
   - Save your workflow JSON export inside the appropriate tier folder (`1. Beginner Projects/`, `2. Intermediate Projects/`, or `3. Advanced Projects/`).
   - Remove any hardcoded API keys, personal phone numbers, or private bot tokens. Use environment variables (e.g. `{{ $env.YOUR_VAR }}`) or placeholders (`YOUR_API_KEY`).
   - Document your workflow in a companion `README.md` with:
     - Architecture & Node Diagram
     - Input/Output specifications
     - Step-by-step setup guide
4. **Test Your Changes**:
   - Verify that your workflow imports cleanly into n8n via **Import from File**.
5. **Submit a Pull Request**:
   - Describe what the workflow does and list the required integrations.

---

## 🔒 Security Best Practices

- **Zero Secret Policy**: Never commit actual API keys, credentials, or `.env` files. Always use `.env.example` templates with mock values.
- **Deduplication & Error Handling**: Ensure loops and polling workflows feature timeout and retry guards.

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the project's **MIT License**.
