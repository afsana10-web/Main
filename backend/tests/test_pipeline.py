def test_demo_case_runs_full_pipeline(client, officer_token):
    headers = {"Authorization": f"Bearer {officer_token}"}
    r = client.post("/api/demo/mostly_compliant/run", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["is_demo"] is True
    assert data["status"] in ("COMPLIANT", "POTENTIAL_NON_COMPLIANCE", "NEEDS_OFFICER_VERIFICATION")

    inspection_id = data["id"]
    results = client.get(f"/api/inspections/{inspection_id}/results", headers=headers)
    assert results.status_code == 200
    body = results.json()
    assert len(body["declarations"]) == 10  # all 10 declaration fields always present
    assert len(body["checks"]) > 0


def test_finding_verification_never_overwrites_automated_result(client, officer_token):
    headers = {"Authorization": f"Bearer {officer_token}"}
    run = client.post("/api/demo/missing_declaration/run", headers=headers).json()
    findings = client.get(f"/api/inspections/{run['id']}/findings", headers=headers).json()
    assert len(findings) > 0
    finding_id = findings[0]["id"]
    original_detected = findings[0]["detected"]

    verify = client.post(
        f"/api/findings/{finding_id}/verify", headers=headers,
        json={"decision": "REJECTED", "remarks": "Officer inspected physically, declaration was present."},
    )
    assert verify.status_code == 200
    assert verify.json()["verification"]["decision"] == "REJECTED"
    # automated finding's "detected" value must be unchanged
    assert verify.json()["detected"] == original_detected


def test_evidence_never_fabricated_when_unavailable(client, officer_token):
    headers = {"Authorization": f"Bearer {officer_token}"}
    run = client.post("/api/demo/poor_quality/run", headers=headers).json()
    evidence = client.get(f"/api/inspections/{run['id']}/evidence", headers=headers).json()
    for e in evidence:
        if e["status"] == "NOT_AVAILABLE":
            assert e["bbox_x"] is None and e["bbox_y"] is None
