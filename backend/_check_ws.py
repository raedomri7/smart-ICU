import warnings
warnings.filterwarnings("ignore")
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from fastapi.testclient import TestClient
from app.main import app
from app.services.monitoring import monitoring_service

c = TestClient(app)

print("=== TEST BACKEND MONITORING ===")
# 1. Health
h = c.get("/health").json()
print(f"Backend: {h['status']} - {h['app']}")

# 2. Scenarios
sc = c.get("/api/ai/scenarios").json()
print(f"Scenarios: {len(sc)} - {sc}")

# 3. Direct monitoring tick
monitor = monitoring_service
monitor.set_source("P-TEST", mode="simulator", scenario="sepsis")
for _ in range(3):
    snap, na, nr = monitor.tick("P-TEST")
v = snap.vitals
d = snap.decision
p = snap.prediction
print(f"\nDirect tick - FC={v.ecg_hr} | PA={v.nibp_sys}/{v.nibp_dia} | SpO2={v.spo2}% | ETCO2={v.etco2}")
print(f"Severity={d.overall_severity} | {d.diagnosis[:60]}")
print(f"Scores: {[s.name+':'+str(s.score) for s in d.clinical_scores[:3]]}")
print(f"Risks: sepsis={p.sepsis_risk}% aki={p.aki_risk}% vae={p.vae_risk}%")
print(f"Reports: {[r.report_type for r in snap.reports]}")

# 4. WebSocket test
print("\n=== TEST WEBSOCKET ===")
with c.websocket_connect("/ws?patient_id=ICU-204") as ws:
    ws.send_json({"type": "set_scenario", "scenario": "sepsis"})
    for i in range(5):
        m = ws.receive_json()
        if m["type"] == "tick":
            vitals = m["vitals"]
            decision = m["decision"]
            fc = vitals.get("ecg_hr", vitals.get("hr", "?"))
            sbp = vitals.get("nibp_sys", vitals.get("sbp", "?"))
            dbp = vitals.get("nibp_dia", vitals.get("dbp", "?"))
            spo2 = vitals.get("spo2", "?")
            print(f"tick {i+1}: FC={fc} | PA={sbp}/{dbp} | SpO2={spo2}% | sev={decision['overall_severity']}")
            if i == 2:
                print("-> WebSocket monitoring OK!")
                break
        elif m["type"] == "alert":
            alert = m["alert"]
            print(f"  ALERT: {alert['signal']} | {alert['event']} | {alert['severity']}")

print("\n=== CHECK FRONTEND ===")
try:
    import urllib.request
    req = urllib.request.Request("http://localhost:3000/dashboard", method="HEAD")
    with urllib.request.urlopen(req, timeout=5) as resp:
        print(f"Frontend dashboard: HTTP {resp.status}")
except Exception as e:
    print(f"Frontend check: {e}")

print("\n=== DIAGNOSIS COMPLETE ===")
