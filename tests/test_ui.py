"""Streamlit tests run only demo.py, whose connector is in-memory."""
import unittest
from pathlib import Path
import pandas as pd

import streamlit as st
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class UITests(unittest.TestCase):
    def start(self):
        st.cache_data.clear()
        at = AppTest.from_file(str(ROOT / "demo.py"), default_timeout=30)
        at.session_state["sonidos"] = False
        at.session_state["efectos"] = False
        at.run()
        self.assertEqual(list(at.exception), [])
        at.selectbox(key="soldado").select("Demo").run()
        self.assertEqual(list(at.exception), [])
        return at

    def click(self, at, label):
        next(b for b in at.button if b.label == label).click().run()
        self.assertEqual(list(at.exception), [])

    def test_navigation_every_click_and_secondary_views(self):
        at = self.start()
        for menu in ["Proximas", "Stats", "Inicio", "Grupo", "Proximas", "Inicio"]:
            at.radio(key="pantalla").set_value(menu).run()
            self.assertEqual(at.session_state["menu"], menu)
            self.assertEqual(list(at.exception), [])
        at.radio(key="seccion_cursada").set_value("Horarios").run()
        self.assertIn("📅 GRILLA DE HORARIOS", [h.value for h in at.header])

    def test_existing_grade_and_date_preserved_and_edit_saves(self):
        at = self.start()
        at.radio(key="pantalla").set_value("Stats").run()
        at.radio(key="seccion_avance").set_value("Historial").run()
        note = next(n for n in at.number_input if n.label == "Nueva nota (4-10):")
        self.assertEqual(note.value, 8)
        self.assertEqual(str(at.date_input[0].value), "2025-03-01")
        note.set_value(10)
        self.click(at, "💾 ACTUALIZAR")
        saved = at.session_state["_demo_df"]
        self.assertEqual(saved.iloc[0]["Nota"], 10)
        self.assertEqual(saved.iloc[0]["Fecha_aprobacion"], "2025-03-01")
        self.assertTrue(any("verificados" in s.value for s in at.success))

    def test_no_final_keeps_form_and_registers(self):
        at = self.start()
        self.click(at, "📋 Terminé de cursar")
        self.click(at, "❌ No, apruebo por cursada")
        self.assertTrue(any(b.label == "🎖️ APROBAR" for b in at.button))
        self.click(at, "🎖️ APROBAR")
        saved = at.session_state["_demo_df"]
        self.assertEqual(saved[saved["Materia"] == "Contabilidad"].iloc[0]["Estado"], "Aprobada")

    def test_failed_save_never_celebrates(self):
        for failure in ["read", "write", "verify"]:
            with self.subTest(failure=failure):
                at = self.start()
                self.click(at, "📋 Terminé de cursar")
                self.click(at, "❌ No, apruebo por cursada")
                at.session_state["_demo_failure"] = failure
                self.click(at, "🎖️ APROBAR")
                self.assertGreater(len(at.error), 0)
                self.assertEqual(len(at.success), 0)
                self.assertFalse(at.session_state["show_confetti"])
                self.assertIsNone(at.session_state["play_sound"])
                if failure in {"read", "write"}:
                    self.assertEqual(at.session_state["_demo_df"].iloc[3]["Estado"], "Cursando")

    def test_planner_search_filter_map_and_enrollment(self):
        at = self.start()
        at.radio(key="pantalla").set_value("Proximas").run()
        at.text_input(key="buscar_Demo").set_value("microeconomia").run()
        self.assertEqual(at.selectbox(key="detalle_Demo").options, ["Microeconomía I"])
        at.checkbox(key="abrir_mapa_Demo").check().run()
        self.assertEqual(list(at.exception), [])
        self.click(at, "⚔️ Agregar a mi cursada")
        saved = at.session_state["_demo_df"]
        self.assertIn("Microeconomía I", saved["Materia"].tolist())
        at.selectbox(key="filtro_Demo").select("Bloqueadas").run()
        self.assertEqual(at.selectbox(key="detalle_Demo").options, ["Microeconomía II"])
        self.assertTrue(next(b for b in at.button if b.label == "⚔️ Agregar a mi cursada").disabled)

    def test_editing_partial_does_not_invent_exam_date(self):
        at = self.start()
        self.click(at, "✏️")
        date_input = next(d for d in at.date_input if d.label == "Fecha del próximo parcial:")
        self.assertIsNone(date_input.value)
        self.click(at, "💾 GUARDAR")
        self.assertEqual(at.session_state["_demo_df"].iloc[3]["Fecha_examen"], "")

    def test_empty_search_and_effect_preferences(self):
        at = self.start()
        at.checkbox(key="sonidos").check().run()
        at.slider(key="volumen").set_value(20).run()
        at.checkbox(key="efectos").check().run()
        self.assertEqual(at.session_state["volumen"], 20)
        at.radio(key="pantalla").set_value("Proximas").run()
        at.text_input(key="buscar_Demo").set_value("No existe").run()
        self.assertTrue(any("No hay materias" in i.value for i in at.info))
        self.assertEqual(list(at.exception), [])

    def test_switching_approved_subject_refreshes_saved_values(self):
        at = self.start()
        at.radio(key="pantalla").set_value("Stats").run()
        at.radio(key="seccion_avance").set_value("Historial").run()
        at.selectbox(key="hist_materia_Demo").select("Historia Económica Contemporánea").run()
        note = next(n for n in at.number_input if n.label == "Nueva nota (4-10):")
        self.assertEqual(note.value, 9)
        self.assertEqual(str(at.date_input[0].value), "2025-07-01")

    def test_sheets_float_blank_columns_remain_editable(self):
        st.cache_data.clear()
        at = AppTest.from_file(str(ROOT / "demo.py"), default_timeout=30)
        at.session_state["sonidos"] = False
        at.session_state["efectos"] = False
        at.session_state["_demo_df"] = pd.DataFrame([{
            "Nombre":"Demo", "Materia":"Contabilidad", "Estado":"Cursando",
            "Fecha_examen":float("nan"), "Nota_parcial1":float("nan"),
        }])
        at.run()
        at.selectbox(key="soldado").select("Demo").run()
        self.click(at, "✏️")
        next(n for n in at.number_input if n.label == "Parcial 1 (0=sin nota):").set_value(8)
        self.click(at, "💾 GUARDAR")
        self.assertEqual(at.session_state["_demo_df"].iloc[0]["Nota_parcial1"], 8)

    def test_approval_effect_is_generated_only_after_confirmation(self):
        at = self.start()
        at.checkbox(key="sonidos").check().run()
        at.checkbox(key="efectos").check().run()
        self.click(at, "📋 Terminé de cursar")
        self.click(at, "❌ No, apruebo por cursada")
        self.click(at, "🎖️ APROBAR")
        embeds = at.get("iframe")
        html = "\n".join(e.proto.srcdoc for e in embeds)
        self.assertIn("MISSION COMPLETE", html)
        self.assertIn("playMissionComplete", html)
        self.assertNotIn("cdn.jsdelivr", html)

    def test_invalid_initial_sheet_shows_error_without_crashing(self):
        st.cache_data.clear()
        at = AppTest.from_file(str(ROOT / "demo.py"), default_timeout=30)
        at.session_state["_demo_df"] = pd.DataFrame({"Otra columna":["dato ficticio"]})
        at.run()
        self.assertEqual(list(at.exception), [])
        self.assertGreater(len(at.error), 0)

    def test_cache_refresh_cannot_replace_open_edit_baseline(self):
        at = self.start()
        at.radio(key="pantalla").set_value("Stats").run()
        at.radio(key="seccion_avance").set_value("Historial").run()
        next(n for n in at.number_input if n.label == "Nueva nota (4-10):").set_value(10)
        remote = at.session_state["_demo_df"].copy(deep=True)
        remote.loc[0, "Nota"] = 6
        at.session_state["_demo_df"] = remote
        st.cache_data.clear()  # Simulates TTL expiry / another session's save.
        self.click(at, "💾 ACTUALIZAR")
        self.assertGreater(len(at.error), 0)
        self.assertEqual(len(at.success), 0)
        self.assertEqual(at.session_state["_demo_df"].iloc[0]["Nota"], 6)

    def test_blank_legacy_state_does_not_become_active(self):
        st.cache_data.clear()
        at = AppTest.from_file(str(ROOT / "demo.py"), default_timeout=30)
        at.session_state["_demo_df"] = pd.DataFrame([{
            "Nombre":"Demo", "Materia":"Contabilidad", "Estado":float("nan"),
        }])
        at.run()
        at.selectbox(key="soldado").select("Demo").run()
        self.assertFalse(any(b.label == "📋 Terminé de cursar" for b in at.button))
        self.assertEqual(at.session_state["_base_df"].iloc[0]["Estado"], "")
        self.assertEqual(list(at.exception), [])


if __name__ == "__main__":
    unittest.main()
