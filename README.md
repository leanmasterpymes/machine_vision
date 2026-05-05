# machine_vision

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Aplicacion web que recibe la imagen de una hoja escaneada, reconstruye su contenido y devuelve un archivo Excel editable.

## Stack

- **UI:** Streamlit (subida + edicion de tabla + descarga)
- **Vision:** modelo de vision multimodal de Anthropic via `anthropic` SDK
- **Excel:** openpyxl + pandas

## Estructura

```
machine_vision/
├── streamlit_app.py      # UI principal
├── app/
│   ├── vision.py         # imagen -> JSON estructurado
│   └── excel.py          # DataFrame -> .xlsx
├── uploads/              # gitignored
├── outputs/              # gitignored
├── requirements.txt
├── .env.example
└── README.md
```

## Puesta en marcha

```bash
cd /home/mapo/proyectos/machine_vision
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # y completar ANTHROPIC_API_KEY
streamlit run streamlit_app.py
```

Streamlit abre automaticamente http://localhost:8501. Subi la imagen, presiona **Extraer contenido**, edita la tabla en pantalla y descarga el `.xlsx`.

## Despliegue en Streamlit Community Cloud

1. Empujar el repo a GitHub.
2. Entrar a https://share.streamlit.io con la cuenta de GitHub y elegir **New app**.
3. Seleccionar el repo, branch `main`, y como archivo principal: `streamlit_app.py`.
4. En **Advanced settings → Secrets** pegar:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. **Deploy**. La URL queda en `https://<app>.streamlit.app`.

El codigo lee el secreto desde `st.secrets` en Cloud y desde `.env` en local.
