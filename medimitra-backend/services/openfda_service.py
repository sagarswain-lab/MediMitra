import requests

OPENFDA_BASE = "https://api.fda.gov"

def search_drug(medicine_name: str) -> dict:
    """Search OpenFDA for a drug by name."""
    try:
        url = f"{OPENFDA_BASE}/drug/label.json"
        params = {"search": f"openfda.brand_name:{medicine_name}", "limit": 1}
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("results"):
                return {"found": True, "data": data["results"][0]}
        return {"found": False, "data": {}}
    except Exception as e:
        print(f"OpenFDA error: {e}")
        return {"found": False, "data": {}}

def check_drug_interaction(drug_a: str, drug_b: str) -> dict:
    """Check interaction between two drugs using OpenFDA."""
    try:
        url = f"{OPENFDA_BASE}/drug/event.json"
        query = f'patient.drug.medicinalproduct:"{drug_a}"+AND+patient.drug.medicinalproduct:"{drug_b}"'
        params = {"search": query, "limit": 1}
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            count = data.get("meta", {}).get("results", {}).get("total", 0)
            return {"has_reports": count > 0, "report_count": count}
        return {"has_reports": False, "report_count": 0}
    except Exception as e:
        print(f"OpenFDA interaction error: {e}")
        return {"has_reports": False, "report_count": 0}

def verify_medicine(medicine_name: str) -> dict:
    """Verify if a medicine exists in OpenFDA database."""
    try:
        result = search_drug(medicine_name)
        if result["found"]:
            openfda = result["data"].get("openfda", {})
            return {
                "verified": True,
                "brand_name": openfda.get("brand_name", [medicine_name])[0],
                "manufacturer": openfda.get("manufacturer_name", ["Unknown"])[0],
            }
        return {"verified": False, "brand_name": medicine_name, "manufacturer": "Not found"}
    except Exception as e:
        print(f"OpenFDA verify error: {e}")
        return {"verified": False, "brand_name": medicine_name, "manufacturer": "Error"}