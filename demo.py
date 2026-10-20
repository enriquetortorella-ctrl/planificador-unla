"""Run with `streamlit run demo.py`: fake records, in-memory writes only."""
import importlib.util
from pathlib import Path
import sys
import types

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# The real connector is never imported or constructed by this runner.
connector = types.ModuleType("streamlit_gsheets")
connector.GSheetsConnection = type("DisabledGSheetsConnection", (), {})
sys.modules["streamlit_gsheets"] = connector

spec = importlib.util.spec_from_file_location("demo_subject", ROOT / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def fixture():
    rows = [
        dict(Nombre="Demo", Materia="Introducción a Economía Empresarial", Estado="Aprobada", Nota=8, Fecha_aprobacion="2025-03-01"),
        dict(Nombre="Demo", Materia="Historia Económica Contemporánea", Estado="Aprobada", Nota=9, Fecha_aprobacion="2025-07-01"),
        dict(Nombre="Demo", Materia="Matemática I", Estado="Final"),
        dict(Nombre="Demo", Materia="Contabilidad", Estado="Cursando"),
    ]
    return app.asegurar_columnas(pd.DataFrame(rows).fillna("")).astype(object)


class MemoryConnection:
    def read(self, worksheet=0, ttl=0):
        if st.session_state.get("_demo_failure") == "read" or st.session_state.get("_demo_verify_fail"):
            raise RuntimeError("Simulated read failure")
        if "_demo_df" not in st.session_state:
            st.session_state["_demo_df"] = fixture()
        return st.session_state["_demo_df"].copy(deep=True)

    def update(self, worksheet=0, data=None):
        if worksheet == "backup":
            if st.session_state.get("_demo_failure") == "backup":
                raise RuntimeError("Simulated missing backup")
            return
        if st.session_state.get("_demo_failure") == "write":
            raise RuntimeError("Simulated write failure")
        st.session_state["_demo_df"] = data.copy(deep=True)
        if st.session_state.get("_demo_failure") == "verify":
            st.session_state["_demo_verify_fail"] = True


app.get_connection = lambda: MemoryConnection()
st.warning("🎮 MODO DEMO · Datos ficticios. Los cambios duran esta sesión y no se conectan a Google Sheets.")
app.main()
